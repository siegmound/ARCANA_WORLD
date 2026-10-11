"""Offline, synthetic-only W3-B invocation provenance checks.

This module validates bindings supplied by an evidence resolver. The bundled
resolver protocol has no trust store for production owners, so positive
results remain explicitly synthetic and never establish runtime authority.
Payload decoding is delegated to the existing N2A/N2C implementation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Callable, Generic, Mapping, Protocol, Sequence, TypeVar
from uuid import UUID

from scripts.r6_si1_bandwidth_f2b_n2c_capture_verify import verify_capture_payload


SYNTHETIC_SCOPE = "SYNTHETIC_FIXTURE_ONLY"
INVOCATION_VALID = "SYNTHETIC_INVOCATION_VALID_RUNTIME_AUTHORITY_UNKNOWN"
CAPTURE_ONLY_STOP = "CAPTURE_ONLY_STOP_REQUIRED"
CAPTURE_FAILED = "CAPTURE_FAILED"
UNKNOWN_AUTHORITY = "UNKNOWN_AUTHORITY"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ProvenanceError(ValueError):
    """Malformed, inconsistent, duplicate, or unauthoritative fixture input."""


T = TypeVar("T")


@dataclass(frozen=True)
class Owned(Generic[T]):
    value: T
    evidence_id: str


@dataclass(frozen=True)
class RunIdentity:
    run_uuid: str
    attempt_uuid: str
    job_execution_id: str


@dataclass(frozen=True)
class ProcessIdentity:
    communicator_uuid: str
    communicator_epoch: int
    host_id: str
    pid: int
    rank: int
    role: str


@dataclass(frozen=True)
class AssignmentIdentity:
    sequence: int
    sender_rank: int
    destination_rank: int
    mpi_tag: int
    local_modnum: int
    model_id: str
    model_definition_sha256: str


@dataclass(frozen=True)
class CallIdentity:
    shells_phase: str
    shells_call_sequence: int
    rpeat: int
    max_iter: int
    pure_call_sequence: int
    pure_iteration: int
    fem_ordinal: int


@dataclass(frozen=True)
class EffectiveStateIdentity:
    input_manifest_sha256: str
    variable_vector_sha256: str
    state_id: str
    constraints_sha256: str


@dataclass(frozen=True)
class ImplementationIdentity:
    source_lock_sha256: str
    candidate_tree_sha256: str
    build_record_sha256: str
    executable_sha256: str


@dataclass(frozen=True)
class DofIdentity:
    ordering_id: str
    feg_sha256: str
    runtime_sha256: str
    permutation_manifest_sha256: str


@dataclass(frozen=True)
class SystemIdentity:
    capture_point: str
    n: int
    kl: int
    ku: int
    a0b0_sha256: str


@dataclass(frozen=True)
class InvocationContext:
    run: Owned[RunIdentity]
    process: Owned[ProcessIdentity]
    assignment: Owned[AssignmentIdentity]
    call: Owned[CallIdentity]
    effective_state: Owned[EffectiveStateIdentity]
    implementation: Owned[ImplementationIdentity]
    dof: Owned[DofIdentity]
    system: Owned[SystemIdentity]


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    owner: str
    subject: str
    value_sha256: str
    scope: str
    evidence_bytes: bytes
    evidence_sha256: str


class EvidenceResolver(Protocol):
    def resolve(self, evidence_id: str) -> EvidenceRecord | None: ...


class MappingEvidenceResolver:
    """Resolver for bounded fixtures; not a production trust authority."""

    def __init__(self, records: Mapping[str, EvidenceRecord]):
        self._records = dict(records)

    def resolve(self, evidence_id: str) -> EvidenceRecord | None:
        return self._records.get(evidence_id)


@dataclass(frozen=True)
class SnapshotSidecar:
    schema_version: int
    scope: str
    invocation_key: str
    payload_sha256: str
    payload_bytes: int
    source_value_sha256: str
    n: int
    kl: int
    ku: int
    dof_ordering_id: str


@dataclass(frozen=True)
class CaptureOutcome:
    status: str
    invocation_key: str | None
    payload_sha256: str | None
    runtime_authority: str
    solver_entered: bool
    error: str | None = None


CAPTURE_TERMINAL_RETURN = "RETURN_BEFORE_SOLVER"


def require_capture_terminal(outcome: CaptureOutcome) -> str:
    """Accept only explicit terminal capture outcomes; unknown states fail closed."""
    if not isinstance(outcome, CaptureOutcome):
        raise ProvenanceError("typed capture outcome required")
    if (not isinstance(outcome.status, str) or
            outcome.status not in {CAPTURE_ONLY_STOP, CAPTURE_FAILED} or
            outcome.solver_entered is not False):
        raise ProvenanceError("capture-only outcome is not a verified pre-Solver terminal state")
    return CAPTURE_TERMINAL_RETURN


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _hash_ok(value: object, label: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ProvenanceError(f"{label} must be lowercase SHA256")


def _positive(value: object, label: str, *, zero: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < (0 if zero else 1):
        raise ProvenanceError(f"{label} outside its valid integer range")


_OWNER_AND_SUBJECT = {
    "run": ("RUN_ORCHESTRATOR_FIXTURE", "run"),
    "process": ("COMMUNICATOR_FIXTURE", "process"),
    "assignment": ("MASTER_DISPATCH_FIXTURE", "assignment"),
    "call": ("CALL_TRACE_FIXTURE", "call"),
    "effective_state": ("INPUT_STATE_FIXTURE", "effective_state"),
    "implementation": ("BUILD_PROVENANCE_FIXTURE", "implementation"),
    "dof": ("DOF_PROVENANCE_FIXTURE", "dof"),
    "system": ("SYSTEM_CAPTURE_FIXTURE", "system"),
}
_VALUE_TYPES = {
    "run": RunIdentity,
    "process": ProcessIdentity,
    "assignment": AssignmentIdentity,
    "call": CallIdentity,
    "effective_state": EffectiveStateIdentity,
    "implementation": ImplementationIdentity,
    "dof": DofIdentity,
    "system": SystemIdentity,
}


def invocation_key(context: InvocationContext) -> str:
    """Stable key over typed identity values; excludes evidence envelope bytes."""
    values = {name: asdict(getattr(context, name).value) for name in _OWNER_AND_SUBJECT}
    return hashlib.sha256(b"ARCANA-N2C-W3B-INVOCATION-V1\0" + _canonical(values)).hexdigest()


def invocation_coordinate_key(context: InvocationContext) -> str:
    """Physical call coordinates, deliberately excluding mutable capture contents."""
    run = context.run.value
    process = context.process.value
    assignment = context.assignment.value
    call = context.call.value
    coordinates = {
        "run_uuid": run.run_uuid,
        "attempt_uuid": run.attempt_uuid,
        "communicator_uuid": process.communicator_uuid,
        "communicator_epoch": process.communicator_epoch,
        "host_id": process.host_id,
        "pid": process.pid,
        "rank": process.rank,
        "assignment_sequence": assignment.sequence,
        "shells_phase": call.shells_phase,
        "shells_call_sequence": call.shells_call_sequence,
        "rpeat": call.rpeat,
        "pure_call_sequence": call.pure_call_sequence,
        "pure_iteration": call.pure_iteration,
        "fem_ordinal": call.fem_ordinal,
    }
    return hashlib.sha256(b"ARCANA-N2C-W3B-FEM-COORDINATE-V1\0" + _canonical(coordinates)).hexdigest()


def _assignment_binding_key(context: InvocationContext, resolver: EvidenceResolver) -> str:
    """Immutable master assignment and owner evidence identity within one run attempt."""
    binding = context.assignment
    record = resolver.resolve(binding.evidence_id)
    if record is None:  # validate_invocation normally catches this; keep the helper fail-closed.
        raise ProvenanceError("assignment evidence is UNKNOWN")
    return hashlib.sha256(b"ARCANA-N2C-W3B-ASSIGNMENT-BINDING-V1\0" + _canonical({
        "assignment": asdict(binding.value),
        "evidence_id": binding.evidence_id,
        "owner": record.owner,
        "subject": record.subject,
        "scope": record.scope,
        "value_sha256": record.value_sha256,
        "evidence_sha256": record.evidence_sha256,
    })).hexdigest()


def _verify_evidence(context: InvocationContext, resolver: EvidenceResolver) -> None:
    for field, (expected_owner, expected_subject) in _OWNER_AND_SUBJECT.items():
        binding: Owned[object] = getattr(context, field)
        if not isinstance(binding, Owned) or not isinstance(binding.value, _VALUE_TYPES[field]):
            raise ProvenanceError(f"{field} typed owner binding is required")
        if not isinstance(binding.evidence_id, str) or not binding.evidence_id:
            raise ProvenanceError(f"{field} evidence reference is missing")
        record = resolver.resolve(binding.evidence_id)
        if record is None:
            raise ProvenanceError(f"{field} evidence is UNKNOWN")
        if record.evidence_id != binding.evidence_id:
            raise ProvenanceError(f"{field} resolver returned a different evidence identity")
        if record.scope != SYNTHETIC_SCOPE:
            raise ProvenanceError("production owner authority is UNKNOWN to this offline validator")
        if record.owner != expected_owner or record.subject != expected_subject:
            raise ProvenanceError(f"{field} evidence owner/subject mismatch")
        if not isinstance(record.evidence_bytes, bytes):
            raise ProvenanceError(f"{field} evidence must be immutable bytes")
        actual_evidence_sha = hashlib.sha256(record.evidence_bytes).hexdigest()
        _hash_ok(record.evidence_sha256, f"{field} evidence digest")
        _hash_ok(record.value_sha256, f"{field} evidence value digest")
        if actual_evidence_sha != record.evidence_sha256:
            raise ProvenanceError(f"{field} evidence bytes digest mismatch")
        try:
            envelope = json.loads(record.evidence_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProvenanceError(f"{field} evidence envelope malformed") from exc
        expected = {
            "evidence_id": record.evidence_id,
            "owner": record.owner,
            "subject": record.subject,
            "scope": SYNTHETIC_SCOPE,
            "value_sha256": _sha(asdict(binding.value)),
        }
        if envelope != expected or record.value_sha256 != expected["value_sha256"]:
            raise ProvenanceError(f"{field} evidence does not bind the supplied value")


def validate_process_role(process: ProcessIdentity) -> None:
    """Validate the fixture role/rank pair, including the legitimate coordinator."""
    if not isinstance(process, ProcessIdentity):
        raise ProvenanceError("typed process identity required")
    _positive(process.rank, "MPI rank", zero=True)
    if process.role == "COORDINATOR" and process.rank != 0:
        raise ProvenanceError("coordinator role requires rank 0")
    if process.role == "WORKER" and process.rank == 0:
        raise ProvenanceError("worker role cannot use coordinator rank 0")
    if process.role not in {"COORDINATOR", "WORKER"}:
        raise ProvenanceError("unknown process role")


def validate_invocation(context: InvocationContext, resolver: EvidenceResolver) -> str:
    """Validate structure and fixture evidence; never returns production authority."""
    if not isinstance(context, InvocationContext):
        raise ProvenanceError("typed InvocationContext required")
    _verify_evidence(context, resolver)
    run = context.run.value
    proc = context.process.value
    assignment = context.assignment.value
    call = context.call.value
    state = context.effective_state.value
    impl = context.implementation.value
    dof = context.dof.value
    system = context.system.value

    for value, label in ((run.run_uuid, "run UUID"), (run.attempt_uuid, "attempt UUID"),
                         (proc.communicator_uuid, "communicator UUID")):
        try:
            UUID(value)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ProvenanceError(f"{label} malformed") from exc
    if not isinstance(run.job_execution_id, str) or not run.job_execution_id or not isinstance(proc.host_id, str) or not proc.host_id:
        raise ProvenanceError("run/process identity incomplete")
    _positive(proc.pid, "process id")
    validate_process_role(proc)
    _positive(proc.communicator_epoch, "communicator epoch", zero=True)
    if proc.role == "COORDINATOR" or proc.rank == 0:
        raise ProvenanceError("rank 0 is a valid MPI coordinator but not a worker FEM invocation")
    for value, label in ((assignment.sequence, "assignment sequence"),
                         (assignment.sender_rank, "assignment sender"),
                         (assignment.destination_rank, "assignment destination"),
                         (assignment.mpi_tag, "MPI tag"),
                         (assignment.local_modnum, "local ModNum")):
        _positive(value, label, zero=label in {"assignment sender", "MPI tag"})
    if assignment.destination_rank != proc.rank:
        raise ProvenanceError("assignment destination does not match worker rank")
    if assignment.mpi_tag != assignment.local_modnum:
        raise ProvenanceError("ModNum does not match received MPI tag")
    if not isinstance(assignment.model_id, str) or not assignment.model_id:
        raise ProvenanceError("stable model identity missing")
    _hash_ok(assignment.model_definition_sha256, "model definition")

    if call.shells_phase not in {"SH", "SF"}:
        raise ProvenanceError("Shells phase must be SH or SF")
    for value, label in ((call.shells_call_sequence, "Shells call sequence"),
                         (call.pure_call_sequence, "Pure call sequence"),
                         (call.pure_iteration, "Pure iteration"),
                         (call.fem_ordinal, "FEM ordinal")):
        _positive(value, label)
    _positive(call.max_iter, "MaxIter", zero=True)
    _positive(call.rpeat, "rpeat", zero=True)
    if call.shells_phase == "SH" and call.rpeat == 0:
        raise ProvenanceError("rpeat=0 is invalid for SH")
    if call.shells_phase == "SF":
        if call.max_iter == 0 and call.rpeat != 0:
            raise ProvenanceError("SF with MaxIter=0 requires source-valid rpeat=0")
        if call.max_iter > 0 and call.rpeat == 0:
            raise ProvenanceError("SF with MaxIter>0 requires a positive rpeat")

    for item, label in ((state.input_manifest_sha256, "input manifest"),
                        (state.variable_vector_sha256, "effective variable vector"),
                        (state.constraints_sha256, "resolved constraints"),
                        (impl.source_lock_sha256, "source lock"),
                        (impl.candidate_tree_sha256, "candidate source tree"),
                        (impl.build_record_sha256, "build record"),
                        (impl.executable_sha256, "executable"),
                        (dof.feg_sha256, "FEG"), (dof.runtime_sha256, "runtime"),
                        (dof.permutation_manifest_sha256, "DOF permutation"),
                        (system.a0b0_sha256, "A0/b0")):
        _hash_ok(item, label)
    if not isinstance(state.state_id, str) or not state.state_id or not isinstance(dof.ordering_id, str) or not dof.ordering_id:
        raise ProvenanceError("state or DOF ordering identity missing")
    if system.capture_point != "POST_VBCS_PRE_SOLVER":
        raise ProvenanceError("capture point must be post-VBCs and pre-Solver")
    _positive(system.n, "matrix dimension")
    for value, label in ((system.kl, "KL"), (system.ku, "KU")):
        _positive(value, label, zero=True)
    if system.kl >= system.n or system.ku >= system.n:
        raise ProvenanceError("bandwidth must be smaller than dimension")
    return invocation_key(context)


class InvocationLedger:
    """In-memory uniqueness guard scoped to one synthetic run fixture."""

    def __init__(self) -> None:
        self._invocations: set[str] = set()
        self._assignments: dict[tuple[str, str, int], str] = {}

    def register(self, context: InvocationContext, resolver: EvidenceResolver) -> str:
        key = validate_invocation(context, resolver)
        run = context.run.value
        assignment = context.assignment.value
        assignment_key = (run.run_uuid, run.attempt_uuid, assignment.sequence)
        assignment_binding = _assignment_binding_key(context, resolver)
        prior_binding = self._assignments.get(assignment_key)
        if prior_binding is not None and prior_binding != assignment_binding:
            raise ProvenanceError("conflicting reuse of master assignment sequence binding")
        coordinate = invocation_coordinate_key(context)
        if coordinate in self._invocations:
            raise ProvenanceError("duplicate FEM invocation coordinates")
        # Mutate only after every identity and uniqueness check has passed.
        self._invocations.add(coordinate)
        self._assignments[assignment_key] = assignment_binding
        return key


def verify_sidecar(
    *,
    payload: bytes,
    sidecar: SnapshotSidecar,
    context: InvocationContext,
    key: str,
    oracle_ab: Sequence[Sequence[float]],
    oracle_b0: Sequence[float],
) -> dict[str, object]:
    if not isinstance(sidecar, SnapshotSidecar):
        raise ProvenanceError("typed snapshot sidecar required")
    system = context.system.value
    dof = context.dof.value
    if (isinstance(sidecar.schema_version, bool) or not isinstance(sidecar.schema_version, int) or
            sidecar.schema_version != 1 or sidecar.scope != SYNTHETIC_SCOPE):
        raise ProvenanceError("sidecar schema/scope is not an accepted synthetic fixture")
    if sidecar.invocation_key != key:
        raise ProvenanceError("sidecar invocation key mismatch")
    _positive(sidecar.payload_bytes, "sidecar payload byte count")
    for value, label, allow_zero in ((sidecar.n, "sidecar dimension", False),
                                     (sidecar.kl, "sidecar KL", True),
                                     (sidecar.ku, "sidecar KU", True)):
        _positive(value, label, zero=allow_zero)
    if sidecar.payload_bytes != len(payload):
        raise ProvenanceError("sidecar payload byte count mismatch")
    if sidecar.payload_sha256 != hashlib.sha256(payload).hexdigest():
        raise ProvenanceError("sidecar payload digest mismatch")
    if (sidecar.source_value_sha256 != system.a0b0_sha256 or
            (sidecar.n, sidecar.kl, sidecar.ku) != (system.n, system.kl, system.ku) or
            sidecar.dof_ordering_id != dof.ordering_id):
        raise ProvenanceError("sidecar system/DOF binding mismatch")
    return verify_capture_payload(
        payload,
        expected_payload_sha256=sidecar.payload_sha256,
        expected_source_sha256=sidecar.source_value_sha256,
        oracle_ab=oracle_ab,
        oracle_b0=oracle_b0,
        kl=sidecar.kl,
        ku=sidecar.ku,
    )


def run_capture_only_gate(
    *,
    context: InvocationContext,
    resolver: EvidenceResolver,
    ledger: InvocationLedger,
    write_payload: Callable[[], bytes],
    sidecar: SnapshotSidecar,
    oracle_ab: Sequence[Sequence[float]],
    oracle_b0: Sequence[float],
) -> CaptureOutcome:
    """Simulate a diagnostic gate: every capture outcome stops before Solver."""
    key: str | None = None
    try:
        key = ledger.register(context, resolver)
        payload = write_payload()
        if not isinstance(payload, bytes):
            raise ProvenanceError("writer did not return immutable payload bytes")
        verified = verify_sidecar(
            payload=payload, sidecar=sidecar, context=context, key=key,
            oracle_ab=oracle_ab, oracle_b0=oracle_b0,
        )
        if verified.get("status") != "SYNTHETIC_SNAPSHOT_VERIFIED_AGAINST_INDEPENDENT_ORACLE":
            raise ProvenanceError("independent payload verifier did not accept fixture")
        outcome = CaptureOutcome(CAPTURE_ONLY_STOP, key, verified["payload_sha256"], UNKNOWN_AUTHORITY, False)
        require_capture_terminal(outcome)
        return outcome
    except Exception as exc:
        # Capture failure is terminal by design. No path invokes the mock Solver.
        outcome = CaptureOutcome(CAPTURE_FAILED, key, None, UNKNOWN_AUTHORITY, False, str(exc))
        require_capture_terminal(outcome)
        return outcome


def coordinate_synthetic_workers(outcomes: Sequence[CaptureOutcome]) -> str:
    """Model coordinated fixture stop; does not prove MPI/runtime semantics."""
    if not outcomes:
        raise ProvenanceError("worker outcome set must not be empty")
    if any(item.status != CAPTURE_ONLY_STOP or item.solver_entered for item in outcomes):
        return CAPTURE_FAILED
    return CAPTURE_ONLY_STOP


__all__ = [
    "AssignmentIdentity", "CallIdentity", "CaptureOutcome", "DofIdentity",
    "EffectiveStateIdentity", "EvidenceRecord", "ImplementationIdentity",
    "InvocationContext", "InvocationLedger", "MappingEvidenceResolver",
    "ProcessIdentity", "ProvenanceError", "RunIdentity", "SnapshotSidecar",
    "SystemIdentity", "Owned", "CAPTURE_FAILED", "CAPTURE_ONLY_STOP",
    "INVOCATION_VALID", "SYNTHETIC_SCOPE", "UNKNOWN_AUTHORITY",
    "CAPTURE_TERMINAL_RETURN", "coordinate_synthetic_workers", "invocation_coordinate_key", "invocation_key",
    "require_capture_terminal", "run_capture_only_gate",
    "validate_invocation", "validate_process_role", "verify_sidecar",
]

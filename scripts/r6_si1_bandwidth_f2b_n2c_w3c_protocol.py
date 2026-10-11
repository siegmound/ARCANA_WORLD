"""Deterministic synthetic model of the W3-C capture-only coordinator protocol.

This is an event/state model, not an MPI implementation. All accepted fixture
records remain SYNTHETIC_FIXTURE_ONLY and runtime authority remains UNKNOWN.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re
from typing import Callable
from uuid import UUID

from scripts.r6_si1_bandwidth_f2b_n2c_w3b_provenance import (
    CallIdentity, SYNTHETIC_SCOPE,
)


CAPTURE_ONLY = "CAPTURE_ONLY"
DECISION_FROZEN = "DECISION_FROZEN"
AGREEMENT_COMPLETE = "ALL_RANKS_AGREED"
ACK_COMPLETE = "ACKNOWLEDGEMENT_COMPLETE"
ASSIGNMENT_DISPATCHED = "ASSIGNMENT_DISPATCHED"
CAPTURE_WRITTEN = "CAPTURE_WRITTEN"
WORKER_TERMINALS_COLLECTED = "WORKER_TERMINALS_COLLECTED"
COORDINATED_TERMINAL = "COORDINATED_TERMINAL"
JOB_TERMINATED = "JOB_TERMINATED"
CAPTURE_VERIFIED = "CAPTURE_VERIFIED"
GLOBAL_FAILURE = "GLOBAL_FAILURE"
UNKNOWN = "UNKNOWN"

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ProtocolError(ValueError):
    """Invalid or out-of-order synthetic protocol event."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def decision_digest(decision: "CaptureDecision", *, include_digest: bool = False) -> str:
    payload = decision.canonical_record()
    if not include_digest:
        payload.pop("decision_sha256", None)
    return hashlib.sha256(b"ARCANA-N2C-W3C-DECISION-V1\0" + _canonical(payload)).hexdigest()


@dataclass(frozen=True)
class CaptureDecision:
    run_uuid: str
    attempt_uuid: str
    job_execution_id: str
    communicator_uuid: str
    communicator_epoch: int
    roster: tuple[int, ...]
    mode: str
    solver_permitted: bool
    assignment_sequence: int
    model_id: str
    model_definition_sha256: str
    worker_rank: int
    target: CallIdentity
    pure_max_iterations: int
    sf_final_guard_confirmed: bool
    first_shells_call: bool
    first_pure_call: bool
    first_pure_iteration: bool
    first_fem_invocation: bool
    prior_fem_solver_invocations: int
    terminal_policy: str
    failure_policy: str
    authority_scope: str
    decision_sha256: str

    def canonical_record(self) -> dict[str, object]:
        return {
            "run_uuid": self.run_uuid, "attempt_uuid": self.attempt_uuid,
            "job_execution_id": self.job_execution_id,
            "communicator_uuid": self.communicator_uuid,
            "communicator_epoch": self.communicator_epoch, "roster": list(self.roster),
            "mode": self.mode, "solver_permitted": self.solver_permitted,
            "assignment_sequence": self.assignment_sequence, "model_id": self.model_id,
            "model_definition_sha256": self.model_definition_sha256,
            "worker_rank": self.worker_rank, "target": self.target.__dict__,
            "pure_max_iterations": self.pure_max_iterations,
            "sf_final_guard_confirmed": self.sf_final_guard_confirmed,
            "first_shells_call": self.first_shells_call,
            "first_pure_call": self.first_pure_call,
            "first_pure_iteration": self.first_pure_iteration,
            "first_fem_invocation": self.first_fem_invocation,
            "prior_fem_solver_invocations": self.prior_fem_solver_invocations,
            "terminal_policy": self.terminal_policy,
            "failure_policy": self.failure_policy,
            "authority_scope": self.authority_scope,
            "decision_sha256": self.decision_sha256,
        }


def freeze_decision(**fields: object) -> CaptureDecision:
    """Build a digest-sealed immutable decision record for synthetic testing."""
    decision = CaptureDecision(decision_sha256="", **fields)  # type: ignore[arg-type]
    return replace(decision, decision_sha256=decision_digest(decision))


def validate_decision(d: CaptureDecision) -> None:
    if not isinstance(d, CaptureDecision) or not isinstance(d.target, CallIdentity):
        raise ProtocolError("typed capture decision required")
    for name, value in (("run_uuid", d.run_uuid), ("attempt_uuid", d.attempt_uuid),
                        ("communicator_uuid", d.communicator_uuid)):
        try:
            UUID(value)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ProtocolError(f"invalid {name}") from exc
    if not d.job_execution_id or d.mode != CAPTURE_ONLY or d.solver_permitted is not False:
        raise ProtocolError("decision must be immutable CAPTURE_ONLY with Solver forbidden")
    if d.authority_scope != SYNTHETIC_SCOPE:
        raise ProtocolError("production authority is UNKNOWN to this offline model")
    if (type(d.roster) is not tuple or not d.roster or
            any(type(rank) is not int or rank < 0 for rank in d.roster)):
        raise ProtocolError("invalid communicator roster")
    if tuple(sorted(set(d.roster))) != d.roster or d.roster[0] != 0:
        raise ProtocolError("roster must be fixed, unique, ascending and include coordinator rank 0")
    if d.worker_rank == 0 or d.worker_rank not in d.roster:
        raise ProtocolError("selected target must be one nonzero worker in the fixed roster")
    if (type(d.communicator_epoch) is not int or d.communicator_epoch < 0 or
            type(d.assignment_sequence) is not int or d.assignment_sequence < 1 or
            not d.model_id or not _SHA256.fullmatch(d.model_definition_sha256)):
        raise ProtocolError("incomplete assignment or communicator identity")
    bool_fields = (d.sf_final_guard_confirmed, d.first_shells_call, d.first_pure_call,
                   d.first_pure_iteration, d.first_fem_invocation)
    if any(type(value) is not bool for value in bool_fields):
        raise ProtocolError("reachability and call-path facts must be explicit booleans")
    t = d.target
    if t.shells_phase not in {"SH", "SF"}:
        raise ProtocolError("invalid SH/SF phase")
    if any(type(x) is not int for x in (t.shells_call_sequence, t.rpeat, t.max_iter,
                                         t.pure_call_sequence, t.pure_iteration,
                                         t.fem_ordinal, d.pure_max_iterations,
                                         d.prior_fem_solver_invocations)):
        raise ProtocolError("call coordinates must be integers, not booleans")
    if min(t.shells_call_sequence, t.pure_call_sequence, t.pure_iteration,
           t.fem_ordinal, d.pure_max_iterations) < 1 or d.prior_fem_solver_invocations != 0:
        raise ProtocolError("target is not the first source-reachable FEM invocation")
    if not all((d.first_shells_call, d.first_pure_call, d.first_pure_iteration,
                d.first_fem_invocation)):
        raise ProtocolError("capture-only target must be the first reachable call at every level")
    if t.pure_iteration != 1 or t.fem_ordinal != 1:
        raise ProtocolError("capture-only cannot pass a prior FEM/Solver to reach target")
    if t.shells_phase == "SH":
        if t.max_iter < 1 or t.rpeat != 1 or t.shells_call_sequence != 1:
            raise ProtocolError("SH target requires first SH call, positive MaxIter and rpeat=1")
    else:
        if not d.sf_final_guard_confirmed:
            raise ProtocolError("SF FEM reachability guard is UNKNOWN")
        if t.max_iter != 0 or t.rpeat != 0 or t.shells_call_sequence != 1:
            raise ProtocolError("capture-only SF is reachable only as the first Shells call with outer MaxIter=0 and rpeat=0")
    if d.terminal_policy != "ALL_RANKS_TERMINAL_THEN_JOB_EXIT_THEN_EXTERNAL_VERIFY":
        raise ProtocolError("unsupported terminal policy")
    if d.failure_policy != "FAIL_CLOSED_GLOBAL_FAILURE_OR_UNKNOWN_NO_SOLVER":
        raise ProtocolError("unsupported failure policy")
    if not _SHA256.fullmatch(d.decision_sha256) or d.decision_sha256 != decision_digest(d):
        raise ProtocolError("decision digest mismatch")


@dataclass(frozen=True)
class Acknowledgement:
    rank: int
    run_uuid: str
    attempt_uuid: str
    communicator_uuid: str
    communicator_epoch: int
    decision_sha256: str
    origin: str  # rank 0 is LOCAL_COORDINATOR; nonzero ranks are RECEIVED_WORKER


@dataclass(frozen=True)
class TerminalStatus:
    rank: int
    status: str  # CAPTURE_WRITTEN, IDLE_STOPPED, or FAILURE
    solver_entered: bool
    payload_complete: bool = False
    run_uuid: str | None = None
    attempt_uuid: str | None = None
    communicator_uuid: str | None = None
    communicator_epoch: int | None = None
    decision_sha256: str | None = None


@dataclass(frozen=True)
class ProtocolState:
    decision: CaptureDecision
    phase: str = "UNVALIDATED"
    no_solver_ranks: tuple[int, ...] = ()
    acknowledgements: tuple[Acknowledgement, ...] = ()
    dispatched_sequences: tuple[int, ...] = ()
    capture_count: int = 0
    terminal_statuses: tuple[TerminalStatus, ...] = ()
    coordinator_local_ack: bool = False
    job_exit_code: int | None = None
    external_verification: str = "PENDING"
    runtime_authority: str = "UNKNOWN"
    failure: str | None = None
    solver_mock_entries: int = 0

    def fail(self, reason: str, *, unknown: bool = False) -> "ProtocolState":
        return replace(self, phase=UNKNOWN if unknown else GLOBAL_FAILURE,
                       no_solver_ranks=self.decision.roster, failure=reason,
                       external_verification="PENDING", runtime_authority="UNKNOWN")

    def freeze(self) -> "ProtocolState":
        if self.phase != "UNVALIDATED":
            return self.fail("capture decision cannot be refrozen or protocol state reopened")
        try:
            validate_decision(self.decision)
        except (ProtocolError, TypeError) as exc:
            return self.fail(str(exc))
        return replace(self, phase=DECISION_FROZEN, no_solver_ranks=self.decision.roster)

    def acknowledge(self, ack: Acknowledgement) -> "ProtocolState":
        if self.phase not in {DECISION_FROZEN, AGREEMENT_COMPLETE, ACK_COMPLETE}:
            return self.fail("ACK outside frozen-decision phase")
        if not isinstance(ack, Acknowledgement) or type(ack.rank) is not int:
            return self.fail("typed acknowledgement with integer rank required")
        d = self.decision
        if (ack.run_uuid, ack.attempt_uuid, ack.communicator_uuid, ack.communicator_epoch,
                ack.decision_sha256) != (d.run_uuid, d.attempt_uuid, d.communicator_uuid,
                                         d.communicator_epoch, d.decision_sha256):
            return self.fail("stale or mismatched decision acknowledgement")
        if ack.rank not in d.roster:
            return self.fail("ACK from rank outside roster")
        expected_origin = "LOCAL_COORDINATOR" if ack.rank == 0 else "RECEIVED_WORKER"
        if ack.origin != expected_origin:
            return self.fail("coordinator local ACK must be distinct from received worker ACK")
        if any(old.rank == ack.rank for old in self.acknowledgements):
            return self.fail("duplicate or conflicting rank ACK")
        acks = self.acknowledgements + (ack,)
        local = self.coordinator_local_ack or ack.rank == 0
        phase = AGREEMENT_COMPLETE if len(acks) == len(d.roster) else DECISION_FROZEN
        return replace(self, acknowledgements=acks, coordinator_local_ack=local, phase=phase)

    def dispatch(self, *, rank: int, assignment_sequence: int, model_id: str) -> "ProtocolState":
        if self.phase != ACK_COMPLETE or len(self.acknowledgements) != len(self.decision.roster):
            return self.fail("assignment dispatch before unanimous decision ACK")
        d = self.decision
        if type(rank) is not int or type(assignment_sequence) is not int or not isinstance(model_id, str):
            return self.fail("typed assignment dispatch fields required")
        if (rank, assignment_sequence, model_id) != (d.worker_rank, d.assignment_sequence, d.model_id):
            return self.fail("unauthorized or conflicting assignment dispatch")
        if self.dispatched_sequences:
            return self.fail("duplicate assignment dispatch")
        return replace(self, phase=ASSIGNMENT_DISPATCHED,
                       dispatched_sequences=(assignment_sequence,))

    def complete_acknowledgement(self) -> "ProtocolState":
        if (self.phase != AGREEMENT_COMPLETE or not self.coordinator_local_ack or
                len(self.acknowledgements) != len(self.decision.roster) or
                {ack.rank for ack in self.acknowledgements} != set(self.decision.roster)):
            return self.fail("acknowledgement set incomplete or coordinator-local ACK missing")
        return replace(self, phase=ACK_COMPLETE)

    def capture(self, *, rank: int, target: CallIdentity, payload_complete: bool,
                verification_status: str = "PENDING", run_uuid: str | None = None,
                attempt_uuid: str | None = None, communicator_uuid: str | None = None,
                communicator_epoch: int | None = None,
                decision_sha256: str | None = None) -> "ProtocolState":
        if self.phase != ASSIGNMENT_DISPATCHED:
            return self.fail("capture outside dispatched target phase")
        d = self.decision
        if (run_uuid, attempt_uuid, communicator_uuid, communicator_epoch, decision_sha256) != (
                d.run_uuid, d.attempt_uuid, d.communicator_uuid, d.communicator_epoch,
                d.decision_sha256):
            return self.fail("stale or mismatched capture event")
        if type(rank) is not int or rank != self.decision.worker_rank or target != self.decision.target:
            return self.fail("wrong or duplicate FEM target")
        if self.capture_count:
            return self.fail("duplicate target completion")
        if payload_complete is not True or verification_status != "PENDING":
            return self.fail("partial payload or premature/failed verification")
        return replace(self, phase=CAPTURE_WRITTEN, capture_count=1)

    def terminal(self, status: TerminalStatus) -> "ProtocolState":
        if self.phase not in {CAPTURE_WRITTEN, WORKER_TERMINALS_COLLECTED}:
            return self.fail("terminal status before target capture")
        if (not isinstance(status, TerminalStatus) or type(status.rank) is not int or
                type(status.solver_entered) is not bool or type(status.payload_complete) is not bool):
            return self.fail("typed terminal status with explicit boolean facts required")
        d = self.decision
        if (status.run_uuid, status.attempt_uuid, status.communicator_uuid,
                status.communicator_epoch, status.decision_sha256) != (
                d.run_uuid, d.attempt_uuid, d.communicator_uuid, d.communicator_epoch,
                d.decision_sha256):
            return self.fail("stale or mismatched terminal status")
        if status.rank not in self.decision.roster or any(s.rank == status.rank for s in self.terminal_statuses):
            return self.fail("unexpected or duplicate terminal status")
        if status.solver_entered is not False:
            return self.fail("Solver entry observed under no-Solver latch")
        if status.rank == self.decision.worker_rank:
            if status.status != "CAPTURE_WRITTEN" or status.payload_complete is not True:
                return self.fail("selected worker lacks complete capture terminal")
        elif status.status != "IDLE_STOPPED":
            return self.fail("non-target rank has unexpected terminal status")
        statuses = self.terminal_statuses + (status,)
        phase = WORKER_TERMINALS_COLLECTED if len(statuses) == len(self.decision.roster) else CAPTURE_WRITTEN
        return replace(self, phase=phase, terminal_statuses=statuses)

    def coordinate_stop(self) -> "ProtocolState":
        if self.phase != WORKER_TERMINALS_COLLECTED:
            return self.fail("cannot decide coordinated terminal state before every rank is accounted")
        if (self.capture_count != 1 or len(self.terminal_statuses) != len(self.decision.roster) or
                any(s.solver_entered for s in self.terminal_statuses)):
            return self.fail("success invariants not satisfied")
        return replace(self, phase=COORDINATED_TERMINAL)

    def report_job_exit(self, exit_code: int) -> "ProtocolState":
        if self.phase != COORDINATED_TERMINAL or type(exit_code) is not int or exit_code != 0:
            return self.fail("job exit missing, nonzero, or reported before coordinated terminal")
        return replace(self, phase=JOB_TERMINATED, job_exit_code=exit_code)

    def verify_external(self, *, passed: bool) -> "ProtocolState":
        if self.phase != JOB_TERMINATED:
            return self.fail("external verification must occur after modeled job termination")
        if passed is not True:
            return self.fail("independent payload verification failed")
        return replace(self, phase=CAPTURE_VERIFIED, external_verification="SYNTHETIC_PASS",
                       runtime_authority="UNKNOWN")

    def solver_dispatch_boundary(self, rank: int, mock_solver: Callable[[], None]) -> "ProtocolState":
        """Check the latch at the boundary; the mock is reachable only if permitted."""
        if type(rank) is not int or rank not in self.decision.roster or not callable(mock_solver):
            return self.fail("Solver attempt from rank outside roster")
        # This model represents capture-only exclusively. Even malformed or
        # pre-freeze states cannot dispatch the callback.
        return self.fail("Solver entry attempt blocked by monotonic no-Solver latch")

    def attempt_clear_no_solver_latch(self, rank: int) -> "ProtocolState":
        if type(rank) is not int or rank not in self.decision.roster:
            return self.fail("latch mutation from rank outside roster")
        return self.fail("no-Solver latch is monotonic and cannot be cleared")

    def timeout(self, reason: str) -> "ProtocolState":
        return self.fail(reason or "protocol timeout", unknown=True)

    def crash(self, rank: int, reason: str) -> "ProtocolState":
        if rank not in self.decision.roster:
            return self.fail("crash report from rank outside roster")
        return self.fail(reason or "rank crashed without terminal status", unknown=True)


def drive_valid_fixture(state: ProtocolState) -> ProtocolState:
    """Convenience driver for deterministic unit fixtures, not an MPI runtime."""
    d = state.decision
    state = state.freeze()
    for rank in d.roster:
        origin = "LOCAL_COORDINATOR" if rank == 0 else "RECEIVED_WORKER"
        state = state.acknowledge(Acknowledgement(rank, d.run_uuid, d.attempt_uuid,
            d.communicator_uuid, d.communicator_epoch, d.decision_sha256, origin))
    if state.phase != AGREEMENT_COMPLETE:
        return state
    state = state.complete_acknowledgement()
    state = state.dispatch(rank=d.worker_rank, assignment_sequence=d.assignment_sequence,
                           model_id=d.model_id)
    state = state.capture(rank=d.worker_rank, target=d.target, payload_complete=True,
                          run_uuid=d.run_uuid, attempt_uuid=d.attempt_uuid,
                          communicator_uuid=d.communicator_uuid,
                          communicator_epoch=d.communicator_epoch,
                          decision_sha256=d.decision_sha256)
    for rank in d.roster:
        status = "CAPTURE_WRITTEN" if rank == d.worker_rank else "IDLE_STOPPED"
        state = state.terminal(TerminalStatus(rank, status, False, rank == d.worker_rank,
            d.run_uuid, d.attempt_uuid, d.communicator_uuid, d.communicator_epoch,
            d.decision_sha256))
    return state.coordinate_stop()


__all__ = [
    "Acknowledgement", "ACK_COMPLETE", "AGREEMENT_COMPLETE", "ASSIGNMENT_DISPATCHED", "CAPTURE_ONLY",
    "CAPTURE_VERIFIED", "CAPTURE_WRITTEN", "CaptureDecision", "COORDINATED_TERMINAL",
    "DECISION_FROZEN", "GLOBAL_FAILURE", "JOB_TERMINATED", "ProtocolError",
    "ProtocolState", "TerminalStatus", "UNKNOWN", "WORKER_TERMINALS_COLLECTED",
    "decision_digest", "drive_valid_fixture", "freeze_decision", "validate_decision",
]

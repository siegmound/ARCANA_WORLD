from __future__ import annotations

from dataclasses import replace
import hashlib
import json

import pytest

from scripts.r6_si1_bandwidth_f2b_n2a_snapshot import encode_snapshot
from scripts.r6_si1_bandwidth_f2b_n2c_capture_verify import canonical_oracle_sha256
from scripts.r6_si1_bandwidth_f2b_n2c_w3b_provenance import (
    AssignmentIdentity, CallIdentity, DofIdentity, EffectiveStateIdentity,
    EvidenceRecord, ImplementationIdentity, InvocationContext, InvocationLedger,
    MappingEvidenceResolver, Owned, ProcessIdentity, ProvenanceError,
    RunIdentity, SnapshotSidecar, SystemIdentity, CAPTURE_FAILED,
    CAPTURE_ONLY_STOP, UNKNOWN_AUTHORITY, coordinate_synthetic_workers,
    run_capture_only_gate, validate_invocation, validate_process_role,
)


def _fixture(*, phase="SH", rpeat=1, max_iter=2):
    values = {
        "run": RunIdentity("12345678-1234-5678-1234-567812345678", "22345678-1234-5678-1234-567812345678", "fixture-job-1"),
        "process": ProcessIdentity("32345678-1234-5678-1234-567812345678", 0, "fixture-host", 4321, 1, "WORKER"),
        "assignment": AssignmentIdentity(1, 0, 1, 7, 7, "fixture-model-a", "a" * 64),
        "call": CallIdentity(phase, 1, rpeat, max_iter, 1, 1, 1),
        "effective_state": EffectiveStateIdentity("b" * 64, "c" * 64, "fixture-state-1", "d" * 64),
        "implementation": ImplementationIdentity("e" * 64, "f" * 64, "1" * 64, "2" * 64),
        "dof": DofIdentity("fixture-dof-order", "3" * 64, "4" * 64, "5" * 64),
        "system": SystemIdentity("POST_VBCS_PRE_SOLVER", 4, 1, 2, "0" * 64),
    }
    owners = {
        "run": ("RUN_ORCHESTRATOR_FIXTURE", "run"),
        "process": ("COMMUNICATOR_FIXTURE", "process"),
        "assignment": ("MASTER_DISPATCH_FIXTURE", "assignment"),
        "call": ("CALL_TRACE_FIXTURE", "call"),
        "effective_state": ("INPUT_STATE_FIXTURE", "effective_state"),
        "implementation": ("BUILD_PROVENANCE_FIXTURE", "implementation"),
        "dof": ("DOF_PROVENANCE_FIXTURE", "dof"),
        "system": ("SYSTEM_CAPTURE_FIXTURE", "system"),
    }
    refs = {}
    records = {}
    for name, value in values.items():
        evidence_id = f"fixture:{name}:1"
        digest = hashlib.sha256(json.dumps(value.__dict__, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        owner, subject = owners[name]
        envelope = json.dumps({"evidence_id": evidence_id, "owner": owner, "subject": subject,
                               "scope": "SYNTHETIC_FIXTURE_ONLY", "value_sha256": digest},
                              sort_keys=True, separators=(",", ":")).encode()
        records[evidence_id] = EvidenceRecord(evidence_id, owner, subject, digest,
                                               "SYNTHETIC_FIXTURE_ONLY", envelope,
                                               hashlib.sha256(envelope).hexdigest())
        refs[name] = Owned(value, evidence_id)
    context = InvocationContext(**refs)
    oracle_ab, _, oracle_b0, oracle_kl, oracle_ku = _system()
    values["system"] = replace(values["system"], a0b0_sha256=canonical_oracle_sha256(
        oracle_ab, oracle_b0, kl=oracle_kl, ku=oracle_ku))
    value = values["system"]
    evidence_id = refs["system"].evidence_id
    digest = hashlib.sha256(json.dumps(value.__dict__, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    owner, subject = owners["system"]
    envelope = json.dumps({"evidence_id": evidence_id, "owner": owner, "subject": subject,
                           "scope": "SYNTHETIC_FIXTURE_ONLY", "value_sha256": digest},
                          sort_keys=True, separators=(",", ":")).encode()
    records[evidence_id] = EvidenceRecord(evidence_id, owner, subject, digest,
                                           "SYNTHETIC_FIXTURE_ONLY", envelope,
                                           hashlib.sha256(envelope).hexdigest())
    refs["system"] = Owned(value, evidence_id)
    context = InvocationContext(**refs)
    resolver = MappingEvidenceResolver(records)
    return context, resolver, records


def _system():
    # Mathematical row/column indexing: asymmetric KL=1, KU=2.
    n, kl, ku = 4, 1, 2
    ldab = 2 * kl + ku + 1
    ab = [[0.0] * n for _ in range(ldab)]
    diagonal = kl + ku
    dense = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(max(0, i - kl), min(n, i + ku + 1)):
            value = float(10 * (i + 1) + j + 1)
            ab[diagonal + i - j][j] = value
            dense[i][j] = value
    b0 = (1.25, -2.5, 3.75, 4.0)
    return ab, dense, b0, kl, ku


def _sidecar(context, resolver, payload):
    key = validate_invocation(context, resolver)
    oracle_ab, _, b0, kl, ku = _system()
    return SnapshotSidecar(1, "SYNTHETIC_FIXTURE_ONLY", key,
                           hashlib.sha256(payload).hexdigest(), len(payload),
                           canonical_oracle_sha256(oracle_ab, b0, kl=kl, ku=ku),
                           len(b0), kl, ku, context.dof.value.ordering_id)


def test_positive_owner_backed_fixture_and_capture_stops_before_solver():
    context, resolver, _ = _fixture()
    ab, _, b0, kl, ku = _system()
    captured_ab = [row[:] for row in ab]
    captured_b = list(b0)
    payload = encode_snapshot(captured_ab, captured_b, kl=kl, ku=ku).data
    sidecar = _sidecar(context, resolver, payload)
    calls = []
    result = run_capture_only_gate(context=context, resolver=resolver,
        ledger=InvocationLedger(), write_payload=lambda: payload, sidecar=sidecar,
        oracle_ab=ab, oracle_b0=b0, mock_solver_entry=lambda: calls.append("solver"))
    assert result.status == CAPTURE_ONLY_STOP
    assert result.runtime_authority == UNKNOWN_AUTHORITY
    assert result.solver_entered is False and calls == []


def test_rank_zero_is_valid_coordinator_but_not_fem_worker():
    coordinator = ProcessIdentity("32345678-1234-5678-1234-567812345678", 0, "fixture-host", 10, 0, "COORDINATOR")
    validate_process_role(coordinator)
    context, resolver, _ = _fixture()
    bad = replace(context, process=Owned(coordinator, context.process.evidence_id))
    _, _, records = _fixture()
    record = records[context.process.evidence_id]
    value_sha = hashlib.sha256(json.dumps(coordinator.__dict__, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    envelope = json.dumps({"evidence_id": record.evidence_id, "owner": record.owner,
                           "subject": record.subject, "scope": record.scope,
                           "value_sha256": value_sha}, sort_keys=True, separators=(",", ":")).encode()
    records[record.evidence_id] = replace(record, value_sha256=value_sha, evidence_bytes=envelope,
                                           evidence_sha256=hashlib.sha256(envelope).hexdigest())
    with pytest.raises(ProvenanceError, match="not a worker FEM"):
        validate_invocation(bad, MappingEvidenceResolver(records))


@pytest.mark.parametrize("field,value", [
    ("assignment", AssignmentIdentity(1, 0, 2, 7, 7, "fixture-model-a", "a" * 64)),
    ("effective_state", EffectiveStateIdentity("b" * 64, "c" * 64, "changed-state", "d" * 64)),
    ("dof", DofIdentity("fixture-dof-order", "3" * 64, "4" * 64, "0" * 64)),
])
def test_owner_binding_mismatch_fails_closed(field, value):
    context, resolver, _ = _fixture()
    changed = replace(context, **{field: Owned(value, getattr(context, field).evidence_id)})
    with pytest.raises(ProvenanceError):
        validate_invocation(changed, resolver)


def test_owner_endorsed_assignment_to_wrong_worker_still_fails_semantically():
    context, _, records = _fixture()
    assignment = replace(context.assignment.value, destination_rank=2)
    record = records[context.assignment.evidence_id]
    digest = hashlib.sha256(json.dumps(assignment.__dict__, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    envelope = json.dumps({"evidence_id": record.evidence_id, "owner": record.owner,
                           "subject": record.subject, "scope": record.scope,
                           "value_sha256": digest}, sort_keys=True, separators=(",", ":")).encode()
    records[record.evidence_id] = replace(record, value_sha256=digest, evidence_bytes=envelope,
                                           evidence_sha256=hashlib.sha256(envelope).hexdigest())
    context = replace(context, assignment=Owned(assignment, context.assignment.evidence_id))
    with pytest.raises(ProvenanceError, match="destination does not match"):
        validate_invocation(context, MappingEvidenceResolver(records))


def test_missing_owner_evidence_and_tampered_evidence_fail_closed():
    context, resolver, records = _fixture()
    missing = replace(context, run=Owned(context.run.value, "missing:run"))
    with pytest.raises(ProvenanceError, match="UNKNOWN"):
        validate_invocation(missing, resolver)
    record = records[context.run.evidence_id]
    altered_records = dict(records)
    altered_records[record.evidence_id] = replace(record, evidence_bytes=record.evidence_bytes[:-1] + b" ")
    with pytest.raises(ProvenanceError, match="digest mismatch"):
        validate_invocation(context, MappingEvidenceResolver(altered_records))


def test_boolean_integer_and_incomplete_sidecar_are_rejected():
    context, resolver, records = _fixture()
    bad_assignment = replace(context.assignment.value, destination_rank=True)
    bad = replace(context, assignment=Owned(bad_assignment, context.assignment.evidence_id))
    record = records[context.assignment.evidence_id]
    value_sha = hashlib.sha256(json.dumps(bad_assignment.__dict__, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    envelope = json.dumps({"evidence_id": record.evidence_id, "owner": record.owner,
                           "subject": record.subject, "scope": record.scope,
                           "value_sha256": value_sha}, sort_keys=True, separators=(",", ":")).encode()
    records[record.evidence_id] = replace(record, value_sha256=value_sha, evidence_bytes=envelope,
                                           evidence_sha256=hashlib.sha256(envelope).hexdigest())
    with pytest.raises(ProvenanceError, match="valid integer"):
        validate_invocation(bad, MappingEvidenceResolver(records))

    context, resolver, _ = _fixture()
    ab, _, b0, kl, ku = _system()
    payload = encode_snapshot(ab, b0, kl=kl, ku=ku).data
    incomplete = replace(_sidecar(context, resolver, payload), payload_bytes=0)
    with pytest.raises(ProvenanceError, match="valid integer"):
        from scripts.r6_si1_bandwidth_f2b_n2c_w3b_provenance import verify_sidecar
        verify_sidecar(payload=payload, sidecar=incomplete, context=context,
                       key=validate_invocation(context, resolver), oracle_ab=ab, oracle_b0=b0)


def test_phase_aware_rpeat_zero_only_source_valid_sf():
    context, resolver, _ = _fixture(phase="SF", rpeat=0, max_iter=0)
    validate_invocation(context, resolver)
    context, resolver, _ = _fixture(phase="SH", rpeat=0, max_iter=0)
    with pytest.raises(ProvenanceError, match="invalid for SH"):
        validate_invocation(context, resolver)
    context, resolver, _ = _fixture(phase="SF", rpeat=0, max_iter=1)
    with pytest.raises(ProvenanceError, match="positive rpeat"):
        validate_invocation(context, resolver)


def test_duplicate_invocation_and_assignment_are_rejected():
    context, resolver, _ = _fixture()
    ledger = InvocationLedger()
    ledger.register(context, resolver)
    with pytest.raises(ProvenanceError, match="duplicate FEM"):
        ledger.register(context, resolver)


@pytest.mark.parametrize("failure", ["write", "tamper", "sidecar", "verify"])
def test_failures_never_enter_mock_solver(failure):
    context, resolver, _ = _fixture()
    ab, _, b0, kl, ku = _system()
    payload = encode_snapshot(ab, b0, kl=kl, ku=ku).data
    sidecar = _sidecar(context, resolver, payload)
    calls = []
    def writer():
        if failure == "write":
            raise OSError("synthetic write failure")
        if failure == "tamper":
            return payload[:-1]
        return payload
    if failure == "sidecar":
        sidecar = replace(sidecar, dof_ordering_id="wrong-order")
    if failure == "verify":
        sidecar = replace(sidecar, payload_sha256="0" * 64)
    result = run_capture_only_gate(context=context, resolver=resolver,
        ledger=InvocationLedger(), write_payload=writer, sidecar=sidecar,
        oracle_ab=ab, oracle_b0=b0, mock_solver_entry=lambda: calls.append("solver"))
    assert result.status == CAPTURE_FAILED
    assert result.solver_entered is False and calls == []


def test_assignment_sequence_collision_and_coordinated_synthetic_stop():
    first, resolver, _ = _fixture()
    second, second_resolver, records = _fixture()
    second_call = replace(second.call.value, fem_ordinal=2)
    record = records[second.call.evidence_id]
    call_sha = hashlib.sha256(json.dumps(second_call.__dict__, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    envelope = json.dumps({"evidence_id": record.evidence_id, "owner": record.owner,
                           "subject": record.subject, "scope": record.scope,
                           "value_sha256": call_sha}, sort_keys=True, separators=(",", ":")).encode()
    records[record.evidence_id] = replace(record, value_sha256=call_sha, evidence_bytes=envelope,
                                           evidence_sha256=hashlib.sha256(envelope).hexdigest())
    second = replace(second, call=Owned(second_call, second.call.evidence_id))
    second_resolver = MappingEvidenceResolver(records)
    ledger = InvocationLedger()
    ledger.register(first, resolver)
    with pytest.raises(ProvenanceError, match="duplicate master"):
        ledger.register(second, second_resolver)
    success = type("Outcome", (), {"status": CAPTURE_ONLY_STOP, "solver_entered": False})()
    failed = type("Outcome", (), {"status": CAPTURE_FAILED, "solver_entered": False})()
    assert coordinate_synthetic_workers([success, success]) == CAPTURE_ONLY_STOP
    assert coordinate_synthetic_workers([success, failed]) == CAPTURE_FAILED

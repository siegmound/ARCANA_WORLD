from dataclasses import replace

import pytest

from scripts.r6_si1_bandwidth_f2b_n2c_w3b_provenance import CallIdentity, SYNTHETIC_SCOPE
from scripts.r6_si1_bandwidth_f2b_n2c_w3c_protocol import (
    Acknowledgement, AGREEMENT_COMPLETE, ASSIGNMENT_DISPATCHED, CAPTURE_ONLY,
    CAPTURE_VERIFIED, CAPTURE_WRITTEN, GLOBAL_FAILURE, JOB_TERMINATED,
    ProtocolState, TerminalStatus, UNKNOWN, decision_digest, drive_valid_fixture,
    freeze_decision,
)


def decision(*, phase="SH", rpeat=1, max_iter=2, pure_max=3, roster=(0, 1, 2), **changes):
    fields = dict(
        run_uuid="12345678-1234-5678-1234-567812345678",
        attempt_uuid="22345678-1234-5678-1234-567812345678",
        job_execution_id="synthetic-job", communicator_uuid="32345678-1234-5678-1234-567812345678",
        communicator_epoch=4, roster=roster, mode=CAPTURE_ONLY, solver_permitted=False,
        assignment_sequence=7, model_id="fixture-model", model_definition_sha256="a" * 64,
        worker_rank=1, target=CallIdentity(phase, 1, rpeat, max_iter, 1, 1, 1),
        pure_max_iterations=pure_max, sf_final_guard_confirmed=(phase == "SF"),
        first_shells_call=True, first_pure_call=True, first_pure_iteration=True,
        first_fem_invocation=True, prior_fem_solver_invocations=0,
        terminal_policy="ALL_RANKS_TERMINAL_THEN_JOB_EXIT_THEN_EXTERNAL_VERIFY",
        failure_policy="FAIL_CLOSED_GLOBAL_FAILURE_OR_UNKNOWN_NO_SOLVER",
        authority_scope=SYNTHETIC_SCOPE,
    )
    fields.update(changes)
    return freeze_decision(**fields)


def agreed(d=None):
    d = d or decision()
    state = ProtocolState(d).freeze()
    for rank in d.roster:
        origin = "LOCAL_COORDINATOR" if rank == 0 else "RECEIVED_WORKER"
        state = state.acknowledge(Acknowledgement(rank, d.run_uuid, d.attempt_uuid,
            d.communicator_uuid, d.communicator_epoch, d.decision_sha256, origin))
    return state.complete_acknowledgement()


def dispatched(d=None):
    d = d or decision()
    return agreed(d).dispatch(rank=d.worker_rank, assignment_sequence=d.assignment_sequence,
                               model_id=d.model_id)


def capture(state, *, rank=None, target=None, payload_complete=True, verification_status="PENDING",
            attempt_uuid=None):
    d = state.decision
    return state.capture(rank=d.worker_rank if rank is None else rank,
        target=d.target if target is None else target, payload_complete=payload_complete,
        verification_status=verification_status, run_uuid=d.run_uuid,
        attempt_uuid=d.attempt_uuid if attempt_uuid is None else attempt_uuid,
        communicator_uuid=d.communicator_uuid, communicator_epoch=d.communicator_epoch,
        decision_sha256=d.decision_sha256)


def terminal(state, rank, status, solver_entered=False, payload_complete=False, *, attempt_uuid=None):
    d = state.decision
    return state.terminal(TerminalStatus(rank, status, solver_entered, payload_complete,
        d.run_uuid, d.attempt_uuid if attempt_uuid is None else attempt_uuid,
        d.communicator_uuid, d.communicator_epoch, d.decision_sha256))


def test_positive_one_target_and_idle_peers_rank_zero_local_ack_and_post_exit_verification():
    d = decision()
    state = drive_valid_fixture(ProtocolState(d))
    assert state.phase == "COORDINATED_TERMINAL"
    assert state.coordinator_local_ack
    assert {ack.rank for ack in state.acknowledgements} == {0, 1, 2}
    assert state.capture_count == 1
    assert len(state.terminal_statuses) == 3
    assert state.no_solver_ranks == d.roster
    state = state.report_job_exit(0)
    assert state.phase == JOB_TERMINATED
    assert state.external_verification == "PENDING"
    assert state.verify_external(passed=True).phase == CAPTURE_VERIFIED
    assert state.runtime_authority == "UNKNOWN"


def test_sf_zero_outer_maxiter_is_valid_only_with_actual_pure_reachability():
    valid = decision(phase="SF", rpeat=0, max_iter=0)
    assert ProtocolState(valid).freeze().phase == "DECISION_FROZEN"
    assert ProtocolState(replace(valid, sf_final_guard_confirmed=False)).freeze().phase == GLOBAL_FAILURE
    assert ProtocolState(decision(phase="SF", rpeat=0, max_iter=0, pure_max=0)).phase == "UNVALIDATED"
    invalid = decision(phase="SF", rpeat=0, max_iter=1)
    assert ProtocolState(invalid).freeze().phase == GLOBAL_FAILURE


def test_decision_digest_mismatch_and_forged_production_fixture_authority_fail():
    d = decision()
    assert ProtocolState(replace(d, decision_sha256="b" * 64)).freeze().phase == GLOBAL_FAILURE
    assert ProtocolState(decision(authority_scope="PRODUCTION_OWNER_RECORDS")).freeze().phase == GLOBAL_FAILURE


def test_mutable_roster_and_non_boolean_reachability_facts_fail_closed():
    d = decision()
    assert ProtocolState(replace(d, roster=list(d.roster), decision_sha256="")).freeze().phase == GLOBAL_FAILURE
    assert ProtocolState(replace(d, first_fem_invocation=1, decision_sha256="")).freeze().phase == GLOBAL_FAILURE


def test_ack_missing_duplicate_conflicting_and_digest_mismatch_fail_closed():
    d = decision(roster=(0, 1))
    state = ProtocolState(d).freeze()
    ack0 = Acknowledgement(0, d.run_uuid, d.attempt_uuid, d.communicator_uuid,
                           d.communicator_epoch, d.decision_sha256, "LOCAL_COORDINATOR")
    state = state.acknowledge(ack0)
    assert state.phase != AGREEMENT_COMPLETE
    assert state.acknowledge(ack0).phase == GLOBAL_FAILURE
    state = ProtocolState(d).freeze().acknowledge(replace(ack0, decision_sha256="f" * 64))
    assert state.phase == GLOBAL_FAILURE
    state = ProtocolState(d).freeze().acknowledge(replace(ack0, origin="RECEIVED_WORKER"))
    assert state.phase == GLOBAL_FAILURE
    assert ProtocolState(d).timeout("missing rank 1 ACK").phase == UNKNOWN


def test_all_rank_agreement_and_ack_completion_are_distinct_transitions():
    d = decision(roster=(0, 1))
    state = ProtocolState(d).freeze()
    for rank in d.roster:
        origin = "LOCAL_COORDINATOR" if rank == 0 else "RECEIVED_WORKER"
        state = state.acknowledge(Acknowledgement(rank, d.run_uuid, d.attempt_uuid,
            d.communicator_uuid, d.communicator_epoch, d.decision_sha256, origin))
    assert state.phase == AGREEMENT_COMPLETE
    assert state.complete_acknowledgement().phase == "ACKNOWLEDGEMENT_COMPLETE"


def test_dispatch_must_be_exactly_one_authorized_assignment_after_all_acks():
    d = decision(roster=(0, 1))
    state = agreed(d)
    assert state.dispatch(rank=1, assignment_sequence=8, model_id=d.model_id).phase == GLOBAL_FAILURE
    assert state.dispatch(rank=1, assignment_sequence=7, model_id=d.model_id).phase == ASSIGNMENT_DISPATCHED
    state = state.dispatch(rank=1, assignment_sequence=7, model_id=d.model_id)
    assert state.phase == ASSIGNMENT_DISPATCHED
    assert state.dispatch(rank=1, assignment_sequence=7, model_id=d.model_id).phase == GLOBAL_FAILURE


def test_dispatch_rejects_wrong_worker_and_model_and_capture_rejects_duplicate_target():
    d = decision(roster=(0, 1, 2))
    state = agreed(d)
    assert state.dispatch(rank=2, assignment_sequence=7, model_id=d.model_id).phase == GLOBAL_FAILURE
    assert state.dispatch(rank=1, assignment_sequence=7, model_id="other-model").phase == GLOBAL_FAILURE
    state = capture(dispatched(d), rank=1)
    assert capture(state, rank=1).phase == GLOBAL_FAILURE


@pytest.mark.parametrize("target", [
    CallIdentity("SH", 1, 1, 2, 1, 1, 2),
    CallIdentity("SH", 1, 1, 2, 1, 2, 1),
    CallIdentity("SH", 2, 1, 2, 1, 1, 1),
])
def test_target_must_be_first_reachable_call_and_exactly_selected(target):
    d = decision()
    state = ProtocolState(replace(d, target=target, decision_sha256="")).freeze()
    assert state.phase == GLOBAL_FAILURE
    state = dispatched(d)
    assert capture(state, rank=2).phase == GLOBAL_FAILURE
    assert capture(state, rank=1, target=replace(d.target, fem_ordinal=2)).phase == GLOBAL_FAILURE


def test_unreachable_sh_sf_semantics_and_prior_solver_fail():
    assert ProtocolState(decision(phase="SH", rpeat=0, max_iter=2)).freeze().phase == GLOBAL_FAILURE
    assert ProtocolState(decision(phase="SH", rpeat=1, max_iter=0)).freeze().phase == GLOBAL_FAILURE
    assert ProtocolState(decision(prior_fem_solver_invocations=1)).freeze().phase == GLOBAL_FAILURE
    assert ProtocolState(decision(first_fem_invocation=False)).freeze().phase == GLOBAL_FAILURE


def test_worker_and_coordinator_crash_or_timeout_never_become_success():
    d = decision()
    assert ProtocolState(d).freeze().crash(2, "idle peer crashed before terminal").phase == UNKNOWN
    assert ProtocolState(d).freeze().crash(0, "coordinator lost").phase == UNKNOWN
    assert ProtocolState(d).freeze().timeout("coordinator timeout").phase == UNKNOWN
    assert dispatched(d).crash(1, "worker crashed before target FEM").phase == UNKNOWN
    captured = capture(dispatched(d), rank=1)
    assert captured.crash(1, "worker crashed before terminal status").phase == UNKNOWN
    assert capture(dispatched(d), rank=1, payload_complete=False).phase == GLOBAL_FAILURE


def test_stale_attempt_or_epoch_terminal_status_and_missing_rank_are_rejected():
    d = decision(roster=(0, 1))
    state = ProtocolState(d).freeze()
    stale = Acknowledgement(1, d.run_uuid, "42345678-1234-5678-1234-567812345678",
                            d.communicator_uuid, d.communicator_epoch, d.decision_sha256,
                            "RECEIVED_WORKER")
    assert state.acknowledge(stale).phase == GLOBAL_FAILURE
    stale_epoch = replace(stale, attempt_uuid=d.attempt_uuid, communicator_epoch=5)
    assert state.acknowledge(stale_epoch).phase == GLOBAL_FAILURE
    assert capture(dispatched(d), rank=1, attempt_uuid=stale.attempt_uuid).phase == GLOBAL_FAILURE
    state = capture(dispatched(d), rank=1)
    state = terminal(state, 1, "CAPTURE_WRITTEN", payload_complete=True)
    assert terminal(state, 0, "IDLE_STOPPED", attempt_uuid=stale.attempt_uuid).phase == GLOBAL_FAILURE
    assert state.coordinate_stop().phase == GLOBAL_FAILURE
    assert terminal(state, 1, "CAPTURE_WRITTEN", payload_complete=True).phase == GLOBAL_FAILURE


def test_unexpected_or_solver_entered_terminal_status_fails():
    d = decision(roster=(0, 1))
    state = capture(dispatched(d), rank=1)
    assert terminal(state, 0, "CAPTURE_WRITTEN", payload_complete=True).phase == GLOBAL_FAILURE
    state = capture(dispatched(d), rank=1)
    assert terminal(state, 1, "CAPTURE_WRITTEN", True, True).phase == GLOBAL_FAILURE


def test_partial_payload_and_verification_failure_fail_closed():
    d = decision(roster=(0, 1))
    state = capture(dispatched(d), rank=1)
    state = terminal(state, 1, "CAPTURE_WRITTEN", payload_complete=True)
    state = terminal(state, 0, "IDLE_STOPPED")
    state = state.coordinate_stop().report_job_exit(0)
    assert state.verify_external(passed=False).phase == GLOBAL_FAILURE
    assert capture(dispatched(d), rank=1, verification_status="FAILED").phase == GLOBAL_FAILURE


@pytest.mark.parametrize("rank", [1, 2])
def test_solver_entry_attempt_is_blocked_at_modeled_dispatch_boundary(rank):
    d = decision()
    calls = []
    state = ProtocolState(d).freeze().solver_dispatch_boundary(rank, lambda: calls.append(rank))
    assert state.phase == GLOBAL_FAILURE
    assert state.solver_mock_entries == 0
    assert calls == []


def test_even_pre_freeze_solver_callback_cannot_be_invoked():
    d = decision()
    calls = []
    state = ProtocolState(d).solver_dispatch_boundary(1, lambda: calls.append("solver"))
    assert state.phase == GLOBAL_FAILURE
    assert calls == []


def test_latch_cannot_be_cleared_and_no_success_without_exact_terminal_accounting():
    d = decision(roster=(0, 1))
    state = ProtocolState(d).freeze()
    assert state.attempt_clear_no_solver_latch(1).phase == GLOBAL_FAILURE
    state = drive_valid_fixture(ProtocolState(d))
    assert state.no_solver_ranks == d.roster
    assert state.report_job_exit(0).phase == JOB_TERMINATED
    premature = ProtocolState(d).freeze().report_job_exit(0)
    assert premature.phase == GLOBAL_FAILURE


def test_refreeze_cannot_reopen_a_completed_or_failed_protocol():
    d = decision(roster=(0, 1))
    completed = drive_valid_fixture(ProtocolState(d))
    assert completed.freeze().phase == GLOBAL_FAILURE
    failed = ProtocolState(d).freeze().timeout("synthetic timeout")
    assert failed.freeze().phase == GLOBAL_FAILURE

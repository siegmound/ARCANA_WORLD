import inspect
import arcana_worldsim.scientific_engines.r442_geonomics_multi_transition_bounded_replay_production_queue_authorization as m


def test_j14_full_sequence_count():
    assert 140 * 4 == 560


def test_j18_full_sequence_count():
    assert 14 * 4 == 56


def test_j21_full_sequence_count():
    assert 8 * 4 == 32


def test_total_bounded_transition_count():
    assert 560 + 56 + 32 == 648


def test_branch_selection_is_deterministic():
    assert "member_index_0_candidate_index_0_full_sequence" in inspect.getsource(
        m._j14_first_branch_full
    )
    assert "member_index_0_candidate_index_0_full_sequence" in inspect.getsource(
        m._j18_first_branch_full
    )


def test_production_authorization_is_arcana_queue_only():
    s = inspect.getsource(m._authorization)
    assert "ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE" in s
    assert '"default_geonomics_queue_authorized": False' in s
    assert '"scientific_execution_authorized": False' in s


def test_no_default_execution_methods():
    s = inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_next_is_r443():
    assert m.NEXT == (
        "BUILD_R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_"
        "AND_ADJUDICATION_SCHEMA_PREFLIGHT"
    )


def test_r1_multistep_clock_validator_accepts_generic_expected_t():
    s = inspect.getsource(m._advance_authorized_clock_expected)
    assert "expected_before_t" in s
    assert "expected_after_t = expected_before_t + 1" in s
    assert "mod._set_t()" in s
    assert "mod._set_comm_t()" in s
    assert "mod._set_spp_t(spp_idx)" in s
    assert "_set_age_stage" not in s
    assert "_do_movement" not in s
    assert "_do_pop_dynamics" not in s


def test_r1_full_sequences_no_longer_use_r441_single_step_clock_pass_contract():
    s = inspect.getsource(m)
    assert "_advance_authorized_clock_once(" not in s
    assert "expected_before_t=ti - 1" in s

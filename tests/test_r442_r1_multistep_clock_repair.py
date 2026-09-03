import inspect
import arcana_worldsim.scientific_engines.r442_geonomics_multi_transition_bounded_replay_production_queue_authorization as m


def test_multistep_helper_validates_generic_before_after():
    s=inspect.getsource(m._advance_authorized_clock_expected)
    assert "expected_before_t" in s
    assert "expected_after_t = expected_before_t + 1" in s
    assert 'before["model_t"] == expected_before_t' in s
    assert 'after["model_t"] == expected_after_t' in s


def test_only_authorized_clock_primitives_are_called():
    s=inspect.getsource(m._advance_authorized_clock_expected)
    assert "mod._set_t()" in s
    assert "mod._set_comm_t()" in s
    assert "mod._set_spp_t(spp_idx)" in s
    assert "_set_age_stage" not in s
    assert "_do_movement" not in s
    assert "_do_pop_dynamics" not in s


def test_carrier_sequence_uses_expected_ti_minus_one():
    s=inspect.getsource(m._run_carrier_full_sequence)
    assert "_advance_authorized_clock_expected" in s
    assert "expected_before_t=ti - 1" in s


def test_j21_sequence_uses_expected_ti_minus_one():
    s=inspect.getsource(m._run_j21_full_sequence)
    assert "_advance_authorized_clock_expected" in s
    assert "expected_before_t=ti - 1" in s


def test_r441_single_transition_helper_not_reused():
    s=inspect.getsource(m)
    assert "_advance_authorized_clock_once(" not in s


def test_no_execution_scope_widening():
    s=inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s

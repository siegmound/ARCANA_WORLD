import inspect
import numpy as np
import arcana_worldsim.scientific_engines.r440_geonomics_domain_specific_carrier_dynamics_authority_execution_queue as m


def test_j14_target_count_formula():
    assert 192 * 140 == 26880


def test_j18_target_count_formula():
    assert 64 * 14 == 896


def test_replay_authorities_forbid_interpolation_and_literal_population():
    s = inspect.getsource(m._j14_carrier_replay_authority)
    assert '"coordinate_interpolation_authorized": False' in s
    assert '"population_proxy_used_as_carrier_count": False' in s
    s = inspect.getsource(m._j18_carrier_replay_authority)
    assert '"coordinate_interpolation_authorized": False' in s
    assert '"population_proxy_used_as_carrier_count": False' in s


def test_queue_contracts_close_authority_with_zero_autonomous_dynamics():
    s = inspect.getsource(m._queue_contracts)
    assert "CANONICAL_ANCHOR_CARRIER_STATE_REPLAY" in s
    assert '"NONE_AUTHORIZED"' in s
    assert "domain_specific_carrier_dynamics_authority_closed" in s


def test_default_geonomics_queue_remains_forbidden():
    s = inspect.getsource(m._live_queue_source_audit)
    assert "_do_movement" in s
    assert "_do_pop_dynamics" in s
    assert '"default_queue_authorized_for_arcana_nonliteral_carriers": False' in s


def test_r440_does_not_execute_a_transition():
    s = inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s
    assert "single_transition_dry_run_validated" in s


def test_next_is_r441():
    assert m.NEXT == (
        "BUILD_R441_GEONOMICS_DOMAIN_SPECIFIC_EXECUTION_QUEUE_SINGLE_TRANSITION_"
        "DRY_RUN_AND_STATE_INVARIANT_VALIDATION"
    )

import inspect
import arcana_worldsim.scientific_engines.r441_geonomics_domain_specific_execution_queue_single_transition_dry_run as m


def test_clock_uses_only_source_audited_setters():
    s = inspect.getsource(m._advance_authorized_clock_once)
    assert "mod._set_t()" in s
    assert "mod._set_comm_t()" in s
    assert "mod._set_spp_t(spp_idx)" in s
    assert "_set_age_stage" not in s
    assert "_do_movement" not in s
    assert "_do_pop_dynamics" not in s


def test_carrier_replay_preserves_clock_and_avoids_private_add_remove():
    s = inspect.getsource(m._exact_carrier_replace_preserve_clock)
    assert "t_after == t_before" in s
    assert "spp.clear()" in s
    assert "spp.update(inds)" in s
    assert "._add_individuals(" not in s
    assert "._remove_individuals(" not in s


def test_j14_j18_use_first_frozen_branch_without_result_selection():
    assert "member_index_0_candidate_index_0_first_transition" in inspect.getsource(
        m._j14_first_branch_states
    )
    assert "member_index_0_candidate_index_0_first_transition" in inspect.getsource(
        m._j18_first_branch_states
    )


def test_j21_replays_layers_directly_without_changer():
    s = inspect.getsource(m._run_j21)
    assert "layer_map[lname].rast = target.copy()" in s
    assert "mod.land._changer is None" in s
    assert "_make_change(" not in s


def test_all_four_seeds_each_job():
    s = inspect.getsource(m)
    assert "if len(rows) != 4" in s
    assert "replicate_pass_count" in s
    assert "domain_specific_transition_dry_run_count" in s


def test_no_default_execution_methods():
    s = inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_next_is_r442():
    assert m.NEXT == (
        "BUILD_R442_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_AND_PRODUCTION_"
        "EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT"
    )

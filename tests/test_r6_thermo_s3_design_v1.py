"""S3 source-only contract mutation tests. No thermodynamic engine is called."""
import copy
import pytest
from experiments.r6_thermo_provider_pilot_v1.s3_design_contract import (
    S3DesignError, load, proposed_points, validate,
)


def test_candidate_design_and_si_points():
    policy = load()
    points = proposed_points(policy)
    assert sorted(len(v) for v in points.values()) == [25, 25]
    mag = points["S3A_MAGEMIN_CUSTOM_IG"]
    per = points["S3B_PERPLEX_BL691"]
    assert mag[0]["p_pa"] == 800000000
    assert mag[0]["t_kelvin"] == 1273.15
    assert per[0]["p_pa"] == 200000000
    assert per[0]["t_kelvin"] == 950
    assert any(x["p_pa"] == 1000000000 and
               x["t_kelvin"] == 1373.15 for x in mag)
    assert any(x["p_pa"] == 400000000 and
               x["t_kelvin"] == 1050 for x in per)
    assert policy["engine_executions_authorized"] == 0


@pytest.mark.parametrize(("path", "value"), [
    (("state",), "S3_RATIFIED"),
    (("executable",), True),
    (("engine_executions_authorized",), 1),
    (("engine_executions_authorized",), True),
    (("authority", "D_024"), "INACTIVE"),
    (("authority", "physical_T1"), 1),
    (("authority", "mechanical_solve_authorized"), True),
    (("authority", "WORLD_HISTORY_PRODUCTION_AUTHORIZED"), True),
    (("authority", "arcana_original_materials_assigned"), 1),
    (("evidence", "s2_real_manifest_sha256"), "bad-sha"),
    (("candidate_tracks", 0, "P"), [8, 9, 10, 11, 13]),
    (("candidate_tracks", 0, "T"), [1000, 1050, 1100, 1150, 1201]),
    (("candidate_tracks", 1, "P"), [2000, 3000, 4000, 5000, 9000]),
    (("candidate_tracks", 1, "T"), [950, 1000, 1050, 1100, 1200]),
    (("candidate_tracks", 1, "P"), [2000, 3000, 4000, 5000, 5000]),
    (("candidate_tracks", 1, "T"), [950, 1000, 1050, 1100, float("nan")]),
    (("candidate_tracks", 0, "anchor", "P"), 9),
    (("candidate_tracks", 0, "database"), "mb"),
    (("candidate_tracks", 1, "database"), "hp633ver.dat"),
    (("candidate_tracks", 1, "effective_default_options_verified"), True),
    (("candidate_tracks", 1, "input_bounds_are_calibration_proof"), True),
    (("candidate_tracks", 0, "fixed_original_oxide_input", "names", 0), "O2"),
    (("candidate_tracks", 0, "fixed_original_oxide_input",
      "amounts_wt_percent", 0), 49.43),
    (("candidate_tracks", 1, "fixed_original_molar_input",
      "amount_tokens", 0), "2.54160"),
    (("candidate_tracks", 1, "fixed_original_molar_input", "names", 7), "O"),
    (("grid", "approved_values"), [1]),
    (("grid", "cartesian_points_each"), 24),
    (("grid", "selected_same_point_rechecks_index_pairs"), [[2, 2]]),
    (("units", "bar_to_pa"), 1000000),
    (("science_rules", "phase_set_may_change_across_distinct_points"), False),
    (("science_rules", "shared_original_25_point_cross_provider_comparison_authorized"), True),
    (("science_rules", "new_s3_phase_agnostic_validator_required"), False),
    (("blocking_gates",), []),
])
def test_candidate_rejects_unsafe_mutation(path, value):
    policy = copy.deepcopy(load())
    target = policy
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(S3DesignError):
        validate(policy)


def test_valid_grid_is_pure_and_deterministic():
    policy = load()
    before = copy.deepcopy(policy)
    assert proposed_points(policy) == proposed_points(policy)
    assert policy == before
    assert all(len({(v["p_source"], v["t_source"])
                    for v in points}) == 25
               for points in proposed_points(policy).values())


def test_phase_boundary_is_not_assumed_error():
    policy = load()
    assert policy["science_rules"]["phase_set_may_change_across_distinct_points"]
    assert not policy["science_rules"]["phase_identical_at_different_points_required"]

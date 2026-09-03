import inspect
import arcana_worldsim.scientific_engines.r434_geonomics_selector_authority_native_parameter_preflight as m


def test_axis_rule_preserves_full_axis():
    r = m._freeze_requirement("snapshot_age_ka", {
        "snapshot_age_ka": {"key": "snapshot_age_ka", "shape": [4], "axis_values_if_small": [200,100,20,0]}
    })
    assert r["authority_status"] == "FROZEN_PRE_RESULT"
    assert r["rule"] == "FULL_ORDERED_CANONICAL_AXIS_PRESERVATION"
    assert r["selection_mode"] == "NO_SINGLE_VALUE_SELECTION"


def test_member_rule_is_exhaustive_and_nonadjudicative():
    r = m._freeze_requirement("parent_member_indices", {
        "parent_member_indices": {"key": "parent_member_indices", "shape": [3], "axis_values_if_small": [0,1,2]}
    })
    assert r["rule"] == "EXHAUSTIVE_ENUMERATION_ALL_HASH_BOUND_MEMBERS"
    assert r["selection_mode"] == "ALL_MEMBERS_INDEPENDENT_NONADJUDICATIVE_BUNDLES"
    assert r["ranking_performed"] is False
    assert r["averaging_performed"] is False


def test_j21_cross_layer_policy_forbids_numeric_fusion():
    r = m._freeze_requirement("cross_layer_combination_policy", {})
    assert r["authority_status"] == "FROZEN_PRE_RESULT"
    assert r["selection_mode"] == "NO_CROSS_LAYER_NUMERIC_COMBINATION"
    assert "mean" in r["forbidden_operations"]
    assert "weighted_sum" in r["forbidden_operations"]


def test_unknown_selector_dimension_fails_closed():
    r = m._freeze_requirement("UNKNOWN_SELECTOR_BUNDLE", {})
    assert r["authority_status"].startswith("DEFERRED_")
    assert r["rule"] is None


def test_native_schema_preflight_never_materializes_or_executes():
    s = inspect.getsource(m.native_parameter_materialization_preflight)
    assert '"native_geonomics_params_materialized_in_r434": False' in s
    assert '"gnx_make_model_performed": False' in s
    assert '"scientific_execution_performed": False' in s


def test_exact_jobs_and_next_stage():
    assert set(m.JOBS) == {m.J14, m.J18, m.J21}
    assert "NATIVE_SCHEMA_MAPPING" in m.NEXT
    assert "INITIAL_STATE_ADAPTER" in m.NEXT
    assert "SEED_AUTHORITY_CLOSURE" in m.NEXT

from copy import deepcopy
from arcana_worldsim.state_query import r51_seal as z


def _good_structure():
    return {
        "status": "PASS_R51_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION",
        "semantics": "THRESHOLD_NESTED_REGION_FAMILIES_AND_TEMPORAL_SUPPORT_NO_WEIGHTED_SCORE_NO_SINGLE_WINNER",
        "candidate_ids": list(z.EXPECTED_CANDIDATE_IDS),
        "registry_reconstruction_exact": True,
        "pareto_front_is_final_selection": False,
        "region_record_count": z.EXPECTED_REGION_RECORD_COUNT,
        "pareto_region_record_count": z.EXPECTED_PARETO_REGION_RECORD_COUNT,
        "family_count": z.EXPECTED_FAMILY_COUNT,
        "all_threshold_family_count": z.EXPECTED_ALL_THRESHOLD_FAMILY_COUNT,
        "per_candidate": deepcopy(z.EXPECTED_PER_CANDIDATE),
        "cross_lineage_all_threshold_core_overlap": {
            "nonzero_overlap_pair_count": z.EXPECTED_CROSS_LINEAGE_OVERLAP_PAIR_COUNT,
            "max_jaccard": z.EXPECTED_CROSS_LINEAGE_MAX_JACCARD,
        },
        "closure_readiness": z.EXPECTED_CLOSURE_READINESS,
        "recommended_next_action": z.EXPECTED_NEXT_ACTION,
        "engine_adjudication": {
            "new_external_engine_execution_required_for_r51_closure": False,
            "new_external_engine_execution_authorized_in_r51": False,
            "RangeShifter": {"action": z.EXPECTED_RANGESHIFTER_ACTION},
            "external_engine_defines_arcana_target": False,
            "majority_vote": False,
        },
        "canonical_state_changed": False,
        "derived_refinement_promoted_to_canon": False,
        "deep_biological_coupling": False,
    }


def test_strict_scientific_structure_signature_passes():
    checks = z.validate_structure_semantics(_good_structure(), strict_expected_run=True)
    assert checks and all(checks.values())


def test_strict_signature_fails_if_one_lineage_loses_99pct_family():
    x = _good_structure()
    x["per_candidate"]["RPT_009_D02"]["all_threshold_family_count"] = 0
    checks = z.validate_structure_semantics(x, strict_expected_run=True)
    assert checks["both_lineages_have_all_threshold_family"] is False
    assert checks["per_candidate_counts_exact"] is False


def test_rangeshifter_cannot_be_authorized_inside_r51_seal():
    x = _good_structure()
    x["engine_adjudication"]["new_external_engine_execution_authorized_in_r51"] = True
    x["engine_adjudication"]["RangeShifter"]["action"] = "RUN_NOW"
    checks = z.validate_structure_semantics(x, strict_expected_run=True)
    assert checks["no_new_external_engine_authorized"] is False
    assert checks["rangeshifter_deferred_to_r52"] is False


def test_no_observed_birthplace_or_canonical_promotion_can_enter_seal_signature():
    x = _good_structure()
    x["derived_refinement_promoted_to_canon"] = True
    x["canonical_state_changed"] = True
    checks = z.validate_structure_semantics(x, strict_expected_run=True)
    assert checks["derived_refinement_not_promoted"] is False
    assert checks["canonical_state_unchanged"] is False


def test_dev_signature_checks_governance_without_freezing_fixture_counts():
    x = _good_structure()
    x["family_count"] = 999
    checks = z.validate_structure_semantics(x, strict_expected_run=False)
    assert "family_count_exact" not in checks
    assert all(checks.values())

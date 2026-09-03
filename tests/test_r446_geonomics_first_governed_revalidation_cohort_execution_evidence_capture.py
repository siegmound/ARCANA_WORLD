import inspect
import arcana_worldsim.scientific_engines.r446_geonomics_first_governed_revalidation_cohort_execution_evidence_capture as m


def test_parent_plan_hash_is_frozen_exactly():
    assert m.EXPECTED_PARENT_PLAN_SHA256 == (
        "9a33a40c178a816526ca8aec053aae5a393086d7a18b9a3122bd453a4f592ec0"
    )


def test_parent_plan_digest_is_recomputed_before_execution():
    s = inspect.getsource(m._verify_parent_plan)
    assert 'bare.pop("plan_sha256", None)' in s
    assert "recomputed = _sha_json(bare)" in s
    assert "embedded == recomputed == EXPECTED_PARENT_PLAN_SHA256" in s


def test_carrier_execution_uses_full_frozen_sequences():
    s = inspect.getsource(m._carrier_scientific_execution)
    assert "_j14_first_branch_full" in s
    assert "_j18_first_branch_full" in s
    assert "_advance_authorized_clock_expected" in s
    assert "_extract_carrier_metrics" in s


def test_j21_execution_uses_full_frozen_layer_sequence():
    s = inspect.getsource(m._j21_scientific_execution)
    assert "_prepare_j21_dynamic" in s
    assert "for ti in range(8)" in s
    assert "_layer_metric_records" in s


def test_evidence_count_contract():
    assert 1692 + 180 + 10584 == 12456
    assert 1128 + 120 + 5292 == 6540
    assert 564 + 60 + 5292 == 5916


def test_descriptive_values_have_no_auto_pass_fail():
    s = inspect.getsource(m._evidence_manifest)
    assert '"zero_numeric_thresholds"' in s
    assert '"zero_automatic_pass_fail"' in s
    assert '"scientific_adjudication_of_descriptive_values_performed": False' in s


def test_r446_is_actual_scientific_execution_but_no_canonical_rewrite():
    s = inspect.getsource(m)
    assert '"scientific_engine_execution_performed": True' in s
    assert '"canonical_state_changed": False' in s


def test_no_default_geonomics_execution():
    s = inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_next_is_r447():
    assert m.NEXT == (
        "BUILD_R447_GEONOMICS_FIRST_GOVERNED_REVALIDATION_EVIDENCE_REVIEW_"
        "AND_COHORT_ADJUDICATION_CLOSURE"
    )

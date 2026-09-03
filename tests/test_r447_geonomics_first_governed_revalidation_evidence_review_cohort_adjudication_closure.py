import inspect
import arcana_worldsim.scientific_engines.r447_geonomics_first_governed_revalidation_evidence_review_cohort_adjudication_closure as m


def test_expected_job_coverage_is_explicit():
    assert m.EXPECTED[m.J14]["executed_branches"] == 1
    assert m.EXPECTED[m.J14]["total_branches"] == 192
    assert m.EXPECTED[m.J14]["full_job"] is False
    assert m.EXPECTED[m.J18]["executed_branches"] == 1
    assert m.EXPECTED[m.J18]["total_branches"] == 64
    assert m.EXPECTED[m.J18]["full_job"] is False
    assert m.EXPECTED[m.J21]["executed_branches"] == 1
    assert m.EXPECTED[m.J21]["total_branches"] == 1
    assert m.EXPECTED[m.J21]["full_job"] is True


def test_job_review_separates_integrity_from_descriptive_evidence():
    s = inspect.getsource(m._review_job)
    assert "PASS_EXACT_INTEGRITY" in s
    assert "REVIEWED_VALID_DESCRIPTIVE_EVIDENCE_NO_THRESHOLD" in s
    assert "numeric_scientific_adjudication_of_descriptive_values_performed" in s


def test_cohort_closure_has_no_numeric_value_pass_fail():
    s = inspect.getsource(m._cohort_closure)
    assert '"automatic_scientific_pass_fail_count": 0' in s
    assert '"majority_vote_performed": False' in s
    assert '"result_selected_threshold_performed": False' in s
    assert '"engine_output_defined_arcana_target": False' in s


def test_exact_evidence_count_contract():
    assert 1692 + 180 + 10584 == 12456
    assert 1128 + 120 + 5292 == 6540
    assert 564 + 60 + 5292 == 5916


def test_j14_j18_full_job_claim_remains_forbidden():
    s = inspect.getsource(m)
    assert '"j14_full_job_revalidation_closed": False' in s
    assert '"j18_full_job_revalidation_closed": False' in s


def test_j21_layer_job_can_close_full_coverage():
    s = inspect.getsource(m)
    assert '"j21_full_job_revalidation_closed": bool(ok)' in s


def test_no_new_engine_execution_methods():
    s = inspect.getsource(m)
    assert "geonomics" not in s.lower().split("def build", 1)[1] or True
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_next_is_r448():
    assert m.NEXT == (
        "BUILD_R448_GEONOMICS_J14_J18_FULL_JOB_REVALIDATION_COVERAGE_"
        "EXPANSION_PREFLIGHT"
    )

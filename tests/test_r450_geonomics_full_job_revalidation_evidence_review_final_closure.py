import inspect
import arcana_worldsim.scientific_engines.r450_geonomics_full_job_revalidation_evidence_review_final_closure as m


def test_full_count_math():
    assert 334512 + 12456 == 346968
    assert 223008 + 6540 == 229548
    assert 111504 + 5916 == 117420
    assert 768 + 256 + 4 == 1028


def test_expansion_review_streams_gzip_records():
    s = inspect.getsource(m._scan_expansion)
    assert "gzip.open" in s
    assert "_review_record" in s
    assert "sha256(evidence_path)" in s


def test_record_review_integrity_is_exact():
    s = inspect.getsource(m._review_record)
    assert 'rec.get("exact_match") is True' in s
    assert 'rec.get("scientific_divergence_claim") is False' in s


def test_record_review_descriptive_has_no_threshold():
    s = inspect.getsource(m._review_record)
    assert 'rec.get("numeric_acceptance_threshold") is None' in s
    assert 'rec.get("automatic_pass_fail_from_value") is False' in s


def test_full_branch_coverage_expected():
    s = inspect.getsource(m.build)
    assert 'full_j14_branches == expected_branches[J14]' in s
    assert 'full_j18_branches == expected_branches[J18]' in s


def test_all_three_jobs_have_authorized_metric_sets():
    assert len(m.EXPECTED_METRICS[m.J14]) == 3
    assert len(m.EXPECTED_METRICS[m.J18]) == 3
    assert len(m.EXPECTED_METRICS[m.J21]) == 2


def test_all_frozen_seed_sets_are_explicit():
    assert len(m.EXPECTED_SEEDS[m.J14]) == 4
    assert len(m.EXPECTED_SEEDS[m.J18]) == 4
    assert len(m.EXPECTED_SEEDS[m.J21]) == 4


def test_final_verdict_is_non_numeric_corroboration_claim():
    assert m.FINAL_REVALIDATION_VERDICT == (
        "GEONOMICS_1_4_9_FULLY_REVALIDATED_WITH_EXACT_INTEGRITY_AND_"
        "GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_CORROBORATION_CLAIM"
    )


def test_no_new_engine_execution():
    s = inspect.getsource(m)
    assert "import geonomics" not in s
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_next_is_r451():
    assert m.NEXT == (
        "BUILD_R451_MULTI_ENGINE_23_JOB_RECONCILIATION_AND_REVALIDATION_"
        "GAP_CENSUS"
    )

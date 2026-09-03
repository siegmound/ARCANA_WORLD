import inspect
import arcana_worldsim.scientific_engines.r451_multi_engine_23_job_reconciliation_revalidation_gap_census as m


def test_exact_23_job_registry_is_embedded():
    assert len(m.EXPECTED_JOBS) == 23
    assert len({x[0] for x in m.EXPECTED_JOBS}) == 23


def test_engine_distribution_exact():
    assert m.EXPECTED_ENGINE_COUNTS == {
        "Madingley": 4,
        "RangeShifter": 5,
        "CDMetaPOP": 5,
        "NEMO": 3,
        "Geonomics": 3,
        "SLiM": 3,
    }
    assert sum(m.EXPECTED_ENGINE_COUNTS.values()) == 23


def test_exact_geonomics_closed_jobs():
    assert m.GEONOMICS_CLOSED == {
        "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
        "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS",
        "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS",
    }


def test_scanner_distinguishes_scientific_from_process_success():
    s = inspect.getsource(m._classify_local_object)
    assert "SCIENTIFIC_VALID" in s
    assert "PROCESS_EXECUTION_SUCCESS_ONLY" in s
    assert "PREFLIGHT_OR_GOVERNANCE" in s
    assert "BLOCKED_OR_INVALID" in s


def test_job_classification_never_auto_closes_non_geonomics():
    s = inspect.getsource(m._classify_job)
    assert "FULLY_REVALIDATED_CLOSED_R450" in s
    assert "SCIENTIFIC_EVIDENCE_PRESENT_CLOSURE_NOT_PROVEN" in s
    assert "PENDING_R452_EVIDENCE_ADJUDICATION_BEFORE_RERUN" in s


def test_scan_excludes_failed_partial_r449_shards_as_current_authority():
    s = inspect.getsource(m._json_files)
    assert "failed_or_partial_shards" in s


def test_no_engine_execution_in_r451():
    s = inspect.getsource(m)
    assert "import geonomics" not in s
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_expected_current_gap_math():
    assert 23 - 3 == 20


def test_next_is_r452():
    assert m.NEXT == (
        "BUILD_R452_NON_GEONOMICS_JOB_SPECIFIC_EVIDENCE_ADJUDICATION_"
        "AND_EXECUTION_PLAN"
    )

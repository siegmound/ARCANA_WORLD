import inspect
import arcana_worldsim.scientific_engines.r454_non_geonomics_exact_seed_readout_dry_run_authorization as m


def test_parent_hashes_are_frozen():
    assert m.EXPECTED_R452_PLAN_SHA256 == (
        "f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6"
    )
    assert m.EXPECTED_R453_REGISTRY_SHA256 == (
        "f39bb36251a95f2d9e310113a9286608d72188374d7d9bc73fe90aa697e5d380"
    )


def test_five_seed_modes_explicit():
    assert set(m.EXPECTED_SEED_MODES) == set(m.ENGINE_ORDER)
    assert m.EXPECTED_SEED_MODES["SLiM"] == "SLIM_COMMAND_LINE_MINUS_S_SEED"


def test_exact_ten_metric_ids():
    ids = set().union(*m.EXPECTED_METRICS.values())
    assert len(ids) == 10


def test_metric_validation_forbids_thresholds_and_auto_pass_fail():
    s = inspect.getsource(m._validate_metric)
    assert 'metric.get("numeric_acceptance_threshold") is not None' in s
    assert 'metric.get("automatic_pass_fail_from_value") is not False' in s


def test_probe_selection_is_deterministic_first_job():
    s = inspect.getsource(m._first_probe_jobs)
    assert "rows[0]" in s


def test_authorization_only_follows_all_checks():
    s = inspect.getsource(m.build)
    assert '"scientific_execution_authorized": bool(ok)' in s
    assert '"authorized_scientific_stream_count": 80 if ok else 0' in s


def test_r454_dry_run_is_not_scientific_evidence():
    s = inspect.getsource(m.build)
    assert '"dry_run_evidence_is_scientific_evidence": False' in s
    assert '"historical_execution_performed_in_r454": False' in s


def test_no_external_runtime_in_python_authority_module():
    s = inspect.getsource(m)
    assert "subprocess" not in s


def test_next_is_r455():
    assert m.NEXT == (
        "BUILD_R455_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_"
        "AND_EVIDENCE_CAPTURE"
    )

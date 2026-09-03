import inspect
import arcana_worldsim.scientific_engines.r452_non_geonomics_job_specific_evidence_adjudication_execution_plan as m


def test_exact_non_geonomics_engine_distribution():
    assert m.EXPECTED_COUNTS == {
        "Madingley": 4,
        "RangeShifter": 5,
        "CDMetaPOP": 5,
        "NEMO": 3,
        "SLiM": 3,
    }
    assert sum(m.EXPECTED_COUNTS.values()) == 20


def test_geonomics_jobs_are_explicitly_excluded():
    assert len(m.GEONOMICS_JOBS) == 3
    s = inspect.getsource(m._freeze_plan)
    assert "if jid in GEONOMICS_JOBS" in s


def test_seed_authority_is_discovered_not_invented():
    s = inspect.getsource(m._discover_frozen_seeds)
    assert "_seed_json_files" in s
    assert "_collect_job_seed_records" in s


def test_job_record_hash_binds_immutable_r42_record():
    s = inspect.getsource(m._freeze_plan)
    assert '"r42_job_record_sha256": _job_record_hash(job)' in s


def test_all_jobs_require_new_scientific_execution():
    s = inspect.getsource(m._freeze_plan)
    assert '"new_scientific_execution_required": True' in s
    assert '"promotion_candidate": False' in s


def test_r453_interface_and_readout_gate_is_explicit():
    s = inspect.getsource(m._freeze_plan)
    assert "ENGINE_SPECIFIC_READOUT_AUTHORITY_REQUIRED_R453" in s
    assert "ENGINE_SPECIFIC_SCIENTIFIC_INTERFACE_REQUIRED_R453" in s


def test_r452_does_not_authorize_execution():
    s = inspect.getsource(m._freeze_plan)
    assert '"scientific_execution_authorized": False' in s
    assert '"scientific_engine_execution_performed": False' in s


def test_no_external_engine_execution_in_r452():
    s = inspect.getsource(m)
    assert "subprocess" not in s
    assert "run_default_model(" not in s


def test_next_is_r453():
    assert m.NEXT == (
        "BUILD_R453_NON_GEONOMICS_SCIENTIFIC_EXECUTION_INTERFACE_"
        "AND_READOUT_AUTHORITY_PREFLIGHT"
    )

import inspect
import arcana_worldsim.scientific_engines.r453_non_geonomics_scientific_execution_interface_readout_authority_preflight as m


def test_parent_plan_hash_exact():
    assert m.EXPECTED_R452_PLAN_SHA256 == (
        "f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6"
    )


def test_five_engine_readout_authorities():
    assert set(m.READOUT_AUTHORITY) == {
        "Madingley", "RangeShifter", "CDMetaPOP", "NEMO", "SLiM"
    }


def test_exact_ten_metric_definitions():
    ids = [
        x["metric_id"]
        for a in m.READOUT_AUTHORITY.values()
        for x in a["metrics"]
    ]
    assert len(ids) == 10
    assert len(set(ids)) == 10


def test_cdmetapop_native_scientific_artifact_is_summary_not_file_count():
    a = m.READOUT_AUTHORITY["CDMetaPOP"]
    assert "summary_popAllTime.csv" in a["authorized_artifacts"]
    assert (
        "CDMETAPOP_OUTPUT_FILE_COUNT_AS_SCIENTIFIC_BIOLOGICAL_EVIDENCE"
        in m.FORBIDDEN
    )


def test_madingley_cannot_define_arcana_species_identity():
    assert "MADINGLEY_COHORT_AS_ARCANA_SPECIES_IDENTITY" in m.FORBIDDEN


def test_slim_raw_tree_sequence_is_primary_authorized_artifact():
    assert (
        m.READOUT_AUTHORITY["SLiM"]["authorized_artifacts"]
        == ["SLIM_TREE_SEQUENCE_RAW"]
    )


def test_r41_is_semantic_gate_not_historical_evidence():
    s = inspect.getsource(m._freeze_registry)
    assert '"r41_microbenchmarks_are_historical_scientific_evidence": False' in s


def test_r453_does_not_authorize_scientific_execution():
    s = inspect.getsource(m._freeze_registry)
    assert '"scientific_execution_authorized": False' in s
    assert '"dry_run_validated": False' in s


def test_no_external_execution_in_r453():
    s = inspect.getsource(m)
    assert "subprocess" not in s
    assert "run_default_model(" not in s


def test_next_is_r454():
    assert m.NEXT == (
        "BUILD_R454_NON_GEONOMICS_EXACT_SEED_INJECTION_READOUT_EXTRACTION_"
        "DRY_RUN_AND_SCHEMA_VALIDATION"
    )

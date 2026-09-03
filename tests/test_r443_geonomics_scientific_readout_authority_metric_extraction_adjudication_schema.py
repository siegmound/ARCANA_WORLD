import inspect
import arcana_worldsim.scientific_engines.r443_geonomics_scientific_readout_authority_metric_extraction_adjudication_schema as m


def test_five_unique_metric_definitions():
    r = m._readout_registry()
    assert r["unique_metric_definition_count"] == 5


def test_j14_j18_only_one_scientific_descriptive_metric():
    r = m._readout_registry()
    for job in (m.J14, m.J18):
        mids = r["jobs"][job]["authorized_metrics"]
        assert mids == [
            "GNX_CARRIER_COORDINATE_READBACK_XY",
            "GNX_CARRIER_NATIVE_CELL_READBACK_IJ",
            "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE",
        ]


def test_j21_exact_two_metric_ids():
    r = m._readout_registry()
    assert r["jobs"][m.J21]["authorized_metrics"] == [
        "GNX_NATIVE_LAYER_RASTER_READBACK",
        "GNX_NATIVE_LAYER_DESCRIPTIVE_SUMMARY",
    ]


def test_density_and_population_history_are_forbidden():
    r = m._readout_registry()
    ids = {x["readout"] for x in r["forbidden_readouts"]}
    assert "Species.N_or_calc_density_as_population_density" in ids
    assert "Species.Nt_as_population_history" in ids
    assert "births_deaths_as_scientific_history" in ids


def test_nn_schema_has_no_threshold_or_normalization():
    s = m._extraction_schema(m._readout_registry())
    nn = s["carrier_nn_distance_schema"]
    assert nn["thresholding_authorized"] is False
    assert nn["normalization_authorized"] is False
    assert nn["rounding_authorized"] is False
    assert nn["raw_vector_preserved"] is True


def test_adjudication_forbids_result_selection_and_majority_vote():
    a = m._adjudication_schema()
    assert a["adjudicative_numeric_threshold_count"] == 0
    assert a["global_rules"]["majority_vote_authorized"] is False
    assert a["global_rules"]["result_selected_threshold_authorized"] is False
    assert a["global_rules"]["engine_output_target_definition_authorized"] is False
    assert a["global_rules"]["canonical_rewrite_authorized"] is False


def test_r443_does_not_execute_model_or_extract_metrics():
    s = inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s
    assert "metric_extraction_dry_run_validated" in s


def test_next_is_r444():
    assert m.NEXT == (
        "BUILD_R444_GEONOMICS_READOUT_EXTRACTION_DRY_RUN_AND_ADJUDICATION_INPUT_"
        "VALIDATION"
    )

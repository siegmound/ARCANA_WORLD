import inspect
import arcana_worldsim.scientific_engines.r444_geonomics_readout_extraction_dry_run_adjudication_input_validation as m


def test_record_count_contract():
    assert 24 + 24 + 2352 == 2400
    assert 1208 + 1192 == 2400


def test_carrier_metrics_exact_ids():
    s = inspect.getsource(m._extract_carrier_metrics)
    assert "metric_id=MID_COORD" in s
    assert "metric_id=MID_CELL" in s
    assert "metric_id=MID_NN" in s
    assert m.MID_COORD == "GNX_CARRIER_COORDINATE_READBACK_XY"
    assert m.MID_CELL == "GNX_CARRIER_NATIVE_CELL_READBACK_IJ"
    assert m.MID_NN == "GNX_CARRIER_NEAREST_NEIGHBOR_DISTANCE"


def test_nn_uses_native_geonomics_kdtree():
    s = inspect.getsource(m._extract_carrier_metrics)
    assert "spp._kd_tree.tree.query(public_coords, k=2)" in s
    assert "numeric_acceptance_threshold" in s


def test_cell_readback_is_exact_floor_semantics():
    s = inspect.getsource(m._extract_carrier_metrics)
    assert "np.floor(expected_coords).astype(np.int32)" in s
    assert '"EXACT_INTEGRITY_ONLY"' in s


def test_j21_only_native_layers_and_two_states():
    s = inspect.getsource(m._run_j21_readout_dry_run)
    assert "len(dynamic_by_name) != 147" in inspect.getsource(m._prepare_j21_dynamic)
    assert "dynamic_sidecar_count" in s
    assert "state_index=0" in s
    assert "state_index=1" in s


def test_adjudication_has_no_numeric_threshold_or_majority_vote():
    s = inspect.getsource(m._adjudication_input)
    assert '"numeric_threshold_used": numeric_threshold_used' in s
    assert '"majority_vote_used": False' in s
    assert '"engine_output_defined_target": False' in s
    assert '"canonical_rewrite_performed": False' in s


def test_no_default_model_execution():
    s = inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_next_is_r445():
    assert m.NEXT == (
        "BUILD_R445_GEONOMICS_SCIENTIFIC_EXECUTION_AUTHORIZATION_AND_FIRST_"
        "GOVERNED_REVALIDATION_RUN_PREFLIGHT"
    )

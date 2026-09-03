import inspect
import arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers as m

def test_zip_return_contract_is_source_audited():
    s=inspect.getsource(m._install_geonomics_149_ndarray_change_dim_metadata_adapter)
    assert '"rast_series = list(zip(timesteps, rast_series))"' in s
    assert '"return(rast_series, dim, res, ulc, prj)"' in s

def test_series_items_are_timestep_raster_tuples():
    s=inspect.getsource(m._install_geonomics_149_ndarray_change_dim_metadata_adapter)
    assert "isinstance(step, tuple)" in s
    assert "len(step) == 2" in s
    assert "isinstance(step[0], (int, np.integer))" in s
    assert "isinstance(step[1], np.ndarray)" in s

def test_shape_check_targets_raster_tuple_element():
    s=inspect.getsource(m._install_geonomics_149_ndarray_change_dim_metadata_adapter)
    assert "step[1].shape" in s
    assert "r.shape" not in s

def test_timestep_labels_are_validated():
    s=inspect.getsource(m._install_geonomics_149_ndarray_change_dim_metadata_adapter)
    assert "[int(step[0]) for step in series]" in s
    assert "expected_timesteps" in s
    assert "timestep_labels_validated_count" in s

def test_exact_counts_are_gated():
    s=inspect.getsource(m)
    assert '"tuple_structure_validated_count"] == 1176' in s
    assert '"timestep_labels_validated_count"] == 1176' in s
    assert '"ndarray_change_tuple_structure_validation_count_all_replicates"' in s
    assert '"ndarray_change_timestep_label_validation_count_all_replicates"' in s
    assert "== 4704" in s

def test_no_execution_or_transpose():
    s=inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s
    assert "._make_change(" not in s
    assert "np.transpose(" not in s

import inspect
import arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers as m

def test_adapter_requires_exact_governed_source_semantics():
    s=inspect.getsource(m._install_geonomics_149_ndarray_change_dim_metadata_adapter)
    for token in ['"dim = change_rast.shape"','"start = start_rast.flatten()"','"end = change_rast.flatten()"','"start_rast.shape"']:
        assert token in s

def test_adapter_changes_only_dim_metadata_for_yx_raster():
    s=inspect.getsource(m._install_geonomics_149_ndarray_change_dim_metadata_adapter)
    assert 'shape == (layer_dim[1], layer_dim[0])' in s
    assert 'result = (series, lyr.dim, res, ulc, prj)' in s
    assert '"raster_transpose_performed": False' in s
    assert '"raster_values_modified": False' in s

def test_adapter_fails_closed_on_other_shapes():
    s=inspect.getsource(m._install_geonomics_149_ndarray_change_dim_metadata_adapter)
    assert 'rejected_shape_count' in s
    assert 'incompatible' in s

def test_adapter_is_restored_after_make_model():
    s=inspect.getsource(m._j21_dynamic_model_preflight)
    assert '_install_geonomics_149_ndarray_change_dim_metadata_adapter()' in s
    assert 'finally:' in s
    assert '_restore_geonomics_149_ndarray_change_dim_metadata_adapter' in s

def test_exact_repair_counts_are_required():
    s=inspect.getsource(m._j21_dynamic_model_preflight)
    assert 'compat_evidence["call_count"] == 1176' in s
    assert 'compat_evidence["metadata_repair_count"] == 1176' in s
    whole=inspect.getsource(m)
    assert 'ndarray_change_dim_metadata_repair_count_all_replicates' in whole
    assert '== 4704' in whole

def test_no_execution_or_raster_transform():
    s=inspect.getsource(m)
    assert 'run_default_model(' not in s
    assert '.walk(' not in s
    assert '.run(' not in s
    assert '._make_change(' not in s
    assert 'np.transpose(' not in s

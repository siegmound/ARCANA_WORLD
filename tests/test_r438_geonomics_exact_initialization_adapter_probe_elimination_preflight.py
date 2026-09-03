import inspect
import arcana_worldsim.scientific_engines.r438_geonomics_exact_initialization_adapter_probe_elimination_preflight as m

def test_coords_digest_exact_and_ordered():
    assert m._coords_digest([[1.,2.],[3.,4.]])==m._coords_digest([[1.,2.],[3.,4.]])
    assert m._coords_digest([[1.,2.],[3.,4.]])!=m._coords_digest([[3.,4.],[1.,2.]])

def test_adapter_source_never_reads_population_proxy_before_result_reporting():
    s=inspect.getsource(m._install_exact_nonliteral_carriers)
    body=s.split("return {")[0]
    assert 'population_proxy' not in body
    assert 'spp.clear(); spp.update(inds)' in s

def test_adapter_updates_orig_comm_and_native_caches():
    s=inspect.getsource(m._install_exact_nonliteral_carriers)
    for token in ['_set_coords_and_cells()','_set_kd_tree()','_set_dens_grids(mod.land)','_calc_density(set_N=True)','_set_e(mod.land)','mod.orig_comm=copy.deepcopy(mod.comm)']:
        assert token in s

def test_adapter_requires_nongenomic_probe_and_rand_comm_false():
    s=inspect.getsource(m._install_exact_nonliteral_carriers)
    assert 'spp.gen_arch is not None' in s
    assert 'mod.rand_comm is not False' in s

def test_no_population_add_remove_or_model_execution_calls():
    s=inspect.getsource(m)
    assert '._add_individuals(' not in s
    assert '._remove_individuals(' not in s
    assert '.add_individuals(' not in s
    assert 'run_default_model(' not in s
    assert '.walk(' not in s
    assert '.run(' not in s

def test_next_action_r439():
    assert m.NEXT=='BUILD_R439_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_AND_DYNAMIC_LAYER_CHANGE_PREFLIGHT'

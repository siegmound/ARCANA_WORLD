import numpy as np
import inspect
import arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers as m


def test_time_mapping_uniform_j14():
    a=np.array([3.0,2.98,2.96])
    r=m._time_mapping(a,job_id="x",physical_unit="Ma",years_multiplier=1e6)
    assert r["geonomics_T"]==2
    assert r["initial_model_t"]==-1
    assert r["final_model_t_after_T_steps"]==1
    assert r["uniform_physical_interval"] is True
    assert np.isclose(r["single_fixed_years_per_timestep_claim"],20000.0,rtol=0.0,atol=1e-6)


def test_time_mapping_irregular_preserves_variable_durations():
    a=np.array([20.,15.,14.,10.,0.])
    r=m._time_mapping(a,job_id="x",physical_unit="ka",years_multiplier=1000.)
    assert r["geonomics_T"]==4
    assert r["variable_duration_ordinal_transition_mapping"] is True
    assert r["physical_rate_mapping_authority_created"] is False
    assert [x["geonomics_timestep"] for x in r["transitions"]]==[0,1,2,3]


def test_exact_j21_change_schedule_uses_jump_events_only():
    s=inspect.getsource(m._add_exact_j21_change_schedule)
    assert '"start_t": t' in s
    assert '"end_t": t' in s
    assert '"n_steps": 1' in s
    assert 'p["model"]["T"] = 8' in s


def test_compiled_schedule_inspects_change_function_defaults():
    s=inspect.getsource(m._inspect_compiled_j21_schedule)
    assert '"__defaults__"' in s
    assert "compiled_change_target_exact_count" in s
    assert "schedule_count == 1176" in s
    assert "counts.get(t) == 147" in s


def test_carrier_dynamics_are_not_authorized():
    s=inspect.getsource(m._carrier_dynamics_authority_gate)
    for token in [
        '"autonomous_movement_authorized": False',
        '"autonomous_population_dynamics_authorized": False',
        '"autonomous_ageing_interpretation_authorized": False',
        '"default_main_fn_queue_scientific_execution_authorized": False',
    ]:
        assert token in s


def test_physical_sidecars_are_explicit():
    assert m.R439_DYNAMIC_SIDECAR_NAMES=={"temperature_anomaly_c","precipitation_factor","npp_factor","sea_level_anomaly_m"}


def test_no_model_execution_calls():
    s=inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s
    assert "._make_change(" not in s


def test_next_action_r440():
    assert m.NEXT=="BUILD_R440_GEONOMICS_DOMAIN_SPECIFIC_CARRIER_DYNAMICS_AUTHORITY_AND_EXECUTION_QUEUE_PREFLIGHT"


def test_ndarray_dim_metadata_adapter_is_metadata_only():
    s=inspect.getsource(m._install_geonomics_149_ndarray_change_dim_metadata_adapter)
    assert "dim = change_rast.shape" in s
    assert "shape == (layer_dim[1], layer_dim[0])" in s
    assert "result = (series, lyr.dim, res, ulc, prj)" in s
    assert '"raster_transpose_performed": False' in s
    assert '"raster_values_modified": False' in s


def test_dynamic_model_preflight_restores_dim_adapter():
    s=inspect.getsource(m._j21_dynamic_model_preflight)
    assert "_install_geonomics_149_ndarray_change_dim_metadata_adapter()" in s
    assert "_restore_geonomics_149_ndarray_change_dim_metadata_adapter" in s
    assert 'compat_evidence["metadata_repair_count"] == 1176' in s

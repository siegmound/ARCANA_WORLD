import inspect
from pathlib import Path
import arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers as m

def test_dynamic_sidecars_are_source_semantic_four():
    assert m.R439_DYNAMIC_SIDECAR_NAMES == {
        "temperature_anomaly_c",
        "precipitation_factor",
        "npp_factor",
        "sea_level_anomaly_m",
    }

def test_r437_static_sidecars_remain_historical_two():
    assert m.R437_STATIC_SIDECAR_NAMES == {
        "temperature_anomaly_c",
        "sea_level_anomaly_m",
    }

def test_r333_source_semantic_gate_is_hash_bound_and_not_live_minmax_based():
    s=inspect.getsource(m._r333_dynamic_representability_semantic_authority)
    assert m.R333_SOURCE_SHA256=="c32d78efcffccf60dd0a70870dc6d9555a9eed823ec4fa5e7fb3c2e61705fc40"
    assert "np.clip(P,0,1.5)" in s
    assert "np.clip(N,0,1.2)" in s
    assert '"live_minmax_used_to_define_transform": False' in s
    assert '"clipping_authorized": False' in s

def test_r4_37_bound_precip_npp_layers_are_removed_not_scaled():
    s=inspect.getsource(m._add_exact_j21_change_schedule)
    assert "del layers[lname]" in s
    assert "set(bound_dynamic_sidecars.values())" in s
    assert '"precipitation_factor"' in s
    assert '"npp_factor"' in s
    assert "np.clip" not in s

def test_refined_dynamic_counts():
    s=inspect.getsource(m)
    assert "len(native_records) == 147" in s
    assert "len(sidecar_records) == 4" in s
    assert "total_native_states == 1323" in s
    assert "future_change_targets == 1176" in s
    assert "counts.get(t) == 147" in s
    assert "schedule_count == 1176" in s

def test_no_execution_or_result_selected_transform():
    s=inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s
    assert "._make_change(" not in s

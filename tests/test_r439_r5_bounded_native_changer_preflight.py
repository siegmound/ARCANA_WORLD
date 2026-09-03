import inspect
import arcana_worldsim.scientific_engines.r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers as m

def test_probe_selection_is_deterministic():
    s=inspect.getsource(m._j21_dynamic_model_preflight); assert "probe_name = canonical_names[0]" in s; assert "FIRST_LAYER_IN_FROZEN_DYNAMIC_AUTHORITY_ORDER" in s
def test_probe_has_eight_changes():
    s=inspect.getsource(m._j21_dynamic_model_preflight); assert "for t in range(8):" in s; assert "BOUNDED_NATIVE_CHANGER_SCHEMA_PROBE" in s
def test_all_1176_targets_are_native_series_validated():
    s=inspect.getsource(m._j21_dynamic_model_preflight); assert "len(direct_records) == 1176" in s; assert "direct_pass_count == 1176" in s; assert "adapted(validation_layer, target, t, t, 1)" in s
def test_all_four_seeds_remain_required():
    s=inspect.getsource(m._j21_dynamic_model_preflight); assert "len(seed_binding_rows) == 4" in s; assert "all_four_frozen_seed_bindings_exact" in s
def test_no_full_changer_materialization():
    s=inspect.getsource(m._j21_dynamic_model_preflight); assert '\"full_147_layer_landscape_changer_materialized\": False' in s; assert '\"fourfold_redundant_changer_compilation_performed\": False' in s
def test_no_execution():
    s=inspect.getsource(m); assert "run_default_model(" not in s; assert ".walk(" not in s; assert ".run(" not in s; assert "._make_change(" not in s

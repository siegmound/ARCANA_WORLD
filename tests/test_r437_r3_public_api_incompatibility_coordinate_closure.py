import inspect
import arcana_worldsim.scientific_engines.r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run as m

def test_no_public_or_private_individual_mutation_in_r3_validation():
    s=inspect.getsource(m._exact_state_public_api_dry_run)
    assert "mod.add_individuals(" not in s
    assert "._add_individuals(" not in s
    assert "._remove_individuals(" not in s
    assert "spp.burned = True" not in s

def test_runtime_source_incompatibility_is_a_required_gate():
    s=inspect.getsource(m._exact_state_public_api_dry_run)
    assert "source_gen_arch.L" in s
    assert "self.gen_arch.L" in s
    assert "construction_probe_is_nongenomic" in s
    assert "public_api_exact_state_injection_compatible" in s

def test_all_coordinates_are_checked_against_actual_model_dims():
    s=inspect.getsource(m._exact_state_public_api_dry_run)
    assert "mod.land.dim" in s
    assert "dim[0] - 0.001" in s
    assert "dim[1] - 0.001" in s
    assert "canonical_coords" in s

def test_r438_remains_mandatory():
    assert m.NEXT=="BUILD_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT"

def test_no_model_execution_calls():
    s=inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s

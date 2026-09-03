from pathlib import Path
import inspect
import arcana_worldsim.scientific_engines.r432_target_authority_binding_geonomics_static as m

def test_r432_r2_uses_r423_profile_indirection_for_j18_j21():
    s = inspect.getsource(m._geo_profiles)
    assert "profile_path" in s
    assert "binding_materialized" in s
    assert "canonical_spatial_source" in s
    assert "canonical_spatial_sources" in s
    assert "binding_translation_materialized" not in s

def test_r432_r2_preserves_three_geonomics_jobs_and_no_runtime_execution():
    assert {m.J14,m.J18,m.J21} == {
        "R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS",
        "R42_J18_SAPIENT_200KA_TO_0_GEONOMICS",
        "R42_J21_PRODUCER_20KA_TO_0_GEONOMICS",
    }
    s = inspect.getsource(m._geo_profiles)
    assert "'runtime_parameter_compiled_count':0" in s
    assert "'external_engine_execution_authorized':False" in s

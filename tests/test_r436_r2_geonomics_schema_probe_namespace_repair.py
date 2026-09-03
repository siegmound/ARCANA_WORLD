from pathlib import Path
import numpy as np
import pytest
import arcana_worldsim.scientific_engines.r436_geonomics_native_parameter_model_construction_injection_preflight as m


def test_geonomics_probe_reader_repairs_only_missing_np_namespace(tmp_path):
    p=tmp_path/"probe.py"
    p.write_text("params={'landscape':{'layers':{'x':{'init':{'defined':{'rast':np.ones((2,3))}}}}}}\n")
    params,e=m._read_geonomics_generated_schema_probe(p)
    assert params["landscape"]["layers"]["x"]["init"]["defined"]["rast"].shape==(2,3)
    assert e["controlled_np_namespace_injected"] is True
    assert e["scope"]=="NON_SCIENTIFIC_SCHEMA_PROBE_ONLY"


def test_probe_reader_does_not_claim_scientific_authority(tmp_path):
    p=tmp_path/"probe.py"
    p.write_text("params={'x':np.ones((1,1))}\n")
    _,e=m._read_geonomics_generated_schema_probe(p)
    assert e["arcana_materialized_native_parameter_import_path_unchanged"] is True


def test_strict_native_import_remains_self_contained(tmp_path):
    p=tmp_path/"native.py"
    p.write_text("import numpy as np\nparams={'x':np.ones((1,2))}\n")
    params=m._import_params_module(p)
    assert params["x"].shape==(1,2)


def test_strict_native_import_still_rejects_missing_numpy_import(tmp_path):
    p=tmp_path/"bad_native.py"
    p.write_text("params={'x':np.ones((1,2))}\n")
    with pytest.raises(NameError):
        m._import_params_module(p)


def test_schema_probe_evidence_is_explicitly_non_scientific():
    import inspect
    s=inspect.getsource(m._make_template)
    assert '"scientific_evidence": False' in s
    assert "schema_probe_namespace_adapter" in s


def test_no_run_walk_or_default_model_added():
    import inspect
    s=inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s

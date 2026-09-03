from pathlib import Path
import importlib.util
import json
import tempfile


def _load_module():
    p = Path("scripts/r455_execution_source_introspection.py")
    spec = importlib.util.spec_from_file_location("r455i", p)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def test_expected_hashes_are_exact():
    m=_load_module()
    assert m.EXPECTED_PLAN_SHA == "f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6"
    assert m.EXPECTED_REGISTRY_SHA == "f39bb36251a95f2d9e310113a9286608d72188374d7d9bc73fe90aa697e5d380"


def test_five_non_geonomics_engines_exact():
    m=_load_module()
    assert m.ENGINE_ORDER == ["Madingley","RangeShifter","CDMetaPOP","NEMO","SLiM"]


def test_python_inspector_recovers_function_signature_and_literal_mapping(tmp_path):
    m=_load_module()
    p=tmp_path/"x.py"
    p.write_text(
        'ADAPTER_PATHS={"NEMO":"benchmarks/nemo.py"}\n'
        'def execute_job(job, seed=1):\n'
        '    import subprocess\n'
        '    return subprocess.run(["x"])\n'
    )
    r=m.inspect_python(p)
    assert r["parse_ok"]
    assert r["literal_bindings"]["ADAPTER_PATHS"]["NEMO"]=="benchmarks/nemo.py"
    assert any(x["name"]=="execute_job" for x in r["functions"])
    assert any("subprocess" in x["text"] for x in r["relevant_lines"])


def test_compactor_limits_large_lists():
    m=_load_module()
    r=m._compact({"seed_ledger":list(range(100))})
    assert r["seed_ledger"]["__list_len__"]==100


def test_source_globs_include_r421_r422_and_historical_r43_r47():
    m=_load_module()
    text="\n".join(m.SOURCE_GLOBS)
    assert "r421" in text
    assert "r422" in text
    assert "r43" in text
    assert "r47" in text


def test_helper_has_no_external_execution_import():
    s=Path("scripts/r455_execution_source_introspection.py").read_text()
    assert "import subprocess" not in s
    assert "subprocess.run(" not in s


def test_helper_is_explicitly_not_r455_scientific_stage():
    s=Path("scripts/r455_execution_source_introspection.py").read_text()
    assert '"scientific_evidence": False' in s
    assert '"engine_execution_performed": False' in s

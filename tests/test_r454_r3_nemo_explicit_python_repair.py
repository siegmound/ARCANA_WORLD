from pathlib import Path
import hashlib

POST={'capture_v0_6D1_R4_54_dry_runs.ps1': 'cea5fbb81a92937e904d0d36acc6be8c826d169fa74c92e43903c6f7f0a81e9c', 'benchmarks/r454/run_nemo_r454.sh': '04ebb845d7c5f8c6678d5ac5028729fdd83e0146cdd433fa4de1c9c775843fa4'}

def test_exact_postpatch_hashes():
    for rel,h in POST.items():
        assert hashlib.sha256(Path(rel).read_bytes()).hexdigest()==h

def test_nemo_wrapper_requires_explicit_collector_python():
    s=Path("benchmarks/r454/run_nemo_r454.sh").read_text()
    assert 'collector_python="$7"' in s
    assert '"$collector_python" - "$ini_src"' in s
    assert '"$collector_python" "$collector"' in s

def test_no_implicit_python_command_remains_in_nemo_wrapper():
    s=Path("benchmarks/r454/run_nemo_r454.sh").read_text()
    lines=[x.strip() for x in s.splitlines()]
    assert not any(x.startswith("python ") or x.startswith("python -") for x in lines)

def test_bridge_derives_python_from_governed_conda_binding():
    s=Path("capture_v0_6D1_R4_54_dry_runs.ps1").read_text()
    assert 'BASE_PY="`${CONDA_EXE%/conda}/python"' in s
    assert 'R454_NEMO_BASE_PYTHON_MISSING' in s

def test_bridge_passes_explicit_python_to_nemo_wrapper():
    s=Path("capture_v0_6D1_R4_54_dry_runs.ps1").read_text()
    assert '"`$ROOT/benchmarks/r454/nemo_collect_r454.py" "`$BASE_PY"' in s

def test_bridge_fallback_preserves_execution_diagnostics():
    s=Path("capture_v0_6D1_R4_54_dry_runs.ps1").read_text()
    assert "bridge_stdout_tail" in s
    assert "bridge_stderr_tail" in s
    assert "bridge_timed_out" in s

def test_bridge_fallback_preserves_nemo_probe_identity():
    s=Path("capture_v0_6D1_R4_54_dry_runs.ps1").read_text()
    assert '$e $p.JobId $p.Seed "NEMO_RANDOM_SEED_INI_PARAMETER"' in s

def test_nemo_scientific_collector_not_modified_by_r3():
    assert hashlib.sha256(
        Path("benchmarks/r454/nemo_collect_r454.py").read_bytes()
    ).hexdigest()=="4e588c5ac9be22ef6a7de11f3f8611bd750d4d7f2a86c416ac9a73f7730c7ffb"

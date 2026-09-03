from pathlib import Path

RUNNER = Path("run_v0_6D1_R4_36.ps1")


def _txt():
    return RUNNER.read_text(encoding="utf-8")


def test_runner_uses_existing_governed_geonomics_wsl_python():
    s=_txt()
    assert "/home/jose/miniforge3/envs/arcana-geonomics-149/bin/python" in s
    assert "wsl.exe" in s
    assert "wslpath" in s


def test_runner_preflights_exact_geonomics_version():
    s=_txt()
    assert 'print(gnx.__version__)' in s
    assert '$ResolvedVersion -ne "1.4.9"' in s


def test_runner_does_not_install_or_create_runtime():
    s=_txt().lower()
    assert "pip install" not in s
    assert "conda create" not in s
    assert "mamba create" not in s


def test_windows_remains_orchestrator_and_final_auditor():
    s=_txt()
    assert 'check_v0_6D1_R4_36_source_manifest.py' in s
    assert 'test_r436_geonomics_native_parameter_model_construction_injection_preflight.py' in s
    assert 'audit_v0_6D1_R4_36_seal.py' in s


def test_only_integrated_build_is_routed_through_wsl():
    s=_txt()
    assert "$WslScript = \"$WslRoot/scripts/run_v0_6D1_R4_36.py\"" in s
    assert "PYTHONPATH='$WslSrc'" in s
    assert "governed WSL Geonomics 1.4.9" in s

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "python"
if (Test-Path (Join-Path $Root ".venv\Scripts\python.exe")) {
    $Python = Join-Path $Root ".venv\Scripts\python.exe"
}
$env:PYTHONPATH = Join-Path $Root "src"
& $Python -m pytest -q (Join-Path $Root "tests\test_r321_present_lineage_registry.py")
if ($LASTEXITCODE -ne 0) { throw "R3.21 unit/closure tests failed." }
& $Python -m py_compile `
    (Join-Path $Root "src\arcana_worldsim\scientific_engines\r321_present_lineage_registry.py") `
    (Join-Path $Root "scripts\run_v0_6D1_R3_21_present_lineage_registry.py")
if ($LASTEXITCODE -ne 0) { throw "R3.21 compile check failed." }
Write-Host "PASS_R321_CANDIDATE_CHECKS"

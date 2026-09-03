$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$ROOT\src" + $(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" })

Write-Host "=== R3.23 source authority ==="
python "$ROOT\scripts\check_v0_6D1_R3_23_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.23 source manifest failed closed." }

Write-Host "=== R3.23 regression ==="
python -m pytest -q "$ROOT\tests\test_r323_functional_ensemble.py"
if ($LASTEXITCODE -ne 0) { throw "R3.23 regression failed closed." }

Write-Host "=== R3.23 integrated calibration + ensemble replay ==="
python "$ROOT\scripts\run_v0_6D1_R3_23.py" --root "$ROOT"
if ($LASTEXITCODE -ne 0) { throw "R3.23 integrated run failed closed." }

Write-Host "PASS_R323_INTEGRATED_CANDIDATE_RUN"

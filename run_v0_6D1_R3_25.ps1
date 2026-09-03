$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src;$env:PYTHONPATH"
Write-Host "=== R3.25 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_25_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.25 source manifest failed closed." }
Write-Host "=== R3.25 regression ==="
python -m pytest -q "$Root\tests\test_r325_h2_detailed_biology.py"
if ($LASTEXITCODE -ne 0) { throw "R3.25 regression failed closed." }
Write-Host "=== R3.25 H2 detailed biology + embodiment feasibility ==="
python "$Root\scripts\run_v0_6D1_R3_25.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.25 H2 run failed closed." }
Write-Host "=== R3.25 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_25_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.25 final seal failed closed." }
Write-Host "PASS_R325_INTEGRATED_AND_FINAL_SEAL_RUN"

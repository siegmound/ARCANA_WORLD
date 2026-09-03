$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src;$env:PYTHONPATH"
Write-Host "=== R3.24 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_24_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.24 source manifest failed closed." }
Write-Host "=== R3.24 regression ==="
python -m pytest -q "$Root\tests\test_r324_h1_candidate_discovery.py"
if ($LASTEXITCODE -ne 0) { throw "R3.24 regression failed closed." }
Write-Host "=== R3.24 H1 discovery + robustness ==="
python "$Root\scripts\run_v0_6D1_R3_24.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.24 H1 candidate discovery failed closed." }
Write-Host "=== R3.24 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_24_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.24 final seal failed closed." }
Write-Host "PASS_R324_INTEGRATED_AND_FINAL_SEAL_RUN"

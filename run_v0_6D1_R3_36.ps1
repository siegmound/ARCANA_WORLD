$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r336"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.36 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_36_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.36 source authority failed closed." }
Write-Host "=== R3.36 regression ==="
python -m pytest "$Root\tests\test_r336_producer_selection_ecology.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.36 regression failed closed." }
Write-Host "=== R3.36 producer selection-ecology + pathway resolution ==="
python "$Root\scripts\run_v0_6D1_R3_36.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.36 integrated stage failed closed." }
Write-Host "=== R3.36 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_36_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.36 final seal failed closed." }
Write-Host "PASS_R336_INTEGRATED_AND_FINAL_SEAL_RUN"

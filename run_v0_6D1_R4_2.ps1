$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r42"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R4.2 source authority ==="
python "$Root\scripts\check_v0_6D1_R4_2_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R4.2 source authority failed closed." }
Write-Host "=== R4.2 historical-window materialization regression ==="
python -m pytest "$Root\tests\test_r42_historical_materialization.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R4.2 regression failed closed." }
Write-Host "=== R4.2 baseline artifact registry + 23-job execution freeze ==="
python "$Root\scripts\run_v0_6D1_R4_2.py" --root "$Root"
$RunExit=$LASTEXITCODE
Write-Host "=== R4.2 final fail-closed seal ==="
python "$Root\scripts\audit_v0_6D1_R4_2_seal.py" --root "$Root"
$SealExit=$LASTEXITCODE
if ($RunExit -eq 3 -or $SealExit -eq 3) { Write-Host "R4.2 BLOCKED. Paste output; do not execute historical engine jobs yet."; exit 3 }
if ($RunExit -ne 0 -or $SealExit -ne 0) { throw "R4.2 failed closed." }
Write-Host "PASS_R42_INTEGRATED_AND_FINAL_SEAL_RUN"

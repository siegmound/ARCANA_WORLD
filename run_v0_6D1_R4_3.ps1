param(
  [switch]$PrepareOnly,
  [switch]$Smoke,
  [switch]$RepairNemo,
  [string]$JobId = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r43"
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}; New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R4.3 source authority ==="
python "$Root\scripts\check_v0_6D1_R4_3_source_manifest.py"
if($LASTEXITCODE -ne 0){throw "R4.3 source authority failed closed."}
Write-Host "=== R4.3 regression ==="
python -m pytest "$Root\tests\test_r43_historical_revalidation.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw "R4.3 regression failed closed."}
Write-Host "=== R4.3 governed execution bridge ==="
& "$Root\capture_v0_6D1_R4_3_historical_jobs.ps1" -PrepareOnly:$PrepareOnly -Smoke:$Smoke -RepairNemo:$RepairNemo -JobId $JobId
$RunExit=$LASTEXITCODE
if($RunExit -ne 0){exit $RunExit}
if($PrepareOnly -or $Smoke -or -not [string]::IsNullOrWhiteSpace($JobId)){exit 0}
Write-Host "=== R4.3 final fail-closed seal ==="
python "$Root\scripts\audit_v0_6D1_R4_3_seal.py" --root "$Root"
$SealExit=$LASTEXITCODE
if($SealExit -eq 3){Write-Host "R4.3 BLOCKED. Paste output; do not begin R4.4."; exit 3}
if($SealExit -ne 0){throw "R4.3 final seal failed closed."}
Write-Host "PASS_R43_INTEGRATED_AND_FINAL_SEAL_RUN"

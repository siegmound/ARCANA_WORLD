param(
  [switch]$PrepareOnly,
  [string]$JobId = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r47"
if(Test-Path $Tmp){Remove-Item -Recurse -Force $Tmp}; New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R4.7 source authority ==="
python "$Root\scripts\check_v0_6D1_R4_7_source_manifest.py"
if($LASTEXITCODE -ne 0){throw "R4.7 source authority failed closed."}
Write-Host "=== R4.7 regression ==="
python -m pytest "$Root\tests\test_r47_cdmetapop_forcing_parity.py" -q --basetemp "$Tmp" -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw "R4.7 regression failed closed."}
Write-Host "=== R4.7 governed CDMetaPOP forcing-parity reexecution ==="
& "$Root\capture_v0_6D1_R4_7_cdmetapop_jobs.ps1" -PrepareOnly:$PrepareOnly -JobId $JobId
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
if($PrepareOnly -or -not [string]::IsNullOrWhiteSpace($JobId)){exit 0}
Write-Host "=== R4.7 final fail-closed seal ==="
python "$Root\scripts\audit_v0_6D1_R4_7_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){Write-Host "R4.7 seal BLOCKED. Paste output."; exit 3}
Write-Host "PASS_R47_INTEGRATED_AND_FINAL_SEAL_RUN"

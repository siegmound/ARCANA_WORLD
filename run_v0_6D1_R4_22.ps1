param(
  [switch]$PrepareOnly,
  [switch]$CollectOnly,
  [string]$JobId = ""
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src" + ($(if($env:PYTHONPATH){";$env:PYTHONPATH"}else{""}))
$pytestBase = Join-Path $Root 'outputs\v0_6D1_R4_22\pytest_tmp'
$pytestParent = Split-Path -Parent $pytestBase
if(-not (Test-Path $pytestParent)) { New-Item -ItemType Directory -Path $pytestParent -Force | Out-Null }
Write-Host '=== R4.22 source authority ==='
python "$Root\scripts\check_v0_6D1_R4_22_source_manifest.py" "$Root"
if($LASTEXITCODE -ne 0){ exit 2 }
Write-Host '=== R4.22 regression (project-local pytest basetemp) ==='
python -m pytest -q "$Root\tests\test_r422_authorized_p2_reexecution.py" --basetemp "$pytestBase" -p no:cacheprovider
if($LASTEXITCODE -ne 0){ exit 2 }
Write-Host '=== R4.22 authorized P2 symmetric reexecution + deferred Geonomics completion audit ==='
& "$Root\capture_v0_6D1_R4_22_authorized_jobs.ps1" -PrepareOnly:$PrepareOnly -CollectOnly:$CollectOnly -JobId $JobId
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }
if($PrepareOnly -or -not [string]::IsNullOrWhiteSpace($JobId)){ exit 0 }
Write-Host '=== R4.22 final fail-closed seal ==='
python "$Root\scripts\audit_v0_6D1_R4_22_seal.py" --root "$Root"
if($LASTEXITCODE -ne 0){ Write-Host 'R4.22 seal BLOCKED. Preserve outputs/v0_6D1_R4_22 diagnostics.'; exit 4 }
Write-Host 'PASS_R422_INTEGRATED_AND_FINAL_SEAL_RUN'

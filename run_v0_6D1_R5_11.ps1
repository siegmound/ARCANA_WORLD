$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root 'src'
Write-Host '=== R5.11 source + R5.10 candidate / sealed R3.30 authority ==='
python (Join-Path $Root 'scripts/check_v0_6D1_R5_11_source_manifest.py') --root $Root
if ($LASTEXITCODE -ne 0) { throw 'R5.11 source authority failed closed.' }
Write-Host '=== R5.11 R3.30 reconciliation regression (project-local pytest basetemp) ==='
$BaseParent = Join-Path $Root '.pytest_tmp'
if (-not (Test-Path $BaseParent)) { New-Item -ItemType Directory -Force -Path $BaseParent | Out-Null }
$BaseTemp = Join-Path $BaseParent 'r511'
if (Test-Path $BaseTemp) { Remove-Item -Recurse -Force $BaseTemp }
python -m pytest -q (Join-Path $Root 'tests/test_r511_r330_census_group_reconciliation.py') --basetemp $BaseTemp
if ($LASTEXITCODE -ne 0) { throw 'R5.11 regression failed closed.' }
Write-Host '=== R5.11 runtime utility review + sealed R3.30 census/group reconciliation ==='
python (Join-Path $Root 'scripts/run_v0_6D1_R5_11.py') --root $Root
if ($LASTEXITCODE -ne 0) { throw 'R5.11 reconciliation failed closed.' }
Write-Host 'PASS_R511_R510_TO_R330_CENSUS_GROUP_ABM_RECONCILIATION_CANDIDATE_RUN'
Write-Host 'R5.11 remains CANDIDATE; R3.30 was not rerun and no external engine was executed. Downstream R3.31 is not auto-authorized.'

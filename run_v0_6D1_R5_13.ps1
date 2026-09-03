$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root 'src'
Write-Host '=== R5.13 source + R5.12 candidate / sealed R3.32 authority ==='
python (Join-Path $Root 'scripts/check_v0_6D1_R5_13_source_manifest.py') --root $Root
if ($LASTEXITCODE -ne 0) { throw 'R5.13 source authority failed closed.' }
Write-Host '=== R5.13 R3.32 reconciliation regression (project-local pytest basetemp) ==='
$BaseParent = Join-Path $Root '.pytest_tmp'
if (-not (Test-Path $BaseParent)) { New-Item -ItemType Directory -Force -Path $BaseParent | Out-Null }
$BaseTemp = Join-Path $BaseParent 'r513'
if (Test-Path $BaseTemp) { Remove-Item -Recurse -Force $BaseTemp }
python -m pytest -q (Join-Path $Root 'tests/test_r513_r332_subsistence_regional_readiness_reconciliation.py') --basetemp $BaseTemp
if ($LASTEXITCODE -ne 0) { throw 'R5.13 regression failed closed.' }
Write-Host '=== R5.13 runtime utility review + sealed R3.32 subsistence/regional-readiness reconciliation ==='
python (Join-Path $Root 'scripts/run_v0_6D1_R5_13.py') --root $Root
if ($LASTEXITCODE -ne 0) { throw 'R5.13 reconciliation failed closed.' }
Write-Host 'PASS_R513_R512_TO_R332_SUBSISTENCE_REGIONAL_READINESS_RECONCILIATION_CANDIDATE_RUN'
Write-Host 'R5.13 remains CANDIDATE; R3.32 was not scientifically rerun and no external engine was executed. Downstream R3.33 is not auto-authorized.'

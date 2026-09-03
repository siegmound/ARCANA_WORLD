$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root 'src'
Write-Host '=== R5.14 source + R5.13 candidate / sealed R3.33 authority ==='
python (Join-Path $Root 'scripts/check_v0_6D1_R5_14_source_manifest.py') --root $Root
if ($LASTEXITCODE -ne 0) { throw 'R5.14 source authority failed closed.' }
Write-Host '=== R5.14 R3.33 reconciliation regression (project-local pytest basetemp) ==='
$BaseParent = Join-Path $Root '.pytest_tmp'; if (-not (Test-Path $BaseParent)) { New-Item -ItemType Directory -Force -Path $BaseParent | Out-Null }
$BaseTemp = Join-Path $BaseParent 'r514'; if (Test-Path $BaseTemp) { Remove-Item -Recurse -Force $BaseTemp }
python -m pytest -q (Join-Path $Root 'tests/test_r514_r333_holocene_domestication_reconciliation.py') --basetemp $BaseTemp
if ($LASTEXITCODE -ne 0) { throw 'R5.14 regression failed closed.' }
Write-Host '=== R5.14 runtime utility review + sealed R3.33 Holocene domestication reconciliation ==='
python (Join-Path $Root 'scripts/run_v0_6D1_R5_14.py') --root $Root
if ($LASTEXITCODE -ne 0) { throw 'R5.14 reconciliation failed closed.' }
Write-Host 'PASS_R514_R513_TO_R333_HOLOCENE_DOMESTICATION_RECONCILIATION_CANDIDATE_RUN'
Write-Host 'R5.14 remains CANDIDATE; R3.33 was not scientifically rerun or mutated and no external engine was executed. Downstream R3.34 is not auto-authorized.'

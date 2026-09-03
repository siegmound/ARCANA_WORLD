$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root 'src'
Write-Host '=== R5.12 source + R5.11 candidate / sealed R3.31 authority ==='
python (Join-Path $Root 'scripts/check_v0_6D1_R5_12_source_manifest.py') --root $Root
if ($LASTEXITCODE -ne 0) { throw 'R5.12 source authority failed closed.' }
Write-Host '=== R5.12 R3.31 reconciliation regression (project-local pytest basetemp) ==='
$BaseParent = Join-Path $Root '.pytest_tmp'
if (-not (Test-Path $BaseParent)) { New-Item -ItemType Directory -Force -Path $BaseParent | Out-Null }
$BaseTemp = Join-Path $BaseParent 'r512'
if (Test-Path $BaseTemp) { Remove-Item -Recurse -Force $BaseTemp }
python -m pytest -q (Join-Path $Root 'tests/test_r512_r331_abstract_technological_ecology_reconciliation.py') --basetemp $BaseTemp
if ($LASTEXITCODE -ne 0) { throw 'R5.12 regression failed closed.' }
Write-Host '=== R5.12 runtime utility review + sealed R3.31 abstract technological-ecology reconciliation ==='
python (Join-Path $Root 'scripts/run_v0_6D1_R5_12.py') --root $Root
if ($LASTEXITCODE -ne 0) { throw 'R5.12 reconciliation failed closed.' }
Write-Host 'PASS_R512_R511_TO_R331_ABSTRACT_CULTURAL_TECHNOLOGICAL_ECOLOGY_RECONCILIATION_CANDIDATE_RUN'
Write-Host 'R5.12 remains CANDIDATE; R3.31 was not scientifically rerun and no external engine was executed. Downstream R3.32 is not auto-authorized.'

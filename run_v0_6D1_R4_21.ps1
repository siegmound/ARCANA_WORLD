$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$env:PYTHONPATH = "$root\src" + ($(if($env:PYTHONPATH){";$env:PYTHONPATH"}else{""}))
$pytestBase = Join-Path $root 'outputs\v0_6D1_R4_21\pytest_tmp'
$pytestParent = Split-Path -Parent $pytestBase
if(-not (Test-Path $pytestParent)) { New-Item -ItemType Directory -Path $pytestParent -Force | Out-Null }
Write-Host '=== R4.21 source authority ==='
python .\scripts\check_v0_6D1_R4_21_source_manifest.py .
if($LASTEXITCODE -ne 0){ exit 2 }
Write-Host '=== R4.21 regression (project-local pytest basetemp) ==='
python -m pytest -q .\tests\test_r421_p2_static_validation_reexecution_authorization.py --basetemp "$pytestBase"
if($LASTEXITCODE -ne 0){ exit 2 }
Write-Host '=== R4.21 P2 static validation + symmetric reexecution authorization ==='
python .\scripts\run_v0_6D1_R4_21.py --root .
if($LASTEXITCODE -ne 0){ Write-Host 'R4.21 BLOCKED. Preserve outputs/v0_6D1_R4_21 diagnostics.'; exit 3 }
Write-Host '=== R4.21 final fail-closed seal ==='
python .\scripts\audit_v0_6D1_R4_21_seal.py --root .
if($LASTEXITCODE -ne 0){ exit 4 }
Write-Host 'PASS_R421_INTEGRATED_AND_FINAL_SEAL_RUN'

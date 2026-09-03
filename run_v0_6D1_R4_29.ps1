param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = "$Root\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$PytestTmp = Join-Path $Root "outputs\v0_6D1_R4_29\pytest_tmp"
New-Item -ItemType Directory -Force -Path $PytestTmp | Out-Null
Write-Host "=== R4.29 source authority ==="
& $Python scripts\check_v0_6D1_R4_29_source_manifest.py $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R4.29 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q tests\test_r429_selector_authority_design_validation_j14_authorization.py --basetemp $PytestTmp
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R4.29 explicit selector authority + schemaless closure + target-design validation + J14 execution authorization ==="
& $Python scripts\run_v0_6D1_R4_29.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.29 BLOCKED."; exit $LASTEXITCODE }
Write-Host "=== R4.29 final fail-closed seal ==="
& $Python scripts\audit_v0_6D1_R4_29_seal.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.29 FINAL SEAL BLOCKED."; exit $LASTEXITCODE }
Write-Host "PASS_R429_INTEGRATED_AND_FINAL_SEAL_RUN"

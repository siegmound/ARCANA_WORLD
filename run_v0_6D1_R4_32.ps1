param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = "$Root\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$PytestTmp = Join-Path $Root "outputs\v0_6D1_R4_32\pytest_tmp"
New-Item -ItemType Directory -Force -Path $PytestTmp | Out-Null
Write-Host "=== R4.32 source authority ==="
& $Python scripts\check_v0_6D1_R4_32_source_manifest.py $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R4.32 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q tests\test_r432_target_authority_binding_geonomics_static.py --basetemp $PytestTmp
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R4.32 target authority binding + Geonomics canonical parameter static validation ==="
& $Python scripts\run_v0_6D1_R4_32.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.32 BLOCKED."; exit $LASTEXITCODE }
Write-Host "=== R4.32 final fail-closed seal ==="
& $Python scripts\audit_v0_6D1_R4_32_seal.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.32 FINAL SEAL BLOCKED."; exit $LASTEXITCODE }
Write-Host "PASS_R432_INTEGRATED_AND_FINAL_SEAL_RUN"

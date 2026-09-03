param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = "$Root\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$PytestTmp = Join-Path $Root "outputs\v0_6D1_R4_25\pytest_tmp"
New-Item -ItemType Directory -Force -Path $PytestTmp | Out-Null

Write-Host "=== R4.25 source authority ==="
& $Python scripts\check_v0_6D1_R4_25_source_manifest.py $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.25 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q tests\test_r425_target_protocol_preflight_geonomics_j14_discovery.py --basetemp $PytestTmp
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.25 target protocol repair preflight + Geonomics J14 spatial-authority discovery ==="
& $Python scripts\run_v0_6D1_R4_25.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.25 BLOCKED."; exit $LASTEXITCODE }

Write-Host "=== R4.25 final fail-closed seal ==="
& $Python scripts\audit_v0_6D1_R4_25_seal.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.25 FINAL SEAL BLOCKED."; exit $LASTEXITCODE }

Write-Host "PASS_R425_INTEGRATED_AND_FINAL_SEAL_RUN"

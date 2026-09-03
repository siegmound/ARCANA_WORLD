param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = "$Root\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$PytestTmp = Join-Path $Root "outputs\v0_6D1_R4_26\pytest_tmp"
New-Item -ItemType Directory -Force -Path $PytestTmp | Out-Null

Write-Host "=== R4.26 source authority ==="
& $Python scripts\check_v0_6D1_R4_26_source_manifest.py $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.26 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q tests\test_r426_target_extractor_implementation_j14_authority_request.py --basetemp $PytestTmp
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.26 target extractor implementation + Geonomics J14 new spatial-authority request freeze ==="
& $Python scripts\run_v0_6D1_R4_26.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.26 BLOCKED."; exit $LASTEXITCODE }

Write-Host "=== R4.26 final fail-closed seal ==="
& $Python scripts\audit_v0_6D1_R4_26_seal.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.26 FINAL SEAL BLOCKED."; exit $LASTEXITCODE }

Write-Host "PASS_R426_INTEGRATED_AND_FINAL_SEAL_RUN"

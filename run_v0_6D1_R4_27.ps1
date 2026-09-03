param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = "$Root\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$PytestTmp = Join-Path $Root "outputs\v0_6D1_R4_27\pytest_tmp"
New-Item -ItemType Directory -Force -Path $PytestTmp | Out-Null

Write-Host "=== R4.27 source authority ==="
& $Python scripts\check_v0_6D1_R4_27_source_manifest.py $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.27 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q tests\test_r427_target_extractor_static_validation_authority_adjudication.py --basetemp $PytestTmp
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.27 extractor static validation + target/J14 authority request adjudication ==="
& $Python scripts\run_v0_6D1_R4_27.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.27 BLOCKED."; exit $LASTEXITCODE }

Write-Host "=== R4.27 final fail-closed seal ==="
& $Python scripts\audit_v0_6D1_R4_27_seal.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.27 FINAL SEAL BLOCKED."; exit $LASTEXITCODE }

Write-Host "PASS_R427_INTEGRATED_AND_FINAL_SEAL_RUN"

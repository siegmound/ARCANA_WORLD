param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONPATH = "$Root\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$PytestTmp = Join-Path $Root "outputs\v0_6D1_R4_23\pytest_tmp"
New-Item -ItemType Directory -Force -Path $PytestTmp | Out-Null

Write-Host "=== R4.23 source authority ==="
& $Python scripts\check_v0_6D1_R4_23_source_manifest.py $Root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.23 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q tests\test_r423_p2_evidence_normalization_geonomics_binding.py --basetemp $PytestTmp
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.23 P2 evidence normalization + Geonomics canonical spatial binding completion audit ==="
& $Python scripts\run_v0_6D1_R4_23.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.23 BLOCKED."; exit $LASTEXITCODE }

Write-Host "=== R4.23 final fail-closed seal ==="
& $Python scripts\audit_v0_6D1_R4_23_seal.py --root $Root
if ($LASTEXITCODE -ne 0) { Write-Host "R4.23 FINAL SEAL BLOCKED."; exit $LASTEXITCODE }

Write-Host "PASS_R423_INTEGRATED_AND_FINAL_SEAL_RUN"

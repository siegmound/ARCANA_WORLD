param([string]$Python = "python")
$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$env:PYTHONPATH = (Join-Path $Root "src")
$PytestBase = Join-Path $Root ".pytest_tmp_r435"
if (Test-Path $PytestBase) { Remove-Item -Recurse -Force $PytestBase }

Write-Host "=== R4.35 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_35_source_manifest.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.35 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q ".\tests\test_r435_geonomics_native_schema_initial_state_seed_closure.py" --basetemp $PytestBase
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.35 Geonomics native schema + exact initial-state adapter + seed authority closure ==="
& $Python ".\scripts\run_v0_6D1_R4_35.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "R4.35 BLOCKED"
    exit $LASTEXITCODE
}

Write-Host "=== R4.35 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_35_seal.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "R4.35 FINAL SEAL BLOCKED"
    exit $LASTEXITCODE
}

Write-Host "PASS_R435_INTEGRATED_AND_FINAL_SEAL_RUN"

param([string]$Python = "python")
$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$env:PYTHONPATH = (Join-Path $Root "src")
$PytestBase = Join-Path $Root ".pytest_tmp_r434"
if (Test-Path $PytestBase) { Remove-Item -Recurse -Force $PytestBase }

Write-Host "=== R4.34 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_34_source_manifest.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.34 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q ".\tests\test_r434_geonomics_selector_authority_native_parameter_preflight.py" --basetemp $PytestBase
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.34 Geonomics selector authority freeze + native parameter materialization preflight ==="
& $Python ".\scripts\run_v0_6D1_R4_34.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "R4.34 BLOCKED"
    exit $LASTEXITCODE
}

Write-Host "=== R4.34 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_34_seal.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "R4.34 FINAL SEAL BLOCKED"
    exit $LASTEXITCODE
}

Write-Host "PASS_R434_INTEGRATED_AND_FINAL_SEAL_RUN"

param([string]$Python = "python")
$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$env:PYTHONPATH = (Join-Path $Root "src")
$PytestBase = Join-Path $Root ".pytest_tmp_r433"
if (Test-Path $PytestBase) { Remove-Item -Recurse -Force $PytestBase }

Write-Host "=== R4.33 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_33_source_manifest.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.33 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q ".\tests\test_r433_target_binding_static_adjudication_geonomics_runtime_preflight.py" --basetemp $PytestBase
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== R4.33 target binding static adjudication + Geonomics runtime parameter compilation preflight ==="
& $Python ".\scripts\run_v0_6D1_R4_33.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "R4.33 BLOCKED"
    exit $LASTEXITCODE
}

Write-Host "=== R4.33 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_33_seal.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "R4.33 FINAL SEAL BLOCKED"
    exit $LASTEXITCODE
}

Write-Host "PASS_R433_INTEGRATED_AND_FINAL_SEAL_RUN"

param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r436"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.36 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_36_source_manifest.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36 regression (project-local pytest basetemp) ==="
& $Python -m pytest -q ".\tests\test_r436_geonomics_native_parameter_model_construction_injection_preflight.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36 native params + make_model construction + exact-state injection preflight ==="
& $Python ".\scripts\run_v0_6D1_R4_36.py"
if($LASTEXITCODE -ne 0){
  Write-Host "R4.36 BLOCKED"
  exit $LASTEXITCODE
}

Write-Host "=== R4.36 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_36_seal.py"
if($LASTEXITCODE -ne 0){
  Write-Host "R4.36 FINAL SEAL BLOCKED"
  exit $LASTEXITCODE
}

Write-Host "PASS_R436_INTEGRATED_AND_FINAL_SEAL_RUN"

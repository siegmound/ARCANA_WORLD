param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$PytestBase=Join-Path $Root ".pytest_tmp_r432_r2"
if(Test-Path $PytestBase){ Remove-Item -Recurse -Force $PytestBase }

Write-Host "=== R4.32-R2 precondition proof + profile-indirection repair ==="
& $Python ".\tools\r4_32_r2_apply_profile_indirection_repair.py" --root .
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.32-R2 dedicated repair regression ==="
& $Python -m pytest -q ".\tests\test_r432_r2_r423_profile_indirection_repair.py" --basetemp $PytestBase
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.32 full rerun under repaired source authority ==="
& ".\run_v0_6D1_R4_32.ps1"
if($LASTEXITCODE -ne 0){
  Write-Host "R4.32-R2: repaired R4.32 rerun BLOCKED. Preserve outputs for diagnosis."
  exit $LASTEXITCODE
}

Write-Host "=== R4.32-R2 postrepair reseal verification ==="
& $Python ".\tools\r4_32_r2_postrepair_reseal_audit.py" --root .
exit $LASTEXITCODE

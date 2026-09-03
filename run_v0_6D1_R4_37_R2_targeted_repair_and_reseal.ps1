param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r437_r2"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.37-R2 apply targeted native-representability + public-API compatibility repair ==="
& $Python ".\tools\r4_37_r2_apply_targeted_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.37-R2 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r437_r2_targeted_repair.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.37 rerun with targeted repair ==="
& ".\run_v0_6D1_R4_37.ps1"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.37-R2: R4.37 remains BLOCKED. Preserve outputs."
    exit $LASTEXITCODE
}

Write-Host "=== R4.37-R2 postrepair reseal verification ==="
& $Python ".\tools\r4_37_r2_postrepair_reseal_audit.py"
exit $LASTEXITCODE

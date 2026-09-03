param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r437_r3"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.37-R3 apply public-API incompatibility + coordinate representability closure ==="
& $Python ".\tools\r4_37_r3_apply_closure_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.37-R3 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r437_r3_public_api_incompatibility_coordinate_closure.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.37 rerun with validation-closure semantics ==="
& ".\run_v0_6D1_R4_37.ps1"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.37-R3: R4.37 remains BLOCKED. Preserve outputs."
    exit $LASTEXITCODE
}

Write-Host "=== R4.37-R3 postrepair reseal verification ==="
& $Python ".\tools\r4_37_r3_postrepair_reseal_audit.py"
exit $LASTEXITCODE

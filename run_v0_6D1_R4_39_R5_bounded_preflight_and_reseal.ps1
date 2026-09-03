param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r439_r5"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.39-R5 apply bounded native changer preflight repair ==="
& $Python ".\tools\r4_39_r5_apply_bounded_preflight_repair.py"
if($LASTEXITCODE -ne 0){
    exit $LASTEXITCODE
}

Write-Host "=== R4.39-R5 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r439_r5_bounded_native_changer_preflight.py" --basetemp $Base
if($LASTEXITCODE -ne 0){
    exit $LASTEXITCODE
}

Write-Host "=== R4.39 full rerun with bounded native changer preflight ==="
& ".\run_v0_6D1_R4_39.ps1"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.39-R5: R4.39 remains BLOCKED. Preserve outputs."
    exit $LASTEXITCODE
}

Write-Host "=== R4.39-R5 postrepair reseal verification ==="
& $Python ".\tools\r4_39_r5_postrepair_reseal_audit.py"
exit $LASTEXITCODE

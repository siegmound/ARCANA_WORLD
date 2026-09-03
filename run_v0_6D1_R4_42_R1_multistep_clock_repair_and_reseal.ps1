param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r442_r1"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.42-R1 apply multi-step clock validation repair ==="
& $Python ".\tools\r4_42_r1_apply_multistep_clock_repair.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.42-R1 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r442_r1_multistep_clock_repair.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.42 full rerun with multi-step clock validation ==="
& ".\run_v0_6D1_R4_42.ps1"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.42-R1: R4.42 remains BLOCKED. Preserve outputs."
    exit $LASTEXITCODE
}

Write-Host "=== R4.42-R1 postrepair reseal verification ==="
& $Python ".\tools\r4_42_r1_postrepair_reseal_audit.py"
exit $LASTEXITCODE

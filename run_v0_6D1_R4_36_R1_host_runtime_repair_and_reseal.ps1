param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r436_r1"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.36-R1 apply governed WSL host-runtime bridge repair ==="
& $Python ".\tools\r4_36_r1_apply_host_runtime_bridge_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36-R1 dedicated host-runtime bridge regression ==="
& $Python -m pytest -q ".\tests\test_r436_r1_host_runtime_bridge_repair.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36 full rerun through repaired R4.0-style host-runtime boundary ==="
& ".\run_v0_6D1_R4_36.ps1"
if($LASTEXITCODE -ne 0){
  Write-Host "R4.36-R1: R4.36 remains BLOCKED. Preserve outputs."
  exit $LASTEXITCODE
}

Write-Host "=== R4.36-R1 postrepair reseal verification ==="
& $Python ".\tools\r4_36_r1_postrepair_reseal_audit.py"
exit $LASTEXITCODE

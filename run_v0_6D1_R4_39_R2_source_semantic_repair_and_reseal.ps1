param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r439_r2"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.39-R2 apply R3.33 source-semantic dynamic representability repair ==="
& $Python ".\tools\r4_39_r2_apply_source_semantic_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.39-R2 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r439_r2_r333_source_semantic_dynamic_representability_repair.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.39 full rerun with source-semantic dynamic partition ==="
& ".\run_v0_6D1_R4_39.ps1"
if($LASTEXITCODE -ne 0){
  Write-Host "R4.39-R2: R4.39 remains BLOCKED. Preserve outputs."
  exit $LASTEXITCODE
}

Write-Host "=== R4.39-R2 postrepair reseal verification ==="
& $Python ".\tools\r4_39_r2_postrepair_reseal_audit.py"
exit $LASTEXITCODE

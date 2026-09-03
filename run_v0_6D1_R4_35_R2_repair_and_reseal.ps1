param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r435_r2"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.35-R2 apply schema-true repair + preserve prepatch evidence ==="
& $Python ".\tools\r4_35_r2_apply_schema_true_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.35-R2 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r435_r2_schema_true_repair.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.35 full rerun under repaired authority readers ==="
& ".\run_v0_6D1_R4_35.ps1"
if($LASTEXITCODE -ne 0){
  Write-Host "R4.35-R2: R4.35 remains BLOCKED. Preserve outputs."
  exit $LASTEXITCODE
}

Write-Host "=== R4.35-R2 postrepair reseal verification ==="
& $Python ".\tools\r4_35_r2_postrepair_reseal_audit.py"
exit $LASTEXITCODE

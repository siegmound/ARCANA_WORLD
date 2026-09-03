param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r436_r2"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.36-R2 apply Geonomics defined-layer schema-probe namespace repair ==="
& $Python ".\tools\r4_36_r2_apply_schema_probe_namespace_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36-R2 dedicated schema-probe regression ==="
& $Python -m pytest -q ".\tests\test_r436_r2_geonomics_schema_probe_namespace_repair.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36 full rerun through R1 governed WSL bridge + R2 schema-probe repair ==="
& ".\run_v0_6D1_R4_36.ps1"
if($LASTEXITCODE -ne 0){
  Write-Host "R4.36-R2: R4.36 remains BLOCKED. Preserve outputs."
  exit $LASTEXITCODE
}

Write-Host "=== R4.36-R2 postrepair reseal verification ==="
& $Python ".\tools\r4_36_r2_postrepair_reseal_audit.py"
exit $LASTEXITCODE

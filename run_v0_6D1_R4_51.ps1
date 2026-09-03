param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r451"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.51 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_51_source_manifest.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.51 regression ==="
& $Python -m pytest -q ".\tests\test_r451_multi_engine_23_job_reconciliation_revalidation_gap_census.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.51 immutable R4.2 23-job reconciliation + evidence gap census ==="
& $Python ".\scripts\run_v0_6D1_R4_51.py"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.51 BLOCKED. No prior evidence is promoted and no engine is executed."
    exit $LASTEXITCODE
}

Write-Host "=== R4.51 final fail-closed census seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_51_seal.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "PASS_R451_INTEGRATED_AND_FINAL_SEAL_RUN"

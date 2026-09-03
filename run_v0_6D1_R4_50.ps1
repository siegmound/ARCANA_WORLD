param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r450"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.50 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_50_source_manifest.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.50 regression ==="
& $Python -m pytest -q ".\tests\test_r450_geonomics_full_job_revalidation_evidence_review_final_closure.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.50 independent full Geonomics evidence corpus review ==="
& $Python ".\scripts\run_v0_6D1_R4_50.py"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.50 BLOCKED. No Geonomics evidence is modified."
    exit $LASTEXITCODE
}

Write-Host "=== R4.50 final fail-closed Geonomics closure seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_50_seal.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "PASS_R450_INTEGRATED_AND_FINAL_SEAL_RUN"

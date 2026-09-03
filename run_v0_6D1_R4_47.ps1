param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r447"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.47 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_47_source_manifest.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.47 regression ==="
& $Python -m pytest -q ".\tests\test_r447_geonomics_first_governed_revalidation_evidence_review_cohort_adjudication_closure.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.47 governed evidence review + cohort adjudication closure ==="
& $Python ".\scripts\run_v0_6D1_R4_47.py"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.47 BLOCKED. Preserve R4.46 scientific evidence."
    exit $LASTEXITCODE
}

Write-Host "=== R4.47 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_47_seal.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "PASS_R447_INTEGRATED_AND_FINAL_SEAL_RUN"

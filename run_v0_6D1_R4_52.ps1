param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r452"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.52 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_52_source_manifest.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.52 regression ==="
& $Python -m pytest -q ".\tests\test_r452_non_geonomics_job_specific_evidence_adjudication_execution_plan.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.52 freeze exact 20-job non-Geonomics scientific execution plan ==="
& $Python ".\scripts\run_v0_6D1_R4_52.py"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.52 BLOCKED. No external engine is executed."
    exit $LASTEXITCODE
}

Write-Host "=== R4.52 final fail-closed plan seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_52_seal.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "PASS_R452_INTEGRATED_AND_FINAL_SEAL_RUN"

param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=Join-Path $Root "src"

$Base=Join-Path $Root ".pytest_tmp_r456"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.56 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_56_source_manifest.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.56 regression ==="
& $Python -m pytest -q ".\tests\test_r456_multi_engine_23_job_full_evidence_review_final_revalidation_closure.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.56 independent 20-job R4.55 review + R4.50 Geonomics closure reuse ==="
& $Python ".\scripts\run_v0_6D1_R4_56.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.56 final fail-closed 23-job multi-engine revalidation seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_56_seal.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "PASS_R456_INTEGRATED_AND_FINAL_SEAL_RUN"

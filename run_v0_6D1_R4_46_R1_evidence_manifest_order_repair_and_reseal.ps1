param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r446_r1"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.46-R1 apply evidence-manifest metric-id order repair ==="
& $Python ".\tools\r4_46_r1_apply_evidence_manifest_order_repair.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.46 patched source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_46_source_manifest.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.46 original regression after repair ==="
& $Python -m pytest -q ".\tests\test_r446_geonomics_first_governed_revalidation_cohort_execution_evidence_capture.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.46-R1 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r446_r1_evidence_manifest_metric_id_order_repair.py" --basetemp "$Base-r1"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.46-R1 reseal existing scientific evidence WITHOUT rerun ==="
& $Python ".\tools\r4_46_r1_reseal_existing_scientific_evidence.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.46-R1 postrepair reseal verification ==="
& $Python ".\tools\r4_46_r1_postrepair_reseal_audit.py"
exit $LASTEXITCODE

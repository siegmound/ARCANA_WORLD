param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r454_r2"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.54-R2 apply NEMO result-capture + SLiM divergence API repair ==="
& $Python ".\scripts\apply_v0_6D1_R4_54_R2_nemo_slim_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 patched source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_54_source_manifest.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 original regression after R2 repair ==="
& $Python -m pytest -q ".\tests\test_r454_non_geonomics_exact_seed_readout_dry_run_authorization.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54-R2 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r454_r2_nemo_slim_repair.py" --basetemp ($Base+"_r2")
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 rerun disposable five-engine dry-run gate after targeted NEMO/SLiM repair ==="
& ".\run_v0_6D1_R4_54.ps1" -Python $Python
if($LASTEXITCODE -ne 0){
  Write-Host "R4.54 remains BLOCKED. Preserve R4.54-R2 diagnostics; do not proceed to R4.55."
  exit $LASTEXITCODE
}

Write-Host "=== R4.54-R2 postrepair reseal verification ==="
& $Python ".\scripts\audit_v0_6D1_R4_54_R2_postrepair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "PASS_R454_R2_NEMO_SLIM_REPAIR_AND_R454_RESEAL_RUN"

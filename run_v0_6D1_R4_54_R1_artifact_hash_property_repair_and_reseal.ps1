param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r454_r1"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.54-R1 apply PowerShell artifact_hashes materialization repair ==="
& $Python ".\scripts\apply_v0_6D1_R4_54_R1_artifact_hash_property_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 patched source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_54_source_manifest.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 original regression after repair ==="
& $Python -m pytest -q ".\tests\test_r454_non_geonomics_exact_seed_readout_dry_run_authorization.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54-R1 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r454_r1_artifact_hash_property_repair.py" --basetemp ($Base + "_r1")
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 rerun disposable dry-run gate + authorization after bridge repair ==="
& ".\run_v0_6D1_R4_54.ps1" -Python $Python
if($LASTEXITCODE -ne 0){
  Write-Host "R4.54 remains BLOCKED. Preserve R4.54/R1 diagnostics; do not proceed to R4.55."
  exit $LASTEXITCODE
}

Write-Host "=== R4.54-R1 postrepair reseal verification ==="
& $Python ".\scripts\audit_v0_6D1_R4_54_R1_postrepair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "PASS_R454_R1_ARTIFACT_HASH_PROPERTY_REPAIR_AND_R454_RESEAL_RUN"

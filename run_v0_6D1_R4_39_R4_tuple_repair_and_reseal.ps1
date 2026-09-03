param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r439_r4"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.39-R4 apply Geonomics lyr-series timestep/raster tuple repair ==="
& $Python ".\tools\r4_39_r4_apply_lyr_series_tuple_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.39-R4 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r439_r4_lyr_series_timestep_raster_tuple_repair.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.39 full rerun with tuple-aware dim-metadata repair ==="
& ".\run_v0_6D1_R4_39.ps1"
if($LASTEXITCODE -ne 0){
  Write-Host "R4.39-R4: R4.39 remains BLOCKED. Preserve outputs."
  exit $LASTEXITCODE
}

Write-Host "=== R4.39-R4 postrepair reseal verification ==="
& $Python ".\tools\r4_39_r4_postrepair_reseal_audit.py"
exit $LASTEXITCODE

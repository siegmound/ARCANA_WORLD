param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r439_r3"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}
Write-Host "=== R4.39-R3 apply Geonomics ndarray change dim-metadata compatibility repair ==="
& $Python ".\tools\r4_39_r3_apply_ndarray_dim_metadata_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
Write-Host "=== R4.39-R3 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r439_r3_ndarray_change_dim_metadata_repair.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
Write-Host "=== R4.39 full rerun with ndarray dim-metadata compatibility repair ==="
& ".\run_v0_6D1_R4_39.ps1"
if($LASTEXITCODE -ne 0){Write-Host "R4.39-R3: R4.39 remains BLOCKED. Preserve outputs."; exit $LASTEXITCODE}
Write-Host "=== R4.39-R3 postrepair reseal verification ==="
& $Python ".\tools\r4_39_r3_postrepair_reseal_audit.py"
exit $LASTEXITCODE

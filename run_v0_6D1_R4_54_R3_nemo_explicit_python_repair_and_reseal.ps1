param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r454_r3"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.54-R3 apply explicit NEMO collector Python + bridge diagnostic repair ==="
& $Python ".\scripts\apply_v0_6D1_R4_54_R3_nemo_explicit_python_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 patched source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_54_source_manifest.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 original regression after R3 repair ==="
& $Python -m pytest -q ".\tests\test_r454_non_geonomics_exact_seed_readout_dry_run_authorization.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54-R3 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r454_r3_nemo_explicit_python_repair.py" --basetemp ($Base+"_r3")
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54 rerun five-engine disposable gate after targeted NEMO host-interface repair ==="
& ".\run_v0_6D1_R4_54.ps1" -Python $Python
if($LASTEXITCODE -ne 0){
  Write-Host "R4.54 remains BLOCKED. The NEMO row now contains bridge stdout/stderr diagnostics."
  exit $LASTEXITCODE
}

Write-Host "=== R4.54-R3 postrepair reseal verification ==="
& $Python ".\scripts\audit_v0_6D1_R4_54_R3_postrepair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "PASS_R454_R3_NEMO_EXPLICIT_PYTHON_REPAIR_AND_R454_RESEAL_RUN"

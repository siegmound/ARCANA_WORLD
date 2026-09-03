param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r453"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.53 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_53_source_manifest.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.53 regression ==="
& $Python -m pytest -q ".\tests\test_r453_non_geonomics_scientific_execution_interface_readout_authority_preflight.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.53 freeze five-engine execution interface + scientific readout authority ==="
& $Python ".\scripts\run_v0_6D1_R4_53.py"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.53 BLOCKED. No external engine is executed."
    exit $LASTEXITCODE
}

Write-Host "=== R4.53 final fail-closed authority seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_53_seal.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "PASS_R453_INTEGRATED_AND_FINAL_SEAL_RUN"

param([string]$Python="python")

$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r448"

if(Test-Path $Base){
    Remove-Item -Recurse -Force $Base
}

Write-Host "=== R4.48 source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_48_source_manifest.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.48 regression ==="
& $Python -m pytest -q ".\tests\test_r448_geonomics_j14_j18_full_job_revalidation_coverage_expansion_preflight.py" --basetemp $Base
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "=== R4.48 J14/J18 full-coverage inventory + frozen expansion plan ==="
& $Python ".\scripts\run_v0_6D1_R4_48.py"
if($LASTEXITCODE -ne 0){
    Write-Host "R4.48 BLOCKED. No scientific expansion execution authorized."
    exit $LASTEXITCODE
}

Write-Host "=== R4.48 final fail-closed seal ==="
& $Python ".\scripts\audit_v0_6D1_R4_48_seal.py"
if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }

Write-Host "PASS_R448_INTEGRATED_AND_FINAL_SEAL_RUN"

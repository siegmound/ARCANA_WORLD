param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r436_r3"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.36-R3 apply postrepair meta-audit syntax fix ==="
& $Python ".\tools\r4_36_r3_apply_postrepair_audit_fix.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36-R3 dedicated meta-audit regression ==="
& $Python -m pytest -q ".\tests\test_r436_r3_postrepair_meta_audit_fix.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36-R2 corrected postrepair verification on already SEALED outputs ==="
& $Python ".\tools\r4_36_r2_postrepair_reseal_audit.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.36-R3 repair-chain closure audit ==="
& $Python ".\tools\r4_36_r3_repair_chain_closure_audit.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "PASS_R436_R3_REPAIR_CHAIN_CLOSED_NO_R436_RERUN_REQUIRED"

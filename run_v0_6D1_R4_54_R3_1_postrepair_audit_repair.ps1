param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=(Join-Path $Root "src")
$Base=Join-Path $Root ".pytest_tmp_r454_r3_1"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.54-R3.1 apply postrepair audit literal-brace repair ==="
& $Python ".\scripts\apply_v0_6D1_R4_54_R3_1_postrepair_audit_brace_repair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54-R3.1 dedicated regression ==="
& $Python -m pytest -q ".\tests\test_r454_r3_1_postrepair_audit_brace_repair.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.54-R3.1 verify existing SEALED R4.54 only; no engine rerun ==="
& $Python ".\scripts\audit_v0_6D1_R4_54_R3_postrepair.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "PASS_R454_R3_1_POSTREPAIR_AUDIT_REPAIR_AND_EXISTING_R454_RESEAL_VERIFICATION"

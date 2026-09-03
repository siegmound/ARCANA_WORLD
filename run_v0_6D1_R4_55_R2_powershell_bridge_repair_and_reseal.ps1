param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$env:PYTHONPATH=Join-Path $Root "src"
$Base=Join-Path $Root ".pytest_tmp_r455_r2"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}
Write-Host "=== R4.55-R2 preserve parser-blocked evidence + apply PowerShell bridge repair ==="
& $Python ".\scripts\apply_v0_6D1_R4_55_R2_powershell_bridge_repair.py";if($LASTEXITCODE-ne0){exit $LASTEXITCODE}
Write-Host "=== R4.55 patched source authority ==="
& $Python ".\scripts\check_v0_6D1_R4_55_source_manifest.py";if($LASTEXITCODE-ne0){exit $LASTEXITCODE}
Write-Host "=== R4.55 original regression after R2 repair ==="
& $Python -m pytest -q ".\tests\test_r455_non_geonomics_80_stream_execution_evidence_capture.py" --basetemp $Base;if($LASTEXITCODE-ne0){exit $LASTEXITCODE}
Write-Host "=== R4.55-R1 regression remains valid ==="
& $Python -m pytest -q ".\tests\test_r455_r1_seed_ledger_order_config_index_repair.py" --basetemp ($Base+"_r1");if($LASTEXITCODE-ne0){exit $LASTEXITCODE}
Write-Host "=== R4.55-R2 dedicated bridge regression ==="
& $Python -m pytest -q ".\tests\test_r455_r2_powershell_bridge_parser_repair.py" --basetemp ($Base+"_r2");if($LASTEXITCODE-ne0){exit $LASTEXITCODE}
Write-Host "=== R4.55 resume/run after parser repair ==="
& ".\run_v0_6D1_R4_55.ps1" -Python $Python
if($LASTEXITCODE-ne0){Write-Host "R4.55 remains BLOCKED. Completed jobs remain resume-valid.";exit $LASTEXITCODE}
Write-Host "=== R4.55-R2 postrepair reseal verification ==="
& $Python ".\scripts\audit_v0_6D1_R4_55_R2_postrepair.py";if($LASTEXITCODE-ne0){exit $LASTEXITCODE}
Write-Host "PASS_R455_R2_POWERSHELL_BRIDGE_REPAIR_AND_R455_RESEAL_RUN"

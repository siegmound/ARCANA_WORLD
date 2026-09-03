param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$Base=Join-Path $Root ".pytest_tmp_r437_r1"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.37-R1 diagnostic regression ==="
& $Python -m pytest -q ".\tests\test_r437_r1_live_failure_detail_diagnostic.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.37-R1 live failure-detail capture (NO Geonomics rerun) ==="
& $Python ".\tools\r4_37_r1_live_failure_detail_diagnostic.py"
exit $LASTEXITCODE

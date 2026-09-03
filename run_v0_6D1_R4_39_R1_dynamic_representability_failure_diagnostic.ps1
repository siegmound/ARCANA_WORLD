param([string]$Python="python")
$ErrorActionPreference="Stop"
$Root=(Get-Location).Path
$Base=Join-Path $Root ".pytest_tmp_r439_r1"
if(Test-Path $Base){Remove-Item -Recurse -Force $Base}

Write-Host "=== R4.39-R1 diagnostic regression ==="
& $Python -m pytest -q ".\tests\test_r439_r1_dynamic_representability_failure_diagnostic.py" --basetemp $Base
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}

Write-Host "=== R4.39-R1 live dynamic representability failure capture (NO Geonomics rerun) ==="
& $Python ".\tools\r4_39_r1_dynamic_representability_failure_diagnostic.py"
exit $LASTEXITCODE

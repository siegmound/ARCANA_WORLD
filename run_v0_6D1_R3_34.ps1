$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r334"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.34 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_34_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.34 source authority failed closed." }
Write-Host "=== R3.34 regression ==="
python -m pytest "$Root\tests\test_r334_producer_domestication.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.34 regression failed closed." }
Write-Host "=== R3.34 producer authority + plant coevolution + domestication ==="
python "$Root\scripts\run_v0_6D1_R3_34.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.34 integrated stage failed closed." }
Write-Host "=== R3.34 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_34_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.34 final seal failed closed." }
Write-Host "PASS_R334_INTEGRATED_AND_FINAL_SEAL_RUN"

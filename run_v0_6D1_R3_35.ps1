$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r335"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.35 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_35_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.35 source authority failed closed." }
Write-Host "=== R3.35 regression ==="
python -m pytest "$Root\tests\test_r335_producer_genetics.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.35 regression failed closed." }
Write-Host "=== R3.35 producer heritable variation + selection response + domestication genetics ==="
python "$Root\scripts\run_v0_6D1_R3_35.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.35 integrated stage failed closed." }
Write-Host "=== R3.35 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_35_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.35 final seal failed closed." }
Write-Host "PASS_R335_INTEGRATED_AND_FINAL_SEAL_RUN"

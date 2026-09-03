$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src"
$Tmp = Join-Path $Root ".pytest_tmp\r333"
if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
Write-Host "=== R3.33 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_33_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.33 source authority failed closed." }
Write-Host "=== R3.33 regression ==="
python -m pytest "$Root\tests\test_r333_holocene_environment_domestication.py" -q --basetemp "$Tmp" -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "R3.33 regression failed closed." }
Write-Host "=== R3.33 Holocene environment + ecological partners + domestication ==="
python "$Root\scripts\run_v0_6D1_R3_33.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.33 integrated stage failed closed." }
Write-Host "=== R3.33 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_33_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.33 final seal failed closed." }
Write-Host "PASS_R333_INTEGRATED_AND_FINAL_SEAL_RUN"

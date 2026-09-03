$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PytestBase = Join-Path $Root ".pytest_tmp\r328"
if (Test-Path $PytestBase) { Remove-Item -Recurse -Force $PytestBase }
New-Item -ItemType Directory -Force -Path $PytestBase | Out-Null
$env:PYTHONPATH = (Join-Path $Root "src")
Write-Host "=== R3.28 source authority ==="
python (Join-Path $Root "scripts\check_v0_6D1_R3_28_source_manifest.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "R3.28 source authority failed closed." }
Write-Host "=== R3.28 regression ==="
python -m pytest (Join-Path $Root "tests\test_r328_highres_200ka_to_0.py") -q -p no:cacheprovider --basetemp $PytestBase
if ($LASTEXITCODE -ne 0) { throw "R3.28 regression failed closed." }
Write-Host "=== R3.28 high-resolution 200 ka to 0 replay ==="
python (Join-Path $Root "scripts\run_v0_6D1_R3_28.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "R3.28 integrated replay failed closed." }
Write-Host "=== R3.28 final single-stage seal ==="
python (Join-Path $Root "scripts\audit_v0_6D1_R3_28_seal.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "R3.28 final seal failed closed." }
Write-Host "PASS_R328_INTEGRATED_AND_FINAL_SEAL_RUN"

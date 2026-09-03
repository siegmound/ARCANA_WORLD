$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PytestBase = Join-Path $Root ".pytest_tmp\r327"
if (Test-Path $PytestBase) { Remove-Item -Recurse -Force $PytestBase }
New-Item -ItemType Directory -Force -Path $PytestBase | Out-Null
$env:PYTHONPATH = (Join-Path $Root "src")
Write-Host "=== R3.27 source authority ==="
python (Join-Path $Root "scripts\check_v0_6D1_R3_27_source_manifest.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "R3.27 source authority failed closed." }
Write-Host "=== R3.27 regression ==="
python -m pytest (Join-Path $Root "tests\test_r327_hominin_macro_replay.py") -q -p no:cacheprovider --basetemp $PytestBase
if ($LASTEXITCODE -ne 0) { throw "R3.27 regression failed closed." }
Write-Host "=== R3.27 hominin macro-evolution replay to 200 ka ==="
python (Join-Path $Root "scripts\run_v0_6D1_R3_27.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "R3.27 integrated replay failed closed." }
Write-Host "=== R3.27 final single-stage seal ==="
python (Join-Path $Root "scripts\audit_v0_6D1_R3_27_seal.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "R3.27 final seal failed closed." }
Write-Host "PASS_R327_INTEGRATED_AND_FINAL_SEAL_RUN"

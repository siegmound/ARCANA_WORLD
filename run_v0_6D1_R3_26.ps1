$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$Root\src;$env:PYTHONPATH"
Write-Host "=== R3.26 source authority ==="
python "$Root\scripts\check_v0_6D1_R3_26_source_manifest.py"
if ($LASTEXITCODE -ne 0) { throw "R3.26 source manifest failed closed." }
Write-Host "=== R3.26 regression ==="
$PytestBaseTemp = Join-Path $Root ".pytest_tmp\r326"
if (Test-Path $PytestBaseTemp) { Remove-Item -Recurse -Force $PytestBaseTemp }
New-Item -ItemType Directory -Force -Path $PytestBaseTemp | Out-Null
python -m pytest -q -p no:cacheprovider --basetemp "$PytestBaseTemp" "$Root\tests\test_r326_h3_quant_genetics_bridge.py"
if ($LASTEXITCODE -ne 0) { throw "R3.26 regression failed closed." }
Write-Host "=== R3.26 H3 quantitative-genetics bridge ==="
python "$Root\scripts\run_v0_6D1_R3_26.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.26 H3 bridge failed closed." }
Write-Host "=== R3.26 final single-stage seal ==="
python "$Root\scripts\audit_v0_6D1_R3_26_seal.py" --root "$Root"
if ($LASTEXITCODE -ne 0) { throw "R3.26 final seal failed closed." }
Write-Host "PASS_R326_INTEGRATED_AND_FINAL_SEAL_RUN"

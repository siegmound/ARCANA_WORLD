$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
python -m pytest -q (Join-Path $Root "tests\test_r37d_directional_selection_closure.py")
if ($LASTEXITCODE -ne 0) { throw "R3.7D tests failed" }
python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_7D.py")
if ($LASTEXITCODE -ne 0) { throw "R3.7D formal audit failed" }

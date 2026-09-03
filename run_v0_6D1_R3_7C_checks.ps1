$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
python -m pytest -q (Join-Path $Root "tests\test_r37c_directional_selection_oracle.py")
if ($LASTEXITCODE -ne 0) { throw "R3.7C tests failed" }
python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_7C.py")
if ($LASTEXITCODE -ne 0) { throw "R3.7C formal audit failed" }

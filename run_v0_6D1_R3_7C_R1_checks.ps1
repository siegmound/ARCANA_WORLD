$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
python -m pytest -q (Join-Path $Root "tests\test_r37c_directional_selection_oracle.py") (Join-Path $Root "tests\test_r37c_r1_composite_selection_repair.py")
if ($LASTEXITCODE -ne 0) { throw "R3.7C/R1 tests failed" }
python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_7C.py")
if ($LASTEXITCODE -ne 0) { throw "Parent R3.7C formal audit failed" }
python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_7C_R1.py")
if ($LASTEXITCODE -ne 0) { throw "R3.7C-R1 formal audit failed" }

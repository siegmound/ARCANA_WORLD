param([string]$Python = "python")
$ErrorActionPreference = "Stop"
& $Python -m pytest -q tests/test_r37f_stress_window_shadow.py
if ($LASTEXITCODE -ne 0) { throw "R3.7F unit tests failed" }
& $Python scripts/formal_audit_v0_6D1_R3_7F.py
if ($LASTEXITCODE -ne 0) { throw "R3.7F formal audit failed" }

param([string]$Python = "python")
$ErrorActionPreference = "Stop"
& $Python -m pytest -q tests/test_r37g_production_validation.py
if ($LASTEXITCODE -ne 0) { throw "R3.7G unit tests failed" }
& $Python scripts/formal_audit_v0_6D1_R3_7G.py
if ($LASTEXITCODE -ne 0) { throw "R3.7G formal audit failed" }

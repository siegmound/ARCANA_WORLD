param([string]$Python = "python")
$ErrorActionPreference = "Stop"
& $Python -m pytest -q tests/test_r37h_closed_loop_binding.py
if ($LASTEXITCODE -ne 0) { throw "R3.7H unit tests failed" }
& $Python scripts/formal_audit_v0_6D1_R3_7H.py
if ($LASTEXITCODE -ne 0) { throw "R3.7H formal audit failed" }

param([string]$Python = "python")
$ErrorActionPreference = "Stop"
& $Python -m pytest -q tests/test_r37e_short_world1_shadow.py
if ($LASTEXITCODE -ne 0) { throw "R3.7E targeted tests failed" }
& $Python scripts/formal_audit_v0_6D1_R3_7E.py
if ($LASTEXITCODE -ne 0) { throw "R3.7E formal audit failed" }

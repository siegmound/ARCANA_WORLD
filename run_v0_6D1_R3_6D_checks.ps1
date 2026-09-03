$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PWD\src"
Write-Host "=== pytest full candidate ==="
python -m pytest -q
Write-Host "=== parent R3.5 formal audit ==="
python scripts/audit_v0_6D1_R3_5.py
Write-Host "=== parent R3.6A formal audit ==="
python scripts/audit_v0_6D1_R3_6A.py
Write-Host "=== parent R3.6B formal audit ==="
python scripts/audit_v0_6D1_R3_6B.py
Write-Host "=== parent R3.6C formal audit ==="
python scripts/audit_v0_6D1_R3_6C.py
Write-Host "=== R3.6D formal audit ==="
python scripts/audit_v0_6D1_R3_6D.py

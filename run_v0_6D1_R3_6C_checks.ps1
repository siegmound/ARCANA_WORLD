$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PWD\src"
python -m pytest -q
python scripts\audit_v0_6D1_R3_5.py
python scripts\audit_v0_6D1_R3_6A.py
python scripts\audit_v0_6D1_R3_6B.py
python scripts\audit_v0_6D1_R3_6C.py

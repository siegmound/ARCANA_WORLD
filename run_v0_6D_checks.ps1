$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
python -m pytest -q (Join-Path $Root "tests\test_historical_deep_bridge_v0_6D.py")
python (Join-Path $Root "scripts\real_d22_to_d3_transfer_smoke_v0_6D.py")
python (Join-Path $Root "scripts\cha1_pulse_reference_audit_v0_6D.py")
python (Join-Path $Root "scripts\audit_v0_6D.py")

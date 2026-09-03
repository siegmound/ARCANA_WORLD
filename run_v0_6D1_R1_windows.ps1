$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
python (Join-Path $Root "scripts\materialize_rebaseline_210ma_v0_6D1_R1.py") --root $Root
python (Join-Path $Root "scripts\rebaseline_radius_sensitivity_v0_6D1_R1.py")
python -m pytest -q (Join-Path $Root "tests")
python (Join-Path $Root "scripts\audit_v0_6D1_R1.py")
Write-Host "v0.6D1-R1 checks complete."

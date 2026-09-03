$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
python (Join-Path $root "scripts\run_v0_6D1_R3_16_c2_bridge_fixed_biology.py") @args
exit $LASTEXITCODE

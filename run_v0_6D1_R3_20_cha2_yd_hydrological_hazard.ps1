$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
python (Join-Path $root "scripts/run_v0_6D1_R3_20_cha2_yd_hydrological_hazard.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

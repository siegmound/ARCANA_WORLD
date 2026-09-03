$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
python (Join-Path $root "scripts\run_v0_6D1_R3_18_recent_exposure_transport_readiness.py") @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

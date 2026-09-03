$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
python (Join-Path $root "scripts\run_v0_6D1_R3_17_recent_restart_sync.py") @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

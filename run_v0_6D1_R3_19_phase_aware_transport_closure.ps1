$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
python (Join-Path $root "scripts\run_v0_6D1_R3_19_phase_aware_transport_closure.py")
exit $LASTEXITCODE

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = (Join-Path $Root "src")
python (Join-Path $Root "scripts\run_v0_6D1_R3_9_precha1_continuation.py")
exit $LASTEXITCODE

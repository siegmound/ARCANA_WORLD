$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LocalEnv = Join-Path $Root "set_r40_engine_env.local.ps1"
if (Test-Path $LocalEnv) { . $LocalEnv }
$env:PYTHONPATH = "$Root\src"
python "$Root\scripts\run_v0_6D1_R4_0.py" --root "$Root"
exit $LASTEXITCODE

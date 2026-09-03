$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "python"
if (Test-Path (Join-Path $Root ".venv\Scripts\python.exe")) {
    $Python = Join-Path $Root ".venv\Scripts\python.exe"
}
& $Python (Join-Path $Root "scripts\run_v0_6D1_R3_10_cha1_highres_bridge.py") @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

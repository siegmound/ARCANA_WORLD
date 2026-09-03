$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Root
try {
    $env:PYTHONPATH = "$Root\src"
    python -m pytest -q tests/test_r312_postcha1_diversity_recovery.py tests/test_r311_postcha1_recovery.py tests/test_r310_cha1_highres_bridge.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

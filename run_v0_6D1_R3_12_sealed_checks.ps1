$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseTemp = Join-Path $Root (".pytest_tmp\r312_sealed_checks_" + $PID)

Push-Location $Root
try {
    $env:PYTHONPATH = "$Root\src"

    # Keep pytest temporary files inside the project tree.  This avoids
    # Windows/Hermes permission problems in %LOCALAPPDATA%\Temp\pytest-of-<user>.
    if (Test-Path $BaseTemp) {
        Remove-Item -Recurse -Force $BaseTemp
    }
    New-Item -ItemType Directory -Force -Path $BaseTemp | Out-Null

    python -m pytest -q `
        --basetemp "$BaseTemp" `
        tests/test_r312_postcha1_diversity_recovery.py `
        tests/test_r311_postcha1_recovery.py `
        tests/test_r310_cha1_highres_bridge.py `
        tests/test_r39_precha1_continuation.py `
        tests/test_r38_restartable_checkpoint.py `
        tests/test_r37i_production_promotion.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    python scripts/formal_audit_v0_6D1_R3_12_sealed.py `
        --root $Root `
        --run-dir "$Root\local_runs\v0_6D1_R3_12" `
        --out "$Root\outputs\v0_6D1_R3_12\FORMAL_AUDIT_SEALED_v0_6D1_R3_12_RECHECK.json"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "PASS_R312_SEALED_CHECKS_WITH_LOCAL_BASETEMP"
} finally {
    Pop-Location
    if (Test-Path $BaseTemp) {
        Remove-Item -Recurse -Force $BaseTemp -ErrorAction SilentlyContinue
    }
}

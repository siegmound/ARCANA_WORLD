$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Root
try {
    $env:PYTHONPATH = "$Root\src"
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
    function Run-PytestBlock([string]$Tag, [string[]]$Files) {
        $BaseTemp = Join-Path $Root (".pytest_tmp\r313_" + $Tag + "_" + $PID)
        if (Test-Path $BaseTemp) { Remove-Item -Recurse -Force $BaseTemp }
        python -m pytest -q --basetemp "$BaseTemp" @Files
        $Code = $LASTEXITCODE
        if (Test-Path $BaseTemp) { Remove-Item -Recurse -Force $BaseTemp -ErrorAction SilentlyContinue }
        if ($Code -ne 0) { exit $Code }
    }
    Run-PytestBlock "r313_to_r310" @(
      "tests/test_r313_longterm_postcha1_reassembly.py",
      "tests/test_r312_postcha1_diversity_recovery.py",
      "tests/test_r311_postcha1_recovery.py",
      "tests/test_r310_cha1_highres_bridge.py"
    )
    Run-PytestBlock "r39" @("tests/test_r39_precha1_continuation.py")
    Run-PytestBlock "r38" @("tests/test_r38_restartable_checkpoint.py")
    Run-PytestBlock "r37i" @("tests/test_r37i_production_promotion.py")
    python scripts/formal_audit_v0_6D1_R3_13_sealed.py --root $Root --run-dir "$Root\local_runs\v0_6D1_R3_13" --out "$Root\outputs\v0_6D1_R3_13\FORMAL_AUDIT_SEALED_v0_6D1_R3_13_RECHECK.json"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "PASS_R313_SEALED_CHECKS_WITH_LOCAL_BASETEMP"
} finally { Pop-Location }

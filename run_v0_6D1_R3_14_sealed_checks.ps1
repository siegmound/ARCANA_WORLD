$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Root
try {
    $env:PYTHONPATH = "$Root\src"
    $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
    $Tmp = Join-Path $Root (".pytest_tmp\r314_sealed_" + $PID)
    if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
    python -m pytest -q --basetemp "$Tmp" `
      "tests/test_r314_late_cenozoic_binding.py" `
      "tests/test_r314_c1_numeric_portability.py" `
      "tests/test_r313_longterm_postcha1_reassembly.py" `
      "tests/test_r312_postcha1_diversity_recovery.py"
    $Code = $LASTEXITCODE
    if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue }
    if ($Code -ne 0) { exit $Code }

    python "scripts/formal_audit_v0_6D1_R3_14_sealed.py" `
      --root "$Root" `
      --out "$Root\outputs\v0_6D1_R3_14\FORMAL_AUDIT_SEALED_v0_6D1_R3_14.json" `
      --seal-out "$Root\R3_14_SEAL_SUMMARY.json"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "PASS_R314_SEALED_BINDING_CHECKS_WITH_LOCAL_BASETEMP"
} finally {
    Pop-Location
}

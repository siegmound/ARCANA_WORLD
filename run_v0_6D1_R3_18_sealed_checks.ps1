param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$Base = Join-Path $Root (".pytest_tmp_r318_sealed_checks_" + $PID)
New-Item -ItemType Directory -Force -Path $Base | Out-Null

& $Python -m pytest -q (Join-Path $Root "tests\test_r318_recent_exposure_transport_readiness.py") --basetemp (Join-Path $Base "g1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m pytest -q (Join-Path $Root "tests\test_r317_recent_restart_sync.py") --basetemp (Join-Path $Base "g2")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m pytest -q (Join-Path $Root "tests\test_r316_c2_bridge_fixed_biology.py") --basetemp (Join-Path $Base "g3")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m pytest -q (Join-Path $Root "tests\test_r315_late_cenozoic_secular_biology.py") --basetemp (Join-Path $Base "g4")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m pytest -q (Join-Path $Root "tests\test_r314_late_cenozoic_binding.py") (Join-Path $Root "tests\test_r314_c1_numeric_portability.py") --basetemp (Join-Path $Base "g5")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$RunDir = Join-Path $Root "local_runs\v0_6D1_R3_18"
$AuditOut = Join-Path $Root "outputs\v0_6D1_R3_18\FORMAL_AUDIT_SEALED_v0_6D1_R3_18.json"
$SealOut = Join-Path $Root "R3_18_SEAL_SUMMARY.json"
& $Python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_18_sealed.py") --root $Root --run-dir $RunDir --out $AuditOut --seal-out $SealOut
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "PASS_R318_SEALED_CHECKS_WITH_LOCAL_BASETEMP"

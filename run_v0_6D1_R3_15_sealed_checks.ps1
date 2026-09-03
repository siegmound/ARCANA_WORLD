param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$Base = Join-Path $Root (".pytest_tmp\r315_sealed_checks_" + $PID)
New-Item -ItemType Directory -Force -Path $Base | Out-Null

# Focused production surface, split to keep Windows pytest teardown deterministic.
& $Python -m pytest -q `
  (Join-Path $Root "tests\test_r315_late_cenozoic_secular_biology.py") `
  (Join-Path $Root "tests\test_r314_late_cenozoic_binding.py") `
  --basetemp (Join-Path $Base "g1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Python -m pytest -q `
  (Join-Path $Root "tests\test_r314_c1_numeric_portability.py") `
  (Join-Path $Root "tests\test_r313_longterm_postcha1_reassembly.py") `
  --basetemp (Join-Path $Base "g2")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$RunDir = Join-Path $Root "local_runs\v0_6D1_R3_15"
$AuditOut = Join-Path $Root "outputs\v0_6D1_R3_15\FORMAL_AUDIT_SEALED_v0_6D1_R3_15.json"
$SealOut = Join-Path $Root "R3_15_SEAL_SUMMARY.json"
& $Python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_15_sealed.py") --root $Root --run-dir $RunDir --out $AuditOut --seal-out $SealOut
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "PASS_R315_SEALED_CHECKS_WITH_LOCAL_BASETEMP"

param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $Root "src"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$Base = Join-Path $Root (".pytest_tmp\r315_checks_" + $PID)
New-Item -ItemType Directory -Force -Path $Base | Out-Null
& $Python -m pytest -q `
  (Join-Path $Root "tests\test_r315_late_cenozoic_secular_biology.py") `
  (Join-Path $Root "tests\test_r314_late_cenozoic_binding.py") `
  (Join-Path $Root "tests\test_r314_c1_numeric_portability.py") `
  (Join-Path $Root "tests\test_r313_longterm_postcha1_reassembly.py") `
  --basetemp $Base
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$AuditOut = Join-Path $Root "outputs\v0_6D1_R3_15\FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_15.json"
& $Python (Join-Path $Root "scripts\formal_audit_v0_6D1_R3_15_candidate.py") --root $Root --out $AuditOut
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

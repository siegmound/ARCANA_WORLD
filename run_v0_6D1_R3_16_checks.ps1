$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$bt = Join-Path $root ".pytest_tmp_r316_checks"
New-Item -ItemType Directory -Force -Path $bt | Out-Null
python -m pytest -q `
  (Join-Path $root "tests\test_r316_c2_bridge_fixed_biology.py") `
  --basetemp (Join-Path $bt "r316")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q `
  (Join-Path $root "tests\test_r315_late_cenozoic_secular_biology.py") `
  --basetemp (Join-Path $bt "r315")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q `
  (Join-Path $root "tests\test_r314_late_cenozoic_binding.py") `
  (Join-Path $root "tests\test_r314_c1_numeric_portability.py") `
  --basetemp (Join-Path $bt "r314")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python (Join-Path $root "scripts\formal_audit_v0_6D1_R3_16_candidate.py")
exit $LASTEXITCODE

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
$bt = Join-Path $root ".pytest_tmp_r320_checks"
New-Item -ItemType Directory -Force -Path $bt | Out-Null
python -m pytest (Join-Path $root "tests/test_r320_cha2_yd_hydrological_hazard.py") -q --basetemp (Join-Path $bt "r320")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest (Join-Path $root "tests/test_r314_c1_numeric_portability.py") -q --basetemp (Join-Path $bt "r314c1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python (Join-Path $root "scripts/formal_audit_v0_6D1_R3_20_candidate.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

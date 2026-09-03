$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
$bt = Join-Path $root ".pytest_tmp_r318_checks"
New-Item -ItemType Directory -Force -Path $bt | Out-Null

python -m pytest -q (Join-Path $root "tests\test_r318_recent_exposure_transport_readiness.py") --basetemp (Join-Path $bt "r318")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q (Join-Path $root "tests\test_r317_recent_restart_sync.py") --basetemp (Join-Path $bt "r317")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q (Join-Path $root "tests\test_r316_c2_bridge_fixed_biology.py") --basetemp (Join-Path $bt "r316")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q (Join-Path $root "tests\test_r315_late_cenozoic_secular_biology.py") --basetemp (Join-Path $bt "r315")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest -q (Join-Path $root "tests\test_r314_late_cenozoic_binding.py") (Join-Path $root "tests\test_r314_c1_numeric_portability.py") --basetemp (Join-Path $bt "r314")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$out = Join-Path $root "outputs\v0_6D1_R3_18\FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_18.json"
python (Join-Path $root "scripts\formal_audit_v0_6D1_R3_18_candidate.py") --root $root --out $out
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

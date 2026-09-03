$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $root "src"
$bt = Join-Path $root ".pytest_tmp_r320_sealed"
New-Item -ItemType Directory -Force -Path $bt | Out-Null
python -m pytest (Join-Path $root "tests/test_r320_cha2_yd_hydrological_hazard.py") -q --basetemp (Join-Path $bt "r320")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pytest (Join-Path $root "tests/test_r314_c1_numeric_portability.py") -q --basetemp (Join-Path $bt "r314c1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python (Join-Path $root "scripts/formal_audit_v0_6D1_R3_20_candidate.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$cand = Get-Content (Join-Path $root "outputs\v0_6D1_R3_20\FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_20.json") -Raw | ConvertFrom-Json
if ([string]$cand.checks -ne "57/57") { throw "R3.20 candidate audit must be 57/57 before seal; got '$($cand.checks)'" }
python (Join-Path $root "scripts/formal_audit_v0_6D1_R3_20_sealed.py") `
  --root $root `
  --run-dir (Join-Path $root "local_runs\v0_6D1_R3_20") `
  --out (Join-Path $root "outputs\v0_6D1_R3_20\FORMAL_AUDIT_SEALED_v0_6D1_R3_20.json") `
  --seal-out (Join-Path $root "R3_20_SEAL_SUMMARY.json")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "PASS_R320_SEALED_CHECKS_WITH_LOCAL_BASETEMP"

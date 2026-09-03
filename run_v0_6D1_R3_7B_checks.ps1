$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Root
try {
  $env:PYTHONPATH = Join-Path $Root "src"
  python scripts/analyze_r37a_b2_neutral_closure_v0_6D1_R3_7B.py `
    reference_results/v0_6D1_R3_7A_B2/v0_6D1_R3_7A_B2_RESULTS.zip `
    outputs/v0_6D1_R3_7B/NEMO_B2_NEUTRAL_LIFECYCLE_CLOSURE_v0_6D1_R3_7B.json
  if ($LASTEXITCODE -ne 0) { throw "R3.7B B2 analysis failed" }

  python -m pytest -q `
    tests/test_segregation_aware_admixture_v0_6D1_R3_7.py `
    tests/test_segregation_potential_lifecycle_v0_6D1_R3_7A.py `
    tests/test_nemo_r37a_b2_binding.py `
    tests/test_r37b_neutral_lifecycle_and_b2_closure.py
  if ($LASTEXITCODE -ne 0) { throw "R3.7B tests failed" }

  python scripts/formal_audit_v0_6D1_R3_7B.py
  if ($LASTEXITCODE -ne 0) { throw "R3.7B formal audit failed" }
} finally {
  Pop-Location
}

$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PWD\src"
Write-Host "=== R3.7 targeted tests ==="
python -m pytest -q tests\test_segregation_aware_admixture_v0_6D1_R3_7.py tests\test_r37_reference_validation.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R3.7 reference closure ==="
python scripts\analyze_segregation_aware_reference_v0_6D1_R3_7.py reference_results\v0_6D1_R3_6D_RAW_RESULTS.zip reference_results\R3_6E_CAUSAL_INFERENCE.json --out reference_results\R3_7_SEGREGATION_AWARE_REFERENCE_CLOSURE.json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R3.7 formal audit ==="
python scripts\formal_audit_v0_6D1_R3_7.py
exit $LASTEXITCODE

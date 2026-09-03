$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "$PWD\src"
Write-Host "=== R3.7 parent + R3.7A tests ==="
python -m pytest -q tests\test_segregation_aware_admixture_v0_6D1_R3_7.py tests\test_r37_reference_validation.py tests\test_segregation_potential_lifecycle_v0_6D1_R3_7A.py tests\test_nemo_r37a_b2_binding.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== Rebuild parent NEMO lifecycle reference ==="
python scripts\analyze_r37a_parent_reference.py reference_results\v0_6D1_R3_6D_RAW_RESULTS.zip --out reference_results\R3_7A_PARENT_NEMO_DRIFT_AND_KEFF_REFERENCE.json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "=== R3.7A formal audit ==="
python scripts\formal_audit_v0_6D1_R3_7A.py
exit $LASTEXITCODE

# v0.6D1-R3.7

Segregation-aware reduced-order admixture repair candidate.

Run:

```powershell
$env:PYTHONPATH = "$PWD\src"
pytest -q tests\test_segregation_aware_admixture_v0_6D1_R3_7.py
python scripts\analyze_segregation_aware_reference_v0_6D1_R3_7.py `
  reference_results\v0_6D1_R3_6D_RAW_RESULTS.zip `
  reference_results\R3_6E_CAUSAL_INFERENCE.json
python scripts\formal_audit_v0_6D1_R3_7.py
```

R3.7 validates a candidate operator only. Production runtime binding remains blocked until R3.7A defines the lifecycle of the new segregation-potential state.

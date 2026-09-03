# R3.6E — NEMO Evidence Closure & Quantitative-Genetics Causal Inference Gate

This candidate adds a fail-closed analysis layer over the completed R3.6D NEMO evidence.

Run:

```powershell
$env:PYTHONPATH = "$PWD\src"
python scripts\analyze_nemo_causal_inference_v0_6D1_R3_6E.py reference_results\v0_6D1_R3_6D_RAW_RESULTS.zip --out reference_results\R3_6E_CAUSAL_INFERENCE.json
python scripts\formal_audit_v0_6D1_R3_6E.py
pytest -q tests\test_nemo_causal_inference_v0_6D1_R3_6E.py
```

R3.6E is diagnostic/governance only. It performs no canonical write and changes no D3 biological constants.

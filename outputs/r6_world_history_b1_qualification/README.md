# R6 B1 WORLD_HISTORY bootstrap qualification

This compact package records B1 qualification of synthetic B0 WORLD_HISTORY at source commit `76458611d1a6608a6dac63036d0a698801043f62`. It contains the final H1–H18 matrix, isolated test-run counts/durations, environment evidence, qualification decision, and a reproducibility check.

Run from repository root with a fresh temp root:

```powershell
$ArcanaTemp = Join-Path $env:TEMP ('ARCANA_B1_' + [guid]::NewGuid().ToString('N'))
$env:TEMP = $ArcanaTemp; $env:TMP = $ArcanaTemp
python outputs/r6_world_history_b1_qualification/B1_SEMANTIC_REPRODUCIBILITY_CHECK.py
```

The active R6 pytest suite and seven focused runs are recorded in `B1_TEST_RESULTS.json`. `B1_ARTIFACT_MANIFEST.json` hashes retained package files and the closure report; it intentionally does not hash itself. Environment details are evidence only and are excluded from semantic identities.

Only `AUTHORIZE_B2_SYNTHETIC_SCALE_QUALIFICATION` is approved by this qualification.

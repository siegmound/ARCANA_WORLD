# ARCANA R6 — FAIR receipt: corrected PANGAEA 921284, 66 fitted friction rows

Date: 2026-11-21. Exact FAIR-tested code SHA: `07b311c452ff0bc0bc85bdfee75f00b40da43075`.
Decision: `PANGAEA921284_CORRECTED_DATASET_FAIR_PASS__PER_EXPERIMENT_EFFECTIVE_NORMAL_UNBOUND`.

## 1. FAIR terminal evidence supplied by operator

```text
HEAD 07b311c4
tests/test_r6_g2_g3_rsf_pangaea.py: 13 passed in 0.07s
RSF_TEST_EXIT_CODE=0
pangaea_921284.tab: OK (sha256sum --check)
status=SOURCE_INGESTED__EARTH_ANALOGUE_ONLY_NOT_T0
model_fit_rows=66
source_sha256=b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d
RSF_REINGEST_EXIT_CODE=0
PASS: 66 righe, nessuna tensione inventata
```

This is **operator-reported FAIR execution**, not an independently rerun or raw-file-byte audit in this authoring environment.

Source:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_PANGAEA921284_RAW_NEW_01/pangaea_921284.tab`.

Corrected new report:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_PANGAEA921284_RAW_NEW_01/INGEST_NEW_02/REPORT.json`.

## 2. Actual fitted parameter inventory returned by FAIR

| Metric | Count |
|---|---:|
| Source-fitted parameter rows | 66 |
| Distinct source event labels | 10 |
| Distinct sample labels | 10 |
| Distinct (event, sample, experiment) keys | 23 |
| Single-state fitted rows | 57 |
| Two-state fitted rows | 9 |
| Fitted a-b < 0 | 20 |
| Fitted a-b = 0 | 3 |
| Fitted a-b > 0 | 43 |

All 66 source rows have pressure-scaled `immediate_delta_tau_pa=null`
and `steady_delta_tau_pa=null` in the verified corrected report. Other unqualified fields (per-experiment effective normal pressure and absolute shear traction) remain null.

**Interpretation:** the fitted sign of `a-b` represents steady rate weakening (<0) or strengthening (>0) **for each model-fit row under its stated laboratory conditions**. The 66 fitted rows are not 66 statistically independent instrument observations. 23 distinct identifier tuples are not automatically 23 independent experiments with independent geological sampling either. The fitted sign distribution is NOT an estimate of seismic event probability, ARCANA faults, or world-historical tectonic behavior.

Source: Ikari & Kopf, PANGAEA 921284, https://doi.org/10.1594/PANGAEA.921284 ; original 2017 article DOI 10.1126/sciadv.1701269 (10 MPa nominal, 7 MPa previous Tohoku tests). Provenance is linked to source raw file SHA above.

## 3. Software gate

At `07b311c452ff0bc0bc85bdfee75f00b40da43075`:
- **Corrected targeted RSF FAIR = 13/13 PASS**, 0.07 s, exit code 0;
- **corrected real PANGAEA 66 model-fit import PASS**, SHA verified, immutable new report;
- **full prior 134-test G2/G3 regression + 13 new RSF tests at same SHA PENDING**;
- source code of the new RSF module remains confined to the isolated development branch, **not the main R6 branch**.

The full regression should exercise 147 tests if no hidden parametrizations or collection changes occur; do not report this as an observed number until run.

## 4. World-simulation authority

```text
EARTH_LAB_FRICTIONAL_PARAMETRIZATION=SOURCE_VALIDATED
PANGAEA921284_FITTED_MODEL_ROWS=66
LAB_RATE_STATE_DELTA_MU=CONDITIONAL_SOURCE_BOUNDED
LAB_EFFECTIVE_NORMAL_STRESS_PER_EXPERIMENT=null
LAB_RATE_STATE_DELTA_TAU=null
ARCANA_FAULT_MINERALOGY_AND_HYDRATION=null
ARCANA_ACTUAL_FAULT_SLIP_INTERFACE_AUTHORITY=false
G2_FULL_PT_RATE_MATERIAL_COVERAGE=false
G3_BASAL_AND_CUT_PHYSICAL_FORCING=false
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

NEXT: full G2/G3 + RSF regression; if PASS, review safe fast-forward engineering merge. The subsequent **scientific** milestone should be source-specific pressure and reference friction source mapping, plate 5:8 fault-side physical topology and material context, alongside separate crust/mantle material coverage and mantle forcing. The valid PANGAEA lab model must never be automatically mapped into the ARCANA T0.

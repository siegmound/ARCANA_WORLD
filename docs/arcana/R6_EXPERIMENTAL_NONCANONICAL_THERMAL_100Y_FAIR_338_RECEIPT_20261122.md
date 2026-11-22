# ARCANA R6 — FAIR 338/338 noncanonical thermal-column 100-year benchmark receipt

**Date:** 2026-11-22.
**FAIR source commit (operator-reported checkout):** `9d65dd5a83277e4186f1340cd80c515a6212db4a`.
**Decision:** `R6_EXPERIMENTAL_100Y_SYNTHETIC_THERMAL_COLUMN_FAIR_338_PASS__PERMANENT_NONCANONICAL_NO_T1`.

## FAIR evidence from operator terminal output

The operator used FAIR `arcana-r6-linux` and executed
`bash scripts/r6_experimental_thermal_100y_fair_gate.sh` on source HEAD `9d65dd5a83277e4186f1340cd80c515a6212db4a`.
Terminal stdout was furnished in conversation; its salient values are:

```text
EXPERIMENTAL_SOURCE_HEAD=9d65dd5a83277e4186f1340cd80c515a6212db4a
EXPERIMENTAL_AUTHORITY=EXPERIMENTAL_NONCANONICAL_ONLY

34 passed in 0.17s
338 passed in 1.39s

{"decision": "EXPERIMENTAL_NONCANONICAL_100Y_CONSERVATIVE_THERMAL_BENCHMARK_PASS",
 "synthetic_numerical_run_executed": true,
 "duration_years": 100,
 "convergence_errors_k":
 [7.305767530851881e-05, 1.8270107545959036e-05, 4.567882797346101e-06],
 "energy_balance_pass": true,
 "canonical_history_created": false,
 "physical_T1": null}

FAIR_THERMAL_NUMERIC_BENCHMARK=PASS
FAIR_NUMERICAL_ERRORS_K= [7.305767530851881e-05, 1.8270107545959036e-05, 4.567882797346101e-06]
FAIR_ENERGY_RESIDUALS_J_M2=
 [1.1641532182693481e-10, -0.00012207019608467817, 0.00012207042891532183]
EXPERIMENTAL_NONCANONICAL_ONLY=TRUE
CANONICAL_PHYSICAL_T1=NULL
FAIR_EXPERIMENT_100Y_TARGET_34=PASS
FAIR_EXPERIMENT_100Y_SELECTED_338=PASS
FAIR_EXPERIMENT_100Y_SYNTHETIC_NUMERIC_GATE=PASS
```

**Evidence paths:**
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_EXP_THERMAL_100Y_TARGET_34.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_EXP_THERMAL_100Y_FULL_338.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_EXP_THERMAL_100Y_NONCANONICAL_NEW_01/REPORT.json`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_EXP_THERMAL_100Y_NONCANONICAL_NEW_01/MANIFEST.json`.

The report content and its SHA manifest were checked by the FAIR runner; the operator reports its success. **The assistant has not independently fetched/hashed the private FAIR evidence files** and does not claim any additional run or fresh numerical evaluation.

## Result interpretation

The bounded, **synthetic** one-dimensional thermal problem has authored R6 reference material parameters from `R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json`:
oceanic density 2890 kg/m³, specific heat 1000 J/(kg·K), conductivity 2.2 W/(m·K), radiogenic bulk heat proxy 3e-7 W/m³. The T0 original **model** geometry/plate anchor is `R6G1D-R089-C359` (native original plate 8, source thickness 6500 m); the 1000 m experiment subcolumn, initial 300 K + 15 K cosine, zero-flux top/bottom and constant coefficients are explicitly noncanonical declared experimental conditions, **not natural ARCANA 210 Ma T0 thermodynamics**.

For (n, dt years) = (50,1), (100,0.25), (200,0.0625), maximum temperature error against the exact **synthetic** cosine-decay+source solution decreased approximately by 4x with refinement. The residual energy integral was at most ~1.22e-4 J/m² (operator output), and all self-tests and independent assertions passed. This demonstrates expected convergence **for this one specified analytical problem**, not proof of every geographic T0 source model, 3D mesh, multiscale thermal forcing, G2/G3 mechanics, geology, groundwater or long-term physical HistoryStore.

The user-established binding governance is `docs/arcana/governance/R6_EXPERIMENTAL_RUN_NONCANONICAL_POLICY.json` (Git blob `75658d37b12ac3d2c3b3fed5b9e56203a6ae3cf1`). **All experimental simulations remain noncanonical forever**, including successful FAIR benchmarks and eventual completed simulator. No automatic promotion; any future canonical world history must come from a separately qualified and authorially ratified **new production simulation lineage**.

## Engineering acceptance

The latest R6 main prior to this branch was FAIR 304/304 tested `2ecabde7f86f052ecd25eaa34a6e4042dd7f13e7`. New selected regression **338/338**, of which 34 target new test cases, passed on exact `9d65dd5a83277e4186f1340cd80c515a6212db4a`. This is the **selected** R6 G2/G3+geology+query+thermal pilot suite, not necessarily every test available in the repository.

The pilot code, tests, source governance, immutable research config and FAIR runner are accepted for **software-only fast-forward integration**, only if main is still exact ancestor `2ecabde7f86f052ecd25eaa34a6e4042dd7f13e7`. This receipt and ledger update are documentation-only descendants of tested source HEAD `9d65dd5a83277e4186f1340cd80c515a6212db4a`. Source Python and test blob identities must remain unchanged after FAIR.

Scientific restrictions remain unchanged:
```text
FAIR_100Y_NONCANON_TARGETED=34_OF_34_PASS
FAIR_100Y_SELECTED_EXTENDED_REGRESSION=338_OF_338_PASS
FAIR_100Y_SOURCE_ANCHORED_SYNTHETIC_INTEGRATION=PASS
FAIR_100Y_ANALYTIC_ERROR_DECREASING=true
FAIR_100Y_ENERGY_INTEGRAL_PASS=true
EXPERIMENTAL_RUN_AUTHORITY=EXPERIMENTAL_NONCANONICAL_ONLY
EXPERIMENTAL_AUTOMATIC_CANON_PROMOTION=false
EPOCH_T0_PLUS_100_Y_HISTORICAL_ARCANA_T1=NOT_CALCULATED
EXPERIMENTAL_1000_Y_NUMERICAL_PILOT=NOT_RUN
REAL_WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
HISTORYSTORE_MUTATIONS=0
PHYSICAL_T1=null
D_024=ACTIVE
```

## Next scientific priority

Investigate whether a **second separate noncanonical 1000-year version** of this reduced synthetic model can be independently numerically checked (error-vs-analytic, energy, stability and step-size/space convergence). Estimate model diffusion timescale, boundary-condition influence, sensitivity to the R6 authored rho/Cp/k/Q intervals and thermal profile assumptions. Keep the special case's source T0 anchor, but **never present** the 1000-year calculation as real tectonic/hydrological/orogenic/historical history.

Separately continue closure of the actual physical T0 initialization, G2/G3 force balance, fault material/hydration, boundary histories and cross-physics validity before attempting any true world-history T1.

See `docs/arcana/R6_EXPERIMENTAL_NONCANONICAL_100Y_THERMAL_COLUMN_PILOT_20261122.md`.

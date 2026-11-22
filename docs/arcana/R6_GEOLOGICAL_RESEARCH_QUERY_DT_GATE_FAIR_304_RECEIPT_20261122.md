# ARCANA R6 — FAIR 304/304 Geological Research Query + Short-Δt Readiness Gate

**Recorded:** 2026-11-22.
**Exact operator-tested source commit:** `041704f5e37c28ce7cccbe2f72b0a2ea56df33b5`.
**Scope:** engineering research-query infrastructure and **scientific NO-GO diagnosis**, not T0-to-T1 solver qualification.
**Decision:** `R6_GEOLOGICAL_RESEARCH_QUERY_FAIR_304_PASS__DT_100_1000_Y_NO_GO_NO_PHYSICAL_T1`.

## 1. Operator-reported FAIR receipts

The operator selected the exact source commit `041704f5e37c28ce7cccbe2f72b0a2ea56df33b5` on FAIR with conda `arcana-r6-linux` and previously verified `PYTHONPATH=src:.`; the following values are reproduced from operator-provided terminal stdout, **not** independently fetched FAIR logs:

```text
29 passed in 0.13s
TARGET_EXIT_CODE=0

{"decision": "NO_GO_PHYSICAL_T0_TO_T1_FOR_100_OR_1000_YEARS", "source_bound_cells": 0, "child_geometry_count": 0, "dt_horizon_years": [100, 1000], "physical_T1": null, "world_history_production_authorized": false}
DT_GATE_EXIT_CODE=0

304 passed in 1.30s
FULL_REGRESSION_EXIT_CODE=0

{"decision": "SOURCE_BACKED_T0_RESEARCH_QUERY_ONLY_NO_NATURAL_ROCK_INFERENCE", "source_bound_cells": 1, "child_geometry_count": 4, "dt_horizon_years": [], "physical_T1": null, "world_history_production_authorized": false}
RESEARCH_QUERY_EXIT_CODE=0
PASS: REAL T0 GEOLOGICAL RESEARCH QUERY
PLATE: 8
CHILD GEOMETRIES: 4
NO NATURAL MINERALOGY OR HISTORY GENERATED
QUERY_SCIENTIFIC_CHECK_EXIT_CODE=0
```

The 304 passing cases constitute the **explicitly selected R6 G2/G3+geochemistry+geological query regression**, not every conceivable test in the repository. The `DT_GATE_EXIT_CODE=0` attests correct execution of a **NO-GO report**: it is **not** successful numerical advance of 100 or 1000 years. Query stdout plus post-output assertions attest the correct research function and provenance guard. Original FAiR raw files and manifest hashes were not independently inspected within this recording.

Reported FAIR evidence locations:

- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_RESEARCH_DT_TARGET_29.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_RESEARCH_DT_FULL_304.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_T0_DT_100_1000_GATE_NEW_01/REPORT.json` and `MANIFEST.json`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_RESEARCH_NATIVE_QUERY_NEW_01/REPORT.json` and `MANIFEST.json`

## 2. Actual verified scope

The query uses the previously qualified original 180×360 T0 source grid; on the demonstrated oceanic model cell `R6G1D-R089-C359`, the bound source plate is **8** in the original zero-based IDs `0..11`, reference crust thickness **6500 m**, and authorial oceanic material-reference density **2890 kg/m3**. A representative density parameter is **not** a measured natural local rock density; the query fixture supplies **no measured sample** and no mineral candidate. The result has four deterministic child-cell **geometries** and no child rock mass, petrology, ore, Deep or historical physical T1 assignments.

The separate `--dt-gate` audits two requested elapsed intervals, Δt = 100 and 1000 Julian years, against the original B6N8H physical T0→T1 requirements matrix at Git blob `3d27761f7f0558cf7bba7081a7cc76fad875e204`, and rejects claims of physical T1 because T0 thermal profile/bindings and governed evolution are incomplete. The B6N8H gate is an **earlier snapshot**, and the report explicitly does not claim to re-audit all more recent G2/G3 constraints.

Physical NO-GO currently continues independently of 100- versus 1000-year numerical duration. A **future** thermal-only isolated regional/column **noncanonical experiment** could be scientifically valuable to evaluate a reduced demonstrator. Such an experiment must specify source-supported or explicitly synthetic initial conditions, conductivity, heat capacity, density, heat production, surface/basal boundary histories, evolution scheme, timestep/spatial convergence, and energy accounting. It must not be represented as the accepted ARCANA global physical T1 or written as its canonical WorldHistory.

## 3. Integration and scientific authority

Integration may only fast-forward R6 main from exact `34bdfd884a418cd54ba41c24ef79b1f51f9d41da` if no competing main advance occurred. This receipt and ledger updates are **documentation-only** descendants of the FAIR-tested source `041704f5e37c28ce7cccbe2f72b0a2ea56df33b5`. Python and test file blobs must remain identical to their tested values.

```text
R6_GEO_QUERY_TARGETED=29_OF_29_PASS
R6_GEO_QUERY_SELECTED_EXTENDED=304_OF_304_PASS
R6_GEO_QUERY_SOURCE_BOUND_T0_CELLS=1
R6_GEO_QUERY_CHILD_GEOMETRIES=4
R6_GEO_QUERY_SOURCE_PLATE_ID=8
R6_GEO_QUERY_SAMPLE_MEASUREMENT=NOT_SUPPLIED
R6_DT_100_YEARS=NO_GO_PHYSICAL_T1
R6_DT_1000_YEARS=NO_GO_PHYSICAL_T1
R6_DT_100_1000_REPORT_EXIT=0
R6_PHYSICAL_T1=null
R6_NATIVE_LOCAL_NATURAL_ROCK_DENSITY=UNKNOWN
R6_NATURAL_ORE_AND_DEEP=UNASSIGNED
R6_HISTORY_STORE_WRITES=0
R6_WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
R6_MECHANICAL_SOLVE_AUTHORIZED=false
D_024=ACTIVE
```

## 4. Scientific next action

Recommend a **strictly isolated, explicitly noncanonical T0→T0+100-year thermal-column feasibility pilot**, before the proposed 1000-year case. Its purpose is numerical and physical consistency of a *specified reduced model*, **not** natural WorldSim historical evolution. Initially source-audit whether any real T0 local profile, material thermal parameters and boundary assumptions are eligible; if not, label all input as declared hypothetical or block the study. Require timestep convergence and energy-balance checks before escalating duration. Keep the original T0 research-query, resource/Deep historical potential and replayable future refinement architecture independent of that pilot. The separate older experimental authorial geochemistry plate-1..12 mapping still needs correction to original 0..11 before real source placements.

See `docs/arcana/R6_GEOLOGICAL_RESEARCH_QUERY_AND_T0_SHORT_DT_FEASIBILITY_20261122.md`.

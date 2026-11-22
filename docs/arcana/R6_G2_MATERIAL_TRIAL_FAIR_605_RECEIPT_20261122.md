# ARCANA R6 — FAIR 605 original G2 material/fluid trial software receipt

**Date:** 2026-11-22  
**FAIR-tested exact Git SHA:** `1ce49decda12fe3d57eb66f097b482d27edcdc10`  
**Development branch:** `r6/g2-t0-material-fluid-law-trial-20261122`  
**Integration branch:** `r6/multiphysics-integration-20261026`  
**Previously integrated HEAD:** `a2c285ba22f2dbc40bda9d1c097989c0a7e1f249`  
**Decision:** `SOURCE_AUTHENTIC_G2_EXPLICIT_MATERIAL_TRIAL_SOFTWARE_FAIR_PASS__SOURCE_GEOLOGY_UNSELECTED`  
**Evidence qualification:** operator-pasted FAIR terminal results; external source report bytes not independently imported here.

## FAIR operator terminal results

```text
G2_T0_MATERIAL_TRIAL_CODE_HEAD=1ce49decda12fe3d57eb66f097b482d27edcdc10
G2_T0_MATERIAL_TRIAL_AUTHORITY=EXPLICIT_NONCANONICAL_AUTHORIAL_ENGINEERING_TRIAL_NO_SOURCE_ROCK
67 passed in 0.14s
605 passed in 4.37s
{"decision":"G2_T0_EXPLICIT_MATERIAL_TRIAL_ENGINE__SOURCE_LITHOLOGY_UNSELECTED",
 "original_8x8_nodes":81,"original_16x16_nodes":289,
 "selected_rock_phases":0,"selected_fluid_pressures":0,
 "selected_constitutive_laws":0,
 "independent_explicit_material_trial_engine":true,
 "physical_T1":null,"mechanical_solve_authorized":false,"D_024":"ACTIVE"}
FAIR_G2_T0_MATERIAL_UNSELECTED_SOURCE_8X8=PASS
FAIR_G2_T0_MATERIAL_UNSELECTED_SOURCE_16X16=PASS
FAIR_G2_T0_MATERIAL_SOURCE_CHAIN_AND_COLD_PT_REPLAY=PASS
FAIR_G2_T0_MATERIAL_TARGET_67=PASS
FAIR_G2_T0_MATERIAL_SELECTED_605=PASS
FAIR_G2_T0_MATERIAL_NO_ROCK_FLUID_FAULT_SOLVE_OR_T1=PASS
```

The 67 new targeted tests are a **subset of** the 605 selected regression tests (not 672 distinct tests). This was not an exhaustive all-repository test run.

## Exact code lineage and unchanged FAIR-tested Git blobs

Integration was performed via **successful non-force fast-forward** with `expected_sha=a2c285ba22f2dbc40bda9d1c097989c0a7e1f249`, targeting the exact tested source commit `1ce49decda12fe3d57eb66f097b482d27edcdc10`. Git compare before update showed **7 ahead, 0 behind** and no code changes between tested and development source SHA.

| Path | Exactly tested Git blob SHA |
|---|---|
| `experiments/plate58_deforming_explore_v1/g2_t0_material_trial.py` | `021a1aecf9cb71750e719a68a0f438b29a263e69` |
| `tests/test_r6_g2_t0_material_trial.py` | `7194fad3ba2f4b2fef5c9bce97220ee51823a498` |
| `scripts/r6_g2_t0_material_trial_fair_gate.sh` | `85fdbc959ba0227a0506a0efb4131f7171335e08` |

The FAIR operator gate re-opened both original 8×8/16×16 source pairs, coupled handoff, source conditional P–T, and Earth-only cold-context references and wrote non-overwriting evidence under:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2_T0_MATERIAL_FLUID_TRIAL_NEW01/
```

The actual original-source G2 templates remain **UNSELECTED**. The 81 and 289 values refer to original parent-node counts for two overlapping regional extents; they are not independently assigned rock-material sample populations.

## Scientific scope and no-go

The reusable engine can test *explicitly supplied* hypothetical continuum Drucker–Prager and triaxial differential-stress creep laws against stated T/P/rate/water provenance and material conditions. A passing numerical trial **does not identify Arcana T0 rocks or phases, physical pore/fluid state, fault-side normal stress, independent mantle forcing or a real brittle–ductile transition**. Stress invariants from distinct laws are not interchangeable without validated transformation.

```text
source_materials_selected = 0
source_fluid_pressures_selected = 0
source_constitutive_laws_selected = 0
D-024 = ACTIVE
mechanical_solve_authorized = false
physical_T1 = null
WORLD_HISTORY_PRODUCTION_AUTHORIZED = false
```

After this software-only FAIR milestone, the research direction is *tool orchestration and evidence-based replacement*, not mandatory continuation of current solver architecture. See `docs/arcana/R6_TOOL_ORCHESTRATOR_REPLACEABILITY_ADR_20261122.md`. Older FAIR receipts and externally immutable evidence remain recoverable, even if their code is later superseded.

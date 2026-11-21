# ARCANA R6 — FAIR Earth reference geochemistry: source compilation and 200/200 regression

**Date:** 2026-11-21. **Exact FAIR-tested code HEAD:** `9b1ddd456121fb0df7d437480b1344149a6884d3`.
**Decision:** `EARTH_GEOCHEM_REFERENCE_LIBRARY_FAIR_200_PASS__ORIGINAL_T0_MINERAL_COMPOSITION_UNASSIGNED`.

## FAIR terminal receipt (operator-provided)

```text
HEAD is now at 9b1ddd45 docs(r6): register 6 Earth chemistry references, 63,620 thermophysical support-only and FAIR validation pending
17 passed in 0.08s
TARGET_EXIT_CODE=0
200 passed in 1.03s
FULL_REGRESSION_EXIT_CODE=0
{
  "decision": "REAL_EARTH_BULK_GEOCHEMISTRY_LIBRARY__R6_T0_COMPOSITION_UNASSIGNED",
  "earth_reference_records": 6,
  "native_T0_cells": 64800,
  "thermal_support_cells": 63620,
  "T0_composition_assignments": 0,
  "T0_mineral_phase_assignments": 0,
  "T0_fault_gouge_assignments": 0,
  "D_024": "ACTIVE",
  "physical_T1": null
}
GEOCHEM_SOURCE_EXIT_CODE=0
```

**Scope of verification:** the FAIR operator reported successful targeted (17/17) and prescribed extended G2/G3+RSF+T0+geochemistry (200/200) pytest suites and execution of the Earth geochemistry source compiler. The assistant did not independently execute FAIR or receive its immutable `REPORT.json`/`MANIFEST.json` bytes. These are the exact operator-provided results and test SHA. This is **not a claim of globally running the entire repository's tests**, nor of original ARCANA physical material mapping.

Expected FAIR evidence paths:
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEOCH_TARGET_17.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEOCH_FULL_200.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEOCH_REAL_SOURCES.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_T0_EARTH_GEOCH_REFERENCE_NEW_01/REPORT.json` and `MANIFEST.json`.

## Published-source chemistry and scope

Three upstream published Earth analogue tables were vendor-copied byte-for-byte from MIT-licensed georefdatar commit `e82b70de1b65d8e9cde52166b93ebc88a50934b2`, with source Git blob SHA verified in GitHub:

| Source reference | Scope | Original Git blob |
|---|---|---|
| Rudnick and Gao (2014) | Four Earth continental crust averages: upper, middle, lower, bulk; oxide wt.% + selected traces | `4127120d7499e3d9b62a22384465c39b8806aaf0` |
| Salters and Stracke (2004) | Earth depleted mantle reference reservoir, oxide wt.% and water **model** `H2O=116 ppm` | `262447b687f5cae36fde836ffd12c7d439a9f16b` |
| Sun and McDonough (1989) | Earth N-type MORB trace proxy; source CSV does not declare per-value units | `10e8fce96afa6ddd2b50f0f8a43d783f60d5c34c` |

No terrestrial mean was auto-bound to ARCANA 210 Ma. Source table dimensions are distinct from T0 support classes. The original R6 source registry has `64,800` native 1° cells with `63,620` **conditionally admitted thermal/material role** support cells (14,258 continental + 49,362 ocean), and 1,180 excluded/unknown thermal cells. Thermal support eligibility is not a spatial bulk-oxide or mineral identification. No stratified upper/middle/lower crust ARCANA composition is supplied by the terrestrial tables.

The compiled elemental accounting for selected published oxides is **oxide-equivalent** and explicitly does not infer modal minerals, Fe²⁺/Fe³⁺, equilibrated lithology, water activity, actual fault gouge, tectonic crust formation, ore deposits or spatial Deep concentrations. The published water estimate in terrestrial depleted MORB mantle is not a T0 fault pore pressure or an actual ARCANA mantle hydration field. The Sun/McDonough file has no unit-bearing column, hence values are retained unconverted as a **trace-only, unit-unknown** analogue.

## Software integration acceptance and hard boundaries

The software step is qualified for **engineering integration only** with a non-forced fast-forward after confirming main is an ancestor of the source-tested branch. Any subsequent receipt commit modifies only documentation. It does not ratify actual T0 compositions.

```text
EARTH_GEOCHEM_PINNED_REFERENCE_RECORDS=6
R6_T0_NATIVE_CELLS=64800
R6_THERMAL_ROLE_SUPPORT=63620
R6_FAIR_GEOCH_TARGETED=17_OF_17_PASS
R6_FAIR_GEOCH_EXTENDED=200_OF_200_PASS
R6_FAIR_SOURCE_COMPILER_EXIT=0
ARCANA_T0_BULK_GEOCHEM_CELL_ASSIGNMENTS=0
ARCANA_T0_MINERAL_MODAL_CELL_ASSIGNMENTS=0
ARCANA_T0_FAULT_GOUGE_ASSIGNMENTS=0
ARCANA_T0_GEOLOGICAL_RESOURCE_DEPOSITS=null
ARCANA_T0_DEEP_X_ACCESSIBILITY=null
G2_CONSTITUTIVE_ROCK_PT_RATE_AND_WATER_AUTHORITY=false
G3_PHYSICAL_MANTLE_CUT_AND_GPE_FORCING=false
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

## Next substantive scientific action

Develop a **bounded authorially configurable T0 bulk-rock composition scenario contract** using exact original source support IDs, plate provenance and phase-specific material roles; do not assign 6 Earth references directly to the world. Select/record a defensible geological prior and spatial heterogeneity, native lithology/chemistry/facies assumptions with confidence and uncertainty. Separate basaltic ocean crust, gabbro, sediments, mantle and fault gouge. The next experimental gate should require fully unit-tagged oxide totals and volatiles (including Fe oxidation state), phase equilibrium P/T, fluid fugacity and a provider with an applicability range before claiming mineral assemblages, deposits or rheology. Geological history must be conserved over time; no arbitrary per-cell ore deposit concentrations or Deep accessibility from oxide abundance. `D-024` remains active until continuous physical source-qualified T0→T1 closure.

Related source audit: `docs/arcana/R6_T0_GEOLOGICAL_COMPOSITION_REAL_EARTH_REFERENCES_AND_IDENTIFIABILITY_20261121.md`.

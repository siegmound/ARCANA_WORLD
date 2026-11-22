# ARCANA R6 — FAIR 538 original T0 cold-crust thermal context receipt

**Date:** 2026-11-22  
**Exactly FAIR-tested Git SHA:** `dbf48ede0f4192a5c3eff2b67ed341a6e25db41b`  
**Development branch:** `r6/g2-cold-crust-rheology-relevance-20261122`  
**Base integration SHA:** `b095c051d55589e28546be49c9db603c8f409cea`  
**Decision:** `FAIR_538_SOURCE_ORIGINAL_T0_COLD_CRUST_TEMPERATURE_CONTEXT_PASS__NO_RHEOLOGY_OR_T1`  
**Evidence classification:** `FAIR_OPERATOR_TERMINAL_REPORTED_PASS__EXTERNAL_MANIFEST_BYTES_NOT_INDEPENDENTLY_IMPORTED`

## 1. Operator terminal acceptance (exact source SHA)

```text
COLD_CRUST_CODE_HEAD=dbf48ede0f4192a5c3eff2b67ed341a6e25db41b
COLD_CRUST_AUTHORITY=EARTH_CONTEXTUAL_THERMAL_WINDOW__NOT_LAB_CONSTITUTIVE_VALIDITY
51 passed in 0.10s
538 passed in 4.32s
{"decision":"SOURCE_T0_COLD_CRUST_THERMAL_CONTEXT__NO_CONSTITUTIVE_LAW_SELECTED",
 "original_8x8_source_nodes":81,
 "original_16x16_source_nodes":289,
 "earth_analogue_BPT_temperature_only_nodes_8x8":81,
 "earth_analogue_BPT_temperature_only_nodes_16x16":248,
 "GT95_T_only_nodes_8x8":0,
 "GT95_T_only_nodes_16x16":0,
 "source_materials_assigned":0,
 "source_fault_stresses_assigned":0,
 "physical_T1":null,
 "mechanical_solve_authorized":false,
 "D_024":"ACTIVE"}
FAIR_G2G3_T0_8X8_COLD_CRUST_TEMP_CONTEXT=PASS
FAIR_G2G3_T0_8X8_EARTH_CONTEXT_WINDOW_NODE_COUNT=81
FAIR_G2G3_T0_16X16_COLD_CRUST_TEMP_CONTEXT=PASS
FAIR_G2G3_T0_16X16_EARTH_CONTEXT_WINDOW_NODE_COUNT=248
FAIR_G2G3_T0_COLD_CRUST_SOURCE_SHA_RECONSTRUCTION=PASS
FAIR_G2G3_T0_COLD_CRUST_TARGET_51=PASS
FAIR_G2G3_T0_COLD_CRUST_SELECTED_538=PASS
FAIR_G2G3_T0_COLD_CRUST_NO_LAW_SELECTION_OR_T1=PASS
```

**Counting policy:** the 51 new tests are included in 538 selected R6 regression tests, NOT additive; 538 does not claim whole-repository exhaustive coverage. The two footprints overlap, so the reported 81+289 node evaluations are **not 370 independent or global source nodes**. There were 248 of 289 nodes with **any nonzero-depth temperature-only intersection** in 16×16, leaving 41 that do not intersect this particular Earth contextual interval. All 81 of 81 nodes in 8×8 intersect.

## 2. Scientifically bounded interpretation

The numerical result reconstructs the **original source-authenticated T0 PRE crustal cubic temperature profiles** and solves for depth intervals where `T(z)` intersects an **Earth quartz-rich brittle/plastic transition contextual corridor** of 523.15–623.15 K (250–350°C). Multiple disjoint depth intervals and nonlinear profiles are handled; their co-located *conditional vertical overburden increments* are reported, but **no actual brittle–ductile transition depth or material law is inferred**. Temperature *overlap* does not prove phase identity, semibrittle/low-T creep applicability, frictional regime, transition, strength, stress or rate validity.

The independent pre-existing FAIR 487 P–T source result already found **zero** T-only overlap with terrestrial wet-quartzite GT95 [1173.15,1373.15] K for every original crustal node in both extents. The current FAIR 538 report re-confirms zero GT95 source-node overlap: **do not use GT95 as full-cold-crust creep**. The new Earth-only Byerlee laboratory/reference friction operator is separate from the source-nodal calculation; it requires *external explicitly supplied* effective normal stress and never creates Arcana fault traction, pressure or friction coefficients.

This is **source-authentic numerical contextual analysis**, not a physically ratified T0 rock/fault state. No surface load, pore/effective pressure, mineralogy, water fugacity, plate-specific rheology, damaged interface, mantle coupling, sourced basal/cut tractions, GPE vertical closure, physical T1 or HistoryStore is authorized or generated. The original 8×8 has no **local** 3-plate junction, even when global parent node 34587 is in its footprint; 16×16 retains the authentic three-plate local junction.

## 3. Evidence provenance, no overwrite

The script on tested SHA reopens and SHA-validates original source input directories, coupled handoff and lithostatic P–T reports:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02/
  R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01/
  R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01/
```

The script creates distinct **write-once** evidence and logs:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_COLD_CRUST_TARGET_51_NEW01.log
  R6_G2G3_COLD_CRUST_SELECTED_538_NEW01.log
  R6_G2G3_T0_COLD_CRUST_REGIME_NEW01/
```

The gate validates all recorded output SHA-256, node counts, 523.15–623.15 K temperature-only scope, non-ratification flags and exact replay before printing PASS. The original FAIR folder bytes/logs were **not fetched or independently hashed a second time** into the documentation environment; this receipt cites the user's operator terminal and the independently inspected exact committed runner source.

## 4. Decision and next science

```text
FAIR_TARGETED=51/51_OPERATOR_REPORTED_PASS
FAIR_SELECTED=538/538_OPERATOR_REPORTED_PASS
FAIR_ORIGINAL_8X8_CONTEXT_NODES=81/81
FAIR_ORIGINAL_16X16_CONTEXT_NODES=248/289
FAIR_GT95_ANY_CRUST_OVERLAP_8X8=0
FAIR_GT95_ANY_CRUST_OVERLAP_16X16=0
EARTH_BPT_CONTEXT_NOT_A_LAB_LAW=true
SOURCE_MATERIALS_ASSIGNED=0
SOURCE_FAULT_STRESSES_ASSIGNED=0
G2_LITHOLOGY_WATER_PRESSURE_P_T_RATE=UNKNOWN
G3_CUT_BASAL_MANTLE_GPE=UNKNOWN
FAULT_SIDED_MECHANICAL_LAW=UNKNOWN
D_024=ACTIVE
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_T1=null
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

Software-only no-force fast-forward to R6 integration is eligible **only after** ancestral comparison and exact unchanged module/test/script Git blob verification against FAIR source `dbf48ede0f4192a5c3eff2b67ed341a6e25db41b`. Receipt and ledger commits made after FAIR do not expand numeric or physical authority.

The next *substantive* science stage is choosing and source-validating an **explicit single-bounded 8×8 T0 regional material hypothesis** (mineral phase/rock identity and heterogeneity with known Earth-analogue-vs-Arcana authority), water/hydration/effective pressure, and **full cold-crust lab T/P/stress/rate applicability** for a brittle and low-temperature-plastic mechanism. Then independently source G3 forces and true fault-sided law before any actual physical T0→T1; 16×16 is regional extent sensitivity, not automatic mesh convergence.

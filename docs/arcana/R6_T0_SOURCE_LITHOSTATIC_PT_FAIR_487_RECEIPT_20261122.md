# ARCANA R6 — FAIR 487 original T0 conditional lithostatic P–T reference

**Date:** 2026-11-22  
**Exactly executed FAIR code SHA:** `38f68c329751520849745dad6f2c9c022b78b59e`  
**Development branch:** `r6/t0-source-lithostatic-pt-20261122`  
**Source integration base:** `042545cc8e86eb39770d54be697a2216062e05a9`  
**Decision:** `FAIR_487_ORIGINAL_T0_CONDITIONAL_LITHOSTATIC_PT_PASS__GT95_T_COVERAGE_ZERO__PHYSICAL_T1_BLOCKED`  
**Evidence class:** `FAIR_OPERATOR_TERMINAL_REPORTED_PASS__RAW_EXTERNAL_FILES_NOT_INDEPENDENTLY_TRANSFERRED`

## 1. Operator terminal acceptance at exact code SHA

```text
G2G3_T0_PT_SOURCE_CODE_HEAD=38f68c329751520849745dad6f2c9c022b78b59e
G2G3_T0_PT_SOURCE_AUTHORITY=CONDITIONAL_SOURCE_MODEL_REFERENCE_NONCANONICAL
36 passed in 0.41s
487 passed in 4.23s
{"decision":"ORIGINAL_T0_CONDITIONAL_LITHOSTATIC_PRESSURE_AND_EXACT_THERMAL_PT__NOT_PHYSICAL_STRESS",
 "original_8x8_nodes":81, "original_16x16_nodes":289,
 "source_8x8_moho_delta_overburden_Pa_range":[769888000.0,1374800000.0],
 "source_8x8_base_delta_overburden_Pa_range":[2455000000.0,4202960000.0],
 "GT95_T_only_whole_crust_count_8x8":0,
 "unresolved_G2_G3_FAULT_groups":8,
 "mechanical_solve_authorized":false,"physical_T1":null,"D_024":"ACTIVE"}
FAIR_G2G3_ORIGINAL_T0_8X8_CONDITIONAL_PT=PASS
FAIR_G2G3_ORIGINAL_T0_8X8_GT95_T_ONLY_COVERAGE={'temperature_only_some_overlap': 0, 'temperature_only_full_layer_covered': 0}
FAIR_G2G3_ORIGINAL_T0_16X16_CONDITIONAL_PT=PASS
FAIR_G2G3_ORIGINAL_T0_16X16_GT95_T_ONLY_COVERAGE={'temperature_only_some_overlap': 0, 'temperature_only_full_layer_covered': 0}
FAIR_G2G3_SOURCE_PRE_GRAVITY_LAB_SHA_PINNED=PASS
FAIR_G2G3_T0_LITHOSTATIC_PT_REFERENCE_TARGET_36=PASS
FAIR_G2G3_T0_LITHOSTATIC_PT_REFERENCE_SELECTED_487=PASS
FAIR_G2G3_CONDITIONAL_PT_NO_PHYSICAL_STRESS_OR_T1=PASS
```

The 36 new targeted tests **are included in** the 487 selected R6 tests. The 487 are a selected regression, not a statement of exhaustive whole-repository coverage.

## 2. Physically meaningful *conditional* result

The model uses original SHA-pinned T0 PRE source crust/mantle-lithosphere layer thickness, density, and cubic temperature coefficients, and the pinned R6 gravity value **9.82 m/s²**. It solves a 1D constant-layer-density overburden **increment** relative to the mathematical model surface:

```text
Delta(sigma_v)(z) = integral_{0}^{z} rho(z') * g dz'     [Pa]
```

The original 8×8 nodes produce these source-model conditional overburden increments:

| Level | Minimum | Maximum |
|---|---:|---:|
| Moho | 769,888,000 Pa | 1,374,800,000 Pa |
| Lithosphere base | 2,455,000,000 Pa | 4,202,960,000 Pa |

They are **NOT** absolute lithostatic or pore pressure, stress on a fault plane, actual mantle traction, calibrated GPE or verified T0 natural rock properties. The exact surface/atmospheric/ocean loads, realistic pressure evolution, pore/fluid pressures, effective stresses, topographic force closure and mechanical LAB remain unprovided. These numbers must **never** be assigned to fault effective normal stress or G3 basal force by naming convention.

The original 8×8 and 16×16 crustal PRE cubic temperature ranges have **zero nodes with any temperature overlap** with terrestrial wet-quartzite GT95 laboratory T interval **1173.15–1373.15 K** and zero whole-crust coverage, in both domains. This is temperature-only rejection of *that particular full-crust GT95 analogue* at T0. It does not prove that no other crustal rheology exists; it also does not establish actual Arcana phase identity, creep coefficients, water/fugacity or local fault conditions.

The two original regions contain 81+289 original source columns (370 counted across **two overlapping extents**, not 370 independent global cells). The 16×16 domain is **regional extent sensitivity**, not automatically grid convergence.

## 3. Frozen provenance and reported evidence

The tested code pins Git blob `7b182347014747f14ffcd591bdcf4f7f87640e87` for `experiments/plate58_deforming_explore_v1/G2_G3_PAIRED_PHYSICAL_SCENARIO_V1.json` to read gravity and GT95 T scope. The FAIR script source-reads, revalidates and leaves unchanged:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02/
  R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02/
  R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01/
```

New non-overwriting exact output paths in committed gate:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_G2G3_PT_REFERENCE_TARGET_36_NEW01.log
  R6_G2G3_PT_REFERENCE_SELECTED_487_NEW01.log
  R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01/
    REGION_8X8_SOURCE_PT.json
    REGION_16X16_SOURCE_PT.json
    AUDIT.json
    MANIFEST.json
```

The script rehashes the output files via manifest and asserts no physical solve, all eight unresolved G2/G3/FAULT groups, and null absolute/fault/effective/pore pressures for every source node. These checks printed PASS in FAIR terminal. This receipt **does not claim an independent second download/byte audit** of the FAIR output directories, nor an independent 16×16 pressure range not supplied in operator stdout.

## 4. Authority boundary and next science

```text
FAIR_TARGETED=36/36_OPERATOR_REPORTED_PASS
FAIR_SELECTED=487/487_OPERATOR_REPORTED_PASS
FAIR_ORIGINAL_SOURCE_REOPEN_8X8=PASS
FAIR_ORIGINAL_SOURCE_REOPEN_16X16=PASS
SOURCE_MODEL_DELTA_OVERBURDEN=CONDITIONALLY_COMPUTED
GT95_T_ONLY_ANY_OVERLAP_8X8=0
GT95_T_ONLY_ANY_OVERLAP_16X16=0
G2_ACTUAL_MINERALOGY_AND_WATER=UNKNOWN
G2_CONSTITUTIVE_FULL_T_P_RATE_COVERAGE=UNKNOWN
G3_ACTUAL_BASAL_AND_CUT_TRACTIONS=UNKNOWN
FAULT_NORMAL_EFFECTIVE_PRESSURE=UNKNOWN
PHYSICAL_T1=null
MECHANICAL_SOLVE_AUTHORIZED=false
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

**Software-only no-force integration** may proceed after exact ancestry and code/test/runner blob comparisons against the above FAIR-tested SHA. This source-calibrated *input-support* pressure derivation does not close the G2/G3/FAULT constitutive, mantle/GPE or fault mechanics.

Next actual science priority: source/authorially select one specific 8×8 rock/phase + fluid state and a constitutive mechanism covering the actual PRE thermal domain, then calibrate pressure/rate/stress conventions and apply independent mantle/GPE, full basal/cut forces and real sided fault law. Do not stretch the GT95 law into the cold crust by extrapolation; do not silently convert conditional overburden into effective pressure or fault normal stress.

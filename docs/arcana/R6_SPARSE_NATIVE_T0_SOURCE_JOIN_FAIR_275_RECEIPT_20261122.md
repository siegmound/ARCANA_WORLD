# ARCANA R6 — FAIR 275/275 sparse original T0 native geological source join

**Receipt date:** 2026-11-22.
**Exact FAIR-tested software HEAD:** `2974dc341d6a6ff22f45f619ae53b413b43893df`.
**Decision:** `R6_T0_SPARSE_SOURCE_BOUND_GEOLOGICAL_READBACK_FAIR_275_PASS__NO_NATURAL_GEOLOGY_OR_HISTORY_PRODUCTION`.

## 1. FAIR evidence reported by operator

On workstation FAIR, using `arcana-r6-linux` and source commit `2974dc341d6a6ff22f45f619ae53b413b43893df`, the operator reports:

```text
.....................                                                    [100%]
21 passed in 0.23s
TARGET_EXIT_CODE=0
B-v2 Field Package: FOUND
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY/R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz
Vector Plate Partition: FOUND
  /home/jlpfritas/HPC-POMDP/Arcana/_ARCANA_EXTERNAL_SOURCES/r6/tectonic_t0/R6_T0_VECTOR_PLATE_PARTITION.npz

275 passed in 1.23s
FULL_REGRESSION_EXIT_CODE=0

{"decision": "PINNED_SPARSE_NATIVE_T0_COARSE_SOURCE_EXTRACTED_NO_NATURAL_ROCK_MAP",
 "source_bound_cells": 1,
 "density_reference_not_natural_cell_density": true,
 "child_geometry_count": 4,
 "natural_rock_mineralogy_created": 0, "physical_T1": null}
SOURCE_EXTRACTION_EXIT_CODE=0

PASS: ORIGINAL T0 SOURCE JOIN VERIFIED
Plate ID: 8
Crust domain: NORMAL_OCEANIC
Crust thickness (m): 6500.0
Reference density (kg/m3): 2890.0
Child geometries: 4
No natural mineralogy or physical history generated
SOURCE_SCIENTIFIC_CHECK_EXIT_CODE=0
```

The transcript for the source assertion contains terminal paste/rendering artifacts, but success of the CLI and the final scientific assertion exit code 0 were explicitly reported. This receipt cites **operator-provided terminal output**, not an independent FAIR execution, raw evidence-file content, or independently computed source SHA digests. The public adapter verified both original NPZ SHA256 values in its successful extraction path, while the independent terminal assertion verified their expected digest identifiers in the report. This is a FAIR source-integrity readback conditional on the original code path and checked output, not proof of cellwise natural petrology.

Expected source logs:
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_SOURCE_TARGET_21.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_SOURCE_FULL_275.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_NATIVE_T0_SOURCE_DEMO_NEW_01/REPORT.json`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_NATIVE_T0_SOURCE_DEMO_NEW_01/MANIFEST.json`

## 2. Scientific adjudication

The branch source `src/arcana_worldsim/r6/geological_source_t0_adapter.py` is accepted for **read-only engineering integration** because FAIR demonstrated:
- Exact SHA-pinned original field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e` and tectonic partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`, including source manifest Git blob pins.
- Recovered a genuine native **model T0** cell `R6G1D-R089-C359` with canonical plate ID **8** from correctly zero-based plate set `0..11`, source crust class `NORMAL_OCEANIC`, source model crust thickness **6,500 m**, authored thermophysical reference density **2,890 kg/m³**.
- Produced exactly 4 deterministic child-cell geometries for a 2×2 request. No physical density, child mass, geochemical composition, modal mineral phase, ore inventory, Deep access or historical state is created in child cells.
- Demonstrated 21/21 new tests and 275/275 **selected R6 extended regression** tests PASS; not the entire possible repository test suite.

**Authority limits:** density=2,890 kg/m³ is an authorially chosen **bulk oceanic-crust reference**, not a sampled/observed local rock density. The native domain and crustal thickness are fields of the T0 physical **model**; they do not prove a real sampled rock or resource deposit. `B6N8N_thermal_membership_verified=false`: the exact 63,620-cell thermophysical eligibility membership was not separately reconstructed or attested during this extraction. That thermal eligibility does not define which cells have real mineralogy; all 64,800 parent cells remain spatially valid. No sourcing of chemistry, 3D subsurface stratigraphy, ore formation, biological populations or Deep energy distribution has occurred.

The earlier separate `experiments/t0_authorial_composition_v1/provider.py` uses a contradictory plate range 1..12 for hypothetical native placement; it was NOT invoked in these source tests and must be corrected to canonical 0..11 before any source-backed compositional placement. Do not claim it is source-validated.

## 3. Engineering and physical gates

Engineering acceptance permits a **nonforced fast-forward** from R6 main `0fe8605eaf60147429e51490d1963f7f2de3f434` to a later receipt-only descendent of the exact FAIR-tested source SHA `2974dc341d6a6ff22f45f619ae53b413b43893df`. No Python source or tests may be changed after FAIR without new execution.

Scientific status:
```text
R6_SPARSE_NATIVE_T0_ADAPTER_TARGETED=21/21_PASS
R6_R6_G2_G3_AND_GEOLOGY_SELECTED_REGRESSION=275/275_PASS
R6_T0_SOURCE_NPZ_SHA_VERIFY_IN_EXTRACTOR=PASS
R6_DEMONSTRATED_SOURCE_CELL=R6G1D-R089-C359
R6_DEMONSTRATED_SOURCE_PLATE=8
R6_DEMONSTRATED_CRUST_ROLE=NORMAL_OCEANIC
R6_DEMONSTRATED_MODEL_CRUST_THICKNESS_M=6500.0
R6_DEMONSTRATED_REFERENCE_RHO_KG_M3=2890.0
R6_REFINEMENT_REQUEST_CHILD_GEOMETRIES=4
NATURAL_CELL_ROCK_DENSITY_ASSIGNMENTS=0
NATURAL_MINERAL_OR_ORE_ASSIGNMENTS=0
DEEP_ACCESSIBILITY_ASSIGNMENTS=0
B6N8N_EXACT_THERMAL_MEMBERSHIP_PER_CELL=NOT_VERIFIED
ORIGINAL_PARENT_PHYSICAL_HISTORY=NOT_GENERATED
T0_TO_T1_MECHANICAL_SOLVE_AUTHORIZED=false
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
D_024=ACTIVE
physical_T1=null
```

## 4. Next lightweight science milestone

Honor the operator-approved low-computation strategy: retain sparse provenance-qualified T0 coarse information and query-only refinement rather than full 3D all-cell petrology. The next task should:
1. Resolve the plate-ID mismatch in the older **hypothetical** geochemical placement contract from 1..12 to 0..11 and rerun FAIR compatibility if it is to be used.
2. Provide an evidence-backed bridge from authentic source-read native T0 coarse values to an explicitly **nullable** research sample screen, keeping reference rho separate from observational rho and preserving source IDs, checkpoint/epoch, uncertainties and original geometry.
3. When material-history physics later qualifies, bind to original R6 historical event/checkpoint provenance and enforce parent-child *extensive* mass/energy conservation. Do not precompute mineral assemblages, Deep or resource occurrence globally.

Source design: `docs/arcana/R6_SPARSE_NATIVE_T0_SOURCE_GEOLOGICAL_ADAPTER_20261122.md`.

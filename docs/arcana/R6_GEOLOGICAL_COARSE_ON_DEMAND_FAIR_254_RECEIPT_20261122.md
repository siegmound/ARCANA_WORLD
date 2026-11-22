# ARCANA R6 — FAIR 254/254 geological coarse state and on-demand refinement receipt

**Date recorded:** 2026-11-22. **Exact operator-tested development source commit:** `2a4c217facf398c3a8a977b4e097cc17dd95fef9`.
**Decision:** `GEOLOGICAL_COARSE_ON_DEMAND_INFRASTRUCTURE_FAIR_254_PASS__NO_PHYSICAL_GEOLOGICAL_HISTORY`.

## Operator-reported FAIR execution

The operator checked out exact source commit `2a4c217facf398c3a8a977b4e097cc17dd95fef9` at `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY`, in conda environment `arcana-r6-linux` (Python 3.12.14; pytest 9.1.1). Initial shell runs had an environment activation failure and then `ModuleNotFoundError: No module named 'arcana_worldsim'` because `PYTHONPATH=src:.` was not exported. These failures were environmental only, were corrected and never reflected a failed scientific unit test.

The operator provided the following successful terminal results (preserved semantically from pasted stdout; assistant did **not** fetch the actual FAIR log files or output bytes):

```text
30 passed in 0.14s
TARGET_EXIT_CODE=0

254 passed in 1.38s
FULL_REGRESSION_EXIT_CODE=0

{"status": "EMPTY_SPARSE_GEOLOGY_TEMPLATE", "real_geological_cells": 0, "physical_T1": null}
TEMPLATE_EXIT_CODE=0

{"decision": "SPARSE_COARSE_CATALOG_CONTRACT_VERIFIED_NO_REAL_T0_STATE", "child_geometry_count": 0, "actual_geological_cells": 0, "physical_T1": null}
EMPTY_CATALOG_EXIT_CODE=0

{"decision": "ON_DEMAND_GEOMETRY_AND_CONSTRAINTS_ONLY_NO_GEOLOGY_CREATED", "child_geometry_count": 4, "actual_geological_cells": 0, "physical_T1": null}
REFINEMENT_DEMO_EXIT_CODE=0

PASS: raffinamento deterministico, nessuna geologia inventata
SCIENTIFIC_CONTRACT_EXIT_CODE=0
```

**Scope:** 30 new tests and 254 tests in the **explicitly selected R6 G2/G3, geology, RSF, geochemical and new coarse-state regression**, *not* a claim that the repository's entire possible test inventory ran. The 4 successful CLI stages were template, empty catalog, demo query, and output assertion; they are not four independent geology/physics solver benchmarks.

FAIR evidence directory paths supplied by shell invocation:
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_COARSE_TARGET_30.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_COARSE_FULL_254.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_COARSE_EMPTY_TEMPLATE_NEW_01.json`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_COARSE_EMPTY_REPORT_NEW_01/REPORT.json` and `MANIFEST.json`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_GEO_COARSE_GEOMETRY_DEMO_NEW_01/REPORT.json` and `MANIFEST.json`.

No actual FAIR output SHA256 values were furnished here; the source tests validate their format, and operator's terminal asserts validate key resulting fields, but this receipt does **not** claim independently audited bytes or immutable log digests.

## Scientific adjudication

The new `src/arcana_worldsim/r6/geological_coarse_state.py` is accepted as **software infrastructure only**:
- Reuses R6's original 180 × 360 (64,800) cell identity and `hierarchical_refinement.subdivide_parent_cells` without a second world grid.
- Uses the B6N8N source index (Git blob `e06770577ebaf549aa113a4e72ec9f6095a29c2d`) for 63,620 **thermophysical eligible**, not natural bulk-rock chemistry or modal mineral mapping.
- Provides a bounded **sparse** noncanonical geology hypothesis catalog for optional family, density/temperature/thickness intervals and source-identified event claims. No blanket per-cell inventory, mineral composition, ore deposit or Deep atlas is constructed.
- Deterministically generates four geometric child cells in the demonstrated 2×2 request; every child's geological family, density, rock mass, minerals, water, ore probability and Deep access remain `null`.
- Screens a density sample only against explicitly declared intervals, without posterior probabilities, inference of genuine minerals, or guarantees that lack of interval overlap proves absence.
- Does **not** claim parent/child mass conservation without authentic extensive parent mass and volumes; `conservation_checked=false` until independent providers validate it.
- Does **not** execute physical tectonic T0→T1, material history, G2/G3 coupling, physical caveats, HistoryStore write, or source-backed ore/Deep production.

The demonstrated parent cell is an **arbitrary synthetic geometry-only research query**, not user-selected or geologically qualified T0 material. The empty catalog has zero physical geological assignments and no physical history. R6 main engineering integration is safe only as a nonforced fast-forward after confirming main's ancestor SHA equals `3805648c36aa70e7ab709e593c33abaaedfb616e`; the FAIR-tested source code remains unchanged by this documentation-only receipt.

```text
FAIR_GEO_COARSE_TARGETED=30_OF_30_PASS
FAIR_GEO_COARSE_SELECTED_EXTENDED=254_OF_254_PASS
FAIR_EMPTY_CATALOG_TEMPLATE=PASS
FAIR_EMPTY_CATALOG_REPORT=PASS
FAIR_ON_DEMAND_DEMO_CHILD_GEOMETRY=4
FAIR_SCIENTIFIC_ASSERTIONS=PASS
R6_ORIGINAL_NATIVE_PARENT_CELLS=64800
R6_THERMOPHYSICAL_ELIGIBLE_SUPPORT_NOT_MINERALOGY=63620
NATURAL_T0_GEOLOGY_ASSIGNED_CELLS=0
ACTUAL_HISTORICAL_MATERIAL_EVENT_COUNT=0
ACTUAL_T0_MINERAL_PHASE_FIELDS=null
ACTUAL_T0_RESOURCE_ORE_DEPOSITS=null
ACTUAL_T0_DEEP_ACCESSIBILITY=null
G2_G3_MECHANICAL_SOLVE_AUTHORIZED=false
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
D_024=ACTIVE
physical_T1=null
```

## Future work — computation-efficient history-first geology

The next scientific task should NOT precompute 3D mineralogy for all 64,800 cells. Instead implement **read-only, sparse source-backed coarse property extraction**, selecting just a few original source grid cells and authentic plate IDs from SHA-pinned field and plate-partition NPZ files and determining which property represents:
- an actual native source parameter, e.g. `crustal_thickness_m`;
- a thermophysical *reference-model* density, NOT measured local rock density;
- a currently absent natural composition or mineral;
- an unknown historical state, since physical T0→T1 is still blocked.

Also reconstruct the exact original B6N8N membership as a **separate integrity preflight** only when needed for its source-eligible thermal adapter. The future query adapter should bind to real `CheckpointEnvelope`/`EventRecord`/`RefinementReconstructionRecipe` only after physically qualified history exists. Maintain provenance, parent-child conservation of **extensive** quantities if later known, uncertainty and replay-stable identity; defer expensive local phase equilibrium and ore models until a researcher requests them and their scientific applicability is qualified.

See design: `docs/arcana/R6_GEOLOGICAL_COARSE_STATE_ON_DEMAND_REFINEMENT_SCIENCE_20261121.md`.

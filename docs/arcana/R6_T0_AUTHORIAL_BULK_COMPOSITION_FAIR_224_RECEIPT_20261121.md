# ARCANA R6 — FAIR 224/224 explicit T0 bulk-rock composition hypothesis provider

**Date:** 2026-11-21.
**Exact operator-tested development HEAD:** `e48f4c30d0a5550875472f8a9263c7c6cb5a0317`.
**Decision:** `T0_AUTHORIAL_BULK_OXIDE_HYPOTHESIS_PROVIDER_FAIR_224_PASS__UNSELECTED_NO_PHYSICAL_GEOLOGY`.

## 1. FAIR operator terminal receipt

```text
HEAD is now at e48f4c30 docs(r6): seal source-bound authorial bulk rock research candidate and pending FAIR 224 gate
........................ [100%]
24 passed in 0.28s
TARGET_EXIT_CODE=0
...
224 passed in 1.23s
FULL_REGRESSION_EXIT_CODE=0
{"status": "EMPTY_AUTHORIAL_SCENARIO_TEMPLATE", "T0_compositions": 0, "physical_T1": null}
TEMPLATE_EXIT_CODE=0
{"decision": "AUTHORIAL_BULK_OXIDE_HYPOTHESES_ONLY_NO_CANONICAL_GEOLOGY",
 "candidate_recipes": 0, "candidate_mixtures": 0,
 "hypothetical_native_assignments": 0,
 "physical_T0_assignments": 0, "physical_T1": null}
COMPOSITION_COMPILE_EXIT_CODE=0
PASS: contratto T0 valido, nessuna geologia inventata
```

**Evidence class:** exact FAIR operator-pasted stdout. The authoring/GitHub environment has not obtained raw FAIR logs or locally rerun FAIR. The 224 defined G2/G3+RSF+T0 geology+geochemistry+new-authorial-provider tests are **not** the entire repository's global test suite.

FAIR recorded paths:
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_T0_BULK_COMPOSITION_TARGET_24.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_T0_BULK_COMPOSITION_FULL_224.log`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_T0_BULK_AUTHORIAL_TEMPLATE_NEW_01.json`
- `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_T0_BULK_AUTHORIAL_EMPTY_REPORT_NEW_01/REPORT.json` plus `MANIFEST.json`.

## 2. Scientific and software acceptance boundary

The validated module `experiments/t0_authorial_composition_v1/provider.py` provides (a) exact SHA-pin of `B6N8N` 180×360 spatial support index, (b) explicit authored oxide amounts and value intervals in wt.%, (c) conserved mass-fraction mixing, (d) conditional native-cell placement with strict original `face_row,face_col,face_plate_id` and actual field package SHA, and (e) immutable noncanonical output.

Crucially, the **actual FAIR runtime exercise consisted only of an EMPTY template and EMPTY compilation** plus synthetic unit tests. It has **NOT** demonstrated real 63,620-cell admitted member-file export, actual original field/plate NPZ placement, a user-selected authorial lithology or physical T0 rock. Source format in the repository does use `face_row,face_col,face_plate_id`, but the true external NPZ and membership ledger must be jointly opened and verified on FAIR before any physical regional assignment even as a candidate. No false full spatial source execution is claimed.

Original support: **64,800 native cells** with **63,620 thermophysical eligible**, *not* 63,620 geochemically mapped cells; exactly **0 selected compositions, 0 hypotheses placed, 0 ratified physical cells** in FAIR output. Previous 6 Earth chemical reference records are a separate source-bound laboratory library; no terrestrial chemistry was assigned to ARCANA.

The output explicitly preserves:
```text
R6_T0_BULK_PROVIDER_TARGETED_FAIR=24_OF_24_PASS
R6_T0_BULK_PROVIDER_EXTENDED_FAIR=224_OF_224_PASS
R6_T0_AUTHORIAL_TEMPLATE_GENERATED=true
R6_T0_EMPTY_NONCANONICAL_REPORT_GENERATED=true
R6_B6N8N_NATIVE_CELLS=64800
R6_B6N8N_THERMOPHYSICAL_ELIGIBLE_CELLS=63620
EARTH_REFERENCE_CHEMISTRY_RECORDS=6
AUTHOR_SELECTED_T0_COMPOSITION_RECIPES=0
AUTHOR_SELECTED_T0_COMPOSITION_MIXTURES=0
AUTHOR_SELECTED_T0_COMPOSITION_PLACEMENTS=0
RATIFIED_T0_COMPOSITION_CELLS=0
MINERAL_PHASE_FIELD_T0=null
FAULT_GOUGE_MINERALOGY_AND_HYDRATION=null
ROCK_PT_FO2_FLUID_PHASE_CLOSURE=null
G3_MANTLE_AND_CUT_TRACTIONS=null
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

## 3. Integration decision and next scientific milestone

The tested software commit qualifies for **engineering-only, non-forced fast-forward** into the R6 integration branch provided that integration head is the checked ancestor `083a6a685c177c43ae1e3c321084e7d8b3f9258d`. This receipt does not modify Python source; no global geology, Earth lab friction or realistic mineral reservoir has been authorized.

**Next:** provenance-constrained **actual native spatial identity preflight**: on FAIR, read canonical original `R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz` with SHA `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e` and original plate vector `R6_T0_VECTOR_PLATE_PARTITION.npz` SHA `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`. Reconstruct the *complete* admitted support membership using exact B6N8N physical source predicates; compare source canonical membership SHA `f61f4a89bacdf458636720ed4df67bd97cc731159bb588f6836e065241e1e499`, 63,620 ids and the excluded class SHA; select neither a mineral nor an ocean/continental facies by guess. Only **after** this native source gate, define a minimal author-selected regional bulk-rock scenario with stated oxide/volatile uncertainty and genuine source provenance for candidate research, then select thermodynamic phase equilibrium and compare G2/G3 physical material applicability. No physical T0/T1 production authorization follows merely from success.

See governing contract `docs/arcana/R6_T0_EXPLICIT_BULK_ROCK_COMPOSITION_HYPOTHESIS_PROVIDER_20261121.md`.

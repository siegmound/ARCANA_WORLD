# ARCANA R6 — Single original-T0 G2/G3 physical-support packet

**Date:** 2026-11-22  
**Status:** `DEVELOPMENT_IMPLEMENTED__FAIR_ORIGINAL_SOURCE_PENDING`  
**Branch:** `r6/g2g3-source-physical-packet-20261122`  
**Base integration HEAD:** `c681f57232d159761d36b0eaf0d6bffd11c18c69`  
**Decision:** source-authenticated original T0 model support is reusable for a single material/force/fault scenario, but **not a physical solver authorization**.

## Why this is substantive and what it is not

The 100-year and 1000-year thermal-column experiments are qualified as **synthetic 1D numerical validation**, not geological time-forward ARCANA T0. A larger synthetic time interval does not close T0 rock/mineral phase, water, pore pressure, mantle forcing or fault state.

The original G2/G3 internal core+exterior operators, 81/289-node original regions, 8 core plus 120/504 exterior triangles and 32/64 source exterior cut edges already exist; the missing unit is one **complete physical support handoff** that can be populated with actual sourced/authorial laws. We implement one compiler that reuses the existing upstream SHA-authenticated FEG/PRE and four provider manifests and emits:

1. `SOURCE_INDEX.json`: exact original parent-node order, all **128/512 source original facet IDs and ownership**, 32/64 external edge IDs and owner plate/side metadata, 51-field PRE record SHA per original node, and **16 source original T0 model thermal coefficients/geometry/density fields per node**. The thermal profiles are `SOURCE_ORIGINAL_AUTHORED_PRE_MODEL`, not observed mineralogy or a physically ratified historical T0 temperature. The 1000-year synthetic pilot is not used as input.
2. `UNSELECTED_PHYSICAL_PROPOSAL.json`: every actual original parent, cut edge and basal facet has an explicit **null** slot for material/phase, fluid/effective pressure, constitutive applicability, cut traction N/m and basal shear+normal pressure Pa. Full GPE/vertical support, mechanical LAB/independent mantle flow, sided fault/34587 junction law and versioned solver/rank/restart are explicitly `null`. The eight unresolved source matrix groups are carried forward intact. Nothing is silently set to 0 or 'dry'.
3. `MANIFEST.json`: SHA256 of both generated files, exact verified original FEG/PRE hashes, and immutable no-T1/no-solver/no-HistoryStore markers.

The experiment source matrix is pinned to Git blob `b4f6bef26302de4ab780674b58fa4e59d4cac0d6` (`R6_G2_G3_INTEGRATED_PHYSICAL_PROVIDER_MATRIX_20261121.json`). The original source manifests and original regional FEG/PRE are validated through existing `read_pinned`, `source_core_geometry` and the source chain; no fabricated numeric load/lithology values are accepted.

The **8×8** scope is the first input packet (81 nodes, 128 basal facets, 32 cut edges, source plates 5/8); **16×16** preserves original 34587 triple node and serves domain sensitivity (289 nodes, 512 facets, 64 cut edges, source plates 5/8/11). It does not establish numerical grid convergence.

## Key safeguards

- No original FAIR evidence, published 100/1000-year thermal reports, base model, PRE/FEG, source manifests or canon files are edited.
- Source groups remain `SOURCE_AUTHORITY_GAP`. An unselected template is not physically populated, however complete its geometric coverage.
- Every `null` slot remains null: `pore_pressure=0`, `basal_traction=0`, `chemistry=crust code`, and `fault slip from shared EN nodes` are prohibited defaults.
- The source FEG 2D sheet is not an extruded 3D fault solid. The T0 thermal reference layer base is not automatically mechanical LAB.
- The output is **write-once, outside the repository**, SHA-linked. An ambiguous set of genuinely distinct FAIR source provider chains refuses execution rather than choosing a newest timestamp.
- The 8×8 packet and 16×16 packet must use the exact same four source provider manifests; there is no automatic physical state transfer to T1.

## Validation plan (not yet an FAIR PASS)

Locally exercised: 36 portable checks PASS, with two source-matrix pin tests pending their native repo environment. The **planned** new targeted count is 38; the prior selected R6 suite was 368; new selected target is **406 total**, including the 38 (not 368 + 406).

On FAIR, from a detached checkout at the new exact branch SHA under conda `arcana-r6-linux`:

```bash
bash scripts/r6_g2g3_physical_source_packet_fair_gate.sh
```

The fail-closed runner first requires 38 targeted and 406 selected regression cases, then executes a **real, independently SHA-validated source readback** at 8×8 and 16×16 to fresh non-overwriting external evidence folders under `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6`. Discovery searches only certified four-provider chains; if it reports `PHYSICAL_PACKET_SOURCE_CHAIN_MISSING_OR_AMBIGUOUS`, the operator may specify all four exact provider evidence directories in environment variables: `R6_MULTI_DIR`, `R6_INTERFACE_DIR`, `R6_NODAL_DIR`, `R6_FORCE_DIR`. No arbitrary path selection is accepted.

**FAIR 38/406 and real-source packet generation are currently PENDING.** Portable fixture tests use synthetic node IDs for negative/positive correctness only; they do not constitute original-source validation. Never fast-forward the R6 integration branch before FAIR validation and exact code SHA comparison.

## Physics milestone immediately after source packet

The next *scientific* step is not another model-age extension or acceptance gate: submit one **source-complete, physically selected** 8×8 G2/G3/FAULT material-force scenario, retaining the source IDs and supported pressure/temperature/rate domains. Choose original phase and hydrated/fugacity state **authorially with explicit support**, derive independent mantle boundary conditions, all cut and all basal normal/tangential loads, unique GPE owner, and a versioned sided fault law (or explicitly justified transmission model). Then verify equivalent support at 16×16 and only consider a bounded noncanonical physical EXPLORE with independent scientific validation. Never automatically produce historical T1.

```text
R6_G2G3_SOURCE_PACKET_IMPLEMENTED = TRUE
R6_G2G3_SOURCE_PACKET_FAIR = PENDING
G2_ACTUAL_ROCK_PHASE_ASSIGNED = FALSE
G2_FLUID_AND_CONSTITUTIVE_COVERAGE = UNKNOWN
G3_ACTUAL_FULL_BASAL_AND_CUT_FORCE = UNKNOWN
G3_MANTLE_GPE_FAULT_LAW = UNKNOWN
MECHANICAL_SOLVE_AUTHORIZED = FALSE
D_024 = ACTIVE
physical_T1 = null
WORLD_HISTORY_PRODUCTION_AUTHORIZED = FALSE
```


## FAIR NEW01 source-readback incident and NEW02 corrective scope (2026-11-22)

**The first FAIR test suite PASS was not a successful source packet.** Operator terminal at exact SHA `ef285fa05eb278143a2700f73aacf3abcdfbb571`:

```text
PHYSICAL_SOURCE_PACKET_SHA=ef285fa05eb278143a2700f73aacf3abcdfbb571
38 passed in 0.13s
406 passed in 3.26s
--- Read ORIGINAL FAIR FEG/PRE + four source manifest chain (8x8) ---
PhysicalSourcePacketError: PHYSICAL_PACKET_ORIGINAL_TRIPLE_NODE_DRIFT
```

The error was raised inside `create_packet` while attempting the source-authenticated 8×8 readback, before source index/manifest publication; the 16×16 readback was not reached. Preserve `TARGET_38_NEW01` and `SELECTED_406_NEW01` logs as first-attempt evidence, **not** as evidence of a published source packet.

### Root cause and scientifically correct interpretation

The original guard `(34587 in parent_ids) == (extent == 16)` incorrectly equated **global parent-node membership in a footprint** with **a locally incident triple-plate junction**. The FAIL at 8×8 implies the original selected 8×8 parent-node list includes `34587`; that does **not** imply three plates in that 8×8 source region. The existing SHA-chained interface provider, `g3_multiscale_interface.py`, instead computes `actual_3plus_plate_junctions` from source incident plate ownership. The source-inventory decision maintains *zero* original 3+-plate junctions for 8×8 and one original `34587` junction with plates `[5,8,11]` for 16×16. The new compiler requires that provider's verified incidence records and its matching boolean; it no longer infers a junction from a node ID alone.

**No scientific state or physical rock/force/fault authority changed.** Genuine original source index retains parent ID `34587` wherever present and reports `source_parent_34587_present_in_footprint` separately from `source_actual_3plus_plate_junctions`.

### Second preventative correction before NEW02

The old runner's final cross-extent check compared the *entire* `source_hashes` dictionaries as equal, including two hashes which **must be different** between 8×8 and 16×16: `original_FEG_sha256` and `original_PRE_sha256`. They are different files with different node/element support. The new `verify_cross_extent_provider_chain` function requires identity of the **four common SHA-verified upstream provider manifests**, while demanding **distinct valid source FEG and PRE hashes** and the correct regional junction identities. It rejects swapped/missing providers and pseudo-equal regional file hashes; never reuses an 8×8 FEG/PRE as the 16×16 source.

New deterministic test cases cover 8×8 with parent 34587 but **no** actual triple, missing/spoofed/incorrect 3-plate incidence, and cross-extent source hash rules. The original science source-matrix pin and no-T1 tests are unchanged.

**NEW02 planned gate**: **42 targeted tests**, **410 selected** (the 42 are included in 410). Locally, **40/40 portable tests PASS**; two repository-native matrix-pin tests cannot execute in the isolated local fixture environment, although both passed in the original FAIR NEW01 38/38. The updated bash runner syntax check passed. The original 100/1000-year numerical pilots and old evidence are untouched.

Only a **fresh FAIR checkout of the exact new patch SHA** and successful 42/410 + BOTH authentic source readbacks under `NEW02` can qualify this engineering source packet. It still will **not** authorize mechanical T1, geological mineral/ore/Deep assignments, or canonical history.

```text
SOURCE_PACKET_NEW01_TARGETED=38/38_FAIR_OPERATOR_PASS
SOURCE_PACKET_NEW01_SELECTED=406/406_FAIR_OPERATOR_PASS
SOURCE_PACKET_NEW01_SOURCE_READBACK=FAIL_ORIGINAL_TRIPLE_NODE_GUARD
SOURCE_PACKET_NEW02_TARGETED=FAIR_PENDING_EXPECTED_42
SOURCE_PACKET_NEW02_SELECTED=FAIR_PENDING_EXPECTED_410
SOURCE_PACKET_NEW02_SOURCE_8X8=FAIR_PENDING
SOURCE_PACKET_NEW02_SOURCE_16X16=FAIR_PENDING
PHYSICAL_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

Note for downstream work: the older `g2_g3_source_coupled_runner.source_inputs` also contains a 34587-by-extent guard. This packet calls `source_core_geometry`, not that full candidate runner; the older candidate path must have its own independently scoped source-incidence correction before an actual coupled source-run, rather than silently inheriting this package's qualification.

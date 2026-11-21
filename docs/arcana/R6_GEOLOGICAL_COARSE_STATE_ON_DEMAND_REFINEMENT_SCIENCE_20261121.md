# ARCANA R6 — Geological Coarse State & On-Demand Refinement (sparse scientific contract)

**Date:** 2026-11-21. **Software parent:** R6 main `3805648c36aa70e7ab709e593c33abaaedfb616e` (FAIR 224/224 PASS, explicit unselected bulk-oxide provider).
**Development branch:** `r6/geological-coarse-state-on-demand-refinement-20261121`.
**Decision:** `SPARSE_COARSE_GEOLOGY_AND_DETERMINISTIC_REQUEST_LOCAL_REFINEMENT_IMPLEMENTED__NO_REAL_GEOLOGICAL_HISTORY_OR_MATERIAL_CLASS_ASSIGNED`.

## 1. Scientific change of priority — avoid global mineral-detail computation

The ARCANA WorldSim mission is to generate an internally coherent, queryable history from ~210 Ma to 0 ka, with **future local enhancement** for geology, water, deep structure, resources, life and civilizations. A precomputed 3D modal mineralogy for every material column, every native 1° cell and every epoch would be a poor research strategy before physical T0 mechanics and material transport close.

Prior R6 progress has:
- A canonical 180 × 360 native 1° grid = 64,800 parent cells, source identity `R6_GLOBAL_GEOGRAPHY_1DEG_V1`.
- A thermophysical-role eligible support of 63,620 cells, NOT a natural mineralogy map. The original B6N8N source index Git blob `e06770577ebaf549aa113a4e72ec9f6095a29c2d` is pinned; the remaining 1,180 are outside that **particular** thermal provider eligibility, not outside planetary geology.
- R6 hierarchical child cell geometry already present in `src/arcana_worldsim/r6/hierarchical_refinement.py`, with canonical parent IDs, deterministic child IDs and request scope, **no** physical interpolation.
- `src/arcana_worldsim/r6/refinement.py` stores branch-bound reconstruction recipes tied to checkpoints, parent state IDs, boundary conditions, model configuration and seed lineage; the current geological adapter does not claim its conditions are met.
- `src/arcana_worldsim/r6/query.py` supports historical state / provenance read queries. The new sparse geological research records are **not** inserted into `HistoryStore`; they are research-only until a physical history exists.

**Design decision:** retain compact coarse *material-state descriptors* and a sparse event/provenance trail, refine spatially/temporally and petrologically **only on demand**, conserving physically validated quantities if available. We do NOT replace the actual historical solver with a retrospectively fabricated plausible history.

## 2. Scientific model: density and several observables, not a lookup to rock names

For future parent cells, the minimum possible coarse descriptor is a generic family (or `UNRESOLVED`), an interval of **effective cell bulk density** (not a mineral density), crustal thickness interval and temperature interval, all with units, uncertainty and time support. The first contract provides an explicit vocabulary for possible generic research categories: silicic/felsic crust, mafic crust, ultramafic, metamorphic, clastic or carbonate sediments and other unknown bulk materials. **None is automatically assigned** based on R6 crust-domain codes, density or Earth analogues.

The original bulk-oxide reference compiler remains available when an investigator asks a detailed petrological question; it is not run on all parent cells and all times.

The optional *density screening* compares a user-provided sample interval with separately declared candidate density intervals. This is mathematically only **interval intersection**. It returns `INTERVAL_OVERLAP_ONLY_NOT_IDENTIFICATION`, `posterior_probability=null`, `geological_presence_confirmed=false`. Two mineral/rock types may share density; a positive interval overlap does not prove presence, while non-overlap under an uncalibrated narrow prior does not prove natural absence. No universal Earth default density ranges are populated. Future discriminants could include pressure-/temperature-corrected bulk density, seismic velocities, susceptibility, geochemistry, porosity and water state when sources justify them.

## 3. Implementation

- `src/arcana_worldsim/r6/geological_coarse_state.py` — source-index-bound **empty or sparse**, **noncanonical** coarse catalog, optional hypothesis event references, deterministic request-scoped child geometry, conditional density screening, write-once SHA-linked evidence report. This module imports the original canonical parent-grid validator and original R6 child-subdivision function: it creates no second geography system.
- `tests/test_r6_geological_coarse_on_demand.py` — 30 expected tests: canonical index integrity, sparse temporal/event validation, deterministic replay despite input reordering, no values inherited by children, no physical history or mass conservation falsely claimed, density overlap only, invalid source promotion, scope errors, space/time query budgets, write-once output SHA.
- `experiments/geological_coarse_v1/EMPTY_SOURCE_ANCHORED_CATALOG.json` — exactly **zero** events, parent snapshots, rock families, density assumptions, authorship selections or canonical T0 authority.
- `experiments/geological_coarse_v1/DEMO_GEOMETRY_ONLY_QUERY.json` — one arbitrary native parent cell, synthetic geometry-only research question at 210 Ma, 2×2 subdivision, no density sample or candidate: for FAIR transport validation **only**, not a selected geological region.

### Sparse catalog contract

- `events` and `snapshots` are **optional arrays** (max 512 each), not a 64,800-row world tensor. Original parent IDs validated with the governed 180×360 grid.
- `at_ma` is a declared research age between 210 and 0 Ma, **not** a confirmed output of the T0→T1 solver.
- Event types identify possible geological processes: deformation, magmatism, erosion, sedimentation, alteration, metamorphism, fluid transport, recycling, candidate enrichment. Each event remains `AUTHORIAL_HYPOTHESIS_NOT_PHYSICAL_EVENT`; historical physics and timestamps are not authorized merely because a record has an event name.
- Snapshot coarse values are **nullable** and, when present, bounded by explicitly supplied intervals with units. Hypothesis values must be tagged `BOUNDED_AUTHORIAL_HYPOTHESIS`; unresolved values cannot masquerade as zero.
- Parent source-checkpoint linkage is **forced null** at this stage: without a source-validated physical historical checkpoint no historical state or checkpoint closure may be claimed.
- A snapshot may reference only existing events with matching cell support whose age is between its own age and the initial 210 Ma epoch (the chronology uses Ma before present).
- Snapshot/event results carry no physical fault, rock, Deep or resource authority. In particular `physical_T1=null`, `world_history_production_authorized=false`.

### On-demand branch, not eager 3D field production

Request needs a sorted/validated parent-cell set (max 8), an age, a research question ID and refinement factor 2–8 with a **hard cap of 256 child geometries**. The request ID binds the original sparse catalog digest and all research inputs; repeated queries of the same catalog with reordered parents give the same identity and geometry.

The output:
1. Retrieves the coarse parent snapshot/event references **only if provided**, else `null`;
2. Calls **existing** `hierarchical_refinement.subdivide_parent_cells` for child **bounds and IDs only**;
3. Explicitly sets every child's density, material family, mineral phases, water, ore likelihood, Deep accessibility and mass to **null**;
4. Exposes a constraint requiring a future scientifically selected provider to preserve authentic parent *extensive* quantities. No parent rock mass is currently source-known, and so `parent_mass_kg=null`, `conservation_checked=false`. It would be physically invalid to divide coarse density or mass equally among equal-angle child regions.
5. Provides optional screening against declared noncalibrated candidate density intervals without claiming posterior probabilities or deposits;
6. Writes new immutable `REPORT.json` and hash manifest to a never-before-existing directory. No write to R6 `HistoryStore`, canonical world, FEG/PRE/NPZ or T1.

### Continuation compatibility

When real T0 inputs/physical dynamics are qualified, the catalog may become an index to **actual** R6 `DomainStateEnvelope`, `EventRecord`, `CheckpointEnvelope` and `RefinementReconstructionRecipe`, rather than a parallel event truth source. A future geological local provider must be attached through the existing R6 refinement execution and its checkpoint, boundary/seed lineage, conservation checks and source validity. A query result may be stored as a separate, provenance-verified child branch, never as a silent mutation of the already established parent history.

Source material states (density vs measured rock chemistry), process histories and query results have different evidence status. The system must never elevate a *research hypothesis* to a world-canon observation.

## 4. FAIR verification gate

**DEV, FAIR PENDING.** The last completed main R6 scientific baseline is **224/224 FAIR PASS** on `e48f4c30d0a5550875472f8a9263c7c6cb5a0317`, integrated by documentation-only commit `3805648c36aa70e7ab709e593c33abaaedfb616e`.

For this branch:
1. Run **30 expected** targeted tests; then all previous 224 defined G2/G3+RSF+source geology+geochemical+authorial geology tests plus the new test = **254 expected**.
2. Produce a new empty catalog using `python -m arcana_worldsim.r6.geological_coarse_state --repo-root . --empty-template-out "$BASE/R6_GEO_COARSE_EMPTY_NEW_01.json"`.
3. Run the empty compile with `--catalog` and `--output`; expect 64,800 original cells and 63,620 thermal-eligible support, **0** coarse snapshots, **0** physical geological assignments, `physical_T1=null`.
4. Run the static geometry-only demo query against the original empty catalog with `--query experiments/geological_coarse_v1/DEMO_GEOMETRY_ONLY_QUERY.json`; expect **four** child geometries, no inherited rock property, and no physical history. This is **not** a geological T0 simulation.

The FAIR source binary grid/plate and **63,620-cell original admitted membership** preflight remains an independent future task for any actual spatial physics and authorial rock placement. It is **not** necessary to precompute a complete detailed mineral library merely to establish source parent cell IDs and child geometry.

## 5. Scientific next action after FAIR

The next useful step is **sparse physically sourced state adapter**, not all-world mineralization: source-bind only a few real T0 parent cell thermophysical descriptors from original NPZ with exact SHA and plate IDs, as uncertainty-bearing coarse attributes. Then attach a read-only checkpoint/event authority when actual validated physical history exists. An on-demand sample-density query should return candidate material families and explicit missing discriminants, not a deterministic ore map. Target a single test region only after the author selects a geological question.

The separate, still-open planetary mechanical conditions — G2 exact rock P/T/rate law, physically independent fault gouge and normal stress, G3 mantle/basal and outer-cut loads/GPE — must be closed before physical T0→T1, production history, real evolving mineral resources or Deep history.

```text
R6_GLOBAL_PARENT_CELL_IDENTITIES=64800
R6_THERMAL_ELIGIBLE_SUPPORT_ONLY=63620
EARTH_GEOCHEM_REFERENCE_RECORDS=6
R6_COARSE_SPARSE_CATALOG=IMPLEMENTED_NONCANONICAL
R6_ON_DEMAND_CHILD_GEOMETRY=REUSES_HIERARCHICAL_REFINEMENT
R6_COARSE_PHYSICAL_STATE_COUNT=0
R6_COARSE_REAL_PROCESSED_EVENTS=0
R6_REFINEMENT_PHYSICAL_CHILD_MATERIALS=0
R6_DEEP_RESOURCE_OR_MINERAL_PROBABILITY=UNASSIGNED
R6_NEXT_TARGETED_TESTS_EXPECTED=30
R6_NEXT_EXTENDED_TESTS_EXPECTED=254
R6_FAIR_TESTS_FOR_NEW_BRANCH=PENDING
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

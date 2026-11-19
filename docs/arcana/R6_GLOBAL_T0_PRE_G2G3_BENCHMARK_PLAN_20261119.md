# ARCANA R6 — Global T0 benchmark before G2/G3 (100 and 1000 model years)

**Date:** 2026-11-19. **Decision:** move a bounded **global T0 kinematic+data-throughput baseline** ahead of physical G2/G3 integration. **Status:** plan and contract published; **no new global simulation executed** and **no production/T1 approval**. D-024 continues to apply. Architecture G3 A remains author-ratified for future EXPLORE and unchanged.

## Why this step is valuable

The author explicitly proposed assessing the existing *entire planetary layer* for 100 or 1000 years **before** adding G2/G3, to measure CPU/memory/runtime and numerical deviations. This is sensible and complements, rather than replaces, eventual deforming physics.

Current source-bound T0 available for this scope:
- `R6_T0_CANONICAL_PLATE_KINEMATICS.json`: twelve authorial Euler vectors at 210 Ma, constant for the first model segment only under `R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json`.
- `R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json` plus authenticated external NPZ: global 64,800 parent faces, 64,442 unique FEG vertices, 128,880 triangles, per-triangle plate IDs. Adapter `src/arcana_worldsim/r6/shellset_mesh/adapter.py` validates provenance.
- `R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.{json,dat}`: **passive** material/thermal/geological T0 fields at the 64,442 numerical nodes, with authoritative hash, but **not** a first T1 thermal/mechanical update.
- `src/arcana_worldsim/r6/finite_rotation.py`: exact constant-Euler quaternion-based point rotation; does **not** resolve contacts or issue canonical whole-world states.
- B6I/B6J existing first-segment bound is approximately 27,123.405 model years; a benchmark up to 1,000 years is before the first modeled rift event but must explicitly check the frozen source-based bound and stop if the source changes.

What is **not** a precedent for this same workload:
1. `docs/arcana/R6_RUNTIME_R2_1000Y_FAIR_20261030.md` already reports a **1000-year 9-cell** compact integrated microdomain history (110.023109 s launch→exit, including persistence and reconstructions, rather than pure physics/kernel time). It is not a 64,442-node planetary benchmark.
2. `docs/arcana/R6_RUNTIME_R2_10K_FAIR_20261030.md` reports **10,000 years on 9 synthetic cells**; not planetary.
3. `docs/arcana/B2_WORLD_HISTORY_64442_NODE_SCALE_QUALIFICATION.md` qualified storage on 64,442 synthetic nodes, not 100/1000 years of actual T0 physical integration.
4. `docs/arcana/R6_KINEMATIC_REGIONAL_T1_EXPLORE_FAIR_20261118.md` moved 9 nodes of plate5 for 10 model years, preserving PRE fields passively.

These results justify new performance measurement; **do not extrapolate the 9-cell timings linearly to the globe** because the cost of boundaries, IO, full-source access, ownership, and candidate future physics may be different.

## Exact scope of the proposed new benchmark

**Global T0 source-bound `KINEMATIC_AND_PASSIVE_PRE_ONLY`, not a deforming mechanical T1.**

### Phase 0: source and load baseline
- In a new isolated, clean FAIR verification checkout, authenticate mesh, Euler, PRE T0, and first-segment bound with source SHA identity and units. No changes to original FAIR evidence.
- Record CPU/wall time for input reading, mesh construction, PRE mapping, active resident set size and maximum RSS, and disk needs.
- Preserve per-triangle plate ownership, source parent cell IDs and per-node PRE lineage. No invented plate ownership at ambiguous shared boundary nodes.
- Do **not** run the global ShellSet solver or assert tectonic stresses, thickness changes, thermal diffusion, erosion, subduction, climate or mineral flow.

### Phase 1: 100-year global kinematics
- Apply the source Euler rotation to **each plate's own material point representation**, preserving parent-node/triangle identity. Boundary nodes may be referenced by multiple plates: use transient per-plate views strictly for **kinematic diagnostic**, **never** duplicate FEG DOFs in the physical solver.
- Check direct Euler rotation by 100 years against 100 successive 1-year finite rotations and a 50+50 restart split. Input PRE remains immutable/passive.
- Check coordinate-unit norms; no NaN/Inf; triangle orientations and signed spherical area relative to T0 **within each rigid plate**; analytic finite-rotation semigroup and reversibility; checkpoint/readback identity; plate inventories.
- Report source plate-boundary separations/overlaps as **unresolved kinematic interfaces**, not automatically “numerical drift” or geological creation of voids.
- Time input load, each advance p50/p95/max, cumulative CPU and wall, peak RSS and checkpoint persistence (size/write/read/hash). Do not materialize a full 64k-node history every year: bounded checkpoints only.

### Phase 2: 1000-year global kinematics, conditional on Phase 1
- Run a new fresh trajectory after Phase1 integrity and resource review; keep 100-year outcome independently retained.
- Compare 1-year ×1000 composed rotations to direct 1000-year rotation and one or more checkpoint split/restart representations.
- Record metrics at model years `0,1,10,100,500,1000` (no periodic giant snapshots unless separately justified), including geometric drift, geometry quality per plate, unresolved interface residual and source material/passive PRE identity.
- Cost analysis: source load vs step CPU vs serialization, disk throughput, observed RSS; compare 100Y and 1000Y hot rates and growth. Avoid invented memory/CPU quotas and timeouts; obey actual FAIR allocation and stop on real resource limits.
- Preserve a source-hashed result manifest in a **new exclusive external FAIR evidence directory**, with diagnostic only provenance; never mutate canonical HistoryStore.

## Fail-closed and numerical interpretation

A global shared-node mesh **cannot** be advected as one rigid object under 12 different Euler vectors. In every plate-boundary corner where two incident plates differ, the per-plate positions separate or overlap; that is a diagnostic of omitted G2/G3 accommodation and **not** an error to “fix” by averaging Euler or assigning a single arbitrary plate ID. A transient per-plate *view* must not be misrepresented as a physically closed continuous global deformed mesh.

Measure separately:
- **Numerical drift:** composition vs analytical direct rotation, radial norm, area of triangles moved within a single plate, restart replay inconsistency, nonfinite or inverted triangles.
- **Physical closure deficit:** boundary gaps/overlaps and missing traction/strain fields. No solver means no physically meaningful deformation, loads, newly created crust, resources, tectonic elevation, hydrology or deep material redistribution.
- **Runtime evidence:** actual observed cost for implemented *kinematic/passive* layers. This is a lower-level performance baseline, not a forecast for full G2/G3, thermal/OrbData, or later WorldSim multi-physics history.

Do not call passive PRE snapshots for years 100/1000 **evolved thermodynamics**. Carry T0 property values as tagged reference state only, without asserting validity at later ages. First-segment Euler policy supports a bounded kinematic experiment, not a new canonical history.

## Test ordering and deliverables

1. Implement one global baseline runner with explicit `--years 100|1000`, source pin checks, output directory exclusive, measured phases, bounded checkpoints and **unit tests for multi-plate shared-node semantics**. No run in implementation/publishing step.
2. FAIR execution **100 years first**, inspect actual output/peak RSS/source drift and source boundary bookkeeping before attempting 1000.
3. If 100-year metrics/identity/area/restart checks pass and resources are acceptable, run **1000 years**, capture comparative profile and method-level discrepancies.
4. Record a decision `GLOBAL_T0_KINEMATIC_BASELINE_PASS_OR_BLOCKED`, then return to the previously ratified G3 A and close G2/G3 physically.

**No new G2/G3 implementation is required to perform the kinematic/performance baseline; conversely this baseline does not waive G2/G3 for a real deforming T1.**

```text
GLOBAL_100Y_PLAN=READY_FOR_IMPLEMENTATION
GLOBAL_1000Y_PLAN=CONDITIONAL_ON_100Y
GLOBAL_100Y_EXECUTION=NOT_STARTED
GLOBAL_1000Y_EXECUTION=NOT_STARTED
PRE_T0_FIELD_EVOLUTION=NOT_IMPLEMENTED
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_DEFORMING_T1=BLOCKED
G3_ARCHITECTURE_A=RATIFIED_EXPLORE_ONLY
```

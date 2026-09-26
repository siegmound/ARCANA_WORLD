# R6 Physical World Evolution — Adjudication

**Baseline:** `main` at `592b1651b405363373590092e133bd25569d99a5` (origin/main matched at inspection).
**Decision:** `EXTERNAL_SCIENTIFIC_RESEARCH_REQUIRED`
**Verdict:** `PHYSICAL_LAW_AUTHORITY_BLOCKED__NO_CAUSALLY_BOUND_POST_210MA_GEODYNAMIC_LAW`

## Finding

R6 has a validated synthetic 210 Ma initial world and a validated latent geometry representation. Neither supplies post-t0 causal physics. Existing A1 and R1–R3 artifacts are useful reference evidence and downstream support machinery; they do not authorize R6 plate motion, breakup, collision, orogeny, topographic evolution, or a canonical future trajectory.

The candidate `HYBRID_PROCESS_CONSTRAINED_EVOLUTION` is a research hypothesis, not a selected or authorized law. Process simulation alone would require unbound constitutive laws and forcings. A precomputed boundary trajectory would be reproducible but no independent R6 trajectory authority exists, and adopting A1 would silently turn a reference Earth-like history into ARCANA's synthetic history. A hybrid could ultimately combine causal evolution and bounded validation, but only after its actual laws and constraints are researched and governed.

## Repository archaeology and reuse findings

- `src/arcana_worldsim/late_cenozoic/paleogeography.py` delegates to an A1-endpoint/event reconstruction. Its own semantic label is `DERIVED_ENDPOINT_CONSTRAINED_RECONSTRUCTION_NOT_INDEPENDENT_GEOLOGICAL_OBSERVATION`; its recent tectonic freeze is explicitly a short handoff convention, not a 210 Ma evolution law.
- `src/arcana_worldsim/post_cha1/paleogeographic_history.py` reconstructs land support from A1 endpoints and event timing. This is a rule-based support reconstruction, not a plate/mantle process solver.
- `src/arcana_worldsim/scientific_engines/r310_cha1_highres_bridge.py` requires `frozen_tectonics=True` for the short CHA-1 bridge. It evolves the event/ecological state, not tectonics.
- R3.11/R3.14/R3.18/R3.20 supply recovery, environmental-clock, exposure/transport, and hydrological-hazard capabilities. These consume/bridge physical or environmental boundary states; none is a post-210 Ma geodynamic law. R3.14 explicitly describes its adaptive clock as a scheduler, not new physics.
- R3.27/R3.28 provide human/population replay time/grid machinery, not geodynamic forcing or plate evolution.
- `R4_0_MULTI_ENGINE_ORCHESTRATOR_CONTRACT.md` makes ARCANA the canonical state owner and external engines bounded evidence providers; its registry does not register a physical-geography solver.
- `R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json` labels R6 t0 as a new synthetic design decision, A1 as reference/design evidence, plate motion as unknown, numeric bathymetry as unmaterialized, and the first causal physical consumer as not yet law-bound or executable. `R6_SIMULATION1_PHYSICAL_GEOGRAPHY_T0_BINDING` similarly preserves unknown kinematics and does not recover the lost Simulation-1 bootstrap.
- `src/arcana_worldsim/r6/initial_world/topography.py` and generator create initial synthetic relief/province patterns. This is t0 design geometry, not uplift/orogeny/erosion dynamics. The initial-world validation does not materialize a drainage network or erosion result.
- Latent geometry permits deterministic geometric refinement under its declared procedural support. It does not add higher-resolution tectonic/material observations or a motion law.
- Repository search found no governed FastScape, Badlands, GPlates, or other landscape/geodynamic engine suitability decision applicable to R6. No candidate is selected here.

### Historical mode classification

| Capability | Classification | R6 implication |
|---|---|---|
| A1 210→0 trajectory (`references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz`, SHA256 `9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f`) | `PRECOMPUTED_FRAME_SEQUENCE` / `REFERENCE_ONLY` | May support separately authorized diagnostics or broad constraints. Never assign `R6 state(t)=A1 state(t)` or interpolate it as R6 truth. |
| D3.2C/A1 event-driven paleogeographic support | `RULE_BASED_TRANSITION` | Deterministic endpoint/event support reconstruction only; not endogenous plate kinematics or lithosphere dynamics. |
| R3.10 tectonic raster over CHA-1 bridge | `STATIC_REFERENCE` / `DIAGNOSTIC_ONLY` | Frozen short-window boundary convention; no generalization to 210 Myr. |
| R3.11 onward and R3.14/18/20 | `DOWNSTREAM_BOUNDARY_CONSUMERS` | Reuse only as adapters/validation where field, time, and grid contracts match. |
| R6 initial-world generator | `STATIC_SYNTHETIC_INITIALIZATION` | Direct t0 state only; no temporal physical law. |
| Hybrid-1 early schematic | `REFERENCE_ONLY` | Not formal Simulation-1 authority and not a validated R6 solver. |

## What can be decided now

- **Time direction:** forward from the governed synthetic 210 Ma state only. A1/R1–R3 may be reference or separately authorized field-specific validation; no backcasting, copying, or generic categorical interpolation.
- **Plate semantics:** only t0 plate identity/coarse province support is present. Plate motion, spherical rotation/velocity, boundary evolution, oceanic/continental crust evolution, and event state are not yet frozen.
- **Breakup/collision/orogeny:** no initiation law, force/kinematic rules, seeded-event authority, or collision/uplift response is bound. No manual map editing or visual-choice event placement.
- **Topography/landscape:** t0 relief exists; post-t0 uplift/subsidence, volcanism, erosion, sedimentation, landscape relaxation, and their coupling remain unbound. A global coarse solver versus regional landscape solver cannot be selected without a causal driver contract and suitability evaluation.
- **Sea/land:** land elevation plus a governed sea-level datum/forcing can define a limited shoreline boundary, but t0 sea-level reference is authorial and ocean volume/eustatic history is unbound. Bathymetry is not required merely to evolve continental kinematics; it is required before bathymetry-dependent basin, shelf, ocean-circulation, or climate coupling.
- **Deep:** Deep's extant contracts concern energy/genetic/ecological state and historical biological replay. They do not establish Deep→mantle/tectonic causation. R6 geodynamic coupling is `UNKNOWN`; do not infer it. If selected by future authority, it requires a specific `R6_DEEP_GEODYNAMIC_COUPLING_CONTRACT` and any declared physical initializer.
- **Temporal policy:** the future solver should use process/event-bounded adaptive intervals and restartable checkpoints, but exact timestep/error/displacement bounds require the selected law and stability evidence. An adaptive clock alone is not physical authority.
- **Conservation:** future law must state spherical coverage/partition invariants, crust/area accounting, allowed transfers, and topology checks. Do not impose conservation on quantities legitimately changed by governed processes.
- **Ensembles:** uncertainty sources are known conceptually, but no distributions/member count are authorized. A canonical realization must be chosen by validity/stability/contract criteria and authorially fixed broad constraints, never aesthetics.

## Readiness

No first 210 Ma interval contract is emitted: required motion law, breakup/collision/event semantics, forcing, topographic response, and solver identity are not bound. This adjudication does not execute evolution, climate, hydrology, Deep, or provider acquisition; it does not alter t0, the global grid, current-state ledger, Authority Register, or execution indexes.

See the paired authority matrix, reuse map, and targeted external research questions. Full machine-readable governance is in `R6_PHYSICAL_WORLD_EVOLUTION_CONTRACT.json`.

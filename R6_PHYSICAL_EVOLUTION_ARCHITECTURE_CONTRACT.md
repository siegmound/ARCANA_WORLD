# R6 physical evolution architecture contract

**Decision:** `HYBRID_PROCESS_CONSTRAINED_EVOLUTION_ARCHITECTURE`\
**Verdict:** `HYBRID_LAYERED_ARCHITECTURE_SUPPORTED__CAUSAL_LAWS_STILL_REQUIRE_AUTHORITY`\
**Baseline:** `main` at `592b1651b405363373590092e133bd25569d99a5` (origin matched)

## Bound architecture

R6 uses `R6_HYBRID_PROCESS_CONSTRAINED_PHYSICAL_EVOLUTION`. ARCANA owns canonical state semantics, causal laws/events, forcing, uncertainty, seed lineage, provenance, validation, checkpointing and `WORLD_HISTORY`. A computational solver may resolve only the state ARCANA supplies; it is not an authority for physical laws or event choices.

The intended sequence is:

```text
canonical t0 → ARCANA causal transition → plate/event state
→ spherical geometry/topology resolution → tectonic vertical response
→ optional landscape response → validation/checkpoint → WORLD_HISTORY
```

The master plate representation is spherical vector/topological state. The 1°/180×360 grid is a derived global materialization, not master plate geometry. Regional refinement must derive from authorized vector boundaries and retain native support; raster enlargement cannot create physical evidence.

## Law structure is not parameter authority

This contract binds layer boundaries, causal ordering, event and lineage semantics, uncertainty rules and validation classes. It does **not** bind initial plate motion, breakup timing, thresholds, rates, uplift magnitudes or solver runtime. A representation such as finite rotations says how kinematics are encoded; it does not say why plates move. `UNKNOWN` remains unknown and is neither zero nor implicit persistence.

Motion is represented as piecewise time-valid spherical finite rotations relative to an explicit frame/reconstruction tree. An adapter such as pyGPlates may resolve ARCANA-authored rotations and topologies. It may not choose velocities, rift locations/times, collisions, subduction polarity or tectonic laws. Runtime and R6 adapter remain unpinned/unvalidated.

Rifting is organized as eligibility → driver-conditioned trigger → realization → event-recorded topology/lineage change. A seeded choice can resolve an authorized underdetermined alternative, but cannot replace physical eligibility or trigger authority. Collision and vertical response follow the same rule: no event, boundary change or relief is created without a governed law and provenance.

## Response, sea level and unknown domains

Tectonic uplift/subsidence is an ARCANA-derived forcing distinct from landscape response. FastScape and Badlands/eSCAPE remain candidate downstream landscape solvers, not plate engines; global spherical suitability is unqualified. Climate-dependent erosion stays disabled until causal climate and required material/base-level drivers exist. No precipitation is manufactured.

The sea-level reference datum can define land/ocean interpretation at t0 only. That is not a temporal/eustatic curve or shoreline-evolution authority. Numeric bathymetry remains `UNKNOWN`; it is not needed for narrow initial continental kinematics, but is required before depth-dependent basins, shelves, circulation/coupled ocean-climate or marine consumers. Deep→geodynamics remains `OPTIONAL_UNBOUND_INTERFACE` and Deep is not required for the first replay.

Integration is forward from 210 Ma and adaptive, with step criteria for displacement, events, boundary transitions, response timescales and authorized hard events. Numeric limits remain unbound. Simulation checkpoints preserve solver/law/seed state needed for restart; historical snapshots retain queryable physical state and evidence, not every solver internal. No implicit persistence follows from absence of an event.

## Readiness

The canonical t0 payload remains unchanged (`a6edad24…2506c`). Plate motion and bathymetry are unknown. The current plate IDs and crust classes are coarse raster support, not vector boundary truth. The architecture is ready; the first interval is not executable. See [parameter requirements](R6_PHYSICAL_EVOLUTION_PARAMETER_REQUIREMENTS.md) and [readiness matrix](R6_FIRST_PHYSICAL_INTERVAL_READINESS_MATRIX.md). No execution contract is created.

The canonical realization must not be selected for aesthetics, A1 similarity, resource/civilization outcomes or narrative preference. Any later selection must be fixed before trajectory generation and rely on law validity, stability, topology, explicitly authorized envelopes, reproducibility and contract compliance.

**Next action:** `R6_INITIAL_PLATE_KINEMATICS_AND_RIFT_PARAMETER_AUTHORITY_BINDING`.

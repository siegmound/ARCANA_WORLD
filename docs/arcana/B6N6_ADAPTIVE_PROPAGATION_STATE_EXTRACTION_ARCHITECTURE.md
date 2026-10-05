# R6 B6N6 — Adaptive Propagation and Significant-State Extraction

## Decision and scope

B6N6 separates the simulator's temporary numerical timeline from persistent WORLD_HISTORY. It defines an architecture and two contracts; it does not implement propagation, select a timestep, supply physics, or authorize canonical writes. The normative contracts are `contracts/R6_ADAPTIVE_PROPAGATION_CANDIDATE_TRAJECTORY_V1.json` and `contracts/R6_SIGNIFICANT_STATE_EXTRACTION_RECONSTRUCTION_V1.json`.

## Reused R6 mechanisms and remaining gaps

The design reuses B0-C atomic `HistoryStore.append_transaction`, B0-D closed-input `ReplayRecipe` validation/execution, B0-F isolated refinement child branches and reconstruction recipes, B0-G `MinimalStateContract`/`validate_extraction`, B0-E queries, and B6N4-A resolution-relative event-impact adjudication. `CheckpointEnvelope` already separates restart state from retained history. `EventRecord` carries time support, spatial support, trigger/cause, before/after IDs and dependency IDs. No second persistence, replay, event-significance, or refinement framework is introduced.

The remaining implementation gaps are domain adapters for candidate trajectory generation, domain-specific significance/reconstruction tolerance authorities, dynamic predicate evaluators, uncertainty estimation, and a production orchestrator that joins existing mechanisms. B6N6 does not qualify any of them.

## Time model and candidate trajectory

`INTERNAL_DT` is the temporary numerical increment. `CANDIDATE_SIMULATION_WINDOW` is the temporary integration scope. `REFINEMENT_WINDOW` is a temporal and optionally spatial sub-scope replayed at increased resolution. `PERSISTENT_STATE_INTERVAL` is determined after trajectory adjudication and extraction. Therefore `INTERNAL_DT != PERSISTENT_STATE_INTERVAL`.

Candidate samples S0…Sn are not canonical states merely because the solver computed them. They may be discarded after event/uncertainty extraction, significance decisions and replay closure. Reproducibility binds the base checkpoint, model/runtime/configuration identities, source/provider/authority references, initial state/dependencies, forcing/event predicates, seed lineage where stochastic, numerical setup and step decisions, domain resolutions, refinement decisions, dependency/isolation graph, uncertainty masks, and expected extracted identities. Samples remain retained where replay cannot establish a required tolerance or boundary.

## Adaptive stepping and UNKNOWN

An authorized controller may use governed integration error, change rates, event proximity, significance proximity, uncertainty growth, domain stability limits and model/authority validity bounds. It may grow or shrink `INTERNAL_DT`; growth never exceeds the tightest applicable authority/model bound. A revalidation horizon is not reclassified as an event-free interval. B6N6 assigns no arbitrary physical constants or thresholds.

Resolution and numerical unknowns may support time/space refinement, ensembles, preservation, or stopping the affected scope. Model capability, model authority and source authority unknowns cannot be repaired by refinement; isolate/preserve/stop the affected scope and request new authority. Dependency-isolation unknown prevents claiming local independence. Unknown is never converted to false, and refinement must not continue indefinitely against an irreducible authority gap.

## Events and refinement

Detectors may watch governed threshold crossings, predicate changes, topology/support/interface transitions, domain discontinuities and uncertainty/significance crossings. A candidate crossing is recorded over `[tA,tB]`; refinement narrows that bracket until the governed timing/significance criterion is met or uncertainty is irreducible. The event record retains the evidence-supported interval, confidence/uncertainty, scope, impacts, provenance and authority. No exact event time is fabricated. Event occurrence and state impact remain separate: an `EVENT_ONLY` event may be recorded without a state.

Local refinement identifies affected and buffer/dependency scope, domains, spatial resolution, parent checkpoint, forcing interval and replay recipe. It executes on an isolated child branch using B0-F. It cannot silently change the parent/global state. Effects beyond the child region require governed causal-dependency closure.

## Significant-state extraction and reconstruction

Only after a candidate trajectory is resolved or its irreducible unknowns are explicitly preserved does extraction apply B6N4-A against declared domain/resolution context. It considers topology, support, interface regime, geometry, climate, hydrology, Deep, resources, ecology, lineages, cross-domain causation, irreversibility, uncertainty boundaries and downstream effects. Thresholds remain references to future domain authority, not values invented here.

Keep mandatory event boundaries, required PRE/POST causal states, uncertainty boundaries, causal branch points, model/authority validity transitions and checkpoints needed for reconstruction. Omit other numerical samples unless an existing retention action, reconstruction tolerance or replay-closure need requires them. Reconstruction requirements span geometry, kinematics, climate, hydrology, Deep, resources, ecology and lineages; each domain must supply an authority-backed tolerance. If a tolerance is missing, do not claim lossy compression is valid.

The existing event ledger remains independent of state publication: `NO NEW STATE` does not erase an event. Existing `ReplayRecipe` fields cover checkpoint, runtime/configuration, seeds, forcing, events, dependencies, provenance, adapter and expected outputs; future adapters must bind numerical decisions, predicates, resolution, refinement, dependency closure and uncertainty when applicable. Deterministic replay may replace dense sample storage only when it verifies the required result.

## Canonicalization and current rift case

The order is candidate integration → qualification/refinement → event and uncertainty adjudication → state extraction → replay/provenance closure → atomic publication. Existing B0-C transactions provide all-or-nothing reader visibility; refinement uses the existing branch-scoped transaction. Failure publishes nothing, leaving canonical history unchanged.

If a future valid rift model provides evolvable variables, governed dynamic predicates, source/model authority and state-transfer/topology contracts, this architecture can monitor it, adapt stepping, bracket/refine a transition, extract PRE/POST states and persist sparse history without knowing event time in advance. The current B6N5 status remains `UNKNOWN_NOT_GOVERNED`: no next structural predicate, common authority, finite pre-transition interval, or selected provider exists. Adaptive resolution cannot fill that model/authority gap. The 8214.051909111062-year value remains only a model-scope revalidation horizon; 27123.405156307464 years remains the consumed preactivation horizon.

## Qualification boundary

Focused tests validate these contract invariants against the frozen B6N5 attestation and existing R6 interfaces. They do not constitute a physics run or authorize current-rift propagation. All canonical and execution gates remain false for this stage: no dt2, T2, B6O, mechanics, forward propagation, topology transition, or WORLD_HISTORY mutation.

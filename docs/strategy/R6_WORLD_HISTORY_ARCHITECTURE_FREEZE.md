# ARCANA WorldSim — R6 World History Architecture Freeze

**Status:** High-level architecture freeze; not an implementation or execution authorization  
**Repository:** siegmound/ARCANA_WORLD  
**Objective charter:** [`ARCANA_R6_CANONICAL_CLEAN_REPLAY_OBJECTIVE.md`](ARCANA_R6_CANONICAL_CLEAN_REPLAY_OBJECTIVE.md)  
**Architecture decisions:** conceptual responsibilities and contracts frozen; implementation choices explicitly deferred

## 1. Purpose and source boundary

R6 is simultaneously a **world generator**, **historical state engine**, **temporal world database**, **query system**, and **selective high-resolution replay engine**. Its product is `WORLD_HISTORY(x,y,t)` with causal explanation—not only `WORLD @ YEAR 0`.

This document freezes those architectural responsibilities and their interfaces. It does not implement the simulator, authorize a run or provider acquisition, or reopen any scientific adjudication.

The architecture consumes:

- the R6 World History Objective Charter, which fixes persistent queryable history, RAW-FIRST behavior, uncertainty, selective refinement, and `R5_R6_RECONCILIATION_REQUIRED = false`;
- `ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md`, which makes human population emergent, treats resource access/technology/Deep as coupled determinants, and reserves macrohistorical mechanisms for separately authorized implementation;
- `ARCANA_WORLD_CURRENT_STATE.md` as the R5/R5.17 status ledger, not as a blanket R6 input contract. Its internal R5/P7S entries describe distinct historical steps and are not promoted by this architecture;
- the available HRAB architecture contract and adjudication, because the named `ARCANA_HIGH_RES_ANCHORBRIDGE_HANDOFF_2026-09-21.md` is not present in this checkout. HRAB permits a sparse temporal constraint/unknown-mask architecture, fixes older-to-younger causality, and does not claim full temporal parent-material state, general endpoint backcasting, categorical interpolation, or spatial resampling;
- the local `R6_BIOME4_PRODUCTION_INPUT_CONTRACT.md/.json`, which freezes a consumer-driven interface but records unresolved monthly-temperature/cloud/elevation/soil/grid gaps and explicitly leaves production execution unauthorized;
- P7S/HRAB constraints only at the interfaces described below. No scientific result or adjudication is changed here.

## 2. Architectural invariants

1. Canonical initial conditions, canonical laws, and explicit replayable CHA-1/CHA-2 event contracts drive the clean forward replay.
2. ARCANA owns state meaning, authority labels, support semantics, and history interfaces. Engines and providers are replaceable implementations beneath those contracts.
3. Simulation state and persisted historical state are separate products with separate retention purposes.
4. Historical state is RAW-FIRST: preserve supported state, events, authority, uncertainty, and provenance before generating analytical views.
5. Partial domains are valid. UNKNOWN, sparse support, derived support, NOT_APPLICABLE, and OUTSIDE_SCOPE remain distinct where applicable.
6. Authority anchors constrain or inform state; they do not automatically set runtime or consumer checkpoints and do not authorize interpolation.
7. The global history, event-adaptive execution, and query-driven refinement are coordinated modes, not competing worlds. A refinement starts as a branch and cannot overwrite global history by default.
8. `K_effective(x,t)` is derived from upstream resource and access state; it is not the stored substitute for resource history.
9. R5 is not an R6 runtime dependency and agreement with R5 is not a canonicality condition.
10. Architecture readiness does not imply scientific-input readiness or execution authorization.

## 3. Top-level component responsibilities

These are responsibilities, not a requirement for one executable, service, package, or process per letter.

| Component | Responsibility and contract boundary |
|---|---|
| A. Canonical input / initial state | Validate canonical initial-state packages, laws, spatial support, event definitions, configuration, and seed/ensemble lineage. Reject unbound or semantically mismatched inputs; publish immutable run-input identity. |
| B. Physical world engine | Evolve governed physical geography and boundary state, including land geometry, elevation, shoreline, terrain, and basins, using authorized forward rules and drivers. |
| C. Climate engine | Produce climate state/forcing with explicit provider/model authority, domain, temporal/spatial support, uncertainty, and output interval. |
| D. Deep engine | Maintain first-class Deep state and governed interactions with physical, ecological, and human domains; expose intensity, accessibility, stability, resource value, and hazard only where defined. |
| E. Hydrology / freshwater engine | Evolve water stores, flows, freshwater availability and relevant aquatic support under climate, physical geography, and authorized soil/land inputs. It does not silently promote another engine’s diagnostic runoff to hydrological authority. |
| F. CHA event engine | Validate, schedule, apply, and record CHA-1/CHA-2 event contracts; bind event footprint, timing, forcing/effects, uncertainty, and provenance to before/after state. |
| G. Parent material / soil engine | Consume sparse HRAB constraints and authorized physical/temporal drivers; emit supported parent-material/soil state or UNKNOWN. It cannot treat the 0 ka endpoint as a paleo initializer or invent missing histories. |
| H. Vegetation / flora engine | Own ARCANA flora and vegetation history interfaces, including supported composition/distribution and authorized productivity; BIOME4 is a bounded solver/provider, not the flora ontology. |
| I. Fauna / trophic engine | Own fauna state, species/range/population/trophic history interfaces and uncertainty; Madingley or another engine can supply bounded calculations only under its governed adapter. |
| J. Aquatic / marine ecology engine | Own freshwater and marine biological state interfaces, respecting land/shoreline, aquatic connectivity, and biological authority. Marine resource support is not inferred from terrestrial proxies. |
| K. Natural resource engine | Materialize first-class terrestrial biological, freshwater, marine, geological/material, and Deep resource histories from authorized domain state. Keep resource stock/support separate from access and human carrying support. |
| L. Human demographic engine | Evolve population, migration, demographic structure, and uncertainty as emergent state; no target population is imposed to force an endpoint. |
| M. Settlement / connectivity / trade engine | Evolve settlements, routes, connectivity, accessibility, and trade-network state; bind environmental/resource/Deep conditions and their time support. |
| N. Technology / infrastructure engine | Track technology and infrastructure state and their effects on transformation, mobility, extraction, storage, and effective access/capacity. |
| O. Polity / conflict / civilization engine | Represent governed institutions, polities, conflict, and macrohistorical transitions, with their causal interactions and uncertainty; this charter does not define narrative content or detailed laws. |
| P. Historical state store | Persist queryable domain snapshots/views, support/uncertainty labels, versions, and provenance references needed for history queries and downstream consumers. |
| Q. Event store | Persist immutable event records and state-transition links, including CHA events and modelled events, with timing, footprint, status, and provenance. |
| R. Provenance / authority store | Preserve value-independent authority class, source/runtime identity, transformations, configuration, dependencies, seeds/ensemble lineage, validation, and conflicts. |
| S. Checkpoint / restart system | Persist restart-complete simulation checkpoints and their exact dependencies, seed state, forcing cursor, and schema/runtime compatibility; verify restart equivalence. |
| T. Query engine | Answer state, history, search, event-difference, lineage, and “why” queries over persisted history and indexes without requiring a world rerun. |
| U. Selective refinement / high-resolution replay engine | Plan and execute a bounded derived branch from a valid refinement anchor, boundary conditions, higher-resolution evidence where available, and a planned causal cone. |
| V. Validation / invariant engine | Apply input, authority, physical, temporal, domain, cross-domain, endpoint, ensemble, restart, and provenance checks; return PASS/PASS_WITH_UNKNOWN/PARTIAL/BLOCKED/FAIL. |

### Global system architecture

```text
Canonical initial state + laws + CHA contracts + governed providers + run/seed identity
                                  |
                          R6 ORCHESTRATOR
                                  |
       +--------------------------+---------------------------+
       |                          |                           |
 Physical / climate /       CHA event engine          Deep / water / soil
 environment engines              |                    and ecology engines
       +--------------------------+---------------------------+
                                  |
                human / settlement / resource engines
                                  |
     +----------------------------+---------------------------+
     |                            |                           |
 Simulation state          Event + provenance       Validation / checkpoints
     |                            |                           |
     +-------------------- RAW historical state --------------+
                                  |
                    searchable derived views / query
                                  |
                       local refinement branches
```

## 4. Causality, feedback, and execution ordering

The causal graph is a directed dependency relation with feedback groups—not a single acyclic stage list. The orchestrator resolves upstream prerequisites, then advances strongly coupled domains using an implementation-specific coordination strategy that must be separately specified and validated. This freeze does not select a numerical iteration or solver.

### Feedback/coupling model

```text
climate -> hydrology -> freshwater ecology -> flora <-> fauna
    |            |                 |             ^       |
    +-> soil <---+-----------------+-------------+-------+
          ^                                               |
          +---------------- ecology <--------------------+

physical world -> shoreline/land -> climate, hydrology, ecology, resources
Deep <-> flora/fauna (only where canonical laws authorize the coupling)
Deep <-> humans; Deep -> hazard/access/resource value

flora/fauna -> biological RESOURCE_HISTORY <- material/resource engine
RESOURCE_HISTORY <-> humans (use/pressure/management only under future authority)
humans <-> ecology; humans <-> settlement/connectivity/trade
technology/infrastructure <-> access and K_effective
trade <-> resource accessibility; settlement <-> environment
conflict/war <-> population, settlement, trade, resources, polity
```

Feedback timing has three distinct meanings:

- **INTRA-STEP FEEDBACK:** coupled domains affect each other within one declared execution unit before its accepted output is committed. The implementation must disclose convergence/iteration or simultaneous-update semantics and record non-convergence; no algorithm is selected here.
- **INTER-STEP FEEDBACK:** a completed interval/domain output becomes an input to a later interval or consumer step. Dependency order and the source checkpoint/version are explicit.
- **SLOW STATE FEEDBACK:** accumulated state (e.g. soil development, resource pressure, infrastructure, technology, institutions, or settlement persistence) affects later faster processes. It is carried as state with age/version/provenance rather than recomputed as a same-step algebraic shortcut.

No edge authorizes a coupling by itself: the applicable canonical law, input authority, and domain contract must permit it. If an upstream input is UNKNOWN, downstream outputs depending on it are marked UNKNOWN/partial or computed only through an explicitly bounded alternative path; no silent numeric default, zero, or authority upgrade is allowed.

## 5. Temporal object model

| Object | Purpose / authority | Persisted or runtime-only | Restartable / queryable | Model-derived; coincidence and consumer rules |
|---|---|---|---|---|
| `AUTHORITY_ANCHOR` | Evidence point/range with governed support; constrains or informs a state, not an arbitrary between-anchor rule. | Persist authority record and provenance. | Not inherently restartable; queryable as evidence/support. | May be provider/canonical evidence or a governed derived constraint. May coincide in time with any other object, but does not thereby become one. Consumer may require its value, not an engine run. |
| `SIMULATION_CHECKPOINT` | Complete restart boundary for continuing a computation. | Persist restart package or reference. | Restartable when full state, cursors, schema/runtime compatibility, and stochastic state are captured; not automatically a historical query result. | May be model-derived. May coincide with a snapshot/anchor/consumer time, but semantics remain separate. Orchestrator/restart system can require it. |
| `HISTORICAL_SNAPSHOT` | Queryable domain state at explicit time and support, with uncertainty and lineage. | Persist in the history store or governed retained representation. | Queryable; not necessarily restartable. | May be direct, sparse, or model-derived. May coincide with checkpoint, but need not contain internal restart variables. Downstream history queries/consumers can require it. |
| `EVENT_RECORD` | Describes a timed transition, forcing, or event and its relation to before/after state. | Persist in event store. | Not itself restartable or a full state query; supports event/change queries. | May be externally authorized or model-derived according to event class. May coincide with a snapshot time; consumers may request event boundaries. |
| `REFINEMENT_ANCHOR` | Validated initial/boundary state for local replay with causal context and boundary conditions. | Persist its identity and all source references. | Restartable only if packaged as a compatible checkpoint; queryable as a state/support reference. | May be model-derived and need not be a hard authority anchor. Can coincide with snapshot/checkpoint/anchor but is semantically distinct. Refinement planner may require it. |
| `CONSUMER_CHECKPOINT` | Requested evaluation time/support for a downstream consumer such as ecology. | Persist request and realized output if executed. | Not inherently restartable; queryable when its output is materialized. | Request is not evidence and may be model-derived in its scheduling rationale. May coincide with provider time, authority anchor, snapshot, or simulation checkpoint without conflating them. Consumer planner creates it only for actual demand. |

Thus `provider timestamp != authority anchor != simulation checkpoint != historical snapshot != consumer checkpoint`. A provider timestamp is metadata about source sampling until a governed contract assigns stronger semantics.

## 6. Temporal resolution modes

### A. Global base history

A planet-wide, searchable causal backbone. It advances in independently restartable execution intervals, with state/event/authority outputs and validation at configured boundaries. It is not one monolithic 200 kyr job. The exact interval ages and grid remain unfrozen. HRAB's 12 hard anchors (200, 125, 120, 20, 15, 14, 13, 12, 11, 10, 5, 0 ka) remain source-specific governance/validation boundaries; they do not force 11 universal runtime intervals or imply full parent-material evolution.

### B. Event-adaptive resolution

The planner can request denser temporal or spatial execution around governed system changes—such as CHA events, rapid shoreline/climate changes, ecological collapse, mass migration, population crash, war, or polity collapse. Trigger, resolution, support, and boundary metadata must be recorded. A source timestamp or hard anchor alone is not a trigger. Resolution changes do not authorize unsupported interpolation, backcasting, or fake spatial detail.

### C. Query-driven refinement

A later local/regional replay responds to a historical query or scientific need. It uses a refinement anchor, boundary conditions, relevant causal history, and finer evidence if available. It becomes a versioned `DERIVED_REFINEMENT_BRANCH`, never an automatic correction to global base history.

## 7. Global execution, interval, and restart model

An interval execution is a resumable work unit, not a new governance gate. It can be configured with:

```text
interval identity and temporal/spatial support
input/forcing manifest + authority preflight
seed / ensemble lineage
compatible start checkpoint (or canonical initial state)
runtime simulation state and event/forcing cursors
requested snapshots and consumer checkpoints
event records + provenance references
validation report and partial/UNKNOWN counts
end checkpoint (when restart-complete)
```

### Temporal execution lifecycle

```text
plan interval and consumer demand
  -> validate inputs, authority, boundary/checkpoint identity
  -> hydrate simulation state and stochastic/forcing cursors
  -> advance coupled domains; schedule/apply events
  -> materialize requested history/events/provenance (RAW-FIRST)
  -> validate invariants, cross-domain state, and outputs
  -> persist end checkpoint + interval report
  -> PASS / PASS_WITH_UNKNOWN / PARTIAL: allow governed dependent work
     BLOCKED / FAIL: isolate interval/domain; never advertise unsupported completion
  -> resume only from compatible checkpoint and identical declared lineage
```

An interval is independently restartable only when its start state and all necessary hidden/runtime state are recoverable: domain state needed to advance, event/forcing positions, configuration and runtime identities, schema compatibility, external-engine state where relevant, stochastic generator/member state, and exact input/authority hashes. An output snapshot alone is insufficient. A checkpoint with missing restart variables is not promoted as restart-complete.

The interval contract binds start/end support, forcing manifest, state/version inputs, event schedule, run configuration, seed/ensemble lineage, outputs, validation, and checkpoint hashes/identities. Retries must not mutate the identity of completed outputs silently. Hard scientific anchors may be compared as constraints at relevant boundaries, never forced by arbitrary endpoint adjustment.

### Asynchronous domain timescales and consumer checkpoint planning

Domains may advance on different process scales. The architecture uses a **CONSUMER_CHECKPOINT_PLANNER** to accept a request containing consumer, domain/variables, space-time support, accuracy/use purpose, dependencies, and required authority status. It resolves whether to:

1. reuse a compatible persisted snapshot;
2. request a supported upstream checkpoint/output;
3. schedule a governed domain evaluation at the requested consumer time;
4. return partial/UNKNOWN/BLOCKED if mandatory authority or compatible state is absent.

No implicit daily/monthly/anchor-wide resampling is performed. A domain adapter must declare how its output is valid at the requested time; a provider's available timestamp is not automatically the consumer request. Cross-timescale reconciliation must be explicit in each consuming contract and preserve source temporal support and uncertainty. BIOME4 exemplifies this rule: determine ecological demand first, then preflight its mandatory fields at those demanded checkpoints; do not run at every climate timestamp or all 12 anchors by default. The current BIOME4 input gaps remain UNKNOWN and execution remains unauthorized.

## 8. Simulation state, history store, and retention

`SIMULATION_STATE` is the full ephemeral/internal state necessary to advance active models, including solver state, latent variables, coupled-domain buffers, event/forcing cursors, and RNG state. It may include variables that have no direct historical query role.

`HISTORICAL_STATE_STORE` is the persisted, provenance-bearing and queryable record used for `State(x,y,t)`, history/search, derived views, downstream consumers, event reconstruction, uncertainty reporting, and valid restart/refinement anchors. It must retain enough to interpret support and derive intended queries, not every internal numeric variable.

Conceptual retention classes (orthogonal labels may be combined by policy):

- `RETAIN_ALWAYS`: authoritative initial conditions, canonical event records, promoted historical state, support/uncertainty semantics, provenance and version identities needed to interpret the history.
- `RETAIN_EVENT`: state/event evidence around governed events and resolution transitions.
- `RETAIN_CHECKPOINT`: restart-complete checkpoint state and compatibility manifest at designated interval boundaries.
- `RETAIN_QUERY_VIEW`: reproducible summaries/index inputs needed to search without rerunning the world; rebuildable only from retained source history and a versioned transformation.
- `RECOMPUTABLE`: deterministic/model-derived intermediates whose full dependencies and exact method/runtime are retained and whose recomputation is authorized and feasible.
- `EPHEMERAL`: transient solver work arrays and temporary buffers not required for history, provenance, query, restart, or declared reproducibility.

Classification is per datum and purpose, not per file. Data classed recomputable still needs enough source and transform provenance to reproduce or explain it. Do not discard a value needed for valid restart merely because it is not a user-facing query variable.

## 9. RAW-FIRST history and derived views

```text
simulation / governed provider results
          |
          v
historical states + event records + support/uncertainty + provenance
          |
          v
versioned derived views, summaries, search indexes, statistics, maps
```

First-class histories include `PHYSICAL_HISTORY`, `CLIMATE_HISTORY`, `HYDROLOGY_HISTORY`, `PARENT_MATERIAL_HISTORY`, `SOIL_HISTORY`, `DEEP_HISTORY`, `FLORA_HISTORY`, `FAUNA_HISTORY`, `FRESHWATER_ECOLOGY_HISTORY`, `MARINE_ECOLOGY_HISTORY`, `RESOURCE_HISTORY`, `HUMAN_HISTORY`, `SETTLEMENT_HISTORY`, `TRADE_HISTORY`, `TECHNOLOGY_HISTORY`, `POLITY_HISTORY`, and `CONFLICT_HISTORY`. Coverage may be partial. Each applicable state reports `KNOWN`, `DERIVED_SUPPORTED`, `SPARSE_AUTHORITY`, `UNKNOWN`, or `NOT_APPLICABLE`/`OUTSIDE_SCOPE` with authority class and uncertainty; numeric presence alone is never authority.

Derived views include biome/species/Deep/resource/population maps, networks, and statistics. Each records source history versions, transformations, authority level, uncertainty propagation, and provenance. Views are disposable/rebuildable only where source retention supports that; changing a view does not require planetary rerun and cannot rewrite source state.

## 10. Resource, Deep, ecological, and external-engine contracts

### Resource history and effective support

`RESOURCE_HISTORY(x,y,t)` is upstream first-class state, with domain-specific semantics for terrestrial biological resources, freshwater, marine, timber, biomass, stone, clay, salt, metals/ores, other geological materials, and Deep resources. Presence, stock/production, quality, accessibility, and human usability must not be conflated where separately governed.

```text
RESOURCE_HISTORY + technology + accessibility + trade
               + infrastructure + Deep + hazards
                              -> K_effective(x,t)
```

`K_effective` (or `K(x,t)` where the governed model uses that name) is a derived human-support state. It carries its own method, inputs, authority status, uncertainty, and provenance and never replaces the resource histories.

### Deep as first-class history

`DEEP_HISTORY(x,y,t)` is independently queryable. Where governed, it can expose `DEEP_INTENSITY`, `DEEP_ACCESSIBILITY`, `DEEP_STABILITY`, `DEEP_RESOURCE_VALUE`, and `DEEP_HAZARD`. It can couple to flora/fauna, evolution, human biology, settlement, extraction, technology, trade, warfare, and politics only under canonical laws and valid authority. It is not a settlement bonus scalar.

### ARCANA-owned ecological interfaces and engine substitution

ARCANA owns `FLORA_STATE`, `FAUNA_STATE`, `AQUATIC_STATE`, and `MARINE_STATE`, including meanings, units, support classes, uncertainty, and lineage. BIOME4 does not equal flora; Madingley or any other provider does not equal fauna. External engines (including BIOME4, Madingley, SLiM, Geonomics, RangeShiftR, NEMO, or CDMetaPOP where later authorized) sit behind:

```text
ARCANA semantic contract
 -> engine adapter (input/output mapping, runtime and provenance)
 -> bounded solver execution (only if authorized)
 -> normalized ARCANA output
 -> contract/invariant validation
 -> historical-state materialization
```

Substitution requires an adapter conforming to the same ARCANA contract and an adjudicated scientific scope; matching file shape or variable names is insufficient. Solver-specific output cannot silently redefine canonical state semantics. Diagnostics remain diagnostics unless separately promoted.

## 11. Query, search, and causal explanation

The query engine supports conceptual operations:

- **STATE:** retrieve state for a region/time and return value plus semantic type, support, uncertainty, authority, version, and provenance;
- **HISTORY:** retrieve a variable/species/resource history over a region and interval, including gaps and state transitions;
- **SEARCH:** locate space-time regions satisfying cross-domain conditions over compatible supports/grids without rerunning the world;
- **PROVENANCE / WHY:** explain evidence, canonical initial state, prior state, events, rules, providers, model/runtime, configuration, stochastic lineage, and transformations contributing to a result;
- **EVENT / CHANGE:** identify recorded events and supported differences between times, distinguishing observed/materialized transitions from query-derived comparisons;
- **LINEAGE:** trace a value/view to all upstream provider/model/event/state versions and validations.

Search requires retained or recomputable-without-world-rerun query summaries/index state; index values are derived views, never scientific source authority. Cross-domain search must expose joins that fail because spatial or temporal support is incompatible rather than silently aligning/resampling. The architecture supports queries such as regions during 80–40 ka with freshwater, biological productivity, large-herbivore support, stable Deep, a specified parent material, and coast/river connectivity. It returns candidate/support masks and provenance, not an unqualified assertion of full coverage.

## 12. Selective refinement, causal cones, and branch semantics

### Query-driven high-resolution replay

```text
query identifies region + interval + requested variables
  -> validate query support and choose valid REFINEMENT_ANCHOR
  -> recover coarse/global boundary conditions and parent-history version
  -> bind finer evidence only where it genuinely exists and is authorized
  -> plan necessary upstream CAUSAL_CONE
  -> warm up local/regional coupled state under declared boundary rules
  -> execute forward causal replay with events/laws/seed lineage
  -> materialize DERIVED_REFINEMENT_BRANCH + provenance/uncertainty
  -> validate against boundary, support, and invariants
  -> expose alongside global history; promotion requires separate adjudication
```

A valid refinement anchor has explicit time and spatial footprint; source/global-history version; state and support semantics; authority and uncertainty; sufficient causal precursor state; compatible boundary conditions; runtime/schema compatibility if used as a restart checkpoint; and a documented reason that forward refinement from it is scientifically valid. A present endpoint is not a universal paleo initializer.

The **CAUSAL_CONE_PLANNER** determines the minimal upstream domains required for requested outputs. For example, climate refinement may require hydrology, soil where affected, flora, fauna, Deep coupling where authorized, resources, and humans where the query asks for them. It records included/excluded dependencies and why; it does not run every engine for every query. The planner is an architectural responsibility, not implemented here.

Refinement branches record parent global-history version, anchor, region/time/resolution, boundary conditions, providers, models/runtimes, events, seed/ensemble lineage, validation, uncertainty, and outputs. Their state is `DERIVED_REFINEMENT_BRANCH` and their authority remains distinct from the global history. Promotion into any new global/reference history requires separate governed adjudication; no automatic merge or overwrite.

The system must never claim coarse-cell interpolation/resampling as physical high-resolution truth, invert present state into the past, or synthesize subcell detail without appropriately resolved evidence.

### Provenance lineage

```text
provider / canonical initial state / prior state / event
               \       |       / 
                 model + configuration
                         |
           runtime + seed/ensemble member
                         |
                 derived calculation
                         |
            normalized ARCANA state value
                         |
       authority class + support + uncertainty
                         |
             snapshot / derived view / query
```

Each edge is versioned and content-identifiable where appropriate. Authority is a separate field/class attached through explicit adjudication—not inferred from a value, engine success, or downstream visualization. Derived-view lineage links to source-history versions and transformation versions so that provenance survives materialization.

## 13. Uncertainty, stochastic histories, and partial state

The model supports ensemble member identity, declared reference/median states, quantiles, support probability, uncertainty intervals, conflict flags, forcing uncertainty, and structural model uncertainty where scientifically appropriate. Deterministic processes need not be replicated as ensembles. Stochastic macrohistory, evolution, dispersal, or demographic outcomes must retain member/seed lineage rather than collapsing to one convenient trajectory. Queries identify whether they return a member, summary, or pooled statistic and how uncertainty was propagated.

UNKNOWN is first-class and never means zero, absence, persistence, NOT_APPLICABLE, or a default material/biome. A downstream domain may produce a partial result only if its contract defines how unknown inputs affect that result and marks resulting uncertainty/support. For example, climate known + hydrology known + soil unknown does not invalidate those known upstream histories, and does not authorize numeric soil or dependent ecology. Failure/blocking is isolated by domain/interval when dependencies permit.

## 14. Validation and orchestration

### Validation layers

The validation engine checks, as applicable:

1. input contract and shape/semantic validation;
2. authority and temporal/spatial support validation;
3. state invariants;
4. conservation and physical checks;
5. hard-anchor preservation and anchor residuals (as constraints, not forced targets);
6. ensemble sensitivity where relevant;
7. timestep/resolution convergence where applicable;
8. cross-domain consistency;
9. checkpoint/restart equivalence;
10. provenance completeness and reproducibility metadata.

An interval or domain can return `PASS`, `PASS_WITH_UNKNOWN`, `PARTIAL`, `BLOCKED`, or `FAIL`. Only contractually valid dependencies may proceed; partial validity must not be labelled global completion.

### Orchestrator

The high-level orchestrator resolves dependencies and authority prerequisites; plans global intervals and event-adaptive work; requests consumer checkpoints; assigns run/ensemble lineage; invokes adapters; manages checkpoints and resume; coordinates coupled-domain steps; materializes history/events/provenance; validates; isolates failures; and reports partial/unknown support. It does not reinterpret scientific authority, silently fill missing values, or choose an engine outside an authorized adapter.

## 15. Adjudicated design questions

1. **Minimum persisted state for arbitrary-time queries:** every claimed query time must have either a persisted supported snapshot/constraint or a documented, versioned, reproducible reconstruction path whose source states bracket/support the query under an authorized temporal rule. Retain state values or references, validity/support masks, semantic units, authority class, uncertainty, time/space support, event links, version, and provenance. Arbitrary time does not mean every time is numerically known; otherwise return UNKNOWN/unsupported.
2. **Restart checkpoint but not necessarily history:** latent solver variables, integrator/coupling buffers, RNG/member state, forcing/event cursors, and internal engine state needed to resume; these may be `RETAIN_CHECKPOINT` without being query variables.
3. **How consumers request checkpoints:** submit a typed request to the consumer-checkpoint planner with variable/domain, time/region, use, dependencies, resolution/support needs, and mandatory authority; planner reuses, schedules, or declines/returns partial.
4. **Asynchronous timescales:** each domain declares native support and validity; explicit adapter/consumer rules reconcile the requested time, preserving uncertainty and not silently resampling.
5. **Avoiding BIOME4 at every climate anchor:** ecological consumers declare actual evaluation demand; the planner schedules only eligible requested checkpoints after mandatory-input/grid preflight. The current contract says all 12 anchor runs are not required and production is unauthorized.
6. **Feedback cycles without a pure DAG:** represent coupled domains as feedback groups and distinguish intra-step, inter-step, and slow-state feedback; require a declared, validated coordination policy later, without selecting its numerical algorithm now.
7. **UNKNOWN upstream propagation:** preserve per-variable/per-cell support; dependent outputs remain UNKNOWN or partial unless a separately authorized path makes the result independent of the unknown input.
8. **Refinement consistency with global boundaries:** bind the parent-history version, valid refinement anchor, spatial/temporal boundary conditions and causal precursor state; validate boundary residuals without force-fitting; disclose incompatible support and uncertainty.
9. **Versioned refinement:** separate immutable branch identity and parent version from global history; no promotion/overwrite without a separate adjudication.
10. **Recomputable versus retained:** retain authority, promoted history, event/provenance identity, required query support, and restart state; recompute only versioned derivations with complete dependencies and a valid replay method; keep transient work arrays ephemeral only if no query/restart/provenance need remains.
11. **Provenance through views:** each view stores source-state/version references, transformation identity/version, authority class, uncertainty propagation, and output identity.
12. **Engine substitution:** adapters map between stable ARCANA semantic contracts and solver-specific inputs/outputs; preflight, normalization, validation, and authority adjudication remain ARCANA-owned.
13. **Stochastic history queries:** preserve member/seed/ensemble lineage; queries explicitly select member or declared ensemble summary and report aggregation semantics/uncertainty.
14. **Valid refinement anchor:** time/region, supported state and uncertainty, authority/provenance, parent version, causal context, compatible boundary conditions/runtime where relevant, and authorized forward direction.
15. **Independently restartable interval:** compatible start checkpoint plus complete runtime/solver/coupling state, forcing/event cursors, configuration/runtime/schema identity, input hashes, and stochastic state; restart-equivalence validation passes.

## 16. R5 role

Freeze the charter's superseding rule:

```text
R5_R6_RECONCILIATION_REQUIRED = false
R5 = OPTIONAL_DIAGNOSTIC + REFERENCE_WORLD + DEVELOPMENT_HISTORY
     + PROVIDER/METHOD_DISCOVERY_SOURCE + REGRESSION_CLUE_SOURCE
R5_UPSTREAM_RUNTIME_DEPENDENCY = false
```

R6 starts from canonical initial conditions, laws, and event contracts. R5-derived artifacts are not implicit initial conditions or runtime dependencies. Voluntary comparisons may aid diagnosis; disagreement alone is not a failure or veto.

## 17. Freeze boundary

### Frozen by this architecture

- component responsibilities and ARCANA-owned domain interfaces;
- causal/domain boundaries and explicit feedback categories;
- distinct temporal-object semantics;
- global base, event-adaptive, and query-driven refinement modes;
- independently restartable interval contract;
- simulation-state/history-store separation and conceptual retention classes;
- RAW-FIRST source history and versioned derived views;
- first-class domain histories, resources, Deep, ecology, and human state;
- authority/provenance and uncertainty/partial-state semantics;
- external-engine adapter/normalization/validation boundary;
- consumer-checkpoint planning, including BIOME4 demand-driven preflight;
- state/history/search/event/lineage/provenance query responsibilities;
- causal-cone planning and derived refinement branches;
- validation layers, status semantics, orchestrator responsibilities;
- R5 has no upstream runtime dependency and R5 matching is not a canonicality gate.

### Explicitly not frozen

- database, object store, filesystem, or other storage technology;
- file formats, serialization, compression, schemas, and exact data model;
- SQL/API/query language or index technology;
- exact global grid, spatial resolution, timestep sizes, or interval ages;
- exact checkpoint frequencies and exact BIOME4 consumer run ages;
- numerical coupling, feedback iteration, solver, and convergence algorithms;
- number of ensemble members or ensemble execution framework;
- orchestration, parallelization, workflow, or scheduling library;
- provider-gap closure, new provider selection/acquisition, or any scientific execution;
- detailed laws for societies/civilizations or domain-specific implementation plans.

These choices require later design and, where they affect science or authority, separate governed contracts. Existing BIOME4 runtime/input contracts remain authoritative at their present scope; this architecture neither expands nor relaxes them.

## 18. Explicit non-authorization

This freeze does not execute R6, BIOME4, or any other engine; acquire providers; close BIOME4 gaps; reopen or modify P7S/HRAB; create soil/parent-material/ecological/resource/human results; define exact grid/timestep/database; or authorize downstream R5.17 work. It changes no scientific adjudication and does not update `ARCANA_WORLD_CURRENT_STATE.md`.

---

**Decision:** `R6_WORLD_HISTORY_ARCHITECTURE_FROZEN`  
**Verdict:** `PASS_HIGH_LEVEL_ARCHITECTURE_FROZEN__IMPLEMENTATION_AND_SCIENTIFIC_EXECUTION_NOT_AUTHORIZED`  
**Recommended next action:** `R6_ARCHITECTURE_CONTRACT_AND_INTERFACE_SPECIFICATION`

# ARCANA WorldSim — R6 WORLD HISTORY OBJECTIVE

**Status:** Authoritative strategic objective and requirements charter; not an implementation or execution authorization
**Project:** ARCANA WorldSim  
**Repository:** siegmound/ARCANA_WORLD
**Development/reference line:** R5
**Target world-history line:** R6
**Charter reconciliation date:** 2026-09-23

## 1. Objective

R6 is the governed system for generating, preserving, querying, explaining, and selectively refining ARCANA world history. It is not an endpoint-only replay and is not a reproduction target for the R5 final world.

R6 must combine, at the objective level:

- a causal world generator that runs forward from canonical initial conditions under canonical physical laws and explicit replayable CHA-1 and CHA-2 event contracts;
- a persistent global historical-state engine and temporal world database;
- a query system over state, events, evidence, uncertainty, and provenance;
- selective high-resolution replay for justified regions and causal cones.

This charter specifies outcomes and constraints only. It does not select the implementation DAG, database technology, storage formats, timestep values, or detailed process architecture.

The long-term product is an explainable historical world: for each state, ARCANA should be able to recover what it was, when and where it applied, which authorities and rules support it, how it arose, what remains uncertain, and which reproducible transitions connect it to other states.

## 2. Clean causal replay

R6 must be a clean forward simulation from canonical initial conditions. It must use canonical physical laws and explicit, replayable CHA-1 and CHA-2 event contracts, including their governed timing, spatial applicability, effects, uncertainty, stochastic components, and provenance.

R6 inherits the mature authority, provider, validation, unknown-state, and provenance disciplines developed in R3–R5. It must not inherit R5 development debris, one-off fallbacks, superseded intermediate artifacts, or unadjudicated state merely because those artifacts are locally available.

A clean replay separates effects of the canonical initial state, laws, and events from effects of historical implementation choices, partial recoveries, debugging work, and pipeline evolution. Reproducibility is required to the degree appropriate to each engine: preserve inputs, contracts, runtime identity, event and seed lineage, stage decisions, and tolerances. Bit-identical output is not presumed where a governed external engine cannot guarantee it.

No R6 simulation begins implicitly by existence of this objective.

## 3. Persistent world history

R6 must preserve a queryable GLOBAL BASE HISTORY across the governed simulation domain. Historical state is a first-class result, not merely transient state discarded after producing the terminal world.

The history objective includes, where supported by scientific authority:

- physical and geographical history, including land, elevation, shoreline, terrain, basins, and other governed spatial structure;
- climate and hydrological history;
- parent-material and soil history, with unsupported states remaining UNKNOWN;
- Deep history as an independent historical field;
- flora, vegetation, NPP, and plant-distribution history;
- fauna, species ranges, population state, and trophic history;
- freshwater ecological history;
- marine ecological history;
- material-resource history;
- terrestrial biological-resource history;
- freshwater-resource history;
- marine-resource history;
- Deep-resource history;
- human population, migration, and settlement history;
- technology, trade, institutions, conflict, and civilizations as governed human-history domains.

These domains need not all be complete before R6 architecture is designed or before an otherwise eligible simulation stage can proceed. Each domain must expose its support, authority, temporal applicability, uncertainty, and missing-state semantics. A field that lacks authority remains unknown or outside scope rather than being fabricated to create global coverage.

Ecology and natural history have independent scientific value. Flora and fauna must remain independently queryable and must not exist only as intermediates for human carrying capacity or support calculations.

## 4. Resources, Deep, and human support

RESOURCE_HISTORY(x,y,t) is a first-class upstream historical state. Natural material, biological, freshwater, marine, and Deep resources must not be collapsed directly into K(x,t).

K(x,t), where used, is a downstream derived/effective human-support quantity. It consumes governed resource history together with technology, accessibility, trade, infrastructure, Deep, and hazards. Its value, semantics, uncertainty, and provenance must identify those dependencies. It is not a substitute for the underlying resource histories.

Deep is not merely a settlement bonus. R6 must support queryable DEEP_HISTORY(x,y,t), including, where governed, DEEP_INTENSITY, DEEP_ACCESSIBILITY, DEEP_STABILITY, DEEP_RESOURCE_VALUE, and DEEP_HAZARD. Deep can support, constrain, or endanger systems depending on its state and context.

Human population is emergent rather than a target used to force a preferred world. Human-history outputs may include population, migration, settlements, technology, trade networks, institutions, conflict, and civilization/polity histories. They must be derived from governed causal state and rules, with uncertainty and ensembles where justified; they must not be tuned to reproduce R5 or an author-selected endpoint.

## 5. Historical queries and explanations

R6 must make world state queryable conceptually as State(x,y,t), with appropriate domain-specific dimensions and support. It must support historical search and filtering across space and time, including joins or comparisons across relevant domains where their authorities and grids permit.

Queries must be able to return state together with its semantic type, support, uncertainty, authority, and provenance. They must support causal/provenance explanation of WHY a state exists: the source evidence, initial conditions, events, process rules, model/runtime, and prior states contributing to it. A derived analytical answer must not be misrepresented as a direct observation or canonical state.

Examples of required future query capability include:

- Where was species S at time T?
- Which large herbivores existed in region R at 15 ka?
- Where were accessible copper-bearing regions around 6 ka?
- Which regions between 20 and 15 ka had freshwater, large-herbivore support, salt, and stable Deep?

The query contract includes historical search/filtering and explainability, but does not prescribe a query language or database product.

## 6. RAW-FIRST history and derived views

R6 follows RAW-FIRST / DERIVED-VIEWS:

> Simulate once; preserve governed historical states, events, authority, and provenance; derive analytical views later.

Derived views may include continent, climate, biome, Deep, species-history, resource, population, trade-network, civilization, and statistical views. Each view must declare its source history, transformation, authority level, and version/provenance.

Changing or adding a derived analytical view must not require rerunning the world simulation when the retained history and provenance are sufficient. Derived views do not overwrite the underlying historical state. Corrections to a simulation state require a governed replay or adjudication path, not an untracked view edit.

R6 must distinguish conceptually between:

- SIMULATION STATE: ephemeral or working state needed to numerically advance a process;
- HISTORICAL STATE STORE: persisted, queryable and replay-supporting representation of historical states, events, authority, uncertainty, and provenance.

The objective requires retaining enough information for historical queries, scientific provenance, downstream derivation, replay initialization, and high-resolution refinement. It does not prescribe storage technology or an exact schema.

## 7. Temporal objects and their distinct meanings

The following temporal objects are conceptually distinct even if a future implementation co-locates their data:

- AUTHORITY ANCHOR: an external or canonical evidence point with governed temporal and spatial support. It constrains or informs simulation; it is not automatically a runtime checkpoint.
- SIMULATION CHECKPOINT: a restartable runtime state at a simulation boundary. It exists to support execution/restart and is not automatically a fully queryable historical snapshot.
- HISTORICAL SNAPSHOT: a persisted, queryable representation of world state at a stated time/support, with provenance and uncertainty. It is not automatically sufficient to restart a simulation.
- EVENT RECORD: a governed transition or event relating states, with timing, applicability, effects, and provenance. It is not itself a state snapshot.
- REFINEMENT ANCHOR: a validated state selected as a start or boundary condition for a local or regional replay, with required causal and boundary context. It is not automatically a hard authority anchor.
- CONSUMER CHECKPOINT: a point actually requested by a downstream consumer, such as ecology. It is not implied by a provider timestamp or by every authority anchor.

A provider timestamp, simulation checkpoint, consumer checkpoint, and hard authority anchor are not equivalent. No ecological or BIOME4 run is required merely because a provider has a timestamp or because an authority anchor exists.

Temporal intervals may be independently checkpointable where useful, but no fixed number or schedule is specified here.

## 8. Temporal and spatial authority rules

Preserve the governed AnchorBridge constraints:

- causal temporal direction is older-to-younger forward where forward evolution is authorized;
- an endpoint at the present is a constraint or validation target, not a general paleo initializer;
- lineage, material, species, or other state must not be assigned outside its governed existence/applicability interval;
- UNKNOWN remains first-class and is not zero, persistence, absence, or NOT_APPLICABLE;
- source anchors constrain states but do not authorize arbitrary interpolation between them.

FORBID:

- linear interpolation between hard anchors as historical truth;
- present-to-past inversion or backcasting;
- generic categorical interpolation or nearest-anchor copying;
- fake spatial upsampling, replication, or resampling presented as new physical detail;
- arbitrary uniform high-frequency timesteps selected without process need;
- overwriting hard anchors with reconstructed intermediates;
- converting missing authority into zero, persistence, or fabricated coverage;
- inventing subcell detail without finer spatial evidence.

Intermediate history may be materialized only when supported by explicit, process-constrained rules and required drivers. It must be reproducible, uncertainty-bearing, explicitly model-derived, and lower-authority than the hard authority anchors it is conditioned by. Where those conditions fail, preserve UNKNOWN. An intermediate state must not be forced to match an endpoint by arbitrary adjustment.

Higher spatial resolution is permitted only where finer physical evidence supports it. Temporal density does not imply spatial detail. A coarser provider may condition a finer model cell only while remaining explicitly identified as coarse support; this does not create fine-scale evidence.

## 9. Global history and selective refinement

R6 recognizes three resolution modes without prescribing their numerical settings or implementation:

**A. GLOBAL BASE HISTORY** — a planet-wide, searchable historical backbone that preserves state, events, uncertainty, and provenance at a scientifically defensible baseline resolution.

**B. EVENT-ADAPTIVE RESOLUTION** — temporarily increased temporal or spatial resolution when governed physical, ecological, geological, or human dynamics require it. Resolution changes must be process-motivated and recorded; arbitrary uniform high-frequency expansion is not a substitute.

**C. QUERY-DRIVEN LOCAL/REGIONAL HIGH-RESOLUTION REPLAY** — a later, selective replay for a query or scientific need, initialized from an appropriate refinement anchor and supplied with valid boundary conditions, causal context, canonical laws/events, and higher-resolution providers where available.

Where scientifically possible, a refinement recomputes only the necessary causal cone rather than globally restarting the world. The refinement must preserve deterministic seed lineage or a declared ensemble lineage, disclose its dependencies and boundaries, and retain its own provenance. It must not silently overwrite or promote itself into the global base history. Promotion requires separate governed adjudication.

Global intervals or event windows should be independently restartable where useful. The objective does not mandate an arbitrary timestep hierarchy, checkpoint frequency, or refinement algorithm.

## 10. Uncertainty and partial-state support

Partial historical state is valid. R6 must preserve distinctions among supported values, derived values, sparse constraints, UNKNOWN, OUTSIDE_SCOPE, and NOT_APPLICABLE according to their actual semantics. Lack of evidence is not evidence of zero or physical inapplicability.

Uncertainty must accompany source and model-derived states. Ensembles and seed lineages should be represented where stochasticity, path dependence, or evidentiary uncertainty materially affects conclusions. A single run is not uniquely true solely because it was run first. The objective does not require ensembles where they are scientifically unjustified or computationally irrelevant; the choice and its rationale must be explicit.

R6 must validate stage prerequisites and fail closed where a mandatory authority is absent. A blocked cell or domain must not silently block unrelated valid states, but neither may a valid subset be described as complete global history.

## 11. R5 role and canonicalization — superseding decision

### Historical rationale retained

The earlier objective proposed R5-to-R6 reconciliation before canonical promotion because R5 was generated while architecture, provider authority, fallbacks, and partial recoveries were evolving. That comparison was intended to expose unexplained divergence and keep R5 available as an oracle while R6 matured. This rationale remains part of the project’s decision history.

### Superseding rule

The mandatory comparison gate is superseded. Freeze:

**R5_R6_RECONCILIATION_REQUIRED = false**

R5’s role is:

**OPTIONAL_DIAGNOSTIC**

Development/reference world; provider and method discovery history; debugging and regression clue source.

R6 does not need to reproduce R5 outcomes. R6 may produce different climate, ecology, flora, fauna, resources, human populations, settlements, or civilizations when those outcomes follow from governed R6 contracts, canonical laws/events, and causal execution.

Similarity to R5 is not a criterion for R6 validity, canonical promotion, or R6 canonicalization. R5 remains useful evidence and may be compared voluntarily for diagnosis, regression investigation, or explanation, but disagreement alone is neither failure nor a veto.

R6 canonicalization must depend on:

- scientific validity and authorized state semantics;
- internal physical, temporal, and cross-domain invariants;
- reproducibility appropriate to the involved engine;
- complete provenance for each promoted state and derived result;
- preservation of UNKNOWN and other support distinctions;
- contract integrity and validated prerequisites;
- causal consistency with canonical initial conditions, laws, events, and declared stochastic lineage.

No R6 state becomes canonical merely because it is newer; nor must it agree with R5 to be canonical. Promotion remains subject to an explicit validity and governance decision under the criteria above.

## 12. BIOME4 and consumer-driven ecological checkpoints

The local R6 BIOME4 production input contract is an available worktree authority, even if absent from published main. Its exact runtime identity, input semantics, gaps, soil interface, grid preflight, and UNKNOWN policy remain governed by that contract. This objective does not reopen P7S or claim that missing BIOME4 inputs have been filled.

Preserve the distinctions:

**provider timestamp ≠ simulation checkpoint ≠ BIOME4 consumer checkpoint ≠ hard authority anchor**

First determine which ecological/biological checkpoints the R6 architecture actually consumes. Run BIOME4 only at requested consumer checkpoints whose complete mandatory inputs and grid/mask compatibility pass preflight. Otherwise the corresponding ecological result remains UNKNOWN. Do not require closure of every climate/provider gap before R6 architecture design, and do not run BIOME4 at all provider timestamps or all authority anchors by default.

A BIOME4 contract with explicit input gaps is compatible with continued R6 architecture planning. It is not authorization to execute BIOME4 or to substitute synthetic sunshine, sea-level elevation, annual-to-monthly temperature, or unknown soil.

## 13. Stage governance and scope

Every future implementation stage must identify its required authorities and prerequisites, validate them before execution, retain provenance and uncertainty, and state which outputs are partial, unknown, or outside scope. A stage may advance only when its governed result supports the declared next action.

This charter does not:

- implement the R6 DAG or detailed model architecture;
- select a database, storage format, query engine, or schema;
- set timestep values, checkpoint schedules, or spatial resolutions;
- close BIOME4 or other provider gaps;
- authorize provider acquisition or scientific runs;
- reopen P7S or HRAB;
- authorize physical-soil completion, ecology, resource materialization, human simulation, or a downstream R5.17 stage.

R5 current-state and stage ledgers remain historical status authorities for R5. This charter does not rewrite or complete those stages.

## 14. Long-term success criterion

R6 succeeds as a world-history system when its governed record can answer spatial, temporal, cross-domain, and causal questions about the world from retained historical state and events; can distinguish authority from model-derived reconstruction and unknown state; and can reproduce or selectively refine relevant history from documented initial conditions, laws, events, inputs, and seed/ensemble lineage.

The required result is not a single prescribed endpoint. It is a persistent, explainable, queryable, uncertainty-aware history whose natural, physical, resource, Deep, and human domains remain independently meaningful.

---

**Charter status:** Reconciled as the R6 WORLD HISTORY objective on 2026-09-23.
**Implementation architecture:** Not frozen.
**R5_R6_RECONCILIATION_REQUIRED:** false.
**Recommended next action:** R6_WORLD_HISTORY_ARCHITECTURE_FREEZE.

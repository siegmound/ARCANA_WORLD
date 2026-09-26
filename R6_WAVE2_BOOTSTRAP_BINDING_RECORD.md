# R6 Wave 2 — canonical authority and bootstrap binding

**Baseline:** `main` / `origin/main` `592b1651b405363373590092e133bd25569d99a5`
**Disposition:** software interfaces implemented; scientific bootstrap remains blocked and explicitly unbound.
**Scope:** targeted source reconciliation, initial-state candidate audit, provider/temporal registries, request contract, and bounded climate/hydrology adapters. No model, provider acquisition, or scientific replay was run.

## Source findings

- The R6 objective and architecture freeze are valid design authorities. They require a clean forward replay from a bound canonical initial state under canonical laws and replayable CHA-1/CHA-2 contracts; R5 artifacts are not implicit initial conditions. The architecture distinguishes provider time, authority anchors, simulation checkpoints, historical snapshots, refinement anchors, and consumer checkpoints.
- The exact R3.28 NPZ hash matches the mandated value. Its `age_ka` vector is `float64`, 280 finite values, strictly descending from 200 to 0 ka, with no duplicates. All 12 hard anchors occur exactly. This is only a clock from a population-fork replay, not physical or parent-material state.
- The A1 210–0 Ma NPZ hash is verified. It contains 11 frames on 90×180, including plate/land masks, climate/forage, population and carrying-capacity variables. It is a mixed downstream reference bundle, not a clean canonical R6 initial-world package. The R3.8 150 Ma checkpoint is likewise a continuation state, not an R6 initializer.
- P7S has bounded 65-cell climate evidence and explicit support/mask gaps; the driver-recovery adjudication blocks a complete historical forcing. No global climate payload is bound here. Krapp/Beyer variables, support, resolution, and temporal semantics remain product-specific; no cross-provider interpolation or grid resampling is authorized.
- B6 D1 is a contract. B6 D3 itself records an execution error, zero snapshot results, and `paleohydrology_materialized=false`. B6 D4 records a separate derived freshwater-access result; it does not repair or replace the failed physical D3 replay. The shoreline adapter is scoped and does not establish a global dated shoreline history.
- CHA-1 and CHA-2 contracts are bound as scoped source contracts only. CHA-1 describes the 66.0–65.5 Ma event bridge; CHA-2 describes a Younger-Dryas-class event and nested 15–11 ka hazard diagnostics. Neither by itself supplies a complete R6 bootstrap package or makes an R6 run executable.
- The Scientific Authority Register basis is earlier than this HEAD. It was not rebuilt. Targeted findings and hashes are recorded in `R6_WAVE2_TARGETED_AUTHORITY_RECONCILIATION.json`.

## R6 implementation

Wave 2 adds immutable versioned provider descriptors, a role-distinct temporal registry (including `PROVIDER_TIMESTAMP`), deterministic bootstrap identity metadata, and typed consumer state requests that check time, grid/cells, declared native resolution, variables, support, and minimum authority. Climate binding now supports caller-supplied governed values only when authority references and applicability are explicit; the default remains fixture-only. Hydrology adds a no-execution import boundary for an already-produced result, requiring exact upstream support alignment, contract-matched units, result hash, and authority references. It does not call the legacy B6 runtime.

Wave 1 regression plus Wave 2 interface tests pass. This establishes software readiness only; it is not scientific authorization or provider binding.

## Readiness matrix

| Domain/interface | Status | Current evidence / gate |
|---|---|---|
| R6 core identities, state, store, query, provenance | `SOFTWARE_READY` | Wave 1 reference backend and Wave 1–2 tests; no production DB claim |
| Provider registry / adapters | `SOFTWARE_READY` | Metadata and governed-result boundary; no new provider acquisition |
| Temporal roles and consumer request | `SOFTWARE_READY` | Distinct typed records and strict request validation |
| Canonical initial physical world | `BLOCKED` | No complete qualifying R6 package identified/bound |
| Canonical laws and seed/ensemble lineage | `BLOCKED` | Not bound to a canonical initial package |
| CHA-1 / CHA-2 | `AUTHORITY_BOUND_SCOPED` | Contracts referenced; R6 runtime/event integration not executed |
| Climate | `AUTHORITY_BOUND_SCOPED` | P7S bounded proof and source adjudications only; no global R6 climate state |
| Shoreline / land applicability | `AUTHORITY_BOUND_SCOPED` | B6 D2C1 adapter; incomplete time/domain coverage |
| Hydrology / paleohydrology | `BLOCKED_FOR_R6_STATE` | B6 D3 failed; D4 remains a distinct bounded derived output |
| Parent material / soil | `BLOCKED_OR_UNKNOWN` | HRAB core is not full history; physical soil not created |
| Flora / BIOME4 | `BLOCKED` | Mandatory full-grid inputs not bound; no execution |
| Fauna / marine ecology | `BLOCKED_OR_UNKNOWN` | No complete historical range/abundance or aquatic biological authority |
| Deep / resources / human history | `SOFTWARE_NOT_BOUND` | No Wave 2 scientific state or execution |

## First scientific state and next work

No first R6 scientific state was persisted: the canonical initial world, laws, and seed/ensemble lineage are unbound; the current scoped climate/hydrology evidence does not close those prerequisites. `R6_BOOTSTRAP_MANIFEST.json` therefore records a deterministic but explicitly unbound bootstrap identity and `scientific_execution_authorized=false`. No UNKNOWN value was changed to a number, and no current-state ledger or execution index was modified.

**Next action:** recover or govern a complete canonical initial-state package and bind its laws, event contracts, grid, runtime/configuration, and seed/ensemble lineage; refresh the targeted authority reconciliation against that package before authorizing any R6 science. Do not start a global climate/hydrology replay, BIOME4, soil, ecology, macrohistory, or provider acquisition from this checkpoint.

# R6 World History Core — Capability Reconciliation

**Assessment:** before implementation, against the frozen architecture at
`cadbd7b5874d01770ceafc7571fc41e749ef58c2`.
**Scientific execution:** unauthorized. **Historical bootstrap identity:** untouched.

This inventory reuses the Wave-1/Wave-2 core rather than recreating it. State
identity, UNKNOWN semantics, provenance, typed temporal roles, and the
append-only JSON HistoryStore already exist. Querying is currently limited to
`state_at`; architecture registries and planning are conceptual only. Typed
event semantics, additional checkpoint identity fields, explicit state-envelope
lineage metadata, retention labels, and refinement branch metadata are partial
or absent.

| Frozen requirement | Reusable implementation | Status | Remaining gap |
|---|---|---|---|
| Canonical/scientific authority | `AuthorityClass`, provenance, provider descriptors, authority anchors | PARTIAL | No domain authority registry; canonical bootstrap remains unbound. |
| State identity | `DomainStateId` content hash | IMPLEMENTED | — |
| Historical-state envelope | `DomainStateEnvelope` | PARTIAL | Explicit model-derived/applicability/conflict/event/refinement fields. |
| UNKNOWN / NOT_APPLICABLE | `SupportClass` and query status | IMPLEMENTED | — |
| Provenance and uncertainty | `ProvenanceRecord`, recursive trace; frozen uncertainty mapping | IMPLEMENTED | Domain-specific uncertainty details remain domain-owned. |
| Six temporal roles | Temporal record subclasses and `TemporalAuthorityRegistry` | IMPLEMENTED | Event and refinement payload semantics need typed fields. |
| HistoryStore | Append-only JSON reference store | IMPLEMENTED | Typed iteration/query access to events/checkpoints/branches. |
| History queries | `HistoryQueryService.state_at` | PARTIAL | HISTORY, SEARCH, LINEAGE, AVAILABLE_RESOLUTION, REFINEMENT_CANDIDATES. |
| Event records | Generic `EventRecord.details` | PARTIAL | Named affected support, cause, before/after, causal dependencies. |
| Checkpoint metadata | Runtime/config/seeds/dependencies/validation/restart state | PARTIAL | Parent ID, authority refs, provider manifests, engine versions, outputs. |
| Refinement anchor/branch | Typed `RefinementAnchor`; generic `BranchId` | PARTIAL | Immutable branch scope, boundary conditions and provenance record. |
| Domain registry | Provider registry only | MISSING | Domain availability, bindings, query and refinement status. |
| Dependency graph / causal cone | Architecture prose/JSON only | MISSING | Executable conditional graph and deterministic cycle-aware closure. |
| Retention classes | None | MISSING | Typed ALWAYS_PERSIST, CHECKPOINT_PERSIST, DERIVED_RECOMPUTABLE, EPHEMERAL. |
| Engine role registry | Provider registry only | MISSING | Bounded capability and authorization status per engine. |
| Branch/refinement lineage | State parent/provenance links | PARTIAL | Explicit base history, anchor, query scope, boundaries and outputs. |

The machine-readable inventory, including source paths and deferred scientific
work, is in `R6_WORLD_HISTORY_CORE_CAPABILITY_RECONCILIATION.json`. It records
what exists at the assessment point; later software additions do not rewrite
the Wave-2 bootstrap snapshot.

## Implementation boundary

Only reusable software foundations are added after this reconciliation:
state metadata with backward-compatible identity handling; executable domain,
engine, retention and conditional-dependency registries; deterministic
causal-cone planning; typed event/checkpoint/refinement records; and the missing
history-query operations. No provider is newly bound, no scientific state is
created, and no simulation is authorized.

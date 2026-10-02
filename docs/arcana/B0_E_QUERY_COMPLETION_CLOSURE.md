# B0-E WORLD_HISTORY Query Completion

**Scope:** generic local-history query APIs. Queries are exact and read-only; no scientific evolution, replay execution, provider lookup, spatial GIS operation, or implicit interpolation is performed.

## History query

`HistoryQueryService.history_result` returns a typed `HistoryResult` containing immutable `DomainStateEnvelope` records. Optional filters cover the existing exact dimensions: history, branch, domain, time key, cell membership for `CELL_SET`, and selector kind. The returned state retains StateId, temporal/spatial support, authority, uncertainty, payload reference, provenance, parents, and event references; payload bytes are never copied into the result. The existing `history()` tuple API remains available.

Ordering is the semantic tuple `(time coordinate system, time support kind, time key, domain, spatial selector, grid ID, cell IDs, StateId)`. It is independent of filesystem enumeration and insertion order. Time keys are opaque exact keys; this query does not infer elapsed-time ordering from their syntax. No authority floor is offered because the current core has no defined authority ordering.

## Exact difference

`HistoryQueryService.difference(state_a_id, state_b_id)` compares the exact persisted states and defines numeric difference as **B − A**. Compatible states must have identical domain semantics and complete `SpatialSupport`, and matching temporal coordinate system and support kind. Their time keys may differ, as expected for a temporal difference. No support conversion, resampling, or interpolation is attempted.

Statuses are `COMPARABLE`, `INCOMPATIBLE_SUPPORT`, `UNKNOWN_INPUT`, `NOT_APPLICABLE`, `OUTSIDE_SCOPE`, `MISSING_INPUT`, and `TYPE_OR_SHAPE_MISMATCH`. Scalars and flat numeric vectors produce exact deltas (vectors require equal lengths). Booleans, strings and JSON mappings report equality/change only; no subtraction is invented. Unsupported shapes/types return a non-success status.

Each result retains both source state records, exposing both authorities, uncertainty mappings, and support classes. Uncertainty propagation is explicitly `NOT_PROPAGATED`; the difference inherits no authority. UNKNOWN, NOT_APPLICABLE and OUTSIDE_SCOPE remain semantic statuses, not null-valued numeric observations.

## Unified WHY

`HistoryQueryService.why(state_id)` returns a typed `WhyResult` with the target and state lineage, provenance DAG, events, forcings, checkpoints, replay recipes, external references and unresolved typed references. It follows only recorded parent/provenance/event/forcing/checkpoint/replay/dependency links. A replay recipe is discovered by its declared expected output StateId; WHY reads its retained records and never reruns replay.

Records and references are deduplicated by semantic ID and result tuples are sorted by ID. Shared ancestry is included once. A missing recognized typed reference is listed under unresolved references; arbitrary external/source references are retained separately. Corrupt typed records fail closed. No source data or causal relation is inferred.

## Support boundaries and purity

The existing `state_at` distinctions remain: exact cell match, `OUTSIDE_SUPPORT`, `SUPPORT_MISMATCH` for selectors that cannot answer cell membership, `UNKNOWN`, `NOT_APPLICABLE`, `OUTSIDE_SCOPE`, `MISSING_DOMAIN`, and `MISSING_TIMESTAMP`. A missing state ID in `difference` returns `MISSING_INPUT`. General polygon/raster containment remains outside this API.

History, difference, and WHY only call store read/list APIs. Regression tests compare store bytes before and after queries. They do not create records, change authority, execute replay, materialize refinements, or access providers over a network.

## Gate status after B0-E

- **H4 history query:** `IMPLEMENTED_AND_TESTED` for the exact represented filters and reopen/insertion-independent order above.
- **H5 difference query:** `IMPLEMENTED_AND_TESTED` for exact state comparisons, documented support/type restrictions, metadata retention and reopen.
- **H6 WHY/provenance:** `IMPLEMENTED_AND_TESTED` for recorded state/provenance/event/forcing/checkpoint/replay links, deterministic traversal, dangling references and corruption failure.
- **H14 support boundaries:** `PARTIAL`; current exact cell selectors are covered, but general spatial containment is intentionally not implemented.
- **H17 deterministic ordering:** `IMPLEMENTED_AND_TESTED` for B0 history and WHY result collections. This is not a claim about external engines or future query surfaces.

No existing checkpoint, forcing, replay, state, or authority record schema is changed by B0-E.

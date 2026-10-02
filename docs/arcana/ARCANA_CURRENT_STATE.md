# ARCANA WorldSim — Current State

## Repository and lineage

- Repository: `siegmound/ARCANA_WORLD`
- Working line: `r6/pre-b0-repository-consolidation`
- Parent scientific HEAD: `2aa6a8e4d8edbd7796c5c2dea4c8d0d90f042264`
- Current objective: PRE-B0 safe repository consolidation; B0 is the next
  implementation milestone after cleanup review.

## R6 T0 and runtime boundary

- T0 authorial realization: `B_PANGAEA_LIKE_LATE_TRIASSIC_v2`, ratified for
  T0 materialization. Preserve its authority artifacts and producer lineage.
- Materialized ShellSet support: 64,442 nodes, 128,880 triangles; canonical
  mesh SHA256 `6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad`.
- S1B FAIR result reported successful loading of the governed ARCANA T0
  runtime package (`expected_nodes=64442`, loaded=true, ARCANA mode=true,
  failure=false). Current `runtime_authorized=true` is limited to
  `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`; it does not authorize
  full mechanics or forward evolution.
- Reconcile this FAIR handoff evidence with the tracked pre-execution
  compatibility closure, which still records `runtime_authorized=false` and
  `runtime_or_mechanics_qualification_claimed=false`. This documentation does
  not silently rewrite those scientific/runtime artifacts.
- `runtime_authorized=true` only for
  `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`
- `mechanics_authorized=false`
- `forward_evolution_authorized=false`
- `dt_selected=false`
- `t1_created=false`
- `canonical_state_changed=false`

## PRE-B0 consolidation

C0-A inventory and C0-B authority/dependency adjudication are recorded in
`C0_B_AUTHORITY_DEPENDENCY_AUDIT.md`. C0-E cleanup is being performed on the
consolidation branch; no cleanup step changes scientific authority. The
milestone after cleanup is **B0 — Minimal WORLD_HISTORY Core**.

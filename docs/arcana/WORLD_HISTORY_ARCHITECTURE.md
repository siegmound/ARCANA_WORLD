# WORLD_HISTORY Architecture

WORLD_HISTORY is a persistent causal and queryable history, not a dense dump
of every timestep. It stores enough governed state and provenance to answer
historical queries, replay a causal path and refine selected regions or time
windows later.

## Core decisions

- Query-driven access to state by time, region and domain.
- Minimal sufficient state with explicit provenance and provider identity.
- Adaptive historical checkpoints; event records and forcing connect them.
- Deterministic replay reconstructs detail from governed inputs and recorded
  transformations where possible.
- High-resolution refinement is selective and branches from explicit anchors.
- ARCANA owns canonical state, scientific semantics and canonicalization.
- Providers are replaceable/bounded and do not acquire authority from output.
- The hard canonical storage ceiling is **500 GB**. No final field count,
  checkpoint density or compression design is fixed here.

## Initial implementation boundary

B0 is the Minimal WORLD_HISTORY Core: identities, immutable state/event and
provenance records, checkpoint/refinement anchors, storage and query behavior.
It does not imply long-interval physical evolution or authorize a provider's
mechanics. T0 inputs and R6 physical contracts remain explicit upstream
dependencies.

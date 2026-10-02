# B0-F Refinement Isolation and Reconstruction Closure

**Scope:** generic branch/storage contract and deterministic synthetic refinement only. No production ARCANA spatial refinement, T0 change, T1, mechanics, or scientific promotion is performed.

## Branch and write scope

The existing `RefinementBranchEnvelope` remains schema V0 and its existing branch IDs and read behavior are unchanged. It declares the child branch, parent branch/history, anchor, region, time interval, domains, resolution, boundary conditions and provenance. New `RefinementReconstructionRecipe` records bind that child branch to a validated parent checkpoint/state basis and a deterministic output manifest. The recipe is a separate record because the existing branch envelope does not identify its base checkpoint or carry typed per-output parent/child support and payload identities. Keeping outputs out of the branch semantic body also avoids a circular StateId/BranchId identity dependency.

`HistoryStore.append_refinement_transaction` is the branch-scoped publication API. It verifies parent checkpoint/history/branch and parent state membership, region support, boundary-condition digest, child branch/history/domain/time, exact child spatial support, payload identity, and the declared output set before atomically publishing branch metadata, recipe, child states and permitted provenance/event records. Generic `append_state` and `append_transaction` reject writes into a registered refinement child branch; parent records remain append-only immutable. The store has no branch merge or overwrite API.

## Reconstruction contract

`RefinementReconstructionRecipe` (`ARCANA_R6_REFINEMENT_RECONSTRUCTION_V0`) captures branch and parent IDs, checkpoint, parent states, parent region cell IDs, boundary-condition SHA-256, runtime/configuration/seed identity, model/adapter identity, and an ordered output manifest. Each manifest entry identifies the expected output StateId, parent support cells, child support cells, and optional payload identity. It reuses B0-D payload identity semantics without duplicating payload bytes. A separate recipe is necessary because B0-D `ReplayRecipe` is bound to a single branch/checkpoint scope and one expected output; refinement uses a parent checkpoint and multiple child-branch outputs.

The injected refinement runner receives resolved immutable parent states, branch/recipe metadata, and declared boundary inputs, but no store handle. The core verifies output order, StateIds, child branch/history, declared domains/time, support mapping and payload identities. Results remain candidates until a verified `MATERIALIZED` recipe plus output records are explicitly published through the atomic branch transaction. `MATERIALIZED` means a deterministic output manifest was recorded; it is not scientific approval or authority promotion.

## Synthetic proof and query behavior

The fixture starts with coarse cells A–D in a parent state and checkpoint. Region B is refined to B1–B4 using explicit fixture boundary offsets and a deterministic runner. Child states have the child BranchId and `FIXTURE_ONLY` authority/support. Reopening the store and rerunning the adapter reproduces the same child StateIds and payload identities while parent state bytes remain unchanged.

History queries remain branch-exact: parent history returns parent records and child history returns child records only. There is no parent fallback. B0-E difference permits cross-branch comparison only where domain, temporal semantics and complete spatial support match; this finer synthetic support is `INCOMPATIBLE_SUPPORT`. WHY follows the explicit refinement recipe to child-branch metadata, parent checkpoint/state, provenance, and output records without executing the runner.

## Transaction, authority and compatibility

The entire child publication bundle uses the existing B0-C atomic transaction contract. Injected interruption rolls back branch, recipe and child outputs on reopen. Parent records are read-only inputs and remain byte-identical. Child authority is explicit in each state and is never copied or promoted from the parent.

`src/arcana_worldsim/r6/initial_world/refinement.py::materialize_region` is **ADAPTER_NEEDED**: it deterministically returns array fields, masks and a rich descriptor/provenance mapping, while the generic B0-F contract persists typed states, branch/checkpoint references and per-output support identities. No adapter is added here; its field-specific resolution/authority metadata must be explicitly mapped before reuse.

## Gate status and limits

- **H10 branch isolation:** `IMPLEMENTED_AND_TESTED` for the branch-bound write API, immutable parent records, exact branch queries, reopen and atomic publication failure behavior. There is no branch merge or distributed concurrency contract.
- **H11 reconstruction:** `IMPLEMENTED_AND_TESTED` for the generic synthetic multi-output reconstruction contract, declared input closure, injected deterministic adapter, reopen and identity verification. No real T0 refinement or scientific adapter is qualified.

Remaining limits include generalized spatial geometry containment, canonical branch merge/conflict resolution, promotion workflow, payload byte storage, and adapters for the initial-world array producer or scientific refinement engines. R6 authorization gates remain unchanged.

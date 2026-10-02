# B0-D Forcing and Replay Closure

**Scope:** generic WORLD_HISTORY infrastructure with synthetic fixtures only. No ARCANA physical transition, ShellSet/OrbData execution, or T1 creation is performed.

## Typed records

- `ForcingRecord` uses schema `ARCANA_R6_FORCING_V0` and deterministic `ForcingId`. Its identity binds history/branch, forcing kind/domain, declared temporal and spatial support, support and authority classes, an optional compact JSON value or payload reference, provenance IDs, and source references. Unsupported support cannot carry a value or payload. Machine paths are excluded through the shared deterministic-ID rules.
- `ReplayRecipe` uses schema `ARCANA_R6_REPLAY_RECIPE_V0` and deterministic `ReplayRecipeId`. It references a base checkpoint, runtime identity, configuration SHA-256, seed lineage, ordered forcing IDs, ordered event IDs, upstream dependencies, provenance IDs, expected output state and optional expected payload identity, plus a stable model/adapter identity. It stores no executable code, absolute path, or timestamp.
- Existing checkpoint identity and schema are unchanged. The recipe references the checkpoint and checks runtime/configuration/seed/dependency agreement at replay time.

## Persistence and closure

Forcings and recipes have typed append/read/list APIs with read-time identity validation and participate in the existing bounded atomic `append_transaction` API. Their buckets are additive and do not change the existing store manifest or record-layout version.

`validate_replay_inputs` resolves exactly the declared checkpoint, restart states, forcing records, events, expected state, and recursive provenance parents. It checks branch/history scope, supported input status, runtime/configuration/seed identity, dependency agreement and dependency resolution. Payload forcing references require an explicit resolver and content-digest verification. Missing, corrupt, or mismatched inputs fail closed; no substitute search occurs.

## Executor and verification

`execute_replay` validates closure before calling an injected deterministic runner. The runner receives an immutable resolved-input bundle and recipe, not the store, so it cannot implicitly persist or mutate WORLD_HISTORY. Its output is a candidate. Verification compares semantic state identity, scope, authority/support, payload reference and any declared payload identity. Mismatches have status `MISMATCH`; they are never success-with-warning. No output is persisted automatically.

## Synthetic proof and limits

The B0-D test fixture atomically stores synthetic `fixture:s0` inputs, provenance, two ordered forcings, an event, checkpoint, expected `fixture:s1`, and recipe; a new store instance reopens and verifies the recipe. The injected integer adapter applies ordered forcing steps and seed deterministically. Repeated replay before/after reopening yields the same output state ID and payload identity. The fixture remains `FIXTURE_ONLY`; equality does not promote scientific/provider/canonical authority.

Negative tests cover missing and malformed forcing identities, forcing corruption, runtime/configuration/seed disagreement, missing events, checkpoint dependency mismatch and unresolved dependencies, changed forcing order, wrong produced state, wrong output payload digest, and resolved forcing-payload integrity. The recipe ID captures sequence order, so reordering is a different recipe and must independently match its expected output.

**H8 replay integrity:** `IMPLEMENTED_AND_TESTED` for typed recipe/forcing persistence, closure validation, and deterministic synthetic replay equivalence. This does not establish replay equivalence for external engines or any physical ARCANA model.

## Authority and remaining limits

Replay does not upgrade authority. The synthetic result remains `FIXTURE_ONLY`. B0-D does not implement a general workflow engine, automatic payload/CAS store, unified WHY query, external runtime resolver, engine compatibility policy, physical forcing model, or scientific replay. Store transaction guarantees retain the existing B0-C single-writer/process-interruption scope.

R6 authorization gates remain unchanged: runtime authorization is limited to `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`; mechanics, forward evolution, `dt`, T1, and canonical-state changes remain unauthorized/false.

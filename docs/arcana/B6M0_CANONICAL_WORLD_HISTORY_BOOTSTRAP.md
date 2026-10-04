# B6M0 Canonical WORLD_HISTORY Bootstrap

## Decision

`PASS_B6M0_CANONICAL_WORLD_HISTORY_BOOTSTRAP` at source baseline `d20c3533f2729a31d5c5823d1233a3ffc0b9a56a`. The governed T0 genesis is represented by 14 domain-state records at one canonical temporal state (210 Ma). The B0-C transaction ran in a private staging store, then the completed directory was atomically installed.

## Validation

- Durable reopen: `PASS_TYPED_RECORDS_AND_QUERIES_AFTER_REOPEN`.
- Idempotence: `ALREADY_INITIALIZED_IDENTICAL`.
- Synthetic conflicting target: `CONFLICTING_CANONICAL_STORE`.
- Genesis queries: STATE `FOUND`, WHY provenance resolves, SUPPORT `AVAILABLE`, UNKNOWN `UNKNOWN`, and temporal validity is represented by the T0 instant and authority anchor.
- Difference is not applicable because T0 has no predecessor; no replay recipe or refinement checkpoint was fabricated.
- Existing payloads are referenced; payload bytes copied: `0`.

## Regression

B6M0 focused tests: **8 passed**. Complete active R6 suite: **448 passed**. Python compile and compileall: **PASS**.

## Scientific boundary

This operation initializes history with the already governed T0. It does not apply the selected dt or candidate, create T1, move nodes, mutate topology, run mechanics, or execute a transition. `t1_created=false`, `canonical_state_changed=false`, `forward_evolution_authorized=false`, and `topology_transition_executed=false`.

## Discovery and next stage

The portable discovery contract uses `ARCANA_WORLD_HISTORY_ROOT` as the runtime locator and logical store id `r6canonical_18bab1f51f02b62f6b78e893b24c9fd81f8d48b8ed30d513c6d19141ebf3e4a0`; the machine path is excluded from semantic identity. Readiness: `READY_TO_RESUME_ATOMIC_FIRST_T1_PUBLICATION`. The next stage may resume atomic first-T1 publication. B6M0 itself did not create T1.

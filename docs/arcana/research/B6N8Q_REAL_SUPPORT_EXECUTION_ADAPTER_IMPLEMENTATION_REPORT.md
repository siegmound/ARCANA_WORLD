# B6N8-Q — Real-Support Execution Adapter

## Decision

`PASS_B6N8Q_REAL_SUPPORT_EXECUTION_ADAPTER_IMPLEMENTED_VALIDATED_READY_FOR_ADAPTER_QUALIFICATION`

This closes the B6N8-P infrastructure blocker only. It does not qualify or authorize real T0 execution. The real scenario roster remains unbound, its count `N` remains unknown, and expected cardinality remains `63620 × N`.

## Baseline and authority

- Branch: `r6/b6n8q-real-support-execution-adapter`
- Implementation source baseline: `bb2dc97534ee5cb42b71fad777c0ecbcbeb9b8ca`
- B6N8-P qualified source: `f79ccef337a72152bdbf13369d01960f3df8cb2d`; its decision remains `BLOCKED_B6N8P_EXECUTION_CONFIGURATION_INCOMPLETE`.
- B6N8-O provider qualified source: `73d98ee14f933622f0d3f18f66985b06f364abcd`; production execution remains unauthorized.
- P and O attestations, P run contract, candidate-output identity, and all 16 P-snapshot authority byte/text hashes are checked fail-closed by the adapter. Raw checkout-byte SHA256 and canonical UTF-8/LF SHA256 are handled separately.

## Implementation

`src/arcana_worldsim/r6/b6n8q_execution_adapter.py` adds typed execution modes, authorization, externally supplied scenario rosters with explicit support assignments, per-support metadata plans, deterministic identities, candidate records/manifests, validation, external staging writes, and fail-closed resume behavior. Synthetic tasks are yielded in deterministic batches only for roster-declared support/scenario pairs; no implicit Cartesian product is created. Batch size is operational and excluded from semantic identity. It imports and reuses B6N8-O; no thermal equations were copied and no O source or synthetic guard was changed.

`METADATA_PREFLIGHT` runs the qualified B6N8-N support preflight and constructs deterministic non-generative plans, including support class, material roles, tuple identities, source-term references, geometry reference and already-governed diffusivity values. Across 63,620 admitted supports it found 14,258 continental and 49,362 positive-age oceanic supports; 1,072 unresolved-ocean and 108 zero-age ridge supports remain excluded. There were zero admitted unresolved or ambiguous supports. The measured Windows run took 6.610420 seconds; this is a single metadata observation, not a performance limit or thermal benchmark. Evaluator functions were replaced by fail-if-called sentinels during the 63,620-support test.

Numerical orchestration and candidate writing accept only explicit `TEST_Q_...` fixture identifiers and a `TEST_ONLY`, noncanonical roster. Scenario entries carry explicit support assignments; the adapter creates no implicit support-by-scenario product. The synthetic continental and oceanic paths were exercised. Candidate identity binds run, support, scenario, configuration, T0, provider and output-contract identity. Writes are atomic and restricted to staging outside the repository and any `WORLD_HISTORY` path. Manifests transition `PLANNED → RUNNING → VALIDATION_PENDING → COMPLETE_CANDIDATE_SET`; failures remain `INCOMPLETE`. Resume verifies the same content-derived run identity and stored candidate hashes. There is no HistoryStore/checkpoint/promotion import or API.

The real execution request path requires a qualified roster and then still fails closed because Q grants no real-run authorization. The P scenario class remains `AUTHORIZED_SCENARIO_ENSEMBLE`, while the actual roster and `N` remain unresolved.

## Validation

- B6N8-Q adapter tests: **20 passed**.
- Combined adapter, B6N8-O initializer, and PRE_ORBDATA implementation/runtime-package tests: **71 passed**.
- The combined regressions did not access WORLD_HISTORY.
- Full active R6 suite: `FULL_R6_SUITE_NOT_RUN_BY_STAGE_SAFETY_CONSTRAINT`.
- Python compilation: **PASS**.
- JSON parse and UTF-8/LF checks: **PASS**.
- Portable-path and local-reference checks: **PASS**.
- `git diff --check`: **PASS**; untracked authored-text whitespace check: **PASS**.

## Q gates

Q1–Q6 and Q8, Q12–Q14 pass. Q7, Q9 and Q10 pass for synthetic-only candidate execution. Q11 passes for metadata-only validation of all 63,620 real supports. Q14 means ready for a later execution-adapter qualification; it is not real-run authorization.

## Remaining blocker and non-actions

The exact remaining execution blocker is the unbound real scenario roster and unresolved `N`; no real run authorization exists. No real support profile, T0 candidate or T0 state was generated. Provider science, physical parameters, Buck selection/mechanics, dt, T2, canonical checkpoints and WORLD_HISTORY were unchanged. `REAL_T0_EXECUTION_READY` remains `false`.

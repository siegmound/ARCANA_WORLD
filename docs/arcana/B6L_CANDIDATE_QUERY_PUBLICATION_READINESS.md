# B6L Candidate Query and Publication Readiness

## Decision

`PASS_B6L_CANDIDATE_QUERY_PUBLICATION_READINESS` qualifies source commit
`406013da9f761d5581f889470c3626f89024f2b7`. B6L establishes
`READY_FOR_CANONICAL_T1_PUBLICATION`; it does not publish T1 or itself grant
publication authorization.

## Candidate and queries

B6K's candidate remains the fixed input: 27,123.405156307464 years, target
209.97287659484368 Ma, and candidate payload SHA256
`9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a`.
The support index resolves all 64,442 canonical nodes to 66,435 plate-local
representations. The extra 1,993 rows equal the governed multi-plate incidence
expansion; no node is lost, row unexplained, identity collided, or unique owner
assigned. Boundary and junction support remain set-valued.

A typed B0-D `ReplayRecipe` is persisted in the isolated B6L store, reopened,
resolved, and executed against the governed input closure. It reproduces the
B6K candidate state identity and exact payload SHA. Query checks pass for
STATE, HISTORY, DIFFERENCE, WHY, SUPPORT, REPLAY, UNKNOWN, and temporal validity.
The difference view distinguishes changed geometry, unchanged topology,
asynchronous non-update, UNKNOWN accommodation, and runtime model-scope limits.
Refinement is `READY_AFTER_CANONICAL_PUBLICATION`; no refinement was run.

## Publication and safety

The publication plan uses one B0-C `HistoryStore.append_transaction` bundle.
It creates semantic/provenance/event/temporal records and references or promotes
the existing content-addressed candidate payload without copying it. A
disposable synthetic target passed injected failures before publication, after
partial writes, before commit, and during reopen/recovery; rollback and retry
were deterministic. B0-C's stated limits on concurrent visibility and full
power-loss durability remain.

The future canonical state class is
`CANONICAL_FIRST_STATE_AT_RIFT_ACTIVATION_BOUNDARY_PRETRANSITION`. The endpoint
still records the satisfied rift predicate and `transition=NOT_EXECUTED` with
pre-transition topology. Ordinary continuation is blocked until a separately
authorized and executed rift transition. No canonical store was touched; no
T1, mechanics, transition, or second dt was produced.

## Validation and next step

Windows tests: B6L focused **15 passed**, related B5–B6K/B0-C,D,F **120 passed**,
full active R6 **440 passed**. Static validation results and artifact hashes
are retained in the JSON package and SHA256 manifest.
The next proposed action is `AUTHORIZE_ATOMIC_FIRST_T1_PUBLICATION_AND_FINAL_QUERY_ACCEPTANCE`.
That authorization is not granted by B6L itself.

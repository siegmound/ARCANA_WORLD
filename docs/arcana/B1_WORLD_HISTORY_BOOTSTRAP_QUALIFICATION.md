# R6 B1 — WORLD_HISTORY Bootstrap Qualification

## A. Qualified revision and scope

Qualified source commit: `76458611d1a6608a6dac63036d0a698801043f62` on
`r6/b1-world-history-bootstrap-qualification`. The worktree was clean before
qualification runs. Environment: Python 3.11.15, Windows 10, AMD64. The
HistoryStore schema is `ARCANA_R6_FILE_HISTORY_STORE_V0`, identity format 1,
record layout 1. The active R6 suite contains 323 tests.

B1 qualifies the synthetic B0 lifecycle only. It does not qualify scientific
production use, real T0 evolution, mechanics, `dt`, or T1.

## B. H1–H18

The machine-readable matrix at
`outputs/r6_world_history_b1_qualification/B1_H1_H18_MATRIX.json` gives each
gate's status, exact tests, implementation modules, reopen evidence, negative
checks, scope, and limitations. H1–H8, H10–H13, and H15–H18 are
`PASS_INTEGRATED`. H9 append-only behavior and H14 support boundaries remain
`PASS_SCOPED`; no broader concurrency/immutability claim or general GIS
containment is made.

## C–D. Test and lifecycle evidence

The focused B0-B through B0-H runs passed 7, 11, 13, 17, 8, 12, and 3 tests.
The complete active R6 suite passed 323 tests. Counts and measured durations
are in `B1_TEST_RESULTS.json`.

The B0-H lifecycle test creates a fixture-only store, atomically publishes the
initial bundle, destroys and reopens the store, queries it, executes replay,
reconstructs a refinement branch, measures storage, and reopens again. It
asserts that semantic identities and query results survive each filesystem
boundary. `B1_SEMANTIC_REPRODUCIBILITY_CHECK.py` repeats the lifecycle in two
fresh roots with reversed insertion order and compares WHY ordering as well as
semantic outputs.

## E–F. Corruption, recovery, and determinism

Integrated tests reject altered state, payload, forcing, refinement recipe,
and ambiguous journal content. Interrupted publication is rolled back on a
new store instance, leaves pre-existing records intact, and remains idempotent.
Fresh-root builds match state/forcing/event/checkpoint/recipe IDs, payload
identities, history order, replay/refinement outputs, retention choices and
canonical storage totals. Operational journal IDs and filesystem timestamps
are excluded.

## G–H. Scientific safety and storage

Qualification did not execute ShellSet or OrbData mechanics, alter governed T0
or authority, select `dt`, create canonical T1, promote provider authority, or
run real refinement. Existing gates remain: runtime authorization is limited
to `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`; mechanics, forward
evolution, `dt`, T1, and canonical-state change remain false.

Storage evidence uses explicit fixture scopes only. Canonical metadata, payload,
and transaction metadata remain separate; shared payload objects count once.
Index, scratch, provider cache, refinement cache, and qualification evidence
are separately exercised by the supplemental qualification check and do not
enter canonical persistent bytes. The cap is strictly below decimal
500,000,000,000 bytes; small test caps exercise the exceeded case. The
repository itself is not measured as WORLD_HISTORY.

## I–J. Portability and limitations

Semantic qualification artifacts contain no absolute machine paths, temp
roots, or usernames. OS/Python/architecture are environment evidence only.
Qualification is bounded to the current local filesystem HistoryStore and
synthetic deterministic adapters. H9 remains scoped to tested immutable-record
and append behavior; H14 remains limited to exact declared support semantics.
Remote storage, concurrent filesystem mutation, general GIS containment, and
scientific engine replay are outside this qualification.

## K–L. Decision and next stage

All H1–H18 gates pass at their declared scope, with no failures. The core is
authorized to proceed only to `AUTHORIZE_B2_SYNTHETIC_SCALE_QUALIFICATION`.
This authorization does not extend to real T0 evolution, `dt`, T1, mechanics,
or scientific production.

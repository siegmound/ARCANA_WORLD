# R6 B2 — 64,442-node WORLD_HISTORY scale qualification

## A. Qualified revision and scope

Source commit: `700bb2228555f3d5ea9a2b79414b8cacbbb8473b`. Environment: Python 3.11.15, Windows / AMD64, NumPy 2.4.3. Values and connectivity are synthetic `FIXTURE_ONLY`. No real T0, production FEG, runtime package, ShellSet, or OrbData mechanics was read or run.

## B. Synthetic dataset and payload

Generated 64,442 synthetic node identifiers and 128,880 synthetic triangles in one deterministic NPZ. Size 5,028,822 bytes; SHA256 `a4924e54aab9d9ae7e1fd395ff812279da39b6f65358b0d08cf937711c0b4ad7`. Generation 0.0080s, serialization 0.0205s, write 0.0020s, verification 0.0072s. A disposable corrupted copy failed payload verification.

## C. Spatial support and calibration

The full grid uses the existing `GRID` selector, with empty `cell_ids`; support metadata is 118 bytes and five initial state envelopes total 4942 bytes. It is not enumerated per state. The API cannot resolve an individual cell against a GRID selector (`SUPPORT_MISMATCH`); sampled direct payload indices are explicitly not represented as store membership queries.

- 1,024 nodes: payload 57,440 B; generation 0.0004s, serialization 0.0026s, write 0.0005s, reopen 0.0013s, accounting 0.0168s, metadata 1,360 B.
- 8,192 nodes: payload 444,512 B; generation 0.0008s, serialization 0.0023s, write 0.0005s, reopen 0.0011s, accounting 0.0166s, metadata 1,360 B.
- 32,768 nodes: payload 1,771,616 B; generation 0.0021s, serialization 0.0065s, write 0.0010s, reopen 0.0011s, accounting 0.0165s, metadata 1,363 B.
- 64,442 nodes: payload 5,028,822 B; generation 0.0080s, serialization 0.0205s, write 0.0020s, reopen 0.0019s, accounting 0.0277s, metadata 26,734 B.

## D. Persistence, queries, replay and refinement

Target publication 1.4769s; reopen 0.0019s. Target storage accounting took 0.0277s. Typed verification succeeded after reopen. The store contains 18 semantic JSON records, 26,734 metadata bytes and 19 files; with the payload, the transient fixture has 20 files. JSON count follows semantic records, not node cardinality.

Twenty samples: state query median/p95/max 0.0399/0.0472/0.0472s; history 0.0144/0.0174/0.0174s; difference 0.0038/0.0061/0.0061s; WHY 0.0054/0.0080/0.0080s.

Replay `VERIFIED` in 0.0101s. Refinement `VERIFIED` in 0.0107s for a 256-cell parent sample, with 4 output states and immutable parent. A second build with reversed record insertion reproduced payload and semantic IDs, forcing/checkpoint/recipe IDs, refinement output IDs, query order and storage totals: `True`.

## E. Retention, accounting and memory

Raw generated arrays 5,026,428 B; minimal retained fields 2,191,028 B; reconstructable identifiers, coordinates and topology omitted 2,835,400 B. Forcing is retained as a typed referenced record; derived view, diagnostics and scratch are omitted.

Canonical metadata: 26,734 B in 19 files. Canonical payload: 5,028,822 B in 1 file. Shared payload was counted once. Canonical total 5,055,556 B of 500,000,000,000 B; within cap `True`. Other categories are empty. Peak Python traced allocation 21,784,097 B; RSS not measured.

## F. Regression and decision

`python -m pytest -q --basetemp=<isolated B2 temp>/full_r6 -p no:cacheprovider`: **323 passed, 0 failed, 0 errors** in 121.41s. Production WORLD_HISTORY source changes: **0**. Scale class: **NO_SCALE_BLOCKER_OBSERVED**. B3 readiness: **READY_WITH_MEASURED_LIMITATIONS**.

The support-membership limitation must be respected in B3. No arbitrary latency threshold was applied; measured timings are hardware-specific.

## G. Scientific safety and next stage

Mechanics, forward evolution, `dt`, T1 and canonical-state mutation remain false. The only runtime authorization remains `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`. Maximum next-stage authorization: `AUTHORIZE_B3_GOVERNED_T0_READ_ONLY_INGEST` — read-only governed T0 ingest only; no evolution or mechanics.

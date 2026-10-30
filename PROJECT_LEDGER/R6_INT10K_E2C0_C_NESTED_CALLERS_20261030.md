# E2-C0-C — FAIR nested JSON caller attribution (2026-10-30)

STATUS: `E2_C0_NESTED_CALLERS=COMPLETE` (operator-pasted stdout from pre-existing `.pstats`); `E2_C0_REFERENCE_PARITY=PASS` remains prior y101/y501/y751 exact ordered 61-record-per-year hash oracle. This is synthetic 3×3 engineering evidence, NOT canonical World History or scientific qualification. No new simulation ran for this attribution.

FAIR source local worktree `~/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK`, commit `9dce77b5d65d4301d2145f9ad527b8efee0fe96d` (not confirmed pushed). Saved profiles `~/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E2C0_PROFILE_Piy2PjHo/PROFILE_YEAR_{101,501,751}.pstats`. Immutable 1000Y oracle `INT10K_1000Y_GEOMETRY_R1_YJBeAKT4/1000y`, manifest SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`. These source files were NOT independently mounted in this documentation session.

| Cost (cumulative ms, direct caller edges) | Y101 | Y501 | Y751 |
|---|---:|---:|---:|
| Regional `_canonical` (12 calls total) | 21.362 | 81.727 | 119.907 |
| ... called by regional `_sha` (7 calls) | 11.359 | 37.223 | 53.090 |
| ... called by `advance_region` (2 calls) | 5.056 | 21.404 | 32.093 |
| ... called by `run_regional_segment` (3 calls) | 4.947 | 23.100 | 34.725 |
| Regional `_sha` total (7 calls) | 12.188 | 40.243 | 57.465 |
| ... from `verify_regional_checkpoint` (4 calls) | 8.077 | 26.683 | 38.175 |
| ... from `seal_regional_checkpoint` (1 call) | 4.065 | 13.512 | 19.241 |
| History-free `_canonical` (12 calls) | 7.656 | 24.559 | 35.149 |
| ... called by history-free `_sha` (10 calls) | 7.609 | 24.507 | 35.098 |
| History-free `_sha` (10 calls) | 8.177 | 26.535 | 38.036 |
| ... from `verify_history_independent_checkpoint` (7 calls) | 4.137 | 13.334 | 19.114 |
| ... from `seal_history_independent_checkpoint` (3 calls) | 4.040 | 13.201 | 18.923 |
| `verify_regional_checkpoint` (2 calls; inclusive) | 15.719 | 34.405 | 45.891 |

Regional JSON encoder + direct regional decoder calls: 27.500/113.738/166.163 ms at Y101/501/751 (~34.3/56.2/59.5% of cProfile wall); additionally history-free canonical JSON ~7.656/24.559/35.149 ms. Y751 combined disjoint direct regional encoding+decoding and history-free encoding ~204.7 ms of 279.2 ms profiled (~73.3%). **Not all removable.** Caller/parent inclusive metrics overlap: do not sum `_sha`, `verify_*` and underlying `_canonical` totals together. Python cProfile adds overhead; hash-only consumer does not write JSONL.

Published parent source `regional_geological_evolution.py`: `advance_region` clones entire state via `json.loads(_canonical(dict(state)))`, emits annual complete `snapshot={..., 'cells':json.loads(_canonical(cells))}`, then `run_regional_segment` does `checkpoint_region=json.loads(_canonical(region))` **before** removing `records/snapshots/routing_events/initial_condition_events`. Even history-independent 1-year output thus copies an annual full snapshot that is discarded from the frontier. Regional integrity checkpoint is verified twice; outer history-free seal and verify also perform canonical JSON over growing state. Proof of historical storage duplication: full history ~1.916 GB, ~92.6% REGIONAL_SNAPSHOT, Y1000 snapshot 11k deposits (99.73% of snapshot bytes).

NEXT E2-C1 TEST-FIRST DESIGN: **First candidate** construct a semantically equivalent, detached checkpoint frontier without JSON-copying soon-to-be-removed history; establish field allowlist and deep-mutable isolation, exact canonical checkpoint SHA/parity and failure-mode tests before any source change. **Second** separate runtime current-state from archival full-snapshot payload using immutable/deposit-ID keyed ledger, append-only events/deltas and sparse sufficient-state checkpoints, retaining exact deposit order, composition, material provenance, mass and Deep balances. Adapter must reuse B0 `HistoryStore`, retention/replay/query and transaction/recovery APIs rather than competing store. Prove exact archive oracle parity at y0..1000/all 9 cells, 11000 final deposits, 3Y/10Y short oracles, corruption/crash tests. Do not remove integrity checks or invent UNKNOWN; no global 64-core/GPU refactoring for 9 cells. Source/physics changes and scientific/canonical production remain unauthorized by this document.

Prior reports: `PROJECT_LEDGER/R6_INT10K_E2C0_CPROFILE_PARITY_20261030.md` and `PROJECT_LEDGER/R6_INT10K_1000Y_FAIR_PERFORMANCE_E2C_E2D_HANDOFF_20261030.md`.

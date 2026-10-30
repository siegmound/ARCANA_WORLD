# R6 INT10K E2-C1 — controlled frontier projection gate (2026-10-30)

**Status:** `E2C1_GATE_PREPARED__FAIR_EXECUTION_PENDING`. This document records an executable gate package prepared in the current chat, **not** a completed FAIR execution, source commit, or scientific authorization.

## Goal / test-first operation

Replace only the history-independent checkpoint projection in `src/arcana_worldsim/r6/regional_geological_evolution.py`:
- OLD: `checkpoint_region=json.loads(_canonical(region))` then pop `records/snapshots/routing_events/initial_condition_events`.
- CANDIDATE: `checkpoint_region=json.loads(_canonical({key:value for key,value in region.items() if key not in HISTORY_KEYS}))`, then set `history_independent_continuation=True`.
- Retained fields are still canonical JSON validated and deeply detached. No change to physics, original history writer, event stream, source identity, or checkpoint digest algorithm.
- **Unresolved semantic gap:** the old clone validated even excluded historical fields, whereas the new clone does not. In the current history-free path, annual snapshots have already been validated by `json.loads(_canonical(cells))` and emitted via `history_consumer`; before a general production replacement, formally define fail-closed rules for noncanonical **excluded** history and arbitrary custom consumers. Negative test only certifies rejection of nonfinite retained state. A PASS of the bounded successful-input replay gate does NOT claim universal invalid-input behavioral equivalence.

## Runner artifact (prepared, not run on FAIR)

- Current-chat deliverable file `arcana_e2c1_fair_gate.sh`, SHA256 `388668c0741b6ad45d475091284965df7db46abb0b13f50b562b8ef55be55991`. Package ZIP (runner + README) SHA256 `da996050ef9b29f9eff85d507d204bfa3dd43e2118bd5c264b0e95b5d7853e39`.
- Files were created in the chat artifact environment, **not** copied to FAIR or uploaded into this repository. A new chat can reconstruct the bounded runner from this specification if the conversation attachment is unavailable.
- FAIR worktree precondition: `~/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK`, clean branch `r6/geometry-ulp-r1-fair` exact HEAD `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`; no extra clone. FAIR source commit had not been shown pushed to GitHub.
- Immutable 1000Y original `INT10K_1000Y_GEOMETRY_R1_YJBeAKT4/1000y`, manifest SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`. Original E0 results and all three source/checkpoint/index/history digests are checked before stage.
- Fresh output root `$HOME/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E2C1_FRONTIER_PROJECTION_XXXXXXXX`. Local *new* code branch created by gate: `r6/e2c1-frontier-projection-r1-fair`. The runner **never commits or pushes**.
- Before candidate change: 3 one-year resumptions from checkpoints 100/500/750, 7 repetitions each; verify every 61 ordered original record-kind/payload-SHA per year and capture baseline checkpoint SHA256/bytes, state SHA256, latest regional snapshot SHA256, full emitted stream digest, median wall/CPU. After candidate change: bounded regressions, 3×7 exact replays and field-by-field SHA equivalence; all source and old evidence stay unmodified.
- Regression set: `tests/test_r6_int10k_e2c1_frontier_projection.py` (new), `test_r6_int10k_history_independent.py`, `test_r6_regional_geological_evolution.py`, `test_r6_int10k_frontier_checkpoint.py`, `test_r6_int10k_full_history_oracle.py`, `test_r6_int10k_short_reference.py`, `test_r6_int10k_source_provenance.py`, `test_r6_int10k_surface_small_uplift_precision.py`. `py_compile` and `git diff --check`.
- Final expected operator marker **only after FAIR execution**: `E2C1_GATE=PASS_PARITY_SOURCE_UNCOMMITTED`; on any error `E2C1_GATE=BLOCKED_EXIT_...`, with source diff and partial output preserved. No 1000Y rerun, no 64-core or GPU load, no canonical/forward authority.

## Next decision after operator results

If exact SHA parity and targeted regressions PASS, inspect saved `PARITY_RESULT.json`, `PYTEST_RUN.log`, `SOURCE_DIFF.patch`, `FILE_MANIFEST.json`, and run/check original evidence hash; perform review of excluded-history invalid-input behavior. Only then determine whether to commit on FAIR to a new source child and run broader 3Y/10Y exact pinned-oracle qualification. Performance ratios in the report are medians from 7 repeats at each age and exclude actual full JSONL writing; no global speedup inference. The following E2-C2 historical event/delta store adapter must reuse R6 B0 `HistoryStore`, retention/replay/query, preserve all 0..1000 material history, provenance and Deep.

Original first-year FAIL, 1000Y PASS and E2-C0 profiling artifacts remain immutable. All production, GEODYN-2B forward and F2-B solver/science gates remain false.

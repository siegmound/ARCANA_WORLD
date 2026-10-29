# R6-INT10K E2-B — Versioned Frontier and Checkpoint Projection

**Decision:** `E2_B_FRONTIER_CHECKPOINT_PROJECTION_LOCAL_PASS__LEGACY_HISTORY_REQUIRED__FAIR_PENDING`
**Baseline:** `57768923a4a8478381d9153c6f910fba811613d2`
**Classification:** `NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY`

## Scope and implementation

Added `int10k_frontier_checkpoint.py`, a CLI qualification helper and adversarial tests. `FrontierV2`, `HistoryPrefixV1` and `CheckpointV2` are frozen typed wrappers around canonical UTF-8 JSON bytes. The projection verifies the existing regional and unified checkpoint envelopes, then removes regional `records`, `snapshots`, `routing_events`, `initial_condition_events` and unified `records` from the new frontier. The separate history-prefix object retains those exact arrays and event data without modifying the E2-A1 oracle or legacy checkpoint.

The frontier retains the current regional cell state/material inventory, geometry/routing/configuration/source bindings and cumulative ledgers; the unified dynamic state includes current thermal states, surface-water/material state, Maxwell reference/strain/displacement/energy memory, Deep inventories/accessibility/material-volume identities, initial-state/configuration digests, initial inventories, tolerances and cumulative balances. The checkpoint binds source identity, the E0 archive/manifest/result and per-support state hashes, configuration identity, model year, regional/unified next ordinals, a historical high-water mark and the history-reference digest. It names the future commit-chain field explicitly as `NOT_IMPLEMENTED_NO_APPEND_ONLY_CHAIN`; no transaction or append-only guarantee is claimed.

SHA256 is used for deterministic serialization integrity, not producer authentication. Parsing and restore reject unknown schema versions, missing/unknown top-level or frontier fields, bad digest, non-finite values, inconsistent identities/configuration/E0 pins, time/ordinal/high-water mismatch and incomplete or changed history. Restore requires a caller-supplied history prefix with exact coverage and matching digest. It does not reconstruct dynamic state from diagnostic snapshots. A legacy checkpoint is materialized only by explicitly reattaching those histories, after which the existing checkpoint verifiers are run.

## Source-grounded continuation blocker

The current `run_regional_segment(checkpoint=...)` sends the embedded unified checkpoint into `continue_unified_microdomain()`. That function copies `saved["records"]` into the next result/checkpoint; regional state also carries prior `records` and `snapshots`, and `query_material_provenance()` scans regional records. Current summary balances scan unified step records. Therefore the v2 frontier can be serialized without those arrays, but the compatibility bridge must reattach the complete prefix before the legacy runner can continue. It demonstrates lossless separation at the serialization boundary, **not** history-independent continuation or bounded memory.

Dynamic inventories also grow with model state. In the observed local checkpoints, stratified deposits in regional cells grew from 11 at year 1 to 33 at year 3, 55 at year 5 and 110 at year 10. Their serialized portion grew from 3,467 to 34,541 bytes (year 1 to year 10). This is state-bearing material provenance, not a duplicated year-record/snapshot list, and it remains in the frontier because the current engine needs it. Thus these measurements cannot establish size independence from elapsed time. A future E2-C/D design must determine whether material strata can be represented as current inventories plus immutable history references without changing continuation results or provenance.

## Local reference qualification

The runner consumed the preserved local Windows E2-A1 bundles and the original E0 input directory. It verified both oracle manifests and all member hashes, ran `verify_oracle()`, reverified the three E0 input hashes before/after, and required exact E0 source identity/support agreement. At each of four actual checkpoint ages it captured a v2 frontier, sealed and serialized a v2 checkpoint, restored it using the separate history prefix, and required exact equality with the original legacy checkpoint. It then continued from the restored split checkpoint and compared the complete resulting regional and unified result against the local E2-A1 `split_resumed` case using the existing E1 numeric policy (`abs=1e-8`, `rel=2e-14`) and exact structure/identity/order semantics.

| Reference | Age | Frontier bytes | Checkpoint bytes | Separate history-prefix bytes | Deposits | Restored continuation |
|---|---:|---:|---:|---:|---:|---|
| 3Y 1+2 | 1 | 181,084 | 182,458 | 139,917 | 11 | full 1+2 continuation PASS |
| 3Y 1+2 | 3 | 187,968 | 189,342 | 415,843 | 33 | exact legacy checkpoint round-trip |
| 10Y 5+5 | 5 | 194,874 | 196,248 | 705,519 | 55 | full 5+5 continuation PASS |
| 10Y 5+5 | 10 | 212,178 | 213,559 | 1,490,194 | 110 | exact legacy checkpoint round-trip |

For the synthetic checkpoint fixture with identical dynamic state and only added history rows, serialized v2 checkpoint size stayed constant while separately serialized history grew; this tests omission of those arrays but does not establish production-size independence. The real-model checkpoint growth shown above is retained, not normalized away.

The actual resumed continuation took 1.727 s wall / 1.672 s CPU for the 3-year case and 4.088 s wall / 3.938 s CPU for the 10-year case under Windows Python 3.12.10 / NumPy 2.5.1. `tracemalloc` peaks were 5,733,564 and 15,270,773 bytes. Windows process working-set observations were phase-boundary only: 52,273,152→62,619,648 bytes and 76,836,864→94,113,792 bytes respectively; these are not continuous peaks or quotas. Instrumented timing is not compared with uninstrumented E2-A1 timing.

Local external evidence directories, outside the repository:

- `../INT10K_E2_B_WINDOWS_57768923_04/3y_1plus2`, manifest SHA256 `317455655b14ce133997d2553708ec70c5afbb3681618370570d6c0ad19c77e4`, total 745,059 bytes.
- `../INT10K_E2_B_WINDOWS_57768923_04/10y_5plus5`, manifest SHA256 `9e3f7468108b9f15e06223f7f36ae4dc42a013505f8f79b8993bbeac74e23599`, total 821,068 bytes.

Every manifest member was reopened and rehashed locally. The module/CLI/physics source hashes in each `RESTORE_COMPARISON.json` were recalculated against the current local source and all matched. The runner source was untracked/modified against baseline `57768923...` at capture; the byte identities are recorded in the bundle reports, so the source commit field is the baseline commit and not a claim that this implementation was committed during execution. Earlier `_01`, `_02` and `_03` evidence directories remain preserved; `_04` is the final capture after strict history-prefix schema checks. This is local Windows evidence, not FAIR qualification. The FAIR E2-A1 run described in the preceding report section is operator-reported only and its oracle bytes were not imported or used as these local test references.

## Tests and next gate

Focused synthetic suite: **6 passed**. Combined E2-B/E2-A1/E1/regional/drainage/unified regressions: **66 passed** on Windows Python 3.12.10 / NumPy 2.5.1. `py_compile` passed for the module, CLI and tests. The combined run used a new, previously absent workspace-local `--basetemp`; default Windows `%TEMP%` could not create numbered directories and produced setup errors in 10 `tmp_path` tests, which passed with the verified local base directory. No code or output was changed to bypass that environment issue. End-to-end local qualification used the 3-year 1+2 and 10-year 5+5 references, original E0 inputs and real existing continuation kernels. No arbitrary timeout, memory, output-size or history cap is introduced.

Still absent: append-only history writer, atomic transaction/commit-chain head, restart recovery, indexed disk queries, unified-history streaming and memory-independent continuation. To qualify on FAIR without changing its existing checkout, archive the exact committed source into a new scratch directory (do not switch or update the F2AV worktree), verify source/parent, run the focused suite with a fresh scratch-local pytest base, and invoke the implemented CLI with the original verified E0 input directory, the two FAIR E2-A1 oracle bundle directories discovered under `INT10K_E2_A1_FAIR_kjB2nxDO`, and new distinct output directories under a fresh E2-B evidence root. Rehash original E0 inputs before/after and preserve the prior evidence tree. Exact CLI options are `--oracle-dir`, `--input-dir`, `--output-dir`; use two invocations for 3Y and 10Y. A missing/unverifiable oracle bundle is BLOCKED, not a fixture substitution. E2-B is **not complete** while the legacy runner requires the complete prior history. No 100-, 1,000- or 10,000-year run is authorized. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `INT10K_LONG_RUN_AUTHORIZED=false`.

# ARCANA R6 INT10K E2-C1 — FAIR gate execution report (operator log, 2026-10-30)

**Classification:** NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY. **Observed marker:** `E2C1_GATE=PASS_PARITY_SOURCE_UNCOMMITTED`. Source of this report: FAIR terminal output provided by operator; evidence files remain on FAIR and were **not independently fetched or rehashed in the GitHub documentation session**. This PASS is **limited to the test scope**; not a source seal, canonical history, scientific authority, or authorization to execute any forward/solver production.

## Provenance

- The submitted runner SHA256 was checked on FAIR: `388668c0741b6ad45d475091284965df7db46abb0b13f50b562b8ef55be55991`; original script was in `~/HPC-POMDP/Arcana/arcana_e2c1_fair_gate.sh`, not the home directory. Initial command `sha256sum ~/arcana_e2c1_fair_gate.sh` failed solely because the path was wrong.
- First run produced **`E2C1_GATE=BLOCKED_EXIT_1`** at `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E2C1_FRONTIER_PROJECTION_I4rtb1Fb`: `ModuleNotFoundError: numpy` due to nonactivated `arcana-r6-linux` Conda env. Original fail remains preserved, no mutation of source was reported before it.
- Second run activated environment `source ~/miniforge3/etc/profile.d/conda.sh; conda activate arcana-r6-linux`. **Successful evidence root:** `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E2C1_FRONTIER_PROJECTION_qLSPnKHS`.
- FAIR local base SHA: `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`, geometry source parent published `9d9a2512d5e2aca5cc3fd04010d53ac467fe9839`. Runner created local branch `r6/e2c1-frontier-projection-r1-fair` without commit. Operator's final `git status --short`:
  ```
   M src/arcana_worldsim/r6/regional_geological_evolution.py
  ?? tests/test_r6_int10k_e2c1_frontier_projection.py
  ```
- A later standalone `python - <<'PY'` produced `ModuleNotFoundError: arcana_worldsim` **after** the successful gate. Runner had exported `PYTHONPATH="$WORK/src"` only to its subprocess environment, and the invoking interactive shell does not inherit child exports. This later error is **not part of the gate's recorded PASS**; diagnose by changing directory to worktree and setting `PYTHONPATH="$PWD/src"` for standalone commands.

## Exact replay and performance (7 repeats per year)

| year | baseline median wall ms | candidate median wall ms | ratio base/new | wall-time reduction | exact stream/checkpoint/snapshot |
|---:|---:|---:|---:|---:|---|
| 101 | 68.076 | 63.457 | 1.073 | 6.8% | PASS |
| 501 | 180.835 | 163.911 | 1.103 | 9.4% | PASS |
| 751 | 257.135 | 227.452 | 1.131 | 11.5% | PASS |

**Checks printed:** `BASELINE_REFERENCE_ORACLE=PASS`, `E2C1_PATCH_APPLIED=PASS`, `76 passed in 1.38s`, `CANDIDATE_REFERENCE_ORACLE=PASS`, `E2C1_EXACT_CHECKPOINT_AND_HISTORY_PARITY=PASS`, `E2C1_GATE=PASS_PARITY_SOURCE_UNCOMMITTED`. Each stage replays the original source 1000Y checkpoints at years 100/500/750 for 1 year and checks all 61 ordered record kinds/payload hashes from the immutable 1000Y index, then compares candidate vs baseline `checkpoint_sha256`, `checkpoint_bytes`, `regional_state_sha256`, `snapshot_sha256`, emitted stream digest and count. This is bounded one-year resumption and an in-memory SHA callback, not 1000-year full-JSONL writer or planetary scale performance.

## What was changed

- Candidate only changes the **history-independent** regional checkpoint projection: before canonical JSON deep copy, exclude `records`, `snapshots`, `routing_events`, `initial_condition_events`, rather than serializing the complete region and discarding these fields after clone. Retained state still JSON validated and detached; checkpoint integrity digest and engine physics remain unchanged.
- Adds `tests/test_r6_int10k_e2c1_frontier_projection.py` with five length-parametrized canonical/detachment tests and three retained-nonfinite fail-closed tests. Existing relevant regression suites included in the reported 76 PASS.

## Open review items before source commit or science promotion

1. **Read-only FAIR evidence audit**: verify source branch/HEAD/dirty status, `FILE_MANIFEST.json` members/hash/byte-lengths, `PARITY_RESULT.json`, pytest log and source diff; verify immutable source manifest SHA `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a` unchanged. The initial BLOCKED root is preserved.
2. **Semantic nonfinite excluded history gap**: old `json.loads(_canonical(region))` fails for invalid `records`, `snapshots` and event lists **even when excluded from checkpoint**. New projection validates retained fields but not those excluded fields. The 76 tests include nonfinite retained state, **not** nonfinite excluded history. If generalized, candidate might silently accept invalid excluded-history payload from an alternate/nonvalidated event consumer. Define explicit fail-closed producer/consumer contract and add negative tests for excluded-history invalid input, without reintroducing full O(deposits×years) JSON copying. Do not claim arbitrary-invalid-input equivalence based only on successful oracle replays.
3. No commit or push of FAIR source until review and operator approval; do not pull GitHub docs blindly into FAIR branch (divergent children of published base). Do not repeat 1000Y. Next E2-C1-R2 semantic hardening/review and, only if approved, bounded 3Y/10Y oracles with exact commit; E2-C2 deposit event/delta archive remains separate.

**Authority:** `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`. R6 B0 HistoryStore/retention/query/replay should be reused for later archive work.

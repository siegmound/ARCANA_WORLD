# ARCANA R6 INT10K — E2-C1-R3 FAIR executed, positive replay + negative historical validation (2026-10-30)

**Status:** `E2C1_R3_GATE=PASS_PARITY_AND_FAIL_CLOSED_SOURCE_UNCOMMITTED` (operator-provided FAIR terminal output). This closes the **scoped R2 regression** under the tested consumer-mutated historical JSON paths; it does **not** certify all possible semantic inputs, source commit, a new scientific model, canonical world history or global performance.

## Source and evidence identity

- FAIR baseline source HEAD remains `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`, with local working branch `r6/e2c1-frontier-projection-r1-fair`. **Not committed or pushed**. Expected changes:
  ` M src/arcana_worldsim/r6/regional_geological_evolution.py`;
  `?? tests/test_r6_int10k_e2c1_frontier_projection.py`;
  `?? tests/test_r6_int10k_e2c1_r3_excluded_history_validation.py`.
- R3 runnable script SHA256 verified by FAIR operator: `8ccd9ac76ec3a47390dc77f8db1f835fa58f51c32ead56f92e401ed777006641`.
- R3 derived output: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E2C1_R3_FAILCLOSED_FFTmihHU`. R1 source/oracle proof: `INT10K_E2C1_FRONTIER_PROJECTION_qLSPnKHS`; R2 negative diagnostic `INT10K_E2C1_R2_NEGATIVE_bBw3W4k1`. Immutable original 1000Y reference `INT10K_1000Y_GEOMETRY_R1_YJBeAKT4/1000y`, manifest SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`.
- Observed logs: `E2C1_R3_BASE_AND_R2_EVIDENCE=PASS`, `E2C1_R3_ORIGINAL_SOURCE_AND_TEST=PINNED`, `E2C1_R3_PATCH_APPLIED=PASS`, `104 passed in 1.43s`, `CANDIDATE_REFERENCE_ORACLE=PASS` (before and after), `E2C1_R3_EXCLUDED_HISTORY_FAIL_CLOSED=PASS`, `E2C1_R3_EXACT_HISTORY_AND_CHECKPOINT_PARITY=PASS`, `E2C1_R3_SOURCE_AND_ORACLE_UNCHANGED=PASS`, `E2C1_R3_EVIDENCE_MANIFEST=PASS`, final gate PASS. This report only records operator output; GitHub side has not independently copied/hashes-read FAIR profile/evidence files. “Source unchanged” means committed source HEAD/original evidence unchanged; the worktree intentionally contains a patch.

## Comparative wall-time (7 repeats, resumed one-year original oracle, in-memory SHA consumer)

| Year | Original baseline median ms | R1 rerun median ms | R3 median ms | R3 wall reduction vs original | R3 cost relative to R1 rerun |
|---:|---:|---:|---:|---:|---:|
| 101 | 68.076 | 63.741 | 65.459 | 3.84% | +2.70% |
| 501 | 180.835 | 165.858 | 174.597 | 3.45% | +5.27% |
| 751 | 257.135 | 225.124 | 241.754 | 5.98% | +7.39% |

R1 rerun in R3 output is a separate measurement from initial R1 gate (63.457/163.911/227.452 ms). Results do not quantify full 1000Y writer/IO, planetary-scale physics, CPU parallelism, GPU gains or guaranteed long-run wall time. On tested inputs R3 is faster than original but slower than R1; the earlier R1 semantic regression made those R1 gains unacceptable as a general replacement.

## Mechanism and negative proof

R3 helper `_project_validated_history_free_frontier(region)` first applies existing canonical JSON `_canonical(excluded)` (encoding+validation, no decode) to `records`, `snapshots`, `routing_events`, `initial_condition_events`, then JSON canonical-encodes/decodes **only retained frontier fields**, and sets `history_independent_continuation=True`. This restores original behavior for nonfinite, non-serializable and cyclic **excluded** history under the covered paths, while avoiding unnecessary excluded-history JSON parsing and duplication.

Measured one-year y101 historical consumer injection:
- `NEGATIVE_KIND=REGIONAL_SNAPSHOT REJECTED=ValueError`
- `NEGATIVE_KIND=REGIONAL_YEAR_RECORD REJECTED=ValueError`
- `NEGATIVE_KIND=REGIONAL_EVENT REJECTED=ValueError`

Unit regressions cover all four excluded keys with NaN/+Inf/-Inf/object and cyclic containers, immutable/detached retained frontier, canonical parity. Total 104 tests PASS. Exact original 61-ordered-record replay oracle, snapshot and checkpoint hash parity at y101,y501,y751 PASS. Treat this as bounded semantics proof, not a formal proof of all input classes or future custom consumers.

## NEXT (R3-SOURCE-AUDIT, read-only; then qualification/commit decision)

1. **No automatic rerun/patch stacking.** On FAIR use existing activated `arcana-r6-linux` and repo worktree, with `PYTHONPATH=$PWD/src`; verify R3 `FILE_MANIFEST_R3.json` member hashes/lengths and its `source_files` SHA values; validate `PARITY_R3.json` status `PASS_EXACT_PARITY_AND_FAIL_CLOSED` and pytest/negative logs. Check original `MANIFEST.json` SHA and `git diff --check`, `git status --porcelain`, `git diff -- src/arcana_worldsim/r6/regional_geological_evolution.py`, `git rev-parse HEAD`. Keep original and R1/R2 derived evidence immutable.
2. Review integrity semantics: callback can mutate shared objects; validation at frontier is defensible for this scope, but requires deterministic consumer contracts, full-history retention invariants, no unknown fabrication. Verify nested cross-references and error types if generalized beyond pure JSON records.
3. After audit and reviewer approval, decide whether to **commit local R3 patch** on a dedicated child and run bounded pinned 3Y/10Y segmented oracles. The 104 PASS + 3×7 one-year oracle are necessary but not unconditional production authorization.
4. Subsequent E2-C2 will change data model to append-only event/deposit deltas + checkpoint/reader using existing R6 B0 HistoryStore and retention/replay/query; retain all time/place material/Deep/provenance and exact 0..1000 oracle reconstruction. Aim to remove quadratic archive duplication without dropping causal data. No 1000Y regeneration merely for optimization.

All gates `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`.

# R6 INT10K E2-C1 — R3 independent audit PASS, R4 3Y/10Y qualification prepared

Date: 2026-10-30. Noncanonical synthetic engineering only. Document source: FAIR stdout pasted by operator plus a reviewed source diff. Neither a new FAIR execution nor a scientific/production authorization is created by this GitHub note.

## Closed R3 audit

`E2C1_R3_INDEPENDENT_EVIDENCE_AUDIT=PASS`, `MANIFEST_MEMBERS=15`, `SOURCE_FILES=3`, `ORIGINAL_ORACLE=UNCHANGED`; `git diff --check` silent. Worktree still on `r6/e2c1-frontier-projection-r1-fair`, HEAD geometry base `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`, with exactly one modified source and two untracked tests. Earlier R3 operator PASS: 104 tests, fail-closed injection into REGIONAL_SNAPSHOT/YEAR_RECORD/EVENT, 3×7 one-year hash/checkpoint/snapshot oracle parity, R3 median 3.84%/3.45%/5.98% better than original at 101/501/751. External output `INT10K_E2C1_R3_FAILCLOSED_FFTmihHU`, 1000Y immutable manifest SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`.

Source diff independently reviewed by assistant: add `_HISTORY_EXCLUDED_FROM_FRONTIER` and `_project_validated_history_free_frontier(region)` in `src/arcana_worldsim/r6/regional_geological_evolution.py`. Helper canonical JSON-validates excluded history, canonical JSON-copies retained fields, then sets `history_independent_continuation=True`; four old lines of full-state JSON clone then popping history replaced by helper. Diff 28 lines (24 additions, 4 deletions). Physics loops, checkpoint SHA construction and retention interfaces unchanged. Source diff in stdout corroborates the planned R3 patch. The R3 helper's JSON validation does not imply formal input-semantic equivalence for all imaginable custom consumer types, only tested JSON/fail-closed cases.

## Local R3 commit decision

Reviewed R3 change and 15-member evidence audit support a **local source commit with three exact files only**, NOT a GitHub docs-branch merge or push, and NOT production qualification. Stage and review:

- `src/arcana_worldsim/r6/regional_geological_evolution.py`
- `tests/test_r6_int10k_e2c1_frontier_projection.py`
- `tests/test_r6_int10k_e2c1_r3_excluded_history_validation.py`

Use `git diff --cached --check`, `git diff --cached --name-status`, repeat selected pytest, then `git commit -m 'perf(r6): retain fail-closed validation in history-free frontier projection'`. Preserve base commit and both R2/R3 evidence roots; require clean worktree. Exact local commit SHA will be returned by FAIR and is **unknown** until operator executes. Do not invent SHA and do not push absent explicit promotion.

## R4 dedicated short history-independent oracle

Verified prepared conversation artifact `arcana_e2c1_r4_3y10y_committed_gate.py`, SHA256 `eb9ed93973c9c61911b3f56b455396fa59fd595a0f02c8de211eba84f0a1a177`, plus `ARCANA_E2C1_R4_3Y10Y_README.md` and ZIP. R4 is **NOT YET RUN on FAIR**. Python syntax checked in chat container; no run claim. Strict prereqs: branch r6/e2c1-frontier-projection-r1-fair, one clean child commit of 9dce77b5 touching exactly these 3 files, matching R3 `source_files` checksums, original 1000Y manifest SHA and INDEX.jsonl checksum.

Runs bounded 3-year direct vs 1+2 and 10-year direct vs 5+5 with `history_independent_continuation=True` using same synthetic E0 columns, source identity and RegionalConfig(duration_years=1000) as original 1000Y. Compares the ordered payload SHA256 streams **within each kind** with the original INDEX prefix, preserving undated REGIONAL_EVENT entries. Also compares direct vs segmented exact final frontier checkpoint, `subsurface_by_support` and `balances`. Verifies short-reference/regional/R3 pytest suites and that no source/original evidence mutated; writes isolated new evidence root in `.../R6/INT10K_E2C1_R4_3Y10Y_*`. **Global writer interleaving across kinds is not asserted identical** because 1000Y reference writer advanced one year per call; short multi-year orchestration orders kinds differently. `E2C1_R4_GATE=PASS_EXACT_3Y10Y_HISTORY_INDEPENDENT_ORACLE` only after actual FAIR run; any `BLOCKED` requires diagnosis without patch stacking.

Legacy `tests/test_r6_int10k_short_reference.py` already covers `(3,1)` and `(10,5)` but uses default history-in-memory path; R4 specifically closes the missing history-independent path coverage. Neither R4 nor R3 solves quadratic accumulation of duplicated regional snapshots, pending E2-C2 deposit-event/delta design reusing B0 HistoryStore and exact reconstruction oracle. No 1000Y rerun, no new clone, no 64-core or GPU claim.

All authority gates remain: WORLD_HISTORY_PRODUCTION_AUTHORIZED=false, GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false, F2B_SOLVER_EXECUTION_AUTHORIZED=false, ARCANA_SI1_MECHANICS_QUALIFIED=false.

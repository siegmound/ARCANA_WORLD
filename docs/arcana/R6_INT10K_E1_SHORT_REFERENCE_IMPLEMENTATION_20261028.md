# R6-INT10K E1 — Short direct/checkpoint reference implementation (2026-10-28)

**Status:** `R6_INT10K_E1_R1_FAIR_TESTS_PASS_OPERATOR_REPORTED__E0_HASH_RECONCILED_ON_WINDOWS__NEXT_FAIR_RETEST_PENDING`
**Source baseline:** `a33d505611d1a0d772af7503f7388cd8f4d29abb` (E1 implementation source; this report records the local correction and its verification separately from the first FAIR failure).

## First FAIR test result and correction

The operator-reported first Linux run at `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E1_TEST_dMJckvUN` compiled successfully but the test suite exited 1: **24 passed, 2 failed**. Both failures were `test_reference_direct_equals_checkpoint_split` cases `[3-1]` and `[10-5]`, reporting `SHORT_REFERENCE_COVERAGE_INVALID`. This is preserved as a FAIL; its original log was not imported or independently rehashed on Windows.

The defect was the final coverage check treating `snapshots` as one record per simulated year. The regional runner includes the initial state at year 0 and then one snapshot per year. The validator now requires `records` at years `1..years`, `snapshots` at years `0..years`, and `time_years == years`, with exact ordered sequences and fail-closed handling of malformed/missing/duplicate/out-of-order times.

Locally verified on Windows using the available Python 3.11.15 / NumPy 2.4.6 / pytest 8.4.2 environment: the E1, regional and unified focused suites passed **35/35**, zero skips, in 3.87 s. This runtime differs from the planned FAIR runtime and does not qualify Linux. No E0 input execution, E1 original-input run, or 10,000-year benchmark was performed. The corrected source requires a new exact-commit Linux qualification; no FAIR PASS is claimed.

## E1-R1 and E0 hash reconciliation update (2026-10-29)

The operator reports E1-R1 commit `a7b7d4d58d3cc545781778a985529c269a81b9b9` passed 35 Linux tests, compilation, checkout-integrity checks and hash verification of its log/JUnit in FAIR evidence `INT10K_E1_R1_TEST_3MXk3VwX`. These FAIR files were not imported or independently hashed on Windows; this is an operator-reported PASS limited to those checks.

The current Windows source pin in `scripts/r6_int10k_short_reference.py` already contains the complete manifest SHA256. Independent local hashing of the original Windows E0 triplet and transfer bundle confirmed the full identities and byte-for-byte archive-member equality; the manifest and sidecar agree with the result. The 52-character value reported as historical does not occur in the current tracked source or attestations. See `docs/arcana/R6_INT10K_E0_E1_HASH_RECONCILIATION_20261029.md` and its machine attestation. The original E0 FAIR decision is retained as historical operator-reported evidence; a fresh FAIR check of the original loader and full input triplet is required before the later supervised three-year reference. No E0 input or simulation was executed in this reconciliation.

## Implementation artifacts

- `src/arcana_worldsim/r6/int10k_short_reference.py`: bounded `ShortReferenceConfig` accepting **only 3 or 10 years**. Calls the existing `run_regional_segment` (which in turn calls unified thermomechanics/Deep and separately advances regional 3x3 annual surface) once continuously and once as checkpoint-split under the **identical fixed plan, initial states, source identity and physics configuration**. Recursively compares full regional state (including yearly records/snapshots/events/material identity), final unified subsurface state and domain balances. Numeric policy `rel_tol=2e-14`, `abs_tol=1e-8` matches existing short regional pytest; metadata/event keys and statuses exact. NaN/Inf rejected.
- `scripts/r6_int10k_short_reference.py`: Linux-only (uses `resource`) CLI with explicit `--input-dir`, `--output-dir`, `--years` (3/10 only) and `--split-at`. It validates all **three original _03 SHA256 members** before/after loading and numerical evolution, writes exclusively into a new directory under external `ARCANA_WORLD_EVIDENCE`, stores full bounded direct/split reference payload and a manifest with member SHA256. Reports walltime and peak *current process* RSS; **not** a process-tree RSS sampler. Original source and checkout are untouched by the program's code path; full before/after checkout hash checking remains an operator/supervisor responsibility.
- `tests/test_r6_int10k_short_reference.py`: synthetic 3y and 10y direct-vs-split, invalid plan/split and changed plan-identity negatives, nonfinite and event/key/numeric drift detection.

## Important boundaries and known gaps

**This is a numerical baseline, NOT the streaming engine.** The legacy algorithms retain full year/step history in RAM and full checkpoint; the 10k memory growth issue is intentionally not addressed in this commit. The short baseline provides an oracle for future compact frontier+immutable history comparison. No scientific coefficients, feedback links or original kernel files were edited. No ASPECT/ShellSet/Fastscapelib/gFlex runtime is implied. C028/C029 T0 source columns have identical input payload hashes; synthetic regional 3x3 cells do not imply independently calibrated geographical variability.

The new code and tests have **not been executed on FAIR**, and no PASS beyond E0 is claimed. Do not run `--years 10000`, do not use `--years 10` before isolated source tests and short reference 3y validation, do not move the historical F2AV checkout.

## Next validation on FAIR

1. Fetch the *exact new commit*, then use a fresh external `git archive`-extracted source snapshot, **not** the stale F2AV checkout as interpreter import root.
2. Use Python 3.12 in `arcana-r6-linux`; run `python -m py_compile` on both new Python modules and tests; `python -m pytest -q tests/test_r6_int10k_short_reference.py tests/test_r6_regional_geological_evolution.py tests/test_r6_unified_multiphysics_microdomain.py`. Capture complete terminal log and pytest JUnit into new evidence; any nonzero/skip in scoped qualifying tests BLOCKED until adjudicated.
3. Only on Linux test PASS propose bounded 3-year original-input run under external `ARCANA_WORLD_EVIDENCE` with new unique output directory, a strict supervisor runtime/output/RSS limit based on actual host/job quotas. Do not assume node `free -h` is a process entitlement.
4. Validate recorded SHA256/manifest, regional/unit/time/deep balances, direct-vs-split full history, input+worktree immutability and resource telemetry. Reassess before 10-year short reference; after both short PASS start separate `R6_INT10K_E2_FRONTIER_STREAMED_HISTORY` design. No 10k execution authorized by this implementation.

**All gates unchanged**: `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, plus all experiment-specific execution prohibitions. The scientific provider gap matrix remains parallel and open.

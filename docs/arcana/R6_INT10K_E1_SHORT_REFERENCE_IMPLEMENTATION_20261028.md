# R6-INT10K E1 — Short direct/checkpoint reference implementation (2026-10-28)

**Status:** `R6_INT10K_E1_3_AND_10_YEAR_FAIR_REFERENCE_PASS_OPERATOR_REPORTED__E2_STREAMING_CONTRACT_PREPARED`
**Source baseline:** `a33d505611d1a0d772af7503f7388cd8f4d29abb` (E1 implementation source; this report records the local correction and its verification separately from the first FAIR failure).

## First FAIR test result and correction

The operator-reported first Linux run at `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E1_TEST_dMJckvUN` compiled successfully but the test suite exited 1: **24 passed, 2 failed**. Both failures were `test_reference_direct_equals_checkpoint_split` cases `[3-1]` and `[10-5]`, reporting `SHORT_REFERENCE_COVERAGE_INVALID`. This is preserved as a FAIL; its original log was not imported or independently rehashed on Windows.

The defect was the final coverage check treating `snapshots` as one record per simulated year. The regional runner includes the initial state at year 0 and then one snapshot per year. The validator now requires `records` at years `1..years`, `snapshots` at years `0..years`, and `time_years == years`, with exact ordered sequences and fail-closed handling of malformed/missing/duplicate/out-of-order times.

Locally verified on Windows using the available Python 3.11.15 / NumPy 2.4.6 / pytest 8.4.2 environment: the E1, regional and unified focused suites passed **35/35**, zero skips, in 3.87 s. This runtime differs from the planned FAIR runtime and does not qualify Linux. No E0 input execution, E1 original-input run, or 10,000-year benchmark was performed. The corrected source requires a new exact-commit Linux qualification; no FAIR PASS is claimed.

## E1-R1 and E0 hash reconciliation update (2026-10-29)

The operator reports E1-R1 commit `a7b7d4d58d3cc545781778a985529c269a81b9b9` passed 35 Linux tests, compilation, checkout-integrity checks and hash verification of its log/JUnit in FAIR evidence `INT10K_E1_R1_TEST_3MXk3VwX`. These FAIR files were not imported or independently hashed on Windows; this is an operator-reported PASS limited to those checks.

The current Windows source pin in `scripts/r6_int10k_short_reference.py` already contains the complete manifest SHA256. Independent local hashing of the original Windows E0 triplet and transfer bundle confirmed the full identities and byte-for-byte archive-member equality; the manifest and sidecar agree with the result. The 52-character value reported as historical does not occur in the current tracked source or attestations. See `docs/arcana/R6_INT10K_E0_E1_HASH_RECONCILIATION_20261029.md` and its machine attestation. The original E0 FAIR decision remains historical. At the time of the Windows reconciliation, a fresh FAIR loader/input check was pending; the operator now reports that E1-R2 completed the loader, full input and source-identity checks at `5faf619875af86caa2ee824dff4b0a833f4227f1`. Those FAIR artifacts were not imported or independently rehashed on Windows. No E0 input or simulation was executed during the Windows reconciliation itself.

## E1-R2 FAIR results (operator-reported, 2026-10-29)

All results below were supplied by the operator and have not been imported or independently rehashed on Windows. They are bound to exact source commit `5faf619875af86caa2ee824dff4b0a833f4227f1`.

| Gate | Reported outcome | Runtime/output measurements |
|---|---|---|
| E1-R2 Linux regressions and E0 loader/source identity | 45/45 PASS; loader, input and source identity PASS | Evidence locator and test-log digest were not supplied for E1-R2 |
| Original-input reference, 3 years split 1+2 | PASS; `FINAL_EXIT=0`; historical checkout and inputs unchanged | Evidence `INT10K_E1_ORIGINAL_3Y_tSMeQrAp`; 407,197 output bytes; RSS 47,239,168 bytes; internal wall 0.0927017 s |
| Original-input reference, 10 years split 5+5 | PASS; `FINAL_EXIT=0`; historical checkout and inputs unchanged | Evidence `INT10K_E1_ORIGINAL_10Y_pyPsEG4V`; manifest SHA256 `29f30841735848482676a7dad01a377774d591eeaf7b667e89310e87e01b73c7`; 1,316,936 output bytes; RSS 57,716,736 bytes; internal wall 0.2426114 s; process wall 0.46 s |

At 10 years, the reported water balances passed. Maximum absolute solid residual was 0.00048828125 kg against the reported 0.03125 kg tolerance. Deep total residual was 0 J; gross internal transport was 38,795,203,049.11111 J. These are engineering-run observations, not a physical or scientific qualification. Detailed 3-year balance values and the 3-year manifest digest were not supplied and remain UNKNOWN here.

E1-R2 closes the operator-reported 3/10-year baseline stage. It does not qualify 100-, 1,000- or 10,000-year execution, streaming, bounded long-run memory, scientific representativeness or canonical history. The earlier first-run E1 FAIL (24 passed, 2 failed) and its exact evidence remain preserved.

## Implementation artifacts

- `src/arcana_worldsim/r6/int10k_short_reference.py`: bounded `ShortReferenceConfig` accepting **only 3 or 10 years**. Calls the existing `run_regional_segment` (which in turn calls unified thermomechanics/Deep and separately advances regional 3x3 annual surface) once continuously and once as checkpoint-split under the **identical fixed plan, initial states, source identity and physics configuration**. Recursively compares full regional state (including yearly records/snapshots/events/material identity), final unified subsurface state and domain balances. Numeric policy `rel_tol=2e-14`, `abs_tol=1e-8` matches existing short regional pytest; metadata/event keys and statuses exact. NaN/Inf rejected.
- `scripts/r6_int10k_short_reference.py`: Linux-only (uses `resource`) CLI with explicit `--input-dir`, `--output-dir`, `--years` (3/10 only) and `--split-at`. It validates all **three original _03 SHA256 members** before/after loading and numerical evolution, writes exclusively into a new directory under external `ARCANA_WORLD_EVIDENCE`, stores full bounded direct/split reference payload and a manifest with member SHA256. Reports walltime and peak *current process* RSS; **not** a process-tree RSS sampler. Original source and checkout are untouched by the program's code path; full before/after checkout hash checking remains an operator/supervisor responsibility.
- `tests/test_r6_int10k_short_reference.py`: synthetic 3y and 10y direct-vs-split, invalid plan/split and changed plan-identity negatives, nonfinite and event/key/numeric drift detection.

## Important boundaries and known gaps

**This is a numerical baseline, NOT the streaming engine.** The legacy algorithms retain full year/step history in RAM and full checkpoint; the 10k memory growth issue is intentionally not addressed in this commit. The short baseline provides an oracle for future compact frontier+immutable history comparison. No scientific coefficients, feedback links or original kernel files were edited. No ASPECT/ShellSet/Fastscapelib/gFlex runtime is implied. C028/C029 T0 source columns have identical input payload hashes; synthetic regional 3x3 cells do not imply independently calibrated geographical variability.

E1-R2 FAIR PASS is operator-reported as above. Its output bundles and logs are not independently available in this Windows worktree. No streaming implementation exists; the legacy path retains history in memory. Do not run `--years 10000`, do not alter the historical F2AV checkout, and do not infer future resource behavior from the 3- and 10-year measurements.

## Next step — E2 frontier/history streaming contract

The source review and proposed contract are in `docs/arcana/R6_INT10K_E2_FRONTIER_HISTORY_STREAMING_CONTRACT.md`. Before implementation acceptance can claim complete E1 history parity, preserve or produce an authorized reference that includes unified per-step records and the internal split checkpoint: the current E1 result serializes full regional history, unified final state, and aggregate balances, but not unified `steps` or the intermediate checkpoint object. The E2 contract requires coverage of those fields, events, residuals and exact historical queries, plus fault/recovery cases. No simulation was executed for this document update and no 100/1,000/10,000-year run is authorized.

**All gates unchanged**: `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, plus all experiment-specific execution prohibitions. The scientific provider gap matrix remains parallel and open.

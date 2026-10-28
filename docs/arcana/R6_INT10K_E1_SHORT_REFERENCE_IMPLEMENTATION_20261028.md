# R6-INT10K E1 — Short direct/checkpoint reference implementation (2026-10-28)

**Status:** `R6_INT10K_E1_SHORT_REFERENCE_CODE_STAGED__LINUX_TEST_PENDING`  
**Parent source baseline:** `33600f05714168051970c79703bd06d30526f73f` (E0 input qualified by operator-reported FAIR log); this implementation is new and **not yet Linux-tested**. No new engine execution occurred in this GitHub update.

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

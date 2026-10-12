# NEXT — INT-0B bounded failure correction

**Current decision (2026-10-13):** `INT0B_FAILED_PRE_OUTPUT_VALIDATION`. The one authorized local attempt on `683230f5e66397478642c2b8a48550eb1d00cca7` exited 1 after 25.427 seconds at `scripts/r6_functional_development_t_f2b.py:114`: `zip(times, times[1])` uses a scalar float instead of the remaining sequence. No candidate artifacts or candidate manifest were written. Failure records are preserved under `outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01/`; review `docs/arcana/INT0B_EXECUTION_REPORT.md`.

## One bounded next task

Correct the sample ordering comparison to use the remaining sequence and add a focused regression for strictly increasing sampled times, including the scalar-slice regression. Run only the focused offline tests, `py_compile`, and `git diff --check`; do not launch the T-F2B trajectory as part of that correction.

The previous conditional approval covered exactly one trajectory attempt and is consumed. A new explicit authorization is required before any subsequent engineering execution. Do not overwrite or reuse the failure-evidence directory. If a future run is authorized, it must use a fresh absent output destination and the same provider/source/resource preflight.

## Preserved gates

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

No Fair, MPI, ShellSet, Solver, DGBSV, post-rift evolution, canonical publication, or WORLD_HISTORY access/write.

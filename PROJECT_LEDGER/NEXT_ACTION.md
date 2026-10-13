# NEXT — INT-0B-R1 new-run authorization pending

**Current code decision (2026-10-13):** `INT0B_R1_RUNNER_VALIDATION_CORRECTED__REEXECUTION_PENDING_AUTHORIZATION`. The original attempt remains `INT0B_FAILED_PRE_OUTPUT_VALIDATION`; its report and evidence are immutable. The correction and regression are recorded in `docs/arcana/INT0B_R1_RUNNER_CORRECTION.md`.

## One bounded next task

Obtain a separate, explicit authorization for one new local noncanonical INT-0B attempt. The previous one-run authorization is consumed. Do not start the trajectory before that authorization.

Proposed new output path, checked absent on 2026-10-13:

`outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_02`

Proposed command (only after authorization and fresh preflight):

```powershell
$env:ARCANA_EXTERNAL_ROOT = 'F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES'
$env:PYTHONPATH = 'C:\Users\jose_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages;src'
python scripts/r6_functional_development_t_f2b.py --repository-root . --expected-branch r6/si1-bandwidth-f2av --output-relative outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_02
```

Before any future run, verify final branch/HEAD and tracked tree; rerun the provider-backed audit on the final correction commit, record its HEAD-bound composite identity, confirm Python 3.12.10 / NumPy 2.3.5 and `ARCANA_EXTERNAL_ROOT`, recheck `_02` absence, and validate a foreground supervisor recording PID/image, process tree, elapsed time, working set, output size, exit and stop reason. Limits remain 900 seconds, 2 GiB working set and 512 MiB output, monitored thresholds rather than hard OS isolation. No automatic retry; preserve partial evidence under the fresh path.

Scientific configuration remains unchanged from the approved proposal: T-F2B pair 5:11, T0 210 Ma, 1,000 engineering years, frozen Euler forcing, resolutions 0.001 / 0.0005 / 0.00025 and diagnostics at the middle resolution. No trajectory was run during R1. INT-1 remains blocked until a future separately authorized attempt completes and passes validation.

## Preserved gates and prohibitions

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

No Fair, MPI, ShellSet, Solver, DGBSV, post-rift evolution, canonical publication, or WORLD_HISTORY access/write.

# INT-0B attempt report — failed before candidate artifacts

Date: 2026-10-13
Branch: `r6/si1-bandwidth-f2av`
Source HEAD: `683230f5e66397478642c2b8a48550eb1d00cca7`
Parent: `dde79ebe4d26ab7b21eff08245fc83330239c0bc`

## Decision

`INT0B_FAILED_PRE_OUTPUT_VALIDATION`

One execution attempt was made, as authorized. It exited with code 1 after 25.427 seconds. No retry was made. The intended 1,000-year T-F2B computation reached the sample-order validation but failed before candidate artifacts or a candidate manifest were written. Therefore no trajectory, numerical findings, endpoint validation, or replay/restart result is available for independent review.

## Preconditions and command

The local branch, HEAD, parent, and tracked worktree matched the authorized values. The read-only provider audit was rerun against that HEAD and passed. It returned source identity `470e74a0d2b2f504576d6d4a49f53a7866efa0174a6640a4d72cdea7038f6c6c`, field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`, binding index `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00`, vector partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`, and event census `e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e`. Selection remained boundary `R6BND-T0-3eb57747e6f0a3f3305f`, pair 5:11, edge row 91/column 28/EAST. The audit reported no canonical state change and no WORLD_HISTORY access/publication.

Python was 3.12.10, NumPy 2.3.5, and `ARCANA_EXTERNAL_ROOT` pointed to the governed `_ARCANA_EXTERNAL_SOURCES` root. The approved output destination was absent immediately before launch.

The executed command was exactly:

```powershell
python scripts/r6_functional_development_t_f2b.py --repository-root . --expected-branch r6/si1-bandwidth-f2av --output-relative outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01
```

## Failure and observed resources

At `scripts/r6_functional_development_t_f2b.py:114`, the sample-order check calls `zip(times, times[1])`. `times[1]` is a scalar float; Python raises `TypeError: 'float' object is not iterable`. The intended sequence comparison must use a slice, but no source correction or second execution is included in this result.

The failure occurred before output-directory creation, endpoint checks, deterministic replay/restart, serialization, and manifest generation. The candidate manifest is absent. Numerical state values computed earlier in process memory were not persisted and are not claimed as verified results. No output samples, final-state consistency, replay/restart, or candidate invariants can be adjudicated from this attempt.

The foreground PowerShell 7.6.6 supervisor sampled the Python process every 250 ms. It observed elapsed time 25.427 s, peak sampled process working set 4,509,696 bytes, peak candidate output 0 bytes, 97 monitoring iterations, and natural exit code 1. No resource limit was reached and the supervisor did not terminate this run. A separate harmless sleeper test confirmed `Process.Kill(true)` terminates a process tree; the configured run supervisor used this capability if a limit were crossed, but no termination call was needed for this naturally exiting process. A first `taskkill /T` probe failed in this environment. These are sampled observations, not hard OS resource isolation. Run timestamps and PID were not retained.

## Preserved attempt evidence

Failure evidence is stored under:

`outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01/`

It contains `ATTEMPT_FAILURE.json`, `RUNNER_STDOUT.txt` (empty), `RUNNER_STDERR_TRANSCRIPT.txt`, and `FAILURE_EVIDENCE_MANIFEST.json`. The stderr file is explicitly a transcript transcribed from the supervisor output; it is not represented as a re-read of the redirected temporary log. The failure manifest covers the three evidence members and does not represent the absent candidate-run manifest. Its SHA256 is recorded in `PROJECT_LEDGER/EVIDENCE_INDEX.md`.

The scientific run produced no usable trajectory and does not meet the successful INT-0B verdict. This was an engineering computation attempt only; it provides no scientific qualification or promotion authority.

## Next action

Correct the sample-order slice defect and add a focused regression that fails on the scalar form. Review and validate the correction without running the engineering trajectory. The authorized one-attempt allowance has been consumed; any subsequent execution requires a new explicit bounded authorization. Do not reuse or overwrite this failure-evidence directory.

## Gates

`BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` remain unchanged. No Fair, MPI, ShellSet, Solver, DGBSV, canonical publication, or post-rift evolution was performed.

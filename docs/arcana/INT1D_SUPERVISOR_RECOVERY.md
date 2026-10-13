# INT-1D Supervisor Recovery

Date: 2026-10-14

Repository: `siegmound/ARCANA_WORLD`

Branch: `r6/si1-bandwidth-f2av`

Recovery baseline: `54c0cce119da9e061545792840f9b7c430159c7c`

## Preserved `_01` launch failure

The failed supervisor evidence remains unchanged at `outputs/r6_functional_development/INT1D_SUPERVISION_20261014_01/`:

| Artifact | SHA256 |
|---|---|
| `INT1D_LAUNCH_FAILURE.json` | `5bcbf21abdd0f09a362b784808dad2cc1b19add350168aad10a74ebe647b40a6` |
| copied `INT1D_SUPERVISOR_LAUNCHER.ps1` | `8541230c6b6e96fd6f3ffd9ba311bf6381b0592018c85871a54e5f4c176b67db` |

The recorded error was that .NET resolved `run.ndjson.stdout.log` relative to its current directory, which differed from PowerShell's repository location. The record reports `process_start_called=false`, `numerical_runner_started=false`, no candidate output, no trace files, no process measurements, and null exit code. The earlier provider audit and provider-dependent tests passed; the supervisor self-test passed; the actual launch failed before Python started. No numerical trajectory or execution resource measurement resulted. The earlier blocked-provider report remains an accurate historical account of that different environment and time.

## Recovery implementation

In `scripts/r6_int0b_supervisor.ps1`, repository-relative output paths are normalized against the verified absolute repository root; evidence paths are likewise root-bound (or preserved as explicit absolute paths). `Invoke-Monitored` now passes the repository root as the child's working directory and uses absolute trace/stdout/stderr destinations. Trace and stream files use create-new semantics so an existing file is not overwritten.

Run configuration accepts the complete INT-1D override tuple only: the exact boundary selector plus additional and diagnostic resolution factors. The factors must parse as finite positive values and match. An incomplete/inconsistent tuple fails before run-directory creation. With no overrides, the legacy R4 arguments and label remain unchanged. ProviderAudit now requires and forwards an explicit requested boundary ID, then verifies requested and selected IDs in the audit result.

`VerifyRun` computes and reports the exact command, environment configuration, working directory, fresh output/evidence paths, and monitor thresholds without starting the numerical runner or creating either destination. It is a command-plan check; the separate supervisor self-test exercises the real child launch, environment sanitation, process-tree monitoring, termination, exit propagation and stream capture.

## Offline verification

The targeted PowerShell integration tests ran with PowerShell location set to the repository while `.NET Environment.CurrentDirectory` was deliberately set to a different temporary directory. They verify that trace, stdout and stderr paths stay in the evidence directory, INT-1D arguments and the exact boundary are propagated, incomplete/inconsistent overrides are rejected, legacy R4 defaults are retained, and command verification creates no output.

With `ARCANA_EXTERNAL_ROOT=F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES`, and the configured Python path/PYTHONPATH, the supervisor/environment and provider-dependent spatial-support suites completed: **19 passed, 0 failed, 0 skipped** using Python 3.12.10, NumPy 2.3.5 and pytest 9.1.1. The supervisor self-test's child probe validates the same Python/NumPy versions, root, PYTHONPATH and sanitized Git object environment. The initial run without `ARCANA_EXTERNAL_ROOT` failed at the expected provider gate and is not counted as a passing run.

## Final-source gate and conditional execution

The tests above do not replace the required provider audit on the final committed recovery source. Before using the existing conditional authorization, run ProviderAudit with the exact requested boundary `R6BND-T0-27e4d497530e681071fb`, recompute the HEAD-bound source composite, verify all governed hashes, both 73-node admitted profiles/material bindings and frozen Euler forcing, and repeat the relevant provider tests on that committed source.

Only after all source, provider, environment, command, path-absence and active-monitor gates pass may the one authorized run use these fresh paths:

- Candidate: `outputs/r6_functional_development/INT1D_TF2B_5_11_R094C025_C026_20261014_02`
- Supervisor: `outputs/r6_functional_development/INT1D_SUPERVISION_20261014_02`

The command remains pair 5:11, T0=210 Ma, 1,000 engineering years, unchanged frozen Euler forcing and reduced thermal kernel, factors 0.001/0.0005/0.00025/0.000125, diagnostic sample factor 0.000125 and checkpoint/replay factor 0.0005. Monitor for 900 seconds, 2 GiB sampled process-tree working set and 512 MiB cumulative output. These are monitored thresholds, not hard OS quotas. Exactly one attempt is authorized; no retry. A preflight or execution failure must be preserved and terminate this gate.

No new evolution is claimed in this report revision. No Fair, MPI, ShellSet, Solver, or `WORLD_HISTORY` operation occurred. Existing scientific and canonical gates remain unchanged. A successful future trajectory would remain noncanonical engineering evidence and would not qualify a general retention policy or authorize scientific promotion.

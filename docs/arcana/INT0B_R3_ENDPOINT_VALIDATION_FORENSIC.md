# INT-0B-R3 — endpoint validation forensic correction

Date: 2026-10-13
Scope: offline source diagnosis, synthetic regression, and supervisor metadata correction.
Decision: `INT0B_R3_ENDPOINT_VALIDATION_CORRECTED__REEXECUTION_NOT_AUTHORIZED`.

## Preserved failed attempt

The third and final authorized attempt remains `INT0B_R2_THIRD_ATTEMPT_FAILED_DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH`, run from source HEAD `311550d4402f6c2fac422eac1c7f1eed46c58c64`. Its report `docs/arcana/INT0B_R2_THIRD_ATTEMPT_FAILURE.md` and supervision artifacts remain unchanged. The process exited naturally with code 1 after 22.190863 seconds; the sampled process-tree working set peak was 151,773,184 bytes, sampled output was 0 bytes, and no candidate trajectory was persisted. There is no byte-preserved diagnostic sample payload or stderr transcript from which to recover the actual in-memory endpoint values. This report does not manufacture either.

The run did execute the configured numerical calculations in memory before validation failed. It did not complete replay/restart, write a trajectory manifest, or produce usable INT-1 samples. No fourth evolution attempt is authorized.

## Root cause and first mismatch

The old validator's endpoint field sequence was `time_s`, `elapsed_years`, `width_m`, `crust_m`, `lithosphere_m`, `beta`, `accumulated_strain`, `material_coordinate`, and `temperature_k` (`scripts/r6_functional_development_t_f2b.py`, historical HEAD `311550d`, `_DIAGNOSTIC_ENDPOINT_FIELDS` and `_validate_diagnostic_sample_sequence`). `ReducedState.payload()` in `src/arcana_worldsim/r6/functional_development.py` contains `time_s` and the physical state, but not `elapsed_years`. By contrast, the state observer in `src/arcana_worldsim/r6/int0a_pipeline.py:capture_numerical_step_samples` derived that field as `state.time_s / SECONDS_PER_YEAR`.

The first old comparison therefore failed at **`elapsed_years` because the final-state payload lacked that key**. This is a producer/consumer schema mismatch, not evidence of a numerical discrepancy. `time_s` was present before that field in the old comparison order. The expected elapsed value is derived from the final state's `time_s` using the canonical `SECONDS_PER_YEAR = 31,557,600.0`; the actual attempted run's sampled endpoint number was not persisted, so its bit pattern and numeric difference are unknown. The failure message's trailing `0` is the support index, not a sample timestamp.

The failure-before/fix-after fixture uses one `ReducedState` as the source of both the endpoint record and final payload. It confirms that the historical required-key predicate first fails on `elapsed_years`, while the corrected exact derivation check accepts `endpoint.elapsed_years == final_state.time_s / SECONDS_PER_YEAR`. It does not replay or reconstruct the failed run.

## Offline correction

- The diagnostic observer records compact evolving fields for intermediate steps and replaces only the last sample with a complete `ReducedState.payload()` endpoint. This avoids duplicating per-node material dictionaries at every sample while retaining a full exact final-state comparison. Every record carries explicit `support_id`, `record_type`, and derived `elapsed_years`. The enclosing artifact schema is now `ARCANA_R6_TF2B_NUMERICAL_STEP_SAMPLES_V2` because the record shape has expanded.
- The runner rejects missing/mismatched support identifiers, nonfinite or non-increasing times, invalid array cardinalities, inconsistent derived elapsed time or depth, and any exact endpoint difference in the complete final-state payload. It checks support-key and final-state cardinalities before pairing them.
- No tolerance was added. No equation, forcing, timestep, resolution, provider input, or endpoint value was changed.
- `DiagnosticSampleValidationError.diagnostic_record()` prepares structured noncanonical failure metadata: support, validation phase, first mismatching field, expected/observed summaries (with binary64 `float.hex()` for finite scalars), absolute/relative scalar differences where defined, first differing array index, source/configuration identity slots, exit code, and stop classification. Its explicit classification is `NONCANONICAL_FAILURE_DIAGNOSTIC_NOT_TRAJECTORY`. The historical run has not been retroactively given such a record; the helper does not claim to capture or authenticate source identity by itself.

## Supervisor correction

In `scripts/r6_int0b_supervisor.ps1`, when a process-tree snapshot omits the root, the supervisor now refreshes the tracked `Process` object and checks `HasExited` before declaring `MONITOR_ROOT_IDENTITY_LOST`. Natural exit continues through wait/exit-code collection. The summary adds a separate `termination_classification` for natural success, natural nonzero exit, monitored resource termination, process identity loss, monitor error, and descendant cleanup. The run label is changed from stale `INT0B_R1_SINGLE_ATTEMPT` to `INT0B_R2_THIRD_FINAL_ATTEMPT`.

The synthetic supervisor self-test exercises both an intentionally omitted root after natural exit and an omitted root while its process remains alive; the latter is terminated and classified as identity loss. These are local process-supervisor tests only.

## Verification

Focused offline command, using Windows Python 3.12 and a fresh writable pytest base directory:

```text
python -m pytest -q --basetemp <fresh-writable-temp> tests/test_r6_functional_development_t_f2b_samples.py tests/test_r6_int0a_pipeline.py tests/test_r6_int0b_supervisor_environment.py tests/test_r6_functional_development.py
```

Result: **62 passed, 0 failed, 0 skipped**. The supervisor regression ran its bounded synthetic child-process tests; no provider-backed evolution was invoked. `py_compile` and `git diff --check` also passed. The PowerShell 7 self-test covers sanitized environment, resource stops, natural nonzero exit during the missing-root snapshot race, and a still-live process identity-loss path. No separate operator-interrupt mechanism is claimed; an external termination of the supervisor itself may not emit a completed summary.

The first test attempt exposed a pytest temporary-directory location problem: placing `--basetemp` inside the checkout caused an existing bundle-safety fixture to reject its output as overlapping the protected repository root. The completed run used a fresh writable temporary directory outside the checkout and removed that task-created directory afterward; it did not modify the existing `outputs/` evidence.

## Limits and gates

The previous attempt's numerical endpoint values, resolution comparison, output integrity, replay/restart, and full trajectory remain unavailable. UTF-8/LF and whitespace inspection passed for the changed text files; the existing PowerShell script is normalized to LF. The supervisor limits are sampled operational thresholds, not OS-enforced quotas. The structured failure record is a helper for future authorized execution and does not make a trajectory artifact. A new experiment requires separate explicit authorization and a new output directory.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. INT-1 remains blocked without a complete validated trajectory. No ShellSet, Fair, MPI, Solver, DGBSV, canonical publication, or WORLD_HISTORY operation was performed.

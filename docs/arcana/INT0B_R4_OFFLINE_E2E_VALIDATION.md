# INT-0B-R4 — offline integration validation and fourth-run preparation

Date: 2026-10-13
Scope: synthetic integration regression, output-bundle readback hardening, and supervisor test/preparation only.
Decision: `INT0B_R4_OFFLINE_E2E_VERIFIED__FOURTH_RUN_PENDING_AUTHORIZATION`.

## Boundary and preserved attempts

This gate did not execute provider-backed T-F2B evolution. The three prior attempts remain distinct, immutable failure evidence:

| Attempt | Outcome | Preserved evidence |
|---|---|---|
| `_01` | `INT0B_FAILED_PRE_OUTPUT_VALIDATION` (original runner `TypeError`) | `outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01/` and its failure manifest/transcripts |
| `_02` | `INT0B_R1_SECOND_ATTEMPT_FAILED_PRE_OUTPUT_VALIDATION_GIT_OBJECT_ENV_REINSERTED` | `docs/arcana/INT0B_R1_SECOND_ATTEMPT_FAILURE.md` and `outputs/r6_functional_development/INT0B_R1_SUPERVISION_20261013/` |
| `_03` | `INT0B_R2_THIRD_ATTEMPT_FAILED_DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH` | `docs/arcana/INT0B_R2_THIRD_ATTEMPT_FAILURE.md` and `outputs/r6_functional_development/INT0B_R2_SUPERVISION_20261013_RUN/` |

R3 corrected the endpoint schema comparison and monitor exit-race classification, but did not authorize another evolution. R4 adds offline evidence only; it does not reinterpret any failure as a successful trajectory and does not make INT-1 available.

## End-to-end coverage

The earlier focused suite tested observer capture, runner endpoint validation, replay/restart, trajectory construction, and a generic candidate-bundle writer in separate tests. It did not connect those production functions in one synthetic path or exercise the full runner's artifact writer. The added `test_synthetic_observer_validation_replay_and_candidate_manifest_end_to_end` now performs that bounded connection using `SYNTHETIC_FIXTURE_ONLY` profiles and a one-year synthetic interval:

1. Calls the existing reduced kernel's `capture_numerical_step_samples` for both fixture supports.
2. Checks exact support identities, sample count against kernel substeps, strict time ordering, compact intermediate records (no repeated `materials`), complete endpoint record, and derived `elapsed_years`.
3. Calls the runner's production `_validate_diagnostic_sample_sequence` for each endpoint and proves a changed endpoint is rejected.
4. Uses the production `_diagnostic_samples_document` and strict `_canonical_bytes` serializer; confirms deterministic JSON round-trip.
5. Runs deterministic replay and a split/checkpoint/restore/restart twice, comparing the restart payloads exactly within this fixture contract.
6. Builds a candidate trajectory with the production `trajectory_document` and writes diagnostic samples, trajectory, run result and manifest through the same `_write_candidate_output_bundle` used by `main()`.
7. Verifies the actual write order places `CANDIDATE_MANIFEST.json` last, exact output membership, readback bytes, each listed length/SHA256, the manifest SHA256, and refusal to overwrite the destination.

The helper writes each file, checks its byte count and readback before moving on, writes `RUN_RESULT.json`, then writes and reads back the manifest last. It retains only per-file hashes and sizes, not serialized copies of the entire bundle. Partial output on any error remains non-authoritative. This is synthetic Python evidence; it is not a provider-backed run, an independent runtime, or a physical qualification. Existing test coverage separately verifies the generic protected-root writer and restart/replay semantics.

## Diagnostic sample size and output budget

The production compact intermediate record has 12 top-level fields: seven scalar values (including `elapsed_years`), three 73-element arrays (`material_coordinate`, `z_m`, `temperature_k`), `support_id`, and `record_type`. The endpoint has 22 top-level fields and includes the complete material payload. Each support is bounded at 10,001 records including its initial sample: at most 20,002 total records for the two-support case.

The bounded one-year synthetic test fixture (three nodes/support, two samples/support) serialized its `DIAGNOSTIC_NUMERICAL_SAMPLES` document to **5,474 bytes** with the production canonical serializer. This is an observed fixture artifact size, not a projection for the 73-node case.

The earlier `INT0B_PROVIDER_PREFLIGHT.md` count of 226 numeric entries “per record” does not account for the full endpoint material array. A type-aware count is 226 numeric entries in each compact record and 518 in each full endpoint (the 226 state entries plus four numeric fields for each of 73 materials), totaling 4,521,036 numeric entries at the sample cap. This small correction does not change any physical input or sample limit.

A reproducible serialization stress calculation used the production sample record builder and canonical serializer, 73-element arrays, maximum finite binary64 decimal spelling, 10,000 intermediate records plus one endpoint for each support, and an 8-byte-per-line nesting/separator allowance. It estimates **179,442,031 bytes** (about **171.1 MiB**) for the diagnostic sample JSON alone. This is a calculated synthetic upper estimate under the stated schema and value-width assumptions, not an observed run artifact or memory measurement. The older 333,657,599-byte estimate in the provider preflight is retained as a more conservative planning figure; it is about 318.1 MiB and leaves about 203.2 MiB below 512 MiB for the other candidate files and captured streams. The sample cap causes the observer to fail closed if exceeded.

Thus the 512 MiB output ceiling appears sufficient for the bounded serialized sample artifact under the fixed two-support/73-node/10,001-sample contract, with the older estimate as the planning reserve. It is still a monitored operational threshold, not a hard quota. Actual total bundle size, actual sample count, polling overshoot and runtime output remain unknown until a separately authorized attempt; the supervisor includes candidate files plus captured stdout/stderr in its sampled cumulative-output measurement.

## Supervisor verification and diagnostic streams

The existing Windows PowerShell 7 self-test already exercised PID/descendant discovery, tree termination, sampled working-set and output limits, natural exit code 0, natural nonzero exit, exit during the snapshot race, process-identity loss, and sanitized Git object-directory environment. R4 adds explicit stdout/stderr redirection to raw log files beside each trace, byte counts and SHA256 in the returned summary, and a synthetic nonzero stderr check. Captured stdout/stderr bytes are included in the same cumulative-output polling threshold. A separate synthetic stream-volume case verifies that output emitted to stdout triggers the configured output stop. The regression also rejects the stale R1 run label and checks the prepared R4 label in source.

The monitored thresholds remain sampled, not OS-enforced. Polling can overshoot by one sampling interval plus scheduling and termination time. The self-tests do not demonstrate hard resource isolation or protection from termination of the supervisor itself. Future run stderr is preserved in the evidence directory even when the numerical runner exits nonzero.

## Offline verification

Focused command, on the configured Windows Python 3.12.10 with the bundled NumPy 2.3.5 path and a fresh pytest base outside the checkout:

```powershell
python -m pytest -q --basetemp <fresh-writable-temp> `
  tests/test_r6_functional_development_t_f2b_samples.py `
  tests/test_r6_int0a_pipeline.py `
  tests/test_r6_int0b_supervisor_environment.py `
  tests/test_r6_functional_development.py `
  tests/test_r6_functional_spatial_support.py
```

Final result: **70 passed, 0 failed, 0 skipped**. A preceding iteration found and corrected a test-harness serialization-shape issue in the supervisor self-test while adding stream capture; the final run above includes that correction. `py_compile`, UTF-8/LF, whitespace, and `git diff --check` are required before commit. No provider-backed preflight or evolution is part of this test result.

## Fourth-run preparation — not authorization

Proposed configuration remains the previously approved engineering scenario, but this report does not authorize its execution:

| Setting | Prepared value |
|---|---|
| Source branch | `r6/si1-bandwidth-f2av` |
| Source commit | R4 final commit; must be rechecked at a later authorization gate |
| Pair / support | continental plate pair 5:11; admitted supports `R6G1D-R091-C029` and `R6G1D-R091-C028` |
| Start / interval | T0 = 210 Ma; 1,000 engineering years |
| Driver / model | existing frozen Euler forcing and reduced T-F2B thermal kernel |
| Resolution fractions | `0.001`, `0.0005`, `0.00025`; intermediate samples at `0.0005` |
| Runtime | Windows Python 3.12.10, NumPy 2.3.5, one local Python process; `ARCANA_EXTERNAL_ROOT` must resolve to the governed `_ARCANA_EXTERNAL_SOURCES` directory |
| Candidate destination | `outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04` |
| Supervisor evidence | `outputs/r6_functional_development/INT0B_R4_SUPERVISION_20261013_04` |
| Monitored limits | 900 s elapsed, 2 GiB process-tree working set, 512 MiB candidate output plus captured stdout/stderr; one attempt, no retry |

Both destination paths were checked absent during R4 preparation and were not created. The exact supervisor invocation to use only after a separate authorization and a fresh final-source/provider audit is:

```powershell
pwsh -NoLogo -NoProfile -File .\scripts\r6_int0b_supervisor.ps1 `
  -Mode Run -RepositoryRoot . `
  -PythonPath 'C:\Users\jose_\AppData\Local\Programs\Python\Python312\python.exe' `
  -OutputRelative 'outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04' `
  -EvidenceDirectory 'outputs/r6_functional_development/INT0B_R4_SUPERVISION_20261013_04'
```

The supervisor's `Run` mode passes the existing runner arguments only: repository root `.`, expected branch `r6/si1-bandwidth-f2av`, and the selected output-relative path. It applies the three monitored thresholds and removes only the two known-invalid Git object-directory variables from the child process. The pre-run gate must still verify exact branch/HEAD/parent, tracked cleanliness, source/provider hashes, Python/NumPy/environment identities, both absent destinations, and a read-only provider audit on the eventual execution commit. A new explicit authorization is required before this command can be run. The previous local provider audit is HEAD-bound to its own earlier commit and cannot be reused as final-source evidence.

## Publication and unchanged gates

The local R3 commit is `f2bfefce7e90d055ad44019ff3bf55cf7ebfe506`, parent `dfceb480554549ae363927f32451dfb2b2e9d72e`, on the expected branch with no tracked modifications at entry. Historical output and evidence paths were untracked and preserved. GitHub publication must be a normal fast-forward only; if DNS is unavailable, keep the commit locally and do not rewrite history.

No real evolution, provider-backed run, ShellSet, MPI, Solver, DGBSV, post-rift propagation, or WORLD_HISTORY access/publication was performed. The three old attempt verdicts remain unchanged. `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` remain in force. INT-1 is still blocked pending a complete, separately authorized and validated trajectory.

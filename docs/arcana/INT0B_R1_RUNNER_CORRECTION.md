# INT-0B-R1 — runner correction and re-execution preparation

Date: 2026-10-13

Branch: `r6/si1-bandwidth-f2av`

Correction baseline: `e95c7dbf281ede5312512654262b9925fa87eb02`

Decision: `INT0B_R1_RUNNER_VALIDATION_CORRECTED__REEXECUTION_PENDING_AUTHORIZATION`

## Scope and preserved failure

This is an offline runner correction only. The original attempt remains
`INT0B_FAILED_PRE_OUTPUT_VALIDATION`; its report
[`INT0B_EXECUTION_REPORT.md`](INT0B_EXECUTION_REPORT.md), failure transcript,
supervision records, and output directory
`outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01/`
are preserved unchanged. The local failure-attestation commit
`e95c7dbf281ede5312512654262b9925fa87eb02` remains the parent of this correction.
No evolution was run in R1.

## Correction and regression

The runner now delegates sample validation to
`_validate_diagnostic_sample_sequence()`. Strictly increasing times are checked
with `zip(times, times[1:])`, including finite numeric validation, an initial
time of zero, and exact equality between the final diagnostic record and the
expected final state and derived depth vector. Empty, malformed, boolean,
nonfinite, duplicate, decreasing, and endpoint-inconsistent records fail closed.

`tests/test_r6_functional_development_t_f2b_samples.py` exercises the helper
called by the actual runner. A controlled temporary source mutation restored
the defective `zip(times, times[1])`: the valid three-sample regression failed
with the same `TypeError: 'float' object is not iterable`. The corrected source
then passed the regression and relevant offline suites. The temporary mutation
was reverted before final checks.

## Offline verification

- Focused runner, INT0A pipeline, and functional-development tests: **40 passed**,
  0 failed, 0 skipped, using Python 3.12.10 and NumPy 2.3.5.
- The provider-backed, read-only `audit_pair_5_11()` was rerun on checkout
  `e95c7dbf281ede5312512654262b9925fa87eb02`: PASS. Pair, selected boundary,
  support/provider payload hashes, mapping, and event-census hash agree with
  the previously recorded preflight. `canonical_state_changed=false` and
  `no_world_history_access_or_publication=true`.
- The composite `source_identity_sha256` is now
  `9e027419bd47b551e9d883fde9f0d2e5f08bd415b06872db300161cd3a8b6ea0`. Its
  construction includes Git `HEAD`; the previous preflight identity
  `470e74a0d2b2f504576d6d4a49f53a7866efa0174a6640a4d72cdea7038f6c6c` was bound
  to a different commit. Recompute and record the identity after the R1 commit
  before any future run. Provider payload identities remain as listed in
  `INT0B_PROVIDER_PREFLIGHT.md`.
- Python runtime preflight resolved Python 3.12.10 and NumPy 2.3.5 using the
  existing Codex runtime site-packages path. No dependencies were installed.
- Synthetic foreground supervisor check: a known Python parent (PID 12700)
  and its Python child (PID 23956) were identified by executable path; sampled
  combined working set peaked at 24,244,224 bytes. The synthetic output-limit
  stop was detected and `.Kill(true)` terminated both processes. Output had
  reached 81,920 bytes when a 65,536-byte threshold was observed, demonstrating
  polling overshoot rather than a hard quota. A separate natural exit code 23
  was propagated correctly. Windows CIM parent-process inspection was denied
  by the environment, so the test relied on the known child PID emitted by its
  parent and verified termination directly.
- This validates the process identity, sampling, stop, tree-kill, and exit-code
  mechanisms exercised by the synthetic harness; it does **not** retroactively
  identify the PID/image behind the old 4,509,696-byte observation. That run's
  PID was not retained, so the unexpectedly small historical peak remains
  uncorroborated.

## Proposed next attempt — not executed

The prior authorization was for exactly one run and was consumed by the failed
attempt. A separate bounded authorization is required before another trajectory.

- New proposed output directory:
  `outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_02/`.
  It was absent when checked for this report. The failed `_01` destination is
  not reusable.
- Proposed command and environment, identical to the preflight setup except for
  the new output-relative path:

  ```powershell
  $env:ARCANA_EXTERNAL_ROOT = 'F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES'
  $env:PYTHONPATH = 'C:\Users\jose_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages;src'
  python scripts/r6_functional_development_t_f2b.py --repository-root . --expected-branch r6/si1-bandwidth-f2av --output-relative outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_02
  ```

- Proposed scientific configuration is unchanged: pair 5:11; T0 210 Ma;
  duration 1,000 engineering years; frozen Euler forcing; resolution fractions
  0.001, 0.0005, and 0.00025; existing sampling at the middle resolution.
  No equations, forcing, timestep settings, resolution factors, or sample values
  changed. The sole runner behavior change is fail-closed validation of the
  sample sequence.
- Inputs/provider documents match the prior listed hashes in the read-only
  audit on `e95c7dbf`. Because composite source identity binds Git HEAD, repeat
  the audit against the final correction commit immediately before a future
  authorized run.
- Proposed monitored operational limits remain 900 seconds, 2 GiB process
  working set, and 512 MiB cumulative output. They are sampled stop thresholds,
  not hard OS quotas. Any future supervisor record must include PID and image,
  process-tree accounting/termination status, peak working set, output bytes,
  elapsed time, exit code, and stop reason.
- No execution, new trajectory, replay, restart, or numerical finding is
  claimed. `INT-1` remains blocked until a future run is separately authorized,
  completes, and is validated.

## Unchanged gates

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`;
`THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`;
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`;
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

No WORLD_HISTORY, ShellSet, MPI, Solver, DGBSV, canonical publication, or
post-rift evolution was performed.

# INT-0B-R2 — execution-environment isolation correction

Date: 2026-10-13
Repository: `ARCANA_WORLD_R6_BW0`
Branch: `r6/si1-bandwidth-f2av`
Decision: `INT0B_R2_EXECUTION_ENV_CORRECTED__THIRD_ATTEMPT_PENDING_AUTHORIZATION`

## Scope and outcome

This work corrects the supervisor's child-process environment and verifies it offline. It did **not** launch the INT-0B trajectory, create candidate numerical output, or authorize a third attempt. `_01` and the `_02` failure records remain historical evidence and were not edited. The proposed `_03` trajectory destination is still absent.

The R1 supervisor loaded `C:\Users\jose_\AppData\Local\ARCANA\r6-env.ps1` before starting Python. That bootstrap reintroduced `GIT_OBJECT_DIRECTORY` and `GIT_ALTERNATE_OBJECT_DIRECTORIES`; the child consequently resolved Git objects outside the checkout and failed source-identity validation. The correction sanitizes exactly these two variables from `ProcessStartInfo.Environment` at the final launch boundary, after bootstrap. Other environment variables are preserved.

A first R2 child audit exposed a separate path typo: one literal `ARCANA_EXTERNAL_ROOT` used `corsiiuu` while the governed path is under `corsiiiuu`. `Set-ArcanaPythonRuntimeEnvironment` now derives the external source root from the resolved repository location, verifies that directory exists, and sets the existing Python runtime path. The regression checks the governed physical-geography payload exists. This prevents a false environment PASS when the root string is syntactically present but points to the wrong location.

## Offline verification

The real PowerShell 7 supervisor self-test intentionally injects invalid Git object-store variables into its parent. The unsanitized child fails repository object access; the sanitized child succeeds at repository discovery, `git rev-parse HEAD`, and `git cat-file -t <expected-head>`. The test verifies child PID, interpreter and NumPy versions, effective Git-related environment, preserved `PATH`, `PYTHONPATH` and `ARCANA_EXTERNAL_ROOT`, and the presence of the governed physical input payload. It also exercises a descendant process, monitored wall-time/working-set/output stop paths, tree termination, and natural nonzero exit-code propagation.

On commit `d9d87fe8853b5c17f5bc8fd27d496aaf9aa45b57`, the sanitized child reported:

- Python `3.12.10`; NumPy `2.3.5`.
- Repository `F:\corsiiiuu\Magistrale\Arcana\ARCANA_WORLD_R6_UBUNTU_PORT\ARCANA_WORLD_R6_BW0`; exact HEAD `d9d87fe8853b5c17f5bc8fd27d496aaf9aa45b57`; object type `commit`.
- No `GIT_OBJECT_DIRECTORY` or `GIT_ALTERNATE_OBJECT_DIRECTORIES`; `GIT_PAGER=cat` remained, demonstrating unrelated Git environment was not globally cleared.
- `PATH`, `PYTHONPATH` and the derived external-root setting remained intact.

The focused regression set passed **41 tests** with a fresh writable pytest `--basetemp`; `py_compile` and `git diff --check` passed. The test uses the base Python executable because the virtual-environment launcher PID differs from the Python process PID on this host; the production supervisor's configured Python executable is the base Python 3.12 interpreter. No compiler, Fair, MPI, ShellSet, Solver, DGBSV, or scientific evolution was run.

## Provider-backed audit on final correction source

The provider audit was run through the same `ProcessStartInfo` child-launch and Git-variable sanitization path as the supervisor. It returned exit code 0 and bound its result to the correction commit:

- Branch / source HEAD: `r6/si1-bandwidth-f2av` / `d9d87fe8853b5c17f5bc8fd27d496aaf9aa45b57`.
- HEAD-bound source identity SHA256: `7438690f5b7d59b1ab0177a0ac270deb188fcfc233308131da6d6515998461bd`.
- Provider result: `outputs/r6_functional_development/INT0B_R2_SUPERVISION_20261013_FINAL/provider-audit/provider-audit-result.json`, 101,132 bytes, SHA256 `2db09f684c59acb40a1115794f47b0e06c9d8e4dd33c67360948339cd3a994b1`.
- The child diagnostic recorded the resolved external root and the required physical-geography payload as a file, with both Git object-store variables absent.
- Verified provider identities remained: field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`; admitted-support index `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00`; vector partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`; event census `e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e`; kinematics artifact `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2`; kinematics semantic identity `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`.
- Pair remained 5:11; selected boundary `R6BND-T0-3eb57747e6f0a3f3305f`; `canonical_state_changed=false`; no WORLD_HISTORY access/publication.

This confirms provider audit execution under the corrected local environment at audit time. It does not guarantee future filesystem identity or turn the engineering providers into scientific authority. The original preflight's input SHA records remain in [INT0B provider preflight](INT0B_PROVIDER_PREFLIGHT.md).

## Proposed third-attempt contract — not authorized or executed

The prior approved scientific configuration is unchanged: continental pair 5:11; T0 210 Ma; 1,000 engineering years; frozen Euler forcing; existing reduced thermal kernel; resolution fractions 0.001, 0.0005 and 0.00025; one local Python process; no automatic retry. Proposed new candidate output:

`outputs/r6_functional_development/INT0B_TF2B_5_11_R2_20261013_03`

It was verified absent after correction. `_01` remains present and untouched; `_02` remains absent as a trajectory output, with its separate failure/supervision evidence preserved. Proposed supervisor invocation from the repository root (must be rechecked immediately before any separately authorized attempt):

```powershell
pwsh -NoProfile -File scripts/r6_int0b_supervisor.ps1 `
  -Mode Run `
  -RepositoryRoot . `
  -OutputRelative outputs/r6_functional_development/INT0B_TF2B_5_11_R2_20261013_03 `
  -EvidenceDirectory outputs/r6_functional_development/INT0B_R2_SUPERVISION_20261013_RUN
```

The supervisor's underlying runner arguments remain `--repository-root . --expected-branch r6/si1-bandwidth-f2av --output-relative <the path above>`. Monitored thresholds remain 900 seconds, 2 GiB process-tree working set, and 512 MiB cumulative output. They are sampled operational stop thresholds, not OS-enforced quotas; polling overshoot remains possible. The proposed run evidence directory must also be absent before use.

**Next action:** obtain a separate explicit authorization for one attempt, then repeat branch/HEAD, provider/input, environment, supervisor and destination checks immediately before execution. Until then, no run is permitted by this report. INT-1 remains blocked pending a complete, validated trajectory.

## Preserved gates and non-actions

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

No third trajectory run, Fair/MPI/ShellSet/Solver/DGBSV, physical post-rift evolution, or canonical/WORLD_HISTORY operation occurred.

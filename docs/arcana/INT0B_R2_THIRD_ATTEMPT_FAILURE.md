# INT-0B-R2 — third and final authorized attempt failed

Date: 2026-10-13
Repository branch: `r6/si1-bandwidth-f2av`
Source HEAD: `311550d4402f6c2fac422eac1c7f1eed46c58c64`
Parent: `d9d87fe8853b5c17f5bc8fd27d496aaf9aa45b57`

## Decision

`INT0B_R2_THIRD_ATTEMPT_FAILED_DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH`

This was the single third/final attempt authorized for INT-0B-R2. It must not be retried under that authorization. The numerical runner completed its three configured resolution passes and failed while validating the middle-resolution diagnostic samples against the final state. No candidate trajectory was committed to the requested output path, and no replay/restart or post-run numerical adjudication completed. The engineering computation did execute in memory; this is not a claim that no evolution calculation occurred.

## Preflight identity and configuration

The local branch, HEAD, parent and tracked worktree matched the authorized identity. The final provider-backed audit was rerun through the sanitized child-process path on this HEAD.

- Provider audit: `outputs/r6_functional_development/INT0B_R2_SUPERVISION_20261013_FINAL_311550_PROVIDER/provider-audit/provider-audit-result.json`; locally verified SHA256 `8c9fc82a8ee4457a34a57efaa0bb53109047413562b237db733ddb9e3fbca58c`.
- Source-composite identity: `a19070287adedb0bb009ce5c56380892ca173d4eee30b662c6c1a7d34406b34a`.
- Pair `5:11`; selected boundary `R6BND-T0-3eb57747e6f0a3f3305f`; admitted supports `R6G1D-R091-C029` and `R6G1D-R091-C028`, each with a 73-node T0 profile.
- Provider payload identities: field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`; support index `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00`; vector partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`; event census `e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e`; kinematics artifact `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2`; kinematics semantic identity `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`.
- The sanitized child self-test recorded Python `3.12.10`, NumPy `2.3.5`, correct Git HEAD and preserved `ARCANA_EXTERNAL_ROOT`/`PYTHONPATH`; both invalid Git object-directory variables were absent in the sanitized child.
- Approved configuration remained pair 5:11, T0 210 Ma, 1,000 engineering years, frozen Euler forcing, existing reduced thermal kernel and resolution fractions `0.001`, `0.0005`, `0.00025`. The only command configuration change from the approved plan was the new `_03` destination.
- Both the requested candidate destination `outputs/r6_functional_development/INT0B_TF2B_5_11_R2_20261013_03` and its immediate run evidence destination were confirmed absent before launch. The candidate destination remains absent after failure.

## Observed execution

Supervisor evidence is preserved at `outputs/r6_functional_development/INT0B_R2_SUPERVISION_20261013_RUN/`:

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `run-summary.json` | 1,122 | `b699666d0c5e33db350b02404b544065f57fda290f49d0721011be02f475a271` |
| `run.ndjson` | 69,221 | `7c2812bbda0daa38d8c228555737c662fb07e385a185984d87391bb01d3ea993` |

The summary records root PID `33688` (`python.exe`, Python 3.12.10), elapsed time `22.190863 s`, `194` samples at a 100 ms polling interval, peak sampled process-tree working set `151,773,184` bytes, peak/final output-directory size `0` bytes, child exit code `1`, and sampled (not OS-enforced) limits. No limit was reached. Polling overshoot is not applicable to a limit-triggered stop; the recorded duration is the observed natural-run duration.

The runner failure observed in the foreground tool output was:

```text
RuntimeError: DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH:R6G1D-R091-C029:0
```

The exception arose in `_validate_diagnostic_sample_sequence()` called from `main()` after resolution results were assembled and before replay/restart and output-manifest writing. The endpoint validator compares the final diagnostic record with the middle-resolution final state across the declared endpoint fields and derived `z_m`. The failing field was not separately recorded, so it remains UNKNOWN. The traceback was observed in the foreground tool output; no byte-preserved stderr transcript is present in the run evidence directory.

No sample series, final-state report, resolution-comparison artifact, replay/restart result or run manifest was written. Consequently the requested manifest, continuity, invariant, endpoint and replay checks cannot be completed, and INT-1 has no validated trajectory to analyze. The output directory size is zero and the candidate output directory was not created.

## Supervisor metadata anomaly

The supervisor summary contains two incorrect metadata values: its `label` is the stale `INT0B_R1_SINGLE_ATTEMPT`, and its `stop_reason` is `MONITOR_ROOT_IDENTITY_LOST`. The NDJSON shows the root process being sampled through 22.066 s and then naturally exiting before the next process snapshot. The supervisor loop checks `HasExited` before taking a process-tree snapshot; the observed sequence is consistent with a race in which natural exit occurs between those operations. The supervisor nevertheless preserved the child exit code `1` and the correct root PID. Thus the runner failure is established, but the summary's stop reason is not an accurate classification of that natural exit. This report does not rewrite the immutable run evidence.

## Scope and disposition

This was a noncanonical engineering run only. No result qualifies physical science, promotes a provider, or authorizes canonical publication. There is no evidence in this attempt of access to or modification of `WORLD_HISTORY`; the provider audit also records `no_world_history_access_or_publication=true` and `canonical_state_changed=false`.

Preserved gates:

- `BLOCKED_F2AV_QUALIFICATION`
- `OPERATOR_CLASS_UNVERIFIED`
- `THRESHOLD_UNJUSTIFIED`
- `RESOURCE_2GB_SCOPE_UNRESOLVED`
- `F2B_SOLVER_EXECUTION_AUTHORIZED=false`
- `ARCANA_SI1_MECHANICS_QUALIFIED=false`
- `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`

Next work is offline diagnosis of the exact endpoint mismatch using a focused synthetic reproduction and correction of the supervisor's natural-exit race/attempt label, if confirmed by test. Any further evolution execution requires a new, separately bounded authorization. INT-1 remains blocked until a complete trajectory with independently validated evidence exists.

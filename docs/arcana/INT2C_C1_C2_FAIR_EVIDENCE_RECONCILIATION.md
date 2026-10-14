# INT-2C-C1/C2 — Fair evidence reconciliation

Date: 2026-10-14. Branch `r6/si1-bandwidth-f2av`; entry Windows/GitHub HEAD
`3d53ed80ea170d7b0b3d20b3fb4e40ff103a4daa`. Local tracked worktree/index were
clean, with no pending commits or local ledger changes. Fetch verified identical
remote HEAD and divergence counts 0/0. Existing untracked evidence was preserved.

**Decision: `INT2C_C1_C2_FAIR_PREFLIGHT_REPORTED__C3_PENDING_AUTHORIZATION`.**
The following Fair results are reported by the operator in the reconciliation
instruction. C1/C2 files were not identified in the inspected local task output
paths. Their hashes have not been independently recalculated on Windows. No
remote reacquisition, environment installation, store publication or numerical
execution was performed in this consolidation.

## Evidence and authority

| Evidence locator supplied by operator | Reported outcome | Windows verification |
| --- | --- | --- |
| `INT2C_RUNTIME_CHECK_BXFon4Yd` | Isolated Fair Python 3.12.10 / NumPy 2.3.5; Conda installation exit 0 | Operator-reported; original files not imported/rehash-verified here |
| `INT2C_C1_zC7ONJo8` | Technical attestation PASS; eleven typed records; checkpoint/recipe IDs match Windows | Operator-reported Fair outcome; local Windows records independently rechecked |
| `INT2C_C2_ljWdyPsq` | Atomic HistoryStore registration of 11 records, reopened-store verification PASS, typed readback PASS, `validate_replay_inputs()` PASS | Operator-reported; no independent Windows store/log verification |

C2 store inventory: **16 files / 78,945 bytes**, operator-reported.
No real numerical kernel execution occurred in C1/C2, according to that report.
Full remote paths, exact Fair tested commit, runtime binary hashes, command
transcripts and C1 artifact digests were not supplied; retain UNKNOWN for them.
The evidence locator strings above are identifiers, not invented full paths.

Reported C2 identities:

- Result SHA256: `ae1e99c652a064fb60d691590c76c4150981b11ce42e1bc6d9381a9719c28932`.
- Log SHA256: `3392ebf60061734e5a86f7061281ba6f3c2befa545af7b18688eeeb93451064a`.

These digests are recorded as **OPERATOR_REPORTED**, not Windows-verified.
The installation result does not authenticate historical R4 interpreter binaries
or establish numerical replay equivalence. Store/input closure does not prove
that the kernel has run or that its result matches the R4 oracle.

## Local records and preserved history

Windows technical attestation remains at
`outputs/r6_functional_development/INT2CB_TECHNICAL_ATTESTATION_20261014_02/`.
Its three-member manifest SHA256 is
`8b172002968c9fcd7620d78b456054ac7ca0e7a9afa49f2f9e91ca81e9b1731d`.
Local membership, member sizes/hashes and typed checkpoint/recipe identities
were rechecked. This is independent verification of the **local** records, not
an independent comparison with untransferred Fair bytes.

- Technical checkpoint:
  `r6checkpoint_45ccc437cbe2d5d8d40febbbbc3d7d6d5b5a1a42e7060ca40027048524b71158`.
- Matching recipe:
  `r6recipe_46e4b555cd4f996cd58020b840819c6ff468cb4640254fb3bb4efb6e887a4c92`.
- Validation scope: `TECHNICAL_ENGINEERING_INPUT_CLOSURE_ONLY`.
- Historical original checkpoint remains `CANDIDATE_NONCANONICAL`, unchanged.

The original INT-2C-B report and `INT2CB_BLOCKED_FAIR_RUNTIME_IDENTITY_MISMATCH`
remain immutable historical observations from before the operator's isolated
runtime provisioning. C1/C2 are subsequent, separately reported advances.
No checkpoint is physically or canonically promoted by this reconciliation.

## Next action — INT-2C-C3

Prepare one supervised real R4 B0 replay, **pending final authorization and
preflight**. Before execution, bind the actual source commit, runtime, isolated
store and C1/C2 records to acquired evidence; verify complete dependencies,
reopened readback, forcing/configuration and exact Python 3.12.10 / NumPy 2.3.5.
Confirm fresh evidence paths, monitoring and process termination capability.
Any unresolved source/store/runtime identity must block the final preflight.

The eventual authorized runner must use current `HistoryStore`,
`validate_replay_inputs()` and `execute_replay()` with the genuine
`DeterministicKernelAdapter`, recomputing both 73-node states from initial
inputs using `pure_shear_thermal_step`, 1,000 engineering years and fraction
0.0005. Expected final values remain verification oracles only. Acceptance
requires the complete expected state identity and original per-support payload
digests; preserve discrepancies, without normalization or automatic retry.
This task grants no numerical execution authorization.

## Consolidation checks and gates

Scope: this report and the five operational ledger files only. PROCEDURE,
historical reports, source, B0 contracts and outputs remain unchanged. Focused
INT-2C-A/B offline regressions: **29 passed, 0 failed, 0 skipped**. No new kernel
execution test was added. Documentation references, UTF-8/LF, whitespace,
exact staged membership and diff checks are required before publication. Actual
Linux store publication is not repeated on restricted Windows. Publication uses
a verified normal fast-forward push.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`,
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

# INT3-ENG10K-F3 — Option B Authorization Decision Preparation

Date: 2026-10-24
Repository / branch: `siegmound/ARCANA_WORLD` / `r6/si1-bandwidth-f2av`
Preparation HEAD: `569ddd3a14933677f322334c1677b4e9899d393a`

## Decision status

**Decision pending operator selection.** This document prepares the explicit
choice; it does not make that choice, issue an execution authorization, create a
runner-accepted authorization artifact, or permit a numerical process to start.
Until a separate decision is recorded, retain
`INT3_ENG10K_EXECUTION_AUTHORIZED=false`.

The F2 proposal is
`INT3F_ENGINEERING_AUTHORIZATION_PROPOSAL_READY__EXECUTION_NOT_AUTHORIZED`.
F1 remains a reported read-only reconnaissance at its historical exact source
HEAD `1bf06ef0e624723c3722a351496ae3b7c2544f40`; its resource values must not be
represented as new observations or as measurements for this preparation HEAD.
The original F review's blocked result remains historical and unchanged.

## Fixed experiment scope

If separately authorized after the final exact-commit preflight, the only proposed
experiment is `R6-INT3-ENG10K-A`: ordered pair 5:11, two authenticated R4 supports,
direct integration for 10,000 engineering years, and restart from the R4
1,000-year checkpoint for 9,000 years. Use only factors 0.001, 0.0005 and
0.00025, the existing Python 3.12.10 / NumPy 2.3.5 runtime, existing kernel,
forcing and boundary conditions, and noncanonical output. No parameter,
configuration, physical equation, input, or scenario substitution is in scope.

## Option B risk register

| Risk / limit | Evidence and status | Required operator acknowledgement |
|---|---|---|
| 900-second wall limit | Supervisor stop threshold; workload duration is UNKNOWN. It is not a completion estimate. | The process may be stopped at the threshold; completion within 900 seconds is not promised. |
| 2 GiB process-group RSS | Sampled supervisor threshold, not an OS-enforced quota. Fair F1 reported visible `memory.max`/`memory.high` as `max`; the F1 files were not independently imported on Windows. | RSS can exceed 2 GiB between samples or before termination takes effect. |
| 512 MiB cumulative output | Sampled threshold, not filesystem quota. Prior 66,715,648-byte value is only a serialization projection. | Output can exceed the threshold between samples; personal quota and future free space are UNKNOWN. |
| Resource observations | F1 host/session memory and `/home` free-space figures are historical, single-time observations, not a job reservation. | Future allocation, actual workload peak RSS, thermal substep count and personal filesystem quota remain UNKNOWN. |
| Stop/monitor failures | Any timeout, monitor error, forced termination, nonzero exit, incomplete output or missing/invalid manifest is a failed/incomplete attempt. | Preserve the attempt and all partial artifacts; classify honestly; no retry is implied. |
| Numerical comparisons | Direct/restart and resolution results have no justified acceptance tolerance. | Report measured differences descriptively; retain `THRESHOLD_UNJUSTIFIED`. |
| Scientific/canonical authority | This is an engineering-only reduced-model experiment. | No result qualifies model physics automatically or may be promoted to `WORLD_HISTORY`. |

F1's values—MemTotal 1,056,486,536 kB, MemAvailable 1,030,996,348 kB,
`/home` available 16,550,992,183,296 bytes and 361,730,941 free inodes at
2026-10-24T21:26:09Z—are historical operator-reported observations only. They do
not close resource uncertainty. The visible cgroup hierarchy had `max` limits;
no scheduler or cgroup enforcement for this experiment was established. Option A
(verified OS-enforced isolation) remains unavailable/unproven on current evidence
and is not assumed.

## Explicit alternatives for the operator

### APPROVE OPTION B FOR SEPARATE AUTHORIZATION PREPARATION

This selection means only that the operator accepts the residual sampled-monitoring
risks above and authorizes preparation of the final exact-commit binding. It does
**not** authorize preflight access, production supervisor invocation, or numerical
execution. A later distinct authorization would still be required after all
pre-execution checks pass.

### REJECT / DEFER OPTION B

Keep execution blocked until a separately reviewed resource/isolation path or
other sufficient evidence addresses the operator's concerns. No experiment runs.

### Operator decision record — intentionally blank

- Selection: `PENDING_OPERATOR_DECISION`
- Decision date/time: `PENDING`
- Operator identity/authority reference: `PENDING`
- If approved, acknowledged risk: `PENDING`
- Scope limitations accepted: `PENDING`

Do not replace these fields with inferred approval. A decision record must be
explicitly supplied and reviewed before the next phase.

## Exact-commit preflight checklist for a later phase

After an explicit option-B selection, but before any execution authorization, an
already-authorized Fair operator must perform a fresh read-only preflight bound to
the exact candidate commit and proposed output paths:

1. Verify full commit, branch, ancestry and clean execution-source state. Identify
   the same supervisor, runner and immutable execution contract that will run.
2. Reverify the full R4 manifest membership and every member digest, checkpoint,
   kernel source identity, and the exact engineering configuration SHA256.
3. Recalculate provider payload identities and the source-composite for that
   exact commit; verify supports, forcing, profiles and direct/restart inputs.
   Do not reuse F1's HEAD-bound source-composite for another commit.
4. Confirm Python 3.12.10 / NumPy 2.3.5 in the actual child environment and verify
   sanitized process environment.
5. Read current Fair host and attempt-root available memory, filesystem space,
   inode state, personal quota if available, and any applicable scheduler/cgroup
   policy. Confirm the operator has authority and that applicable Fair
   administrative rules permit this workload. Mark unavailable measurements
   UNKNOWN; do not infer enforcement.
6. Confirm a fresh, absent candidate directory and distinct absent supervision
   directory under the authorized evidence root, outside R4 and canonical
   `WORLD_HISTORY`. Bind both paths into the reviewed execution contract.
7. Verify the authorization record and execution contract refer to the same full
   commit, input identities, configuration and paths. Do not create a JSON or
   token that can pass the runner gate until the separate execution authorization
   actually exists.
8. Return the preflight for review. Any mismatch, missing authority, occupied
   path, changed input, monitor failure or unacceptable unknown blocks execution.

F1's prior checksums remain operator-reported: `preflight.log`
`db5c15a0555c00753711007342362cc91d3eb7e48c9f46895573a51f9d67c0e8` and
`resources.log`
`cd960de86593eb38241981d67f07b26df71dfc37e2d12754132486c375c3eaf5`.
The original files were not imported/rehashed on Windows. The F1 evidence path is
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT3F1_RESOURCE_PREFLIGHT/1bf06ef0_20261024_01`.

## Completion and STOP criteria

Keep separate findings for (a) process/run completion, (b) sealed artifact
membership and hashes, (c) observed versus sampled budget behavior, (d) descriptive
direct/restart and resolution comparisons, and (e) scientific interpretation,
which is not authorized. No new numerical or physical tolerance is defined.

Any future attempt must be exactly one run, with no automatic retry. Timeout,
monitor error, resource/output threshold stop, forced termination, invalid input,
nonzero exit, missing or corrupt seal, or incomplete result stops the task and
leaves immutable failure evidence. No follow-on execution is implied.

## Gates preserved

`RESOURCE_2GB_SCOPE_UNRESOLVED`; `THRESHOLD_UNJUSTIFIED`;
`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`;
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`;
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`;
`INT3_ENG10K_EXECUTION_AUTHORIZED=false`.

# INT-2C-C3 — Executable R4 B0 replay closure

Date: 2026-10-14. Branch `r6/si1-bandwidth-f2av`; Windows entry and
Fair-tested source commit `9fb4fc0286cc09bcb6b8eef07bb92a19f4ca5963`.
Tracked worktree/index initially clean, no pending local commits; fetch verified
the same remote HEAD with divergence 0/0. Existing untracked evidence preserved.

**Decision: `INT2C_B0_EXECUTABLE_R4_REPLAY_VERIFIED__SCIENTIFIC_AUTHORITY_UNCHANGED`.**
One operator-authorized Fair replay is closed by reported execution and the
independently verified imported numerical artifacts. No new numerical replay,
HistoryStore construction/publication or Fair access occurred during closure.

## Evidence integrity and authority

Imported bundle:
`outputs/r6_functional_development/INT2C_C3_REPLAY_20261014_01/`.
Windows acquired local byte buffers, authenticated manifest/member lengths and
SHA256, and parsed those same verified buffers. Membership is exactly **21
manifest members plus the manifest: 22 files / 143,807 bytes**. No unexpected
files, unsafe relative member paths or symlinks were accepted. All hashes match.

| Artifact | Bytes | SHA256 independently recalculated on Windows |
| --- | ---: | --- |
| ARTIFACT_MANIFEST.json | 4,175 | `da913ccef5850ae943afadfd90672853db9d1b625eed2ebcc2d508fc599a2852` |
| REPLAY_RESULT.json | 11,418 | `d55e9302ff85c9007679c916124aa1c163304aa88e84b86da62291675901fd4e` |
| COMPUTED_STATE.json | 47,829 | `def81afa18361d7961e9bd777cc03c6ec536be9d587c952f007f69efe2ec2108` |
| SUPERVISION.json | 1,440 | `2c709d8a3d1a3872e63bbb176006c1912a9d64fb7c5ee05bb1e2a39585f22682` |

Both child stdout/stderr files are empty, independently hash-verified. Sixteen
read-copy store files total 78,945 bytes and match REPLAY_RESULT.c2_inventory.
All eleven typed records match fresh, nonnumerical reconstruction of the R4
technical attestation. The committed read-view identity and exact record
membership reconcile. No B0 atomic-write protection was bypassed on Windows.

Parent log SHA256 `4f8b0f778e2c476d1335dd033cc3bc47af8b8e6ca0200e9faea9b3f067ed6c30`
is **OPERATOR_REPORTED**: that separate log was not identified among imported
task files and was not independently rehashed. Linux supervisor test result
**28 PASS / 1 expected SKIP** is also OPERATOR_REPORTED; its test transcript
was not transferred. Child empty logs do not substitute for either parent/test log.

The reported genuine real-kernel execute_replay call, authorization, single
attempt and absence of retry are execution testimony, consistent with the
imported result, command and committed launcher. Byte integrity is independently
verified; it is not an independent cluster signature or observation of the live
historical process.

## Numerical result independently checked offline

COMPUTED_STATE deserializes with its valid complete B0 content identity. It is
equal to the complete unchanged R4 expected state, with identical numerical
payloads and metadata. REPLAY_RESULT reports B0 VERIFIED, zero mismatches and
numerical_execution_started=true; both per-support digests were recalculated
from COMPUTED_STATE using the original pretty-JSON/LF serialization.

- Complete state ID:
  `r6state_d36b8094e89671d0d25894bcd4d798efdb426c65fcd6eb5d6652531f92c51d6a`.
- Each support payload SHA256:
  `2b4836954e688d7aac6d9e26ccb61aa02fa94e9e40550c395922b30fa1b45d7b`.
- Supports: `R6G1D-R091-C029` and `R6G1D-R091-C028`, 73 nodes each, all numeric
  payload fields finite; final time 31,557,600,000 seconds (1,000 years).
- Pair 5:11, original frozen Ux 0.11467052868814648 m/year, reference fraction
  0.0005. Runtime recorded as isolated Python 3.12.10 / NumPy 2.3.5.

Both supports have the same numerical payload; they are not independent
replications. These values reproduce existing engineering output, not a new run:

| Field | Initial | Replayed final (both supports) |
| --- | ---: | ---: |
| Width, m | 111156.82195362539 | 111271.49248231354 |
| Crust thickness, m | 28000 | 27971.144677476324 |
| Lithosphere thickness, m | 80000 | 79917.55622136094 |
| Beta | 1 | 1.0010316103561865 |
| Accumulated strain | 0 | 0.0010310786118935147 |

Final temperature range: **280.0–1671.771417700828 K**; maximum absolute change
from initial profile: **0.07193306832937196 K**. Equality is exact for this
serialization/state contract; no tolerance or normalization was introduced.
Inline state identity, state-file SHA and historical per-support payload SHA
have distinct meanings and are not conflated.

## Source, input and technical checkpoint closure

The twelve source-file normalized hashes in the imported result match Git blobs
at `9fb4fc0286cc09bcb6b8eef07bb92a19f4ca5963`. Historical/current kernel identity
remains `bddedfd7439b328951389012b2af371d106d042018ac4be928325a6395666542`, bound
to original R4 execution commit `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`.
Recorded configuration/source identity matches the existing authenticated R4
preparation. REPLAY_RESULT.r4_inventory matches the original nine local R4 files;
the source manifest remains
`191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`.

Original checkpoints retain CANDIDATE_NONCANONICAL. The derived checkpoint
`r6checkpoint_45ccc437cbe2d5d8d40febbbbc3d7d6d5b5a1a42e7060ca40027048524b71158`
remains VALIDATED solely for TECHNICAL_ENGINEERING_INPUT_CLOSURE_ONLY; recipe
`r6recipe_46e4b555cd4f996cd58020b840819c6ff468cb4640254fb3bb4efb6e887a4c92`
matches. Numerical replay verification is a separate result, not a mutation of
the technical checkpoint or scientific authority.

The original Fair C2 store is not independently available on Windows. Its
recorded source inventory matches the imported read copy; original remote
immutability checks are recorded by the tested launcher. This closure does not
claim a new independent remote C2 rehash. Local R4 and imported C3 bytes were
rechecked unchanged after processing; no original evidence was overwritten.

## Supervision observations

SUPERVISION.json records NATURAL_EXIT, child exit **0**, elapsed time
**0.7619832679629326 s**, peak sampled process-tree RSS **39,845,888 bytes**,
PID **1592336**, start ticks **2178864390**, and two resource samples. Recorded
executable is the isolated replay environment's `bin/python3.12`.

Limits: 900 seconds, 2,147,483,648 RSS bytes, 536,870,912 output bytes. All recorded
overshoot fields are zero. Observation before sealing: 138,192 bytes; adding
1,440-byte supervision and 4,175-byte manifest gives the independently verified
post-seal 143,807 bytes. No observed threshold was exceeded.

These historical timing/RSS/process measurements are contents of an authenticated
imported observation record, not new Windows measurements. Two samples do not
establish an instantaneous peak. Polling, summed RSS and process-group handling
are not hard OS quotas, cgroup enforcement or complete accounting of all transient
processes. Runtime labels/NumPy module hash do not authenticate all historical
interpreter/library binaries or prove universal cross-platform equivalence.

## Closure and retained boundaries

Focused Windows offline regressions: **52 PASS, 6 SKIP** (Linux supervisor
runtime cases remain NOT_TESTED_WINDOWS). This does not replace the separately
operator-reported Linux 28 PASS / 1 expected SKIP. The local regressions use
synthetic runners or read-only input preparation, never another real R4 step.
Only this report and five ledger documents enter the documentation commit.
Imported outputs and historical reports remain untracked/unchanged.

INT-2C is closed for this existing R4 engineering trajectory, specific frozen
forcing, numerical configuration, kernel/source binding and tested Linux runtime.
INT-1D executable replay, general replay validity, physical resolution refinement,
general scientific accuracy and canonical readiness remain unqualified. STOP:
no further replay or new workstream is authorized by this closure.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`,
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

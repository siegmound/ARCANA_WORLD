# R6-INT3-ENG10K-A — Windows implementation readiness

Date: 2026-10-14
Branch: `r6/si1-bandwidth-f2av`
Implementation baseline: `8c75c439ab45a9d4e79930bd506e686e088e151d`

## Decision

`INT3_ENG10K_CODE_READY__WINDOWS_PREFLIGHT_PASS__FAIR_PREFLIGHT_PENDING__NO_NUMERICAL_EVOLUTION`

The isolated runner, bounded observation path, R4 continuation reader, manifest writer, Linux supervisor and offline tests are implemented. The authenticated Windows R4 bundle and current provider audit agree on boundary, supports, forcing and initial profiles. The current provider source-composite identity is `6d277b085383cdba98d38fe970d625d0af0f2d6ab9abdf788e4536194b725582`, whereas the R4 historical bundle binds `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`. Source inspection established that `plate_support_adapter.py` builds this composite with the current Git HEAD as an input. The two composites therefore identify different source checkouts and must not be compared as if they were the same identity. The corrected preflight preserves both hashes, verifies the current source head, and compares each non-source-set provider component identity against the independently R4-bound `source_refs`; it does not rewrite or equate the historical identity.

No 10,000-year numerical evolution, FAIR access, or canonical write was performed. The CLI defaults to `--mode preflight`; `--mode execute` additionally requires a separate source/config/path-bound authorization document. No such authorization was created.

## Authenticated R4 continuation input

The local bundle `outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/` was read-only verified against its independently pinned manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`. The loader checks exact membership of nine artifacts, file sizes and member SHA256 values, parsing from the acquired bytes, the R4 run decision, source/kernel identities, two ordered 73-node supports, forcing and initial/checkpoint state payloads. It binds the candidate checkpoint to the typed candidate state and its declared numerical configuration; the original B0 record remains `CANDIDATE_NONCANONICAL`.

Observed input binding: boundary `R6BND-T0-3eb57747e6f0a3f3305f`; supports `R6G1D-R091-C029` and `R6G1D-R091-C028`; frozen `Ux=0.11467052868814648 m/year`; initial states at `time_s=0`; candidate restart states at 1,000 engineering years (`31,557,600,000 s`); 73 nodes per support. Current provider re-audit reproduced the boundary, ordered supports, velocity and both initial state payloads. Seven non-source-set provider identities match the R4 forcing source references. The current source composite is intentionally distinct from historical R4 because its identity includes the current checkout HEAD.

This is input integrity and technical restart-shape evidence only. It does not attest that 10,000-year forcing is physically applicable or that the candidate checkpoint has scientific/canonical authority.

## Runner and retention contract

`configs/r6_int3_eng10k/engineering_case.json` pins the pair 5:11, initial age 210 Ma, direct duration 10,000 years, restart continuation 9,000 years from the R4 1,000-year state, frozen R4 Euler forcing, the existing `pure_shear_thermal_step` kernel, factors 0.001/0.0005/0.00025, and a 10-year diagnostic schedule at the 0.0005 reference factor. The historical R4 entrypoint and physical kernel were not modified.

The continuation calls the existing kernel with the accumulated `state.time_s`; it does not reset time to zero. Direct and segmented paths are compared field-by-field for time, width, crust/lithosphere, beta, strain, material coordinates and all temperature nodes. Metrics include absolute and relative differences; zero references are explicitly marked undefined where appropriate. No acceptance tolerance is invented. Resolution comparisons are descriptive, not a convergence or scientific pass.

Retained records are the initial state, the first actual numerical state at or after each scheduled target, and the complete final state. There is no interpolation. Missed schedule targets and omitted integration observations are counted. The sample cap is 1,002 records per support; all kernel substeps are not retained and this diagnostic sample set is not a physical history or a restart substitute.

Each serialized sample is capped at 16,384 bytes. Four maximum sample streams (two direct-reference supports and two restart supports) plus 1 MiB fixed allowance project to **66,715,648 bytes**, below the 512 MiB monitored output threshold. The writer computes actual serialized member sizes and rejects an over-budget bundle before writing artifact members; the supervisor also samples cumulative output and terminates on threshold breach. This output projection is not a RAM or RSS estimate. Python object overhead, NumPy working memory and measured Fair RSS remain unknown.

The R4 report recorded 20.633493 seconds for its entire 1,000-year, three-resolution run. Linear work scaling would imply roughly 12.6× that duration for the proposed direct plus restart substeps (about 260 seconds), but this is only a rough planning extrapolation; observer overhead, runtime variation and fairness are unmeasured. The 900-second monitor is a proposed operational stop threshold, not a proven sufficient duration or an OS-enforced quota. The kernel's existing substep bound is not evidence that wall time will remain below the monitor.

## Supervisor scope

The Linux supervisor starts the authorized Python runner in a new process group, verifies the root PID/start ticks/executable, samples `/proc` process-group RSS and output size every 0.1 seconds, captures stdout/stderr, and sends SIGTERM then SIGKILL to that group on a measured threshold or monitoring failure. It records natural exit status, stop reason, peak sampled values and whether limits were only sampled. No automatic retry is implemented. A synthetic mocked test checks the TERM/kill-group/wait control sequence; this is not OS/runtime proof. A descendant that deliberately detaches into a new session is outside this process-group accounting; the runner's expected child operations do not intentionally detach, but Linux verification must test actual behavior. Windows tests exercise pure `/proc` parsing with fixtures only; real process-tree termination and RSS supervision are `FAIR_PENDING`.

## Verification performed

- ENG10K focused offline tests: **17 passed** after the provider-identity, source-reference, output-size, result de-duplication and mocked stop-sequence regressions.
- Existing functional development, INT-0A, INT-1A and INT-2C focused regressions: **113 passed** when pytest's temporary directory was placed outside the repository. An initial run put `--basetemp` under the repository and one existing protected-root test correctly rejected that path; it was rerun outside the repository and passed.
- Python 3.12.10, NumPy 2.3.5 and pytest 8.4.2 available from the configured workspace runtime; no packages installed.
- `py_compile` passed for ENG10K modules, runner, supervisor and tests.
- Real R4 manifest and provider audit were checked read-only as described above.
- After commit `1b7f3e967050915d1ffa3d7b058f2571c036ee47`, Windows `--mode preflight` returned `INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION`. It verified Python 3.12.10 / NumPy 2.3.5, the exact current kernel hash, R4 manifest, provider components, boundary/supports/forcing/profiles and both absent candidate directories. Current source composite for that checkout: `cae5ef5c1b95034474031f716b68dcc0dc54fd9f0a56f97dbec26310f241526f`; historical R4 source composite remains `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`. The preflight created no output and executed no kernel evolution.
- No Linux supervisor runtime test, FAIR preflight, execution-mode run, 10,000-year evolution or canonical operation occurred.

The environment bootstrap left `ARCANA_EXTERNAL_ROOT` unset. For the successful Windows preflight, the process was explicitly pointed to the already present Windows `_ARCANA_EXTERNAL_SOURCES` directory. An earlier pre-commit CLI attempt correctly failed its source-cleanliness gate; the post-commit preflight above passed. FAIR still needs its own exact-commit, runtime, bundle and Linux-supervisor checks.

## FAIR preflight and next decision

After publication of an exact reviewed commit, the operator may run the non-numerical self-test/preflight only in the documented Conda environment, against the exact commit and a separately integrity-checked R4 bundle. The current source-composite hash is recalculated for that commit because HEAD is included in its definition; the historical R4 composite remains fixed and separate. Do not substitute either digest or edit R4 evidence.

Only a later, separate bounded authorization may create the exact new output and supervision directories and invoke `--mode execute`. This Windows implementation task does not grant that authority. Preserve `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

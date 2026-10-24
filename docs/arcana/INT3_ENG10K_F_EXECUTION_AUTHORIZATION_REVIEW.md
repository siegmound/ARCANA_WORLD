# INT3-ENG10K-F — Engineering Execution Authorization Review

Date: 2026-10-24
Repository: `siegmound/ARCANA_WORLD`
Branch / review HEAD: `r6/si1-bandwidth-f2av` / `52a73104cdf56fd3db020868a441889a89286ce5`
FAIR supervisor test commit: `cb9bd8373eeb028b83c8bc1abb376624e3553adb`

## Decision

`INT3F_ENGINEERING_AUTHORIZATION_BLOCKED__REQUIREMENTS_UNRESOLVED`

This is a review result, not an execution authorization. The evidence supports a
bounded engineering-run proposal in principle, but the final provider/runtime
identity and Fair resource availability have not been established for a future
attempt. `INT3_ENG10K_EXECUTION_AUTHORIZED=false` remains in force. No supervisor
execute mode, numerical evolution, Fair access, MPI, Solver, or canonical operation
was run for this review.

## Provenance and identity reconciliation

| Identity | Evidence and result | Authority limit |
|---|---|---|
| INT3-E supervisor code | FAIR result is operator-reported for exact commit `cb9bd8373eeb028b83c8bc1abb376624e3553adb`: preflight marker `INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION`; Linux suite 43/43, 0 skipped, 2.83 s; Python 3.12.10, NumPy 2.3.5, pytest 9.1.1. The three end-to-end synthetic paths were natural child exit, process-group timeout, and leader exit while a descendant remained alive. | FAIR logs and sidecars were not transferred or rehashed on Windows. This does not exercise the ENG10K kernel or establish resource sufficiency. Earlier C/D/E FAILs and collection errors retain their original outcomes. |
| Review HEAD versus FAIR-tested commit | `cb9bd837…` is an ancestor of review HEAD. `git diff cb9bd837… HEAD` contains only `PROJECT_LEDGER/{EVIDENCE_INDEX,LOG,NEXT_ACTION,README,ROADMAP,STATUS}.md` and `docs/arcana/INT3_ENG10K_E_FAIR_EVIDENCE_CLOSURE.md`; the execution code/configuration are unchanged across that range. | The current source-composite identity includes Git HEAD, so its value for a future authorized commit must be freshly computed. The tested commit's composite must not be reused as the new HEAD's identity. |
| R4 bundle | Local R4 manifest SHA256 independently recalculated as `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`. Exact nine-file membership matched: seven payload artifacts, `RUN_RESULT.json` (7,127 bytes; SHA256 `b7625dfc636bc86f062ab38db42ee04215864de2390b78f69fbfe17c2438124a`), and manifest. Every member length and SHA256 matched locally. The bundle contains two ordered 73-node supports, initial states at 0 s, and checkpoint states at 31,557,600,000 s (1,000 engineering years). | This verifies local bytes against the pinned manifest, not the historical process that produced them. Original bundle/output remains untouched. |
| Kernel and configuration | Current `src/arcana_worldsim/r6/functional_development.py` SHA256 is `bddedfd7439b328951389012b2af371d106d042018ac4be928325a6395666542`, matching the R4 execution contract. `configs/r6_int3_eng10k/engineering_case.json` SHA256 is `3f3d3dc6d6ad28a31fdb7f350eedfe971a63708ad0f0f63f2d97e49b4e474f3e`, also matching the contract. The runner uses the existing `pure_shear_thermal_step`; no kernel, forcing, or configuration changes are proposed. | Source hash and configuration identity do not establish physical validity over 10,000 years. |
| Providers and runtime | Earlier INT3 preflight records report the governed R4 provider identities, supports, forcing and profiles matching, and Fair reports Python 3.12.10 / NumPy 2.3.5. | Not re-attested for the prospective final execution identity in this review. `ARCANA_EXTERNAL_ROOT` is unset in this Windows session and its available Python 3.12.10 has no NumPy. Current provider audit/source-composite recomputation was therefore not completed. Fair-side availability must be checked again against the exact future commit and R4 bundle. |
| Direct/restart inputs | The runner loads direct starts from the verified R4 initial states and restart starts from its candidate checkpoint states. Configuration requests 10,000 years direct and 9,000 years from the R4 1,000-year checkpoint, at factors 0.001, 0.0005, 0.00025; the restart comparison uses 0.0005. Both supports share the same authenticated R4 forcing and ordered support identities. | Payload correspondence is verified for the local bundle; actual 10,000-year direct/restart numerical correspondence has not been run and remains unknown. |

The execution contract remains unchanged and declares `execution_authorized: false`
and `canonical_publication_authorized: false`. Its pinned case is pair 5:11 at
210 Ma, boundary `R6BND-T0-3eb57747e6f0a3f3305f`, supports
`R6G1D-R091-C029` / `R6G1D-R091-C028`, frozen extension
`0.11467052868814648 m/year`, and the existing reduced thermal kernel. The original
R4 checkpoint remains noncanonical; no source-composite identities are conflated.

The R4 manifest records these provider identities: event census
`e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e`, kinematics
artifact `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2`,
kinematics semantic `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`,
mapping `b8d57495bc6e196a0b9fe7afd466079bebd97d0f63baafe232f215e45897a09f`,
source set `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`,
support binding `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00`,
thermal field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`,
and vector partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`.
These are authenticated manifest values; external provider payloads were not audited
in this review.

## Static computational and output bounds

The runner performs six direct trajectories (three factors × two supports) and two
checkpoint continuations (0.0005 × two supports): eight kernel trajectories total.
The direct paths each cover 10,000 years. The restart paths each cover 9,000 years
from the R4 1,000-year checkpoint. Direct/restart comparison and resolution metrics
are descriptive; the code does not apply a scientific acceptance threshold.

The kinematic-only minimum number of substeps follows from the maximum width growth
per step, `w_next / w <= 1 + f`:

`N_min = ceil(log(1 + U·D/w_start) / log(1 + f))`.

Using direct width `111156.82195362539 m`, restart checkpoint width
`111271.49248231354 m`, and `U=0.11467052868814648 m/year`, the lower bounds are:

| Work | Factor | Duration per support | Kinematic lower bound per support | Aggregate lower bound |
|---|---:|---:|---:|---:|
| Direct | 0.001 | 10,000 y | 11 | 22 |
| Direct | 0.0005 | 10,000 y | 21 | 42 |
| Direct | 0.00025 | 10,000 y | 42 | 84 |
| R4 checkpoint continuation | 0.0005 | 9,000 y | 19 | 38 |

The eight trajectories therefore require at least 186 total kinematic substeps,
covering 78,000 support-years of integration work. These are lower bounds only:
the kernel also caps each step by
0.8 of a diffusion-stability limit and tightens it against the updated mesh. That
state-dependent thermal cap determines the actual count, which is not statically
known. The implementation fails if a trajectory exceeds 1,000,000 substeps; this
is a code failure bound, not a prediction that the run will approach it.

For the 0.0005 reference-direct and restart paths, the schedule is every 10 years.
The configured maximum is 1,002 retained records per support. A 9,000-year restart
has at most 902 schedule/end-point records per support under the same no-
interpolation policy. Actual retained observations are state-dependent: one
numerical state can cross multiple targets, with the missed targets counted rather
than interpolated. Therefore exact observation counts are `UNKNOWN` before
execution. At most 3,808 records are implied by the two direct-reference and two
restart streams; the writer's more conservative contract projection uses four
streams × 1,002 records.

At 16,384 bytes maximum per serialized sample plus a 1 MiB fixed allowance, the
projected bundle bound is `4 × 1,002 × 16,384 + 1,048,576 = 66,715,648` bytes
(63.625 MiB), below the 512 MiB monitored-output threshold by 470,155,264 bytes
(448.375 MiB). This is a serialized-output projection, not an RSS or disk-capacity
guarantee. The writer checks serialized member sizes before publication and writes
the manifest last; failures attempt an `INCOMPLETE_NONAUTHORITATIVE` marker. A
forced termination during writing may leave only a partial directory without that
marker, which must be preserved and classified incomplete from the missing sealed
manifest/result. Supervisor stdout/stderr also count toward its sampled cumulative
output limit.

Per substep, the explicit one-dimensional kernel evaluates the thermal update over
73 nodes, with repeated stability calculations on the moved mesh; work is at least
linear in node count per accepted substep. The unknown diffusion-limited step count
and Python/runtime overhead dominate any reliable wall-time estimate. The R4 report
recorded 20.633493 seconds for its 1,000-year, three-resolution run. The readiness
report's approximately 260-second linear extrapolation is an unvalidated planning
estimate, not measured INT3 throughput. The 2.83-second FAIR test-suite duration
is synthetic supervisor testing and is not workload timing. Evidence is therefore
insufficient to claim that 900 seconds will complete the run; it is only a maximum
sampled stop threshold.

## Resource and supervision assessment

| Requirement | Status | Evidence / gap |
|---|---|---|
| 900-second wall threshold | UNKNOWN | Supervisor samples elapsed time every 0.1 s and can TERM then KILL its process group. Polling and termination can overshoot. No ENG10K timing measurement exists. |
| 2 GiB process-group RSS threshold | UNKNOWN | Linux tests qualify synthetic process-group monitoring/termination paths only. There is no measured ENG10K peak, no current Fair available-memory record, and no proof of cgroup/systemd or scheduler enforcement. RSS is sampled, not an OS quota. |
| 512 MiB cumulative output | GO, bounded projection only | Static serializer projection is 66,715,648 bytes; supervisor samples candidate plus stdout/stderr. Neither provides hard filesystem quota enforcement. Disk capacity/quota at the future evidence root is not verified. |
| Descendant stop behavior | GO, synthetic scope | FAIR-reported real Linux synthetic tests covered a natural exit, process-group timeout and live descendant after leader exit. Detached descendants outside the process group and resource-exhaustion behavior remain unproven. |
| Interrupted evidence handling | GO with incomplete classification | Fresh attempt paths, collision checks, no automatic retry, manifest-last sealing and incomplete markers are implemented. A kill can interrupt before marker publication; absence of a complete manifest must remain failure/incomplete, never PASS. |
| Evidence isolation | GO by contract, future path UNKNOWN | Contract requires one new attempt below the existing external evidence root, separate `candidate` and `supervision` siblings, outside checkout/R4/WORLD_HISTORY, with collision and symlink checks. Actual root existence/writability, available space and candidate paths must be verified by a future no-evolution preflight. |

No memory availability or OS-enforced limit can be inferred from the synthetic
supervisor suite, the historical F2A-V Fair report, or the R4 process. The evidence
root's current free space/quota, effective scheduler allocation, cgroup hierarchy,
and actual process-tree memory for this workload are all `UNKNOWN`.

## Acceptance contract for any separately authorized attempt

1. **Execution/evidence integrity:** exact authorized source/configuration and
   freshly recomputed provider identities; unique absent attempt paths; child
   command and authorization match; natural exit 0; complete manifest membership,
   byte counts and SHA256; exact source/R4 bindings; no canonical writes. Any stop,
   signal, mismatch, missing manifest, partial member, or exceeded monitor is
   preserved as incomplete/failed evidence, with no retry or overwrite.
2. **Operational completion:** record actual elapsed time, polling overshoot,
   stop reason, process identity/descendants, peak sampled RSS, cumulative output,
   and Fair free-space/quota/enforcement observations. These measurements describe
   the run; they do not turn sampled limits into hard quotas.
3. **Numerical comparison:** retain full field-by-field direct-versus-R4-checkpoint
   continuation and resolution differences, finiteness, invariants, sample counts,
   missed schedule targets and endpoints. No pass/fail equivalence tolerance is
   currently justified; report values and preserve `THRESHOLD_UNJUSTIFIED`.
4. **Scientific interpretation:** characterize only this noncanonical reduced
   model under frozen instantaneous forcing. Do not infer 10,000-year geological
   validity, convergence, event occurrence, general mechanics qualification or
   canonical history readiness.

These criteria do not authorize a run and do not define a numerical tolerance.

The existing runner rejects non-finite temperatures and area-relative error above
`1e-12`. This is the implementation's declared engineering invariant check; it is
not a direct/restart equivalence tolerance, resolution-convergence criterion, or
physical-accuracy threshold.

## Decision matrix and blockers

| Topic | Decision | Evidence | Blocker / mitigation |
|---|---|---|---|
| R4 bytes, checkpoint and kernel/config pins | GO | Local manifest and members rehashed; kernel/config hashes match contract. | Re-verify exact inputs in the final preflight; preserve R4 unchanged. |
| INT3-E synthetic supervisor code | GO, scoped | 43/43 FAIR tests reported on `cb9bd837…`; execution code is unchanged through document-only review HEAD. | Original Fair logs are operator-reported, not locally acquired. No production run authority. |
| Current source/provider/runtime closure | UNKNOWN | Prior preflight reports are tied to earlier exact commits; source composite binds HEAD. | Current Windows environment lacks `ARCANA_EXTERNAL_ROOT` and NumPy, so no current provider audit. Exact Fair preflight and source-composite recomputation are mandatory before any authorization decision. |
| Computational completion under 900 s | UNKNOWN | Kinematic lower bound 186 substeps; state-dependent diffusion steps unknown; prior R4 timing is nonrepresentative. | No honest throughput evidence. Keep the 900 s threshold as a fail/stop limit; do not promise completion. |
| Memory and Fair capacity | UNKNOWN | No INT3 workload RSS or current Fair allocation/enforcement evidence. | Before an authorization proposal can advance, acquire read-only current Fair allocation/quota/cgroup facts and, if unavailable without a job, explicitly retain the risk and require a separately approved bounded run that can stop safely. |
| Output size | GO, projection only | 66,715,648-byte projected ceiling is below 512 MiB. | Verify free space/quota and exact fresh paths at preflight; monitor captures logs and candidate bytes. |
| Direct/restart acceptance | NO-GO for binary pass/fail | Both input paths are closed by the contract, but output relation is unmeasured and no governed tolerance exists. | Treat comparisons as reported diagnostics only until a justified acceptance criterion is separately established. |
| Scientific/canonical promotion | NO-GO | Existing gates and contract explicitly deny authority. | No promotion is in scope; preserve all gates. |

The unresolved provider/runtime identity, unknown Fair memory/capacity, and lack of
workload timing evidence mean that an authorization proposal is not yet ready on
the current record. This is not a judgment that the engineering run is unsafe or
physically invalid; those propositions remain untested.

## Required next action

Before revisiting an authorization proposal, an already authorized Fair operator
must perform a **read-only** final preflight on the exact reviewed candidate commit:
verify the active branch/full HEAD, isolated Python 3.12.10 / NumPy 2.3.5 runtime,
governed provider root and all input hashes, R4 manifest/checkpoint, source-composite
identity, evidence-root existence/free space/quota, and available memory plus any
actual scheduler/cgroup limits. Confirm both fresh candidate/supervision paths are
absent and the unchanged contract still says execution is unauthorized. Return the
preflight record for a separate authorization decision. Do not run execute mode as
part of that preflight. If memory enforcement or a reliable resource observation
is unavailable without launching a job, record that as `UNKNOWN`; do not claim a
hard quota. Numerical direct/restart tolerances remain `THRESHOLD_UNJUSTIFIED` and
must not be invented as part of the preflight.

## Preserved gates

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`;
`RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`;
`INT3_ENG10K_EXECUTION_AUTHORIZED=false`.

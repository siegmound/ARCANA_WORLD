# INT-1B — Evidence Density and Distinct-Regime Selection

Date: 2026-10-13

Source branch/HEAD: `r6/si1-bandwidth-f2av` / `bd9563182d7c8c5b37358d10b025a55c8bc2c8a2`

Decision: `INT1B_NEXT_EVIDENCE_EXPERIMENT_DEFINED__EXECUTION_NOT_AUTHORIZED`

## Scope and evidence identity

This is a read-only design based on the verified INT-0B-R4 noncanonical bundle and the INT-1A retention analysis. The R4 manifest SHA256 is `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`; the R4 sample artifact SHA256 is `ca9c5a4bc6ff4441b198219183e4e564a391d239dfda6e2f87598b7bd14bebad`. The source commit was `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`, with source-composite identity `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`. The current offline bundle verifier and provenance check passed; the INT-1A test suite passed 12 tests. No provider-backed evolution, new run, Fair access, or WORLD_HISTORY access occurred in this task.

INT-1A describes one 1,000-engineering-year pair-5:11 trajectory with two admitted supports. Each support has four records at 0, 484.6791203689449, 969.6005802980742, and 1,000 years. Both support series are numerically identical in the observed output. There are only two interior timestamps, so the audit can compare retention choices on these records but cannot characterize aliasing, online selection, event capture, or a general retention interval. The retrospective adaptive selector used the full trajectory and is not causal. Reported subset reconstruction errors and byte sizes remain case-specific diagnostics; no acceptance threshold or persistent-state policy follows from them.

The measured series include width, crust and lithosphere thickness, beta, accumulated strain, the nodal temperature profile, and material/depth coordinates. Across the interval, width changed by +114.67052868815 m, crust by -28.85532252368 m, lithosphere by -82.44377863906 m, beta by +0.00103161035619, accumulated strain by +0.00103107861189, and maximum nodal temperature by 0.07193306832937196 K. Maximum area-relative error over the three resolution levels was 0, `2.1448848114876e-16`, and `2.1448848114876e-16`. These are outputs of this reduced engineering configuration only.

INT-1A's endpoints-only subset retained 2/4 records (58,905 bytes, 31.17% smaller than the full 85,583-byte sample JSON); either one-interior subset retained 3/4 (72,233 or 72,261 bytes, about 15.6% smaller). For endpoints-only reconstruction, maximum absolute errors included 0.0074311595 m crust, 0.0212318843 m lithosphere/depth, 0.0005829507 K temperature, and 2,361.25 m² derived area. Retaining the first interior sample reduced those respective maxima to 0.0004381543 m, 0.0012518693 m, 0.0000630044 K, and 139.293 m²; this is an observed comparison, not an accuracy threshold. The retrospective selector chose that first interior record (score 0.04289455594) after seeing the complete trajectory. Its choice cannot demonstrate an online policy. The full paired checkpoint JSON is 83,624 bytes, but this does not measure B0 HistoryStore storage or restart cost.

## Why there are four samples

`src/arcana_worldsim/r6/functional_development.py::pure_shear_thermal_step` notifies its observer once for the initial state and after every completed integration substep. The step size is the minimum of the remaining duration, 0.8 times a diffusion stability limit, and—when extension is positive—the configured kinematic fraction times current width divided by extension velocity. It tightens the step against the updated geometry before advancing. A one-million-step guard is an error bound, not a sampling target.

The R4 run used resolution factors `(0.001, 0.0005, 0.00025)` and captured diagnostic samples only on the middle factor, as implemented in `scripts/r6_functional_development_t_f2b.py`. The recorded middle run took three substeps per side. Initial plus three post-step observations therefore yielded four records. The diffusion stability minimum was about `659175626487.45 s`, versus the 1,000-year duration `31557600000 s`; the kinematic step restriction was the active limiter in this run. `src/arcana_worldsim/r6/int0a_pipeline.py` captures every substep; its cap of 10,001 records/support is only a maximum. The observer is not a fixed-interval sampler, and the records are not persistent `HistoryStore` states.

## Distinct admissible candidate

The R4 `EDGE_AUDIT_MATRIX.json` contains 15 classified pair-5:11 edges, eight eligible two-sided admitted nonjunction extensions, and a pair status `ELIGIBLE_QUIESCENT`. This status is not event or activation authority. The existing selected R4 edge is `R6BND-T0-3eb57747e6f0a3f3305f`, with hot-extended supports `R6G1D-R091-C029` and `R6G1D-R091-C028`.

The bounded alternative selected for a future experiment is the already audited edge `R6BND-T0-27e4d497530e681071fb` (parent edge row 94, column 25, axis EAST):

| Property | Plate 5 side | Plate 11 side |
|---|---|---|
| Support | `R6G1D-R094-C026` | `R6G1D-R094-C025` |
| Admitted class | `CONTINENTAL_NORMAL` | `CONTINENTAL_NORMAL` |
| Crust | 35,000 m | 35,000 m |
| Reference lithosphere | 135,000 m | 135,000 m |
| Reference surface heat flow | 0.06 W/m² | 0.06 W/m² |
| Signed opening from the existing Euler provider | — | 0.10694074272424924 m/year |

The edge audit records exact partition mapping, two admitted sides, positive extension, no junction adjacency, and `ELIGIBLE_QUIESCENT`. Relative to the R4 hot-extended support values (28,000 m crust, 80,000 m reference lithosphere, 0.085 W/m², and 0.11467052868814648 m/year), this is a distinct, provider-backed thermal/geometric support class and has a different edge-specific Euler opening. It is not evidence of a different composition or rheological family: the candidate's fully materialized profiles and material tuple must be reloaded and compared in the next read-only preflight. The table does not contain a complete candidate `T(z)` profile.

The alternative mixed normal/hot edge is excluded from this proposal because the audited endpoint-junction treatment is unbound. The B6 rift pair 1:3 is a different case and must not be spliced into this experiment.

## Minimum informative experiment proposal

**One new noncanonical pair-5:11 run**, using the existing T0=210 Ma initializer, provider-backed edge-specific frozen Euler forcing, 1,000 engineering years, the existing reduced thermal kernel, same boundary conditions, and existing resolution controls. Select only the audited normal edge above. Preserve the existing factors `(0.001, 0.0005, 0.00025)` and add the next halved kinematic fraction `0.000125`. Capture every numerical substep on the finest factor, including initial and completed states, and bind the checkpoint, trajectory, and replay comparison to that same factor. This adds a systematic refinement rung rather than manufacturing samples by changing observation timing or stability controls. The expected sample count is not guaranteed; record actual substeps and times.

The current runner hard-selects the lower median eligible edge through `audit_pair_5_11`; it has no boundary selector. The candidate change should be narrow: accept an explicit boundary ID, require it to occur exactly once in the verified eligible edge matrix, and retain every existing admission, support, profile, and kinematics check. The runner must preserve the selected edge identity and derive all outputs from its re-materialized profiles and Euler result. No interpolation, support resampling, new equation, new material parameter, or event claim is allowed.

For comparison, re-use the immutable R4 hot-extended record at the common existing resolution `0.00025` and compare support-class inputs and outputs as an engineering contrast. The relevant kernel, support audit, pipeline, and runner files have no content diff between R4 source `91fc83d` and current HEAD, so the equation/step implementation has not changed in that interval. The new run still needs its own source-composite identity and provider hashes. The comparison isolates an existing provider-supported support/edge case within the same unchanged code path; it does not isolate thermal class from the edge-specific forcing or establish physical causation.

For retention analysis, compute full, endpoints-only, fixed interior, retrospective adaptive, and a separately labeled causal/online policy only if that policy can be defined using information available at each decision time. Keep retrospective results distinct. Serialize the measured full diagnostic trajectory and candidate subsets using the existing deterministic format; measure bytes instead of extrapolating a general storage policy. Record restart/replay on the selected same resolution and retain the existing explicit statement that B0 registration is descriptor-only.

## Preliminary resource envelope

R4 observations: 20.633493 s elapsed, sampled process-tree working-set peak 164,384,768 bytes, output directory 691,140 cumulative bytes according to the supervisor; the nine-file candidate bundle itself was 690,844 bytes. These are observed measurements from one prior run, with sampled operational monitoring, not hard quotas or a predictive guarantee. The R4 sample JSON is 85,583 bytes; its paired full checkpoint is 83,624 bytes.

The additional refinement increases integration work. Using the observed R4 three substeps at 0.0005 and five at 0.00025 as local reference, a halved 0.000125 step is expected to require more substeps (roughly eight is only a planning estimate from the kinematic scale, not a result). Capturing every step will increase sample artifact size; use the existing record schema and observed serialization to plan, then measure actual bytes. Do not present a linear extrapolation as an RSS bound. For any later separately authorized run, retain the prior monitored ceilings of 900 seconds, 2 GiB process-tree working set, and 512 MiB output as operational stop thresholds only; recheck the host, destinations, source, inputs, and supervisor immediately before execution. `RESOURCE_2GB_SCOPE_UNRESOLVED` remains open.

## B0 restart readiness and remaining UNKNOWNs

The R4 artifacts show deterministic direct replay/restart within the reduced kernel and matching same-run state hashes; restart versus uninterrupted maximum temperature difference was `9.992213563236874e-07 K` per support. This does not demonstrate B0 `HistoryStore` registration or executable closed-input reconstruction. The checkpoint carries state, materials, boundary data, and configuration links, while the replay recipe is explicitly `DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE`.

Before a later retention/reconstruction execution is considered, the minimum gap is an adapter that binds the candidate checkpoint and replay recipe to the exact support IDs, materialized T0 profiles, edge-derived forcing, duration, resolution, kernel/build identity, and expected initial-state digest; then register/query/replay through the intended B0 service and compare the reconstructed state to the recorded checkpoint. Measure its cost on the new candidate only after authorization. Do not create a generic checkpoint framework here.

Still UNKNOWN: complete normal-support `T(z)` and material-tuple comparison until re-materialized; number of steps/samples at 0.000125; actual runtime/RSS/output cost for the alternate edge; causal retention behavior; B0 HistoryStore executable replay and its cost; physical representativeness, event occurrence, long-term retention, scientific accuracy, and any canonical use. No physical event authority is inferred from `ELIGIBLE_QUIESCENT`.

## Authorization contract and decision

This report authorizes no execution. A future request must authorize one new, noncanonical run with the exact boundary ID, both support IDs, freshly verified provider/source identities, Python/NumPy environment, fixed 1,000-year scope, the four-factor ladder, finest-factor observer binding, new absent output and supervision directories, active stop monitoring, and immutable partial-failure handling. No retries, alternative boundary, pair 1:3, physics/forcing changes, Fair/MPI/ShellSet/Solver, or WORLD_HISTORY access/publication are included. Any missing profile, changed hash, ineligible edge, non-finite state, or unverified checkpoint/replay binding blocks before evolution.

The next evidence experiment is specified but not authorized: `INT1B_NEXT_EVIDENCE_EXPERIMENT_DEFINED__EXECUTION_NOT_AUTHORIZED`. INT-1A results remain case-specific; all prior successful and failed evidence remains immutable. Preserved gates: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

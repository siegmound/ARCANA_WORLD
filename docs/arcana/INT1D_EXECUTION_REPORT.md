# INT-1D — Distinct-boundary execution and offline retention comparison

Date: 2026-10-14
Repository branch: `r6/si1-bandwidth-f2av`
Execution source commit: `3fa149b7639f59c934a4d722acb388eacc4c9628` (parent `54c0cce119da9e061545792840f9b7c430159c7c`)
Decision: `INT1D_DISTINCT_BOUNDARY_TRAJECTORY_EVIDENCED__GENERAL_RETENTION_POLICY_NOT_QUALIFIED`

## Scope and authority

One conditionally authorized, local, noncanonical T-F2B engineering run was executed for ordered pair 5:11 at T0=210 Ma, using the explicit boundary `R6BND-T0-27e4d497530e681071fb`, the existing frozen Euler forcing and reduced thermal kernel, 1,000 engineering years, and resolution factors 0.001/0.0005/0.00025/0.000125. Diagnostics were recorded at 0.000125; the reference checkpoint/restart remained at 0.0005. No retry or parameter substitution occurred.

The final-source provider audit selected the requested boundary as `ELIGIBLE`, with no blockers, two admitted `CONTINENTAL_NORMAL` supports (`R6G1D-R094-C026`, `R6G1D-R094-C025`), 73 profile nodes per side and signed `Ux=0.10694074272424924 m/year`. The source-composite identity is `a1a4503fe57206750884e454d8a12d778caee38e34b35586805241ad51c01954`. The audit result is 101,193 bytes, SHA256 `3102121346ba63c0cd266d9799c33f5300e1eda79f4e2bd8bb95a2337458a8c3`; its child diagnostic records the configured external root, physical payload present, and both Git object-store environment variables absent. Provider member identities are recorded in the candidate manifest and run result. The audit is read-only provider evidence, not a scientific qualification.

Post-commit offline verification used the existing INT-1A retention evaluator. The R4 reference bundle was independently rechecked with its fixed manifest identity and `validate_r4_provenance`; its original files were not modified. The new artifact set and supervisor records were read-only during verification. Python 3.12.10, NumPy 2.3.5 and pytest 9.1.1 were used for the post-commit targeted suite; 65 tests passed. The suite included the supervisor environment/path tests and provider-dependent spatial-support tests. The provider audit, run artifacts, and this report remain distinct evidence objects.

## Candidate bundle integrity

Candidate directory: `outputs/r6_functional_development/INT1D_TF2B_5_11_R094C025_C026_20261014_02/`
Manifest: `CANDIDATE_MANIFEST.json`, 2,630 bytes, SHA256 `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`.
The directory has exactly nine regular files: the manifest, `RUN_RESULT.json`, and its seven listed members. Every listed byte count and SHA256 matched, as did the manifest's separate RUN_RESULT entry and the run result's artifact hash map.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `CANDIDATE_CHECKPOINT.json` | 84,879 | `b3da8fa3053620bdcea5dba9f5614a274327d7d82cd876a653c18f8198a93cb7` |
| `CANDIDATE_TRAJECTORY.json` | 217,802 | `0a09459471dcb9f85f205497dfa9bcff74d17ccb69cdcb5df0cfe1b1ad7436d6` |
| `DIAGNOSTIC_NUMERICAL_SAMPLES.json` | 157,705 | `540c668b7e0e186e7c0efe36e5fc94d1afe09550a2f5b235ef3485e8b77b1916` |
| `EDGE_AUDIT_MATRIX.json` | 98,359 | `5bbf524d40c7560533640a61f1a9be27a2b4b3f677b49e41f39f6f77c46ec46a` |
| `REPLAY_RESTART.json` | 926 | `3f7d4dfe2466c6eeca306c3aa51c523fb9510bbcca3be3464a94941018339f84` |
| `RUN_RESULT.json` | 8,901 | `603c4e36c7f25d29df300bedb5496bd8ecfb5fa471fb07c29a41af096e3a469b` |
| `SELECTED_SECTION_AND_PROFILES.json` | 50,059 | `4e9c23e0451063461d2648c3aa407a91f8206e61823e46691fb540202fa4fa91` |
| `THERMAL_CONVERGENCE.json` | 200,193 | `8ee8b2c19946a798270e59a3420a1b8507d5c08b5eaf8a7def6fbdc78cee07a0` |
| `CANDIDATE_MANIFEST.json` | 2,630 | `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571` |

The seven manifest members plus `RUN_RESULT.json` total 821,454 bytes. `RUN_RESULT.json` records `canonical_publication=false`, `world_history_accessed=false`, `world_history_mutated=false`, and false for the other preserved non-actions. The trajectory carries the same noncanonical and WORLD_HISTORY flags. Tracked Git state was clean after the run; no canonical publication was made. These run-record flags and repository status are the evidence for non-access/non-mutation; this audit did not independently snapshot an external canonical store.

## Supervisor observations

Supervisor evidence: `outputs/r6_functional_development/INT1D_SUPERVISION_20261014_02/`. The recorded command used the explicit Python 3.12 executable and the intended runner, repository root, branch, boundary, two 0.000125 overrides and candidate destination. Root process PID was 37920 (`python.exe`); 214 process-tree observations were recorded at 100 ms polling. The trace includes the Python root and observed descendants when present. It records natural exit, classification `NATURAL_EXIT_SUCCESS`, exit code 0, elapsed time 24.314529 s, sampled process-tree working-set peak 173,670,400 bytes and cumulative output peak/final total 821,761 bytes. Captured stdout was 307 bytes (SHA256 `b803066db2bb8ba4ef1e771bfa27a128ad22f581c9c4676959042b50e4f708a9`); stderr was empty (SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).

All three monitored thresholds (900 s, 2 GiB process-tree working set, 512 MiB cumulative output) remained below their limits. They are sampled operational thresholds, not OS-enforced quotas. The self-test separately exercised termination on synthetic resource limits and natural exit propagation; the INT-1D run itself exited naturally. The supervisor summary is 2,112 bytes, SHA256 `5f79d747ececc02f0f652d3e65be1f4eac64019387b8dda9e85af7b21f193793`; trace is 78,237 bytes, SHA256 `3cb58d87f74ce758de052269d188095bd44c3f23ea6ae44de29f384748bc15cf`.

## Samples and numerical observations

The sample document declares that all numerical substeps at the selected diagnostic rung were captured. The existing INT-1A `_validate_samples()` accepted both supports: nine records each, identical strictly increasing times, finite scalar/profile values, aligned 73-node material coordinates, and exact `elapsed_years`/`time_s` reconciliation. Times in years were:

`0, 129.57192262500018, 259.1600417403285, 388.7643593705462, 518.3848775404676, 648.0215982751603, 777.6745235999448, 907.3436555403949, 999.9999999999998`.

The final record is 2.27e-13 year below the nominal 1,000-year endpoint (about 7.6 microseconds in the serialized seconds coordinate); it corresponds to the runner's floating-point endpoint. For each support, the initial diagnostic state agrees with the trajectory's initial state. The final 0.000125 diagnostic record matches the corresponding 0.000125 convergence final state exactly across width, crust, lithosphere, beta, accumulated strain, temperature, depth and material coordinates. The 0.0005 checkpoint matches the trajectory's 0.0005 candidate state exactly. Those are distinct resolution products; no cross-resolution bitwise equality is expected.

Both supports have identical measured numerical histories in this run. Per support:

| Quantity | Initial | Final at 0.000125 | Change |
|---|---:|---:|---:|
| Width | 110,852.14113381179 m | 110,959.08187653599 m | +106.94074272420 m |
| Crust thickness | 35,000 m | 34,966.2675111217 m | -33.73248887830 m |
| Lithosphere thickness | 135,000 m | 134,869.88897146942 m | -130.11102853058 m |
| Beta | 1.0 | 1.0009647151749204 | +0.0009647151749204 |
| Accumulated strain | 0 | 0.0009642501362985 | +0.0009642501362985 |

The width change agrees, to floating-point rounding, with the frozen signed Euler rate multiplied by 1,000 years. The initial and final temperature profiles both span 280.0–1694.4975960996 K; maximum nodewise absolute change is 0.02181131702935 K. This range equality does not imply an unchanged profile. Temperatures were finite. Maximum reported area-relative error was 1.2745363550667825e-16 at the two finest rungs.

| Maximum kinematic fraction | Substeps/support | Max temperature change from initial (K) | Max profile difference from finest (K) |
|---:|---:|---:|---:|
| 0.001 | 1 | 0.02208059518807 | 0.00026927815873 |
| 0.0005 | 2 | 0.02192557499666 | 0.00011425796731 |
| 0.00025 | 4 | 0.02184921546859 | 0.00003789843925 |
| 0.000125 | 8 | 0.02181131702935 | 0 |

The refinement comparison is numerical within this fixed reduced engineering model. It is not an error bound, physical uncertainty estimate, or scientific acceptance threshold.

## Replay and restart

`REPLAY_RESTART.json` reports deterministic replay, deterministic restart and `restart_pass=true`. Both direct-state digests equal their replay counterparts (`81b68a2582435e7f78a497fa30fb569c18d40dd07effc1823606a259d5d7eff1` per side); restart-state digests equal restart/replay digests (`7387b29274af0327532d70f4ff0a355139831d93f522158b42895ada68a655a2`). Restart versus uninterrupted maximum temperature difference is 2.0189929728076095e-7 K per side. This is runner-level replay/restart evidence; B0 `HistoryStore` executable registration/query/replay remains descriptor-only and is not established here.

## Offline retention and R4 comparison

The existing evaluator in `scripts/r6_int1a_retention_audit.py` (`_validate_samples()` and `analyze_samples()`) was applied in memory to the new verified diagnostic sample document. It was not used through `run_audit()` because that entry point intentionally binds to R4. No output bundle was created or written by this comparison. The R4 bundle at `outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/` was revalidated with manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`, run-result SHA256 `b7625dfc636bc86f062ab38db42ee04215864de2390b78f69fbfe17c2438124a`, and sample SHA256 `ca9c5a4bc6ff4441b198219183e4e564a391d239dfda6e2f87598b7bd14bebad`.

R4 has four samples/support at 0, 484.6791203689449, 969.6005802980742 and 1,000 years; its diagnostic artifact is 85,583 bytes. INT-1D has nine samples/support at the times above and 157,705 bytes. The sample counts are 8 versus 18 total records across two supports.

| Retention subset (per support) | R4 | INT-1D |
|---|---:|---:|
| Endpoints only: retained records | 2/4 (50%) | 2/9 (22.22%) |
| Full diagnostic JSON | 85,583 bytes | 157,705 bytes |
| Endpoints-only deterministic JSON | 58,905 bytes (31.17% fewer bytes) | 60,347 bytes (61.73% fewer bytes) |
| One interior plus endpoints: retrospective selected time | 484.6791203689449 years | 518.3848775404676 years |
| Corresponding deterministic JSON | 72,233 bytes | 74,267 bytes |

Byte counts are for the evaluator's deterministic JSON subset serialization, not a HistoryStore encoding, RSS or a general storage cost. For INT-1D endpoints-only linear reconstruction, the maximum omitted-state errors were 6.2304372364e-5 K for temperature, 0.0081205006 m for crust and 0.0313219308 m for lithosphere. Retaining the retrospective selected interior point lowered these maxima to 1.6729669369e-5 K, 0.0021866799 m and 0.0084343367 m, respectively. The selector uses the complete trajectory and future endpoint; it is not evidence for a causal online policy. The equivalent R4 endpoint-only maxima were 5.8295069539e-4 K, 0.0074311595 m and 0.0212318843 m; its retrospective one-interior selector chose the first interior sample. No acceptance threshold was selected.

R4 is a different boundary/support regime: hot-extended supports `R6G1D-R091-C029`/`C028`, 28 km crust, 80 km reference lithosphere, 0.085 W/m² surface heat flow and signed Ux 0.11467052868814648 m/year. INT-1D is normal continental support `R6G1D-R094-C026`/`C025`, 35 km crust, 135 km reference lithosphere, 0.06 W/m² heat flow and Ux 0.10694074272424924 m/year. These factors vary together. At the shared 0.00025 rung, reported maximum temperature change from each case's own initial profile is 0.07138090020089294 K for R4 and 0.021849215468591865 K for INT-1D; this is descriptive, not a causal attribution. The recorded R4 and INT-1D sample densities also differ, so their retention error curves are case-specific and do not establish a general policy.

## Verdict, limitations and next action

The verified result is a distinct-boundary, noncanonical engineering trajectory plus case-specific offline retention measurements. The observed boundary is not classified as a geological event. No causal Earth/history interpretation, physical qualification, Solver/mechanics qualification, event-retention authority, online adaptive policy, general retention policy, or canonical publication follows from this run. The earlier `_01` supervisor launch failure and the older blocked-provider report remain immutable historical records; `_01` was not reused. No Fair, MPI, ShellSet, Solver, DGBSV, post-rift evolution or WORLD_HISTORY publication occurred.

Decision: `INT1D_DISTINCT_BOUNDARY_TRAJECTORY_EVIDENCED__GENERAL_RETENTION_POLICY_NOT_QUALIFIED`.

Next action: use the two verified noncanonical trajectories for the bounded INT-2 query/refinement/reconstruction evaluation; retain general retention policy and HistoryStore executable replay as unqualified. Any additional numerical run requires separate authorization.

Preserved gates: `BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

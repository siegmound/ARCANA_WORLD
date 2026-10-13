# INT-0B-R4 — fourth noncanonical engineering execution

Date: 2026-10-13
Decision: `INT0B_NONCANONICAL_INTEGRATED_RUN_EVIDENCED__SCIENTIFIC_PROMOTION_NOT_AUTHORIZED`

## Scope and source identity

This report records the one bounded R4 execution explicitly authorized after the offline R4 gate. It supersedes the *current-action status* in the preparation report `INT0B_R4_OFFLINE_E2E_VALIDATION.md`; that report remains an accurate record of the earlier offline-only checkpoint. The three earlier `_01`, `_02`, and `_03` failures remain separate, immutable outcomes and were not rerun or rewritten.

- Repository branch: `r6/si1-bandwidth-f2av`.
- Tested source commit: `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`; parent `50fbf6dfe1b8068a243ffa60df9ef22e1f5d6876`.
- Runner SHA256: `a0a1f87aeb865b4cecf56c515310286a3bdaa9e399548c59e5976013e2b5814b`.
- Supervisor SHA256: `9c942383f298a602acba77e313d876ec1dd50c3c0cb92b5ee345495f16baea98`.
- Provider-audit result: `outputs/r6_functional_development/INT0B_R4_PREFLIGHT_20261013_91fc83d5/provider-audit/provider-audit-result.json`, 101,132 bytes, SHA256 `1bfbc52d26a4d7565d9b9fcd1d823aca56197eb77ba8fb7ff3f0e6cb84011a17`.
- Source-composite identity from that audit: `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`.
- Runtime: Python 3.12.10, NumPy 2.3.5. The sanitized child had neither `GIT_OBJECT_DIRECTORY` nor `GIT_ALTERNATE_OBJECT_DIRECTORIES`; the governed external input root was resolved.

The read-only audit bound pair 5:11 to boundary `R6BND-T0-3eb57747e6f0a3f3305f` and admitted supports `R6G1D-R091-C029` and `R6G1D-R091-C028` (73 profile nodes each). Provider identities: vector partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`; thermal field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`; support binding index `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00`; kinematics artifact `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2`, semantic identity `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`; event census `e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e`; mapping join `b8d57495bc6e196a0b9fe7afd466079bebd97d0f63baafe232f215e45897a09f`. The selected physical-geography payload identity in the audit record is `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`.

## Execution and supervision

The exact R4 runner was launched once by `scripts/r6_int0b_supervisor.ps1` into the previously absent candidate directory `outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04`; supervisor records are in `outputs/r6_functional_development/INT0B_R4_SUPERVISION_20261013_04/`. No retry occurred.

The supervisor observed PID 39408 (`python.exe`) and its process tree, polling every 100 ms (181 samples). It classified a natural successful exit, code 0, after 20.633493 s. Sampled peak process-tree working set was 164,384,768 bytes. The sampled peak output measurement was 0 bytes, while final cumulative candidate-plus-captured-stream output was 691,140 bytes; artifact writes landed after the last sampled nonzero reading. The candidate directory itself totals 690,844 bytes. Captured stdout was 296 bytes, SHA256 `8fb2b0294f2c87c996c8c40bd0502bee675a092e23c387e6109d8f1e93cfe0f0`; stderr was empty (0 bytes), SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. The independently rerun checks confirmed both captured stream lengths and hashes against the supervisor summary. Stop reason: `NATURAL_EXIT`; no configured threshold was reached. These are sampled operational observations, not OS-enforced quotas or hard peak guarantees.

## Output integrity and temporal checks

The output directory contains exactly nine expected files: seven manifest-listed data artifacts, `RUN_RESULT.json`, and `CANDIDATE_MANIFEST.json`. The manifest schema is `ARCANA_R6_TF2B_INT0_OUTPUT_MANIFEST_V1`; `canonical_publication=false`. All seven listed members passed byte-count and SHA256 checks and exactly matched the `RUN_RESULT.json` artifact digest map. The result file also matched its manifest byte count and SHA256. The candidate-manifest SHA256 is `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`; `RUN_RESULT.json` SHA256 is `b7625dfc636bc86f062ab38db42ee04215864de2390b78f69fbfe17c2438124a`.

The run result is `CONTINENTAL_ENGINEERING_SLICE_PASS`, scope `T0_CONTINENTAL_ENGINEERING_EXTENSION_EXPERIMENT`, duration 1,000 engineering years, frozen signed Euler `Ux=0.11467052868814648 m/year`, reference width `111156.82195362539 m`, and resolution factors `0.001`, `0.0005`, `0.00025`. It reports 15 pair edges, eight admitted two-sided non-junction extensions, and `ELIGIBLE_QUIESCENT` event eligibility; this is not activation authority.

Both admitted supports have four finite samples at elapsed years `0`, `484.6791203689449`, `969.6005802980742`, and `1000`. Times are strictly increasing; each ends at `31,557,600,000 s`. Independent readback matched final sample width, crust, lithosphere, and the complete 73-node temperature profile to the corresponding trajectory candidate state. Initial values on each support were width `111156.82195362539 m`, crust `28000 m`, lithosphere `80000 m`; final values were width `111271.49248231354 m`, crust `27971.144677476324 m`, lithosphere `79917.55622136094 m`. At the sampled middle-resolution trajectory, maximum pointwise initial-to-final temperature change was `0.07193306832937196 K`; the recorded profile range was 280 K to 1671.771417700828 K. These are outputs of the reduced engineering kernel, not geotherm or physical-rift qualification.

All resolution runs reported finite temperatures. Maximum area-relative errors were `0`, `2.1448848114876e-16`, and `2.1448848114876e-16` for the three factors. Maximum temperature differences relative to the finest run were `0.001696950341511183 K`, `0.0005521681284790247 K`, and `0 K`. The recorded stability ratios were `0.046404458010204666`, `0.023213841714926093`, and `0.011609826213934265`. The replay/restart artifact agrees exactly with the corresponding result object: deterministic replay/restart and restart pass are true; direct/replay hashes agree per support. Restart versus uninterrupted maximum temperature difference was `9.992213563236874e-07 K` per support. The B0 trajectory replay descriptor remains `DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE`.

## Output digest index

The manifest lists these seven payload artifacts. SHA256 and byte counts were independently recomputed from the local files; RUN_RESULT is independently recorded in the manifest and reconciles with its artifact digest map.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| CANDIDATE_CHECKPOINT.json | 83,624 | 3aaf0a8aafe69798087abb7c4ca17c082a54941fb79c409ada117871194a71e0 |
| CANDIDATE_TRAJECTORY.json | 215,173 | 5a9d238dfe51dc3c8f4da5590a6f6a882db5dfc3bb04d9e97894398babbecbd1 |
| DIAGNOSTIC_NUMERICAL_SAMPLES.json | 85,583 | ca9c5a4bc6ff4441b198219183e4e564a391d239dfda6e2f87598b7bd14bebad |
| EDGE_AUDIT_MATRIX.json | 98,300 | d89bd4d9cca8928f8e6b913ad6bf1955c429ac2e2e1bb4dc6b6263f7165a59c7 |
| REPLAY_RESTART.json | 924 | baee231f00d65cb463aced5fe7d3cf3ce5969d26cd0d40dceec4bdd8702b510c |
| SELECTED_SECTION_AND_PROFILES.json | 49,603 | 57d841424d31673fb4586ad9978b95e075591cacab02b78c909e351e929621ae |
| THERMAL_CONVERGENCE.json | 148,380 | dc1ac1437f5beb5ce978c9ec0179778dd2d36f4d5886ac3e0883649b696a7f84 |
| RUN_RESULT.json | 7,127 | b7625dfc636bc86f062ab38db42ee04215864de2390b78f69fbfe17c2438124a |
| CANDIDATE_MANIFEST.json | 2,130 | 191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236 |

## Interpretation and boundaries

The provider-backed, noncanonical integrated engineering trajectory is evidenced and its output bundle was checked. The calculation couples the admitted pair-5:11 support, frozen Euler forcing and existing reduced thermal kernel only within this 1,000-year engineering interval. It does not qualify the lateral physical section, long-term temporal applicability, physical event activation, a rift, or ARCANA mechanics. The trajectory is not registered in canonical `HistoryStore`; `WORLD_HISTORY` was not accessed or mutated according to the run record, and all recorded non-actions are false. No canonical checkpoint or publication was created.

Preserved gates: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. The next bounded milestone is INT-1 empirical state-retention and reconstruction analysis using this trajectory; no additional INT-0B execution is authorized by this report.

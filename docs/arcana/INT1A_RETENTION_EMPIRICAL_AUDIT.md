# INT-1A — Empirical state retention and reconstruction audit

Date: 2026-10-13
Decision: `INT1A_RETENTION_EMPIRICAL_BASELINE_EVIDENCED__GENERAL_POLICY_NOT_QUALIFIED`

## Scope and authority

This is an offline analysis of the immutable, noncanonical INT-0B-R4 engineering bundle at `outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/`. No provider-backed evolution or new physical-model calculation was performed; retention and reconstruction metrics were computed offline from the recorded samples. No Fair/MPI/ShellSet/Solver execution or WORLD_HISTORY access was performed. The source execution was commit `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`, with source-composite identity `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`.

The offline evaluator checked the exact nine-file directory membership, the independently recorded R4 candidate-manifest digest `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`, every recorded size and SHA256, source commit/composite identity, provider identities, and noncanonical/replay declarations. It also cross-checked the diagnostic samples against the trajectory initial/candidate states, complete checkpoint states, run-result artifact map, and replay/restart record. Full diagnostic JSON reserialization matched its acquired bytes exactly. These checks establish identity and internal consistency against the repository's recorded R4 evidence; they do not independently reacquire the external provider payloads or elevate their authority.

Machine-readable results and deterministic retention storage table are in `outputs/r6_functional_development/INT1_RETENTION_20261013/FINAL/`. The final analysis manifest SHA256 is recorded by its sidecar and the manifest binds both result files to the R4 source manifest, run-result digest, source commit, and source-composite identity. An earlier first-pass INT-1 output at `outputs/r6_functional_development/INT1_RETENTION_20261013/` and a subsequent intermediate output at `outputs/r6_functional_development/INT1_RETENTION_20261013_R1/` were created during this same audit before the final cross-artifact checks were added. They are retained unchanged and superseded by the `FINAL/` result; only `FINAL/` is the reviewed result.

## Actual trajectory and field inventory

The diagnostic artifact is 85,583 bytes and contains four recorded states per support, at elapsed years `0`, `484.6791203689449`, `969.6005802980742`, and `1000`. The two support records have the same times, material coordinates, and observed numerical field values; they remain separate support identities, not independent trajectories. There are two interior observation times per support. Endpoint-only reconstruction therefore provides two omitted-time comparisons per support (four support/time comparisons total), but only two distinct interior times and one engineering configuration.

| Field | Unit / representation | Observed role and temporal status | Persistence implication |
|---|---|---|---|
| `time_s`, `elapsed_years` | s, year; JSON numbers | Recorded time coordinates; elapsed years are derived from seconds in the runner | Keep one authoritative time coordinate and the conversion/configuration if exact replay is required |
| `width_m` | m; JSON binary64-compatible number | Evolving reduced-state geometry | Needed to restore the reduced state |
| `crust_m`, `lithosphere_m` | m; JSON binary64-compatible numbers | Evolving reduced-state geometry | Needed to restore the reduced state |
| `temperature_k` | K; 73-element array | Evolving thermal state on material-coordinate nodes | Needed for restart; node correspondence must be preserved |
| `material_coordinate` | dimensionless; 73-element array | Fixed Lagrangian/material support; exactly unchanged across samples | Needed to associate temperature nodes and reconstruct physical depth |
| `z_m` | m; 73-element array | Derived as `material_coordinate × lithosphere_m`; stored in each diagnostic record | Recomputable from retained material coordinates and lithosphere, but retained for diagnostics |
| `beta` | dimensionless scalar | Derived from `width_m / initial_width_m` in the state | Recomputable if the initial-width anchor is retained; exact floating-point bits are not promised by recomputation |
| `accumulated_strain` | dimensionless scalar | Updated as `ln(beta)` in the reduced kernel | Recomputable from beta by the declared kernel relation; this does not independently identify the operator |
| `area_m2` | m²; complete endpoint/checkpoint only | Derived diagnostic `width_m × lithosphere_m`; near-conserved by the engineering pure-shear update | Recomputable; not present in compact intermediate records |
| `materials` | per-node density, conductivity, heat capacity, radiogenic production, role | Fixed material configuration; omitted from compact intermediate samples, present in full endpoint/checkpoint | Required, with boundary values and code/configuration identity, for executable restart |
| initial widths/thicknesses, boundary temperatures, `crust_fraction` | m, K, dimensionless | Initial-state/configuration values; complete in the checkpoint/full endpoint, not repeated in compact samples | Required initialization/configuration authority; compact samples alone are not a restart checkpoint |

The complete `CANDIDATE_CHECKPOINT.json` is 83,624 bytes and contains initial and candidate reduced states for both supports. It is a complete endpoint/checkpoint artifact under this runner's schema, not a measured HistoryStore representation or a defined minimum physical-state encoding. Compact intermediate diagnostic records omit material properties and initial/boundary configuration, so they are not independently restartable.

## Observed state changes

Values below are the recorded initial-to-final differences and apply identically to both supports.

| Quantity | Initial | Final | Absolute change | Relative change |
|---|---:|---:|---:|---:|
| Width | 111,156.82195362539 m | 111,271.49248231354 m | +114.67052868815 m | +0.00103161035619 |
| Crust thickness | 28,000 m | 27,971.144677476324 m | −28.85532252368 m | −0.00103054723299 |
| Lithosphere thickness | 80,000 m | 79,917.55622136094 m | −82.44377863906 m | −0.00103054723299 |
| `beta` | 1 | 1.0010316103561865 | +0.00103161035619 | +0.00103161035619 |
| Accumulated strain | 0 | 0.0010310786118935147 | +0.00103107861189 | undefined: zero initial reference |
| Maximum nodal temperature change | — | — | 0.07193306832937196 K (maximum absolute node change) | Not summarized by one scalar-relative ratio |

The sampled temperature extrema remain 280 K and 1671.771417700828 K. Material-coordinate arrays are exactly aligned across all four samples; `z_m` changes consistently with lithosphere thickness. The R4 run reported maximum area-relative error across its three numerical resolutions of 0, `2.1448848114876e-16`, and `2.1448848114876e-16`. These are properties of this reduced engineering run only.

## Retention and reconstruction comparison

All omitted numerical values were reconstructed by piecewise-linear interpolation between the nearest retained **recorded** timestamps. Reconstructed records are diagnostics only, never computed physical history. Absolute error is `|observed − reconstructed|`; RMSE is the scaled root mean square over omitted values; component relative error is reported only where the observed reference is nonzero. Zero-reference/nonzero-error cases are counted and labeled undefined rather than divided by zero. No acceptance threshold was selected.

| Strategy | Retained indices (0-based) | States/support | Retention ratio | Deterministic sample JSON bytes | Change vs full |
|---|---|---:|---:|---:|---:|
| A — Full recorded diagnostics | 0,1,2,3 | 4/4 | 100% | 85,583 (actual source bytes) | reference |
| B — Fixed, endpoints only | 0,3 | 2/4 | 50% | 58,905 | −26,678 bytes (−31.17%) |
| B — Fixed, retain first interior | 0,1,3 | 3/4 | 75% | 72,233 | −13,350 bytes (−15.60%) |
| B — Fixed, retain second interior | 0,2,3 | 3/4 | 75% | 72,261 | −13,322 bytes (−15.56%) |
| C — Retrospective adaptive | 0,1,3 | 3/4 | 75% | 72,233 | −13,350 bytes (−15.60%) |

Full-set serialization is byte-identical to the source sample artifact. Subset sizes are deterministic serializations using the runner's sorted, indented UTF-8 JSON convention with subset metadata clearly relabeled as diagnostic-only. They were not written back into the source bundle. The reduction is not proportional to sample count because metadata, arrays, and the full endpoint's material records remain.

Maximum absolute reconstruction errors, identical for both support records:

| Field | Endpoints only (0,3) | First interior retained (0,1,3) | Second interior retained (0,2,3) |
|---|---:|---:|---:|
| Width (m) | 0 | 0 | 0 |
| Crust (m) | 0.007431159512635 | 0.000438154263975 | 0.006993005248660 |
| Lithosphere (m) | 0.021231884325971 | 0.001251869340194 | 0.019980014985777 |
| Beta (1) | 0 | 0 | 0 |
| Accumulated strain (1) | 1.3276700721e-7 | 7.8307862302e-9 | 1.2493752601e-7 |
| Temperature (K), maximum across nodes | 0.000582950695389 | 0.000063004406002 | 0.000534266170007 |
| `z_m` (m), maximum across nodes | 0.021231884325971 | 0.001251869340194 | 0.019980014985777 |
| Derived area `width × lithosphere` (m²) | 2,361.248821258545 | 139.293004989624 | 2,222.025426864624 |

The first-interior subset has smaller errors than the second-interior subset for these recorded fields, while width and beta reconstruct exactly under the frozen engineering forcing at these sample times. The area diagnostic does not: reconstructing width and lithosphere separately and multiplying creates a larger derived discrepancy. These observed facts do not establish a future retention interval or tolerance.

The retrospective adaptive selector chooses the interior sample with the largest endpoint-chord residual normalized by each field/node's observed range over the complete trajectory. It selects index 1 at 484.6791203689449 years, with score `0.042894555939507036`, and therefore matches the first-interior fixed subset. Because this selector uses the full trajectory, including the future endpoint and the candidate samples, it is retrospective. No causal/online rule was evaluated. No physical event transitions are established; event-driven retention remains `UNKNOWN`.

## Storage, replay and limitations

- The actual full diagnostic sample JSON is 85,583 bytes; the actual paired initial/candidate complete checkpoint JSON is 83,624 bytes, a difference of 1,959 bytes (about 2.29%). These are artifact byte counts, not RSS, a binary numeric lower bound, or HistoryStore storage costs.
- The candidate trajectory JSON is 215,173 bytes and the whole R4 bundle is 690,844 bytes. Full R4 bundle membership and all member hashes passed the offline recheck.
- The replay/restart artifact records deterministic replay/restart as passing in its same-code/runtime/configuration scope; restart versus uninterrupted maximum temperature difference was `9.992213563236874e-07 K` for each support. The B0 recipe remains `DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE`. No B0 HistoryStore replay cost or registration behavior was measured.
- A minimal physical-state persistence schema was not chosen. The existing checkpoint contains temperature, support coordinates, material properties, initialization/boundary data, state geometry and model/configuration links, but this analysis did not benchmark alternate encodings.
- There are only two distinct interior timestamps, one 1,000-year interval, one forcing/kernel/configuration, and two supports with identical observed numerical series. The fixed subsets are distinguishable for these samples, but the evidence is too sparse to evaluate temporal aliasing, event capture, online adaptation, uncertainty-aware retention, or optimal checkpoint intervals.
- No retention percentage or interval can be extrapolated to 210 Ma–present. No physical event, rift, geological validity, canonical history, or scientific qualification follows from this engineering trajectory.

## Reproducible artifacts and verification

Evaluator: `scripts/r6_int1a_retention_audit.py`. Synthetic regressions: `tests/test_r6_int1a_retention_audit.py`. Reviewed output: `outputs/r6_functional_development/INT1_RETENTION_20261013/FINAL/` containing `INT1A_RETENTION_METRICS.json`, `INT1A_RETENTION_STORAGE.csv`, `INT1A_ANALYSIS_MANIFEST.json`, and its SHA256 sidecar. Final analysis-manifest SHA256: `ad2bc118c4c7a15d56a87a3056b4d16ddedcf410f7a65a89c782d8ba41b522ce`; metrics SHA256: `7915d6786d31be3b9d6b7ea19568dbe1982cea87b561bed309d6a9de38430096`; storage-table SHA256: `47e789aa247b9d06db06f3efea2f5cf77a0d12afebbfcbe491daeecb3dc2931f`. The output manifest and sidecar were verified after writing; the source bundle remained unchanged.

The evaluator uses standard-library Python and refuses an existing/overlapping output path, unexpected source membership, mismatched digest/provenance, invalid sample ordering, nonfinite values, changed material-node correspondence, and endpoint/checkpoint/replay mismatches. Its verified source identities are pinned to this R4 bundle; it does not call the T-F2B runner.

Decision: `INT1A_RETENTION_EMPIRICAL_BASELINE_EVIDENCED__GENERAL_POLICY_NOT_QUALIFIED`.

Minimum further evidence for a general policy would be a separately authorized trajectory with a meaningfully different forcing/material regime and denser temporal observations, plus an explicit restart/storage contract. No such run is authorized here; in the absence of those inputs, retain the general policy as `UNKNOWN`.

Preserved gates: `BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

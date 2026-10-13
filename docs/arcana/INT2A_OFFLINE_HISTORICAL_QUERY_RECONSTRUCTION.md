# INT-2A — Offline historical query and reconstruction baseline

Date: 2026-10-14
Source checkout: `r6/si1-bandwidth-f2av`, HEAD `5874f6e161aa086f4adbc53647960052ef7e6bf3`
Decision: `INT2A_OFFLINE_HISTORICAL_QUERY_RECONSTRUCTION_EVIDENCED__B0_EXECUTABLE_BINDING_NOT_QUALIFIED`

## Scope and authority

This gate implements a read-only query over two already-existing, noncanonical T-F2B engineering bundles. It performs no provider-backed evolution, no physical refinement, no Fair/MPI/ShellSet/Solver work, and no read or write of `WORLD_HISTORY`. The execution commits recorded below are the numerical source identities; `5874f6e` is the checkout used for this offline analysis, not the source commit of either trajectory.

The result is engineering evidence only. `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` remain unchanged.

## Input bundle verification

The R4 bundle was loaded through `scripts/r6_int1a_retention_audit.py`'s bounded snapshot loader and its existing `validate_r4_provenance`. INT-1D uses a parallel, narrowly pinned verifier in `scripts/r6_int2a_historical_query.py`: it checks the fixed manifest digest and every member size/digest, exact nine-file directory membership, run/manifest/trajectory artifact maps, provider and source identities, boundary/support selection, sample chronology, separate 0.000125 diagnostic versus 0.0005 checkpoint endpoints, and replay descriptor binding. Both sample documents also pass the existing INT-1A `_validate_samples`; the INT-1A `_interp`, `_difference_metrics`, `_retained_document`, and `analyze_samples` functions supply the temporal interpolation and retention/error calculations.

| Bundle | Numerical source commit | Recorded source-composite identity | Manifest SHA256 | Run-result SHA256 | Samples SHA256 | Members |
|---|---|---|---|---|---|---:|
| R4, `INT0B_TF2B_5_11_R4_20261013_04` | `91fc83d50ec15d8bb9b826926ac2f2dc859281e8` | `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca` | `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236` | `b7625dfc636bc86f062ab38db42ee04215864de2390b78f69fbfe17c2438124a` | `ca9c5a4bc6ff4441b198219183e4e564a391d239dfda6e2f87598b7bd14bebad` | 9 |
| INT-1D, `INT1D_TF2B_5_11_R094C025_C026_20261014_02` | `3fa149b7639f59c934a4d722acb388eacc4c9628` | `a1a4503fe57206750884e454d8a12d778caee38e34b35586805241ad51c01954` | `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571` | `603c4e36c7f25d29df300bedb5496bd8ecfb5fa471fb07c29a41af096e3a469b` | `540c668b7e0e186e7c0efe36e5fc94d1afe09550a2f5b235ef3485e8b77b1916` | 9 |

For each bundle, the manifest, `RUN_RESULT.json`, and all seven listed members were opened as bounded byte snapshots, SHA256-checked, then parsed from those bytes. The source directories were not modified. Source-commit and source-composite values are the values bound in the verified historical run artifacts/reports; this work does not recompute historical builds or provider payloads.

R4 has four samples per support at 0, 484.6791203689449, 969.6005802980742, and 1000 years; its sample artifact is 85,583 bytes. INT-1D has nine samples per support at 0, 129.57192262500018, 259.1600417403285, 388.7643593705462, 518.3848775404676, 648.0215982751603, 777.6745235999448, 907.3436555403949, and 999.9999999999998 years; its sample artifact is 157,705 bytes. The stored irregular times are used directly. Within each experiment the two support histories are numerically identical across the compared stored fields; the two supports are not counted as independent evidence.

## Query contract

Implementation: `scripts/r6_int2a_historical_query.py`; tests: `tests/test_r6_int2a_historical_query.py`.

- `EXACT_OBSERVED` requires exact equality with a verified stored `elapsed_years` value. A near timestamp is rejected; no nearest-sample substitution occurs.
- `BRACKET` returns the two observed records strictly surrounding an interior request. Exact hits must use `EXACT_OBSERVED`; out-of-range requests fail.
- `DIAGNOSTIC_RECONSTRUCTION` uses the existing INT-1A piecewise-linear time interpolation operation on numeric scalar/profile fields. Profile values are paired only by identical, exactly matching `material_coordinate` arrays and node index. No spatial resampling is performed.
- Numeric fields are `width_m`, `crust_m`, `lithosphere_m`, `beta`, `accumulated_strain`, `temperature_k`, `z_m`, and (observed-only) `material_coordinate`. Categorical/authority/material records are unsupported. Material-coordinate profiles cannot be reconstructed.
- Nonfinite/negative/out-of-range times, unknown supports, unsupported fields/modes, missing bundles, malformed provenance, incompatible profile support, and interpolation outside a strict bracket fail closed.
- Results identify experiment, execution source commit and recorded source-composite identity, manifest/run/sample digests, boundary, support, elapsed time or bracket, field/units, resolution rung and sampling mode. Each result labels observed versus reconstructed and states that scientific authority is UNKNOWN and the answer is not canonical.

Verified examples in the generated result include R4 support `R6G1D-R091-C029`, exact observed `width_m=111156.82195362539 m` at year 0; an INT-1D temperature bracket around year 200 bounded by observed times 129.57192262500018 and 259.1600417403285; and the corresponding explicitly approximate linear diagnostic reconstruction. Temporal inspection of years 200–400 returns the two existing observations at 259.1600417403285 and 388.7643593705462. These are retrieval/reconstruction examples, not new physical states. A physical-refinement request returns `PHYSICAL_REFINEMENT_NOT_EXECUTED` with unresolved kernel/executable binding, approved configuration, inputs/state provenance, numerical acceptance authority, and separate execution authorization; it does not call an evolution kernel or select a new resolution value.

## Retention answerability and errors

The evaluator compares omitted stored observations at their actual timestamps. “Exact answerable” counts retained timestamps; internal omitted timestamps remain bracketable when both retained endpoint samples exist, and can be linearly reconstructed. This is query availability, not an accuracy acceptance criterion. Full rows are reported for both supports, whose series are identical within each experiment.

| Experiment / strategy | Retained sample indices | Exact timestamps / total | Omitted interior timestamps with bracket | Serialized diagnostic JSON bytes |
|---|---|---:|---:|---:|
| R4 full | 0,1,2,3 | 4/4 | 0 | 85,583 |
| R4 endpoints | 0,3 | 2/4 | 2 | 58,905 |
| R4 fixed one interior | 0,1,3 | 3/4 | 1 | 72,233 |
| R4 fixed two interior | 0,1,2,3 (all observations) | 4/4 | 0 | 85,583 |
| R4 retrospective adaptive | 0,1,3 | 3/4 | 1 | 72,233 |
| INT-1D full | 0,1,2,3,4,5,6,7,8 | 9/9 | 0 | 157,705 |
| INT-1D endpoints | 0,8 | 2/9 | 7 | 60,347 |
| INT-1D fixed one interior | 0,4,8 | 3/9 | 6 | 74,267 |
| INT-1D fixed two interior | 0,3,6,8 | 4/9 | 5 | 88,167 |
| INT-1D retrospective adaptive | 0,4,8 | 3/9 | 6 | 74,267 |

Representative omitted-state errors (max absolute and RMSE; same per support within each run):

| Experiment / strategy | `temperature_k` (K) | `crust_m` (m) | `lithosphere_m` (m) |
|---|---:|---:|---:|
| R4 endpoints | 5.829506953887e-4 / 6.474313553207e-5 | 7.431159513e-3 / 5.291050574e-3 | 2.123188432597e-2 / 1.511728735737e-2 |
| R4 fixed one interior | 6.300440600171e-5 / 9.685863166855e-6 | 4.381542639749e-4 / 4.381542639749e-4 | 1.251869340194e-3 / 1.251869340194e-3 |
| INT-1D endpoints | 6.230437236354e-5 / 7.325052469726e-6 | 8.120500562654e-3 / 6.236839460972e-3 | 3.132193075726e-2 / 2.405638079371e-2 |
| INT-1D fixed one interior | 1.672966936894e-5 / 2.007617353504e-6 | 2.186679899751e-3 / 1.695231502458e-3 | 8.434336748905e-3 / 6.538750078130e-3 |
| INT-1D fixed two interior | 8.382529472328e-6 / 1.165557832801e-6 | 1.093408282031e-3 / 9.932519164888e-4 | 4.217431938741e-3 / 3.831114539617e-3 |

Retrospective adaptive selection uses the complete trajectory and its future endpoint. Its matching selected subset does not qualify an online policy. The R4/INT-1D difference combines distinct boundary, geometry/material support, forcing and sampling density; no unique cause is inferred. Interpolation errors are not numerical integration convergence errors. No tolerance or general retention policy is selected.

## B0 integration assessment

- `HistoryStore.find_states()` already filters registered `DomainStateEnvelope` records by history, branch, domain, time key and support cell IDs. The INT-2A reader does not duplicate that query method; it queries verified bundle records directly because the engineering JSON is not registered in a B0 store.
- `CheckpointEnvelope` supplies typed restart metadata and binds state IDs, runtime/configuration identity, seeds, dependency/authority/provider references and output manifest. It is not a historical sample query interface.
- B0 replay validates a closed set of registered checkpoint/state/forcing/event/provenance inputs and requires an injected deterministic runner to execute. The engineering run’s `DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE` replay status remains unchanged; INT-2A does not register it or call a runner.
- `MinimalStateContract` and extraction validation describe materialize/derive/refine decisions and dependency identities; they do not create a bundle-backed HistoryStore adapter or retention scheduler.

The minimum future adapter is a separately scoped, explicitly noncanonical bridge from a manifest-verified bundle to typed query records carrying stable history/branch/time-support/spatial-support and provenance references. It must use an isolated candidate store or a deliberately read-only adapter contract, must not write `WORLD_HISTORY`, and must not claim executable replay unless the closed B0 replay inputs and deterministic engine binding are actually registered and verified. This gate does not implement that adapter.

## Output and verification

Final result directory: `outputs/r6_functional_development/INT2A_HISTORICAL_QUERY_20261014_07/` (three files; separate from both inputs).

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `INT2A_QUERY_RESULTS.json` | 230,323 | `e12c139ddc85d9a29a4edd5bcd03e080b35237df3e03382e5b46e0d0614c849f` |
| `INT2A_OUTPUT_MANIFEST.json` | 580 | `b613c94c95c41df503abf0a83ed26f817e00ea6de52822b436152cdc1d84b33d` |
| `INT2A_OUTPUT_MANIFEST.json.sha256` | 93 | `b848dd1d786780714dc20df659d61c8a71fb4056558aaf497b9087b38474af6b` |

The manifest sidecar contains the manifest SHA256, the manifest binds the result size/digest and both source manifest digests, all three files passed byte readback, and the test wrote the identical result/manifest twice into separate fresh temporary directories. The output manifest itself has no self-hash entry. No local timing or HistoryStore performance claim is made.

Validation on Windows: INT-2A + INT-1A focused suites, **27 passed**; `py_compile` passed. The B0 `world_history_core`/`b0_b` suites were also attempted: 28 passed, 9 failed at `HistoryStore` setup because the managed Windows runtime denied `os.link` with `PermissionError: [WinError 5]`; those failures occur in the existing store's immutable-write primitive, before query assertions. No B0 implementation was changed. `git diff --check`, UTF-8/LF and final input/output integrity checks are recorded with the consolidation commit.

## Remaining gates

This result demonstrates offline bundle verification, exact observation lookup, strict bracketing, labeled temporal interpolation, interval inspection, and retrospective retention/query-answerability analysis for these two bundles only. It does not qualify a general retention rule, online adaptive retention, executable HistoryStore binding/replay, scientific mechanics, F2A-V, or canonical history production. Next bounded work: INT-2B, a minimal noncanonical adapter contract/prototype for exposing manifest-verified engineering states through B0 query types, with isolated-store tests and no canonical-store access.

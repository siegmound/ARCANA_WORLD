# G36-R2 FAIR repair and continued WorldSim development

27 November 2026. **FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE**, independently inspected on host `fair` in this session. Development branch `r6/g36r2-fair-repair-20261127`, based on experimental remote `r6/thermo-s3-pt-design-20261123` at `96a7d5c4ded740834edaf39ff804f393f02ea045`; fetch found no successor. The read-only runner checkout remains detached at `e37d6809`; the scientific SOURCE remains clean at `901cbb4a38916190df6a881bb561b6558dd997dd`. No checkout/reset/merge of those trees.

The complete 19-entry handoff package was read and its byte inventory retained in `R6_G36R2_HANDOFF_AND_PROVIDER_INVENTORY_NEW02/HANDOFF_PACKAGE.json`. Repeated log lines and opaque hash listings were deduplicated for review, with the complete original ZIP preserved. Historical R5/main context is not current R6 authority. The stale opening C10 ledger and original law matrix do not override newer primary evidence: in particular, initial Euler motion and a first-segment temporal law are already available. D-024/D-025 remain active.

## Executed G36-R2

Runner/test commit **`c8a2f41916b0595eabd8525d7b4ae2c4be664f07`**, parent `96a7d5c4...`. All `arcana_*.py` runners were extracted with `git ls-tree` / `git show`, and every Git blob checked. The computation ran from the frozen SOURCE using the existing `arcana-r6-linux` conda environment, one BLAS/OpenMP thread. The launch command, commit, extracted code, exit and `/usr/bin/time -v` are retained in `R6_G36R2_FAIR_CAMPAIGN_NEW01`; `RUNNER_IDENTITY.json` in the result pins every helper's SHA256. Original R0 and R1 Git blobs remain unchanged.

The local repair is `||fl+fm|| / max(||fl||,||fm||,1e-300)` with stable finite real norms. `relative` and all constitutive/pressure/traction/Jacobian computations are unchanged. Force vectors, their nonzero norms, residual vectors/norms and the actual legacy expression are saved. Both-zero forces have zero metric but cannot qualify coupling. Each full-size case also exercises the same balance predicate with a wrong-sign reaction and with the legacy metric: both must reject.

| Model | Candidate depth | Action/reaction | Legacy | Dissipation W | Verdict |
|---|---:|---:|---:|---:|---|
| native_diorite2 | 250 km | 0 | 1 | 183116583173.6852 | PASS algebra |
| native_diorite2 | 300 km | 0 | 1 | 176040680732.3127 | PASS algebra |
| native_legacy | 250 km | 0 | 1 | 526329369472.5748 | PASS algebra |
| native_legacy | 300 km | 0 | 1 | 509444504758.1963 | PASS algebra |

All 116 replay comparisons are exact in this environment. Every preserved R1 residual/dissipation, pressure diagnostic and slip-conditioning value is compared. Replay allowances are rtol `1e-12`, dimensionless atol `1e-13`, dimensional atol zero; these are replay allowances, not relaxed acceptance thresholds. Actual comparisons reproduce the prior numbers. The original pressure `<1e-12`, torque `<1e-10`, balance/virtual-work/symmetry/invariance `<1e-11`, adaptive FD `<1e-6`, complex-step `<1e-10` remain enforced. Uniform FD remains reported.

**Exit 0, 85.24 s wall, 15.82 s user + 69.60 s system, peak RSS 924260 KiB, zero swap.** This is a measurement, not a speed projection. No further rerun is needed for G36-R2. Zero builds, assemblies, solves, time advance, assignments and physical promotion. Six parent inventories and SOURCE were checked before and after. G36/R1 failures remain failed, with original manifest pins `beeee8ec...c11f` and `e984cd81...e3ae`.

Decision: `G36R2_CONSERVATIVE_INTERFACE_ALGEBRA_PASS__MANTLE_STATE_AND_NORMAL_REACTION_AUTHORITY_REQUIRED`.

## Continued path A: independent pressure provenance

`arcana_g37_independent_column_pressure.py` independently integrates PRE density on the runtime trapezoidal depth grid; it never obtains column pressure as `p_ref-sigma`. Temperature and rho/alpha are interpolated separately as in `ArcanaRuntimeEvaluateWeighted`, including crust, lithosphere and governed below-LAB thermal extension. Above-sea and submerged starts, final fractional interval and the reference-layer overlap integral are explicit. Manufactured constant/linear density and `p(z,T,rho)` analytic checks and negative-domain tests run before the real replay.

All **902160 IP** reconstruct: reference relative infinity error **4.474751221098668e-16**, anomaly **2.862462027520243e-14** against native G26, threshold unchanged at `1e-12`. Column range 574823858.3378637–6081359924.702168 Pa; 195791 land-start and 706369 submerged-start records. Sea-level exact-zero branch is covered synthetically; no real record has exact zero elevation. NEW01 is preserved; a review corrected the diagnostic domain guard to accept the runtime's last valid interval below 300 km, added a boundary test, and NEW02 verifies the final code. Actual records are below 200 km and unaffected.

**This is not full G37 physical closure.** The reconstructed pressure is relative to the runtime start datum with its water/thermal-density conventions, not an independently admitted absolute EOS pressure or normal traction on the actual interface. Native `tau_zz` is not retained by G26; error paths have not been newly tested in Fortran. Required next work is real surface normals/areas and radial work, hydrostatic/dynamic/reference separation, noncoincident mesh adjoint transfer and resultant/moment tests, cap/transition Jacobians and a physically partitioned unresolved layer. No RHS projection, arbitrary node pinning, empirical torque or mantle immobilization is admissible. This reconstruction does not authorize a mantle solve or select 250/300 km.

## Continued path B: existing ASPECT recovered

`arcana_aspect_recovery_preflight.py` uses existing `ARCANA_ASPECT_TOOLS/udocker-state/bin/proot-x86_64-4_8_0` and the existing `arcana-aspect-v310` root. Only DEBUG/OPTIMIZED `--version`, MPI/compiler version and dynamic-link inspection were executed, with a new scratch `/tmp` bind. Source is exactly `30eb77ee5da186137d436dbad35c6cb3cab64b69`; ASPECT 3.2.0-pre, deal.II 9.6.0, Trilinos 13.2.0, p4est 2.2.0, GCC 11.4, container Open MPI 4.1.2. Host MPI is a distinct environment. Targeted binary/source hashes and complete container metadata/symlink inventory are unchanged; a full-tree content rehash is explicitly not claimed.

The historical logs retain output, not complete launch argv. `COMMAND.json` therefore records a new explicit version-query command using the PRoot backend, with `UDOCKER_DIR` and workdir recovered; it does not claim unknown original flags. The udocker user/metadata setup is bypassed to preserve the historical container. X11 authorization warnings were emitted by the inherited runtime environment; both ASPECT version probes and the command exited 0. **No reinstall, plugin build, benchmark or solve.**

Independent rehash: **48/48 comparisons** from the actually available Blankenbach input/run/output checksum lists. Level 3 has no complete output manifest of the level-4 name; no such inventory is inferred. An initial inventory attempt made that false filename assumption, failed before engine execution and is preserved in NEW01; NEW02 discovers the real lists. Historic Blankenbach qualification is reused only within its synthetic scope. GEODYN-3C remains exact native-time archive/query evidence with an incomplete terminal snapshot interval, not restart or ARCANA physical evolution. Existing single-piece reader limitations remain.

The exact ASPECT tree already contains `benchmarks/hollow_sphere` and DEBUG/RELEASE plugins. Inventory and hashes are captured. Its 3D analytic Stokes benchmark prescribes analytic velocities on **both** boundaries; it does not qualify free-slip rigid modes. Upstream input uses radii 0.5/1, native seconds, end time 0, surface pressure normalization, viscosity exponent `m=3` (mu=r^(m+1)), initial refinement 4, solver tolerance `1e-6`. The source includes the hydrostatic pressure term rho0*g*(R2-r); the prose manual's isoviscous formula is not the entire parameterized implementation. Any campaign must use the exact source/postprocessor, pressure gauge, source conventions and plugin ABI. Proposed next separate authorization: isolated rank-1 synthetic refinement pair (e.g. levels 2/3 as explicitly modified diagnostic inputs, retaining upstream level 4 separately), native L1/L2 velocity/pressure and topography errors, measured memory/time, convergence and work/force diagnostics; no claim to unchanged official case or free-slip closure. No benchmark was launched.

M01 remains `PROPOSED_FOR_AUTHOR_REVIEW_NOT_EXECUTABLE`, authorial selection null, absolute pressure null, engine executions zero. G37 does not turn source delta P into an admitted absolute M01 pressure. T0 volumetric/reduced-state shell geometry, density/EOS, buoyancy, T/composition, rheology, water, heat sources, boundaries and uncertainty must be source-bound or explicitly authored before selecting a mantle provider. No automatic dry-olivine/material assignment.

## Continued path C: documentary closure, trajectory still distinct

`arcana_g18r4_documentary_closure.py` recovers only the exact observed stderr block `Warning: ieee_inexact is signaling\n    0\n` from an immutable diagnostic view. The original ID digits and tag fragments are preserved, never inferred from missing sequence positions. This reconstructs G17 ID159, G18 ID157 and G31 ID157. Negative tests reject absent IDs, duplicate IDs, unrecognized warnings and unsupported layouts.

Full actual artifact inventories, ordered worker rows, request files, pre/post matrices, response/readback identity, native source request/read/print order and residuals were rechecked: **258/258 G17, 258/258 G18, 264/264 G31 PASS**. No factorization or solve, no native rerun. Historical G18/R1/R2/R3 verdicts remain unchanged; the documentary obstruction is resolved by the new evidence, not waived.

The corrected **162-year G15 trajectory remains unqualified**. G30/G31 are endpoint/operator regression, not a trajectory. Next aggregate candidate must bind original G15 inputs/steps and corrected FB2+CSR in an isolated build, compare a corrected band baseline, and exercise heat/stress/dissipation feedback, timestep halving, mass/energy and continuous/restart parity. Do not compare to the wrong-metric trajectory as a physical oracle or add diagnostic elapsed time to history. Material/contact creation/destruction, 108 ridge and 1072 unresolved contacts remain actual process gaps; D12 exclusions and masks are preserved. Solver profiling/optimization comes after parity, with actual session limits and measured output/hash cost.

## World history beyond Physical T1

Machine-readable design: `experiments/world_history_contract_v1/contract.json`. It extends existing `DomainStateEnvelope`, `HistoryStore`, `HistoricalSnapshot` and the external trajectory archive rather than creating a competing store. This is an **unimplemented physical metadata extension design**, not a production validator or new history. It preserves exact query vs refinement separation, independent per-domain/per-region retention, causal dependency closure and real restart-complete checkpoints. Mesh mapping and multi-rank reader remain separate qualifications.

Execution order after physical prerequisites close: a bounded authorized coupled T0→T1; windowed long-integration/restart/conservation qualification; causal tectonics/topography/hydrology/erosion/sediment/resource evolution; then climate/soils/biomes and flora/fauna with H0 preserved, Deep only under explicit canonical laws, and populations/migrations/settlements/civilizations from admitted environmental support. Marine/aquatic and BIOME4 gaps stay explicit. AnchorBridge retains the 12 governed anchors and forward/endpoint-constrained ensembles; no inversion from today, silent interpolation or visual upsampling masquerading as simulation. Query and regional/epoch refinement must preserve original states and emit derived lineage and uncertainty. CHA-1 at 66 Ma, R3.21 lineage, R3.23 ensemble and H0 Deep OFF baseline remain preserved.

Physical T1, global physical torque closure, material admission, global solve and WORLD_HISTORY production remain false/null. Blocking inputs are physical state/traction authority and process closures, not lack of workstation capacity or a need to reinstall ASPECT. This turn does not claim completion of the full planetary roadmap.

## Evidence pins and reproducibility

All directories below are relative to `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6`:

| Bundle | MANIFEST SHA256 |
|---|---|
| `R6_THERMO_G36R2_INTERFACE_METRIC_REPAIR_NEW01` | `4de04df65012846fb1b6319be08085d16b8e344f4c489f5cbfb461ae46280576` |
| `R6_ASPECT_RUNTIME_RECOVERY_NEW01` | `2157bac10d69c9faba1f79a922fc2cc3ad05bef47acffad0ac18ab95e059678d` |
| `R6_G18R4_DOCUMENTARY_CLOSURE_NEW01` | `64539bd34dee9652a163aeee8eb1676c2b0f20fadeec2a99da89a5ad6cbbb593` |
| `R6_G37_COLUMN_RECONSTRUCTION_NEW02` | `5b324066945358dea2eeccc404d67b583b8ce5743aabee8f7fab6da00a350794` |
| `R6_G37_COLUMN_RECONSTRUCTION_NEW01` | `e95b537eca0a8843b4737ebaa24e03c7e6a93aa444ce56390f9497d88569c9a4` |
| `R6_G36R2_HANDOFF_AND_PROVIDER_INVENTORY_NEW02` | `d736c02b5115fb6ad0799245d27b894b298dd3b03d5774898eb669b3716e41fd` |

Final G37 NEW02 pin, exact commands, code SHA256/Git blobs and tests are additionally bound by `R6_G36R2_DEVELOPMENT_DELIVERY_NEW01`. Portable focused suite: **41 passed**, existing FAIR conda, 0.41 s. AST and Git whitespace checks also pass. No packages installed. Current session hardware/cgroup observations are in `R6_FAIR_READINESS_G36R2_NEW01.txt`; no exclusive allocation is inferred. Git commits are local FAIR development commits; no GitHub publication or merge is claimed.

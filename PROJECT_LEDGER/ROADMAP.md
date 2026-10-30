CURRENT 2026-10-30: B1 virtual lossless regional delta proof COMPLETE on FAIR: 1001/1001 exact original snapshot payload hashes and bytes, reduction 99.4897% measured only as virtual snapshot serialization bytes (1.774GB -> 9.06MB). B1 does not imply retained Deep/external history. B2-A next read-only full HISTORY file hash plus all 58000 external event and 1000 Unified Deep record SHA/canonical verification, nested events parity and original 8000 null external time. B2-B versioned B0 HistoryStore typed atomic append/year delta + separate event, annual and unified records; B2-C negative integrity; C scratch transactional committed-view query/replay; D full reconstruction; E resources/Deep/provenance all-kind query+size/performance acceptance. B1 PROJECT_LEDGER/R6_INT10K_E2C2_B1_V2_FAIR_EXACT_VIRTUAL_DELTA_PASS_20261030.md, B2-A PROJECT_LEDGER/R6_INT10K_E2C2_B2A_FULL_HISTORY_EVENT_UNIFIED_AUDIT_GATE_20261030.md. All science/production/forward flags false.

---

CURRENT 2026-10-30: E2-C2-A3 lossless synthetic deposit append-only proof PASS across all 1001 snapshots, 1000 annual records and 11000 nested event deposit matches; 50k dated /8k null-time external events known. Next E2-C2-B1 read-only virtual anchor + per-cell full appended deposits and exact changed nondeposit fields, independently reconstruct all 1001 SHA-identical snapshots and report snapshot-only virtual encoded bytes. B1 will NOT write physical archive, integrate B0, certify Deep or all historical events. After B1 and design review, B2 typify year transaction records and C use existing HistoryStore atomic committed views/retention/query/replay/refinement, then exhaustive all-kinds historical query and size/perf gates. Reports PROJECT_LEDGER/R6_INT10K_E2C2_A3_EXHAUSTIVE_DEPOSIT_HISTORY_PASS_20261030.md and PROJECT_LEDGER/R6_INT10K_E2C2_B1_VIRTUAL_LOSSLESS_DELTA_GATE_20261030.md. World-history production and solver/forward authority false.

---

CURRENT 2026-10-30 E2-C2-A2 PASS sampled deposit law (9 adjacent transitions and 40 SHA-authenticated envelopes). E2-C2-A3 NEXT READ-ONLY: exhaustively inspect 1001 snapshots and 1000 annual records original by indexed SHA; 1000 deposit-prefix and per-year deposit-to-DEPOSITION nested event multiset; count standalone external event null time_year and non-deposit changes. Only if A3 PASS, accept append-only deposit invariant for this exact synthetic fixture. Next E2-C2-B typed delta grammar + sparse anchors integrated B0 HistoryStore with Deep, temporal/causal external events, query/retention/refinement, UNKNOWN, all exact 0..1000 reconstructions. No physics rerun or production. Report PROJECT_LEDGER/R6_INT10K_E2C2_A2_AUTHENTICATED_SAMPLES_PASS_A3_ALLYEAR_GATE_20261030.md.

---

CURRENT (2026-10-30): E2-C1 scoped noncanonical PASS SEALED via R4 independent audit. E2-C2 stages: A1 source/interface and original INDEX JSONL schema census; A2 y0/1/100/500/750/1000 full snapshot/deposit field and SHA inventory; B exact delta/anchor grammar (must capture deposit fields absent from DEPOSITION); C typed HistoryStore atomic transactional adapter with committed read views and retention/query/replay; D deterministic exact time/space query/reconstructor; E exhaustive years0..1000, nine cells, all deposit identities/masses/Deep provenance and negative corruption, performance. Docs PROJECT_LEDGER/R6_INT10K_E2C1_R4_INDEPENDENT_AUDIT_SEALED_20261030.md and PROJECT_LEDGER/R6_INT10K_E2C2_A_SOURCE_API_INVENTORY_20261030.md. No 1000Y physical rerun or scientific authority.

---

## CURRENT 2026-10-30 — E2-C1 qualified by runner 3Y/10Y, independent manifest audit next; E2-C2 design opened

FAIR R4 synthetic 3Y direct/1+2, 10Y direct/5+5 history-independent by-kind exact oracle: PASS 104 tests, records 184/611; source local commit 2c71370e... unpushed. Short-run gate result `PROJECT_LEDGER/R6_INT10K_E2C1_R4_FAIR_3Y10Y_OPERATOR_PASS_20261030.md`; immutable 1000Y original retained. Independent manifest audit before final formal E2-C1 scope seal. E2-C2-A source/schema inventory, E2-C2-B event/deposit delta grammar, E2-C2-C adapter to B0 HistoryStore with transaction/committed view, E2-C2-D deterministic queries/refinement and E2-C2-E exhaustive 0..1000 oracle and performance. **Do not assume DEPOSITION events contain full deposit object/provenance; need lossless supplemental delta**. Design `PROJECT_LEDGER/R6_INT10K_E2C2_LOSSLESS_ARCHIVAL_DESIGN_GATE_20261030.md`; engineering only and authority flags unchanged.

---

## CURRENT 2026-10-30 — E2-C1-R3 PASS, E2-C1 promotion still gated

R2 negative bug (mutated excluded history accepted) reproduced; R3 fail-closed validation and 104 regression tests PASS, exact 3×7 historic checkpoint/oracle parity PASS, local source uncommitted. 7-repeat median wall vs original reduced ~3.84%/3.45%/5.98% at 101/501/751, slower than R1 because full excluded-history canonical JSON validation added; 3×3 engineering-only, no full writer benchmark. **Next:** audit R3 manifest and local diff, then deliberate source commit decision plus bounded 3Y/10Y oracle. Then E2-C2 event/deposit delta + B0 HistoryStore adapter to avoid O(T²) archived snapshots; E2-D1 and D2 after correctness. Full report `PROJECT_LEDGER/R6_INT10K_E2C1_R3_FAIR_FAILCLOSED_PARITY_PERF_RESULT_20261030.md`. Science/solver/production authority unchanged.

---

## CURRENT 2026-10-30 — E2-C1 scoped performance PASS / promotion pending

Guarded FAIR test at local source branch r6/e2c1-frontier-projection-r1-fair: 76 regressions PASS, exact 3×7 single-year history/checkpoint oracle parity PASS, ~6.8/9.4/11.5% median speedup at 101/501/751; no full 1000Y rerun. Source uncommitted. Separate unresolved fail-closed behavior for malformed excluded history requires negative-case contract review, then manifest audit and decision about commit. E2-C2 event/delta HistoryStore adapter is later and distinct. Ref PROJECT_LEDGER/R6_INT10K_E2C1_FAIR_GATE_OPERATOR_RESULT_20261030.md.

---

## CURRENT 2026-10-30 — E2-C0 COMPLETED; E2-C1 proof-first design next

E2-C0, E2-C0-B, E2-C0-C single-year cProfile and direct nested caller attribution PASS (operator logs, exact original 61-record/year hash parity at 101/501/751). ~73.3% of profiled Y751 wall is regional encode/decode plus history-independent canonical encode; includes integrity operations and cannot be assumed removable. Next design lossless frontier projection without copying soon-discarded annual history, reuse B0 HistoryStore/retention/replay/query, then exhaustive 0..1000 historical snapshot parity and bounded implementation benchmarks. See `PROJECT_LEDGER/R6_INT10K_E2C0_C_NESTED_CALLERS_20261030.md` and `NEXT_ACTION.md`. E2-D1 optimized runtime JSON/checkpoint clones after correctness; E2-D2 controlled parallelism later. World History production/solver/forward authority unchanged.

---

## CURRENT — 2026-10-30 E2-C0 single-year CPU profile and oracle parity PASS

FAIR engineering-only evidence E2_C0_REFERENCE_PARITY=PASS for years 101/501/751 (61 record kind+payload hashes/year), resumed from existing checkpoints. Profile root INT10K_E2C0_PROFILE_Piy2PjHo. Profiled wall ~0.080/0.203/0.279 s; json.dumps 110 calls/year and json.loads 12 calls/year, encode+decode ~79%,86%,87% of profiled time with growing data; unified numerical inner execution ~20 ms/year stable. Important: cProfile and hash-only consumer do not reproduce full JSONL I/O costs. Full source/limits/next in PROJECT_LEDGER/R6_INT10K_E2C0_CPROFILE_PARITY_20261030.md. NEXT E2-C0-B direct callers from saved pstats, no rerun; then B0-store-aware lossless E2-C1 schema. Engine SHA 9dce77b5... FAIR-local, separate from GitHub documentation; production/canonical authority unchanged.

---
## CURRENT — 2026-10-30: INT10K 1000Y benchmark changes E2-C/D priorities

- `E2-B2-R1`: Linux exact-commit history-independent frontier / 3Y+10Y oracle gate evidenced at baseline `9d9a2512d5e2aca5cc3fd04010d53ac467fe9839` (operator reported; originals on FAIR).
- `1000Y`: one-off synthetic engineering PASS after ULP surface-geometry correction at FAIR-local `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`; **not** scientific or production authority. 244.781 s engine loop, ~270.512 s full estimated, 1.916 GB history, peak 98.5 MiB RSS. Ref: `PROJECT_LEDGER/R6_INT10K_1000Y_FAIR_PERFORMANCE_E2C_E2D_HANDOFF_20261030.md`.
- **Priority E2-C0**: read-only phase profiling of nonlinear snapshot/deposit duplication; B0 HistoryStore reuse audit; archive/index temporal semantics. 1000Y itself already measured, do not repeat routinely.
- **E2-C1/C2**: lossless append-only event+delta material provenance + sparse sufficient-state checkpoints + deterministic exact temporal rehydration/query and history oracle parity. **E2-D1**: remove redundant JSON deep cloning/re-hash with identical physics; **E2-D2**: controlled CPU/NUMA and optional GPU/MPI parallelism only on causally separable workloads with measured speedup. **E2-E/F** transactional crash recovery, provider/config/source seal, scaling and eventual historical scientific qualification are separate gates.
- Scope: synthetic 3×3 regional basin, C028/C029 actual E0 hash-verified initial columns, synthetic environmental physics/Deep, no world-scale performance extrapolation. Other F2-B/GEODYN/provider authority gaps remain unresolved. All production/forward/solver/science qualification flags remain false.

---

# CURRENT — E2-B2-R1 source provenance corrected locally; FAIR/Linux pending (2026-10-29)

E2-B2-R1 now derives the measured-source dirty state from path-scoped Git status, records source hashes and commit separately, and fails an explicit exact-commit gate on mismatch/dirty/UNKNOWN while retaining diagnostic bundles. Local 3Y/10Y diagnostic runs passed against the local E2-A1 oracle and original E0 inputs; reports captured the dirty runner/helper state. Next: publish as a child of the E2-B2 commit by verified fast-forward, then exact-commit FAIR/Linux regression and capture. The history-free frontier still does not implement durable append-only storage, transactions, recovery or on-disk query. Later 100/1,000/10,000-year scaling requires separate evidence-gated decisions; none authorized. Report: `docs/arcana/R6_INT10K_E2_B2_HISTORY_INDEPENDENT_CONTINUATION.md`. Keep scientific, canonical and long-run gates closed.

---

# PREVIOUS CURRENT — E2-B v2 frontier projection is local/partial; legacy runner remains history-dependent (2026-10-29)

E2-A1 FAIR qualification on source `57768923a4a8478381d9153c6f910fba811613d2` is operator-reported; oracle/manifest checksums and provenance status are in the E2-A1 report. E2-B adds a canonical versioned projection and explicit history-prefix restore bridge. Local 3Y/10Y full continuation comparisons pass against Windows E2-A1 references, but the restore path supplies the entire prior history to existing runners. Dynamic deposit strata also grow with the actual model state. Do not claim streaming, append-only commit semantics, recovery, or history-independent checkpoint size. Next exact-commit Linux tests, then E2-B follow-up to move legacy consumers to archived-history APIs without dropping records/events/balances; E2-C/D/E remain separate gates. No long-run or canonical authorization.

---

# CURRENT — R6-INT10K E2-A1 complete in Windows engineering scope (2026-10-29)

`FULL_HISTORY_ORACLE_V1` now preserves the raw direct result, actual split-prefix result and checkpoint, and resumed full result for 3y 1+2 and 10y 5+5. Windows combined tests passed 60/60 and both local bundles passed manifest/hash/oracle verification. This is a full-history reference and adversarial test gate only; it is not a streaming archive, bounded frontier, transaction chain, Linux/FAIR qualification, or E1 serialized-byte comparison. Next exact-commit Linux validation, then E2-B checkpoint/frontier and E2-C+ history writer/query/transaction stages. The progression to 100/1,000/10,000 years remains future, separately reviewed and not authorized. Full report: `docs/arcana/R6_INT10K_E2_A1_FULL_HISTORY_ORACLE_IMPLEMENTATION.md`. Preserve `OBSERVE_REAL_SCALING_NO_ARBITRARY_RESOURCE_CAPS`; all scientific and canonical gates remain closed.

---

# CURRENT — R6-INT10K E1-R2 short references reported PASS; E2 streaming contract prepared (2026-10-29)

At exact source `5faf619875af86caa2ee824dff4b0a833f4227f1`, E1-R2 test/input and 3-/10-year outcomes are operator-reported PASS; FAIR evidence has not been imported/rehashed on Windows. E2 adopts `OBSERVE_REAL_SCALING_NO_ARBITRARY_RESOURCE_CAPS`: telemetry observes actual wall/CPU, process-tree memory/I/O, storage, checkpoint cost and history throughput; code does not impose arbitrary benchmark budgets. Actual FAIR allocation/site policy remains binding and unknown quotas remain UNKNOWN. Before parity claims, extend the E1 oracle with all unified steps and true split checkpoints. After qualification, sequence separate 100 → 1,000 → 10,000-year measurements, each reviewed on observed resource and integrity results; no extrapolation or run is authorized here. No scientific qualification follows. See `docs/arcana/R6_INT10K_E2_FRONTIER_HISTORY_STREAMING_CONTRACT.md`.

# CURRENT — R6-INT10K E0 code audit complete, physical inputs/runtime pending (2026-10-28)

`R6_INT10K_E0_STATIC_SOURCE_AUDIT_PASS__FAIR_INPUT_RUNTIME_PENDING__NO_EXECUTION`: read-only code review on `d3bb38756d71f39d0e4756c19040068dfa1d5673`; regional+unified path is partially coupled with annual regional surface and separate synthetic Deep, and checkpoint/full-history memory cost is unresolved. Next host source and resource binding, then new compact frontier/streamed archive and 3y/10y parity tests, and separately authorized staged 10/100/1000/10000. Parallel provider-science gap matrix open. See `docs/arcana/R6_INT10K_E0_SOURCE_AND_COUPLING_AUDIT_20261028.md`. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`.

---

# CURRENT — R6-INT10K integrated engine engineering benchmark plan (2026-10-28)

Source `736bdd1e28f5d0b2d5611c4fb22ebb692f706724`; `R6_INT10K_MULTIPHYSICS_ENGINEERING_BENCHMARK_PREPARATION` (DESIGN_ONLY__NOT_EXECUTED). Candidate: existing regional 3×3 synthetic geology/surface/hydrology runner plus unified 2-column thermal/rheology/mechanics/Deep, subject to input/streaming preflight. The older INT3-ENG10K qualified *reduced* 10k run is not evidence of 10k multiphysics stability. Stage E0 source/identity/actual coupling and safe streaming plan; later distinct authorized and supervised E1 10 years, E2 100, E3 1000, E4 10000 years. No full model without measured resource growth and validated fixed-plan checkpoints. Tuning follows baseline and identifies real numerical limitations rather than patching unproven physics. Full plan: `docs/arcana/R6_INT10K_INTEGRATED_MULTIPHYSICS_BENCHMARK_PLAN.md`.

The scientifically necessary `R6_PHYSICAL_ENVIRONMENTAL_PROVIDER_GAP_MATRIX` remains a parallel read-only lane for the 210 Ma→present resource, Deep, climate and biological target. No change to `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` or `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`.

---

# CURRENT — GEODYN-3C bounded archive closed; provider gap audit next (2026-10-28)

Decision `GEODYN_3C_EXPERIMENTAL_TRAJECTORY_ARCHIVE_FAIR_VALIDATED__ARCANA_FORWARD_NOT_AUTHORIZED` — **PASS_OPERATOR_REPORTED** for the existing synthetic engineering ASPECT trajectory archive, **not** ARCANA physical evolution. Qualified code `3c566ea61c79b8dad96274a5d68d845704aeae96` (parent `02fa91cf39f4f79885d033ad3485c0d0f86c4de9`), FAIR evidence `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN3C_20261028T171846Z`. Operator reports: JUnit **86/86 PASS** (no skip/failure/error), independent **11/11 mesh** + **99/99 typed field** comparisons, 11 snapshots/23 source files, query/integrity/negative/path/relocation tests PASS, launcher exit 0, manifest SHA256 `56bfc4789618d149fc402af2319c088fe0bbc9cabc9b1b73622393af9accd54f`; original source files and checkout unchanged, ASPECT not rerun. This report did not independently rehash the FAIR bundle or authenticate caller-declared run identity: `SYNTHETIC_ENGINEERING_ONLY`, `OPERATOR_REPORTED_UNAUTHENTICATED`. Historic R3 `GEODYN3C_20261028T164610Z` remains FAIL. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` and `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`.

**NEXT: R6_PHYSICAL_ENVIRONMENTAL_PROVIDER_GAP_MATRIX** — DESIGN_AND_READ_ONLY_EVIDENCE_AUDIT. Inventory scientifically source-backed and missing initial/boundary/forcing inputs, material/rheology/lithology, resource distributions, Deep geological stores and transport/exchange, surface/erosion, climate/hydrology and flora/fauna dependencies; include provenance, units, spatial-temporal coverage, uncertainty, provider authority, validation requirements and unresolved blockers. Target: an independently reproducible, spatiotemporally queryable **210 Ma → present** world history with selective high-resolution refinement. Unknown science is not fixed by finer resolution. No new Solver, ASPECT/MPI, ARCANA forward run or canonical writes authorized.

---

# CURRENT — GEODYN-2A parser implemented locally; FAIR evidence validation pending (2026-10-27)

The read-only ASPECT PVD/PVTU/VTU adapter is implemented and passes its local synthetic test suite. This is a software/parser result only. It does not validate the original FAIR files, solver provenance, physical interpretation, or an ARCANA model. Next dependency: run the adapter against the existing FAIR bundle after source transfer and compare against the reported GEODYN-2C audit. A later solver smoke test requires separate authorization. The ARCANA forward window remains blocked by unresolved initial fields/support mapping, EOS/rheology, boundary conditions and positive-duration forcing. No ASPECT/MPI/ShellSet run or canonical publication is authorized.

---

# CURRENT — GEODYN-1G closed; GEODYN-2 prepared, not authorized (2026-10-27)

GEODYN-1G verdict: `GEODYN_1G_FAIR_BLANKENBACH_INDEPENDENT_BENCHMARK_QUALIFIED__ARCANA_FORWARD_NOT_AUTHORIZED`. FAIR operator-reported ASPECT 3.2.0-pre Blankenbach 1a results at levels 3 and 4 and the limited refinement comparison are recorded in `docs/arcana/GEODYN_1G_FAIR_CLOSURE_GEODYN_2_PREPARATION.md`. The original FAIR artifacts were not imported/rehashed on Windows.

GEODYN-2 is preparation only. A short synthetic positive-time solver smoke test can test a future adapter but is not an ARCANA geological trajectory. ARCANA forward evolution remains blocked by source-backed initial fields/support mapping, rheology/EOS, complete boundary conditions and authorized positive-time forcing. No repeated Blankenbach run absent demonstrated need. All production and scientific gates remain closed.

---
# Archived CURRENT — prototype-first integrated physical roadmap (2026-10-25)

Decision: develop and execute small working numerical tool integrations before repeated legacy requalification and before selecting the production-scale model. The full objective remains an independently reproducible/queryable 210 Ma -> 0 ka history of tectonics, geology, materials/resources, Deep, climate/hydrology, flora/fauna, populations and civilizations. Do not treat an ENG10K engineering slice as global physics.

1. COMPLETED ENGINEERING BASE: T-F2B/R4 1k; one reduced ENG10K fixed-forcing run + Segment Archive V1; 194 archived states/8 trajectories/186 substeps; byte-for-byte parity of four numerical artifacts, Linux 57/57 tests.
2. CONTINUATION IN DEVELOPMENT: Windows-only short segment test 5k+5k and 5x2k showed small measured endpoint differences; exact archived-substep split reproduces reference. Qualified endpoint/chain code and streaming outer-manifest refactor are local uncommitted work; repeat supported-runtime tests before relying on them beyond prototype.
3. ACTIVE CODEX TASK: smallest executable coupling of existing R6 tectonics/thermal with Deep, using short noncanonical simulation and explicit synthetic inputs where historic data are missing. No legacy Deep full-history asset audit as blocking prerequisite.
4. NEXT ADDITIONS: test one concrete tool at a time for lithology/geology, physical topography, erosion/sediment/hydrology and climate boundary forcing wherever actual state feedback demands co-evolution; otherwise consume persistent prior states offline. Record missing spatial/temporal coupling variables before large runs. ShellSet/pyGPlates remain bounded candidates, not presumed compatible consumers.
5. ARCHIVE DESIGN: modular domain states plus flux/exchange/event records; exact spatial/time/material identities; cross-segment checkpoints, chain manifests and query/replay for downstream climate, Deep, ecosystem/resources. Avoid forcing all arrays into the reduced 73-node state.
6. MODEL SELECTION: benchmark cost, accuracy and multiresolution/spatial/time choices on integrated small cases; qualify missing positive-duration geodynamic driver and geological/Deep equations and providers; authorize the true long simulation only after physical model integration and readiness.
7. LATER BIOLOGY AND SOCIETY: vegetation, fauna and ecology use stored environmental history, with explicit Deep uptake/return and physiological/demographic feedback where actual bidirectional coupling exists; then populations and civilizations.

Prototypes are noncanonical engineering products. Existing F2A-V, mechanics, Solver and WORLD_HISTORY production gates remain CLOSED. Old roadmap text below documents earlier checkpoints, not the present execution priority.

---

# ARCANA R6 — Roadmap operativa corrente (2026-10-27)

## GEODYN-3B — experimental trajectory archive MVP implemented locally

Decision: `GEODYN_3B_EXPERIMENTAL_TRAJECTORY_ARCHIVE_MVP_LOCAL_PASS__FAIR_QUALIFICATION_PENDING`; report `docs/arcana/GEODYN_3B_EXPERIMENTAL_TRAJECTORY_ARCHIVE_MVP.md`. The bounded index/query implementation reuses the qualified ASPECT reader and compatible R6 identity primitives, stores only metadata/references and a manifest seal, and claims no restart/reconstruction. The R1 compatibility repair is locally verified in `docs/arcana/GEODYN_3B_R1_GIT_IDENTITY_COMPATIBILITY.md`: exact 40/64 lowercase Git object IDs are retained; config/input SHA256 remain 64. Combined Windows suite: 69 passed, 2 symlink-privilege skips. GEODYN-3C still requires exact original run/config/input/inventory evidence; absent values block qualification. No FAIR files or solver execution. This does not alter canonical or scientific gates.

## GEODYN-3A — experimental trajectory archive contract ratified

Decision: `GEODYN_3A_EXPERIMENTAL_TRAJECTORY_ARCHIVE_CONTRACT_RATIFIED__GEODYN_3B_MVP_AUTHORIZED`; contract at `docs/arcana/GEODYN_3A_EXPERIMENTAL_TRAJECTORY_ARCHIVE_CONTRACT.md`. Existing R6 components provide reusable identity/hash, partial streaming/finalization and query/accounting patterns, but no solver-neutral experimental snapshot/payload index; canonical HistoryStore and query contracts remain separate. Only the bounded, read-only GEODYN-3B manifest/index/query MVP is authorized; GEODYN-3C may validate the existing R1 bundle only after review. No ASPECT execution, ARCANA remapping, geological-time conversion or canonical promotion. ARCANA forward remains blocked by initial conditions, constitutive laws, boundary conditions, support mapping and time-dependent forcing; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false` and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

---

# Archived roadmap checkpoint (2026-10-24)

## INT3-ENG10K-F3 — Option B decision sheet prepared; no operator selection

Report `docs/arcana/INT3_ENG10K_F3_OPTION_B_AUTHORIZATION_DECISION.md` presents
APPROVE-for-preparation and REJECT/DEFER alternatives. Selection remains pending.
Even approval permits only exact-commit binding preparation and fresh read-only
preflight; a distinct execution authorization is still required. No numerical
evolution authorized. F1 resource observations remain historical/operator-reported;
sampled thresholds are not enforced quotas and workload resource values remain
UNKNOWN. All scientific/canonical gates remain closed.

## INT3-ENG10K-F1/F2 — read-only preflight closed; separate authorization decision pending

F1 report `docs/arcana/INT3_ENG10K_F1_FAIR_RESOURCE_PREFLIGHT_CLOSURE.md` records
operator-reported read-only Fair preflight/resource audit PASS at source HEAD
`1bf06ef0e624723c3722a351496ae3b7c2544f40`; original Fair files were not imported
or independently rehashed on Windows. The observed host had large available
memory/disk, while the visible cgroup limits were `max`; future allocation, quota,
ENG10K RSS and runtime remain UNKNOWN. F2 report
`docs/arcana/INT3_ENG10K_F2_DECISION_PREPARATION.md` recommends only considering
option B through separate explicit authorization, with sampled limits and their
residual risk stated. No execution authorized; no evolution occurred. The earlier
F blocked review and all scientific/canonical gates remain preserved.

## INT3-ENG10K-F — authorization proposal blocked by unresolved identity/resources

Review report `docs/arcana/INT3_ENG10K_F_EXECUTION_AUTHORIZATION_REVIEW.md`:
`INT3F_ENGINEERING_AUTHORIZATION_BLOCKED__REQUIREMENTS_UNRESOLVED`. Local R4
manifest/member and kernel/configuration pins pass, and execution source is
unchanged from the FAIR-tested INT3-E commit. However, final provider/runtime
identity was not re-attested for the current HEAD; Fair available memory, disk
capacity/quota, effective OS enforcement, exact diffusion-limited step counts and
ENG10K workload timing remain UNKNOWN. No authorization or evolution occurred.
Next is a read-only Fair preflight and resource-fact acquisition for the exact
candidate commit, then a distinct authorization review. Sampled thresholds remain
distinct from OS quotas; the scientific gates remain blocked.

## INT3-ENG10K-A — bounded engineering preparation

Windows implementation and offline qualification are prepared in
`docs/arcana/INT3_ENG10K_READINESS_REPORT.md`. The authenticated R4 bundle and
current provider inputs agree on data/support/forcing. The source-composite hashes
differ because each binds a distinct checkout HEAD; historical R4 and current
candidate identities remain separate, while non-source components match. Next
Windows no-evolution provider-backed preflight passed on code commit
`1b7f3e967050915d1ffa3d7b058f2571c036ee47` (source composite
`cae5ef5c1b95034474031f716b68dcc0dc54fd9f0a56f97dbec26310f241526f`). Next
gate is publication followed by non-numerical FAIR preflight on the exact
published commit. A 10,000-year numerical run remains separately unauthorized. This lane does not
qualify physical validity, SI1/Solver, mechanics or canonical history.


## INT-2C-C3 — real R4 B0 executable replay closed (2026-10-14)

Decision: `INT2C_B0_EXECUTABLE_R4_REPLAY_VERIFIED__SCIENTIFIC_AUTHORITY_UNCHANGED`.
Fair-tested source/Windows entry `9fb4fc0286cc09bcb6b8eef07bb92a19f4ca5963`;
tracked worktree initially clean, remote divergence 0/0. Report
`docs/arcana/INT2C_C3_EXECUTABLE_R4_REPLAY_CLOSURE.md`, SHA256 `462dff6628bed482b23b9e8be815239ba53008b5ef11853f59a073e4f6538c6d`.

Imported `outputs/r6_functional_development/INT2C_C3_REPLAY_20261014_01/` verified
independently on Windows: exact 21 manifest members + manifest, 22 files / 143,807
bytes; manifest `da913ccef5850ae943afadfd90672853db9d1b625eed2ebcc2d508fc599a2852`.
Complete computed state and both original per-support payload digests match R4
exactly; B0 result VERIFIED, zero mismatches. Both supports have 73 nodes and
finite payloads. Eleven typed records, 16-file/78,945-byte C2 read copy, committed
view membership, recorded configuration, twelve source hashes and original R4
inventory reconcile. No HistoryStore constructor or real kernel was run locally.

Authenticated SUPERVISION record: natural child exit 0, 0.7619832679629326 s,
39,845,888 peak sampled process-tree RSS bytes, two samples, zero recorded
overshoot. Linux Python 3.12.10 / NumPy 2.3.5, original 1,000 years/fraction 0.0005.
One authorized genuine real-kernel replay/no retry is operator-reported and
consistent with the imported command/result. Parent log digest and Linux
28 PASS / 1 expected SKIP are OPERATOR_REPORTED, not independently rehashed.
Local focused regressions: 52 PASS, 6 Linux SKIP/NOT_TESTED_WINDOWS; no repeat replay.

This closes only the existing R4 engineering trajectory, forcing, kernel/source
binding and tested Linux runtime. Original C2/R4/INT-1D/history and checkpoint
statuses preserved. No general scientific validity, universal cross-platform
identity, physical refinement, INT-1D executable replay or canonical readiness.
STOP after closure; no further execution or workstream is authorized.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Historical INT-2C-C3 — supervised Linux launcher ready, real replay pending (2026-10-14)

Decision: `INT2C_C3_SUPERVISED_LAUNCHER_READY__REAL_REPLAY_PENDING`.
Entry `7ebbccfa136056b2467ece43fbb7fde51748c531`, clean tracked worktree/index.
Report `docs/arcana/INT2C_C3_SUPERVISED_REPLAY_LAUNCHER_PREFLIGHT.md`, SHA256 `ec49f8e894692c79467f44f32bdd73d109ed9af705ca7cfd93c106ecbcb4c2a6`.
Added one CLI and targeted tests; no changes to adapter, attestor, B0 or kernel.
Default preflight never dispatches the kernel. Numerical CLI mode additionally
requires --execute-authorized, which acknowledges separate operator approval;
it does not grant authority. No real R4 kernel or Fair command executed here.

The existing C2 store is read and byte-copied to fresh evidence before current
HistoryStore is opened, protecting the original from constructor metadata/recovery.
All eleven typed records and fixed checkpoint/recipe IDs must match authenticated
R4 preparation; validate_replay_inputs precedes genuine execute_replay. A transparent
wrapper retains independently computed values; full B0 state and both historical
per-support payload hashes are fixed acceptance targets. Mismatches remain evidence.

Linux monitoring uses /proc PID/executable/start ticks and process-tree RSS,
900 s / 2 GiB / 512 MiB sampled thresholds, SIGTERM/SIGKILL termination, stdout/stderr,
exit status and manifest. These are monitored thresholds, not hard quotas.
Exact isolated Python 3.12.10 / NumPy 2.3.5 prefix required; no fallback. Source
commit/cleanliness and twelve loaded code files are checked against Git blobs.

Windows verification: 86 PASS, 6 Linux runtime tests SKIP/NOT_TESTED_WINDOWS,
1 existing Windows store-publication test deselected; py_compile PASS. Six
Linux supervisor cases must pass on Fair before final preflight/authorization.
C1/C2 remain OPERATOR_REPORTED; no independent Fair import/rehash performed.
Next: operator self-test and provider-free supervised B0 preflight with new paths,
then STOP for separate bounded authorization of one real R4 replay. Full candidate
runtime execution and Linux monitor proof remain pending; all historical evidence preserved.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Historical dependency — INT-2C-C3 pending final authorization/preflight

C1/C2 Fair prerequisites are now recorded as OPERATOR_REPORTED: isolated Python
3.12.10 / NumPy 2.3.5, technical-only checkpoint attestation, atomic registration
of 11 records, reopened-store/readback and validate_replay_inputs PASS. No real
kernel execution. Decision `INT2C_C1_C2_FAIR_PREFLIGHT_REPORTED__C3_PENDING_AUTHORIZATION`.
Report `docs/arcana/INT2C_C1_C2_FAIR_EVIDENCE_RECONCILIATION.md`, SHA256 `df21e291f3b4779fbee90235db0566f34a206261fb92ea67a88e30d64d97a75d`. Untransferred Fair files/hashes are not
independently Windows verified; bind actual source/runtime/store identities at
C3 final preflight. Next is one separately authorized supervised R4 replay with
unchanged numerical configuration and full-state/per-support hash acceptance.
The historical INT-2C-B mismatch remains a valid earlier observation; no runtime
check was relaxed. Scientific qualification and canonical publication remain blocked.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Historical INT-2C-B — technical input closure; Fair runtime blocked (2026-10-14)

Decision: `INT2CB_BLOCKED_FAIR_RUNTIME_IDENTITY_MISMATCH`. Entry source
`f49de047ff560f707428b395b7373d46301fdee9`. Report `docs/arcana/INT2C_B_TECHNICAL_CHECKPOINT_RUNTIME_PREFLIGHT.md`,
SHA256 `35defa80a702d3adea30e3c307c8eb2666bb8b4c8b8023dc1c05780b75db025c`. R4's nine files and original identities were reauthenticated
and retained unchanged. New checkpoint/recipe are VALIDATED only in
`TECHNICAL_ENGINEERING_INPUT_CLOSURE_ONLY`; no numerical validation or physical
promotion. Existing adapter/kernel/B0 contract unchanged.

Direct read-only SSH observation on Fair: Miniforge base Python 3.14.7 without
NumPy; existing `arcana-r6-linux` Python 3.12.14 / NumPy 2.5.3. Required Python
3.12.10 / NumPy 2.3.5 was not found in the inspected existing environment roots.
No installation, environment recreation, job or numerical replay occurred.
Do not infer global absence of another runtime or historical binary identity.

Final local attestation: `outputs/r6_functional_development/INT2CB_TECHNICAL_ATTESTATION_20261014_02/`,
three-member manifest SHA256 `8b172002968c9fcd7620d78b456054ac7ca0e7a9afa49f2f9e91ca81e9b1731d`.
The `_01` provisional preparation remains preserved. No outputs are committed.
63 offline tests PASS, 0 FAIL, 0 SKIP, 1 actual Windows store-publication test
deselected. Typed `validate_replay_inputs()` passed through a test reader only;
real transactional publication/reopened-store readback and numerical replay
remain unexecuted. Exact runtime check rejects both alternate Fair versions.

Next decision: either separately authorize exact-runtime provisioning, or
review an explicitly new binding for Fair 3.12.14 / 2.5.3 with its own source,
configuration, checkpoint/recipe identities and future numerical equivalence
against the unchanged R4 full-state and per-support payload oracles. No relaxed
runtime check, store-contract weakening, new scenario or execution authorization.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`,
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

**Obiettivo completo:** storia mondiale causale 210 Ma→0 ka, interrogabile e ricostruibile per geografia/tettonica, geologia, clima, idrologia, risorse, Deep, flora/fauna, popolazioni e società. INT-0B-R4 and INT-1D produced two bounded noncanonical candidate engineering trajectories. INT-1A/INT-2A measured case-specific retention and diagnostic reconstruction; general policy remains unqualified. INT-2B isolated noncanonical B0 registration/readback/query is evidenced by the Fair-reported run and imported artifact hashes. Executable replay, scientific promotion and canonical storage remain unqualified/unauthorized. The earlier Windows hard-link denial remains an environment-specific historical outcome. Le dipendenze non sono una percentuale o una scadenza.

| Gate | Risultato atteso | Stato |
|---|---|---|
| **INT-0A** | Runner minimo che collega realmente 2+ componenti, con tempo/supporto/provenance coerenti | `INT0A_INTEGRATION_CODE_READY__NONCANONICAL_RUN_NOT_YET_EVIDENCED`; suite offline mirata 20 PASS |
| **INT-0B** | Noncanonical T-F2B 5:11 engineering run, samples, comparison, restart, manifest | R4 completed on 91fc83d; bundle/samples/replay/restart verified. INT0B_NONCANONICAL_INTEGRATED_RUN_EVIDENCED__SCIENTIFIC_PROMOTION_NOT_AUTHORIZED. _01-_03 remain immutable failures. |
| **INT-0B-R2** | Isolamento ambiente corretto e tentativo finale bounded | Preflight provider PASS su `311550d`; esecuzione singola fallita su endpoint diagnostico dopo 22.190863 s (exit 1). La diagnosi R3 identifica mismatch di schema `elapsed_years` assente dal final payload, non prova una divergenza numerica; la regressione sintetica e la correzione supervisor passano. Nessun quarto run autorizzato. |
| **INT-0B-R3** | Correzione endpoint e metadata supervisor offline | `INT0B_R3_ENDPOINT_VALIDATION_CORRECTED__REEXECUTION_NOT_AUTHORIZED`; report del run fallito immutato e campioni non recuperati. |
| **INT-0B-R4** | Validazione E2E sintetica, provider preflight e un tentativo engineering bounded | Offline suite 70 PASS; quarto run autorizzato su `91fc83d` completato e bundle verificato. Decisione noncanonical: `INT0B_NONCANONICAL_INTEGRATED_RUN_EVIDENCED__SCIENTIFIC_PROMOTION_NOT_AUTHORIZED`. |
| **INT-1A** | Empirical full/fixed/retrospective retention, reconstruction, replay and byte baseline on existing R4 trajectory | R4 baseline completed; general policy remains unqualified. |
| **INT-1B** | Define minimum added retention evidence and distinct admissible regime | Design preserved; exact edge and full local T0 profiles verified for preparation. |
| **INT-1C** | Add explicit eligible-edge selection and finest-rung diagnostic sampling for a distinct pair-5:11 candidate | `INT1C_DISTINCT_REGIME_CODE_READY__EXECUTION_PENDING_AUTHORIZATION`; 85 offline tests passed, 2 provider-backed tests deselected; no evolution. Full provider preflight/source-composite remains pending external inputs. |
| **INT-1D** | One bounded distinct-boundary trajectory and offline comparison with R4 | `INT1D_DISTINCT_BOUNDARY_TRAJECTORY_EVIDENCED__GENERAL_RETENTION_POLICY_NOT_QUALIFIED`; nine samples/support, manifest and endpoints verified, replay/restart reconciled, INT-1A retention evaluator applied. `_01` launcher failure remains immutable. |
| **INT-2A** | Verify bundles and implement exact/bracket/reconstructed offline queries plus retention answerability | `INT2A_OFFLINE_HISTORICAL_QUERY_RECONSTRUCTION_EVIDENCED__B0_EXECUTABLE_BINDING_NOT_QUALIFIED`; 27 focused tests pass; B0 Windows store tests blocked by `os.link` permission |
| **INT-2B** | Map verified noncanonical observations to existing B0 records and verify isolated registration/query | `INT2B_NONCANONICAL_B0_STATE_QUERY_BINDING_EVIDENCED__EXECUTABLE_REPLAY_NOT_QUALIFIED`; Fair-reported 85 B0 regression PASS, adapter exit 0, transactional store/readback 26/26, 2 provenance, 33 files/163,086 bytes; imported hashes rechecked on Windows; executable replay and canonical authority remain unqualified |
| **INT-2C-A** | Prepare closed R4 B0 replay inputs and deterministic existing-kernel adapter | `INT2C_EXECUTABLE_REPLAY_BINDING_CODE_READY__NUMERICAL_VALIDATION_PENDING`; 24 new mock/contract tests, 58 combined PASS, 1 real-store test deselected; new checkpoint remains candidate; supported-filesystem integration and actual numerical replay pending separate review/runtime/authorization |
| **INT-3** | Provider aggiuntivi, estensione geografica e temporale | Solo con input/applicabilità/contratti adeguati |
| **Produzione WORLD_HISTORY** | Stati/eventi causalmente verificati per tutti i domini fino a 0 ka | Non autorizzata |

## Inventario con scope (non trasformare PASS tecnici in qualifica scientifica)

INT-0B R4 is a completed, bounded noncanonical pair-5:11 engineering run on source commit `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`, source-composite identity `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`. INT-1D is a separate, bounded run on the distinct explicit boundary `R6BND-T0-27e4d497530e681071fb`, source commit `3fa149b7639f59c934a4d722acb388eacc4c9628`, source-composite identity `a1a4503fe57206750884e454d8a12d778caee38e34b35586805241ad51c01954`. The offline INT-1A evaluator measured case-specific retention/reconstruction for both; general retention remains UNKNOWN and neither run qualifies mechanics or canonical history.

- **B0/B6:** HistoryStore/query/replay esistono. B6K candidata geometrica 210→209.97287659484368 Ma e B6N8-A shadow multirisoluzione. Vecchio B6M-R1 bloccato e successivo live-view B6N8-A a due età sono checkpoint distinti; verificare il canonico attuale read-only.
- **Termica/cinematica integrabile:** PRE_ORBDATA, B6N8-O/Q e codice T-F2B con supporto coppia **5:11**, forcing ingegneristico congelato, finestra 1.000 anni e replay/restart. B6N8-R roster real-support ancora incompleto; NON estendere T-F2B alla coppia rift **1:3** per analogia.
- **Post-rift:** B6N5/B6N7 non chiudono la legge di propagazione fisica, eventi di interfaccia/topologia/supporto né `dt2`. Questo blocca la **continuazione fisica post-rift**, non ogni test ingegneristico non canonico.
- **ShellSet/OrbData:** esempio upstream Fair 9/9 nel proprio scope; caso SI1 assembly pre-Solver e recovery, non solve qualificato. W3-C-C ha difetti aperti; W3-C-B-R1, real owner/MPI stop, W4 scala e classi/threshold numerici separati.
- **pyGPlates:** fixture/adapter candidato; reports mapping canonico `PYGPLATES_RUNTIME_UNAVAILABLE` non sono prove runtime positive. Non obbligatorio per INT-0 se Euler/plate support già disponibile.
- **Ambiente/Deep/ecologia/società:** componenti/contratti parziali o legacy, da integrare in futuro senza fabbricare valori UNKNOWN.

## Workstream paralleli (non NEXT generale)

1. **ShellSet SI1:** W3-C-B-R1 → revisione → owner/runtime stop → W4/risorse → criteri fisico-numerici → gate Solver distinto.
2. **Tettonica post-rift:** modello evolvibile e predicati di validità, topologia/interfacce/supporto; non derivare fisica da rigide rotazioni.
3. **OrbData, pyGPlates, BIOME4, risorse e Deep:** provider e input/autorità per estendere vertical slice, solo quando reali dipendenze.

**Non usare le vecchie NEXT storiche.** `NEXT_ACTION.md` è l'unica NEXT attiva. Originali, hash, `BLOCKED` e log sono conservati in `STATUS.md`, `EVIDENCE_INDEX.md`, `LOG.md`, report e storia Git. Conservare separati CODE_READY, NONCANONICAL_RUN, SCIENTIFIC_VALIDATION e CANONICAL_AUTHORITY.

**Gates invariati:** `BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. INT-1C code readiness does not authorize execution or change these gates.

# ARCANA WorldSim R6 — PROJECT_LEDGER

## CURRENT — 2026-10-30 E2-C0 single-year CPU profile and oracle parity PASS

FAIR engineering-only evidence E2_C0_REFERENCE_PARITY=PASS for years 101/501/751 (61 record kind+payload hashes/year), resumed from existing checkpoints. Profile root INT10K_E2C0_PROFILE_Piy2PjHo. Profiled wall ~0.080/0.203/0.279 s; json.dumps 110 calls/year and json.loads 12 calls/year, encode+decode ~79%,86%,87% of profiled time with growing data; unified numerical inner execution ~20 ms/year stable. Important: cProfile and hash-only consumer do not reproduce full JSONL I/O costs. Full source/limits/next in PROJECT_LEDGER/R6_INT10K_E2C0_CPROFILE_PARITY_20261030.md. NEXT E2-C0-B direct callers from saved pstats, no rerun; then B0-store-aware lossless E2-C1 schema. Engine SHA 9dce77b5... FAIR-local, separate from GitHub documentation; production/canonical authority unchanged.

---

## CURRENT — 2026-10-30: INT10K 1000Y engineering PASS / FAIR-local geometry fix / E2-C0 next

**Operative scope and read order:** `PROJECT_LEDGER/R6_INT10K_1000Y_FAIR_PERFORMANCE_E2C_E2D_HANDOFF_20261030.md` → `EVIDENCE_INDEX.md` → `NEXT_ACTION.md`. The old CURRENT blocks below are historical and must not override this one. The source/manifest originals prevail over this narrative.

- **PASS engineering only (operator-reported FAIR):** `PASS_1000Y_ENGINEERING_EXECUTION_COMPLETE`, exact FAIR-local source `9dce77b5d65d4301d2145f9ad527b8efee0fe96d`, branch `r6/geometry-ulp-r1-fair`, parent published `9d9a2512d5e2aca5cc3fd04010d53ac467fe9839`, preserved evidence `INT10K_1000Y_GEOMETRY_R1_YJBeAKT4`; manifest SHA256 `e56f02c726856fd976a3a49b037b95be506b15a2b691d7a308d9ad6d4ad3a59a`. `RUN_EXIT=0`. **The FAIR source commit has not been shown pushed to GitHub.** The new GitHub ledger commit is documentation-only; it does not replace or rehash FAIR source.
- First 1000Y attempt **FAILED** with geometry-volume rounding check, preserved in `INT10K_1000Y_OBSERVE_sNc82fLw`. Follow-up diagnosis `INT10K_1000Y_GEOMETRY_DIAG_Ewx1utQY` documented `1.08066e-05 m³` residual versus legacy `1.23599e-06 m³` tolerance, ULP source ~`1.22e-04 m³`. ULP-aware check fixes precision only; first planned-year integrated run PASS. Earlier 85/86 test failure was missing synthetic fixture `t0_boundary_id`, then fixed; review exact full test logs rather than infer unreported counts.
- **1000Y observed:** 244.780960 s loop wall / 242.020507 s process CPU, ~25.731 s post-loop inferred from timestamps, ~270.512 s estimated end-to-end. HISTORY 1,916,080,917 bytes, peak RSS 103,260,160 B. 1000 annual steps sum 231.733 s; 13.048 s loop not step-attributed. 61,001 indexed envelopes. `REGIONAL_SNAPSHOT` ~92.6% archive; at year 1000 11,000 deposits ~99.73% of a 3.540 MB full snapshot; growing duplication, **not** evidence of a disk stall. CPU/wall ~1 core during simulation; two GPUs unused.
- Derived evidence: `INT10K_1000Y_COST_ANALYSIS_Kaw8pV2x` cost audit PASS, `INT10K_1000Y_RECORD_AUDIT_AyVB7iSW` index audit PASS, direct snapshot 100/500/1000 audit PASS. Original evidence unchanged.
- FAIR hardware: 2× Xeon Gold 6530 (64 physical cores, 128 SMT threads), 4 NUMA nodes, 1 TiB RAM (~979 GiB system-available), 2× RTX 5090 (~32,607 MiB VRAM each). CPU affinity allows 128 threads, **not** proof of site quota/authorization; inspect session cgroup limits along actual path. One core busy is ~1.6% of installed physical cores. Do not assume 64× speedup on 9 cells.
- **NEXT:** E2-C0 read-only decomposition of CPU/JSON/snapshot/checkpoint/hash/IO costs, audit existing B0 HistoryStore/query/replay/retention; then schema/acceptance for lossless delta+event materialization + sparse checkpoints + exact reconstruction. Deterministic policy: Codex design-time, not autonomous loss-based runtime pruning. No new clone/1000Y rerun by default. Keep all canonical/solver/forward-production gates **false**.
- **Git sync note:** current GitHub documentation commit is based on remote `9d9a2512d5e2aca5cc3fd04010d53ac467fe9839`, while `9dce77b5d65d4301d2145f9ad527b8efee0fe96d` exists in a FAIR worktree based on the same parent. Future integration needs an explicit *non-destructive merge/cherry-pick strategy*, preserving exact benchmark source SHA as an ancestor/reference; do not run blind `git pull`/reset/rebase that silently changes qualified SHA.

---


# CURRENT — INT10K E2-B2-R1 provenance correction local PASS; FAIR pending (2026-10-29)

Published base `5f78927f1c06aeda30b3b375f4bacf873f55c6d2`. Windows Python 3.12.10 / NumPy 2.5.1: 74 focused tests pass. E2-B2-R1 records actual commit and SHA256s, derives Git status only for measured sources including untracked files, and reports Git unavailability as UNKNOWN/null. Exact-commit mode now blocks before numerical execution when provenance is mismatched/dirty; diagnostic mode remains separately available. Final-code E0-backed 3Y/10Y parity passed diagnostically; manifests `4cbb926d4a092e6967885c44c7995389b93b94799a04340675b9d59bf29e13e9` and `59b0134b1e3bf19d96b2654e39e4b1d3fe85a9a8973d26c844e6b601f75a393e`. A dirty exact-gate probe returned exit 3 before evolution and produced manifest `751e38ee9744c0e2d3ca69b2337b167d99387a31097efb9ad6b6164dc49d5a6e`. All captures reported dirty sources and are not exact-commit qualification. Next publish R1 child by verified fast-forward, then FAIR/Linux qualification. No long run. Durable append-only history/transactions and all scientific/canonical gates remain pending/closed. See `docs/arcana/R6_INT10K_E2_B2_HISTORY_INDEPENDENT_CONTINUATION.md`.

---

# PREVIOUS CURRENT — E2-A1 FAIR qualification reported; E2-B frontier projection locally partial (2026-10-29)

Operator reports E2-A1 exact-commit FAIR qualification on `57768923a4a8478381d9153c6f910fba811613d2`: Linux 60/60, 3Y/10Y oracle and manifest hashes recorded in `docs/arcana/R6_INT10K_E2_A1_FULL_HISTORY_ORACLE_IMPLEMENTATION.md`; original FAIR files are not locally imported or independently rehashed. E2-B now serializes history-free frontier/checkpoint envelopes and restores against separately supplied history, with local 3Y/10Y reference parity. Existing continuation still requires full prior history; E2-B, append-only transactions and streaming are not qualified. See `docs/arcana/R6_INT10K_E2_B_FRONTIER_CHECKPOINT_IMPLEMENTATION.md`. Next exact-commit Linux qualification and resolve the legacy-history dependency. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `INT10K_LONG_RUN_AUTHORIZED=false`.

Single continuity point. E1-R2 Linux results remain operator-reported at exact commit `5faf619875af86caa2ee824dff4b0a833f4227f1`; FAIR files were not imported or rehashed on Windows. E2-A1 now has a separate `FULL_HISTORY_ORACLE_V1` implementation and locally verified 3-year 1+2 / 10-year 5+5 direct/restart full-history captures on Python 3.12.10 / NumPy 2.5.1. These are Windows engineering results, not FAIR qualification or comparison to the unimported E1 files. E2 streaming/frontier/transaction implementation remains pending. The observe-only policy `OBSERVE_REAL_SCALING_NO_ARBITRARY_RESOURCE_CAPS` remains in force; actual FAIR allocations/site policy bind, unknown quotas remain UNKNOWN. See `docs/arcana/R6_INT10K_E2_A1_FULL_HISTORY_ORACLE_IMPLEMENTATION.md` and `docs/arcana/R6_INT10K_E2_FRONTIER_HISTORY_STREAMING_CONTRACT.md`. Scientific and WORLD_HISTORY gates remain false.

## Current decision — 2026-10-25

Development mode is PROTOTYPE_FIRST_MULTIPHYSICS_INTEGRATION. FAIR ENG10K with Segment Archive V1 completed (194 actual states, 8 trajectories, 186 numerical substeps, Linux 57/57 focused tests). A separate Windows engineering continuation test reports 5k+5k and 5x2k successful checkpoint restoration with small endpoint differences; its uncommitted implementation remains pending supported-runtime testing. These are NOT scientific or canonical history qualifications.

Operator priority: run small, inexpensive, noncanonical numerical integrations between genuinely interdependent physical tools (geodynamics, geology/surface, hydrology where required, Deep energy/transport), then measure integration and scaling before selecting the historical simulation model and resolution. Do not repeatedly requalify legacy runs during prototyping; retain a lightweight evidence trace and scientific gates for production. The previous INT3-F3 pending Option-B instruction was superseded operationally by the later separately bound and completed ENG10K attempt; the F3 decision artifact itself remains historical and unmodified.

The local tectonics/Deep, continuation, material, surface/hydrology and regional prototypes were consolidated in the published R6 branch at HEAD `788a312329c61c4f751b63791284a50d6653fd4d`. Their tests and reports remain bounded engineering evidence; the Windows checks do not imply Fair/Linux qualification or scientific/canonical promotion.

## Leggere in questo ordine
1. STATUS.md - only the opening CURRENT section contains present priority; historical checkpoints follow.
2. NEXT_ACTION.md - current action: implement the bounded E2 frontier/history stream in stages; E1-R2's 3/10-year PASS is operator-reported and full-history parity remains pending.
3. `ROADMAP.md` — dipendenze e filoni paralleli.
4. `PROCEDURE.md` — workflow Git/Windows/Fair e preservazione dei gate.
5. `EVIDENCE_INDEX.md`, `VISION.md`, `ARCHITECTURE.md`, `SHELLSET_HISTORY.md`, `DECISIONS.md`, `LOG.md` e fonti specialistiche secondo la domanda.

**Precedenza:** fonti primarie e prove > commit/scope verificato > priorità di questo ledger > vecchie istruzioni operative > chat. Gli storici «NEXT W2/W3» nei report e vecchi HEAD non sono task attivi. Prima di agire verificare branch, HEAD, dirty/untracked ed evidenze. Non ripetere prove già qualificate nel loro scope.

**Distinguere:** software già testato ≠ integrazione ARCANA ≠ simulazione fisica globale ≠ promozione canonica. R3/R4/R5 sono legacy non-target. Ogni gate aggiorna `STATUS`, `NEXT_ACTION`, `LOG`, `EVIDENCE_INDEX` e `ROADMAP` quando serve, nello stesso commit. `DECISIONS` append-only; risultati `BLOCKED`, hash, source lock, output e report storici rimangono immutati.

## Current decision — GEODYN-3B local MVP implemented (2026-10-27)

Decision: `GEODYN_3B_EXPERIMENTAL_TRAJECTORY_ARCHIVE_MVP_LOCAL_PASS__FAIR_QUALIFICATION_PENDING`. Report: `docs/arcana/GEODYN_3B_EXPERIMENTAL_TRAJECTORY_ARCHIVE_MVP.md`. The ratified GEODYN-3A scope is implemented and synthetically tested on Windows; 42 passed, 2 symlink-privilege skips. No original FAIR payload was indexed and no solver was run. The R1 FAIR qualification remains operator-reported in the Windows record; see STATUS and EVIDENCE_INDEX. GEODYN-3C is the next separate gate.

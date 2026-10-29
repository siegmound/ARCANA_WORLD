# ARCANA WorldSim R6 — PROJECT_LEDGER

# CURRENT — INT10K E2-B2 local history-independent continuation PASS; FAIR pending (2026-10-29)

Windows Python 3.12.10 / NumPy 2.5.1: 67 focused E2-B2/E2-B/E2-A1/E1/regional/unified tests passed. The 3Y 1+2 and 10Y 5+5 HI resumes did not receive the prior history prefix; full histories, checkpoint dynamic state, balances and queries match the local E2-A1 oracle. E0 hashes passed before/after. Final local evidence is `_06` under `INT10K_E2_B2_WINDOWS_20261029_06`; manifest SHA256 3Y `a24f46d051f2dea81f49183ed320f920c7d815ac68f9613542b5e4248df26fb4`, 10Y `e58e774623b3b0e53d488f36eb8667b7dfc074dd45c03f7222778308e7c59870`. Worktree-based run started at `4910c2c4e4b1a00f2999b95937f07cea233a006c`; it is not a committed or Linux qualification. No durable append-only history, transaction/recovery chain, indexed on-disk query, or all-duration constant-size claim. Next exact-commit Linux qualification, then separate E2-C/D/E/F gates. No 100/1,000/10,000-year run. See `docs/arcana/R6_INT10K_E2_B2_HISTORY_INDEPENDENT_CONTINUATION.md`; all science/canonical gates remain false.

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

# ARCANA WorldSim R6 — PROJECT_LEDGER

Single continuity point. E1-R2 45/45 Linux tests and the 3-/10-year references are operator-reported PASS at exact commit `5faf619875af86caa2ee824dff4b0a833f4227f1`; FAIR artifacts were not imported or rehashed on Windows. E2's contract now adopts `OBSERVE_REAL_SCALING_NO_ARBITRARY_RESOURCE_CAPS`: future benchmarks measure actual use, respect real FAIR allocations/site policy, and never interpret unknown quotas as unlimited. Streaming implementation and full-history parity remain pending, including an extended oracle with unified per-step records and split-boundary checkpoints. No new run was performed and no long-run execution is authorized. See `docs/arcana/R6_INT10K_E2_FRONTIER_HISTORY_STREAMING_CONTRACT.md`. Scientific, solver and WORLD_HISTORY gates remain unchanged and false.

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

# ARCANA WorldSim R6 — PROJECT_LEDGER

Single continuity point. Current update: 2026-10-28. Decision `GEODYN_3C_EXPERIMENTAL_TRAJECTORY_ARCHIVE_FAIR_VALIDATED__ARCANA_FORWARD_NOT_AUTHORIZED` — **PASS_OPERATOR_REPORTED** for the existing synthetic engineering ASPECT trajectory archive, **not** ARCANA physical evolution. Qualified code `3c566ea61c79b8dad96274a5d68d845704aeae96` (parent `02fa91cf39f4f79885d033ad3485c0d0f86c4de9`), FAIR evidence `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN3C_20261028T171846Z`. Operator reports: JUnit **86/86 PASS** (no skip/failure/error), independent **11/11 mesh** + **99/99 typed field** comparisons, 11 snapshots/23 source files, query/integrity/negative/path/relocation tests PASS, launcher exit 0, manifest SHA256 `56bfc4789618d149fc402af2319c088fe0bbc9cabc9b1b73622393af9accd54f`; original source files and checkout unchanged, ASPECT not rerun. This report did not independently rehash the FAIR bundle or authenticate caller-declared run identity: `SYNTHETIC_ENGINEERING_ONLY`, `OPERATOR_REPORTED_UNAUTHENTICATED`. Historic R3 `GEODYN3C_20261028T164610Z` remains FAIL. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` and `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`. See `docs/arcana/GEODYN3C_R4_FAIR_QUALIFICATION_CLOSURE.md`, `docs/arcana/qualifications/GEODYN3C_R4_FAIR_QUALIFICATION_ATTESTATION.json`, STATUS and NEXT_ACTION.

## Current decision — 2026-10-25

Development mode is PROTOTYPE_FIRST_MULTIPHYSICS_INTEGRATION. FAIR ENG10K with Segment Archive V1 completed (194 actual states, 8 trajectories, 186 numerical substeps, Linux 57/57 focused tests). A separate Windows engineering continuation test reports 5k+5k and 5x2k successful checkpoint restoration with small endpoint differences; its uncommitted implementation remains pending supported-runtime testing. These are NOT scientific or canonical history qualifications.

Operator priority: run small, inexpensive, noncanonical numerical integrations between genuinely interdependent physical tools (geodynamics, geology/surface, hydrology where required, Deep energy/transport), then measure integration and scaling before selecting the historical simulation model and resolution. Do not repeatedly requalify legacy runs during prototyping; retain a lightweight evidence trace and scientific gates for production. The previous INT3-F3 pending Option-B instruction was superseded operationally by the later separately bound and completed ENG10K attempt; the F3 decision artifact itself remains historical and unmodified.

The local tectonics/Deep, continuation, material, surface/hydrology and regional prototypes were consolidated in the published R6 branch at HEAD `788a312329c61c4f751b63791284a50d6653fd4d`. Their tests and reports remain bounded engineering evidence; the Windows checks do not imply Fair/Linux qualification or scientific/canonical promotion.

## Leggere in questo ordine
1. STATUS.md - only the opening CURRENT section contains present priority; historical checkpoints follow.
2. NEXT_ACTION.md - current action: read-only R6 physical/environmental provider gap matrix; GEODYN-3C archived-output qualification is complete in its bounded experimental scope.
3. `ROADMAP.md` — dipendenze e filoni paralleli.
4. `PROCEDURE.md` — workflow Git/Windows/Fair e preservazione dei gate.
5. `EVIDENCE_INDEX.md`, `VISION.md`, `ARCHITECTURE.md`, `SHELLSET_HISTORY.md`, `DECISIONS.md`, `LOG.md` e fonti specialistiche secondo la domanda.

**Precedenza:** fonti primarie e prove > commit/scope verificato > priorità di questo ledger > vecchie istruzioni operative > chat. Gli storici «NEXT W2/W3» nei report e vecchi HEAD non sono task attivi. Prima di agire verificare branch, HEAD, dirty/untracked ed evidenze. Non ripetere prove già qualificate nel loro scope.

**Distinguere:** software già testato ≠ integrazione ARCANA ≠ simulazione fisica globale ≠ promozione canonica. R3/R4/R5 sono legacy non-target. Ogni gate aggiorna `STATUS`, `NEXT_ACTION`, `LOG`, `EVIDENCE_INDEX` e `ROADMAP` quando serve, nello stesso commit. `DECISIONS` append-only; risultati `BLOCKED`, hash, source lock, output e report storici rimangono immutati.

## Current decision — GEODYN-3B local MVP implemented (2026-10-27)

Decision: `GEODYN_3B_EXPERIMENTAL_TRAJECTORY_ARCHIVE_MVP_LOCAL_PASS__FAIR_QUALIFICATION_PENDING`. Report: `docs/arcana/GEODYN_3B_EXPERIMENTAL_TRAJECTORY_ARCHIVE_MVP.md`. The ratified GEODYN-3A scope is implemented and synthetically tested on Windows; 42 passed, 2 symlink-privilege skips. No original FAIR payload was indexed and no solver was run. The R1 FAIR qualification remains operator-reported in the Windows record; see STATUS and EVIDENCE_INDEX. GEODYN-3C is the next separate gate.

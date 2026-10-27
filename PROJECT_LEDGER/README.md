# ARCANA WorldSim R6 — PROJECT_LEDGER

Single continuity point. Current development update: 2026-10-27. GEODYN-2A-R1 read-only ASPECT snapshot parsing is numerically validated on FAIR for the reported ASPECT 3.2.0-pre series; its Linux results remain operator-reported, not independently rehashed on Windows. The first real-VTU failure remains immutable. GEODYN-3A has ratified the solver-neutral experimental trajectory archive contract and authorized only the bounded GEODYN-3B index/query MVP. GEODYN-3C validation against existing R1 evidence remains a later gate. No ASPECT execution, ARCANA forward evolution, canonical state creation, geological-time conversion, surface/Deep coupling or WORLD_HISTORY publication is authorized. See current STATUS/NEXT_ACTION and `docs/arcana/GEODYN_3A_EXPERIMENTAL_TRAJECTORY_ARCHIVE_CONTRACT.md`.

## Current decision — 2026-10-25

Development mode is PROTOTYPE_FIRST_MULTIPHYSICS_INTEGRATION. FAIR ENG10K with Segment Archive V1 completed (194 actual states, 8 trajectories, 186 numerical substeps, Linux 57/57 focused tests). A separate Windows engineering continuation test reports 5k+5k and 5x2k successful checkpoint restoration with small endpoint differences; its uncommitted implementation remains pending supported-runtime testing. These are NOT scientific or canonical history qualifications.

Operator priority: run small, inexpensive, noncanonical numerical integrations between genuinely interdependent physical tools (geodynamics, geology/surface, hydrology where required, Deep energy/transport), then measure integration and scaling before selecting the historical simulation model and resolution. Do not repeatedly requalify legacy runs during prototyping; retain a lightweight evidence trace and scientific gates for production. The previous INT3-F3 pending Option-B instruction was superseded operationally by the later separately bound and completed ENG10K attempt; the F3 decision artifact itself remains historical and unmodified.

The local tectonics/Deep, continuation, material, surface/hydrology and regional prototypes were consolidated in the published R6 branch at HEAD `788a312329c61c4f751b63791284a50d6653fd4d`. Their tests and reports remain bounded engineering evidence; the Windows checks do not imply Fair/Linux qualification or scientific/canonical promotion.

## Leggere in questo ordine
1. STATUS.md - only the opening CURRENT section contains present priority; historical checkpoints follow.
2. NEXT_ACTION.md - current action: implement only the ratified noncanonical GEODYN-3B archive index/query MVP. ARCANA forward inputs remain unresolved; T0 kinematics remain diagnostic and no geological evolution run is authorized.
3. `ROADMAP.md` — dipendenze e filoni paralleli.
4. `PROCEDURE.md` — workflow Git/Windows/Fair e preservazione dei gate.
5. `EVIDENCE_INDEX.md`, `VISION.md`, `ARCHITECTURE.md`, `SHELLSET_HISTORY.md`, `DECISIONS.md`, `LOG.md` e fonti specialistiche secondo la domanda.

**Precedenza:** fonti primarie e prove > commit/scope verificato > priorità di questo ledger > vecchie istruzioni operative > chat. Gli storici «NEXT W2/W3» nei report e vecchi HEAD non sono task attivi. Prima di agire verificare branch, HEAD, dirty/untracked ed evidenze. Non ripetere prove già qualificate nel loro scope.

**Distinguere:** software già testato ≠ integrazione ARCANA ≠ simulazione fisica globale ≠ promozione canonica. R3/R4/R5 sono legacy non-target. Ogni gate aggiorna `STATUS`, `NEXT_ACTION`, `LOG`, `EVIDENCE_INDEX` e `ROADMAP` quando serve, nello stesso commit. `DECISIONS` append-only; risultati `BLOCKED`, hash, source lock, output e report storici rimangono immutati.

## Current decision — GEODYN-3A contract ratified (2026-10-27)

Decision: `GEODYN_3A_EXPERIMENTAL_TRAJECTORY_ARCHIVE_CONTRACT_RATIFIED__GEODYN_3B_MVP_AUTHORIZED`. Contract: `docs/arcana/GEODYN_3A_EXPERIMENTAL_TRAJECTORY_ARCHIVE_CONTRACT.md`. This authorizes only the read-only experimental GEODYN-3B MVP; no implementation, solver execution or new runtime evidence is claimed. The R1 FAIR qualification remains operator-reported in the Windows record; see STATUS and EVIDENCE_INDEX. GEODYN-3C remains a separate later validation gate.

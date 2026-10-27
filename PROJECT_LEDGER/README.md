# ARCANA WorldSim R6 — PROJECT_LEDGER

Single continuity point. Current development update: 2026-10-27. GEODYN-2A-R1 read-only ASPECT snapshot parsing is numerically validated on FAIR for the reported ASPECT 3.2.0-pre snapshot series. Linux test and numeric comparison results are operator-reported and were not independently rehashed on Windows; the first real-VTU failure remains immutable and its parser repair is documented. Current priority: prepare the bounded GEODYN-3 experimental trajectory archive contract. No ARCANA forward evolution, canonical state creation, geological-time conversion, surface/Deep coupling or WORLD_HISTORY publication is authorized. The older INT3-F3 narrative below is an archived checkpoint; `INT3_ENG10K_EXECUTION_AUTHORIZED=false`. See current STATUS/NEXT_ACTION and `docs/arcana/GEODYN_2A_R1_FAIR_QUALIFICATION_CLOSURE.md`.

## Current decision — 2026-10-25

Development mode is PROTOTYPE_FIRST_MULTIPHYSICS_INTEGRATION. FAIR ENG10K with Segment Archive V1 completed (194 actual states, 8 trajectories, 186 numerical substeps, Linux 57/57 focused tests). A separate Windows engineering continuation test reports 5k+5k and 5x2k successful checkpoint restoration with small endpoint differences; its uncommitted implementation remains pending supported-runtime testing. These are NOT scientific or canonical history qualifications.

Operator priority: run small, inexpensive, noncanonical numerical integrations between genuinely interdependent physical tools (geodynamics, geology/surface, hydrology where required, Deep energy/transport), then measure integration and scaling before selecting the historical simulation model and resolution. Do not repeatedly requalify legacy runs during prototyping; retain a lightweight evidence trace and scientific gates for production. The previous INT3-F3 pending Option-B instruction was superseded operationally by the later separately bound and completed ENG10K attempt; the F3 decision artifact itself remains historical and unmodified.

The local tectonics/Deep, continuation, material, surface/hydrology and regional prototypes were consolidated in the published R6 branch at HEAD `788a312329c61c4f751b63791284a50d6653fd4d`. Their tests and reports remain bounded engineering evidence; the Windows checks do not imply Fair/Linux qualification or scientific/canonical promotion.

## Leggere in questo ordine
1. STATUS.md - only the opening CURRENT section contains present priority; historical checkpoints follow.
2. NEXT_ACTION.md - current action: define the bounded GEODYN-3 experimental trajectory archive contract. ARCANA forward inputs remain unresolved; T0 kinematics remain diagnostic and no geological evolution run is authorized.
3. `ROADMAP.md` — dipendenze e filoni paralleli.
4. `PROCEDURE.md` — workflow Git/Windows/Fair e preservazione dei gate.
5. `EVIDENCE_INDEX.md`, `VISION.md`, `ARCHITECTURE.md`, `SHELLSET_HISTORY.md`, `DECISIONS.md`, `LOG.md` e fonti specialistiche secondo la domanda.

**Precedenza:** fonti primarie e prove > commit/scope verificato > priorità di questo ledger > vecchie istruzioni operative > chat. Gli storici «NEXT W2/W3» nei report e vecchi HEAD non sono task attivi. Prima di agire verificare branch, HEAD, dirty/untracked ed evidenze. Non ripetere prove già qualificate nel loro scope.

**Distinguere:** software già testato ≠ integrazione ARCANA ≠ simulazione fisica globale ≠ promozione canonica. R3/R4/R5 sono legacy non-target. Ogni gate aggiorna `STATUS`, `NEXT_ACTION`, `LOG`, `EVIDENCE_INDEX` e `ROADMAP` quando serve, nello stesso commit. `DECISIONS` append-only; risultati `BLOCKED`, hash, source lock, output e report storici rimangono immutati.

## Current decision — GEODYN-2A-R1 FAIR closure (2026-10-27)

Decision: `GEODYN_2A_R1_ASPECT_READONLY_ADAPTER_FAIR_NUMERICALLY_VALIDATED__ARCANA_FORWARD_NOT_AUTHORIZED`. Closure report: `docs/arcana/GEODYN_2A_R1_FAIR_QUALIFICATION_CLOSURE.md`. FAIR reports 32 Linux tests passed, adapter and independent NumPy comparison exit 0, 11/11 numeric mesh hashes and 99/99 typed field hashes matched for the exact implementation commit. These results are operator-reported; the original FAIR logs and VTU bundle were not transferred or rehashed on Windows. No raw solver outputs are committed. Next is the GEODYN-3 experimental trajectory archive contract, not ARCANA forward evolution.

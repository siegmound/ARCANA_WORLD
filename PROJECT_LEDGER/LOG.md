# Bitacora cronologica — append-only
Non cancellare righe precedenti. Un evento tecnico `PASS` è sempre limitato al proprio scope; i veri seals vivono nei manifest di autorità.

| Data (UTC se disponibile) | Workstream | Riferimento | Esito verificato | Impatto / next |
|---|---|---|---|---|
| 2026-09-28 | ShellSet upstream Fair | `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json` | NVIDIA/MPICH or OpenMPI metadata come da fonte; ListEx1 9/9 parallelo, LAPACK smoke PASS | Non ripetere il benchmark come prova della capacità già dimostrata; ARCANA mechanics non qualificata |
| 2026-09-28 | OrbData/ARCANA Fair | `R6_T0_ORBDATA_ARCANA_FAIR_RUNTIME_QUALIFICATION.json` | ARCANA runtime patch/load & upstream 9/9, bounded | non T0 full solver |
| Storico R6 | B0/B6 | `docs/arcana/B6M0_CANONICAL_WORLD_HISTORY_BOOTSTRAP.md`, `B6K_ISOLATED_FIRST_CANDIDATE_STATE.md`, `B6N5_...`, `B6N6_...` | Core history, candidate, rift authority gap, adaptive architecture | non inventare nuova propagazione |
| 2026-10-08 | BW1 F1/F2-A | F1 and F2-A recovery paths in `EVIDENCE_INDEX.md` | assembly captured, F2-A reconstructed but original blocked | numerical probe F2A-V |
| 2026-10-10 | F2A-V Fortran fix | `df670c8c4faaed641997f5c4bdb701e2ba0afc7d` | NVFortran compile-only PASS; Fair regression 138 PASS | autorun singolo assembly only |
| 2026-10-10 | F2A-V Fair runtime | `BW1_F2AV_RUN/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z` | MPI 75 intentional after ~282 s; Solver non eseguito; parsing BLOCKED | root cause CSV header/data order |
| 2026-10-10 | F2A-V evidence mobility | evidence commit `f318a217dfee2f99d51e834948bcf765d5d45c6b` | LFS archive 38MB e Windows SHA PASS | recovery offline, senza nuovo MPI |
| 2026-10-10 | F2A-V offline recovery (report Codex locale, non committato) | Windows partial result, manifest SHA e2c945442ab49397bc94164c41498b38fc3f091d65db60481c19ca8ec7612ec4 | `BLOCKED_F2AV_RECOVERY_MISSING_F2A_REFERENCE`; CSV normalizzato, 10 pairs e hist/extrema/IEEE coerenti, 79 file+8 staged inputs come riportato; 139 PASS, 2 SKIP | trasportare F2A sealed reference da Fair, poi rerun offline in output nuovo |
| 2026-10-10 | Project management | documentation branch `docs/r6-project-ledger-20261010` | Primo PROJECT_LEDGER creato; nessun risultato fisico promosso | prossima sessione legge ledger e source refs |

## Modello di append per step successivo
`| YYYY-MM-DD | gate | branch + HEAD + run SHA/path | CODE/COMPILE/RUNTIME/SCIENTIFIC decision con blocchi | next gate |`

Ogni nuova riga deve indicare un preciso *scope*; se un risultato rimane blocked, scrivere BLOCKED anche quando alcuni sub-check PASS.

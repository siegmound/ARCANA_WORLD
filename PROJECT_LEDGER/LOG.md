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

| 2026-10-10 | Repo synchronization decision | GitHub `docs/r6-project-ledger-20261010` vs Windows dirty worktree vs Fair evidence | Tre flussi separati; nessun Fair code pull necessario; nessun merge docs su Windows noncommittato | Windows fetch read-only docs; Fair evidence-only push F2-A; Windows LFS evidence fetch e offline recovery |

| 2026-10-10 | F2-A sealed companion evidence push | `evidence/r6-bw1-f2av-20261010` commit `72df050f1dc6616426fd25b33fd7de0cc15d83ac` | PASS transport upload Git LFS su Fair; manifest verificato nel preflight; nessun R6 code pull | Windows fetch/LFS archive + SHA, poi F2A-V recovery offline in nuova dir |

| 2026-10-10 | F2-A sealed Windows intake | GitHub evidence commit `72df050f1dc6616426fd25b33fd7de0cc15d83ac`; manifest inner SHA `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936` | PASS download Git LFS, archive hash, manifest hash, estrazione Windows | F2A-V recovery offline con reference |
| 2026-10-10 | F2A-V recovered against F2-A sealed | Windows `outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/`; manifest SHA `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f` | `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`, runner exit 0. Codice ed evidenza derivata Windows-only, non review indipendente | code review, test SciPy dove necessario, commit codice, numerical adjudication; Solver non autorizzato |

| 2026-10-10 | F2A-V numerical adjudication (Codex Windows read-only report) | complete recovery manifest `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`; source branch HEAD `df670c8c...` | GO only for F2-B preflight **design**. Matrice n128884, 10 asym anomalies, DOF mapping UNKNOWN, no nullspace/condition evidence. 139 PASS/2 SKIP; NVHPC corrected writer unqualified; code uncommitted | consolidate Windows code; F2-B design without Fair/MPI/Solver; preserve original BLOCKED |

| 2026-10-10 | R6 code consolidation Windows -> GitHub | `r6/si1-bandwidth-f2av` commit `61dad0fabaa4f2bb72c386d85a77564894a91ce2` | PASS commit/push di 4 file writer F2A-V/recovery/tests, 395 insertions e 8 deletions; `outputs/r6_si1_bandwidth_f2av_offline_recovery/` ancora untracked | integrare PR #1 ledger; conservare output recovery locale, design F2-B solo |

## Modello di append per step successivo
`| YYYY-MM-DD | gate | branch + HEAD + run SHA/path | CODE/COMPILE/RUNTIME/SCIENTIFIC decision con blocchi | next gate |`

Ogni nuova riga deve indicare un preciso *scope*; se un risultato rimane blocked, scrivere BLOCKED anche quando alcuni sub-check PASS.

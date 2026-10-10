# Stato operativo corrente — checkpoint di sviluppo
**As of:** 2026-10-10; fonte attiva GitHub `siegmound/ARCANA_WORLD`.
**Source working branch:** `r6/si1-bandwidth-f2av`, **HEAD:** `df670c8c4faaed641997f5c4bdb701e2ba0afc7d` (osservato quando il ledger è stato preparato). Altri commit successivi richiedono verifica, non sono automaticamente integrati qui.
**Evidence branch:** `evidence/r6-bw1-f2av-20261010`, HEAD `72df050f1dc6616426fd25b33fd7de0cc15d83ac` (copia LFS non governante; F2A-V parent archive at `f318a217`).

## Gate in primo piano: ShellSet BW1 F2A-V
- Code fix strutturale Fortran: PASS commit `df670c8...`.
- Fair NVFortran 25.11 compile-only: `COMPILE_ONLY_COMPLETE_RUNTIME_NOT_EXECUTED`, `ShellSet.exe` creato.
- Fair Linux regressions: **138 passed**, test exit 0.
- Fair assembly-only run: 2 rank MPI, 1 modello, ~282.09 s, **MPI returncode 75**, `BW1_F2AV_STOP_BEFORE_SOLVER` + `BW1_F2A_STOP_BEFORE_SOLVER`. No Solver/factorization.
- Postprocessor: **`BLOCKED_F2AV_QUALIFICATION`**, failure `F2AVError: invalid saturation indicator`.
- Root cause verificata nel CSV originale: writer dati nell'ordine `...,abs_delta,relative_delta,abs_delta_saturated,...` ma header/parser dichiarano `...,abs_delta,abs_delta_saturated,relative_delta,...`. **Non** assumere che sia l'unico errore.
- Evidence Fair run dir: `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2AV_RUN/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z`.
- Copia Windows estratta: `F:\corsiiiuu\Magistrale\Arcana\F2AV_RECOVERY_INPUT\df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z`.
- Evidence archive SHA256: `0a67103b04959e4f4c0c211a29800f31262f4950ebe34bee60ffa14166041c64`.
- Preservare originale BLOCKED. **Offline recovery parziale storica**: inizialmente `BLOCKED_F2AV_RECOVERY_MISSING_F2A_REFERENCE`, manifest derivato `e2c945442ab49397bc94164c41498b38fc3f091d65db60481c19ca8ec7612ec4`. Evidenza del run senza riferimento mantenuta separata.
- **Recovery offline F2A-V completa eseguita localmente Windows il 2026-10-10** dopo recupero del sealed F2-A: runner exit `0`; decisione `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`, nuovo manifest SHA256 `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`. Input F2-A inner manifest SHA256 `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936` verificato su Windows, archive hash verificato dal `.sha256`. Nuovo risultato locale NON ancora committato/revisionato indipendentemente; numerical adjudication non compiuta.

## Altri stati importanti, non confondere con questo gate
- Fair upstream ShellSet parallel solve eseguito con successo sull'esempio `ListEx1`: 9 modelli su 9, diversi setting NVIDIA, proof `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json`. **Non** qualifica automaticamente la matrice e la soluzione meccanica ARCANA SI1.
- R6 B6: candidate kinematic e stato rift in workflow separato, ma `B6N5` impedisce ulteriore evoluzione postattivazione. B6N6 definisce separazione tra dt interno e stati persistenti. La documentazione storica PRE-B0 non rappresenta più lo stato attuale.

## AUTORIZZAZIONI conservate
`F2-B solver/factorization = NOT_AUTHORIZED`; `ARCANA SI1 mechanics = NOT_QUALIFIED`; `global forward evolution = NOT_AUTHORIZED`; `WORLD_HISTORY production = NOT_AUTHORIZED`; nessun nuovo run MPI F2A-V per semplice correzione CSV. Non confondere MPI exit 75 intenzionale con successo del parser.

**Gate di trasporto e recovery chiuso (2026-10-10):** sealed F2-A pubblicato via Git LFS `72df050f1dc6616426fd25b33fd7de0cc15d83ac`, scaricato ed estratto Windows con doppia verifica SHA256. Recovery completa eseguita nella directory `outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/`. Nuova decisione accettata dal runner: `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`. Rimane da validare/revisionare il codice locale e le misure in adjudication; niente solver. SciPy assente nell'interprete Windows per la raccolta aggiuntiva BW0/BW1.

**Unica prossima attività:** `NEXT_ACTION.md`. Gli altri track possono essere discussi, ma non promossi senza gate.

## Sincronizzazione tra macchine (2026-10-10)
- `WINDOWS_WORKTREE_ONLY`: writer F2A-V corretto, recovery, test e output parziale + completo **non committati**; backup del codice locale confermato.
- `FAIR_WORKTREE_ONLY`: i bundle originali restano immutabili; push del companion F2-A completato senza pull del codice.
- `GITHUB_BRANCH_ONLY`: `PROJECT_LEDGER/` nel branch docs; **non** ancora integrato nel branch di sviluppo e dunque non visibile automaticamente al checkout Windows/Fair.
- `EVIDENCE_LFS`: F2A-V originale e companion sealed F2-A pubblicati su GitHub; F2-A scaricato e verificato su Windows.
Non effettuare merge docs o checkout che possa sovrascrivere il diff locale Codex. Procedura dettagliata in `PROCEDURE.md`.

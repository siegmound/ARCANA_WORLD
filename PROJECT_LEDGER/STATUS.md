# Stato operativo corrente — checkpoint di sviluppo
**As of:** 2026-10-10; fonte attiva GitHub `siegmound/ARCANA_WORLD`.
**Source working branch:** `r6/si1-bandwidth-f2av`, **HEAD:** `df670c8c4faaed641997f5c4bdb701e2ba0afc7d` (osservato quando il ledger è stato preparato). Altri commit successivi richiedono verifica, non sono automaticamente integrati qui.
**Evidence branch:** `evidence/r6-bw1-f2av-20261010`, commit `f318a217dfee2f99d51e834948bcf765d5d45c6b` (copia LFS non governante).

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
- Preservare originale BLOCKED. **Offline recovery non ancora dimostrato**, numerical adjudication non compiuta.

## Altri stati importanti, non confondere con questo gate
- Fair upstream ShellSet parallel solve eseguito con successo sull'esempio `ListEx1`: 9 modelli su 9, diversi setting NVIDIA, proof `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json`. **Non** qualifica automaticamente la matrice e la soluzione meccanica ARCANA SI1.
- R6 B6: candidate kinematic e stato rift in workflow separato, ma `B6N5` impedisce ulteriore evoluzione postattivazione. B6N6 definisce separazione tra dt interno e stati persistenti. La documentazione storica PRE-B0 non rappresenta più lo stato attuale.

## AUTORIZZAZIONI conservate
`F2-B solver/factorization = NOT_AUTHORIZED`; `ARCANA SI1 mechanics = NOT_QUALIFIED`; `global forward evolution = NOT_AUTHORIZED`; `WORLD_HISTORY production = NOT_AUTHORIZED`; nessun nuovo run MPI F2A-V per semplice correzione CSV. Non confondere MPI exit 75 intenzionale con successo del parser.

**Unica prossima attività:** `NEXT_ACTION.md`. Gli altri track possono essere discussi, ma non promossi senza gate.

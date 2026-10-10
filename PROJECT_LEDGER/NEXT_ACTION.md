# Prossimo incarico unico — F2A-V offline recovery e writer fix
**Stato:** READY_TO_IMPLEMENT_OFFLINE_RECOVERY; non già compiuto.
**Working code branch:** `r6/si1-bandwidth-f2av` source `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`.
**Input originale:** Fair assembly-only dir e copia verificata su GitHub LFS in `EVIDENCE_INDEX.md`.

## Root cause confermata sul CSV vero
Header: `i,j,aij,aji,abs_delta,abs_delta_saturated,relative_delta,row_scaled_discrepancy,structure`.
Rows: `i,j,aij,aji,abs_delta,relative_delta,abs_delta_saturated,row_scaled_discrepancy,structure`.
Esempio `715,716`: field6 `2.7159541648303220E-001`, field7 `0`.
Il runner ha registrato `F2AVError: invalid saturation indicator`; il codice non è crashato in Solver.

## Attività in ordine
1. Verificare branch/HEAD, file e hashes del bundle F2A-V e del **companion F2-A recovery**; original result `BLOCKED_F2AV_QUALIFICATION` e MPI rc 75; source/input/memory envelope.
2. Correggere entrambe le `WRITE(78,...)` del **generatore Fortran** nel runner F2A-V affinché ordine args e FORMAT siano identici all'header. Aggiungere regressione che controlli anche associazione semantica valori-colonne, non solo count dei descriptors.
3. Implementare recovery **offline separata**: leggere originale readonly, verificare manifest, hashes, input e stop markers, ricostruire *nuovo* CSV canonico scambiando col 6/7 solo quando verificato, richiamare parser stretto, riconciliare census, extrema, istogrammi, F2-A values, IEEE flags e mapping status, verificare hash originali before/after; output nuovo con result+manifest propri.
4. Se qualsiasi controllo fallisce, `BLOCKED` e nessuna retro-promozione. Su successo atteso `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION` (non PASS numerico).
5. Suite F0/F1/F2-A/F2A-V + nuovi test; `py_compile`, json checks e `git diff --check`. **Non** fare commit/push automaticamente se ancora in code review.
6. Solo dopo recovery: NUMERICAL ADJUDICATION e decisione su F2-B / alternativa.

**Divieti:** niente Fair, MPI, Solver/fattorizzazione, gauge, source-lock edit, prestazioni parallele da riesaminare senza motivazione, WORLD_HISTORY mutate o evolution canonica.

**Output richiesto allo sviluppatore:** root cause testata; file modificati; test e scope; percorso e digest delle evidenze; decisione del recovery; blocchi rimasti; comando esatto per eventuale ulteriore execution offline.

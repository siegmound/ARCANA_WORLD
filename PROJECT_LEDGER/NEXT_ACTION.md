# Prossima attività — consolidare recovery Windows e progettare F2-B preflight
**Input gate:** adjudication offline Windows 2026-10-10; outcome **GO alla progettazione F2-B, NO alla sua esecuzione**. Vedi `STATUS.md`, `EVIDENCE_INDEX.md`, `F2B_PREFLIGHT_DESIGN.md`.

## Fase 1 — Consolidamento codice già revisionato (Windows)
1. Verificare `git status --short`, branch `r6/si1-bandwidth-f2av`, HEAD `df670c8c4faaed641997f5c4bdb701e2ba0afc7d` e backup `F2AV_CODE_BACKUP_20261010`; non fare pull/merge/reset prima del commit.
2. Fare stage **solo di quattro percorsi di codice/test**:
   `scripts/r6_si1_bandwidth_f2av_fair_diagnostics.py`,
   `tests/test_r6_si1_bandwidth_f2av_fair_diagnostics.py`,
   `scripts/r6_si1_bandwidth_f2av_recover_evidence.py`,
   `tests/test_r6_si1_bandwidth_f2av_recover_evidence.py`.
   NON aggiungere `outputs/`, né evidenze originali/manifest sigillati.
3. Verificare `git diff --cached` e `git diff --cached --check`, suite 139 PASS 2 SKIP nel medesimo scope, copertura E2E sealed mancante dichiarata, e SciPy/BW0/BW1 status. Se necessario aggiungere il test positivo E2E con fixture sintetica/appropriata, senza introdurre dipendenza HPC. Non fingere che sia già passato.
4. Solo dopo revisione ed esplicita decisione dell'operatore, commit e push del codice nel branch R6. Se l'operatore non ha ancora dato via libera, fermarsi al report. Merge successivo della PR draft #1 ledger solo su worktree pulito/reviewato, preservando gli aggiornamenti.
5. La recovery derivata completa resta locale fino a un proprio piano di evidence publication/seal. I digest nel ledger sono riferimenti, non equivalenti al bundle pubblicato.

## Fase 2 — F2-B PREFLIGHT DESIGN (no build, no solve)
**Obiettivo:** piano testabile per determinare la fattibilità numerica del caso ingegneristico ARCANA SI1, distinguendola dall'autorizzazione scientifica della meccanica.

1. Audit mirato Fortran `MOD_Shells`, operator assembly, calls a `Solver`, LAPACK band layout e permutation. Derivare formula del mapping completo raw DOF -> pre/post permutation -> nodi/componenti/support, facendo hash di dati e mapping effettivamente disponibili. Se impossibile mantenere `DOF_MAPPING_UNVERIFIED`.
2. Stabilire se dall'equazione e dai vincoli specifici ci si aspetta A simmetrica/non simmetrica; come sono prodotti i dieci mismatch; distinguere errore di assembly, normale non-simmetria della formulazione e perdita di simmetria da trasformazioni/BC. Nessuna riparazione arbitraria `(A+A^T)/2`.
3. Separare ipotesi nullspace/gauge da evidenze e progettare controlli bounded. Non aggiungere automaticamente vincoli che alterino la fisica. Documentare assenza di BC velocity e rischio dei modi rigidi solo come ipotesi da verificare.
4. Dimensionare memoria reale del path di solve: band array 2,249,799,104 byte, copie/fill/factorization, workspace BLAS/LAPACK, per-process vs aggregate, expected process topology, wall-time e failure criteria. Non usare il solo array come stima RSS.
5. Progettare il futuro step di compilazione NVHPC per writer + verifica dei flag IEEE e strict validation; non scambiarlo con una qualifica numerica.
6. Definire il contratto di un **futuro** bounded solve engineering-only: input hashes, residual backward error e criterio normalizzato, check fisici limitati allo scope, failure/error escalation, output manifest, stop/cancel, prohibitions; numeri/threshold non inferiti. Specificare quali test devono precedere la sola autorizzazione di esecuzione.
7. Restituire un deliverable progettuale `F2B_PREFLIGHT_DESIGN.md` con opzioni, rischi, nuove prove mirate strettamente necessarie e decisione `DESIGN_COMPLETE_PENDING_EXECUTION_AUTHORITY` o `DESIGN_BLOCKED_...` (etichette workflow suggerite, non seals).

**Divieti:** nessun nuovo Fair, MPI, fattorizzazione, Solver, autogauge, risoluzione fisica, evoluzione, modifica source-locked ShellSet o stato canonico. No blanket benchmark upstream. Ogni nuovo gate deve aggiornare il ledger e linkare risultati/hash nuovi.

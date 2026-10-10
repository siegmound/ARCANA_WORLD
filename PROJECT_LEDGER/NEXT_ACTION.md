# Prossima attività — integrare il ledger e progettare F2-B preflight
**Input gate:** adjudication offline Windows 2026-10-10; outcome **GO alla progettazione F2-B, NO alla sua esecuzione**. Vedi `STATUS.md`, `EVIDENCE_INDEX.md`, `F2B_PREFLIGHT_DESIGN.md`.

## Fase 1 — Consolidamento e sincronizzazione
1. **DONE**: le 4 modifiche a diagnostica writer + recovery + test sono nel commit `61dad0fabaa4f2bb72c386d85a77564894a91ce2` sul branch `r6/si1-bandwidth-f2av`, senza includere `outputs/`.
2. **NEXT**: con PR #1, integrare `PROJECT_LEDGER/` e `AGENTS.md` nel branch di codice dopo controllo che il diff è soltanto documentale (eccetto i 4 puntatori README/stato, anch'essi documentali) e che l'HEAD base è il commit pubblicato. In Windows fare solo fetch e fast-forward su un worktree senza modifiche tracciate; NON utilizzare reset/hard o fare merge manuali sovrascrivendo `outputs/`.
3. **PENDING**: il recovery derivato completo resta nella directory untracked Windows. Pubblicarlo solo con un piano di evidence publication/seal separato; i digest in questo ledger NON equivalgono a un bundle originale sigillato.
4. **OPEN TEST GAPS**: writer corretto non ancora ricompilato con Fair/NVHPC, nessun test positivo E2E automatico che integri F2-A sealed, BW0/BW1/SciPy ancora da verificare nell'ambiente adatto. Non retro-promuovere `BLOCKED_F2AV_QUALIFICATION` o la meccanica.

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

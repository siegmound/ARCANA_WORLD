# Prossima azione — F2A-V NUMERICAL ADJUDICATION (offline, read-only)
**Stato attuale (2026-10-10):** `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`. Questo è un PASS di **recovery tecnica**, non un PASS della matrice/solver. Il run originale resta `BLOCKED_F2AV_QUALIFICATION`. Le modifiche writer/recovery/test e l'output completo esistono **solo sul worktree Windows**; `r6/si1-bandwidth-f2av` remoto ancora a `df670c8...`.

## Input recovery completa
- `outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/F2AV_RECOVERY_RESULT.json`.
- `F2AV_RECOVERY_ARTIFACT_MANIFEST.json`, SHA256 `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`.
- Sealed F2-A Windows: `F:\corsiiiuu\Magistrale\Arcana\F2A_RECOVERY_INPUT\dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3-20261008T222906Z`. Manifest SHA256 `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`.
- Source F2A-V Windows: `F:\corsiiiuu\Magistrale\Arcana\F2AV_RECOVERY_INPUT\df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z`. Evidenza storica immutabile.
- Originali e recovery precedente rimangono separati. Fair non deve essere coinvolto per questa analisi.

## Step 1 — Audit della recovery e review codice
1. In Windows, verificare branch, HEAD, `git status`, backup codice, e hash del nuovo manifest; controllare che result decision sia esattamente quella sopra, non soltanto exit=0.
2. Review di `scripts/r6_si1_bandwidth_f2av_fair_diagnostics.py`, nuovo `scripts/r6_si1_bandwidth_f2av_recover_evidence.py` e due test. Verificare schema 9 colonne, swapped 6/7 storico, determinismo, validazione F2-A, protezione path/manifest, invariabilità hashes.
3. Rieseguire regressioni pertinenti, py_compile, schema checks; fare raccolta BW0/BW1 nell'ambiente con SciPy quando disponibile. Produrre outcome `CODE_REVIEWED_PASS` o `BLOCKED`. Non aggiungere `outputs/` al commit codice.
4. Solo dopo review, fare commit del codice e successiva integrazione ledger nel branch R6 in worktree pulito. Nessuna alterazione alle prove originali.

## Step 2 — Adjudication numerica separata, solo read-only
5. Leggere integralmente il result e report F2A-V, census normalizzato delle 10 divergenze, summary F2-A e source/array layout. Riconciliare numeri e localizzare eventuali discrepanze di scala, simmetria, diagonale, norma/forzante, IEEE, bounded extrema, DOF. Nessun mapping geografico presunto.
6. Valutare, con qualifiche esplicite, se la matrice ammetta ipotesi ragionevoli sul solver: simmetria, norme relative vs assolute, possibile malcondizionamento, singularità/modalità rigide non dimostrate, assenza di dominanza stretta NON prova di singularità, IEEE flags senza attribuzione causale.
7. Confrontare policy del caso ingegneristico e fisica ARCANA T0. Separare `ENGINEERING_SOLVE_FEASIBILITY` da `SCIENTIFIC_MECHANICS_AUTHORITY`. Non stimare condition number/eigenvalues/gauge senza evidenza.
8. Creare relazione di adjudication con riferimenti file+SHA e una **decisione fail-closed esplicita**: `F2B_PREFLIGHT_PROPOSAL_ALLOWED`, `NEEDS_TARGETED_DIAGNOSTICS`, oppure `BLOCKED_NUMERICAL_OR_MODEL_GAP`. I nomi qui sono proposte di workflow, non promozioni autoritative.
9. Aggiornare `PROJECT_LEDGER/STATUS.md`, `LOG.md`, `EVIDENCE_INDEX.md`, `ROADMAP.md` e `NEXT_ACTION.md` nello stesso commit del gate documentato.

**Divieti:** Fair, MPI, Solver, fattorizzazione, auto-gauge, evoluzione fisica, canonical promotion, riscrittura dei risultati e dei manifest storici. Non confondere recovery completa con qualifica numerica o fisica.

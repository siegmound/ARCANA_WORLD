# ARCANA WorldSim R6 — Stato operativo corrente
**Data ricognizione:** 2026-10-10. **Authority:** questa pagina è un indice operativo, non un seal scientifico. In caso di conflitto prevalgono result, manifest, source lock e contratti originali verificati.

## Repositories / sincronizzazione
- Repo: `siegmound/ARCANA_WORLD`; branch di codice `r6/si1-bandwidth-f2av`, HEAD remoto `61dad0fabaa4f2bb72c386d85a77564894a91ce2` (commit del fix writer e della recovery, pubblicato su GitHub e verificato 2026-10-10). Il run F2A-V originale resta vincolato a `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`.
- `WINDOWS_WORKTREE_ONLY`: le 4 modifiche writer/recovery/test **sono state committate e pubblicate** al commit `61dad0fabaa4f2bb72c386d85a77564894a91ce2`. Sul worktree Windows rimane non tracciato soltanto `outputs/r6_si1_bandwidth_f2av_offline_recovery/`, che è evidenza derivata, non codice. Backup del codice precedente confermato. Prima di qualsiasi sincronizzazione ricontrollare `git status` e l'eventuale collisione con file untracked.
- `MERGED_DEV_BRANCH`: PR #1 della bitacora **merged il 2026-10-10**, commit merge `a388e567aa48c3376da7d4a72b0c2c3e8d64f533`; verificata presenza di `PROJECT_LEDGER/`, `AGENTS.md` e script di recovery nel branch scientifico. Il code fix originale rimane nel commit `61dad0fa`; i soli output recovery locali Windows non sono pubblicati in Git.
- `EVIDENCE_LFS`: branch `evidence/r6-bw1-f2av-20261010` HEAD `72df050f1dc6616426fd25b33fd7de0cc15d83ac` contiene original F2A-V e companion F2-A sealed; intake su Windows verificato.
- Fair: originali HPC immutabili, non serve pull del codice durante audit offline.

## Gate scientifico attuale
**Decisione della review offline Windows (resoconto Codex, 2026-10-10):** `GO_FOR_F2B_SOLVER_PREFLIGHT_DESIGN_ONLY` (etichetta operativa del ledger, NON un nuovo seal/contract di authorità). Sono ammessi lo studio del preflight e i test statici non-esecutivi; **Solver/F2-B execution non autorizzata**.

### Evidenze e risultati
- Originale F2A-V Fair: `BLOCKED_F2AV_QUALIFICATION` su parser `invalid saturation indicator` dopo MPI stop deliberato 75 prima del Solver; l'originale NON viene riscritto.
- Recovery completa Windows `outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/`: `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`; result e 3 artefatti riconciliati nella review; manifest SHA256 `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`. F2-A sealed manifest SHA256 `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`.
- Review: original F2A-V 79 membri manifest + manifest (80 file) intatti; CSV normalizzato solo swap colonne 6/7; cross-reference F2-A sealed passato. `139 passed, 2 skipped`, `py_compile`, JSON e `git diff --check` PASS; pytest primo lancio basetemp default fallito, rerun con --basetemp repository PASS. SciPy/BW0/BW1 non ancora interamente ricontrollati nel medesimo ambiente.
- Matrice: n=128884; kl=ku=727; nKRows=2182; 186996964 valid, 1804327 nonzero, 185192637 zero, nonfinite 0. REAL*8 band array 2249799104 byte stimati, non RSS globale. 93434040 coppie upper confrontate, 10 anomalie (1 zero/nonzero e 9 nonzero mismatch) a threshold rel `1e-12`. Max coefficient abs `3.6508239112970148E+032`; min nonzero `1.4073748835532800E+014`, circa 18.41 decadi. Dominanza strict 0, near 0, nonstrict 128884.
- Le 10 anomalie non hanno causa dimostrata; la simmetria teorica dell'operatore non è ancora provata. `DOF_MAPPING_UNVERIFIED`. Non esistono stime qualificate di condizionamento, spettro, singolarità o gauge. IEEE `underflow/inexact` inherited, cause ignote; nessun overflow/underflow per fase osservati nel report.

### Rischi che rimangono aperti
1. Correzione del writer F2A-V non ancora ricompilata/qualificata su Fair/NVHPC; il CSV recovery proviene dal writer precedente.
2. Manca test positivo automatico E2E recovery con F2-A sealed (run reale controllato dalla review).
3. IEEE intrinsics/sticky flag comportamento da qualificare dove richiesto prima di fare affidamento su nuova instrumentation NVHPC.
4. Mappatura DOF raw -> permutation/node/component/geografia incompleta e classe dell'operatore/asimmetria/gauge non accertate.
5. R6 B6N5 post-rift è un **blocco di autorità fisica separato**; ShellSet engineering case usa parametri di riferimento NON ARCANA science authority.

## Autorizzazioni
`F2B_PREFLIGHT_DESIGN_ALLOWED=true` (solo design; decisione operativa);
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`;
`FORWARD_EVOLUTION_AUTHORIZED=false`;
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
L'esecuzione parallela ShellSet su upstream ListEx1 9/9 è già evidenziata: non ripetere come nuovo gate. **Prossima attività:** `NEXT_ACTION.md`.

## Integrazione documentale — 2026-10-10
`PROJECT_LEDGER/` è presente nel branch `r6/si1-bandwidth-f2av` dopo merge PR #1 (SHA `a388e567aa48c3376da7d4a72b0c2c3e8d64f533`). Lo stato di questo file è quello successivo al merge; nuove chat leggono `AGENTS.md` e `PROJECT_LEDGER/NEW_CHAT.md` senza recuperare una branch docs separata. Su Windows **non** è ancora confermato un fetch/fast-forward fino al commit merge; eseguire sincronizzazione non distruttiva dopo controllo `git status`. Nessun nuovo dato numerico pubblicato da questa integrazione.

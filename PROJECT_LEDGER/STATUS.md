# ARCANA WorldSim R6 — Stato operativo corrente
**Data ricognizione:** 2026-10-10. **Authority:** questa pagina è un indice operativo, non un seal scientifico. In caso di conflitto prevalgono result, manifest, source lock e contratti originali verificati.

## Repositories / sincronizzazione
- Repo: `siegmound/ARCANA_WORLD`; branch di codice `r6/si1-bandwidth-f2av`, baseline codice `61dad0fabaa4f2bb72c386d85a77564894a91ce2` (fix writer e recovery) e ultimo checkpoint documentale `6e6bd36f3db2e6e07f406d757721f7a4b552cf8b`; rilevare HEAD live tramite Git, non inferirlo da questa pagina. Il run F2A-V originale resta vincolato a `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`.
- `WINDOWS_WORKTREE_ONLY`: le 4 modifiche writer/recovery/test **sono state committate e pubblicate** al commit `61dad0fabaa4f2bb72c386d85a77564894a91ce2`. Sul worktree Windows rimane non tracciato soltanto `outputs/r6_si1_bandwidth_f2av_offline_recovery/`, che è evidenza derivata, non codice. Backup del codice precedente confermato. Prima di qualsiasi sincronizzazione ricontrollare `git status` e l'eventuale collisione con file untracked.
- `MERGED_DEV_BRANCH`: PR #1 della bitacora **merged il 2026-10-10**, commit merge `a388e567aa48c3376da7d4a72b0c2c3e8d64f533`; verificata presenza di `PROJECT_LEDGER/`, `AGENTS.md` e script di recovery nel branch scientifico. Il code fix originale rimane nel commit `61dad0fa`; la recovery completa è ora pubblicata separatamente in Git LFS; la directory output locale resta untracked ed è da preservare.
- `EVIDENCE_LFS`: branch `evidence/r6-bw1-f2av-20261010` HEAD `2b03fa558b02cb865c4f234e45f0386fab678822` contiene original F2A-V, companion F2-A sealed e archivio recovery F2A-V completo; push LFS verificato tramite metadati remoti, intake/source integrity attestati dal run Windows.
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
`PROJECT_LEDGER/` è presente nel branch `r6/si1-bandwidth-f2av` dopo merge PR #1 (SHA `a388e567aa48c3376da7d4a72b0c2c3e8d64f533`). Lo stato di questo file è quello successivo al merge; nuove chat leggono `AGENTS.md` e `PROJECT_LEDGER/NEW_CHAT.md` senza recuperare una branch docs separata. Windows ha confermato `PASS_R6_LEDGER_SYNC` fino al checkpoint `6e6bd36f3db2e6e07f406d757721f7a4b552cf8b`; aggiornamenti successivi richiedono nuovo fetch/fast-forward non distruttivo. Nessun nuovo dato numerico pubblicato da questa integrazione.

## F2A-V recovery complete — published derived evidence (2026-10-10)
- Evidence commit: `2b03fa558b02cb865c4f234e45f0386fab678822` on `evidence/r6-bw1-f2av-20261010`.
- Git LFS archive: `evidence/F2AV_OFFLINE_RECOVERY_F2AV_WITH_F2A_REFERENCE_V1.tar.gz`, archive SHA256 `bdde8d4320b1fa6de577988bf911817918e910373bdbff9922c9d9c98f646562` matched remote sidecar and reported Windows digest.
- Derived recovery manifest SHA256 `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`; 3 artifact members plus manifest, source integrity PASS in Windows procedure. Binary payload not independently downloaded in this session.
- Transport `PASS_F2AV_RECOVERY_EVIDENCE_PUSH`; original Fair decision `BLOCKED_F2AV_QUALIFICATION` unchanged; no new solver authority.
- NEXT: F2-B preflight **design only**, see `NEXT_ACTION.md`.

## F2-B design reconnaissance received — 2026-10-10
- Codex read-only reconnaissance eseguita sul **checkout Windows HEAD `6e6bd36f3db2e6e07f406d757721f7a4b552cf8b`** (il remoto era già `bb3b6c781e6d8dac20c446ab9b0e97fe634cb61d`). Stato locale report: nessuna modifica tracciata, 8 file untracked nelle recovery output; nessun test o run eseguito.
- Fonte: report operatore/Codex, **non sealed artifact**. La ricognizione individua due componenti DOF per nodo, permutazioni candidate `new_to_old/old_to_new` e stage FEG/runtime, ma il collegamento end-to-end a raw F2A-V e base geografica resta `DOF_MAPPING_UNVERIFIED`.
- `DGBSV` generale a banda, matrix+RHS overwritten; `INFO=0` non verifica residuo. Zero BC velocity e zero fault; nullspace/gauge `UNKNOWN`; nessuna simmetrizzazione, nessuna stima condizionamento.
- **Disponibile su GitHub:** `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md` (design derivato, non gate solver).
- **NEXT:** `F2B-D1` DOF/permutation provenance attestation design; F2B-E solve/fattorizzazione ancora `NOT_AUTHORIZED`. Nessun nuovo run Fair/MPI/Solver autorizzato.

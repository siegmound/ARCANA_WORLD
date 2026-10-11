# Istruzione di avvio per una nuova chat o Codex

## Checkpoint N2C-W2 — 2026-10-11
- Baseline sorgenti: branch `r6/si1-bandwidth-f2av`, W2 overlay `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e` (parent `8645a48f7ca716c2e3c4b3cee087e7e6f7333262`), già su GitHub e Fair; il ledger è stato aggiornato successivamente su richiesta esplicita dell'utente tramite GitHub, senza esecuzione HPC. Verificare HEAD remoto effettivo prima di agire; non presumere che il detached checkout Fair includa il commit documentale.
- W1: GNU e NVFORTRAN 25/25 fixture PASS; W2: 13 PASS/1 SKIP Windows, source-lock 15 membri, Fair preflight compiler/CLI PASS ma nessuna compilazione né runtime W2.
- Prossimo: candidate builder `--output` in directory nuova esterna al repository, compile-only bridge e intero call graph, con manifest/log/SHA; non lanciare ShellSet/MPI/Solver. Fonte di autorità `NEXT_ACTION.md` e `PROCEDURE.md`.
- Risorse: W1 `MAX_N=2048`, `MAX_STORAGE=2000000` elementi NON significano 2 GB; richiesta relativa ai 2 GB tracciata come `RESOURCE_2GB_SCOPE_UNRESOLVED` senza cap globale. SI1 matrice `2249799104` byte; RAM Fair disponibile riportata non è garanzia di job memory grant.
- Decisione `N2C_W2_CANDIDATE_OVERLAY_IMPLEMENTED__RUNTIME_CAPTURE_BLOCKED_BY_IDENTITY_AND_CODEC_BOUNDS`; scientific/solver gates tutti invariati.


Repository: `siegmound/ARCANA_WORLD`. **Leggi esclusivamente `PROJECT_LEDGER/` per ricostruire la situazione operativa**, nel seguente ordine: `README.md`, `STATUS.md`, `NEXT_ACTION.md`, `ROADMAP.md`, `PROCEDURE.md`, `EVIDENCE_INDEX.md`. Solo per risolvere la precisa attività leggi i sorgenti, i contratti o i manifest citati nel ledger. Non chiedere handoff di vecchie chat e non fidarti di vecchi README/prompt legacy.

Prima di agire: stampa/verifica repo, branch, HEAD, dirty files; verifica che la cartella PROJECT_LEDGER sia nel branch usato (se non lo è, il branch `docs/r6-project-ledger-20261010` è l'origine documentale da integrare). Se il codice cambia dopo lo snapshot della bitacora, ricontrolla il gate; non sovrascrivere un risultato documentato con supposizioni.

ARCANA è orchestratore multiscientifico; finestre candidate, time step interno adattivo, stati significativi derivati da eventi e replay. Il vecchio R3/R4/R5 è legacy non-target. ShellSet upstream è già stato eseguito in parallelo; la F2A-V sul caso ARCANA è distinta.

Segui esclusivamente `NEXT_ACTION.md` finché un risultato verificato non ne aggiorna il contenuto. Al termine di ogni gate significativo fai aggiornare `STATUS.md`, `LOG.md`, `NEXT_ACTION.md` e indici correlati nel repository con commit e push, **dopo** regressioni/approvazioni appropriate. Se mancano fonti o autorizzazioni, esplicita BLOCKED e non inventare progresso.

Prima di suggerire qualsiasi comando Fair, leggi `PROJECT_LEDGER/PROCEDURE.md` e verifica il workflow Windows/Codex → GitHub → Fair/Conda → Windows/ledger, inclusi branch, commit ed ambiente effettivi. Non ricreare ambienti e non suggerire SFTP o copie manuali come procedura ordinaria per sorgenti/test.

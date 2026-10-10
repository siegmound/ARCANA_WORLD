# ARCANA WorldSim R6 — PROJECT_LEDGER
**Unico punto di ingresso per la continuità di sviluppo.** Revisione iniziale 2026-10-10. Questo ledger documenta stato, decisioni operative, roadmap e lavoro da riprendere; **non** sostituisce contratti scientifici, manifest firmati, source lock o evidenze.

## Ordine di lettura per ogni nuova chat / sessione Codex
1. `PROJECT_LEDGER/STATUS.md` — dove siamo e cosa NON è autorizzato.
2. `PROJECT_LEDGER/NEXT_ACTION.md` — l'unico incarico immediato.
3. `PROJECT_LEDGER/ROADMAP.md` — dipendenze e gate, non una scadenza temporale imposta.
4. `PROJECT_LEDGER/PROCEDURE.md` — protocollo per lavorare e aggiornare la bitacora.
5. Solo se rilevante: `VISION.md`, `ARCHITECTURE.md`, `SHELLSET_HISTORY.md`, `EVIDENCE_INDEX.md`, `DECISIONS.md`, `LEGACY_CLEANUP.md`, `LOG.md`.

**Authority precedence:** fonti primarie (codice/contratti/manifests/evidenza immutabile) > stato verificato al commit indicato > decisioni progettuali in questo ledger > documentazione vecchia > memoria delle chat. Se i livelli divergono, NON decidere per analogia: registrarli come conflitto e bloccare la promozione pertinente.

**Bootstrap:** leggere `NEW_CHAT.md`. Verificare repository, branch, HEAD, worktree ed evidenza disponibile prima di eseguire qualunque comando. Non inferire stato da date, nomi di file o conteggi test. La prima simulazione R3/R4/R5 è legacy e non è un target per R6.

**Regola aggiornamenti:** ogni gate significativo deve aggiornare insieme `STATUS.md`, `NEXT_ACTION.md`, `LOG.md`, `EVIDENCE_INDEX.md` (se nuove evidenze) e `ROADMAP.md` (se cambia l'avanzamento). Commit e push come modifica coerente; `PROCEDURE.md` definisce il formato. Non trasformare automaticamente risultati passati in PASS canonici.

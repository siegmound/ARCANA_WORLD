# ARCANA WorldSim R6 — PROJECT_LEDGER

**Punto unico di continuità. Stato operativo aggiornato al 2026-10-13.** Il singolo tentativo INT-0B è fallito prima della scrittura degli artefatti; failure report ed evidenza restano immutabili. INT-0B-R1 ha corretto il controllo dei campioni e superato le regressioni offline. Nessuna traiettoria è disponibile e la precedente autorizzazione è consumata: il prossimo passo è richiedere una nuova autorizzazione delimitata, non eseguire automaticamente un retry.

## Leggere in questo ordine
1. `STATUS.md` — solo la sezione iniziale **CURRENT** contiene la priorità attuale; seguono checkpoint storici.
2. `NEXT_ACTION.md` — **un solo incarico corrente**: revisione/autorizzazione esplicita di un nuovo INT-0B-R1 con output fresco; nessuna esecuzione senza di essa.
3. `ROADMAP.md` — dipendenze e filoni paralleli.
4. `PROCEDURE.md` — workflow Git/Windows/Fair e preservazione dei gate.
5. `EVIDENCE_INDEX.md`, `VISION.md`, `ARCHITECTURE.md`, `SHELLSET_HISTORY.md`, `DECISIONS.md`, `LOG.md` e fonti specialistiche secondo la domanda.

**Precedenza:** fonti primarie e prove > commit/scope verificato > priorità di questo ledger > vecchie istruzioni operative > chat. Gli storici «NEXT W2/W3» nei report e vecchi HEAD non sono task attivi. Prima di agire verificare branch, HEAD, dirty/untracked ed evidenze. Non ripetere prove già qualificate nel loro scope.

**Distinguere:** software già testato ≠ integrazione ARCANA ≠ simulazione fisica globale ≠ promozione canonica. R3/R4/R5 sono legacy non-target. Ogni gate aggiorna `STATUS`, `NEXT_ACTION`, `LOG`, `EVIDENCE_INDEX` e `ROADMAP` quando serve, nello stesso commit. `DECISIONS` append-only; risultati `BLOCKED`, hash, source lock, output e report storici rimangono immutati.

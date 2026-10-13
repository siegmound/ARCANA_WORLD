# ARCANA WorldSim R6 — PROJECT_LEDGER

**Punto unico di continuità. Stato operativo aggiornato al 2026-10-13.** La correzione offline INT-0B-R3 identifica un mismatch di schema (`elapsed_years` derivato nei campioni ma assente dal payload finale), amplia la verifica sintetica endpoint e corregge la classificazione della race di exit nel supervisor. Il report del terzo tentativo resta immutato; nessuna traiettoria verificabile è stata scritta. La precedente autorizzazione è consumata: nessun quarto run è autorizzato e INT-1 resta bloccato.

## Leggere in questo ordine
1. `STATUS.md` — solo la sezione iniziale **CURRENT** contiene la priorità attuale; seguono checkpoint storici.
2. NEXT_ACTION.md — un solo incarico corrente: review/consolidamento della correzione R3 e pubblicazione normale; nessun altro run INT-0B o INT-1 senza nuova autorizzazione.
3. `ROADMAP.md` — dipendenze e filoni paralleli.
4. `PROCEDURE.md` — workflow Git/Windows/Fair e preservazione dei gate.
5. `EVIDENCE_INDEX.md`, `VISION.md`, `ARCHITECTURE.md`, `SHELLSET_HISTORY.md`, `DECISIONS.md`, `LOG.md` e fonti specialistiche secondo la domanda.

**Precedenza:** fonti primarie e prove > commit/scope verificato > priorità di questo ledger > vecchie istruzioni operative > chat. Gli storici «NEXT W2/W3» nei report e vecchi HEAD non sono task attivi. Prima di agire verificare branch, HEAD, dirty/untracked ed evidenze. Non ripetere prove già qualificate nel loro scope.

**Distinguere:** software già testato ≠ integrazione ARCANA ≠ simulazione fisica globale ≠ promozione canonica. R3/R4/R5 sono legacy non-target. Ogni gate aggiorna `STATUS`, `NEXT_ACTION`, `LOG`, `EVIDENCE_INDEX` e `ROADMAP` quando serve, nello stesso commit. `DECISIONS` append-only; risultati `BLOCKED`, hash, source lock, output e report storici rimangono immutati.

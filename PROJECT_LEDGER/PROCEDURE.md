# Procedura obbligatoria per sviluppo e handoff

## A. Apertura sessione (operazioni read-only)
1. Aprire `PROJECT_LEDGER/README.md`, `STATUS.md`, `NEXT_ACTION.md`, `ROADMAP.md`, `EVIDENCE_INDEX.md`.
2. Identificare repo/worktree/branch/HEAD e `git status --short`; NON dare per scontato che questo ledger sia già mergeato nel branch di esecuzione.
3. Confrontare gli SHA/gates dello status con codice, contratti e manifest *relativi al task*, e recuperare le evidenze esterne solo se necessario. Non scandagliare automaticamente 48k+ file né rileggere vecchie chat.
4. Ricontrollare se esiste prova precedente della stessa capacità con lo **stesso scope**; evitare qualifiche duplicate.
5. Dichiarare gate e vincoli di esecuzione prima di cambiare files.

## B. Pacchetto di lavoro
Ogni step sostanziale definisce: obiettivo, scope esatto, ingressi+SHA/versioni, provider/metodi, ipotesi, gap/UNKNOWN, acceptance test, budget calcolo/memoria, output root nuovo, marker/exit attesi, azioni proibite. Separare `CODE_READY`, `COMPILE_READY`, `RUNTIME_EVIDENCED`, `SCIENTIFIC_ADJUDICATED`, `CANONICAL_AUTHORIZED`. Un PASS di compilazione non promuove la fisica.

## C. Esecuzione
Preservare evidenze immutabili in output nuovi; validate provenance/source lock prima dell'esecuzione; test locali mirati; HPC solo quando autorizzato; rispettare limiti operatore, stampare risultato e fallire closed. Distinguere stop intentionally nonzero da errori dei parser. Non mutare source lock, stati canonici o rift senza autorizzazione specifica.

## D. Aggiornamento della bitacora a ogni gate significativo
Nello **stesso commit**:
- aggiungere riga datata e immutabile a `LOG.md` (cosa, commit, evidenza, risultato, interpretazione, next);
- aggiornare `STATUS.md` (una sola vista corrente, inclusi blocked/unknown);
- aggiornare `NEXT_ACTION.md` (un task eseguibile, precondizioni e divieti);
- aggiornare `EVIDENCE_INDEX.md` per nuovi run/hash, o registrare esplicitamente "nessuna nuova evidenza";
- aggiornare `ROADMAP.md` **solo** se cambia un gate o una dipendenza; `DECISIONS.md` solo per decisioni architetturali nuove; `LEGACY_CLEANUP.md` per rimozioni.

Mai riscrivere il verdetto di un run precedente; una recovery nuova conserva decisione originale e nuova identità. Ogni documentazione derivata deve dichiarare fonte e status d'autorità. Prima di merge: link check, git diff --check, regressioni pertinenti, nessuna modifica non autorizzata.

## E. Chiudere la chat
Registrare l'ultimo outcome e il prossimo step nel ledger; fornire soltanto branch/HEAD/next action. La chat è cache, **il repo è continuità**. Se si esaurisce il contesto, la nuova chat parte da `NEW_CHAT.md`, non da un riassunto della vecchia chat.

## F. Concorrenza / branch
Un branch di documentazione può progredire indipendentemente. Prima di merge nel branch attivo verificare divergenza, `git status` e diff. Non fare force-push e non committare output scientifici voluminosi sul branch del codice; usare evidenze esterne immutabili o evidence branch LFS separato con SHA.

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

## G. Sincronizzazione Windows / Fair / GitHub
Tre flussi **indipendenti**: (1) `r6/si1-bandwidth-f2av` codice di sviluppo, attualmente modificato **solo nel worktree Windows e non committato**; (2) `docs/r6-project-ledger-20261010` documento operativo creato direttamente su GitHub, non ancora presente nel branch di sviluppo; (3) `evidence/r6-bw1-f2av-20261010` archivio immutabile su GitHub LFS, i payload originali sono su Fair.

- Non fare `git pull` del codice su Fair quando si vuole semplicemente trasferire un bundle di evidenza già prodotto. Per il companion F2-A: leggere il bundle su Fair, `git push` **nel solo worktree evidence LFS**; Windows esegue fetch/LFS pull del branch evidence e valida gli hash.
- Prima di integrare il ledger in Windows fare un `git fetch` del solo branch docs e ispezionarlo; un fetch non aggiorna i file di lavoro. Non eseguire `git pull`, `merge`, `reset --hard`, `checkout` o `restore` sopra modifiche di Codex non committate. Prima preservare e revisionare il diff Windows. Usare merge non distruttivo su worktree pulito oppure un worktree di revisione separato.
- Prima di pubblicare modifiche Codex: review, regressioni e commit nel branch del codice; poi integrare/mergeare il ledger via GitHub o Windows, risolvendo eventuali conflitti sui documenti aggiornati. Non richiedere che Fair segua ogni commit Windows fino al prossimo vero run HPC autorizzato.
- Ogni resoconto specifica **dove** esiste il cambiamento: `WINDOWS_WORKTREE_ONLY`, `FAIR_WORKTREE_ONLY`, `GITHUB_BRANCH_ONLY`, `MERGED_DEV_BRANCH`, oppure `EVIDENCE_LFS`.

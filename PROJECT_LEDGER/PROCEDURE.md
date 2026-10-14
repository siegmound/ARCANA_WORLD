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

## G. Workflow operativo Windows / GitHub / Fair / Windows

Il percorso predefinito per sviluppo e prove Linux è **Windows Codex → GitHub → Fair/Conda → Windows/ledger**. Prima di proporre comandi Fair, leggere questa sezione e verificare il branch/commit e l'ambiente effettivi.

### G1. Windows — sviluppo e autorità del codice
- Codex opera sul PC Windows nel repository di sviluppo. Legge la bitacora, prepara modifiche, test e documentazione; ogni patch viene revisionata e sottoposta ai test pertinenti prima del commit.
- Commit e push del codice di sviluppo avvengono da Windows, con staging per percorsi espliciti; non usare `git add -A` o `git add .`.
- Prima del push verificare branch, HEAD, parent, membership del commit, `git diff --check`, SHA dei file e HEAD remoto. Il push deve essere fast-forward rispetto al remoto verificato.
- Se MSYS segnala un errore durante `git commit`, controllare `git cat-file`, log e stato per determinare se l'oggetto/commit esiste già; non ripetere ciecamente il commit.
- Non usare reset hard, force push o eliminare output preesistenti per risolvere divergenze. Fermarsi e riconciliare in modo esplicito.

### G2. GitHub — trasporto versionato
- Il trasporto ordinario di sorgenti e test Windows→Fair usa GitHub e un commit preciso. SFTP o copie manuali non sono il percorso ordinario; sono ammesse solo per evidenze esterne specifiche o un'eccezione motivata e tracciata.
- Tenere distinti il branch del codice e il branch evidence. Non includere archivi di evidenza voluminosi nel branch del codice quando il contratto richiede storage esterno o Git LFS.
- Prima di ogni trasferimento verificare la destinazione e l'identità del commit. Per aggiornare Windows usare fetch e solo fast-forward/merge sicuri dopo avere esaminato untracked e collisioni; non sovrascrivere output.

### G3. Fair — worktree Linux separato
- Operatore: `jlpfritas`. Worktree di sviluppo/test: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV`. Non alterare checkout storici per i test N2B.
- Per ricevere codice: ispezionare prima worktree e file presenti; `git fetch origin r6/si1-bandwidth-f2av`; verificare lo SHA effettivamente recuperato; solo se sicuro usare `git switch --detach <SHA_VERIFICATO>`. Non fare merge fra branch storici divergenti, reset hard o pull non controllati.
- **Eccezione lane INT3-ENG10K (richiede branch attivo):** il provider audit lega
  l'identità sorgente al nome del branch attivo. Usare una clone directory nuova
  per questa lane, recuperare e ispezionare `origin/r6/si1-bandwidth-f2av`, poi
  raggiungere il full SHA revisionato soltanto con fast-forward verificato,
  mantenendo attivo il branch locale `r6/si1-bandwidth-f2av`. Prima del provider
  preflight richiedere status pulito, branch esatto e HEAD esatto. Non alterare
  worktree Fair esistenti e non usare reset, clean o aggiornamenti forzati.
  L'eccezione mantiene sia il controllo branch del provider sia il controllo
  esatto del full HEAD del runner.
- Codex non è installato su Fair: il lavoro di review e modifica del ledger resta su Windows.

### G4. Ambiente Python Conda su Fair
- Ambiente predisposto: Miniforge in `$HOME/miniforge3`, nome `arcana-r6-linux`. Attivazione per la sessione:
  ```bash
  source "$HOME/miniforge3/etc/profile.d/conda.sh"
  conda activate arcana-r6-linux
  export PYTHONNOUSERSITE=1
  ```
- Verificare di nuovo ambiente, Python e dipendenze in ogni sessione; eseguire i test con `python -m pytest`. Non affidarsi implicitamente a `/usr/bin/python3`, che può non avere pytest.
- Non creare un nuovo venv, installare pacchetti pip/Conda o ricreare l'ambiente prima di aver verificato quello esistente e ottenuto l'autorizzazione pertinente.

### G5. Compilatori e flag
- Evidenze riportate per Fair: GNU Fortran 13.3.0 (`/usr/bin/gfortran`) e NVFORTRAN 25.11-0. Rilevare versione e disponibilità nell'ambiente della prova; non trattare questi dati storici come verifica automatica della sessione corrente.
- Usare flag specifici del compilatore. N2B GNU: `-std=f2008 -O0 -fno-fast-math -fcheck=all`. NVFORTRAN: `-O0 -Kieee -Mnodaz -Mnoflushz -Mbounds`. Non passare flag GNU a NVFORTRAN.
- Risultati sintetici Fair riportati dall’operatore: N2B ha fixture cross-language runtime con GNU Fortran e NVFORTRAN; N2C-W1 ha writer-fixture runtime con entrambe le toolchain (25 passed ciascuna sul commit `7a4119112a16e32c8cbdae5248ebd91f4020a458`). Gli SHA dei log N2C-W1 sono registrati nel ledger come riferiti dall’operatore, non ricalcolati su Windows. La precedente attestazione NVFORTRAN compile-only resta distinta e storica. Ogni risultato è specifico per toolchain e fixture: compile non equivale a runtime, GNU non implica NVFORTRAN, e nessuna prova sintetica qualifica ShellSet SI1 o autorizza Solver.

### G6. Evidenze Fair e ritorno a Windows
- Conservare gli output secondo il contratto, normalmente fuori dal worktree in `$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE`. Registrare commit testato, toolchain, comando, exit code, risultato, percorso e SHA256 dei byte acquisiti.
- L'operatore riporta log e risultati alla chat. Windows verifica ciò che è effettivamente disponibile localmente, distinguendo dichiarazioni dell'operatore da hash ricalcolati, aggiorna la bitacora, rivede e committa; il push del branch codice è eseguito da Windows. Fair fa fetch solo quando serve un successivo lavoro Linux.
- Se un'evidenza risiede soltanto su Fair, non dichiarare che Windows l'abbia autonomamente ricalcolata. Conservare separati hash riportati, hash verificati localmente e provenance.

### G7. Sicurezza della shell interattiva
- In sessioni Fair interattive evitare blocchi incollati con `set -e`/`exit 1` indiscriminati che possono terminare la sessione SSH. Preferire controlli espliciti degli exit code e diagnostici non distruttivi.
- Non usare `git clean`, reset hard o rimozioni di directory senza autorizzazione esplicita e verifica del target.

### G8. Etichette di provenienza e autorità
- Ogni resoconto specifica dove esiste il risultato: `WINDOWS_WORKTREE_ONLY`, `GITHUB_BRANCH`, `FAIR_WORKTREE`, `FAIR_EXTERNAL_EVIDENCE` o `EVIDENCE_LFS`.
- Una fixture sintetica non qualifica ShellSet SI1. Un compile PASS non è runtime PASS. Un runtime PASS non autorizza di per sé Solver, mechanics o pubblicazione canonica.
- Non fissare qui SHA storici come se fossero HEAD corrente; registrare gli SHA specifici nel ledger del gate e nelle evidenze pertinenti.

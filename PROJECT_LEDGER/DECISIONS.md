# Decisioni stabili e limiti di autorità
Questo registro contiene **decisioni architetturali del progetto e governance operativa**, non nuovi seals scientifici. Aggiungere nuove decisioni numerate invece di cambiare retroattivamente il significato delle vecchie.

- **D-001:** R6 genera una storia indipendente. R3/R4/R5 sono legacy/esperimenti iniziali, non target/anchor da riprodurre. Riuso degli algoritmi solo con verifica.
- **D-002:** ARCANA è orchestrator + owner dello stato canonico; gli strumenti esterni sono provider vincolati dal proprio contratto. La capacità di eseguire un provider non equivale all'autorità scientifica.
- **D-003:** Finestre temporali candidate e passo interno adattivo; nessun `dt` globale fisso imposto. Conservazione degli stati determinata dai cambiamenti e dalla ricostruibilità; `EVENT_ONLY` ammesso.
- **D-004:** UNKNOWN non viene trasformato in dato noto, assenza di evento o valore interpolato. Raffinare è lecito solo se la lacuna è di risoluzione/errore, non di fisica/autorità.
- **D-005:** Source hashes, manifest, decisioni fallite e evidenze passate immutabili; ogni recovery ha nuova identità e non riscrive `BLOCKED`.
- **D-006:** In assenza di specifico permesso, nessuna esecuzione Solver/mechanics/evolution/promotion canonica. Runner diagnostici devono fermarsi prima del Solver, se quello è il contratto.
- **D-007:** Le capacità ShellSet parallel/upstream già provate sono acquisizione nel proprio scope. F2A-V caratterizza un problema differente (matrice globale ARCANA SI1), non riedita la qualifica MPI stock.
- **D-008:** Il ledger è l'unico punto operativo di continuità tra chat. Altri README/stati vecchi possono essere pointer/history e non sovrascrivere `STATUS.md`. In presenza di conflitto, prevalgono le fonti primarie e si richiede riconciliazione.
- **D-009:** Cleanup solo con inventory/consumer/hash/license/authority/replay audit, regressioni e Git reversibility; `REVIEW_UNKNOWN` protetto.
- **D-010:** La completezza degli obiettivi (risorse, Deep, flora, fauna, popoli) resta parte del piano; non ridurre ARCANA al solo motore tettonico.

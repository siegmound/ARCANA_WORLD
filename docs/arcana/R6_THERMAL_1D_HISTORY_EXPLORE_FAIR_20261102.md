# THERMAL 1D HISTORY EXPLORE — stato completo e cronologia interrogabile

2026-11-02. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`THERMAL_1D_HISTORY_EXPLORE=PASS_SHORT_COMPLETE_STATE_CAUSAL_ARCHIVE`

Consegnato un archivio reale di C028 con **5snapshot a0/2,5/5/7,5/10anni**.
Traiettoria diretta, ripresa locale e ripresa in processo separato producono
stati completi e SHA di tutti gli snapshot **identici bit per bit**. Le ricerche
restituiscono solo nodi e istanti effettivamente conservati. Questo è un prototipo
sperimentale, non un sistema B0/CAS o una validazione geologica globale.

## Configurazione fisica e stato persistito

Nuovo namespace `experiments/thermal_1d_history_v1`; v1/v2 termici, provider e R1
immutati. PRE autoriale R091/C028, Moho28km, base80km; materiali/radiogenesi e
Dirichlet280/1671,771417700828K originali. Riutilizzata la geometria545nodi della
seconda iterazione, con2m nei primi/ultimi256m e restante supporto289nodi.
Lo stato iniziale viene dal medesimo profilo PRE salvato, senza nuove osservazioni.
Nessuna deformazione o nuova forzante.564Eulerpassi su10anni,
dt559531,914893617s, rapporto dt/CFL0,249791; il CFL non è modificato.

Ogni snapshot contiene:

- temperature **hi e correction**, profondità, bordi/volumi duali per superficie
  unitaria, capacità, sorgenti integrate e materiali k/rho/Cp/A;
- Moho, condizioni Dirichlet, campo iniziale e identità sorgenti/input/runtime;
- flussi allo stato corrente e flussi usati nell'ultimo passo, distinti nel tempo;
- clock, piano dt/orizzonte, contatore, limite CFL e ledger di tutti i passi accettati;
- SHA del precedente snapshot, duplicato nell'indice causale verificabile.

Lo snapshot è fisicamente completo per la ripresa senza cache geometrico esterno;
il lettore richiede comunque codice/runtime compatibili e un contesto atteso con
SHA esterno (`JOB.json`). Il JSON conserva esattamente i float binary64 nel runtime
provato. I temporanei longdouble non diventano uno stato binario opaco da ripristinare.

Accumulazione Kahan: temperatura fisica=hi−correction. Entrambe le componenti
sono essenziali,543nodi hanno correzione non nulla. La correzione opera soltanto
sull'accumulo; nessun clipping delle temperature, rinormalizzazione energetica o
modifica dei coefficienti. I flussi condivisi usano le differenze compensate.
Confronto con il riferimento semidiscreto già conservato: Linf temporale
8,47883e-9K contro8,47866e-9K del precedente accumulo semplice sullo stesso piano.
Il nuovo collegamento non ripete le campagne spaziali già concluse; mantiene i
loro limiti di risoluzione locale e la scala di errore Euler misurata.

## Restart, identità e cronologia

Ripresa al passo282,5anni, poi altri282passi. Stesso calendario di snapshot e
dt fisso: non viene ridefinito il passo per il solo tratto residuo. Confronto
completo include hi/correction, geometria, materiali, flussi, clock, ledger e
collegamenti causali, non solo la temperatura finale. Passano sia restore nello
stesso processo sia continuazione da un figlio Python nuovo. Tutti i5SHA coincidono.

Rifiutati7casi: byte corrotti, sorgente incompatibile, geometria alterata, bordo
incompatibile, clock incoerente, correzione assente e coda di snapshot non indicizzata.
Per source/geometry/bordo viene anche ricalcolato lo SHA del file alterato: il
rifiuto dipende dall'identità/consistenza, non solo dal vecchio checksum. Non è
una prova di sicurezza contro la sostituzione di tutti i riferimenti fidati.
La coda non confermata viene conservata e rifiutata, mai adottata o rimossa.

File snapshot esclusivi, fsync del file, poi append+fsync dell'indice. Indice e
contenuto verificano SHA, ordine, colonna, clock e parent. **Non** è una transazione
atomica multipla: mancano CAS, concorrenza, fsync delle directory, qualificazione
da crash/power-loss e ammissione generale di input ostili. Nessuna loro garanzia
è dedotta dal successo di questo restart ordinato.

## Ricerca realmente eseguita

CLI `run.py query`: colonna, anno archiviato e intervallo di profondità. Esempio
eseguito anche in un nuovo processo: C028,anno10,0–8m restituisce i nodi
0/2/4/6/8m, stato `STORED_NODES`, SHA e parent, hi/correction e temperatura visualizzata.
Un anno1 non salvato restituisce `TIME_NOT_ARCHIVED` con gli istanti disponibili;
C029 `COLUMN_NOT_ARCHIVED`;0,1–0,9m `NO_STORED_NODES_IN_INTERVAL`.
**Nessuna interpolazione o ricostruzione è implementata.** Non si inventano nodi
sui bordi dell'intervallo richiesto. La temperatura visualizzata è arrotondata a
binary64; hi/correction restano entrambi disponibili come dati autorevoli.

Evoluzione effettivamente interrogata a8m di profondità:

| Anni di modello | Temperatura K |
| --- | ---: |
|0 |280,271985270057 |
|2,5 |280,271978344970 |
|5 |280,271974165595 |
|7,5 |280,271970888118 |
|10 |280,271968100560 |

`ARCHIVE_USAGE.md` e il README riportano il comando completo con SHA del JOB;
`CLI_QUERY_EXAMPLE.json`, `QUERY_INVOCATION.json` ed `EXAMPLE_EVOLUTION.csv`
conservano risposta, invocazione e serie. I ledger intermedi descrivono scambi
per tutti i passi, ma non sostituiscono temperature non archiviate a quegli istanti.

## Bilancio e costi osservati

Energia evoluta solo nei volumi interni. I mezzi volumi terminali sono serbatoi
Dirichlet fissi, esclusi dall'energia evoluta; la loro variazione di energia è0,
mentre gli scambi col dominio interno sono espliciti e non nulli.

| Integrale su10anni, per m² | J/m² |
| --- | ---: |
| Produzione radiogenica interna |+7396842,667680 |
| Scambio dal serbatoio superiore |−26822306,960045 |
| Scambio dal serbatoio basale |+8188315,498777 |
| Variazione energia interna |−11237148,793588 |

Produzione interna0,02343918W/m², nei serbatoi8,2e-7W/m²; somma0,02344W/m².
La somma dei residui di passo è8,79e-11J/m²; il confronto globale fra variazione
dello stato compensato e scambi integrati dà2,33e-10J/m², entro il budget numerico
cumulativo9,53e-8J/m². Il precedente controllo semplice, realmente già salvato sullo
stesso piano, aveva−9,0267J/m²: non viene rieseguito. Non si parla di conservazione
esatta; i numeri dipendono dall'aritmetica e dal dominio del ledger. Le due riprese
mantengono identici anche questi risultati, senza errore aggiuntivo di accumulo.

Snapshot JSON non compressi:76788B aT0,141901/185546/229236B intermedi,
272777B finale; totale906248B per i5snapshot, più indice. La geometria e i prefissi
ledger sono ripetuti intenzionalmente per semplicità/completa ripresa: questa
ridondanza non è una soluzione di storage scalabile.
Scrittura+fsync degli snapshot successivi circa3,98–4,44ms nella traiettoria diretta,
lettura/restore del checkpoint5anni circa3,9ms. Query CLI comprendente la verifica
dell'intera catena circa26,6ms. I tempi di hash, validazione e I/O hanno scope
distinti; non vanno sommati automaticamente alle misure del kernel.

Processo principale finale:1,70s wall esterno, CPU1,55s user+0,08s system nella
ricevuta esterna, piccoRSS111616KiB=109MiB. Include archivio diretto, due split,
figlio, negativi, letture e serializzazione; CPU esterna include il figlio atteso.
Il figlio launch→fine costa0,2677s, con continuazione interna circa0,1651s;
è già incluso nel wall totale. RSS è un picco per processo, non una misura della
somma simultanea dell'albero. BLAS/OMP/MKL1thread, nessun limite RAM artificiale.

## Versioni, conservazione e prossimo passo

run01 completa il primo prototipo con parent nell'indice. run02 ripete tutta la
prova sulla versione finale che incorpora anche il parent in ogni snapshot:
nessuna modifica della fisica e nessun risultato mescolato tra versioni.
Entrambi i sorgenti, archivi, log e costi sono conservati. La query CLI finale è
un'operazione di sola lettura. Nuovi file in namespace/evidenze esclusive;
343pin validati, sorgenti package, termica v1/v2 e input precedenti sono ricontrollati.
Provider/R1 e archivi sigillati rimangono invariati. No commit/push o1000Y/10k/100k.

Prossimo passo utile: collegare questi record a un controller ARCANA sperimentale,
con test brevi di ordinamento/pubblicazione e budget di memoria. Prima di una
cronologia durevole servono regole esplicite per crash, segmenti e riferimenti;
prima di nuovi scenari fisici restano i vincoli di materiali, bordi e risoluzione.
Nessun B0/CAS di produzione, accoppiamento planetario o qualificazione scientifica
è sviluppato o autorizzato automaticamente da questa chiusura.

Evidenza: `ARCANA_WORLD_EVIDENCE/R6/THERMAL_1D_HISTORY_EXPLORE_20261102_01`;
archivio finale interrogabile `run02/direct`, contesto `run02/JOB.json`.

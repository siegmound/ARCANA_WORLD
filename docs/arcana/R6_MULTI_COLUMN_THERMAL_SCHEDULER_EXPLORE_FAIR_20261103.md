# MULTI-COLUMN THERMAL SCHEDULER EXPLORE — epoche condivise logiche

Sessione aperta2026-11-02; chiusura documentale2026-11-03, Europe/Rome.
La radice20261102_01 è conservata senza rinominarla.

`MULTI_COLUMN_THERMAL_SCHEDULER_EXPLORE=PASS_LOGICAL_SHARED_EPOCHS_AND_RECONCILED_RESTART`

**Scheduler realmente eseguito su C028 e C139**, con5e48epoche entro10anni.
Interruzione fra le due pubblicazioni riconciliata da un processo separato:
nessun duplicato, nessuna epoca incompleta esposta come disponibile, identità
complete riprodotte. Coordinamento **logico**, non atomicità fra gli store.

## Implementazione riusata e piano

Namespace isolato `experiments/multi_column_thermal_v1`. Riusa DenseController,
IndexedSession/ReadSession, kernel termico compensato e HistoryStore invariati.
Il registro delle epoche è un'altra istanza del backend R6 esistente, non un
nuovo backend. Contiene DomainStateEnvelope e HistoricalSnapshot con riferimenti
agli stati delle due colonne, hash nativi, history/branch/static/source e parent.

C028: Moho28km/base80km,280/1671,7714K ai bordi. C139:40/200km,
280/1721,7544K. Materiali, profili PRE, geometrie545nodi con2m ai bordi e sorgenti
originali preservati. Nessuno scambio termico laterale. Bilanci energetici separati
per colonna; non viene inventato un dominio energetico comune.

Riferimento principale: **passo accettato intero**. Entrambe eseguono564passi,
dt559531,914893617s fino10anni. Il controller avanza sequenzialmente ciascuna
colonna fino al prossimo confine comune; i substep interni restano quelli del
kernel. Non è un'integrazione fisica accoppiata o una barriera distribuita a ogni
substep. Calendari di pubblicazione:0/141/282/423/564 oppure0/12/…/564. Fisica,
frequenza degli snapshot e selezione di query sono risoluzioni distinte.

Il piano verifica identità, supporti, dt/orizzonte/calendario e source policy.
Uno stato di epoca viene registrato solo dopo aver verificato entrambi gli stati
committed, contenuto dinamico/ledger, clock e hash nativo. Il registro ha parent
ordinati e ID deterministici. **I due commit delle colonne e quello del registro
sono tre operazioni distinte:** nessuna transazione atomica cross-store dichiarata.

## Interruzione e riconciliazione realmente provate

Interruzione controllata dopo C028, prima di C139, al passo282per5epoche e288per48.
In quel momento la prima colonna ha una pubblicazione in più della seconda.
La query C028 restituisce lo stato realmente salvato con shared_epoch_published=false;
la query coordinata restituisce EPOCH_INCOMPLETE, senza presentare una coppia completa.

Il nuovo processo riapre il piano, verifica le epoche esistenti, ripristina ciascun
controller e ammette al massimo una successiva epoca parzialmente pubblicata.
Riusa esattamente **una pubblicazione già presente** in entrambi i casi, avanza
solo la colonna mancante e registra poi l'epoca. Non elimina né ripubblica il primo
stato. Requisiti di idempotenza provati anche richiamando run su una storia completa:
nessun nuovo stato; register_epoch su un'epoca valida risponde ALREADY_AVAILABLE.
La pubblicazione duplicata di colonna viene invece rifiutata dal suo controller.

Diretta e ripresa: tutti gli ID delle colonne, tutti gli ID di epoca e gli stati
nativi completi coincidono, incluse hi/correction, flussi, clock e ledger. Audit
offline212stati nativi e53coppie di epoche diretta/ripresa, senza nuova evoluzione.
La diversa retention5/48mantiene le proprie identità e parent, non viene confusa
con una divergenza della fisica.

Read-view: un lettore aperto nella pausa resta sulla vista incompleta anche dopo
che il figlio termina. Dopo refresh vede l'epoca completa. Il reader usa istanze di
store separate da quelle del writer, evitando che la sua vista fissata limiti le
letture operative del writer. Registro e colonne sono pinnati separatamente;
la combinazione è verificata tramite riferimenti immutabili, non un pin atomico globale.

## Query e budget aggregato

API per colonna+passo archiviato+intervallo di profondità, oltre a query_epoch.
CLI coordinata realmente eseguita al passo288, circa5,10638anni:

| Stato effettivamente salvato, profondità8m | Temperatura K |
| --- | ---: |
| C028 |280,271974012252 |
| C139 |280,143992223637 |

Risposta AVAILABLE con ID dell'epoca, due ID di stato e coordinamento
LOGICAL_NOT_CROSS_STORE_ATOMIC. Eseguita anche la query C028 al passo564 per
27900–28100m: restituisce il nodo Moho realmente presente, senza interpolare.
Tempi o passi non archiviati non producono stati ricostruiti automaticamente.
Comando e risposte in QUERY_INVOCATION/FINAL_QUERY_CLI/FINAL_QUERY_API e README.

Budget aggregato dei buffer prefissi:768KiB=786432B, diviso deterministicamente
in393216B per colonna. Ogni sessione usa la LRU V3; le quote non vengono prestate.
Addebito finale complessivo547060B; somma conservativa dei picchi per-colonna
773424B, non necessariamente simultanei, entro il limite globale. Riducendo il
totale a384KiB le quote scendono a192KiB: stato finale troppo grande, fallback
corretto e addebito complessivo390818B su48epoche, entro393216B. Nessuna perdita
di identità o precisione per far entrare gli stati.

Come in V3, questo budget riguarda i buffer ammessi, chiavi e contenitore LRU:
statici, indici, cache metadata dei controller, stati attivi, diagnostica,
temporanei e risultati del chiamante sono esclusi. **Non è un limite all'intero
RSS**. Il controllo aggregato evita quote prefissi indipendenti illimitate;
il resto della memoria è osservato nella misura di processo.

## Costi misurati

Cold=cache applicativa vuota, non disco freddo; carico/OS cache non controllati.
Tre query calde, mediana, sulle due colonne insieme. Tempi di apertura separati.

| Servizio |5epoche |48epoche |
| --- | ---: | ---: |
| Esecuzione diretta due colonne + registro |1,756s |13,000s |
| Tempo totale preparazione/pubblicazione colonne |1,354s |8,527s |
| Registrazione delle epoche, totale |0,401s |4,472s |
| Restore/riconciliazione nella pausa |0,214s |1,751s |
| Figlio launch→fine |1,417s |9,523s |
| Apertura reader coordinato |6,73ms |22,44ms |
| Query coordinata cold |229,28ms |1668,88ms |
| Query coordinata warm |12,89ms |14,40ms |
| Spazio logico completo, due colonne+registro+piano |918594B |5709290B |
| Allocato/file |1105920B /63 |6938624B /450 |

Il registro pesa20558/357322B logici; i due archivi di colonna restano separati.
Le fasi colonne/registro coprono il wall diretto e non sono sommate di nuovo al
totale della campagna. Il figlio e le query sono già inclusi nel wall complessivo.

Campagna finale51,89s wall esterno, CPU41,95s user+0,64s system (figli inclusi),
piccoRSS76800KiB=75MiB. Include dirette/split, negativi, query e confronti, non il
solo scheduler in produzione. Massimo per processo, non somma RSS simultanea
dell'albero; BLAS/OMP/MKL1thread. Nessuna quota RAM artificiale o installazione.

Dodici negativi rifiutati: epoca incompleta, epoca fuori ordine e colonna duplicata
in ciascuno dei due piani; budget aggregato negativo, PLAN SHA errato, registro
corrotto a cache calda, stato di colonna corrotto a cache calda, riferimento
spaziale incompatibile e dt comune incompatibile. Nessuna epoca viene aggiunta
nei tentativi incompleti/fuori ordine. Il primo avvio run01 si ferma prima di
qualsiasi passo fisico per directory padre mancante; sorgente/log conservati.
Corretto soltanto il setup. Tutti i risultati sopra sono della versione run02,
nessuna modifica o retry del solver e nessun risultato mescolato fra versioni.

## Limiti e prossimo miglioramento utile

La riconciliazione copre un'interruzione controllata con un commit di colonna già
concluso, non SIGKILL/power-loss nel mezzo del backend. La disponibilità condivisa
è logica e verificata, non una garanzia di simultaneità dei tre store.

Costi rimasti concreti: cold query48≈1,67s e registrazione4,47s su48epoche;
la ricostruzione dei prefissi e le verifiche ripetute del registro dominano sul
lavoro termico breve. Il prossimo miglioramento utile è una testa del registro
verificata e un refresh incrementale dei prefissi comuni, prima di aumentare molto
il numero di colonne. Nessun nuovo backend è necessario per quel seguito.

Lo scheduler è idoneo a ulteriori esperimenti coordinati piccoli; non è una
qualifica scientifica, distribuita o planetaria. Originali, solver, provider,
R1 e archivi precedenti preservati; nessun1000Y/10k/100k, commit/push o B0di
produzione. Nuova evidenza: `MULTI_COLUMN_THERMAL_SCHEDULER_20261102_01` sotto
ARCANA_WORLD_EVIDENCE/R6. Storie finali in run02/5 e run02/48, query e catalogo
SHARED_EPOCHS_AND_COLUMNS.csv realmente verificati; manifest/finalizzazione separati.

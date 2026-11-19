# THERMAL CONTROLLER EXPLORE V2 — cache di sessione e seconda colonna

2026-11-02. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`THERMAL_CONTROLLER_EXPLORE_V2=PASS_PINNED_CACHE_AND_TWO_SEPARATE_COLUMNS`

Cache utile sulle letture ripetute; seconda cronologia fisica R013/C139 realmente
pubblicata e ripresa. C028 mantiene tutti i5identificativi e gli stati precedenti.
Nessun nuovo backend, metodo termico, gate formale o accoppiamento laterale.

## Read-view e integrità

Nuovo namespace `experiments/thermal_controller_v2`. Riusa direttamente
`HistoryStore.read_view()` e le API R6 già integrate. `ReadSession` fissa una
read-view per tutta la sessione e conserva statici, record immutabili e prefissi
nativi già verificati. Il contesto comprende radice, view_id, SHA statico e binding
di sorgenti; nessuna cache è condivisa con altri controller o mantenuta dopo close.
I risultati di restore sono copie staccate: modificarli non altera la cache.

Il controllo leggero usa identità dei file e metadata locali
(device/inode/dimensione/mtime/ctime). Una modifica rilevata invalida record e
prefissi e torna alla verifica completa; gli statici vengono riautenticati.
Se cambia il file di codice sorvegliato la sessione rifiuta l'uso. Non è un sistema
di autenticazione contro un filesystem ostile; è una cache per input immutabili
nel runtime locale congelato. `force_verify()` elimina i dati derivati e verifica
nuovamente tutto. Nuove sorgenti/configurazioni richiedono un nuovo controller e
sessione. La versione della cache è inoltre legata nel JOB e nelle ricevute;
la sola ottimizzazione delle letture non cambia le identità fisiche C028.

Verifica eseguita: sessione fissata con1stato, pubblicazione del secondo stato da
un writer separato, la sessione continua a vederne1. Dopo `refresh()` cambia view,
cache eliminata e2stati visibili. In produzione non si dovrebbe chiamare refresh
nel mezzo di una singola interrogazione logica.

Rifiutati6negativi pertinenti: record alterato dopo un restore caldo, statico
alterato a cache calda, sorgente incompatibile, doppia pubblicazione, clock
incoerente e salto di snapshot. I primi due dimostrano che una cache popolata non
nasconde l'alterazione. Restano corretti TIME_NOT_ARCHIVED e intervallo privo di
nodi. Il fallback completo e la modifica di una copia restituita conservano lo
stesso stato autorevole. Nessuna vecchia suite numerica è ripetuta.

## Letture cold/warm e pubblicazione

Misure su copie nuove dell'archivio esistente: nessuna apertura/scrittura del
backend dentro la radice storica sigillata. Cold significa **cache applicativa
vuota**, non disco fisicamente freddo; cache OS e carico della macchina non
controllati. Query a10anni/0–8m e restore dello stato finale, stessi dati/controlli.
Tre sessioni,5coppie di letture calde per sessione; tabella di mediane senza
strumentazione tracemalloc, apertura di controller/sessione esclusa.

| Servizio | V1 senza cache | V2 cold | V2 warm |
| --- | ---: | ---: | ---: |
| Query |185,58ms |120,33ms |6,46ms |
| Restore completo |106,17ms |115,98ms |2,25ms |

Il restore freddo è leggermente **più lento**, perché popola copie dei prefissi.
Il beneficio è il riuso nella stessa sessione, non un'accelerazione universale.
I risultati delle query coincidono escluso il campo di durata; gli stati completi,
SHA e tutti i5ID C028 rimangono identici. La continuazione C028 da5a10anni nel
figlio restituisce lo stesso stato finale; nessuna traiettoria iniziale viene
rieseguita per il confronto delle sole letture.

Pubblicazione dei cinque stati già prodotti, in due radici nuove V1/V2: ID identici.
L'ultimo publish passa121,10→79,30ms; i5valori sono conservati singolarmente,
non interpretati come benchmark dedicato. Il controller riusa la testa già
validata solo quando la nuova membership della view coincide con quella attesa;
altrimenti torna alla lettura normale. Il backend di transazione resta quello
R6 originale. I tempi includono validazione/freezing/hash/I/O, non solo scrittura.

La prima misura di lettura con cache includeva tracemalloc, mentre la baseline
non lo includeva:419ms cold e18ms warm di quella ricevuta non vengono usati per
il confronto principale. Le misure corrette sopra sono un seguito di sole
letture, non un rilancio delle evoluzioni. Tracemalloc resta utile per la memoria:
picco di allocazioni Python della sessione2622806B≈2,50MiB, non RSS. I cinque
prefissi completi nella cache rappresentano906248B serializzati; è un costo RAM
esplicito. In questo test la sessione trattiene cinque prefissi, non una cache
globale illimitata; close li elimina.

## Seconda colonna: R013/C139

Avviata solo dopo il completamento positivo della prima fase. Record PRE nodo4823,
Moho40km, base200km, Tsuperficie280K e Tbase1721,7544386298682K. q iniziale45mW/m²,
materiali nominali PRE e produzione radiogenica originali. Profilo dai polinomi
PRE già usati in EXPLORE2; il valore polinomiale al bordo coincide qui con il
Dirichlet dichiarato, senza aggiustamento numerico. Non si creano osservazioni
subcellulari o nuove forzanti.

Geometria545nodi con2m nei primi/ultimi256m, contatto esatto a40km e griglia interna
propria della colonna. Stessi10anni/564passi del piano breve, dt/CFL0,249791.
Il kernel compensato precedente è importato e chiamato invariato. Nessuna
interpolazione tra temperature poste a profondità diverse di due colonne.

| Risultato C139 | Misura |
| --- | ---: |
| Snapshot reali |0/2,5/5/7,5/10anni |
| Riscaldamento massimo |6,184935e-6K |
| Errore Linf vs riferimento semidiscreto già conservato |1,32646e-9K |
| Variazione energia interna |+4610968,92885J/m² |
| Produzione radiogenica interna integrata |+11108016,42768J/m² |
| Somma residui ledger |1,17416e-10J/m² |

Bordi fissi e stock termici positivi sono verificati dal kernel a ogni passo;
mezzi volumi Dirichlet e sorgenti dei serbatoi restano distinti dal dominio
energetico interno. Diretta10anni e split5+5con figlio: stato completo e tutti i5ID
identici. Il figlio costa0,539s launch→fine; C0280,492s. Provenienze, history_id,
branch_id, supporto verticale e tutti gli ID delle due colonne sono separati.
Il vecchio adattatore aveva etichette C028 hardcoded: il nuovo `ColumnController`
le generalizza con i dati reali della colonna, riusando le stesse interfacce R6.
Non esiste alcun flusso laterale o legge di accoppiamento introdotta qui.

Query separate realmente eseguite anche via CLI. A8m:

| Colonna | T0 K | T10anni K |
| --- | ---: | ---: |
| C028 |280,271985270057 |280,271968100560 |
| C139 |280,143990462424 |280,143993148485 |

Le cinque query C139 sono conservate; chiedere C028 al suo archivio restituisce
COLUMN_NOT_ARCHIVED. La risoluzione fisica verticale è non uniforme; i snapshot
sono ogni2,5anni; la query restituisce solo nodi/tempi salvati. Nessuna maggiore
risoluzione fisica nasce da cache, frequenza di interrogazione o visualizzazione.

## Spazio, prestazioni e seguito

| Archivio diretto completo | Logico | Allocato | File |
| --- | ---: | ---: | ---: |
| C028 |446965B |507904B |21 |
| C139 |447916B |512000B |21 |

La cache non cambia il formato su disco. Restano uno statico e segmenti ledger;
per il restart servono statico e prefisso causale, non un solo record dinamico.
Il controllo offline ricostruisce20stati (diretti/split di entrambe le colonne)
e verifica parità; i10nativi C028 delle due radici corrispondono ancora ai5stati
storici originali riutilizzati per confronto.

Campagna principale6,66s wall, CPU5,56s user+0,12s system (figli inclusi),
piccoRSS51200KiB=50MiB. Include profiling, pubblicazioni, negativi ed evoluzioni;
non è un benchmark del solo kernel. Letture matched aggiuntive2,23s wall,
CPU2,15+0,05s; non avanzano la fisica. Massimi RSS per processo, non somma
simultanea dell'albero. BLAS/OMP/MKL1thread; nessuna installazione o cap artificiale.

Il limite concreto resta il costo iniziale del restore e la copia di prefissi
completi in RAM. La query calda ancora attraversa i record per selezionare il
tempo: prossimo miglioramento utile un piccolo indice temporale **di sessione**
e una politica limitata di prefissi, mantenendo force_verify e view fissata.
I benefici già misurati giustificano la cache attuale senza un nuovo backend.

Una campagna funzionale completa, nessuna correzione del solver o mix di versioni.
Originali/provider/R1/versioni precedenti e archivi preservati; no storia globale,
B0/CAS di produzione, commit/push o promozione scientifica. Evidenze nuove:
`ARCANA_WORLD_EVIDENCE/R6/THERMAL_CONTROLLER_EXPLORE_V2_20261102_01`:
PHASE1/PHASE2, MATCHED_READ_TIMINGS, TWO_COLUMNS, query CLI e sorgenti sigillati.
Istruzioni in ARCHIVE_USAGE.md e nel README del namespace isolato.

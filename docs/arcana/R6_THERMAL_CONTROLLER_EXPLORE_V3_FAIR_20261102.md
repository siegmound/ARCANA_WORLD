# THERMAL CONTROLLER EXPLORE V3 — indice temporale e cache limitata

2026-11-02. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`THERMAL_CONTROLLER_EXPLORE_V3=PASS_INDEXED_BOUNDED_CACHE_48_STATES`

**Sì: l'infrastruttura è sufficientemente efficiente per iniziare uno scheduler
sperimentale di poche colonne con identità e tempi coordinati.** Il beneficio
misurato riguarda letture calde e memoria dei prefissi; il restore freddo e la
pubblicazione restano costosi. Non è una qualifica per una simulazione planetaria.

## Implementazione e perimetro

Namespace nuovo `experiments/thermal_controller_v3`. Riusa `HistoryStore`,
`ReadSession` V2, controller/publisher R6 e kernel termico compensato invariati.
L'indice deriva dai record R6 `HistoricalSnapshot` della read-view fissata:
verifica identità temporali, colonna, clock, supporto della view e ordine del piano.
Mappe tempo→state_id e state_id→posizione evitano la scansione/deserializzazione
di tutti i corpi dinamici a ogni query. I corpi sono letti attraverso `read_state`
quando occorrono per verificare il prefisso nativo.

I prefissi verificati sono buffer JSON canonici immutabili, non grandi alberi
Python mantenuti per ogni snapshot. Politica LRU deterministica; ammissione con
espulsione preventiva, ritorno al predecessore disponibile o verifica completa
quando necessario. Gli stati restituiti sono decodificati/copie di proprietà del
chiamante. Invalidazione, refresh e force_verify rimangono disponibili; quest'ultimo
verifica tutti i48stati. La stessa sequenza di accessi produce le stesse espulsioni.

Budget predefinito384KiB=393216B: include buffer, chiavi e incremento del contenitore
OrderedDict misurati con sys.getsizeof. **Non** limita l'intero RSS: statici/indice,
contenitore vuoto, contatori/log diagnostici, temporanei e risultati posseduti dal
chiamante sono esclusi e dichiarati. Il limite riguarda i prefissi ammessi;
nessun cap RAM del processo è introdotto. Budget0 disabilita la cache dei prefissi.

## Cronologie realmente prodotte

C028 e C139 restano indipendenti,545nodi ciascuna, geometrie/Moho/base e materiali
PRE originali, stessa conduzione/radiogenesi e stessi bordi.10anni e564passi per
ogni traiettoria. Le5pubblicazioni esistenti sono riutilizzate su copie; le48nuove
sono realmente prodotte ai passi0,12,…564, senza interpolazione. Resume al passo288,
anno5,106382978723404; poi276passi fino10anni, non uno split fittizio a5anni.

La diversa retention ha identità di history/branch/piano esplicite. I suoi ID e
parent causali non devono essere uguali a quelli della storia con5snapshot.
Il confronto esclude **solo** il campo parent nativo di retention: temperature
hi/correction, materiali, geometria, sorgenti, flussi, contatori e ledger finali
sono identici. Dentro ciascun piano denso, diretta e figlio coincidono integralmente
in tutti i48ID e stati. Audit offline su192stati (48×diretta/split×2colonne), senza
nuova evoluzione. ID, supporti e proprietà delle due colonne rimangono disgiunti.

Read-view verificata anche durante la pubblicazione: il lettore fissato aT0 vede
ancora1stato dopo il secondo commit; refresh invalida e rende visibili2stati.
Query intermedia realmente eseguita via CLI a5,106382978723404anni per entrambe
le colonne.2,5anni restituisce TIME_NOT_ARCHIVED nella storia densa; intervalli
senza nodi e colonna estranea sono segnalati, senza interpolazione.

## Prestazioni delle letture

Cache applicativa fredda, **non disco freddo**; cache OS/carico non controllati.
Tre letture calde per caso, senza tracemalloc. V2/V3 interrogano gli stessi stati;
risultati e native restaurati coincidono. Tempi in ms, warm=mediana.

| Colonna/stati | Query warm V2 | Query warm V3 | Restore warm V3 | Restore cold V3, indice incluso |
| --- | ---: | ---: | ---: | ---: |
| C028/5 |6,25 |2,21 |2,07 |111,16 |
| C028/48 |28,85 |2,68 |2,49 |829,06 |
| C139/5 |6,36 |2,24 |2,09 |110,59 |
| C139/48 |29,10 |2,67 |2,50 |826,54 |

Costruzione indice:0,44–0,48ms su5stati,2,67–2,69ms su48. Query cold dopo indice
C028:110,75ms/825,62ms su5/48stati, contro V2 cold121,66/870,45ms. La ricostruzione
fredda del prefisso resta dominante: l'indice non la elimina. Su tutte le letture
calde con budget384KiB: **zero nuovi corpi dinamici letti**. Restano controlli dei
metadata dei file della view, non una promessa di costo totale O(1) su qualsiasi
archivio. Sono misure EXPLORE nel perimetro5–48stati.

## Budget, espulsioni e memoria

| C028/48, budget | Cache finale addebitata | Espulsioni nel primo caricamento | Query warm |
| --- | ---: | ---: | ---: |
|0 |0B |0 |829,90ms |
|128KiB |127848B |8 |702,47ms |
|384KiB |273139B |47 |2,68ms |
|1MiB |807879B |45 |2,67ms |

Con128KiB lo stato finale non entra: ammissione saltata e fallback corretto,
nessuna perdita di dati o stato parziale. Con384KiB il picco addebitato è385986B
per C028 e387438B per C139, sempre sotto393216B. Rimane un prefisso finale;
1MiB ne conserva3ma non migliora la query ripetuta dello stato finale in questo
workload.384KiB è quindi sufficiente per questo accesso, non un valore universale.

V2 conserva prefissi il cui contenuto serializzato cresce0,906→8,877MB per C028
passando5→48stati; V3 mantiene buffer ammessi entro il budget. Non è un rapporto
fra RSS, perché le rappresentazioni Python differiscono. Indice serializzato:
1601→16399B; statici53378B per C028 e53653B per C139, fuori dal budget prefissi.
Il totale di più sessioni/colonne richiederà un budget aggregato nello scheduler.

## Pubblicazione, spazio e integrità

Pubblicazioni a5stati riprovate nello stesso ambiente su stati già realmente
prodotti, **senza avanzare di nuovo la fisica**. Medesimo backend/publisher.

| Colonna | Publish5 totale/mediano | Publish48 totale/mediano | Spazio logico5→48 |
| --- | --- | --- | --- |
| C028 |0,340s /63,6ms |2,824s /54,3ms |446965→2667650B |
| C139 |0,347s /70,2ms |3,139s /57,5ms |447916→2680726B |

Allocato48stati:3108864B per colonna;150file contro21a5stati. La crescita comprende
stati dinamici, snapshot temporali e read-view del backend già esistente. Il ledger
rimane segmentato, senza duplicare il prefisso fisico su disco. Il maggior numero
di commit aumenta il costo totale: la cache delle letture non lo cancella.

Rifiutati7negativi: budget negativo, corpo dinamico corrotto dopo cache calda,
metadata temporale corrotto dopo indicizzazione, riferimento statico errato,
sorgente/policy incompatibile, doppia pubblicazione e clock invalido. I test di
invalidation, view, ordering e fallback conservano gli ID attesi. L'integrità è
quella del runtime locale con riferimenti fidati: nessuna nuova garanzia contro
un attore che sostituisca tutti i riferimenti, né qualifica da crash/concorrenza.

Campagna finale:61,67s wall, CPU55,13s user+0,53s system (figli inclusi), piccoRSS
68064KiB=66,47MiB. Include anche baseline V2 non limitata, confronti con cache0,
pubblicazioni e negativi; non è il RSS isolato della sola V3. Tempo interno61,53s
sovrapposto al totale. BLAS/OMP/MKL1thread; nessuna installazione o quota RAM.

run01 si ferma nell'ultimo negativo perché il driver provava a modificare il clock
di un controller non ancora recover. Codice/output conservati, nessun PASS di quel
tentativo. Nella versione finale il negativo ripristina prima lo stato; l'ammissione
LRU espelle inoltre prima dell'inserimento del nuovo buffer. L'intera campagna
run02 è ripetuta su quella versione; dati numerici e soglie invariati. Risultati
principali solo da run02; la misura publish5 aggiuntiva usa la stessa versione e
nessuna nuova traiettoria. Non si mescolano versioni per produrre un PASS.

## Decisione

**Procedere a uno scheduler sperimentale piccolo**, con mappa colonna→stato/sessione,
budget aggregato, identità separate e ordine su tempi di modello comuni. Entrambe
le colonne qui hanno lo stesso calendario accettato/pubblicato e restano non
accoppiate. Non è implementato o autorizzato automaticamente uno scheduler globale.

Limiti emersi: restore freddo0,83s su48stati, costo cumulativo dei commit e indice/
controlli metadata che crescono con l'archivio. Refresh elimina i prefissi della
vecchia view, quindi il beneficio caldo non va esteso senza misura a un lettore
che refresha continuamente. Il miglioramento successivo utile è riusare in modo
verificato i prefissi comuni durante refresh append-only, o introdurre ancore
native periodiche, senza un nuovo backend. Nessuna ulteriore complessità è aggiunta
qui: l'indice e il limite LRU hanno già benefici misurabili.

Provider, solver termico, R1, versioni precedenti e archivi originali invariati;
no1000Y/10k/100k, simulazione globale, B0di produzione, commit/push o validazione
scientifica. Evidenze: `ARCANA_WORLD_EVIDENCE/R6/THERMAL_CONTROLLER_EXPLORE_V3_20261102_01`.
Istruzioni in ARCHIVE_USAGE.md;192stati verificati in SAVED_STATE_AUDIT e catalogo
CSV, query CLI e benchmark grezzi conservati. Manifest/finalizzazione sigillano la
sola nuova consegna, inclusi il primo tentativo e i suoi limiti.

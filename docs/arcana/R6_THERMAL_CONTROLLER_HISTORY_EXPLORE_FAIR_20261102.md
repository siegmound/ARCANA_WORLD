# THERMAL CONTROLLER HISTORY EXPLORE — cinque stati R6 pubblicati

2026-11-02. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`THERMAL_CONTROLLER_HISTORY_EXPLORE=PASS_EXISTING_R6_INTERFACES_FIVE_STATES`

**Dimostrazione realmente eseguita:** controller termico,5stati R6 pubblicati,
query storica e ripresa da processo separato. Stato completo, identificativi R6 e
flussi/ledger coincidono bit per bit con la traiettoria diretta. Tutti i5hash degli
stati numerici ricostruiti coincidono anche con i precedenti snapshot termici:
nessuna modifica al metodo numerico o ai dati fisici.

## Riuso delle interfacce esistenti

Esaminati `RecoveryController`, `CompactRuntime`, `AnnualUpliftPlan`, pipeline
INT0A e interfacce generiche R6. I primi sono legati alla coppia sintetica/forzante
annuale o a un diverso scenario di shear; non sono un controller generico per C028.
Il nuovo adattatore `experiments/thermal_controller_history_v1` riusa realmente:

- `DomainStateEnvelope`, `TimeSupport`, `SpatialSupport`, identità HistoryId/BranchId;
- `HistoricalSnapshot` e `ProvenanceRecord`, con dati dichiarati model-derived;
- protocollo `DomainExtractor`, `MinimalStateContract` e validazione della retention;
- `HistoryStore.find_states/read_state/read_view/append_transaction` per lettura e
  pubblicazione di stato, provenienza e snapshot temporale.

Non viene creato un secondo store o una nuova implementazione CAS/B0. Il backend
R6 esistente usa già transazioni/read-view: è riutilizzato senza modificarlo in
una radice sperimentale esclusiva, non qualificato qui per la produzione o i crash.
L'adattatore aggiunge solo il ciclo termico start→advance→publish→recover.
Non registra un nuovo engine o un dispatch predefinito.

## Esecuzione e cinque stati

Una colonna PRE autoriale C028,545nodi,2m nei primi/ultimi256m e supporto interno
della precedente289. Geometria/materiali/radiogenesi/Dirichlet originali invariati.
Invocato direttamente `thermal_1d_history_v1/thermal.py`, senza copie o patch del
kernel:564passi su10anni, dt559531,914893617s, dt/CFL0,249791.
Temperatura fisica=hi−correction; entrambe le componenti sono sempre persistite.

| Anni | Passo accettato | Identificativo R6, suffisso | T a8m K |
| --- | ---: | --- | ---: |
|0 |0 |…48df8998d |280,271985270057 |
|2,5 |141 |…a5c2293f |280,271978344970 |
|5 |282 |…28d58299 |280,271974165595 |
|7,5 |423 |…1b82fdd8 |280,271970888118 |
|10 |564 |…5062fe41 |280,271968100560 |

Identificativi completi e parent in `PUBLISHED_STATES.csv`. Cinque record
`DomainStateEnvelope` e cinque `HistoricalSnapshot`, con una provenienza comune.
L'adattatore avanza solo dal precedente stato pubblicato fino al prossimo confine
previsto. Pubblica solo uno stato completo READY, col clock step×dt coerente,
parent corretto e retention verificata. Non salta snapshot né adatta dt sullo split.

Ripresa dopo5anni: ripristino nello stesso processo per verifica, poi continuazione
in un Python figlio nuovo fino10anni. Corrispondono **tutti** gli identificativi
pubblicati e il native completo finale. Il controllo offline ricostruisce tutti
istati delle due traiettorie e ne confronta gli hash con il precedente archivio
termico, senza rieseguire le campagne numeriche già concluse.

Sette negativi del nuovo controller rifiutati prima della pubblicazione: duplicato,
clock incoerente, salto di snapshot, parent stale, temperatura compensata incompleta,
riferimento statico errato e sorgente dell'adattatore errata. Il conteggio dei
record resta invariato dopo ogni rifiuto. La singola radice negativa conserva
solo il suo T0; non entra nella dimostrazione diretta/ripresa.

## Statici, dinamici e query

`STATIC.json` immutabile contiene geometria/volumi duali per unità di superficie,
materiali, capacità, sorgenti, campo iniziale, bordi, piano/CFL e contesto del kernel.
Ogni record R6 dinamico contiene hi/correction, clock/contatori, flussi correnti e
dell'ultimo passo, digest nativo e **solo il nuovo segmento ledger**. Il parent
R6 collega i record; il parent hash collega gli stati numerici completi. Il
ripristino autentica statici e ricompone i segmenti in ordine, poi chiama il
validatore nativo originale. Ogni riga ledger compare una sola volta su disco.

Il tradeoff è esplicito: una riga dinamica non basta per il restart; occorrono
il suo statico e il prefisso causale dei segmenti. In memoria il kernel mantiene
ancora il ledger completo. Il test copre564passi, non una storia estesa.

Query CLI realmente eseguita in un processo separato: C028,10anni,0–8m restituisce
nodi0/2/4/6/8m e il suo state_id, `STORED_NODES`, `interpolated=false`. L'API accetta
colonna,tempo e intervallo di profondità; la CLI seleziona la colonna tramite JOB.
Anno1 restituisce `TIME_NOT_ARCHIVED`;0,1–0,9m restituisce
`NO_STORED_NODES_IN_INTERVAL`. Il lettore non inventa valori fra nodi o snapshot.
`QUERY_HISTORY.json` conserva anche la serie ai cinque tempi; `CLI_QUERY.json`
e `QUERY_INVOCATION.json` conservano il comando separato e la risposta.

Risoluzioni distinte:545nodi fisici non uniformi;564passi numerici;5snapshot
ogni2,5anni; query limitata a tempi e nodi salvati. Nessuna risoluzione visuale
aggiunta. I valori mostrati sono binary64, con hi/correction autorevoli disponibili.

## Energia e misure

Ledger identico al precedente: energia interna−11237148,793588J/m²,
radiogenesi interna+7396842,667680J/m², scambio superiore−26822306,960045J/m²,
basale+8188315,498777J/m². Somma residui8,79e-11J/m², identica dopo ripresa.
I mezzi volumi Dirichlet restano serbatoi esclusi dall'energia evoluta; sorgenti
interne e dei serbatoi sono conservate separatamente negli statici. Non è un
bilancio chiuso o una conservazione esatta in aritmetica reale.

| Servizio/quantità | Misura osservata |
| --- | ---: |
| Statico, una copia |53378B |
| Cinque record dinamici R6 |384183B |
| Archivio diretto completo |446965B logici;507904B allocati;21file |
| Precedenti cinque snapshot completi, senza indice |906248B |
| Righe ledger dinamiche totali |564, prima1410 nei cinque prefissi |
| Pubblicazione completa, validazione+store |45,9–121,0ms |
| Apertura controller e restore a5anni |102,8ms |
| Query separata con ricostruzione/verifica |186,1ms |
| Figlio launch→fine |573,9ms |

Il nuovo totale include metadati/provenienza/read-view; il riferimento vecchio
sopra include solo i cinque snapshot. I domini sono espliciti, non un benchmark
isolato del codec o del filesystem. Nessuna compressione è introdotta.

Campagna unica completata sulla versione congelata:3,88s wall esterno,
CPU3,43s user+0,05s system (figlio incluso), piccoRSS41984KiB=41MiB. Wall interno
3,76s sovrapposto al totale. Il figlio misura39MiB HWM; i massimi per processo
non vengono sommati né presentati come RSS simultanea dell'albero. Le fasi di
advance/publish sono separate in RESULT, ma il publish include verifica, freezing,
hash e I/O: non è il solo tempo della scrittura. BLAS/OMP/MKL a1thread.

## Limite emerso e seguito utile

Con cinque record, i costi di publish crescono da46a121ms; query e restore devono
rileggere/validare più record e ricomporre i segmenti. È il limite concretamente
osservato dell'attuale adattatore. Il miglioramento utile è una sessione di lettura
con read-view fissata e cache degli statici/prefissi già verificati, conservando
identità e fallback di controllo. Non serve cambiare la fisica o rifare test
artificiali. Un successivo ancoraggio periodico completo può limitare la dipendenza
dal prefisso, ma non è implementato qui.

Nessuna nuova prova crash, concorrenza distribuita, qualifica B0 di produzione o
simulazione globale è dedotta da questa campagna. Provider, R1, termica precedente
e tutti gli archivi originali invariati; nessun1000Y/10k/100k, commit/push.
Report, sorgenti, nuova storia, negativi e verifiche sono sigillati in
`ARCANA_WORLD_EVIDENCE/R6/THERMAL_CONTROLLER_HISTORY_EXPLORE_20261102_01`.
Archivio principale `run01/direct`, contesto `run01/JOB.json`; istruzioni
riproducibili in `ARCHIVE_USAGE.md` e README del nuovo namespace.

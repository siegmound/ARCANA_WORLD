# GEO-TEMPORAL THERMAL EXPLORE — query geografiche su cronologie reali

2026-11-03. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`GEO_TEMPORAL_THERMAL_EXPLORE=PASS_OWNER_CELL_BOUND_HISTORY_QUERIES`

**Ricerca regione–epoca–profondità realmente eseguita sulle storie R6 da5 e48epoche.**
Temperature, stati compensati, hash e parent restano quelli già simulati.
Zero nuovi passi fisici o pubblicazioni termiche. Namespace isolato
`experiments/geo_temporal_thermal_v1`; HistoryStore, SpatialSupport, scheduler e
sessioni V3 riusati. Nessun backend nuovo.

## Geografia autentica e limite del binding

`initial_world/grid.py` definisce180×360celle, riga0a sud, colonna0a−180°,
raggio6371000m. PRE_ORBDATA conferma i record32792/4823 e gli owner seguenti.
Le aree originali sono ricontrollate con una formula trigonometrica separata.

| Colonna | Limiti latitudine | Limiti longitudine | Centro della cella lat/lon | Area cella m² |
| --- | --- | --- | --- | ---: |
| R091/C028 |1..2° |−152..−151° |1,5/−151,5° |12359917892,348 |
| R013/C139 |−77..−76° |−41..−40° |−76,5/−40,5° |2886354611,245 |

**Sono coordinate delle celle owner, non coordinate dedotte dei nodi FEG.**
Il contratto PRE dichiara `NUMERICAL_RUNTIME_SUPPORT_ONLY; NOT_CANONICAL_NODE_GEOLOGY`
e owner lessicograficamente primo fra le celle incidenti. Il lettore conserva
questa semantica: posizione subcella UNKNOWN, nessuna temperatura orizzontale
interpolata o uniforme sulla cella. La somma nominale dei footprint è15246,273km²,
0,002989% della sfera; non è un'area termica risolta. Quest'ultima rimane null.
I ledger termici restano per unità di area: non vengono moltiplicati per questi
footprint per inventare energia integrata di cella.

CATALOG.json collega SpatialSupport, record PRE completo, sorgenti e geometria.
Moho/base28/80km per C028 e40/200km per C139, materiali e Dirichlet restano
separati. Origine nominale T0=210Ma; le query usano passi accettati e anni di
modello realmente conservati, non una nuova ricostruzione paleogeografica.

## Query e verifiche

La CLI accetta bbox sud/nord/ovest/est, passo archiviato, processo e profondità.
L'intersezione richiede area positiva; il solo contatto al bordo non seleziona.
Ovest>est attraversa l'antimeridiano: verificati sia selezione positiva di C028
sia una regione di seam priva delle due colonne.

| Esito | Significato verificato |
| --- | --- |
| AVAILABLE | Stati effettivamente conservati di colonne selezionate, epoca condivisa pubblicata |
| NOT_SIMULATED | Nessuna traiettoria catalogata interseca la regione tramite il suo owner |
| UNKNOWN | Processo non presente nel catalogo oppure profondità fuori dal supporto |
| TIME_NOT_ARCHIVED | Passo non conservato nel piano5/48 |
| EPOCH_INCOMPLETE | Epoca pianificata priva di commit condiviso nella read-view |

Intervalli dentro il supporto ma senza nodi restituiscono
`NO_STORED_NODES_IN_INTERVAL`; nessun nodo o istante viene interpolato. Le parti
fuori dal supporto sono indicate esplicitamente. Una risposta mondiale AVAILABLE
contiene soltanto le due colonne e dichiara il resto non simulato orizzontalmente.

Dimostrazione finale a10anni, passo564, profondità8m:

| Colonna | Temperatura visualizzata K |
| --- | ---: |
| C028 |280,27196810056006 |
| C139 |280,14399314848487 |

Ogni risposta conserva hi/correction, nativeSHA, state/history/branchID, parent,
read-view, supporto verticale completo, condizioni fisiche e provenienza R6.
Una nuova CLI Python riproduce la stessa risposta. Gli stati completi restaurati
hanno i nativeSHA originali e ogni byte delle copie5/48 rimane invariato.
La ripresa evolutiva bit-identica resta quella già provata dallo scheduler;
qui non viene ripetuta un'altra traiettoria.

La read-view autentica dell'interruzione a288passi vede solo C028 pubblicata:
query coordinata EPOCH_INCOMPLETE. Cambiare le teste sulle copie non modifica
la vista fissata; il refresh esplicito rende disponibile la coppia originale.
Verificati18controlli funzionali e10negativi: regione/passo/profondità invalidi,
corruzione dinamica e di epoca dopo cache calda, binding geografico incompatibile
anche con nuovo SHA, catalogo e piano errati. Corruzioni iniettate esclusivamente
su copie e poi ripristinate; originali reautenticati.

## Costi osservati

Cache applicativa fredda, non disco freddo; warm=mediana di3query. Tempi ms:

| Piano/selezione | Apertura | Query cold | Query warm |
| --- | ---: | ---: | ---: |
|5/C028 |11,13 |133,82 |23,36 |
|5/C139 |8,00 |132,72 |23,28 |
|5/entrambe |11,63 |263,60 |45,09 |
|48/C028 |29,53 |850,44 |17,91 |
|48/C139 |24,94 |847,70 |17,96 |
|48/entrambe |25,30 |1694,47 |33,97 |

Il filtro evita il restore della colonna non selezionata. I prefissi ammessi
occupano273139/273921B per una colonna,547060B per entrambe, sotto il budget
aggregato786432B. Statici, indice, risposte e temporanei sono esclusi dal budget.
Le risposte complete e le verifiche di provenienza/nativeSHA aggiungono costo
alle query calde rispetto alla precedente query minimale dello scheduler.
Non si attribuisce questa differenza a un'accelerazione del backend.

Campagna finale8,93s wall, CPU8,70s user+0,17s system, piccoRSS115712KiB=113MiB;
include hash/lettura del DAT originale78MB, copie, negativi e CLI figlia.
CLI separata1,014s incluso avvio. Nessun cap RAM; BLAS/OMP/MKL1thread.
Il catalogo è un solo file aggiuntivo; le storie restano918594B/5709290B per5/48.
STORAGE registra dimensioni esatte e allocato. Nessuna pubblicazione termica
rieseguita, dunque nessun beneficio di pubblicazione misurato. La ricostruzione
fredda del prefisso domina ancora: non è aggiunta una nuova cache della testa
o del refresh senza una necessità misurata in questo workload.

## Iterazioni, conservazione e prossimo passo

run01 si ferma sul confronto strettamente identico della base C028: il PRE
serializzato1671,7714177008281K differisce di1ULP dal Dirichlet archiviato
1671,771417700828K. Il nuovo adattatore distingue i due valori, controlla lo
scarto entro1ULP e lo espone; gli SHA di input/statici e il bordo fisico conservato
restano invariati. Nessun parametro del solver viene corretto. run02 completa
la prima campagna; run03 ripete tutto sulla versione finale con aree di selezione
esplicite e copertura termica orizzontale null. Risultati principali solo run03;
un'ulteriore query di sola lettura verifica l'attraversamento positivo della seam.
Tutti i tentativi e sorgenti sono conservati.

591pin preesistenti e2421membri dell'archivio scheduler verificati prima/dopo.
Snapshot del worktree intenzionalmente dirty prima del lavoro; provider, kernel,
R1 e precedenti archivi immutati. SHA/input/versione, query grezze, costi e log
sono sigillati nella nuova evidenza con manifest/finalizzazione separati.
Nessuna simulazione nuova, accoppiamento laterale, B0produzione, commit/push o
promozione scientifica.

**Pronto per esplorare consultazioni spaziali di poche colonne.** Per posizionare
fisicamente i singoli nodi FEG serve un binding geografico ulteriore alla sola
cella owner; per una copertura areale termica servono supporti e dati aggiuntivi.
Il miglioramento infrastrutturale utile resta ridurre il restore freddo con
prefissi comuni verificati o ancore native, mantenendo questo stesso backend.

Evidenza: `ARCANA_WORLD_EVIDENCE/R6/GEO_TEMPORAL_THERMAL_20261103_01`.
Esempi e comandi riproducibili in ARCHIVE_USAGE; archivio finale copiato in
`run03/5` e `run03/48`; query CLI in `run03/CLI_QUERY.json`.

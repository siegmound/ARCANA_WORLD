# FIRST PHYSICAL GEODYNAMICS T0→T1 — EXPLORE

2026-11-03. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`FIRST_PHYSICAL_GEODYNAMICS=BLOCKED_REGIONAL_MECHANICAL_INPUTS`

**Non è stato creato un nuovo T1 geodinamico.** Il percorso minimo scelto è
**ShellSet/SHELLS**, con geometria/cinematica T0 e proprietà PRE già disponibili.
Mancano un caso regionale meccanico completo e il suo aggiornamento transiente;
eseguire Earth5R o il runner INT10K invariato introdurrebbe dati fisici differenti.
ASPECT non è un secondo requisito. Non occorrono FastScape, gFlex, idrologia o Deep
per chiudere questo caso.

## D-024 e lavoro già acquisito

Il DECISIONS locale terminava a D-017. D-024 è stata fornita dall'utente durante
questa richiesta e aggiunta integralmente, senza riscrivere le decisioni precedenti.
Il testo ricevuto e il registro precedente sono conservati nelle nuove evidenze.
La richiesta corrente autorizza un breve EXPLORE se gli input bastano: le vecchie
etichette «non autorizzato» restano storiche e non sono il motivo del blocco.

| Componente | Capacità recuperata dai record originali | Binding fisico ancora distinto |
| --- | --- | --- |
| GPlates/pyGPlates | Mapping T0:12placche,64800facce,1983bordi; i report di risoluzione recuperati riportano runtime indisponibile nel loro contesto | Questi report non dimostrano una risoluzione dinamica pyGPlates ARCANA; non negano altri test specialistici. Il nuovo caso può riusare la geometria/cinematica normalizzata R6 |
| ShellSet/SHELLS |9/9modelli upstream ListEx1; MPI/LAPACK e capacity patch già provati | Esempi Earth; nessun nuovo solve meccanico regionale ARCANA |
| OrbData/PRE | Generalizzazione input e loader; pacchetto64442nodi e consumatori termici S1B implementati | Dati termici/densità non selezionano reologia, trazioni o contatto meccanico |
| ASPECT | Blankenbach già eseguito; traiettoria sintetica con11snapshot | Non un caso fisico ARCANA; resta alternativa se il fenomeno richiederà un continuum volumetrico |
| GEODYN | Archivio ASPECT e confronto11mesh/99campi; ultimo snapshot1,0142299266s, fine solver1,098612289s | Reader/archive; nessuno snapshot inventato a fine solver, restart del caso non disponibile |
| INT10K | Storie3Y/10Y e restart verificati nei bundle FAIR esistenti; patrimonio ingegneristico sintetico preservato | Runner usa operatori ARCANA, reologia benchmark e forcing sintetici; non chiama ShellSet/ASPECT |

CAPABILITIES.json applica separatamente le quattro categorie richieste da D-024.
Sono stati ricalcolati22confrontiSHA su21file storici distinti, tutti coincidenti,
inclusi log/Models ShellSet, qualifica OrbData e8membri dei bundle INT10K3Y/10Y.
Nessun benchmark è ripetuto. Il binario ShellSet attuale ha SHA4c0044fe…27e918,
coincidente col binario della qualifica OrbData storica, diverso dal precedente
binario upstream03e1a3f7…5e349. Non è una prova di compilazione dei consumatori
S1B oggi presenti nel worktree.

## Sottosistema minimo e input effettivamente presenti

Il candidato è una piccola sezione continentale non adiacente a junction, con
la coppia5:11 e i supporti C028/C029 come possibile punto di partenza già
identificato dal lavoro precedente. Le due colonne hanno lo stesso profilo T0;
la loro adiacenza non definisce da sola un contatto o una larghezza deformabile.

Interdipendenza richiesta: profili/materiali → densità e resistenza dipendenti
dalla temperatura → equilibrio Shells e tasso di deformazione → aggiornamento
coerente di geometria, spessori/materiali e, dove necessario, temperatura.
SHELLS linearizza iterativamente la relazione deformazione–reologia; non viene
scritto un nuovo operatore meccanico.

Sono già presenti e autenticati:

- T0 nominale210Ma,12vettori Euler rad/anno nel gauge sintetico no-net-rotation;
- legge autoriale del primo segmento: mantenere i vettori T0 fino al primo
  limite evento/legge. Non è corretto dichiarare assente qualsiasi legge temporale;
- limite condizionale della sola attivazione rift27123,405156anni, che non è
  un limite generale di topologia/contatto né un dt selezionato;
- mesh sferica64442nodi/128880triangoli,193320archi,nessuna faglia esplicita,
  supporti e campi nodali T0; frame runtime `RX_PLUS_0P5_DEG`, da trasformare
  anche per vettori e BC, non soltanto per coordinate;
- PRE e configurazione materiale V1: per C028/C029 Moho28km/base80km,
  crosta k2,5/rho2800/Cp1000/A8e-7 e mantello k3,3/rho3300/Cp1200/A2e-8 nelle
  unità SI già dichiarate. Gravità autoriale9,82m/s²;
- sorgente S1B con valutazione nodale/IP dei profili e proprietà. Il vecchio
  template di input con campi termici null non descrive più questa disponibilità.

La mesh è supporto numerico; l'owner PRE non è una classificazione geologica
fine. Il campo chemical_delta_rho=0 è componente runtime di riferimento,
non prova di omogeneità chimica. Il gauge no-net-rotation non determina moto
astenosferico, trazioni basali o bilancio dei momenti.

## Gap preciso e modifica minima

| Dipendenza | Cosa manca per il caso scelto | Modifica minima |
| --- | --- | --- |
| G1 dominio regionale | Selezione di nodi/elementi, bordi del ritaglio, supporto materiale; se include un'interfaccia, contatto/accomodamento e larghezza fisica pertinente | Un solo sottoinsieme con parentID della FEG esistente e tag di bordo; non assumere larghezza fisica dalla distanza dei centri di cella |
| G2 reologia | Legge e parametri attribuiti ai ruoli crosta/mantello regionali | Una tabella ruolo→legge/parametri con convenzioni ShellSet, fonti o scelte autoriali esplicite e intervalli |
| G3 forze/BC temporali | Vincoli di velocità o traction sul bordo, riferimento, condizioni basali e contatto applicabile | Un file BC regionale con nodi/componenti, conversione m/anno→m/s e rotazione nel frame runtime; legare la legge Euler esistente al breve intervallo locale |
| G4 T0→T1 | Trasporto di mesh, massa/spessori e materiali dalla soluzione meccanica; feedback termico e ledger/restart pertinenti | Un adattatore di aggiornamento sul modello regionale dichiarato, riusando controller/HistoryStore e kernel applicabili |

G2 riguarda, secondo il modello effettivamente scelto, i termini di attrito e
pressione efficace e/o i parametri creep `aCreep,bCreep,cCreep,dCreep,eCreep`.
Attrito di faglia e leggi di subduzione servono solo se tali oggetti sono inclusi;
nessuna classificazione planetaria è richiesta. I valori di iEarth5-049.in sono
un esempio Earth. Le due `.bcs` recuperate nella directory INPUT sono Earth5R,
non vincoli ARCANA. Non vengono posti a zero trazioni o forze mancanti.

Il provider material_rheology dichiara esplicitamente dry-olivine
`NOT_ASSIGNED_TO_R6_MATERIAL_ROLES`; il runner unified imposta, fra gli altri,
opening_rate=0,01m/anno e uplift sintetico. Non sono un binding fisico del nuovo
caso. Il rate Euler è disponibile, ma non seleziona da solo quali nodi vincolare
né il contatto; prescrivere la velocità a ogni nodo eliminerebbe il problema
meccanico da risolvere.

Il sorgente FEM di Shells calcola velocità, strain-rate e stress dopo BuildF,
BuildK, VBCs e Solver. Una soluzione statica a T0 non costituisce un T1. Il
kernel pure-shear esistente è riusabile per G4 soltanto con ipotesi di sezione,
larghezza e deformazione giustificate; non viene imposto per aggirare il gap.
SOURCE_ANCHORS conserva linee, estratti e SHA esatti.

**Il prossimo cambiamento utile è un unico pacchetto di input regionale completo**,
non una nuova catena di gate: dominio/tag, leggi costitutive e parametri, BC/forze
sull'intervallo e regola di aggiornamento. REGIONAL_INPUT_TEMPLATE.json specifica
i campi mancanti come null, con una finestra EXPLORE proposta massima10anni.
Poi: build isolata dei consumatori S1B esistenti, solve regionale, breve avanzamento
e controlli numerici mirati. Non occorre rendere ASPECT o altri domini prerequisiti.

## Tempo, stato e processo alternativo

Il collegamento R6 è già disponibile: DomainStateEnvelope/SpatialSupport,
ForcingRecord, eventi, HistoricalSnapshot, controller e HistoryStore. Il futuro
checkpoint meccanico dovrà conservare anche mesh/materiali aggiornati, stato
costitutivo necessario, BC/forzante e loro validità, clock, ledger e identità
build/config. Gli output diagnostici di velocità o VTU da soli non bastano.
In assenza della soluzione non vengono pubblicati un T1 o un evento fisico vuoto.

Come secondo processo già supportato resta la conduzione/radiogenesi1D regionale:
C028 e C139 hanno effettivamente raggiunto+10anni con sorgenti/bordi autoriali,
ledger e restart già provati. Le temperature archiviate a8m sono rispettivamente
280,27196810056006K e280,14399314848487K. THERMAL_FALLBACK collega gli ID reali;
non è una nuova traiettoria, né deformazione tettonica. Non viene ripetuta una
prova termica superata per chiamarla avanzamento geodinamico.

## Esecuzione e preservazione

Eseguito soltanto il recupero stdlib riproducibile in
`experiments/first_physical_geodynamics_v1/audit.py`:68identità in audit03,
22confronti storici e rehash finale.0,32s wall esterno,0,25s CPU user+0,07s system,
21504KiB=21MiB RSS: costi dell'audit, non di una simulazione.
Due primi tentativi si fermano su literal errati del raccoglitore di source anchor
(Xe, poi width_m); log e sorgenti conservati. Il terzo usa una chiave realmente
presente. Nessuna equazione, soglia o parametro è cambiato; zero lanci dei provider.

594pin e2044membri della precedente consegna geo-temporale preservati; D-024 è
l'unica aggiunta autorizzata al registro delle decisioni. Worktree dirty e
HEAD2c71370… preservati; nuovi namespace/evidenze isolati. Nessuna modifica a
INT10K, provider, R1, Thermal1D o archivi storici; nessuna simulazione lunga,
planetaria, commit/push o promozione scientifica/canonica.

Evidenza: `ARCANA_WORLD_EVIDENCE/R6/FIRST_PHYSICAL_GEODYNAMICS_20261103_01`.
INPUT_READINESS, CAPABILITIES, SOURCE_ANCHORS e REGIONAL_INPUT_TEMPLATE sono i
riferimenti operativi; manifest/finalizzazione sigillano la sola nuova consegna.

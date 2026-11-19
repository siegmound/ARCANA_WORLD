# R1 — primo esperimento fisico: input esaminati, evoluzione non ammessa

2026-11-01. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`R1_FIRST_PHYSICAL=BLOCKED_MISSING_MOBILE_COVER_AND_PHYSICAL_DIFFUSIVITY`

Preparazione e mappatura completate. **Nessun passo fisico eseguito:** nei dati
R6 ispezionati non è presente uno stock di copertura mobile associato a una
diffusività superficiale fisica e a un contesto di substrato/bordo compatibile
con R1. Il PASS numerico ridotto resta valido: il blocco riguarda gli input e il
significato fisico, non un nuovo difetto del solver. Non sono richiesti certificati
formali né un nuovo ciclo di ratifiche per questo audit.

## Dati effettivamente presenti

Letti HR2-P0, catalogo e contratti pertinenti; autenticati nuovamente i payload
originali e ispezionati i valori, senza rigenerarli. Non si pretende che ogni dato
planetario sia assente. Si tratta di **dati di modello autoriale T0**, con epoca
nominale210Ma, non misure osservative della Terra a210Ma.

| Input | Contenuto verificato | Compatibilità fisica con R1 |
| --- | --- | --- |
| Geografia iniziale180×360 |14258quote terrestri finite,25–3309,49m;50542quote oceanicheNaN con supporto assente | Quota rispetto al datum, non spessore mobile |
| Superficie chiusaV2,180×360 |64800quote finite,−6819,28–3309,49m; crosta6500–50000m | Copertura geografica completa, ma grandezza fisica diversa dalla copertura mobile |
| PRE_ORBDATA |64442record,51campi; Tsuperficie280K, flusso0,045–0,47415W/m²; profili/materiali a due strati | Stato termico stratificato; non un campo laterale R1 già pronto |
| E0 C028/C029 | Due colonneT0 a73nodi,0–80km,T280–1671,77K e materiali | Input reali del modello per il provider1D; nessuna copertura superficiale |

I tre payload principali mantengono gli SHA di HR2-P0:
`a6edad24…d5462506c` geografia, `31cf4fb7…fef3534` superficieV2,
`2dc83a75…3d3584` termico. Path, dimensioni e SHA completi dei21input/documenti
letti sono in input_audit/INPUT_IDENTITY.json; header, campi e statistiche in RESULT.
Il confronto aggiuntivo col cache32×16 è in TARGET_AREA_COMPARISON.json. Il primo
interpreter shell di quel controllo opzionale non aveva NumPy e si è fermato
prima del calcolo; il controllo è completato nello stesso ambiente arcana-r6-linux.
Le versioni iniziale eV2 sono distinte: V2 non corregge retroattivamente gli UNKNOWN
originali. Nel materiale storico esiste anche una vecchia docstring che diceva
superficieT0 non disponibile; i payload effettivi e HR2-P0 prevalgono su quel testo.

## Mappatura eseguita, senza inventare stock

Nuovo adattatore isolato `experiments/r1_physical_inputs_v1`, senza import o
chiamate al solver. Origine: righe sud→nord, colonne ovest→est, R=6371000m,
confermati dal contratto della griglia. Destinazione32×16, già verificata
numericamente da R1. Le aree indipendenti dell'adattatore concordano con il cache
R1 entro1,49e-15 relativo; non sono dichiarate identiche bit per bit. Prima di
un effettivo handoff si useranno le aree operative del cache. L'overlap usa le vere aree sferiche in sin(latitudine)/longitudine.
I pixel sorgente sono rappresentati costanti a tratti per questa rimappatura;
non viene attribuita retroattivamente un'accuratezza di media continua ai dati.

- Geografia iniziale: **69celle interamente note,443intersecano UNKNOWN**;
  area nota30,0056796% del pianeta. Le medie di cella intera restanoNaN quando
  esiste anche una sola intersezione UNKNOWN. Medie condizionate e frazioni note
  sono campi separati, non riempimenti dei vuoti.
- V2: **512celle note,0UNKNOWN** secondo la sua maschera originale.
- Residuo relativo dell'integrale discreto area×quota:0 osservato per la prima
  mappa e6,28e-20perV2. È conservazione della rappresentazione numerica della
  quota, **non** volume/massa di sedimento conservati.

Individuata anche una finestra dati4×4completamente supportata, latitudine
−33,75..11,25°, longitudine−112,5..−67,5°. È un'anteprima geografica grossolana:
non è una regione simulata né un rettangolo trasformato artificialmente in sfera.
Un operatore regionale richiede bordi/halo e supporti appropriati, non il wrapping
automatico dei margini. Le maschere d'incertezza progettuale sono conservate.
Test sintetici del solo adattatore verificano integrali, supporto vuoto e UNKNOWN;
nessuna loro grandezza diventa input fisico.

## Gap esatti e processi possibili

**Diffusione della copertura con R1:** servono h0[m] non negativo, origine/epoca,
maschere e uno stock/materiale, più kappa superficiale[m²/anno] con legge e valore
fisico dichiarati. R1 usa un kappa scalare e grad(h); su terreno reale va inoltre
chiarito il ruolo di b e della pendenza grad(b+h). Una quota o uno spessore crostale
non fornisce hmobile. Il vecchio SurfaceConfig usa esplicitamente5m di copertura,
1800kg/m³ e1e6m²/anno **sintetici**: non sono parametri fisici recuperati.
Densità non indispensabile per il solo bilancio di volume; è necessaria se si
vuole interpretare la massa/materiale. Non viene aggiunta come falso requisito
per bloccare un futuro esperimento volumetrico.

**Termica verticale1D:** esistono davvero temperature, k,rho,Cp,A, geometrie e un
provider termico1D, quindi è il processo più vicino a un esperimento separato
su dati di modello. Non è però un esperimento con R1 e non viene eseguito qui in
sostituzione. La superficieT0 è uniforme280K, mentre i gradienti, i flussi e la
produzione radiogenica sono verticali. Per il mantello k=3,3W/(mK),rho=3300kg/m³,
Cp=1200J/(kgK) sono disponibili; la loro diffusività termica non è una diffusività
geomorfologica. Su tutta la sfera manca inoltre un livello orizzontale comune
interno al mantello: maxMoho50km>minLAB17,542km. Trasportare temperature di Moho
poste a profondità diverse non risolve il problema. Per conduzione laterale
servono capacità termica/spessore, bordi e una mappatura energetica: il proprietario
numerico dei nodiFEG non fornisce pesi di volume/area fisica.

**Idrologia/erosione:** mancano forcing acqua/clima, stock, canali, erodibilità e
parametri compatibili; le relative maschere iniziali sono UNKNOWN. **Meccanica,
trasporto di placche e Deep:** sono disponibili geometrie/riferimenti e prototipi
limitati, non una legge globale accoppiata pronta con inventari e forcing. I dati
termici non vengono usati per colmare questi gap. La tabella completa dei processi
è PHYSICAL_PROCESS_READINESS.csv.

## Risultato operativo e conservazione

Conclusione: **nessuna simulazione fisica R1 giustificata dagli input disponibili
nel perimetro ispezionato**. Prossimo lavoro minimo: ottenere/definire uno stock
mobile e la sua diffusività/processo su un supporto reale, quindi collegare
mappatura, pendenza e condizioni al bordo. REQUIRED_PHYSICAL_INPUTS.json conserva
i campi mancanti come null. Non sono stati inventati valori né acquisiti nuovi
dataset. Non viene dichiarata un'assenza universale di dati fuori dal catalogoR6.

Il controllo numerico eseguito riguarda solo lettura/mappatura:0passi fisici,
0import/chiamateR1,0simulazioni termiche/accoppiate. Tempo interno0,892s,
CPUuser0,835s/system0,057s, piccoRSS53604KiB≈52,35MiB; ricevuta esterna in
input_audit.time. Questi costi non sono prestazioni di evoluzione fisica.

Branch `r6/runtime-copy-r1-fair`, HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787`,
worktree preservato.343pin della versione numericamente validata e13archivi
pertinenti autenticati prima/dopo;83file pre-esistenti catturati prima del lavoro.
Tutti gli input originali rimangono byte-identici. Modificati soltanto nuovi
file dell'adattatore, questo report e cinque handoff del ledger. Nessuna modifica
al solver, nuova catena formale,1000Y/10k/100k, commit/push o promozione scientifica.

Evidenze esclusive: `ARCANA_WORLD_EVIDENCE/R6/R1_FIRST_PHYSICAL_INPUTS_20261101_01`:
RESULT/INPUT_IDENTITY originali, mappeNPZ, inventario, gap, sorgenti e manifest.

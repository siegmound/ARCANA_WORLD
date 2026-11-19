# ARCANA R6 — Decisione sul primo modello deformante

2026-11-18, FAIR, D-024. **Proposta per decisione autoriale.**

**`PHYSICAL_DEFORMING_T1=BLOCKED_EXACT_G2_G3_INPUTS`.** Il candidato più
diretto con forcing differenziale documentato è un piccolo transetto
continentale fra le placche 5 e 8, con estensione distribuita di un continuo
SHELLS come ipotesi da approvare. Il solo risultato T1 disponibile rimane
`KINEMATIC_REGIONAL_T1=PASS_PRESCRIBED_KINEMATIC_ONLY`. In questa fase sono
stati ridotti gli input esistenti e letti i sorgenti pertinenti. Zero solve,
avanzamenti, nuove mesh o modifiche alle evidenze originali.

## G2 — Quarzite e olivina come proxy, Diamnd invariato

**Disponibile.** I quattro parent cell candidati sono continentali. Tutti i
nove nodi PRE del transetto hanno supporto continentale omogeneo per classe
termica HOT_EXTENDED, flusso superficiale 0,085 W/m², Moho a 28 km e LAB
termico a 80 km. I profili coincidono con quelli del ritaglio interno.
La crosta va da 280 a 1.051,56 K e il mantello litosferico da 1.051,56 a
1.671,77 K. Una riduzione litostatica con g=9,82 m/s² e la densità termica
lineare S1 dà circa 0,754 GPa al Moho e 2,368 GPa alla LAB, misurati dalla
superficie rocciosa. Queste sono scale di pressione del modello. La pressione
interstiziale, la mineralogia e la fugacità restano sconosciute. La densità
chimica zero del runtime ha autorità di componente di riferimento.
[Materiali PRE](../../R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json) ·
[Autorità densità chimica](../../R6_PRE_ORBDATA_CHEMICAL_DENSITY_MECHANICS_AUTHORITY.md) ·
[Densità runtime S1](../../external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90#L313)

**Proposta.** Usare la legge fragile–viscosa di continuo già implementata e,
se l'autore approva i proxy, prendere come riferimenti la quarzite Black Hill
senza fusione di Gleason–Tullis e il ramo dislocazionale di olivina nominalmente
anidra già codificato come benchmark. La calibrazione crostale ha nominali
n=4 e Q=223±56 kJ/mol, con prove attorno a 1,5 GPa e 900–1100 °C.
La crosta PRE resta sotto la minima temperatura di quelle prove e sotto la
pressione di confinamento sperimentale. Il riferimento non separa un volume
di attivazione crostale o un effetto dell'acqua; «senza fusione» non equivale
a «anidro». Il benchmark di mantello usa n=3,5, E=530 kJ/mol, V=14 cm³/mol
e A=1,1e−16 Pa⁻ⁿ s⁻¹. La misura su olivina nominalmente secca di Dixon–Durham
(V=15±5 cm³/mol) è un controllo di scala di laboratorio, con pressione che
interseca solo il tratto profondo dell'intervallo PRE. Il regime di creep e
l'extrapolazione a tassi geologici vanno verificati. PRE non ne determina i
coefficienti. L'unica alternativa proposta è il fit quarzitico con fugacità
esplicita di Hirth–Teyssier–Dunlap, utile se viene assegnato un profilo d'acqua.
Nella legge invariata un fattore di fugacità costante può entrare nel prefattore.
Una fugacità variabile richiede una riduzione motivata e un errore quantificato.
[Prove su quarzite](https://www.sciencedirect.com/science/article/pii/004019519500011B) ·
[Benchmark locale di olivina](../../src/arcana_worldsim/r6/material_rheology_provider.py) ·
[Misura di V in olivina](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2018JB015853) ·
[Fit con fugacità](https://experts.umn.edu/en/publications/an-evaluation-of-quartzite-flow-laws-based-on-comparisons-between/)

**Traduzione nel solutore.** Dal codice, e₃=−(e₁+e₂) e
J₂(D)=½D:D. Il ramo dislocazionale prima dei limiti usa
`η=½ a (2√J₂(D))^(e−1) exp[(b+c z)/T]` e `s=2ηD`. Quindi
`√J₂(s)=½ a (2√J₂(D))^e exp[(b+c z)/T]`. Gli output integrati
orizzontali di `Diamnd` sono relativi alla componente verticale, in Pa·m.
Per una legge di laboratorio in compressione triassiale espressa con
modulo del tasso assiale ε e stress differenziale Δσ,
`2√J₂(D)=√3 ε` e `√J₂(s)=Δσ/√3`. Con
`ε=A (Δσ)^n exp[−(E+PV)/(RT)]`, il prefattore corrispondente è
`a=2 A^(−e) / 3^((1+e)/2)`, con e=1/n, dopo la conversione del
prefattore a Pa e s. Questa conversione vale per la convenzione dichiarata.
Per leggi già espresse in invarianti occorre usare la loro definizione.
Con `P≈P₀+ρgz`, b=(E+VP₀)/(nR) e c=Vρg/(nR), raccordando la pressione
al Moho e usando la profondità assoluta `zOfTop+z`. Fit e input devono
riportare a in Pa·sᵉ, b in K, c in K/m, dCreep in Pa. Conservare il profilo
PRE e quantificare l'errore della riduzione affine della pressione.

Il record ShellSet usa **un eCreep per entrambi gli strati**. Raccomando un
fit con n comune in log-stress nell'inviluppo P–T e tassi attivi, con
prefattori separati, confronto con entrambe le curve e sensitività della
resistenza integrata. Evitare di mediare gli esponenti: il cambio di pendenza
cambia l'aumento di resistenza con il tasso anche quando le curve coincidono
a un punto. Mancano ancora l'inviluppo di tassi e un criterio fisico per
accettare l'errore del fit. Il ramo fragile usa `cFric=tan φ` e pressione
verticale efficace `σ_z+Biot·p_w` con compressione negativa. La politica
idrica deve essere compatibile con il profilo di pressione usato dal codice;
la presenza della densità dell'acqua in PRE non assegna saturazione o
pressione. `dCreep` limita il massimo sforzo di taglio, `visMax` limita la
viscosità media e il codice può troncare l'integrale per taglio basale.
Dichiarare eventuali attivazioni e sensitività. Lasciare l'attrito di faglia
fuori dal primo modello di continuo.
[Diamnd, tassi e attrito](../../external/ShellSet-v1.1.0/src/MOD_Shells.f90#L2346) ·
[Diamnd, transizione e limiti](../../external/ShellSet-v1.1.0/src/MOD_Shells.f90#L2864) ·
[Record LR](../../external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90#L508)

## G3 — Due supporti confrontati, un candidato prioritario

**Interno placca 5.** L'Euler unico ha gradiente covariante simmetrico nullo.
Le quote originali FEG variano da 853,22 a 967,62 m, a parità di spessori,
densità e temperatura in funzione della profondità locale. La riduzione
analitica del momento idrostatico `∫ρg(z−z_ref)dz` sopra il piano comune
−79 km dà uno scarto massimo tra colonne di 2,71e11 J/m². Anche la pressione
al piano differisce di 3,52 MPa. Il piano è un riferimento diagnostico interno
a tutte le colonne, scelto per la comparazione. Il risultato dimostra un
contrasto di carico nei dati e dipende dal riferimento; non valuta il
risultante equilibrato. Il codice S1 calcola anomalie di tensione verticali
rispetto alla propria colonna di riferimento; `Fixed` include contributi
di tensione integrata, pendenza basale e carichi al bordo. Serve chiuderli
con il sostegno regionale esterno e basale. L'intero perimetro è un
taglio artificiale. Non è disponibile una chiusura fisica che trasformi
quel contrasto in deformazione predittiva del ritaglio.
[Squeez S1](../../external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90#L470) ·
[Forze nel continuo](../../external/ShellSet-v1.1.0/src/MOD_Shells.f90#L4383)

**Contatto 5:8, raccomandato.** Due facce adiacenti sullo stesso meridiano,
su due righe contigue. Quattro celle parent R100–101/C021–022, circa
10–12° N, 159–157° W nel frame canonico. La placca 8 è a ovest, la 5 a est.
Otto triangoli parent 71683–71686 e 72403–72406. I segmenti
`R6BND-T0-10fc6a8d9eb6b36cb9a5` e `R6BND-T0-61b58bd29612d49e4498`
non sono incidenti a giunzioni censite. La velocità relativa normale è
+0,157502/+0,157535 m/anno (apertura), con componente tangenziale
−0,006366 m/anno nella convenzione del censimento. È un minimo **supporto
di partenza** con due colonne laterali di celle e due facce documentate.
Adeguatezza della larghezza del dominio e convergenza richiedono verifica
dopo la scelta fisica. Il massimo di apertura 1:3 è su celle oceaniche,
quindi comporterebbe scelte materiali e di contatto ulteriori.
[Censimento cinematico](../../R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json) ·
[Blocco finite-step per ID](../../R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json)

La FEG parent ha zero elementi di faglia. Il censimento 5:8 registra una
classe meccanica UNKNOWN con apertura e shear privi di zona di accomodamento.
La coppia è eleggibile ma quiescente nel modello di rift e il suo limite
condizionale è 31.738,95 anni; il primo limite del calendario precedente è
27.123,41 anni per 1:3. Entrambi appartengono alla legge Euler a tassi fissi.
Una soluzione che redistribuisce i tassi richiede una propria verifica
temporale; nessuno dei limiti autorizza una faglia, la larghezza di un rift
o l'uso del guard come legge materiale.
[Censimento di eleggibilità](../../R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.md) ·
[Legge dell'evento](../../R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.md)

**Problema proposto.** Un singolo continuo estensionale con transizione
distribuita attorno alla traccia 5:8, compatibile con nodi condivisi e SHELLS
esistente. L'accoppiamento attraverso la traccia, la larghezza fisica e il
dominio di interazione sono ipotesi; non vanno dedotti dalla risoluzione di
un grado. Conservare geometricamente i parent FEG senza dedurre apertura
di vuoti o slip da una discontinuità Euler. La deformazione è la soluzione
del bilancio di forza, con GPE di PRE e reazioni al bordo, senza usare la
differenza di velocità per assegnare una strain predefinita.

- **Bordi laterali.** Proposta di pilotare i due lati distali occidentale
  e orientale con il campo tangenziale completo delle rispettive placche
  esterne (m/s nel frame ShellSet), condizionatamente alla loro
  rappresentatività come intorno rigido. Così si conserva anche lo shear
  misurato. I tagli nord/sud attraversano il sistema estensionale: servono
  vincoli di continuazione o trazioni risultanti di un intorno identificato.
  Nessun bordo libero è inferito dal fatto che la mesh finisca. Verificare
  rappresentabilità delle prescrizioni prima dell'assemblaggio; `VBCs` offre
  vincoli cinematici a una o due componenti. I bordi «free» della via
  standard mantengono il contributo litostatico; non sostituiscono trazioni
  generali di un intorno.
- **Base.** Adottare uno scorrimento senza shear solo se si assume e
  giustifica una base meccanicamente disaccoppiata nel breve intervallo,
  con sostegno normale coerente con il termine gravitazionale. In presenza
  di trascinamento servono velocità del mantello, frame comune, legge e
  parametri di accoppiamento, oltre a un ramo SHELLS applicabile. La LAB PRE
  è termica. Il gauge Euler è cinematico; Earth/PB2002 e le opzioni basali
  pilotate del codice non forniscono questi dati ad ARCANA.
- **Frame e modi rigidi.** Calcolare nel frame canonico, applicare la
  trasformazione numerica al binding SHELLS. Con due componenti distali
  prescritte, due nodi non paralleli bastano a escludere le tre rotazioni
  rigide da quel sistema omogeneo. Verificare il rango effettivo, evitando
  pin aggiuntivi se i vincoli lo chiudono. Per una futura formulazione a
  trazioni, verificare equilibrio di lavoro sui modi rigidi e fissare il
  gauge nel nullo senza reazioni artificiali.
[Imposizione delle componenti](../../external/ShellSet-v1.1.0/src/MOD_Shells.f90#L10010) ·
[Forze e reazioni al bordo](../../external/ShellSet-v1.1.0/src/MOD_Shells.f90#L553) ·
[Rami di accoppiamento basale](../../external/ShellSet-v1.1.0/src/MOD_Shells.f90#L3872)

## Decisioni autoriali minime e condizioni per T1

| Decisione | Dato o ipotesi da fornire | Verifica tecnica conseguente |
| --- | --- | --- |
| **G2. Materiale efficace e stato idrico** | Approvare o sostituire i due proxy; specificare regime di creep, pressione/attivazione crostale, acqua e pressione efficace, attrito e resistenza limite. | Ridurre le due leggi a esponente comune nella finestra attiva giustificata. Controllare errori sulle resistenze e sensitività, unità e attività dei limiti. |
| **G3. Accomodamento del 5:8** | Approvare estensione distribuita e assegnare supporto/larghezza fisica e finestra di validità dei tassi distali. | Verificare supporto del transetto e massa sulle celle, prova di scala del dominio e chiusura del bilancio di forza. Se il contatto deve essere discreto, occorre una legge di interfaccia per apertura e shear, oggi assente. |
| **G3. Intorno e base** | Confermare l'intorno rigido sui lati pilotati; assegnare continuazione o carico sui tagli trasversali e sostegno/accoppiamento basale. | Verificare compatibilità con il solutore, rango, reazioni, bilancio di forza e lavoro. |

A scelte chiuse, il primo passo resta regionale e breve: soluzione di
equilibrio con residui e reazioni, poi velocità e tassi per aggiornare la
geometria dei supporti. Un volume materiale segue il Jacobiano di area e
l'incomprimibilità adottata, con bilancio per strato. Un taglio attraversato
da materiale richiede il flusso di massa e di proprietà al bordo. La mappa
G4 già disponibile conserva ID parent e orientamenti, ma richiede il nuovo
binding dei quattro parent e un aggiornamento termico/materiale coerente
con la deformazione scelta. Verificare aree positive, spessori, massa per
materiale, fonte e validità del forcing, e ripresa prima di archiviare T1
in HistoryStore. Una politica di aggiornamento breve con termica disaccoppiata
richiede una stima dell'errore di splitting; non dichiarare un nuovo profilo
termico se non calcolato.

Evidenze in `ARCANA_WORLD_EVIDENCE/R6/FIRST_DEFORMATION_MODEL_DECISION_20261118_01`.
`SOURCE_REDUCTION.json` contiene pin, parent, PRE e risultati. Il primo
controllo SHA del censimento eventi ha confrontato il pin storico CRLF
con il file FAIR LF. La conversione in memoria riproduce esattamente il
pin storico; entrambi sono registrati. Nessun originale è stato riscritto.

# ARCANA R6 — ShellSet regionale, smoke e decisioni G2/G3

2026-11-18. **Caso A: ENGINEERING_ONLY, solve convergente. Caso B:
BLOCKED_EXACT_G2_G3_INPUTS.** Il test riusa la FEG regionale sigillata,
CASE.json e il lettore S1B regionale senza rimaterializzare la mesh. Segue D-024.

## Caso A — Solve regionale

Un driver seriale collega e chiama una volta il modulo SHELLS completo, da
lettura FEG/PRE e parametri a Square, ReadBC, assemblaggio FEM, solve, diagnostica
delle reazioni e Result. Il driver sostituisce l'orchestratore MPI della
suite ShellSet. Gli outline richiesti dall'input legacy sono una lookup
ingegneristica: AF racchiude i nove nodi e gli altri 51 slot sono lontani
dalla regione. Le velocità delle placche legacy sono azzerate nel driver e
nessun codice BC usa quei vettori. La strumentazione nella copia isolata
scrive direttamente le matrici finali v, EDot e tauMat prima di Balanc.
Il primo tentativo di link ha dichiarato Shells_v5p0 come routine esterna.
La versione eseguita importa la routine dal modulo SHELLS. Il tentativo
di link fallito non ha avviato il solver.

Parametri della fixture dal file iEarth5-049.in, con titolo ENGINEERING_ONLY.
In particolare iConve=0 e trHMax=0 modellano una base senza drag per
esercitare la risposta all'estensione laterale prescritta. Le BC di tipo 2
vincolano sud ed est ai soli otto nodi del perimetro. A Euler si aggiunge una
componente est che cresce linearmente con la longitudine canonica per un
totale di 2e-9 m/s fra i due estremi. Il nodo 5 conserva entrambi i gradi di
libertà. Il perimetro fissato rimuove le rotazioni rigide e dà un problema
Dirichlet per il continuo con resistenza interna. I valori sono una fixture
di esercizio numerico priva di attribuzione ai materiali di ARCANA.

| Misura | Risultato |
| --- | ---: |
| Nodi / triangoli / nodi di bordo letti | 9 / 8 / 8 |
| Iterazioni accettate dal solver | 3 |
| Ultimo criterio scoreB riportato / soglia nativa | 0,000309 / 0,000500 |
| Max errore sulle componenti imposte | 2,69e-24 m/s |
| Velocità RMS | 4,87417e-9 m/s |
| Max componente EDot | 9,32603e-15 s⁻¹ |
| Max componente tauMat, integrale verticale | 1,50532e12 N/m |
| Solve wall / CPU user / RSS | 0,12 s / 0,04 s / 10.240 KiB |
| Build NVFORTRAN 25.11 wall / RSS | 2,12 s / 59.056 KiB |

I nove record di velocità e i 56 record elemento/punto hanno ID completi e
valori finiti. Il mapping restituisce le velocità nel frame cartesiano canonico
e le componenti di EDot e tauMat nel frame tangente del solver, con ID parent.
tauMat contiene gli integrali verticali di Sxx−Szz, Syy−Szz e Sxy. Il log
registra anche iterazioni intermedie e il solver ha scritto i file di reazioni e
momenti. Il criterio riportato è la convergenza di velocità del codice nativo.
Questo run produce un equilibrio ingegneristico, senza timestep o T1.

## Caso B — Scheda reologica da decidere

Il riferimento locale `material_rheology_provider.py` contiene una
calibrazione dry-olivine per benchmark. PRE fornisce ruoli materiali,
temperatura e densità, senza mineralogia o fugacità d'acqua.
`constitutive_mechanics_microdomain.py` tratta un diverso problema Maxwell
ridotto. La legge candidata SHELLS è Diamnd, con attrito del continuo e
resistenza di creep limitata da dCreep. Usa una scala aCreep in Pa·s^e,
bCreep in K, cCreep in K/m, dCreep in Pa ed eCreep=1/n. Il ramo fragile
dipende da cFric e dalla pressione efficace con Biot. Queste quantità
richiedono una scelta applicabile alla crosta e al mantello del ritaglio.

Due riferimenti per formulazioni candidate, entrambi condizionati
all'attribuzione autoriale delle litologie:

| Formulazione | Crosta | Mantello | Assunzioni e risposta |
| --- | --- | --- | --- |
| A. Quarzite sperimentale + olivina anidra | Gleason–Tullis, Black Hill senza melt. T 900–1100 °C, pressione sperimentale nominale ~1,5 GPa, n=4±0,9, Q=223±56 kJ/mol, log10 A=−3,96±1,96 con stress in MPa e rate in s⁻¹ | Hirth–Kohlstedt come riferimento nominale già codificato nel progetto. A=1,1e−16 Pa⁻ⁿ s⁻¹, n=3,5, E=530 kJ/mol, V=14e−6 m³/mol. Dixon–Durham misura 15±5 cm³/mol intorno a 1373 K e circa 1,5–8,8 GPa nei propri esperimenti | Il fit crostale a pressione di riferimento non determina cCreep crostale. Richiede una scelta motivata sulla dipendenza dalla pressione e sul campo di validità fuori dal laboratorio. La struttura termica sposta la resistenza crostale con la profondità |
| B. Quarzite con fugacità esplicita + stesso riferimento di mantello | Hirth–Teyssier–Dunlap. n=4, Q=135±15 kJ/mol, m=1, log10 A=−11,2±0,6 con stress e fugacità espressi numericamente in MPa nella forma `rate = A f^m σ^n exp(−Q/RT)` | Stesso mantello della formulazione A | Serve fugacità d'acqua per profondità ed eventualmente pressione. A_T efficace cambia con la fugacità, che riduce lo sforzo richiesto a rate fisso al suo crescere. Non si trasferisce la fugacità terrestre ad ARCANA |

Le incertezze qui riportate appartengono alle singole calibrazioni. Non
costituiscono intervalli già assegnati alla regione. Fonti: [fit sperimentale
quarzo Gleason–Tullis](https://doi.org/10.1016/0040-1951(95)00011-B) e [tabella
delle calibrazioni di Tokle e collaboratori](https://doi.org/10.1002/2016JB013798),
[calibrazione con fugacità](https://doi.org/10.1007/s005310000152),
[riferimento mantello](https://doi.org/10.1029/138GM06) e [misura primaria
del volume di attivazione](https://doi.org/10.1029/2018JB015853).

Invertendo una legge di creep scientifica, lo sforzo di flusso è proporzionale
a `A^(-1/n) rate^(1/n) exp((E+PV)/(nRT))`. Prima di assegnare aCreep serve
allineare gli invarianti di stress e rate di laboratorio con quelli di Diamnd
e convertire i prefattori in SI. Una legge P(z)=P₀+ρgz darebbe localmente
bCreep=(E+P₀V)/(nR) e cCreep=ρgV/(nR), con origine di z coerente e pressione
continua al Moho. Un solo cCreep per strato è un'approssimazione con pressione
affine. Nel caso B la dipendenza da fugacità richiede inoltre una riduzione
esplicita o una legge supportata dal codice. La scheda SHELLS di base ha
un unico eCreep per coppia di strati. I nominali n=4 e n=3,5 non entrano
esattamente nello stesso record. Per adottare uno dei riferimenti serve un fit
a esponente comune con dominio ed errore dichiarati, oppure una scelta
costitutiva già compatibile. Nessuna delle due formulazioni è stata applicata
al solve. I parametri fragili, il limite dCreep e gli eventuali profili di
pressione efficace restano da assegnare.

## Caso B — Condizione meccanica da decidere

Il dominio è interno alla stessa placca. Con i vettori T0 disponibili,
`u=ω×r` ha gradiente spaziale antisimmetrico e deformazione simmetrica nulla.
Sulla sfera preserva distanze e aree. La velocità assoluta varia nel ritaglio,
ma non fornisce un tasso di estensione del materiale. Una differenza del
campo Euler lungo un arco non equivale a una strain rate. Geometria PRE,
topografia, densità e gravità permettono di formulare un contributo di
energia potenziale gravitazionale. L'equilibrio regionale complessivo
dipende anche da come la regione è sostenuta dall'esterno e alla base.

- **Trasporto rigido**. Usare il segmento Euler con validità dichiarata e
  trasportare i supporti. È il percorso se si desidera la cinematica della
  placca. Fornisce moto geografico con spessori e masse invariati e nessuna
  deformazione geodinamica.
- **Risposta meccanica regionale**. Specificare sul perimetro velocità
  differenziali o trazioni ottenute da una legge o da uno stato esterno
  identificato e verificare che siano rappresentabili in SHELLS. Un caso con
  bordo Euler può ancora rispondere a gradienti del carico interno e al drag
  basale, ma queste forze e il supporto del ritaglio vanno motivati. Specificare
  la condizione basale, incluso il frame del mantello se c'è drag, ed eliminare
  i modi rigidi con le prescrizioni già sufficienti o con un gauge esplicito
  se i bordi sono di tipo traction. Definire validità temporale della scelta.
  Una zona di contatto richiederebbe un altro supporto fisico e un binding
  specifico.

Per un primo T1 **deformante**, la scheda da approvare richiede quindi due
scelte accoppiate. Quali ruoli/litologie e parametri Diamnd si applicano nel
dominio, con la loro compatibilità numerica. Quale carico differenziale,
condizione laterale/basale e riferimento rappresentano l'intorno della placca
5. Se la scelta resta Euler rigido, il modello non offre una forzante
deformante dimostrata. Dopo un solve fisico, G4 deve distinguere una frontiera
materiale da un taglio con flusso di massa, legare spessori e densità al
bilancio corretto e fissare l'aggiornamento termico. Il mapping verificato
fornisce gli ID e le grandezze per quel passo. Stato fisico T1 assente.

Codice in `experiments/shellset_regional_explore_v1`. Build, fixture,
sorgenti, diagnostica e mapping conservati in
`ARCANA_WORLD_EVIDENCE/R6/SHELLSET_G2_G3_SMOKE_20261118_01`.

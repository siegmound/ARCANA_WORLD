# ARCANA R6 — Caso regionale ShellSet T0

2026-11-18. `BLOCKED_EXACT_G2_G3_INPUTS`.

Il caso regionale T0 è stato materializzato e il suo lettore PRE verificato.
Le decisioni ancora necessarie riguardano la legge costitutiva per crosta e
mantello e il problema meccanico al bordo. Il solve e l'avanzamento T0→T1
restano non eseguiti. Lo sviluppo segue D-024 e i quattro documenti consegnati
dal recupero FAIR del 18 novembre.

| Gruppo | Consegna | Condizione residua |
| --- | --- | --- |
| G1 | Una FEG locale di 9 nodi, 8 triangoli e 0 faglie. Identificativi parent, owner PRE, aree e circuito dei bordi in CASE.json | Verificare la configurazione meccanica del ritaglio nel binario completo quando G2/G3 sono determinati |
| G2 | Scheda dei parametri della legge ShellSet in MISSING_INPUTS.json | Attribuire legge, parametri e validità ai due ruoli materiali |
| G3 | Velocità Euler T0 riportate nel frame ShellSet e riferite ai nodi del circuito | Scegliere prescrizioni laterali, politica basale e riferimento meccanico |
| G4 | Mapping dei campi nodali e di deformazione verso i supporti parent | Scegliere il trasporto fisico appropriato a G2/G3 e verificarlo sulla futura soluzione |

Il ritaglio occupa le celle R092/C030, R092/C031, R093/C030 e R093/C031,
sulla placca 5. È il primo 2×2, per distanza in indici da R091/C028 e ordine
riga/colonna a parità, con supporti continentali PRE non misti, una sola placca
e nessun nodo sul bordo tettonico. L'area FEG sferica è 49.388,203 km².
Il nodo locale 5 è interno. Il bordo del ritaglio è un confine del dominio
numerico. Le celle e i triangoli conservano il supporto discreto originario.

Il circuito locale `1→2→3→6→9→8→7→4→1` soddisfa le condizioni topologiche
controllate per `Square` in MOD_Shells.f90. `ReadBC` richiede la specifica dei nodi
del circuito. `VBCs` può imporre una o due componenti a seconda del tipo.
Questo controllo non esegue Square o ReadBC nel binario completo. Il lettore
S1B globale impone 64.442 nodi e un censimento globale. La variante sperimentale
con marker distinto legge nove record continentali e conserva la validazione
di ogni record e le funzioni di valutazione originali. Per un futuro solve serve
una build isolata di ShellSet con quel lettore e il normale staging del payload
nella directory privata del caso.

**G2.** La candidata è la legge di continuo `Diamnd` già presente in SHELLS.
Il creep usa una scala di resistenza `aCreep` (Pa·s^eCreep), l'esponente
`eCreep` (adimensionale), la dipendenza `exp((bCreep+cCreep·z)/T)`
(`bCreep` in K e `cCreep` in K/m) e il limite `dCreep` (Pa). Se si usa
la formulazione standard con attrito del continuo, occorrono anche `cFric` e
il trattamento di pressione efficace e `Biot`. Queste scelte determinano
resistenza, sensibilità a temperatura e deformazione e transizione fra i rami.
I profili PRE danno temperatura e proprietà termiche e di densità.
`material_rheology_provider` dichiara il creep dry-olivine come benchmark senza
assegnazione ai materiali R6. `constitutive_mechanics_microdomain` risolve un
incremento Maxwell stratificato con parametri e apertura di prova. Per il caso
corrente servono una sola assegnazione motivata crosta/mantello, il set di
parametri applicabile e l'eventuale legge di pressione efficace. Il ritaglio
non richiede coefficienti di faglia o di subduzione.

**G3.** La formula è `Q (ω × r) / 31557600` in m/s con `r` in metri,
`ω` in rad/anno e `Q` uguale alla rotazione RX +0,5° esistente. L'errore massimo
nel confronto delle coordinate cartesiane unitarie è 2,22e-16. L'inventario
sorgente contiene tutti i 12 vettori e il ritaglio usa solo quello della placca 5.
CASE.json riporta le componenti sud/est (ordine di SHELLS) e l'azimut orario da
nord. Il campo Euler descrive rotazione rigida e non determina trazioni,
trascinamento basale o deformazione. Il gauge cinematico e il frame numerico
sono noti. La decisione necessaria è una specifica laterale/basale per il circuito,
con valori o componenti realmente imposte, riferimento e rimozione dei modi
rigidi compatibile con il problema, e applicabilità sul breve intervallo.
La regola condizionale del primo segmento è già disponibile. Il suo limite
relativo al rift non determina la validità del bordo regionale. Tutte le
prescrizioni e i carichi restano null. La rappresentabilità di eventuali
trazioni scelte va verificata nel percorso `ReadBC`/assemblaggio.

**G4.** `bind_solution` riceve velocità convergenti in ordine sud/est e tensori
EDot nei sette punti per triangolo. Restituisce velocità XYZ canoniche con ID
parent e conserva il tensore runtime e la traccia orizzontale per punto.
L'estrazione dal binario completo resta da collegare. L'aggiornamento geometrico
dovrà integrare le velocità tangenti e controllare orientazione e area dei
triangoli. Per uno strato materiale chiuso, a densità costante, la verifica
richiede massa invariata e spessore coerente con l'area aggiornata. Con trasporto
attraverso il taglio o densità variabile occorre invece il bilancio esplicito
della massa trasportata. La proiezione dei punti EDot sugli stock dipende da
questa scelta. `pure_shear_thermal_step` è riusabile solo se la soluzione supporta
l'ipotesi ridotta di estensione omogenea prescritta. Non si aggiunge il solve
Maxwell stratificato sopra quello ShellSet. Il controller e HistoryStore possono
conservare T0 e, dopo un passo accettato, T1 con parent, clock, supporti, campi
termici e materiali, stato costitutivo pertinente, forcing e ledger dei flussi,
fonti e configurazione per il restart. Questo lavoro produce il solo pacchetto
T0 e il mapping dei campi.

La prova mirata con GNU Fortran 13.3 confronta i 50 campi PRE diversi dall'ID
per tutti i nove nodi e 36 campioni dell'evaluatore (superficie, Moho, LAB e
LAB +1 km) fra lettore originale e variante regionale. Gli output stampati
con 17 cifre decimali in notazione scientifica coincidono. Conteggio errato,
record mancante e magic globale vengono rifiutati. Passano anche il round-trip
FEG, il recupero della velocità Euler canonica, l'associazione EDot e il
rifiuto di ID mancanti e dati non finiti. La costruzione ha richiesto 2,08 s wall
e 402.152 KiB di RSS, inclusa la lettura dei dati parent. La verifica con
compilazioni e probe ha richiesto 3,49 s wall, 3,18 s CPU user e 38.912 KiB
di RSS. Queste misure riguardano preparazione e verifica del reader.

Codice e istruzioni in `experiments/shellset_regional_explore_v1`.
Evidenza in `ARCANA_WORLD_EVIDENCE/R6/SHELLSET_REGIONAL_CASE_20261118_01`.

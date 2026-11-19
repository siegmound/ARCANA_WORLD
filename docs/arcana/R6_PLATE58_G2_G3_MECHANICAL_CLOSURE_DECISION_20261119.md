# ARCANA R6 — G2/G3: decisione fisica dopo il PASS FAIR dei nodi di uscita 5:8

**Data:** 2026-11-19. **Natura:** valutazione scientifica e proposta di contratto, **NON** approvazione autoriale di parametri o soluzione. **D-024 in vigore.** Ramo sperimentale `r6/multiphysics-integration-20261026`.

## 1. Evidenza FAIR ricevuta e interpretazione

L'operatore ha verificato il sorgente al commit `f0af63c12076201fea1dbdb5adfe61b8d0ae9292`, con `pytest` **6/6 PASS** e `boundary_junctions`:

`PASS_G3_EXIT_NODE_INCOMPATIBILITY_IDENTIFIED__SOLVE_BLOCKED`.

Il sorgente diagnostico non assegna BC, materiali o base. Le evidenze restano in
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_NEIGHBOR_16_NEW_01`.
I risultati sono **trascrizione del terminale FAIR fornita dall'operatore**; le evidenze esterne non sono state importate o ricalcolate su GitHub.

| Taglio | Nodo parent | `(v5-v8)_south`, m/s | `(v5-v8)_east`, m/s | modulo m/anno | doppia Dirichlet |
|:--|--:|--:|--:|--:|:--|
| nord, 13°N −159° | 36744 | −1.776479720734727e−10 | +4.991563070263678e−9 | 0.1576214795155939 | incompatibile |
| sud, 9°N −157° | 35306 | −1.4347232703460296e−10 | +4.988338446845373e−9 | 0.15748508690720361 | incompatibile |

Componenti calcolate in m/anno con 31,557,600 s/anno:
- nord: sud −0.00560614364; est +0.15752175075;
- sud: sud −0.00452764231; est +0.15741998937.

La differenza dei **moduli** è 0.00013639261 m/anno, circa **0.08653%** del modulo nord. Il confronto è cinematico e **non** valida un campo continuo di sforzi, né implica una fascia deformante uniformemente estesa.

Dominio 16 parent R099–R102/C020–C023: 25 nodi, 32 triangoli, 6 segmenti di contatto T0. Owner lato N: `[8,5,5,5]`; lato S: `[8,8,8,5]`. Il contatto raggiunge entrambi i tagli esterni. Nessun elemento di faglia esplicito è presente nella FEG sorgente.

## 2. Decisione G3 sui tagli — opzioni ordinate

**Opzione A, preferibile per un T1 fisico:** risolvere un intorno esterno continuo sufficientemente esteso, con trasferimento documentato delle **trazioni/condizioni effettive** all'interno, mantenendo le velocità Euler distali sul bordo ovest della placca 8 e sul bordo est della 5, dove i relativi supporti restano fisicamente rappresentativi. Il campo N/S deve emergere dalla meccanica dell'intorno; i due Euler distinti non sono due comandi allo stesso nodo. Occorre una chiusura anche per il dominio esterno e un test di indipendenza dalla sua estensione. *Attualmente non implementata né qualificata.*

**Opzione B, solo test EXPLORE di sensibilità:** usare le condizioni laterali `free` standard SHELLS sui tagli artificiali N/S in un halo esteso, poi variare drasticamente l'estensione nord/sud e confrontare la soluzione nel transetto centrale. Tale `free` **non è trazione esterna zero**: nel codice `Fixed` il bordo conserva carichi litostatici equivalenti a materiale esterno privo di resistenza. Non attribuire significato geologico a quell'approssimazione senza convergenza e confronto con A o altra evidenza esterna. Un solve B convergente **non è un T1 fisico ratificato**.

**Non ammissibili:** doppia Dirichlet sul nodo condiviso, media aritmetica delle due Euler come BC, scegliere unilateralmente plate ID a un nodo condiviso, periodicità N/S non verificata, trazioni arbitrarie; imporre apertura di una faglia senza legge di interfaccia. Non cambiare silenziosamente la topologia FEG a nodi duplicati.

**Scelta da ratificare:** una legge di continuazione esterna per A, oppure un programma di sensitività B esplicitamente etichettato NONCANONICAL e non promuovibile direttamente a storia T1.

## 3. G2 — reologia: quali dati sono fonte e quali mancano

T0 PRE: area continentale HOT_EXTENDED, Moho ~28 km, LAB termico ~80 km; temperatura crosta ~280–1051.56 K, mantello lit. ~1051.56–1671.77 K; pressione litostatica proxy ~0.754 GPa al Moho e ~2.368 GPa alla LAB. Queste informazioni **non** identificano acqua, fugacità, attrito o mineralogia.

Per la crosta la prova EXPLORE ha comparato due formulazioni quarzitiche: sforzi indicativi a 10 km **405 e 98 MPa prima del cap fragile**, rapporto **4.13265**. La differenza è un'incertezza costitutiva sostanziale. Non sostituire con il solo errore ~3.1% del fit dell'esponente su un inviluppo precedente. Il benchmark mantello dry-olivine del provider del repository (A=1.1e−16 Pa⁻ⁿs⁻¹, n=3.5, E=530 kJ/mol, V=14e−6 m³/mol) è di letteratura e NON assegnato automaticamente all'identità di materiale ARCANA.

Il runtime SHELLS legge per ogni Lithospheric Rheology Record prefattori `aCreep(1:2)`, attivazioni `bCreep(1:2)`, gradienti `cCreep(1:2)`, limiti `dCreep(1:2)`, **un solo `eCreep`** per entrambi gli strati, `cFric`, `Biot`, oltre ad altri campi; l'input del record non è un'autorità di campo per la regione. Nella proposta originale `eCreep=0.267857` è un **fit candidato**, non un valore fisicamente ratificato.

**Campi ancora da determinare:** famiglia proxy crostale scelta (o due scenari distinti), finestra P–T e dei tassi valida, prefattori crostali e conversioni invarianti/unità, acqua/fugacità e pressione di poro, Biot, `cFric`, `fFric` dove richiesto, `dCreep` e `visMax` pertinenti, errore **sull'intera resistenza integrata** con esponente comune, risultati fuori intervallo di laboratorio. Il criterio di confronto deve includere sensibilità dei limiti fragili e del differenziale su tutti gli strati; un singolo stress a 10 km non qualifica il fit.

**Scelta da ratificare:** due scenari di reologia efficaci `G2_QTZ_REFERENCE` / `G2_QTZ_WATER_SENSITIVE` con stato idrico *esplicitamente* modellato o ignoto bloccante, mantello dry-olivine benchmark, e una finestra/criterio quantitativo di fit. Finché mancano dati, i campi nel pacchetto meccanico restano `null` e non si genera un file LR fittizio.

## 4. Base, risoluzione e tempo

La precedente ipotesi **EXPLORE** di free-slip tangenziale alla base non assegna il sostegno normale. In SHELLS thin-shell la GPE e i carichi verticalmente integrati nel continuum richiedono un controllo specifico sui contributi `Squeez`/`Fixed`; NON aggiungere una pressione di base separata prima di verificare se duplichererebbe il termine esistente. Trascinamento mantellare richiederebbe inoltre velocità e legge del mantello, oggi non sorgente-bound.

Larghezza nominale di accomodamento **100 km**, solo ipotesi EXPLORE. Le celle ~1° (~100–110 km) non risolvono fisicamente tale larghezza. Una griglia numerica annidata più fitta può verificare convergenza delle equazioni **senza creare nuovo dettaglio geologico**: l'interpolazione dei parent T0 resta identificata come supporto numerico, non come nuove osservazioni. Le alternative 10 e 300 km restano sensibilità e non calibrazioni.

Un primo `Δt` breve (ad esempio 1 anno) è una possibile prova **non autorizzata**, da selezionare dopo la soluzione del bilancio di forza e controllo di stress/reazioni e dei limiti temporali Euler/eventi. Non scrivere T1 né G4 prima di risolvere flussi sul bordo, conservazione degli stock, massa di ciascuno strato e splitting termico.

## 5. Contratto di solve e prossima azione reale

Prima di **qualunque** `PHYSICAL_DEFORMING_T1`, servono simultaneamente:

1. Scelta fisica registrata per G2 e input dimensionali, con fit verificabile e limiti fragili/idrico.
2. Scelta esplicita per G3 continuo **e** condizioni N/S esterne meccanicamente motivate (A, preferita), oppure un B confinato a esperimenti di sensitività con verifica di indipendenza dal confine; nessuna promozione per default.
3. Chiusura compatibile e non duplicata del sostegno normale basale + interazione tangenziale.
4. Studio di convergenza spaziale sul rift e sull'intorno, tempo di validità, reazioni e lavoro ai bordi, verifica di rango/gauge.
5. Solo dopo, un unico solve meccanico breve seguito da verifica G4/HistoryStore e confronto con T0.

**Decisione attuale:**
```text
FAIR_G3_EXIT_NODE_AUDIT=PASS_6_OF_6
G3_DUAL_EULER_DIRICHLET=REJECTED_BY_SOURCE
G3_NORTH_SOUTH_CONTINUATION=UNRESOLVED
G3_BASAL_NORMAL_SUPPORT=UNRESOLVED
G2_EFFECTIVE_CONSTITUTIVE_LAWS=UNRESOLVED
G2_G3_EXPERIMENTAL_SCENARIO=PROPOSED_NOT_RATIFIED
PHYSICAL_DEFORMING_T1=BLOCKED
```

Nessun nuovo script FAIR necessario per confermare i sei test appena conclusi. **Non perpetuare preflight/micro-audit**: prossimo lavoro tecnico solo dopo selezione della chiusura e dei dati che la rendono fisicamente definita.

## Fonti nel repository

- `docs/arcana/R6_FIRST_DEFORMATION_MODEL_DECISION_FAIR_20261118.md`
- `docs/arcana/R6_PLATE58_FAIR_G3_JUNCTION_CLOSURE_20261119.md`
- `src/arcana_worldsim/r6/material_rheology_provider.py`
- `external/ShellSet-v1.1.0/src/MOD_Shells.f90` (in particolare `Fixed`, `VBCs`, ramo GPE e basal)
- `external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90` (lettura record LR)
- `experiments/plate58_deforming_explore_v1/` (source-bound staging)

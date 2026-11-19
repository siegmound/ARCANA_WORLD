# ARCANA R6 — Esito FAIR: baseline cinematica globale 100–1000 anni

**Data** 2026-11-19. **Classificazione** `PASS_GLOBAL_T0_1000Y_KINEMATIC_BASELINE__CONTACTS_UNRESOLVED`. **Ambito**: esperimento di rotazione rigida su tutte le 12 placche del T0, PRE passivo, senza G2/G3, solver meccanico, nuova crosta, trasporto fisico di risorse né un T1 canonico.

## 1. Fonte e riproducibilità

Questa decisione registra i risultati mostrati dall'operatore nel **terminale FAIR**. I report, i tre checkpoint del benchmark 100Y e i sei del benchmark 1000Y rimangono sul filesystem FAIR e non sono stati importati o autenticati indipendentemente mediante accesso diretto ai file.

- Checkout isolato: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY`
- Commit sorgente del benchmark 100Y: `716a1ba770331cd759ee4703545893235b7696bc`
- Commit sorgente del benchmark 1000Y: `ce4c4d7351dd4d069d0abac251758034c6d247bd`
- Evidenza 100Y: `.../ARCANA_WORLD_EVIDENCE/R6/GLOBAL_T0_KINEMATIC_100Y_NEW_01`
- Evidenza 1000Y: `.../ARCANA_WORLD_EVIDENCE/R6/GLOBAL_T0_KINEMATIC_1000Y_NEW_01`
- Test mirati: 100Y **7/7 PASS**, 1000Y **9/9 PASS**.
- Il runner 1000Y ha verificato manifest e SHA dei membri 100Y e la coerenza delle sorgenti e di T0 prima di avanzare; al suo anno 100, `prior_100y_prefix_bit_exact=true`. La sua verifica finale ha mantenuto gli input precedenti immutati secondo le operazioni di hashing implementate.

## 2. Dimensione planetaria realmente esercitata

```text
canonical_mesh_nodes=64442
triangles=128880
parent_faces=64800
plates=12
plate_local_material_point_views=66435
shared_node_plate_pairs=30
shared_plate_pair_node_observations_at_1000Y=2013
T0_age_ma=210.0
100Y_age_ma=209.9999
1000Y_age_ma=209.999
```

`plate_local_material_point_views` sono viste numeriche transitorie, non nuovi punti geologici. I nodi sorgente condivisi dai contatti sono rappresentati separatamente per permettere due moti cinematici differenti: **questo non equivale** alla duplicazione ratificata di gradi di libertà FEG per il solver fisico.

## 3. Prestazioni FAIR misurate

| Metrica | 100Y | 1000Y |
|:--|--:|--:|
| Source load wall | 0.7793337851762772 s | 0.7788458801805973 s |
| Somma wall dei soli avanzamenti | 0.12856468930840492 s | 1.3146171607077122 s |
| Somma CPU dei soli avanzamenti | 0.1284725430000001 s | 1.3136413190000042 s |
| Step wall p50 | 0.0012844931334257126 s | 0.0013122372329235077 s |
| Step wall p95 | 0.0013042837381362915 s | 0.0013318523764610291 s |
| Step wall massimo | 0.0013717971742153168 s | 0.002121325582265854 s |
| Checkpoint I/O wall | 0.018483232706785202 s | 0.0374610498547554 s |
| Picco processo RSS | 169476 KiB | 169476 KiB |
| RSS istantanea al reporting | 113860 KiB | 113856 KiB |
| Wall fino alla preparazione del rapporto | 1.0948201455175877 s | 2.9379787109792233 s |

Solo 1000Y: verifica evidenza precedente 0.011501479893922806 s; diagnostiche geometriche 0.08622792363166809 s; replay indipendente 500+500 del mezzo segmento 0.6516453735530376 s; user CPU delta 2.845179 s; system CPU delta 0.08904 s. Questi tempi sono annidati: non sommarli indiscriminatamente.

Avanzamenti `1000Y/100Y = 10.225336115067865×` a fronte di dieci volte gli anni. P50 per avanzamento circa +2.16%. Il wall fino al report cambia circa `2.6835×`, perché il caricamento iniziale ha costo quasi fisso e la seconda prova include replay e diagnostiche differenti. Il picco osservato è circa **165.50 MiB**. Non è una previsione delle prestazioni di ShellSet, G2, G3, G4, Deep, biologia o HistoryStore planetario.

## 4. Correttezza numerica

| Metrica | 100Y | 1000Y | Vincolo |
|:--|--:|--:|--:|
| max XYZ direct vs composed, unit | 5.329070518200751e−15 | 5.340172748447003e−14 | ≤1e−11 |
| max radial norm error | 5.10702591327572e−15 | 4.2743586448068527e−14 | ≤1e−11 |
| max signed triangle area drift, sr | 7.3075226425523e−17 | 5.488502447664745e−16 | ≤1e−11 sr |
| Restart | 50+50 error=0 | 500+500 error=0 | ≤1e−11 |
| Exact 100Y prefix | — | true | true |
| Triangoli invertiti, 1000Y | — | 0 | 0 |

Il drift XYZ 1000Y è `10.020833333333334×` quello 100Y, rimane `187.26×` inferiore alla soglia. Una stima di scala radiale usando `R=6371000 m` è **3.402224058e−7 m**, circa **0.34 micrometri**; non si tratta di un errore di posizione geodetico confrontato con dati osservati, ma della differenza numerica di due formule della **stessa** cinematica.

## 5. Contatti: deficit di fisica distinto dall'errore

Al 1000Y, 2013 osservazioni di identità nodali condivise per coppia di placche (30 coppie con nodi in comune):
- separazione media delle viste: **114.39697555002066 m**;
- p95: **195.53105383269806 m**;
- massima: **222.39656222603784 m**;
- zero triangoli a orientamento invertito nella cinematica delle singole placche.

Non chiamare questi numeri `displacement error` o `physically created opening`. I punti sono copiati in viste cinemáticas per placca e trasportati indipendentemente; il massimo di 222.4 m indica incompatibilità delle due posizioni senza legge di deformazione/contatto. Una separazione in coordinate non determina l'area di oceano creata, la massa mancante, una faglia, l'energia di deformazione, la larghezza effettiva o la pressione su un margine.

La deviazione numerica 1000Y è circa 0.34 micrometri in scala posizione, ~6.54e8 volte più piccola del massimo distacco tra viste. Pertanto il limite apparente non è l'integrazione della rotazione; è l'assenza di G2/G3 fisica e del trasferimento meccanico dei contatti.

## 6. Decisione e prossima fase

```text
GLOBAL_R6_T0_100Y=PASS_FAIR_OPERATOR_REPORTED
GLOBAL_R6_T0_1000Y=PASS_FAIR_OPERATOR_REPORTED
KINEMATIC_RUNTIME_RESOURCE_BASELINE=QUALIFIED_FOR_THIS_IMPLEMENTATION_AND_INPUT
RIGID_PLATE_NUMERICAL_ERROR=WITHIN_DECLARED_TOLERANCES
CONTINENTAL_MECHANICAL_CONTACT_ACCOMMODATION=NOT_IMPLEMENTED
PASSIVE_PRE_MATERIAL_THERMAL_EVOLUTION=NOT_IMPLEMENTED
G3_ARCHITECTURE_A=AUTHOR_RATIFIED_EXPLORE_ONLY
G2_EFFECTIVE_RHEOLOGY=UNRESOLVED
G3_EXTERNAL_CONTINUATION_AND_BASAL_SUPPORT=UNRESOLVED
FULL_PHYSICAL_WORLD_1000Y=NOT_TESTED
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_DEFORMING_T1=BLOCKED
```

**Stop a nuovi benchmark di sola cinematica di durata crescente.** Ritorno al lavoro fisico sostanziale già selezionato: chiudere G2 (fragile+duttile, acqua/pressione efficace e legge di creep verificabile sull'intera colonna) e G3 **A** (continuo esterno, trazioni N/S derivate, supporto normale/tangenziale basale compatibile con GPE). Il benchmark globale qui concluso è baseline di throughput e identità; non autorizza un avvio globalizzato del solve con materiali o carichi non giustificati. Quando i primi casi fisici sono chiusi e verificati, la scala planetaria fisica potrà essere misurata separatamente con inventario dei nuovi costi numerici.

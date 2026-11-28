# ARCANA WorldSim — G46: gauge vincolato, datum e restart nativo

28 novembre 2026, Europe/Rome. Provenienza **FAIR_WORKTREE / FAIR_EXTERNAL_EVIDENCE**: lettura ed esecuzione dirette, non dichiarazioni indirette. Handoff G46 letto integralmente e conservato. Autorizzazione esplicita dell’autore: campagna sintetica, plugin isolati, tempo positivo esclusivamente sintetico fino a due passi per lineage, progettazione G15/T0 e pubblicazione GitHub. Branch `r6/g36r2-fair-repair-20261127`; baseline G45 `03190254ff4843cbabd8dd7c8891cea291a67e27`.

## Esito

**`G46_SYNTHETIC_CAMPAIGN_COMPLETED_RESTART_PASS_GAUGE_DATUM_BLOCKED`**, `all_gates_pass=false`. Campagna terminata secondo i gate e la stopping rule dell’handoff; la qualifica completa del mantello AMR resta bloccata. Nessuna tolleranza originale è stata allentata.

- Restart nativo reale, stesso rank e cambio1→2/4/8: PASS nella configurazione sintetica dichiarata. Tutte le storie di soluzione e gli integrali confrontati; nessun export/readback chiamato restart.
- Gauge: tre modi rotazionali a bassa energia, ma non nulli. Il candidato saddle AMR non supera il residuo delle equazioni originali; nessuna correzione della velocità o del forcing viene ammessa.
- Datum: separati errore di quadratura e mancata cancellazione delle facce interne AMR. Il criterio originale coarse resta FAIL; non è stato sostituito con un’identità discreta più favorevole.
- Parità completa della velocità: non recuperata. Le differenze G45 fine sono confermate anche nelle norme volumetriche native dei campi grezzi.
- 17 test mirati/regressioni PASS;11 negativi operatore/datum respinti e4 negativi restart respinti, con scope distinti sotto. Tutti i tentativi falliti e i checker corretti conservati.
- Contratto G15 eseguibile come preflight, pin e input T0 verificati; matrice di10 decisioni T0 con dipendenze, alternative e criteri. Nessuna nuova traiettoria G15 o assegnazione.

| Gate | Esito |
|---|---|
| `AMR_internal_face_cancellation_under_H` | `FAIL_HIGHER_ORDER_INTERNAL_FLUX_REMAINS` |
| `G15_executable_contract_preflight` | `PASS_DESIGN_ONLY_EXECUTION_NOT_AUTHORIZED` |
| `T0_decision_matrix` | `READY_10_UNSELECTED_CHOICES_NO_ASSIGNMENTS` |
| `analytic_prescribed_velocity_regression` | `PASS_NATIVE_AND_G45_TRACE_AUDIT_WITH_AFFINE_LIFT_ADJUDICATION` |
| `coarse_original_G45_pressure_datum` | `FAIL_UNCHANGED_0.005_THRESHOLD` |
| `exact_rotational_kernel` | `BLOCKED_POSITIVE_DISCRETE_STRAIN_AND_NONZERO_OPERATOR_ACTION` |
| `full_free_slip_velocity_rank_parity` | `NOT_RECOVERED_G45_FAILURES_CONFIRMED_BY_RAW_VOLUME_NORM` |
| `higher_order_cellwise_divergence_identity` | `PASS_WITHIN_PREDECLARED_1e-10` |
| `native_changed_rank_restart_1_to_2_4_8` | `PASS_BOUND_SYNTHETIC_CONFIGURATION` |
| `native_same_rank_restart` | `PASS_BOUND_SYNTHETIC_CONFIGURATION` |
| `near_null_saddle_gauge` | `FAIL_ORIGINAL_MOMENTUM_RESIDUAL_THRESHOLD` |
| `negative_operator_datum_gates` | `PASS_10_NATIVE_ARTIFACT_REJECTIONS_PLUS_1_ALGEBRAIC_FORCING_FIXTURE` |
| `negative_restart_gates` | `PASS_3_NATIVE_REJECTIONS_PLUS_1_PRE_RUN_CLOCK_GUARD` |
| `new_free_slip_rank_fine_extension` | `NOT_RUN_AFTER_FAILED_EXACT_KERNEL_GATE` |
| `original_net_rotation_AMR_convergence` | `FAIL_RETAINED_HYDRO_AND_FORCED_CONTROLS` |
| `retained_G45_diagnosis` | `PASS_READONLY_WITH_NATIVE_VOLUME_NORM_COMPLETION` |

20 invocazioni native con CASE_SPEC;14 stadi supervisionati di configure/compile, inclusi due build falliti. Nessun benchmark HPC G44 ripetuto. I9 casi statici includono due controlli originali non convergenti e due probe necessari alle norme volumetriche mancanti;8 invocazioni restart positive/setup/recovery e3 negativi nativi. I casi dipendenti da un gauge ammesso sono NOT_RUN, non PASS.

## Contratti, runtime e protezioni

Contratto principale **`a4be9d965d14dca982ad1d2d3607cdc6814e196c51d2813ceeeacdaae3c5b2fd`**, commit `e693ebaf`, prima di nuove esecuzioni. Supplementi congelati prima dei rispettivi build/run:

| Contratto | SHA256 |
|---|---|
| Semantica restart e wrapper termico | `e31767b6f33ac5f651bba622cddce766420b909654af40fd1a5fe5a0e71350cd` |
| Operatore AMR piccolo/facce interne/controllo analitico | `d3afb0d98ab2d8f9d6b74101538b3f0000097a444bab685f0c9a0d65e75f1efb` |
| Norme volumetriche dei campi G45 conservati | `61e8fb2a09c55a789307b4c3bd4f7f47906a57c426d86d89857c039009573501` |

Runtime G45 qualificato letto in sola lettura: ASPECT3.2.0-pre commit30eb77ee5da186137d436dbad35c6cb3cab64b69, deal.II9.6, Trilinos13.2, p4est2.2, GCC11.4, OpenMPI4.1.2. Nessuna reinstallazione, rebuild prestazionale/SIMD o modifica di ASPECT. Nuovi plugin privati; snapshot del sorgente e SHA dei binari in ogni build. MPI ob1,self,vader con single_copy_mechanism=none, un thread BLAS/OpenMP; affinità fisica esplicita. Nessun solve64/128rank o GPU.

SOURCE901cbb4a38916190df6a881bb561b6558dd997dd pulito e immutato; inventari completi di20 parent verificati alla chiusura. Metadata storico92749elementi invariato; otto binari del deployment G45 identici, G41/G42/supervisore G44 e audit G45 conservati.181identità PID/starttime ricontrollate, nessun processo osservato ancora vivo e tutti i RUN_EXIT senza remaining. Non sono stati terminati job estranei.

Budget:8rank/job,600s/caso,16GiB PSS campionata, swap job64MiB, riserva host max(64GiB,25% MemAvailable iniziale), campioni target0.5s; compilazione un thread. Picco nativo osservato **0.767593GiB**, massimo intervallo di campionamento **0.819299s**. Il cap campionato non è un limite kernel e può perdere picchi brevi; RSS duplica pagine condivise. Oracoli sparsi sul coordinatore separati, non replica di array globali in ogni rank. Le prove MPI sono state serializzate; compilazioni/analisi indipendenti usano core62/63 quando concorrenti.

## Gauge: evidenza e limite matematico

Join dei campi G45 tramite CellId/local-basis minimo, mai solo coordinate o indici globali fra run. Prima dei nuovi solve, analizzati14campi G45 trattenuti e confrontati i valori grezzi. G45 non esportava C completo o masse volumetriche: strumentazione aggiunta solo sui casi decisivi. C contiene hanging-node e condizioni meccaniche omogenee; H resta solo topologico per recuperare le reazioni. La lift affine del controllo a velocità prescritta è separata.

Oracolo sparse indipendente: K, B e M da mapping/FE/quadratura reali; confronto Kz esportato e spettro generalizzato `C^T A C z=lambda C^T M C z`. È spettro di deformazione, non una pretesa di spettro singolare completo del saddle o nullità su tutte le mesh grandi.

| Mesh piccola | Tre autovalori più bassi | Quarto |
|---|---|
| Uniforme L1 | 0.000327510698, 0.000327510698, 0.000327510698 | 2.81426883 |
| AMR L1+1 | 0.000231708796, 0.000244785288, 0.000257229927 | 2.81370877 |

Le rotazioni coordinate grezze su AMR violano H/C di circa3e-5; quelle rese ammissibili producono ancora energia e azione/divergenza non nulle. Il mapping nativo è grado4, la velocità Q2: un moto rigido interpolato non è automaticamente un moto esatto del problema discreto. Le soglie di nullità/ammissibilità erano fissate prima delle misure.

**Rettifica della congettura dell’handoff:** `interpolate_onto_velocity_system` applica già stokes_hanging_node_constraints. Le soluzioni native finali osservate rispettano H/C entro l’arrotondamento; la sola assenza di una seconda distribute dopo la sottrazione non dimostra la causa. Il controllo idrostatico e forced originali continuano a fallire la convergenza nonlineare1e-6 pur uscendo0. Il diagnostico su copia dello stato finale non è una cronologia pre/post di ogni correzione interna: questa limitazione è esplicita.

Candidato saddle ridotto con G=MZ: sul forcing uniforme il moltiplicatore è trascurabile perché il campo soddisfa già quel vincolo; il primo status testuale troppo forte è rettificato da `UNIFORM_SADDLE_ADJUDICATION.json` senza riscrivere il run. Sul piccolo AMR il residuo originale di quantità di moto è **1.1382749704e-6**, contro1e-10; moltiplicatori circa(−3.0183e-4,7.6386e-4,1.3733e-3). Lavoro aggiunto circa5.43e-18 non autorizza a ignorare il carico aggiunto. Il riferimento di pressione ausiliario Euclideo dell’oracolo è distinto dal datum superficiale nativo. Nessun candidato ammesso come gauge equivalente; nessun punto fissato, mantello fermo, torque fitting o proiezione RHS.

## Datum: volume, superficie e geometria interna

Pressione costante10Pa, u/materiale fissi: incremento volumetrico `-10 int div(phi)` a Gauss3/5/7 e superficie `-10 int phi.n` GLL3/Gauss3/5/7; stessa H e stessa massa GLL condensata, risolta intera. Il confronto con la coppia G45 reale differisce dall’incremento a u fissata soltanto di circa5.96e-9 nella norma di traccia: il difetto coarse non viene spiegato da un grande cambiamento della soluzione.

| Quantità coarse | Valore |
|---|---:|
| Criterio originale G45 projected −10n | 0.0062731828 > 0.005, FAIL |
| Diagnostico L2 di massa volumetrico Gauss3 vs superficie GLL3 | 0.0059166976 |
| Traccia Gauss7 vs Gauss7 | 1.15392364e-10 (diagnostico, non sostituisce lo screen originale) |
| Identità per cella volume vs tutte le facce, Gauss3 | 2.06043364e-6 |
| Identità per cella volume vs tutte le facce, Gauss7 | 5.05694010e-15, PASS1e-10 |
| Flusso interno condensato H, Gauss7 | 1.01704192e-5, FAIL1e-10 |
| Azione meccanica C-transpose della pressione costante | norma0.0080017035 |

A quadratura alta si chiude il teorema di divergenza per cella, ma le facce interne mapped AMR non si cancellano nella traccia H secondo il criterio fissato. Non è quindi corretto ridurre tutto al solo ordine di quadratura o chiamare esatto il kernel della pressione costante. Il residuo interno e la tangenzialità al bordo richiedono una variante geometricamente e discretamente coerente. Operatore nativo, geometria, forcing e tolleranze sono rimasti invariati.

## Parità grezza della velocità

Due probe nativi a1rank integrano i campi G45 conservati sulle due mesh reali, con identità CellId/local-basis e senza proiezioni. Le differenze sono campi di input diagnostici, non modifiche alla soluzione ASPECT.

| Confronto | Norma storica G45 | Norma volumetrica nativa G46 |
|---|---:|---:|
| Coarse forced p4−p1 | sotto1e-4 | 7.32707278e-7 |
| Fine forced p8−p1 | 1.15925371e-4 | 1.26496934e-4 |
| Fine datum p4−p1 | 1.52131036e-4 | 1.65932011e-4 |

Le differenze hanno energia di deformazione molto piccola (fine circa2.89e-11/8.09e-11), coerente con un problema di modi poco energetici; questo non sostituisce la parità assoluta. Il fit rotazionale iniziale è solo diagnostico: nessuna velocità corretta o quotient-space usata per PASS. I gate originali restano falliti; nessuna nuova matrice free-slip1/2/4/8 viene dichiarata superata. Il controllo analitico a velocità prescritta supera convergenza nativa e audit G45; il suo apparente difetto C omogeneo è rettificato sottraendo la lift affine esportata, non applicando un gauge free-slip.

## Restart nativo qualificato e semantica dei due passi

Il materiale wrapper delega esattamente la meccanica HollowSphere nativa; solo cp=1 e conducibilità0.001 sono dichiarati sintetici per una prova termica non banale. Temperatura iniziale1000+20xy+10z e marker0.5+0.1xy+0.05z, nessuna assegnazione ARCANA. Mesh uniforme L2, dt0.001s e termine0.002s congelati. Nessuna modifica ASPECT.

**Semantica nativa esplicita:** ASPECT calcola t0, poi advance_time sposta le storie e scrive il checkpoint con clock0.001s. La ripresa legge questo stato pendente, calcola un passo di trasporto a0.001s e serializza a0.002s. Sono due incrementi nativi di clock nella lineage e un solo solve di trasporto nonzero. Non si dichiara un solve a0.002s, una terza accettazione o una verifica matura BDF2. Il plugin di terminazione impone stop>=0.002s e guardia timestep<=2; il solo EndTime nativo usa > e avrebbe avanzato oltre il cap.

Snapshot veri di mesh/solution/old_solution/old_old_solution e restart compresso nativo; fresh process con Resume computation. Gli output del segnale pre_checkpoint_store_user_data sono confrontati tramite supporti stabili, includendo pressione, temperatura, composizione, clock e integrali. Tutti i passi hanno residuo finale<=1e-6 e nessun warning solver.

| Rank di ripresa da1rank | Max differenza relativa campi | Esito |
|---:|---:|---|
| 1 | 0 | True |
| 2 | 3.376289593e-12 | True |
| 4 | 5.287425683e-12 | True |
| 8 | 6.501908406e-12 | True |

Massima differenza relativa degli integrali **7.07598e-14**. Variazione non nulla dei campi T/marker nelle norme dei coefficienti: {'4': 4.359972802945309, '5': 0.02176170140892192}. La ripresa stesso rank è esatta nei campi verificati. Il cambio-rank è supportato in questa configurazione p4est/Q2/manufactured e in questo intervallo; non qualifica restart di mantello compressibile, accoppiamenti o stati ARCANA.

## Negativi, regressioni e fallimenti conservati

11 negativi operatore/datum: rotazione grezza non ammissibile, modo non nullo, forcing incompatibile (fixture algebrica di kernel esatto, non kernel nativo inventato), H rotto, C rotto, contributo MPI omesso, identità rank errata, segno pressione errato, shift non costante, quadratura scambiata, faccia rimossa.10 usano campi/shard nativi tramite overlay; uno prova il predicato con un kernel esatto costruito. I loader e i gate sono quelli di produzione; baseline byte-invariata.

4 negativi restart: checkpoint mancante, compresso corrotto e inventario campi incompatibile respinti dal lettore nativo prima del passo; clock incoerente respinto dal gate reale di lineage prima del lancio. Il checker originale si aspettava il messaggio n_fields, ma il lettore respinge prima il vettore critical composition discretization: adjudication distinta, nessun rerun inutile.

17 test finali PASS, una deprecazione SciPy block_diag nei test G45. Sono conservati: buildNEW02 per tipo SimulatorSignals incompleto; buildNEW05 per inserimento del diagnostico nel metodo errato; primo setup restart con parametro nel subsection errato; segfault del nuovo postprocessor dovuto a update flags FE mancanti; JSON parziale NumPy-bool dopo il successo nativo. Tutti corretti in nuove identità/output o con adjudication read-only, senza ripetere i tre solve restart già riusciti. Conservati anche i primi parser/checker falliti e gli status poi rettificati. Nessuna evidenza G45 riscritta.

## G15 corretto: contratto eseguibile, nessuna traiettoria

Proposta `g46_constrained_gauge_v1/g15_corrected_executable_contract.json`, validatore `scientific_design.py --validate-only`:15binding di file reali e9 parent con inventari verificati. Seed: INITIAL_CHECKPOINT G4 non evoluto e soli array iniziali delle columns_64 G5. Nessun checkpoint meccanico112/162anni ammesso; prima del primo avanzamento occorre inizializzazione meccanica T0 con FB2 slopey/sinA dai sorgenti corretti G30/G31 e confronto band/CSR.

Macrointervalli proposti1,1,10,25,25,25,25,50anni fino162, con half-endpoint matched; policy e tolleranze originali, midpoint predictor escluso dal ledger energetico, CN matched8/4 e raddoppio temporale, massa/calore/energia/stress/dissipazione, restart same/fresh process, D12 e orizzonti evento. Il contratto distingue input invariati, sorgenti corrette, stati contaminati e operatori. Il validatore è eseguibile oggi; l’adapter completo della nuova traiettoria richiede implementazione e qualifica, e nessuna traiettoria G15 è autorizzata in questa campagna.

## T0 completo: decisioni concrete e ammissione

Matrice `mantle_T0_decision_matrix.json`:10decisioni con autorità da fonte versus scelta autoriale, alternative, unità, dipendenze, sensibilità/incertezza e controlli: CMB/interfacce; EOS/massa/gravità; termica; composizione/acqua/redox/fasi; pressione assoluta; reologia; flussi/core/riscaldamento; perturbazioni/velocità/spin-up; interfaccia e gauge comune; masks/anchor/archivio. Tutte le scelte e i valori assegnati restano null.

Raggio6371000m e g superficiale9.82m/s² sono baseline dichiarate, non autorità per CMB terrestre o profilo gravitazionale. G43 resta condizionale0–300km con zero nodi fisici mantellari ammessi; B6K resta geometria plate-local e conserva la riconciliazione di provenienza G45. M01 non selezionato/eseguito. La matrice dà un percorso di decisione e test, non una nuova lista generica di fonti.

## Prossime azioni scientifiche e WORLD_HISTORY

1. Nuova variante sintetica esplicita per geometria AMR conforme, riproduzione dei modi rigidi, tangenzialità meccanica e divergenza volume/bordo coerenti. Qualsiasi copia privata ASPECT deve preservare il runtime storico e superare kernel/compatibilità forcing, regression uniforme/analitica, datum e parità grezza fra rank prima di estendere. Una semplice proiezione su C o sottrazione rotazionale non basta.
2. Percorso A: mappa reale SHELLS–ASPECT non coincidente, aggiunzione, forze/momenti/lavoro e ripartizione della reazione normale; niente doppio conteggio OneBar colonna irrisolta versus mantello risolto.
3. Percorso B: risolvere le scelte T0 source/author-bound e applicare i criteri della matrice; nessun riempimento UNKNOWN.
4. Percorso C indipendente: revisionare il contratto/adattatore G15 corretto e ottenere autorizzazione separata prima della nuova traiettoria. G18/G30/G31 non qualificano automaticamente162anni corretti.
5. D-024: partire dal minimo sottosistema fisicamente chiuso, non attendere tutti gli engine. Physical T1 è una tappa verso WORLD_HISTORY210Ma→0ka, inclusi ultimi200ka: topografia/batimetria, risorse naturali marine/acquatiche, Deep con legge/energia propria, clima/acqua/erosione/suoli/biomi, flora/fauna, popolazioni/insediamenti/civiltà. HistoryStore causale con checkpoint/eventi/provenance, query regione/epoca/processo e raffinamento derivato con lineage/convergenza/incertezza.12anchor[200,125,120,20,15,14,13,12,11,10,5,0]ka,CHA-166Ma,H0sigillato e500000000000byte provvisori conservati.

## Evidenze e riproducibilità

Root write-once `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G46_CONSTRAINED_GAUGE_DATUM_NEW01`. REPORT.json e NUMERICAL_CAMPAIGN.csv contengono20invocazioni e gate; shard C/H/K/M/B/azioni/celle/facce e snapshot restart, log, affinità e risorse sono conservati integralmente. FINAL_GUARDS verifica20parent e source/runtime/processi. COMMITTED_G46_CODE_SNAPSHOTS conserva le revisioni; EXECUTED_STAGE_PROVENANCE distingue moduli caricati da successive modifiche sul disco. L’helper supervisor ereditato nomina G45 nel proprio CODE_IDENTITY; G46_EXECUTED_IDENTITY lega contratto/input/plugin e il contesto G46. Nessun nuovo provider numerico implicito.

Codice di chiusura sperimentale **`e19faa3c79cd4069ccb43c6c3e7d1fae0cf1db18`**. Il commit finale di consegna è identificato dalla storia Git di questo documento. Manifest, verifica indipendente e commit evidence LFS saranno legati nella ricevuta finale esterna al bundle sigillato; il bundle scientifico non viene modificato per aggiungere conferme di upload successive.

Comando read-only del contratto G15, su FAIR nell’ambiente esistente:

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_G36R2_DEV
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$PWD/experiments/r6_thermo_provider_pilot_v1:$PWD/src:$PWD"
python experiments/r6_thermo_provider_pilot_v1/g46_constrained_gauge_v1/scientific_design.py --validate-only
```

I runner originali sono write-once e non vanno rilanciati sulla root sigillata. I nuovi esperimenti richiedono root/contratto propri e il rispetto dei gate; nessun comando manuale è necessario per completare ciò che è già stato eseguito. Per l’archivio completo usare la ricevuta finale e il branch evidence LFS separato. Git LFS non era installato: usato un client privato verificato con gli hash della [release ufficiale3.8.1](https://github.com/git-lfs/git-lfs/releases/tag/v3.8.1), senza configurazioni globali o modifica ASPECT.

`architecture=A_FULL_MANTLE_ADAPTIVE`; D_024=D_025=ACTIVE; `physical_T1=null`; scientific_promotion=false; physical_acceptance=false; mantle_initial_state_admitted=false; mantle_provider_qualified=false; global_solve_authorized=false; WORLD_HISTORY_PRODUCTION_AUTHORIZED=false; material_assignments=0; M01_engine_executions=0; ARCANA_solves=0; additional_time_advance_years=0.

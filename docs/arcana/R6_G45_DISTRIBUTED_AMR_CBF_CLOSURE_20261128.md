# ARCANA WorldSim — G45: CBF distribuito e mesh adattive

28 novembre 2026, Europe/Rome. Esecuzione diretta **FAIR_WORKTREE / FAIR_EXTERNAL_EVIDENCE**, branch `r6/g36r2-fair-repair-20261127`, baseline G44 `2ff7f77a92365dd955d48fcdacfa8ee14d5d168a`. Autorità: handoff G45 letto integralmente, conservato nel bundle, e autorizzazione esplicita dell'autore per progettazione/build/test/campagna sintetica e pubblicazione. T0/G15: soltanto inventario documentale e progettuale.

## Esito: campagna conclusa, qualifica AMR globale non chiusa

**`G45_SYNTHETIC_QUALIFICATION_COMPLETED_WITH_GAUGE_AND_RESTART_BLOCKERS`**, `all_gates_pass=false`. Nessun requisito è stato allentato per ottenere PASS.

- **Uniforme distribuito PASS:** 16 casi a 1/2/4/8 rank, proprietà e copertura, ghost, replica nativa, reazioni indipendenti, lavoro, forze/momenti, datum e convergenza analitica. Replay dei casi G41/G42 compatibili, assert singleton originali conservate.
- **AMR:18casi convergenti superano algebra della traccia e bilanci**, con due risoluzioni 2.350/18.016 celle e 576/1.188 DOF hanging sul bordo. Il percorso forzato/datum usa il controllo separato senza sottrazione rotazionale post-solve. Quattro controlli idrostatici AMR con gauge originale falliscono la convergenza nativa. Il successo del kernel CBF non qualifica tutta la soluzione ASPECT o la politica di gauge.
- **Bloccati:** convergenza AMR con `net rotation`, parte della parità di velocità tra rank e dei test di datum; restart nativo e cambio-rank non qualificati. Il CBF nativo replica correttamente il proprio algoritmo ma fallisce il nostro screen di forza su specifici AMR.
- **9 negativi reali respinti**, 9 test mirati PASS (una deprecazione SciPy nel log),34 audit aggiuntivi dei moti rigidi/grafi dei vincoli PASS. Nessun solve fisico ARCANA, materiale assegnato o avanzamento storico.

| Gate | Esito |
|---|---|
| `AMR_condensed_trace_G45R1_unremoved_gauge` | `PASS_ALGEBRA_AND_EQUILIBRIUM_WITHIN_DECLARED_VARIANT_SCOPE` |
| `AMR_datum` | `BLOCKED_FROZEN_DATUM_OR_VELOCITY_THRESHOLD` |
| `AMR_full_velocity_rank_parity` | `BLOCKED_FROZEN_VELOCITY_PARITY_THRESHOLD` |
| `hydrostatic_AMR_controls` | `BLOCKED_NATIVE_NONLINEAR_CONVERGENCE` |
| `native_checkpoint_restart` | `BLOCKED_NO_AUTHORIZED_NATIVE_T0_CHECKPOINT` |
| `native_raw_AMR_force_conservation` | `FAIL_FROZEN_SCREEN_IN_RETAINED_CASES` |
| `original_net_rotation_forced_AMR` | `BLOCKED_NATIVE_NONLINEAR_CONVERGENCE` |
| `production_negative_tests` | `PASS` |
| `rank_change_restart` | `UNQUALIFIED` |
| `uniform_MPI_CBF` | `PASS` |

I 16 uniformi più18 AMR convergenti sono34 snapshot verificati: non sono 34 prove di un mantello fisico. La matrice originale di 38 casi non è dichiarata integralmente PASS. I rami dipendenti dal gauge originale sono stati fermati; il supplemento G45-R1 ha 22 tentativi, 18 campi convergenti e 4 blocchi idrostatici. In totale 44 invocazioni native con CASE_SPEC (inclusi setup falliti e negativo restart), oltre alla versione e ai build; nei log si contano 192 chiamate Stokes, distinte da solve ARCANA=0.

## Contratti congelati e identità

Contratto originario SHA256 **`9b3214d51e986e7317b04c57ccf3ecdc1bf6729861c3e1dfb00472d65ca548c7`**, commit91dc1c10, congelato prima di compilazione/esecuzioni. Supplemento numerico del gauge SHA256 **`4da69affd756263029c7b9d0888ef1e9addb2ed71a230254e1212b1dab8e9d6f`**, congelato prima del controllo. Entrambi i file originali rimangono identici; ogni retry e riadjudication ha identità distinta.

ASPECT3.2.0-pre, upstream30eb77ee5da186137d436dbad35c6cb3cab64b69, deal.II9.6.0, Trilinos13.2.0, p4est2.2.0, GCC11.4, OpenMPI4.1.2. Nuovo deployment privato G45 con `.text` degli otto eseguibili identico allo storico; nessun rebuild SIMD/ASPECT, nessuna reinstallazione. Plugin isolato release: `68c68fe8b0fd28cc6a9937314952947af0289b17ae609f718987fed564f6a474`; sorgente C++ `137d28936dfac340e0af36800746dc80c0a1bc743b8c7b66570a4c45d89945f3`. `COMMITTED_CODE_IDENTITY.json` e snapshot conservano le revisioni eseguite, incluse quelle fallite; i moduli Python già caricati non vengono confusi con successive revisioni sul disco.

SOURCE congelato901cbb4a38916190df6a881bb561b6558dd997dd, pulito. Verificati gli inventari completi dei 9 parent runtime/scientifici prima e dopo, più 3 archivi documentali G15/G30/G31. Runtime storico: 92749elementi metadata invariati, binari privati invariati, G41/G42 e supervisore G44 byte-identici alla baseline. 256identità PID/starttime osservate ricontrollate, nessun processo vivo corrispondente; tutti i RUN_EXIT hanno remaining vuoto. Nessuna terminazione di altri lavori.

## Metodo matematico e implementazione

Nuovo plugin separato, non rimozione delle assert G41/G42. Assembly solo su celle possedute, vettori MPI partizionati, `compress(add)` per i contributi, inserimento sui proprietari e import ghost prima della lettura. Output per-rank di celle/facce/DOF/constraint e snapshot ghost; nessun array globale completo replicato su ogni rank nel plugin. L'audit SciPy consolida invece dati globali sul coordinatore: è un verificatore indipendente limitato, non una promessa di scalabilità del postprocessing.

H contiene solo vincoli topologici hanging-node omogenei; condizioni fisiche Dirichlet/no-normal e gauge restano fuori da H per conservare le reazioni. Inomogeneità topologiche vengono respinte. Residuo r da tutte le celle; replica upstream distinta sulle sole celle di bordo. Massa full-space diagonale da GLL; sul supporto di traccia indipendente S si risolve **M_S=(Hᵀ diag(m) H)_S**, b_S=(Hᵀr)_S. CG distribuita matrix-free con Jacobi come solo precondizionatore; nessuna sostituzione della massa condensata con la sua diagonale. Traction completa=H x, valutata con la stessa geometria/quadratura. Risoluzione sparse indipendente e controllo SPD/simmetria confermano il solve.

Il riferimento del datum è la proiezione Galerkin di −10n nella stessa traccia vincolata, non una correzione del RHS o un fit di torque. Il confronto puntuale grezzo resta un diagnostico separato. Pressione idrostatica di riferimento sintetica 1000(1−r), contributo dinamico e totale sono distinti; i bilanci dei contributi di sola trazione non vengono impropriamente confrontati col corpo totale. Questo non fornisce pressione assoluta o reazione normale fisica di ARCANA.

Si verificano: copertura unica CellId/face/quadratura, conteggi globali e per-rank, normali/Jacobiani/orientazione, unico bordo top/bottom per cella, constraint closure, ghost-owner equality e grafi dei vincoli tra partizioni. Identità DOF da CellId/local-basis: supporti geometricamente coincidenti su AMR possono essere DOF distinti vincolati, quindi le coordinate da sole non bastano. Indici globali servono solo per join nello stesso run.

Lavoro virtuale con 5 campi casuali ammissibili e 6 tracce rigide, non solo potenza della soluzione quasi nulla. Traslazioni verificate separatamente per componente; rotazioni valutate nella loro rappresentazione discreta, con errore geometrico esplicito (non dichiarate esatte sulla mesh curva). Per l'identità aggiunta delle tracce rigide si usa estensione con coefficienti indipendenti interni nulli; il bilancio geometrico pieno forza/momento è uno screen distinto. Normalizzazione forza con integrale dei moduli di corpo+trazione, momento con ulteriore lunghezza1m sintetico, lavoro con scala di potenza assoluta. Mai divisione per un risultante quasi cancellato.

Soglie originali: parità CBF DOF/facce1e-10, replay lavoro1e-6, aggiunzione1e-8, weak balance forzato e forza/momento1e-4, datum/area0.005, parità tra rank1e-4. Nuovi criteri di vincolo/SPD/CG sono nel contratto; tolleranze Stokes e nonlinearità originali mantenute. Il test oracle Q2 con pesi3/8,3/4,−1/8 dimostra che la semplice divisione diagonale del sistema condensato fallisce il residuo, mentre il sistema completo conserva il lavoro.

## Risultati e limiti misurati

Caso AMR coarse a 4 rank: errore di forza nativo **0.00262224685**, vincolato **6.38059257e-11**; errore di momento vincolato **8.85671524e-10**. L'evidenza dimostra un controesempio allo screen del percorso raw per questi casi, non un verdetto universale sull'implementazione upstream o una nuova autorità fisica.

Il gauge originale forzato si ferma a residuo nonlineare circa 2.07353e-4 contro 1e-6, pur uscendo dal processo con0. L'audit algebrico iniziale era PASS solo nel suo scope; `ORIGINAL_AMR_NATIVE_ADJUDICATION.json` ne impedisce la promozione. Il controllo separato cambia **solo** `Remove nullspace: net rotation → empty`; verifica del diff conservata. Converge alla tolleranza originale, ma lascia esplicitamente la rotazione non rimossa. L'ordine upstream distribuisce i vincoli e poi applica la correzione rotazionale; il controllo sostiene un problema di compatibilità discreta, senza provare una causa unica per ogni mesh/gauge.

Parità di velocità AMR: 2confronti falliti su12; non sono stati corretti proiettando/fittando la velocità. La trazione può concordare mentre il rappresentante di velocità non supera il gate.

| Confronto AMR fallito | Differenze relative: u, CBF nativo, r, m, t vincolata, t idro | Soglia |
|---|---|---:|
| `G45R1_forced_l3_a1_p8_unremoved_NEW01` | 0.00011592537, 2.1642734e-08, 6.0110204e-08, 1.9147951e-18, 2.2289376e-08, 1.4102961e-16 | 0.0001 |
| `G45R1_datum_l3_a1_p4_unremoved_NEW01` | 0.00015213104, 3.5545744e-08, 9.8071718e-08, 1.3176653e-18, 3.6607509e-08, 1.3917505e-16 | 0.0001 |

Datum AMR: 5coppie su6non superano tutti i criteri. Coarse circa0.006273>0.005 sul riferimento di trazione proiettato; fine a 4 rank circa1.8129e-4>1e-4 sull'invarianza di velocità. La dissipazione rimane molto più stabile. Non si modifica la soglia per chiamarlo PASS; quadratura/identità di divergenza e compatibilità del gauge richiedono una successiva indagine separata.

| Caso +10 Pa | Errore t rispetto a −10n proiettato | Differenza u | Differenza dissipazione | Esito |
|---|---:|---:|---:|---|
| `G45R1_datum_l2_a1_p1_unremoved_NEW01` | 0.0062731828 | 5.5527115e-07 | 2.0188728e-10 | False |
| `G45R1_datum_l2_a1_p2_unremoved_NEW01` | 0.0062731856 | 9.0094478e-07 | 2.6692104e-10 | False |
| `G45R1_datum_l2_a1_p4_unremoved_NEW01` | 0.0062731832 | 9.2090355e-07 | 3.1028657e-10 | False |
| `G45R1_datum_l2_a1_p8_unremoved_NEW01` | 0.0062731836 | 7.6779115e-07 | 2.7848213e-10 | False |
| `G45R1_datum_l3_a1_p1_unremoved_NEW01` | 0.0018065313 | 4.8194138e-05 | 2.7466163e-10 | True |
| `G45R1_datum_l3_a1_p4_unremoved_NEW01` | 0.0018061378 | 0.00018129044 | 2.5562996e-11 | False |

Convergenza HollowSphere con velocità analitiche prescritte, distinta dal free-slip: tutti gli errori diminuiscono. Numeri fine/coarse, non certificazione asintotica dell'ordine o costo del mantello completo:

| Mesh | Rank | Fine/coarse uL1 | uL2 | pL1 | pL2 | topografiaL2 |
|---|---:|---:|---:|---:|---:|---:|
| uniforme | 1 | 0.126681 | 0.137166 | 0.114174 | 0.118573 | 0.116995 |
| adattiva | 1 | 0.123028 | 0.139818 | 0.080564 | 0.105662 | 0.410409 |
| adattiva | 4 | 0.123027 | 0.139818 | 0.080564 | 0.105662 | 0.410409 |

Tabella delle invocazioni native; i PASS locali di algebra/bilanci non sostituiscono i gate globali sopra. CSV completo `NUMERICAL_CAMPAIGN.csv`; iterazioni, errori, dissipazione, lavori dei due bordi, tensioni tangenziali, H e masse sono nei report/shard per caso.

| Caso | Gauge | Celle | DOF velocità | DOF hanging bordo | NL converge | Parità CBF nativo | Errore forza nativo / vincolato | PSS GiB | Wall s |
|---|---|---:|---:|---:|---|---:|---|---:|---:|
| `G45R1_datum_l2_a1_p1_unremoved_NEW01` | unremoved | 2350 | 64680 | 576 | True | 3.89e-16 | 0.00272 / 7.45e-11 | 0.277 | 15.069 |
| `G45R1_datum_l2_a1_p2_unremoved_NEW01` | unremoved | 2350 | 64680 | 576 | True | 3.91e-16 | 0.00272 / 7.45e-11 | 0.352 | 10.357 |
| `G45R1_datum_l2_a1_p4_unremoved_NEW01` | unremoved | 2350 | 64680 | 576 | True | 3.87e-16 | 0.00272 / 7.45e-11 | 0.402 | 6.764 |
| `G45R1_datum_l2_a1_p8_unremoved_NEW01` | unremoved | 2350 | 64680 | 576 | True | 4e-16 | 0.00272 / 7.45e-11 | 0.490 | 4.670 |
| `G45R1_datum_l3_a1_p1_unremoved_NEW01` | unremoved | 18016 | 465087 | 1188 | True | 3.88e-16 | 0.00125 / 3.86e-13 | 0.766 | 168.736 |
| `G45R1_datum_l3_a1_p4_unremoved_NEW01` | unremoved | 18016 | 465087 | 1188 | True | 3.93e-16 | 0.00125 / 3.24e-13 | 1.295 | 47.334 |
| `G45R1_forced_l2_a1_p1_unremoved_NEW01` | unremoved | 2350 | 64680 | 576 | True | 3.88e-16 | 0.00262 / 6.38e-11 | 0.277 | 15.098 |
| `G45R1_forced_l2_a1_p2_unremoved_NEW01` | unremoved | 2350 | 64680 | 576 | True | 3.79e-16 | 0.00262 / 6.38e-11 | 0.319 | 10.352 |
| `G45R1_forced_l2_a1_p4_unremoved_NEW01` | unremoved | 2350 | 64680 | 576 | True | 3.87e-16 | 0.00262 / 6.38e-11 | 0.383 | 6.758 |
| `G45R1_forced_l2_a1_p8_unremoved_NEW01` | unremoved | 2350 | 64680 | 576 | True | 3.89e-16 | 0.00262 / 6.38e-11 | 0.490 | 4.129 |
| `G45R1_forced_l3_a1_p1_unremoved_NEW01` | unremoved | 18016 | 465087 | 1188 | True | 3.88e-16 | 0.00121 / 2.69e-13 | 0.766 | 128.138 |
| `G45R1_forced_l3_a1_p2_unremoved_NEW01` | unremoved | 18016 | 465087 | 1188 | True | 3.87e-16 | 0.00121 / 2.86e-13 | 1.042 | 82.750 |
| `G45R1_forced_l3_a1_p4_unremoved_NEW01` | unremoved | 18016 | 465087 | 1188 | True | 3.88e-16 | 0.00121 / 2.89e-13 | 1.295 | 50.462 |
| `G45R1_forced_l3_a1_p8_unremoved_NEW01` | unremoved | 18016 | 465087 | 1188 | True | 3.86e-16 | 0.00121 / 2.64e-13 | 1.601 | 26.088 |
| `analytic_l2_a0_p1_NEW01` | original | — | — | — | — | — | — / — | 0.023 | 1.675 |
| `analytic_l2_a0_p1_NEW01_RETRY2` | original | 768 | 20790 | 0 | True | 3.86e-16 | 4.12e-05 / 4.12e-05 | 0.217 | 2.270 |
| `analytic_l2_a1_p1_NEW01` | original | 2350 | 64680 | 576 | True | 3.89e-16 | 0.00261 / 3.22e-05 | 0.272 | 7.841 |
| `analytic_l2_a1_p4_NEW01` | original | 2350 | 64680 | 576 | True | 3.83e-16 | 0.00261 / 3.22e-05 | 0.395 | 3.695 |
| `analytic_l3_a0_p1_NEW01` | original | 6144 | 156774 | 0 | True | 3.94e-16 | 1.26e-05 / 1.26e-05 | 0.362 | 10.661 |
| `analytic_l3_a1_p1_NEW01` | original | 18016 | 465087 | 1188 | True | 3.9e-16 | 0.0012 / 4.72e-06 | 0.720 | 52.118 |
| `analytic_l3_a1_p4_NEW01` | original | 18016 | 465087 | 1188 | True | 3.86e-16 | 0.0012 / 4.72e-06 | 1.286 | 19.688 |
| `datum_l3_a0_p1_NEW01` | original | 6144 | 156774 | 0 | True | 3.93e-16 | 8.01e-13 / 8.01e-13 | 0.375 | 18.061 |
| `datum_l3_a0_p2_NEW01` | original | 6144 | 156774 | 0 | True | 3.92e-16 | 2.77e-13 / 2.77e-13 | 0.521 | 10.452 |
| `datum_l3_a0_p4_NEW01` | original | 6144 | 156774 | 0 | True | 3.87e-16 | 1.2e-12 / 1.2e-12 | 0.630 | 6.189 |
| `datum_l3_a0_p8_NEW01` | original | 6144 | 156774 | 0 | True | 3.85e-16 | 3.21e-13 / 3.21e-13 | 0.616 | 3.454 |
| `forced_l2_a0_p1_NEW01` | original | 768 | 20790 | 0 | True | 3.94e-16 | 5.16e-14 / 5.15e-14 | 0.218 | 2.819 |
| `forced_l2_a0_p4_NEW01` | original | 768 | 20790 | 0 | True | 3.91e-16 | 6.84e-14 / 6.84e-14 | 0.287 | 1.805 |
| `forced_l2_a1_p1_NEW01` | original | — | — | — | True | — | — / — | 0.219 | 5.205 |
| `forced_l2_a1_p1_NEW01_RETRY2` | original | 2350 | 64680 | 576 | False | 3.82e-16 | 0.00262 / 4.86e-08 | 0.278 | 91.368 |
| `forced_l2_a1_p2_NEW01` | original | 2350 | 64680 | 576 | False | 3.93e-16 | 0.00262 / 4.86e-08 | 0.353 | 47.644 |
| `forced_l2_a1_p4_NEW01` | original | 2350 | 64680 | 576 | False | 3.89e-16 | 0.00262 / 4.86e-08 | 0.383 | 30.116 |
| `forced_l3_a0_p1_NEW01` | original | 6144 | 156774 | 0 | True | 3.89e-16 | 1.92e-12 / 1.92e-12 | 0.375 | 18.065 |
| `forced_l3_a0_p2_NEW01` | original | 6144 | 156774 | 0 | True | 3.88e-16 | 3.17e-13 / 3.17e-13 | 0.521 | 10.504 |
| `forced_l3_a0_p4_NEW01` | original | 6144 | 156774 | 0 | True | 3.89e-16 | 8.22e-13 / 8.22e-13 | 0.502 | 6.169 |
| `forced_l3_a0_p8_NEW01` | original | 6144 | 156774 | 0 | True | 3.8e-16 | 2.11e-13 / 2.11e-13 | 0.616 | 3.458 |
| `hydro_l2_a1_p1_NEW01` | original | — | — | — | False | — | — / — | 0.278 | 64.768 |
| `hydro_l2_a1_p2_NEW01` | original | — | — | — | False | — | — / — | 0.343 | 41.890 |
| `hydro_l2_a1_p4_NEW01` | original | — | — | — | False | — | — / — | 0.402 | 27.049 |
| `hydro_l2_a1_p8_NEW01` | original | — | — | — | False | — | — / — | 0.517 | 15.979 |
| `hydro_l3_a0_p1_NEW01` | original | 6144 | 156774 | 0 | True | 3.87e-16 | 1.23e-13 / 1.23e-13 | 0.370 | 19.188 |
| `hydro_l3_a0_p2_NEW01` | original | 6144 | 156774 | 0 | True | 3.91e-16 | 1.38e-14 / 1.38e-14 | 0.521 | 9.883 |
| `hydro_l3_a0_p4_NEW01` | original | 6144 | 156774 | 0 | True | 3.87e-16 | 1.64e-13 / 1.64e-13 | 0.576 | 5.599 |
| `hydro_l3_a0_p8_NEW01` | original | 6144 | 156774 | 0 | True | 3.99e-16 | 1.9e-13 / 1.91e-13 | 0.620 | 3.463 |
| `negative_invalid_restart_NEW01` | original | — | — | — | — | — | — / — | 0.023 | 1.677 |

## Negativi, restart e tentativi conservati

Baseline adattiva convergente a 4 rank; copie modificate separate con riferimenti interni al bundle e sostituzione atomica dei file modificati. Hash della baseline identici prima/dopo. Si invoca lo stesso valutatore di produzione; per parent e restart si usano verificatore originale e ASPECT reale. Il negativo datum usa il controllo uniforme positivo, separatamente dai datum AMR bloccati.

| Negativo | Gate di produzione | Respinto |
|---|---|---|
| inverted_orientation | FACE_ORIENTATION | True |
| duplicate_face | FACE_COVERAGE | True |
| dropped_face | FACE_COVERAGE | True |
| wrong_sign | INDEPENDENT_TRACE_SOLVE | True |
| omitted_constraint | CONSTRAINT_COVERAGE | True |
| stale_ghost | STALE_GHOST | True |
| wrong_datum | DATUM_GAUGE_SHIFT | True |
| tampered_parent | BUNDLE:tampered_parent | True |
| invalid_native_restart | ASPECT actual missing-checkpoint rejection | True |

Restart: **`BLOCKED_NO_AUTHORIZED_NATIVE_T0_CHECKPOINT`**. Il sorgente pinned impone passo positivo e chiama advance_time prima di maybe_write_checkpoint. Il contratto non autorizza un intervallo sintetico nonzero; non sono stati creati checkpoint a tempo positivo né inventati PASS da export/readback. Stesso-rank e cambio-rank restano da qualificare. Il vero avvio `Resume computation=true` senza checkpoint è respinto dal provider, exit1, senza residui.

Fallimenti conservati: buildNEW01 (API norm del tensore simmetrico; corretta contrazione equivalente), setup analiticoNEW01 (postprocessor duplicato, prima del solve), primo AMRNEW01 con0hanging (fraction0 cancellava i flag upstream; corretto solo l'enablement, regola geometrica invariata), tre AMR forzati con gauge originale e quattro idrostatici non convergenti, confronti rank/datum falliti, primo verificatore di identità basato sulle sole coordinate (corretto usando incidenza topologica). Nessun report precedente riscritto. Anche lo stop mirato del solo controller, dopo la fine del job supervisionato, ha ricevute pidfd.

## Risorse, provenienza e riproducibilità

Runtime G44 riusato: ob1/self,vader/single_copy_mechanism=none, OMP/BLAS/MKL=1, 1/2/4/8 rank su core fisici distribuiti sui 4 NUMA. Nessun nuovo benchmark 64/128 rank o rebuild SIMD. Memoria PSS nativa massima osservata **1.601GiB**, soglia campionata 16 GiB; riserva max(64GiB,25% MemAvailable iniziale), stop per swap >64 MiB, 600 s/caso. Intervallo richiesto 0,5 s, gap massimo osservato **0.755s**. PSS/RSS campionate, RSS duplica pagine condivise; nessun hard cap aggregato o per-rank rivendicato. Coordinatore SciPy fuori dall'albero nativo supervisionato, limite di scalabilità dichiarato. Negativi offline su CPU 63 libera; il negativo MPI attende la fine della matrice. Nodo condiviso, nessuna esclusività presunta.

Bundle **`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G45_DISTRIBUTED_AMR_CBF_20261128_NEW01`**, MANIFEST SHA256 **`440c7366c47519a87124f6b6ccaf43939ef63740b3b54a7791cba8e1d26e6074`**, 4641file. Config argv/ambiente, input, plugin/ABI, stdout/stderr, campioni, ownership, mesh/constraint manifest, codice e failure sono conservati fuori dal branch del codice. Le firme code stage e le parentesi di scope evitano equivalenze tra exit0, algebra, convergenza, fisica e produzione.

Commit di chiusura codice **ce87600519b150ee213db4b5905183ace63429c5**; commit di consegna documentale da `git log -1 --format=%H -- docs/arcana/R6_G45_DISTRIBUTED_AMR_CBF_CLOSURE_20261128.md`. Implementazioni dal più recente:

```text
ce87600519b150ee213db4b5905183ace63429c5 Verify G45 guards before sealing derived closure artifacts
e253c03e6a4392858d68779700bff129364fff68 Provide isolated single-case replay from a fully verified sealed G45 parent
a6b3105849775d62945a29e9f6bbbdfc874f869a Identify constrained coincident supports by CellId and local basis, not coordinates alone
10c9afe2975d959a679045fdd71a940da2a5b3a5 Run independent negative audits on a spare core and serialize native restart rejection
3d6f33d23e00a7f4176274a5fbd5337c7c8df9da Bind AMR constraint graph identities across partitions and preserve all explicit closure blockers
a483a4695ddffe0e698006fb7a9d541ac47da4ae Add independent component-wise rigid translations, rotations and virtual-trace work audit
17d787403051cf3905264bae0a3d4ddb65f9863e Retain failed fine-rank velocity parity and complete independent G45 controls without relaxing gates
334b937c9eea7efeb2ac1422fe0d6c924c78a576 Verify negative overlays never mutate their accepted AMR baseline
a21bba25cec84f5759ebcb31d6aecfd4c8b51556 Test rejection of native solver warnings and retain original AMR convergence adjudication
2eb04f2e7570c6390be8da52e6285523ad87dcd6 Implement genuine production negatives and projected datum reference; bind native zero-time restart blocker
863c94e00767329118d4a02e66cc0324080dc5d0 Freeze separate AMR gauge control and enforce native nonlinear convergence without tolerance changes
63a8fe53bfc44b8545a3930c294ea5abae70a0d0 Enable geometric AMR flags after upstream fraction guard, retain rejected uniform attempt
8aaebfb62232dcde1bc8f804c86d6cabbf6c7f9f Record G45 uniform distributed gate and start frozen adaptive matrix
24d46d5c96f25413be6acf1ed58d7588b8edb379 Preserve failed analytic setup and avoid duplicate postprocessors or overridden AMR strategy
8f89e98d186db36a010b741e60f73f8459087410 Add documentary source-bound full mantle T0 and corrected G15 inventory
eef292b46c280de0855be7260db4da1137d24831 Add resumable frozen G45 matrix, rank parity and gauge/convergence analysis
843a9621432272eaea4f809d9241fc9f35bcb3aa Add independent constrained-trace oracle and fix symmetric strain contraction API
9ac2405fc7b905be2118c4116e7a91bb3b55460f Add isolated G45 native build and pinned synthetic case runner
89b3f24297083cf0816a1131a18b5264c4edad25 Implement separate distributed topology-condensed CBF trace plugin
91dc1c10ea061879e2b33f17be63aa12ab6b51ec Freeze G45 synthetic distributed AMR CBF acceptance contract before runs
```

Comandi di audit read-only:

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_G36R2_DEV
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$PWD/experiments/r6_thermo_provider_pilot_v1:$PWD/src:$PWD"
python - <<'AUDIT'
from pathlib import Path
import arcana_g38_aspect_hollow_sphere as g38
m=g38.verified_bundle(Path('/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G45_DISTRIBUTED_AMR_CBF_20261128_NEW01'),'440c7366c47519a87124f6b6ccaf43939ef63740b3b54a7791cba8e1d26e6074')
print(m['status'],len(m['files']))
AUDIT
```

Replay isolato di un singolo caso, soltanto in una nuova root. Comando fornito per riproducibilità; il wrapper ha CLI verificata e usa gli stessi helper eseguiti, ma non è stato rilanciato inutilmente sull'intera campagna. Il suo PASS vale per quel caso, non per i blocker trasversali:

```bash
python experiments/r6_thermo_provider_pilot_v1/arcana_g45_replay_case.py \
  --parent /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G45_DISTRIBUTED_AMR_CBF_20261128_NEW01 \
  --manifest-sha256 440c7366c47519a87124f6b6ccaf43939ef63740b3b54a7791cba8e1d26e6074 \
  --case G45R1_forced_l2_a1_p4_unremoved_NEW01 \
  --output /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G45_REPLAY_UNIQUE_NEW01
```

I runner di campagna originari puntano alla root storica write-once e non vanno rilanciati sul bundle sigillato. Il replayer ricontrolla l'inventario completo del parent prima/dopo e copia parametri/plugin in un output fresco. Nessun comando manuale è richiesto all'autore per completare il lavoro già eseguito.

## Autorità T0/G15 e roadmap verso WORLD_HISTORY

[Inventario documentale completo](R6_G45_T0_G15_AUTHORITY_INVENTORY_20261128.md), JSON source-bound nel bundle. Sono state lette 41 fonti citate;9 parent G45 e3 archivi G15/G30/G31 verificati integralmente. Il manifest iniziale fornisce già raggio di progetto di 6.371.000 m e gravità superficiale di 9,82 m/s² come baseline analoga terrestre dichiarata; non determinano CMB, massa/gravitazione radiale o EOS. G43 fornisce termica condizionale 0–300 km, quasi radiale sotto LAB, zero nodi ammessi come stato fisico mantellare3D. Composizione/acqua/fasi, pressione assoluta, reologia, flussi/riscaldamento, inizializzazione/perturbazioni/spin-up e incertezza richiedono autorità distinte; nessun UNKNOWN riempito con zero. M01 non selezionato né eseguito.

B6K_INTERIOR è geometria plate-local/candidato isolato, non uno stato mantellare.34/35artifact corrispondono al vecchio manifest; lo script corrente differiva già alla consegna G44. Recuperati i byte legati al manifest dal commit **406013da9f761d5581f889470c3626f89024f2b7**, senza sostituire sorgenti o rieseguire B6K. Questo riconcilia la provenienza, non promuove il candidato o la versione corrente a runtime fisico qualificato.

G15: recuperati policy, indice, checkpoint e input originali112→162anni; nessuna nuova traiettoria eseguita. La futura riqualifica deve ripartire dal primo stato autorevole non contaminato dalla vecchia metrica, usare slopey/sinA e CSR/band corretti, halving/restart, massa/energia e feedback termica/stress/dissipazione. Gli endpoint G30/G31 e la chiusura documentale G18 non certificano162anni corretti.

Prossimo task proposto: contratto sintetico separato per gauge rotazionale compatibile con H/bordi/operatori e per datum/divergenza discreta, con negativi, convergenza e parità8rank fissati prima dei run. Nessun fit di torque, RHS correction o pin arbitrario. Il restart richiede una decisione esplicita su un intervallo sintetico nonzero o un'API nativa di snapshot a t0 verificata; non si aggirano il sorgente congelato o il runtime storico.

Poi: trasferimento conservativo su mesh SHELLS/ASPECT reali e autorità della reazione normale; stato volumetrico T0 source-bound; G15 corretto con restart. D-024 mantiene il minimo sottosistema fisicamente chiuso come avvio, senza un gate universale di tutti i tool. Physical T1 resta una tappa: obiettivo 210 Ma→0 ka, ultimi 200 ka inclusi, risorse naturali/Deep, clima/idrologia/suoli, flora/fauna, popolazioni/insediamenti/civiltà; HistoryStore causale con checkpoint/stati/eventi/provenance, query regione/epoca/processo e raffinamento con lineage/convergenza/incertezza.12 anchor,CHA-1/H0 e budget 500 GB provvisorio preservati.

`architecture=A_FULL_MANTLE_ADAPTIVE`, D-024/D-025 ACTIVE, `physical_T1=null`, `scientific_promotion=false`, `physical_acceptance=false`, `mantle_initial_state_admitted=false`, `mantle_provider_qualified=false`, `global_solve_authorized=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; material_assignments0, ARCANA_solves0, additional_time_advance_years0.

Verifiche indipendenti dopo il sigillo: inventario completo dei 4.641 file ricontrollato dal verificatore storico in `R6_G45_DELIVERY_VALIDATION_NEW01`, manifest `db63a6fa6937d9288386869e20be832cac3b58fce8c6a4e03fb7ae8f56a490dd`. Ulteriore replay read-only delle 14 statistiche uniformi G41 con la normalizzazione storica esatta `max(abs(reference),1e-10)` e soglia stretta 1e-6: tutti PASS, massimo 3.247671e-7. Il primo report usava il denominatore max(abs(reference),1); il runner finale ripristina quello storico, senza nuovi solve né modifica delle evidenze sigillate. Ricevuta separata `R6_G45_UNIFORM_LEGACY_REPLAY_VALIDATION_NEW01`, manifest `4cf9aead330cbadfb4866a88376b6f46654e4cf558ad638442f03065a6033691`. Questi controlli non cambiano i gate AMR bloccati.

# THERMAL 1D EXPLORE — seconda iterazione

2026-11-02. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`THERMAL_1D_EXPLORE2=PASS_RESOLVED_SHORT_TIME_INTERFACE_STUDY`

**Sì al successivo prototipo di collegamento con stato/cronologia**, nel perimetro
termico sperimentale e con risoluzione esplicita. Il metodo mostra ordine circa2
quando gli strati transitori sono risolti. Le griglie uniformi73/145/289, da sole,
**non** dimostrano convergenza sul transitorio di10anni ai bordi. Questo limite
resta parte del risultato, non viene cancellato dal PASS delle prove risolte.
Nessuna validazione geologica, checkpoint/B0 o cronologia lunga viene dichiarata.

## Versione, dati e scenario

Nuovo namespace `experiments/thermal_1d_explore_v2`; v1, provider originale e R1
immutati. Legge e metodo d'interfaccia restano quelli della prima iterazione:
C_i=int(rho Cp dz), S_i=int(A dz), g_f=1/int(dz/k); flusso condiviso
Q_f=g_f(T_destra−T_sinistra), positivo verso l'alto. Il contatto viene integrato
esattamente per tratti sia nei volumi duali sia nelle resistenze. Nessun clipping
delle temperature o riscalamento energetico; i min/max usati nel codice per le
intersezioni geometriche non sono un limiter degli stock termici.

Profili iniziali valutati direttamente dai polinomi PRE_ORBDATA originali,
non interpolati da osservazioni nuove. Materiali nominali invariati: crosta
k2,5,rho2800,Cp1000,A8e-7; mantello k3,3,rho3300,Cp1200,A2e-8 nelle unità SI.
Bordi Dirichlet alle temperature T0 originali, geometria fissa e durata10anni
in ogni traiettoria. Nessun moto o trasporto laterale. I flussi superficiali sono
dati iniziali, non bordi Neumann aggiuntivi. Epoca nominale T0:210Ma.

| Colonna PRE | Identità e geometria | Stato termico realmente diverso |
| --- | --- | --- |
| R091/C028, nodo32792 | Moho28km, base80km | q_s85mW/m², Tbase1671,7714K, tendenza−3,953455e-6K/anno |
| R013/C139, nodo4823 | Moho40km, base200km | q_s45mW/m², Tbase1721,7544K, tendenza+6,184935e-7K/anno |

La seconda è la prima colonna continentale presente nel DAT con rate dichiarato
e q_s<60mW/m²: regola deterministica, non selezione sui risultati. Tutti i suoi
valori vengono dal record originale, con flag di presenza conservati. C029 non è
rieseguita come ambiente distinto. I parametri sono riferimenti autoriali ARCANA,
non misure osservative locali; nessun UNKNOWN è riempito.

## Raffinamento, oracoli e separazione degli errori

Intervalli originali suddivisi×1/×2/×4:73/145/289nodi,24/48intervalli iniziali nei
due materiali, Moho sempre nodo esatto. Per C028 preserva il contatto a28km;
per la nuova colonna usa il suo contatto40km. Su ciascuna griglia:16/32/64Euler
passi, confronto con ODE affine assemblata separatamente tramite intersezioni
scalari e propagata con esponenziale sparso sugli incrementi. Controverifica
con esponenziale denso: massimo scarto2,04e-20K. Questo isola l'errore temporale;
non attribuisce all'esponenziale la precisione spaziale del continuo.

Riferimento continuo indipendente nel breve tempo: il profilo PRE quadratico
per strato ha rate iniziale uniforme r. Senza influenza dei bordi sarebbe
T0+r*t. La correzione Dirichlet semi-infinita è −r I(d,kappa,t), con
I=(t+d²/(2kappa))erfc(d/(2sqrt(kappa*t)))
−d sqrt(t/(pi*kappa)) exp(−d²/(4kappa*t)). Si sommano i contributi dei due bordi,
con le rispettive diffusività. L'integrale equivalente
I=int_0^t erfc(d/(2sqrt(kappa*s)))ds è verificato con quadratura indipendente:
scarto massimo negli incrementi4,4e-21K sui punti controllati.

Questo è un riferimento asintotico di breve tempo, non una soluzione globale
esatta a qualsiasi durata: in10anni le distanze dai bordi al contatto sono migliaia
di lunghezze diffusive; le interazioni remote sono numericamente trascurabili.
Non si estende questa approssimazione a durate lunghe o a colonne sottili.

| C028,10anni |73nodi |145nodi |289nodi |
| --- | ---: | ---: | ---: |
| Errore spaziale L2 K, tempo esatto discreto |7,140e-10 |2,018e-9 |5,699e-9 |
| Errore spaziale Linf K |4,429e-9 |1,771e-8 |7,070e-8 |
| Errore temporale L2 K,64passi |1,211e-11 |3,206e-11 |8,878e-11 |

Le norme sono pesate con le lunghezze dei volumi duali. Gli errori spaziali
**crescono** in questo regime sottorisolto: il primo nodo si avvicina al bordo,
ma resta lontano rispetto allo strato diffusivo (sqrt(kappa*t)≈17m). Il kernel
diffonde numericamente la risposta del bordo ai primi nodi prima di risolverne
la struttura. Non è un difetto residuo del contatto Moho, né un errore temporale.
Per la colonna fredda L2 spaziale cresce3,015e-11→8,527e-11→2,410e-10K.

Ulteriori griglie diagnostiche aggiungono nodi nei primi/ultimi256m con passi
4/2/1m, mantenendo il resto della289 e il contatto originale:417/545/801nodi.
Stessi polinomi e parametri; nessuna nuova informazione fisica viene inventata.

| Strati Dirichlet risolti |4m |2m |1m |
| --- | ---: | ---: | ---: |
| C028 Linf spaziale K |4,832e-8 |1,210e-8 |3,031e-9 |
| R013/C139 Linf spaziale K |7,559e-9 |1,893e-9 |4,741e-10 |

Ordini L2/Linf1,9972–1,9995 sulle due colonne. Sono misure spaziali con propagazione
semidiscreta; nessun errore Euler viene mescolato a queste norme. Le evoluzioni
Euler reali aggiuntive su C028 usano CFL≈0,5 e≈0,25:71/142,282/564,1128/2256passi.
A1m gli errori temporali Linf4,239e-9/2,122e-9K si dimezzano, come richiesto da
Euler. Temperature sempre positive, bordi esattamente costanti. Le prove nominali
più grossolane arrivano invece vicino al rumore di accumulo; non si ricava un
ordine temporale universale dai rapporti dominati dall'arrotondamento.

## Interfaccia e sensibilità

Su tutte le griglie nominali la tendenza iniziale interna, Moho incluso,
corrisponde al rate PRE entro5,33e-24K/s. I flussi ricostruiti unilateralmente al
contatto iniziale coincidono con PRE entro circa1e-14W/m². I flussi sulle facce
adiacenti differiscono fisicamente per sorgenti/accumulo; il loro scarto tende a
zero avvicinandosi al contatto. Per C028 i valori finali adiacenti passano da
0,0534495/0,0524987W/m² a73nodi a0,0529461/0,0527084W/m² a289nodi, attorno al
flusso continuo iniziale0,05277825W/m². Nessuna uguaglianza artificiale imposta.

Sensibilità C028, un parametro alla volta agli estremi **già dichiarati**:
k_C2/3W/(mK), Cp_C800/1200J/(kgK), A_C4e-7/1,2e-6W/m³, A_M0/4e-8W/m³.
Fonte: campi sensitivity_range del contratto materiale PRE. Non si varia una
kappa indipendente. Profilo iniziale e bordi restano nominali: è una perturbazione
istantanea dei coefficienti/sorgenti, **non** una nuova inizializzazione equilibrata
o un'incertezza probabilistica. Il valore0 di A_M è qui un estremo autorizzato,
non un riempimento di valore mancante.

Su289nodi, differenza massima dal nominale dopo10anni: Cp_C800/1200,
9,884e-6/6,589e-6K; A_C estremi4,508e-5K; A_M estremi1,594e-6K. Per k_C la
variazione causa un salto iniziale del flusso al Moho: la risposta deve risolvere
un altro strato diffusivo. La289uniforme stima solo circa±0,00353K e sottostima
fortemente l'effetto locale. Non viene presentata come sensitività convergente.

Risoluzione aggiuntiva±256m attorno al Moho,4/2/1m, riferimento esponenziale:

| k_C | Effetto Moho a4/2/1m K | Riferimento indipendente K |
| --- | --- | ---: |
|2 |+0,0352404 /+0,0353488 /+0,0353757 |+0,035384665 |
|3 |−0,0323855 /−0,0324696 /−0,0324905 |−0,032497424 |

Riferimento a due semispazi con effusività e=sqrt(k*rho*Cp):
deltaT_M=2sqrt(t/pi)(q_M−q_C)/(e_C+e_M)
+t(e_C*r_C+e_M*r_M)/(e_C+e_M). Si sottrae il nominale r0*t.
È derivato dai gradienti e curvature PRE ai due lati, non adattato ai risultati.
Esclude i bordi remoti nel medesimo breve intervallo. Errori al Moho con ordine
2,0014–2,0067; a1m residui8,96e-6K e6,96e-6K. Queste prove di sensibilità
localmente risolte usano l'esponenziale semidiscreto, non una campagna Euler
aggiuntiva. Gli array e i due tipi di propagazione sono etichettati separatamente.

## Energia e costo

Evolvono solo i volumi interni: deltaE=dt(Q_base_interna−Q_top_interna+sum S_i).
I mezzi volumi Dirichlet sono serbatoi esclusi dall'energia evoluta. Tabelle/array
conservano separatamente produzione interna, dei serbatoi e totale. In C028 il
totale resta0,02344W/m²; a289nodi interno0,023320625, serbatoi0,000119375W/m².
Per la colonna fredda il totale è0,0352W/m². Nessuna energia viene rinormalizzata.

A289/64passi residui cumulativi−1,01346J/m² per C028 e−2,98152J/m² per la fredda;
scambi netti−1,12030e7 e+4,59766e6J/m². Nei controlli risolti il cumulativo raggiunge
20,68195J/m² su2256passi; il massimo per passo resta entro il budget proporzionale
agli stock del kernel. È arrotondamento misurato nell'accumulo di grandi temperature,
non conservazione esatta o precisione energetica universale. Prima di molte
continuazioni conviene adottare stato compensato/incrementi e ricontrollarne il
restart; questo lavoro non modifica la versione eseguita per nascondere il residuo.

Campagna principale finale:0,67s wall,0,57s user+0,08s system,RSS133120KiB
(130MiB). Controlli risolti aggiuntivi:1,81s wall,0,78s user+0,11s system,
RSS144908KiB(141,51MiB). I massimi non sono sommati. Costi includono riferimenti,
array e import; wall interno0,448/0,451s sovrapposto, non sommabile ai totali.
BLAS/OMP/MKL1thread; nessuna installazione o limite artificiale RAM.18traiettorie
nominali,16sensibilità Euler,6controlli Euler risolti; riferimenti separati.

Un primo lancio si è fermato nel driver per sottrazione di vettori con/senza i
due nodi Dirichlet. Conservati codice/log/exit; la correzione aggiunge i due
incrementi di bordo nulli al riferimento. Kernel, materiali e soglie invariati;
tutti i risultati riassunti provengono da run02 ed extra01. Il postprocessing
legge soltanto array salvati; verifica40traiettorie, positività, bordi e ledger.

## Collegamento con stato e cronologia

Metodo adatto a una successiva **integrazione sperimentale limitata**, mantenendo
supporto, nodi/volumi, materiali, posizione del contatto, condizioni al bordo,
temperature, clock, contatori e ledger, più identità dei sorgenti/input. Non basta
archiviare73temperature senza geometria e scenario. Il nuovo collegamento dovrà
provare direct/split/restore e conservare gli eventuali bit di compensazione.
Non è implementato o qualificato qui. Per transitori di10anni servono risoluzione
locale o una dichiarazione esplicita della sottorisoluzione; non scegliere una
grande griglia globale o una durata lunga per mascherarla.

Originali v1, R1, provider e archivi preservati; nessun1000Y/10k/100k,
accoppiamento planetario, commit/push o validazione scientifica. Nuova evidenza:
`ARCANA_WORLD_EVIDENCE/R6/THERMAL_1D_EXPLORE2_20261102_01`, con SELECTED_INPUTS,
RESULT delle due esecuzioni, COMPARISON, oracolo Moho, ordini, array, costi e grafico.

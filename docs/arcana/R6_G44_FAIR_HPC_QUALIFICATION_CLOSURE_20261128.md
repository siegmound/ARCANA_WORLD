# ARCANA WorldSim — G44 recupero e qualificazione HPC FAIR

28 novembre 2026, Europe/Rome. Provenienza: **FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE**, lettura ed esecuzione dirette. Autorità operativa: richiesta dell'autore e handoff `ARCANA_CODEX_HANDOFF_G44_HPC_FULL_MANTLE_2026-11-28.md`, conservato integralmente nel bundle. Le misure non sono dichiarazioni dell'operatore riportate indirettamente.

## Esito e configurazione raccomandata

**PASS_SYNTHETIC_HPC_QUALIFICATION_ONLY**. Recuperati MPI 2/4 rank; eseguiti 8/16/32/64 core fisici e 128 thread logici; confrontati TCP, shared-memory, PRoot, deployment nativo, NUMA e throughput. 71 casi di prestazioni nell'analisi principale, oltre a probe, regressioni, fallimenti conservati e sei job del test di throughput. Test mirati finali: **15 passati**, zero failure/error.

Per questa famiglia di benchmark: deployment privato `native_candidate2`, OpenMPI `ob1`, `self,vader`, `btl_vader_single_copy_mechanism=none`, un rank per core fisico, distribuzione sui quattro NUMA, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`. TCP locale esplicito resta l'alternativa qualificata. Non rendere queste variabili impostazioni globali del sistema.

- Livello 4: 32 rank nativi/shared-memory, mediana **4.141 s**, intervallo 3.973–4.150 s.
- Livello 5: 32 rank, mediana **21.618 s**; 64 rank **21.714 s**. La scelta a 32 preserva metà dei core per altri job: la differenza di latenza va letta insieme agli intervalli e al costo in rank-secondi. 128 rank SMT: **23.731 s**, nessun vantaggio misurato su questo carico.
- Livello 6: TCP nativo a 32 rank **178.310 s**, a 64 **152.808 s**; PSS massime osservate 94.28/98.93 GiB. Solo screening singolo, non una scelta di trasporto definitiva per mesh grandi.
- Campagne indipendenti: due job da 32 rank su core disgiunti, tre coppie; mediana di completamento della coppia **39.416 s**, throughput **0.05074 job/s**, rapporto **1.102×** rispetto a job seriali da 64 rank. Include entrambi i preflight: confronto conservativo con il clock del singolo job. Valido per questa mesh sintetica e questo carico del nodo.

Questa è una configurazione raccomandata per esperimenti sintetici e sviluppo del provider. Non è un runtime di produzione scientifica globale ammesso.

## Identità, autorità e protezioni

Repository `siegmound/ARCANA_WORLD`, branch `r6/g36r2-fair-repair-20261127`. Baseline ricevuta `422324f4f7ae5ba017a719c3c318a371711e6d8f`. SOURCE congelato **901cbb4a38916190df6a881bb561b6558dd997dd**, ancora pulito. ASPECT **3.2.0-pre**, upstream **30eb77ee5da186137d436dbad35c6cb3cab64b69**; deal.II 9.6.0, Trilinos 13.2.0, p4est 2.2.0, GCC 11.4, OpenMPI 4.1.2. Nessuna reinstallazione o alterazione del runtime storico.

I nove bundle parentali richiesti sono stati verificati prima dei rispettivi usi e nuovamente alla chiusura con inventario completo e pin originali. `FINAL_GUARDS.json` conserva i pin e conferma l'uguaglianza dei 92749 elementi della metadata del container storico, gli hash degli eseguibili e la pulizia del SOURCE. Nessun verdetto storico riscritto. La precedente riparazione G36-R2, quattro configurazioni, metriche positive/negative e replay R1 resta documentata in [chiusura G36-R2](R6_G36R2_FAIR_REPAIR_AND_WORLD_HISTORY_ROADMAP_20261127.md); questa campagna non modifica la formulazione d'interfaccia.

D-024 e D-025 attive. L'esecuzione diretta FAIR e il commit/push di questa campagna sono autorizzati dalla richiesta corrente; le vecchie istruzioni Windows-only restano storiche. Nessun privilegio amministrativo, installazione di sistema, `killall`, pulizia cache o terminazione di altri lavori. Il nodo è condiviso: assenza di quota/scheduler rilevata non equivale a prenotazione esclusiva né certificazione indipendente della policy del sito.

## Diagnosi pidfd e supervisione

Il Python Conda scientifico non espone `os.pidfd_open` e `signal.pidfd_send_signal`; il Python di sistema espone entrambe e il kernel supera l'apertura di un pidfd sul processo corrente. La causa del preflight R2 è nell'interprete, non una dimostrata incompatibilità del kernel. Il log originale fallito è conservato in `HISTORICAL_G44R2_PREFLIGHT_FAILED.log`; la directory R2 risultava e risulta assente. Nessun manifest R2 inventato.

Il nuovo supervisore usa `/usr/bin/python3`, senza sostituire il Python scientifico. Tag iniziale esatto, stesso UID, starttime, identificazione verificata dopo apertura pidfd; nessun fallback `kill(pid)`. La scansione storica non trova processi vivi con il tag autorizzato e registra no-op, senza esigere pidfd inutilmente. Nuovi job hanno timeout, raccolta di discendenti separati tramite subreaper Linux, TERM/KILL mirati tramite pidfd e scansione finale. Un launcher exit0 con figli da terminare diventa esito125; timeout124, arresto risorse126. Nella versione finale i pidfd restano aperti dalla prima osservazione affidabile fino alla pulizia finale.

Sono state corrette anche due condizioni di monitoraggio: scansione di nuovi servizi SSH non appartenenti al job e transizioni transitorie di accesso `/proc` durante exec/exit. La scansione dei nuovi job segue i discendenti del supervisore; accessi temporaneamente negati hanno retry limitato, dinieghi persistenti bloccano. I test reali coprono figli normali/separati, timeout, orfani, processi estranei, API mancanti, no-match, diniego persistente, tag e starttime errati. Le prove finali MPI4 e L5 a 32/64/128 rank usano il supervisore con pidfd mantenuti e contatori utente/sistema.

Il primo L6/64, eseguito con uno snapshot precedente del monitor, termina ASPECT ma fallisce il controllo `/proc` durante l'uscita; resta **FAILED**. `native_tcp_l6_p64_r1_retry2` usa la revisione `d02d16fa`: un evento `POLLIN` sul pidfd mantenuto può confermare la morte anche durante la transizione di dumpability. Un diniego di accesso, da solo, non dimostra la terminazione. La ripetizione supera supervisione, parità numerica e pulizia; `L6_MONITOR_RECOVERY.json` lega i due tentativi senza riscrivere il primo.

Alla chiusura: 2741 identità PID/starttime osservate ricontrollate, zero processi vivi corrispondenti; tutti i `RUN_EXIT.json` hanno lista `remaining` vuota. La garanzia riguarda i job identificati, non tutti i processi della workstation.

## Metodo, mesh e verifiche numeriche

Upstream HollowSphere invariato: guscio adimensionale r=0.5–1, velocità analitiche prescritte ai due bordi, viscosità r^4, riferimento analitico e tolleranza Stokes 1e-6 originali, t=0, nessuna advezione. Non è il caso free-slip G39 e non è una geometria canonica di ARCANA. Modificati soltanto refinement, directory e strumentazione; visualizzazione e postprocessor originali mantenuti. I gradi di libertà comprendono Stokes e temperatura, anche se la temperatura non avanza.

| Livello | Celle | DOF totali |
|---:|---:|---:|
| 2 | 768 | 28,690 |
| 3 | 6,144 | 215,962 |
| 4 | 49,152 | 1,674,538 |
| 5 | 393,216 | 13,185,610 |
| 6 | 3,145,728 | 104,645,770 |

Versione, rank effettivi, affinità di ogni rank, celle, DOF, step/time, errori L1/L2 di velocità/pressione e topografia sono verificati. Scostamento massimo osservato rispetto al riferimento della stessa mesh: **1.9265824e-05**, soglia relativa originale 1e-4. Gli errori diminuiscono al raffinamento fino al livello6. Errori, residui, iterazioni GMG/Stokes, tempi per sezione e statistiche native sono conservati per ogni caso e aggregati in `NUMERICAL_DETAILS.json`. Nessuna modifica di equazioni, soluzione di riferimento o tolleranze.

Regressioni native G38 L2/L3 e G39 free-slip passate; G41/G42 rigiocate sui quattro casi uniformi Q2 a un rank con plugin originali e stessa ABI: bilanci/CBF superano i controlli originali. Le otto sezioni `.text` relocate sono identiche ai binari storici; non è cambiato compilatore/provider/ABI e non è servita ricompilazione dei plugin. Le assert singleton non sono state aggirate. Questo non qualifica CBF MPI o AMR.

## Scaling forte: misure complete

Wall = clock del supervisore, include avvio MPI e pulizia; clock interno ASPECT e solve-only in `ANALYSIS/SCALING.csv`. Ogni gruppo ha stesso runtime, trasporto, mesh e mapping. Speedup ed efficienza rispetto al minor rank testato nel gruppo: L4 riferimento1, L5 riferimento8, L6 riferimento32. Per L2/L3 riferimenti riportati nel CSV. Non confrontare i tempi storici G38 come baseline prestazionale. `n` indica ripetizioni; finalisti L4/L5 tre ripetizioni, con una prova aggiuntiva della versione finale del monitor su alcuni gruppi L5. Singoli valori restano screening. SMT128 è un confronto di thread, non di 128 core fisici.

| Runtime | MPI | L | Rank | n | Wall mediana s | Intervallo s | PSS max GiB | Speedup | Efficienza |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| native/spread | tcp | 2 | 1 | 1 | 1.876 | 1.876–1.876 | 0.21 | 1.00 | 1.000 |
| native/spread | tcp | 2 | 2 | 1 | 1.329 | 1.329–1.329 | 0.24 | 1.41 | 0.706 |
| native/spread | tcp | 2 | 4 | 1 | 1.382 | 1.382–1.382 | 0.28 | 1.36 | 0.339 |
| native/spread | tcp | 3 | 1 | 1 | 8.038 | 8.038–8.038 | 0.34 | 1.00 | 1.000 |
| native/spread | tcp | 3 | 4 | 1 | 2.919 | 2.919–2.919 | 0.46 | 2.75 | 0.689 |
| native/spread | tcp | 4 | 1 | 1 | 55.129 | 55.129–55.129 | 1.34 | 1.00 | 1.000 |
| native/spread | tcp | 4 | 2 | 1 | 29.948 | 29.948–29.948 | 1.60 | 1.84 | 0.920 |
| native/spread | tcp | 4 | 4 | 1 | 16.208 | 16.208–16.208 | 1.75 | 3.40 | 0.850 |
| native/spread | tcp | 4 | 8 | 1 | 8.841 | 8.841–8.841 | 1.99 | 6.24 | 0.779 |
| native/compact | tcp | 4 | 16 | 1 | 5.939 | 5.939–5.939 | 2.21 | 1.00 | 1.000 |
| native/spread | tcp | 4 | 16 | 1 | 5.678 | 5.678–5.678 | 2.20 | 9.71 | 0.607 |
| native/spread | tcp | 4 | 32 | 1 | 5.356 | 5.356–5.356 | 2.77 | 10.29 | 0.322 |
| native/spread | tcp | 4 | 64 | 1 | 6.007 | 6.007–6.007 | 3.20 | 9.18 | 0.143 |
| native/spread | tcp | 5 | 8 | 1 | 61.446 | 61.446–61.446 | 12.05 | 1.00 | 1.000 |
| native/spread | tcp | 5 | 16 | 1 | 33.348 | 33.348–33.348 | 12.89 | 1.84 | 0.921 |
| native/spread | tcp | 5 | 32 | 1 | 22.187 | 22.187–22.187 | 14.04 | 2.77 | 0.692 |
| native/spread | tcp | 5 | 64 | 1 | 23.698 | 23.698–23.698 | 15.99 | 2.59 | 0.324 |
| native/spread | tcp | 5 | 128 | 1 | 29.697 | 29.697–29.697 | 17.60 | 2.07 | 0.129 |
| native/spread | tcp | 6 | 32 | 1 | 178.310 | 178.310–178.310 | 94.28 | 1.00 | 1.000 |
| native/spread | tcp | 6 | 64 | 1 | 152.808 | 152.808–152.808 | 98.93 | 1.17 | 0.583 |
| native/spread | vader | 2 | 4 | 1 | 1.082 | 1.082–1.082 | 0.29 | 1.00 | 1.000 |
| native/spread | vader | 4 | 1 | 1 | 55.511 | 55.511–55.511 | 1.35 | 1.00 | 1.000 |
| native/spread | vader | 4 | 2 | 1 | 29.958 | 29.958–29.958 | 1.60 | 1.85 | 0.926 |
| native/spread | vader | 4 | 4 | 1 | 15.953 | 15.953–15.953 | 1.75 | 3.48 | 0.870 |
| native/spread | vader | 4 | 8 | 1 | 8.734 | 8.734–8.734 | 2.00 | 6.36 | 0.794 |
| native/compact | vader | 4 | 16 | 1 | 5.580 | 5.580–5.580 | 2.21 | 1.00 | 1.000 |
| native/spread | vader | 4 | 16 | 1 | 5.150 | 5.150–5.150 | 2.20 | 10.78 | 0.674 |
| native/spread | vader | 4 | 32 | 3 | 4.141 | 3.973–4.150 | 2.83 | 13.41 | 0.419 |
| native/spread | vader | 4 | 64 | 3 | 4.688 | 4.549–4.770 | 2.26 | 11.84 | 0.185 |
| native/spread | vader | 5 | 8 | 1 | 61.839 | 61.839–61.839 | 12.05 | 1.00 | 1.000 |
| native/spread | vader | 5 | 16 | 1 | 33.211 | 33.211–33.211 | 12.89 | 1.86 | 0.931 |
| native/spread | vader | 5 | 32 | 4 | 21.618 | 21.131–21.979 | 14.03 | 2.86 | 0.715 |
| native/spread | vader | 5 | 64 | 4 | 21.714 | 21.416–21.969 | 15.27 | 2.85 | 0.356 |
| native/spread | vader | 5 | 128 | 2 | 23.731 | 23.599–23.863 | 17.81 | 2.61 | 0.163 |
| proot/spread | tcp | 3 | 2 | 1 | 4.916 | 4.916–4.916 | 0.41 | 1.00 | 1.000 |
| proot/spread | tcp | 3 | 4 | 1 | 3.291 | 3.291–3.291 | 0.46 | 1.49 | 0.747 |
| proot/spread | tcp | 3 | 8 | 1 | 2.498 | 2.498–2.498 | 0.58 | 1.97 | 0.492 |
| proot/spread | tcp | 4 | 1 | 1 | 55.370 | 55.370–55.370 | 1.34 | 1.00 | 1.000 |
| proot/spread | tcp | 4 | 2 | 1 | 30.103 | 30.103–30.103 | 1.60 | 1.84 | 0.920 |
| proot/spread | tcp | 4 | 4 | 1 | 16.346 | 16.346–16.346 | 1.75 | 3.39 | 0.847 |
| proot/spread | tcp | 4 | 8 | 1 | 9.296 | 9.296–9.296 | 1.99 | 5.96 | 0.745 |
| proot/compact | tcp | 4 | 16 | 1 | 6.324 | 6.324–6.324 | 2.23 | 1.00 | 1.000 |
| proot/spread | tcp | 4 | 16 | 3 | 6.099 | 6.097–6.300 | 2.21 | 9.08 | 0.567 |
| proot/spread | tcp | 4 | 32 | 3 | 5.809 | 5.750–6.212 | 2.83 | 9.53 | 0.298 |
| proot/spread | tcp | 4 | 64 | 1 | 7.440 | 7.440–7.440 | 3.14 | 7.44 | 0.116 |
| proot/spread | tcp | 5 | 8 | 1 | 62.090 | 62.090–62.090 | 12.05 | 1.00 | 1.000 |
| proot/spread | tcp | 5 | 16 | 1 | 43.102 | 43.102–43.102 | 12.89 | 1.44 | 0.720 |
| proot/spread | tcp | 5 | 32 | 3 | 23.773 | 23.650–23.898 | 14.05 | 2.61 | 0.653 |
| proot/spread | tcp | 5 | 64 | 3 | 25.099 | 24.807–25.932 | 15.47 | 2.47 | 0.309 |
| proot/spread | tcp | 5 | 128 | 1 | 38.676 | 38.676–38.676 | 17.85 | 1.61 | 0.100 |
| proot/spread | vader | 2 | 2 | 1 | 1.604 | 1.604–1.604 | 0.24 | 1.00 | 1.000 |
| proot/spread | vader | 2 | 4 | 1 | 1.378 | 1.378–1.378 | 0.28 | 1.16 | 0.582 |


## Scaling debole

Coppie con celle per rank uguali e DOF per rank esplicitati. Efficienza = tempo piccolo / tempo grande. È screening a due punti, non una curva asintotica; setup, output e solve inclusi.

| Runtime/trasporto | L/rank iniziali → finali | Celle/rank | DOF/rank iniziali → finali | Tempo s iniziale → finale | Efficienza |
|---|---|---:|---|---|---:|
| native/tcp | 3/4 → 4/32 | 1536 | 53990.5 → 52329.3 | 2.919 → 5.356 | 0.545 |
| native/tcp | 4/8 → 5/64 | 6144 | 209317.2 → 206025.2 | 8.841 → 23.698 | 0.373 |
| native/tcp | 5/8 → 6/64 | 49152 | 1648201.2 → 1635090.2 | 61.446 → 152.808 | 0.402 |
| native/vader | 4/8 → 5/64 | 6144 | 209317.2 → 206025.2 | 8.734 → 21.714 | 0.402 |
| proot/tcp | 3/4 → 4/32 | 1536 | 53990.5 → 52329.3 | 3.291 → 5.809 | 0.567 |
| proot/tcp | 4/8 → 5/64 | 6144 | 209317.2 → 206025.2 | 9.296 → 25.099 | 0.370 |

## Memoria, I/O e NUMA

64 core fisici/128 logici, due Xeon Gold6530, quattro NUMA. CPU fisici rappresentativi0–63; fratelli SMT64–127, verificati da socket/core_id. Pinning esplicito, rank/socket/NUMA ricostruibile dai marcatori e da `HARDWARE_BEFORE.json`. Caso distribuito: rotazione0,16,32,48,1,17,…; compatto16: CPU0–15, un NUMA. Confronto a pari rank e mesh:

| Runtime/trasporto | 16 rank distribuiti s | 16 rank compatti s |
|---|---:|---:|
| proot/tcp | 6.099 | 6.324 |
| native/tcp | 5.678 | 5.939 |
| native/vader | 5.150 | 5.580 |

Confronto NUMA a una ripetizione per collocazione; non attribuire causalità definitiva da differenze piccole. `ANALYSIS/REPORT.json` contiene distribuzione delle pagine residenti per nodo alla PSS aggregata massima; condivise/file duplicate, nessuna prova di memoria locale o first-touch controllato. Sotto PRoot il nome `/proc/exe` identifica l'interprete: l'analisi segnala esplicitamente i rank inferiti da affinità e PSS. Il runtime nativo consente identificazione diretta.

I valori celle/DOF per rank nello scaling debole sono medie globali. Il conteggio delle celle e dei DOF posseduti da ogni rank e l'imbalance della partizione p4est non sono stati strumentati separatamente; la memoria osservata per processo non li sostituisce.

PSS e RSS aggregate campionate, RSS duplica pagine condivise. Intervallo richiesto0.25s più costo della scansione; gap massimo effettivo **15.449s**. Picchi brevi possono sfuggire. Swap massimo osservato dei job: **0 byte**. `TIME.txt` conserva user/system del comando; `CPU_IO_AND_RANK_METRICS.json` conserva CPU/I/O osservati e PSS per processo; split utente/sistema e thread per processo disponibili nelle prove del supervisore finale. Contatori campionati sono limiti inferiori, non accounting del scheduler; RSS massimo di `/usr/bin/time` non è memoria MPI aggregata. Nessun cap aggregato kernel o cap individuale viene rivendicato.

Soglia PSS ordinaria80GiB, stop per swap del job>64MiB, timeout per caso; riserva host max(64GiB,25% MemAvailable iniziale). Livello6 avviato dopo proiezione L5 e avviso D-025 per possibile superamento100GB: proiezione132837974016 byte, soglia campionata182536110080 byte(170GiB), oltre960GiB disponibili all'avvio. Le soglie sono di arresto campionato, non garanzie di picco. Carico e MemAvailable prima/dopo ogni caso nei raw; cgroup/topologia/scheduler e inventario finale conservati.

## Runtime nativo e SIMD

Il deployment privato cambia esclusivamente interprete ELF e percorsi librerie di otto copie, con librerie storiche fissate e `.text` identico. Necessaria risoluzione dei symlink assoluti nel namespace del container. I tentativi nativi falliti prima della corretta propagazione di librerie a `orted` sono conservati. `NATIVE_BUILD_AND_CPU_AUDIT.json` contiene CMake flags storici, indici32-bit, GMG matrix-free/p4est, risoluzione loader e CPU flags. La procedura versionata ha ricreato un secondo deployment da zero con `.text` identico e versione exit0 (`NATIVE_REPRODUCIBILITY_REPORT.json`). Non è una nuova compilazione ottimizzata.

Confronto PRoot/TCP e nativo/TCP: il beneficio è misurato nelle tabelle, modesto e dipendente dal caso. `self,vader` con single-copy disabilitato passa; non è dimostrata una causa unica UCX/vader/PRoot dei vecchi blocchi. Il vecchio profilo `^vader` fallito rimane fallito. Nessun aggiramento arbitrario dei check.

deal.II mantiene **VECTORIZATION_WIDTH_IN_BITS=0**. Valutazione SIMD isolata, GCC host, tre ripetizioni ruotate su un core, -O3 senza fast-math e contrazione FMA disattivata, checksum bitwise identici per tutti i nove run e ISA YMM/ZMM verificata nel disassemblato:

| Variante microkernel | Mediana s | Intervallo s | Speedup scalare |
|---|---:|---|---:|
| avx2 | 0.183668 | 0.183554–0.183705 | 3.879 |
| avx512 | 0.112049 | 0.111674–0.112171 | 6.358 |
| scalar | 0.712410 | 0.712203–0.712540 | 1.000 |

È un microkernel aritmetico indipendente, non ASPECT: nessuno speedup applicativo inferito. Abilitare SIMD in ASPECT richiede build privata coerente deal.II+ASPECT+plugin e nuove regressioni/confronti AVX2/AVX512; ricompilare il solo eseguibile non basta. Non si ricompila l'intero stack senza un confronto di costo/beneficio: il deployment attuale permette già MPI64 e oltre100M DOF. Due RTX5090 rilevate,32GiB ciascuna circa; inventario soltanto, backend GPU non qualificato.

## Throughput distinto dalle misure di scaling

Sei job L5 indipendenti in tre coppie; 32 core fisici disgiunti per job, stessi input e verifiche analitiche. Nessuna coppia durante le prove di scaling/SIMD. Makespan della coppia include startup/preflight; intervallo **38.050–40.025s**, rapporto rispetto al seriale32 **1.097×** e al seriale64 **1.102×**. Il campo memoria somma picchi individuali campionati, non è un picco simultaneo misurato. Per campagne future raggruppare job indipendenti rispettando mapping disgiunto, memoria/headroom e dipendenze; non applicare questa concorrenza a una singola traiettoria causale.

## Tentativi falliti conservati

I bundle G44/R1 originali restano identici ai pin. Preflight R2 conservato, nessun solve R2. Tutte le directory della nuova campagna restano presenti:

- `native_tcp_l6_p64_r1`: RuntimeError('SUPERVISOR_FAILURE').
- `tcp_aspect_l2_p2_r1`: RuntimeError('NATIVE_EXIT_OR_LEFTOVERS').
- `tcp_aspect_l2_p2_r2`: ValueError("could not convert string to float: 'output/solution/solution-00000'").
- `tcp_l3_p2_spread_r1`: RuntimeError('SUPERVISOR_FAILURE').
- `tcp_l4_p1_spread_r1`: RuntimeError('SUPERVISOR_FAILURE').
- `tcp_probe_p4`: RuntimeError('PROBE_STAGES').

Cause operative risolte senza cambiare fisica: suffisso `.release.so` del plugin, bit eseguibile della probe, statistiche miste numeri/stringhe, scansione dei discendenti e race transitorie `/proc`. I casi con solve exit0 ma parser/monitor fallito restano tali; nuove recovery/ripetizioni hanno identità distinte. `TCP_P2_POSTPROCESS_RECOVERY.json` conserva l'adjudication separata del caso già eseguito, senza falsificare il suo report originale. Log dei riavvii del driver e dei primi deployment nativi sono inclusi. Un retry superato non cancella il primo fallimento.

## Evidenze, commit e riproducibilità

Bundle esterno **`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G44_HPC_FULL_MANTLE_20261128_NEW01`**. Manifest SHA256 **`8ef9676aa03875ea09452286e82edb20f755ab785f7a4f6d2b11d746a0322422`**, **7121** file; inventario completo compatibile con `g25.inventory`, MANIFEST radice escluso, target dei symlink esplicitati. Conservati input, comandi/configurazioni, stdout/stderr, tempi, campioni, versioni, errori e failure. I binari e output voluminosi restano fuori dal branch codice.

- `REPORT.json`: risultato e scope; `FINAL_GUARDS.json`: source/runtime/parent e processi.
- `ANALYSIS/REPORT.json`, `SCALING.csv`, `TABLE.md`: casi, statistiche, scaling e distribuzione NUMA.
- `NUMERICAL_DETAILS.json`, `CPU_IO_AND_RANK_METRICS.json`: audit numerico, rank e risorse.
- `SIMD_ASSESSMENT/REPORT.json`, `THROUGHPUT_NEW01/REPORT.json`: misure con scope separati.
- `FOCUSED_TESTS_FINAL.xml`: test finali; copie dei runner e commit nei file `*_RUNNERS*IDENTITY.json` e nelle ricevute precedenti.

Verifica successiva alla sigillatura: l'intero inventario è stato ricalcolato con il verificatore originale `g38.verified_bundle`, non soltanto con la cache usata durante la creazione del manifest. La ricevuta separata `R6_G44_HPC_DELIVERY_VALIDATION_NEW01`, manifest **`1438fd8dc15d8bd562d5dc96a396843c47fffc7935fc2bdb1574e4bc63fd36d4`**, conserva il PASS dell'audit e 31 file, inclusi gli artefatti reali dei test positivi/negativi recuperati da pytest. Il bundle principale non è stato modificato dopo la sigillatura.

Commit di implementazione e correzione, dal più recente:

```text
3a7aab8136725e964f5fbb5876a35c164c971914 Pin MPI component path in native deployment reproduction
ff63650b0b0667dace16d12fdce040510c1d26f0 Keep CPU mapping tests independent of external FAIR artifacts
54156bfc0a37f9d2231d2fd42bd243474d551738 Include failed supervisor samples in final process identity guards
d02d16fa27078019ac9b522d6d8021cc7e8c4d21 Use retained pidfd termination events to resolve proc exit transitions
64b277e0d40a9845f82ac7ada48d227abded091a Add append-only HPC closure, integrity guards and complete evidence sealing
c9a808bfbb635d303cc1e6c14df70214a08fc7e7 Measure separate two-job throughput on disjoint physical cores
aeae5fff3c55d3cde9b642288c9cd8f666c0a1fe Record per-process user and system CPU observations
a6ce18a4b8264359d613be09c9d629ba2f488443 Retain verified pidfds from first observation through final cleanup
5ed91661601522cbcec66a9ffa75079db70dc96e Add retained HPC scaling analysis and isolated SIMD assessment
63cd4f56e096eb2f570fc598223f60521eccb5fe feat(hpc): qualify private native deployment shared memory and large mesh resource gate
b20cdba0f3d4430bd2962dd6f51742ab06a00b48 feat(hpc): add commit-pinned resumable FAIR campaign launcher
fe8e9b43d33464e214de1bded66507b3df6ec740 fix(hpc): retry transient proc access races while preserving persistent-denial guard
6ed87519b3590c9ba8c174069ca0f4b92c7a419f feat(hpc): prepare isolated native backend and reuse qualified retry outputs
50250876624b3a0e5d054d191ba8097b43dc6de9 fix(hpc): scope monitoring to subreaper descendants and resume gated stages
8f386171ba2cac17e688664ff98ee0b9fc0d6a64 fix(hpc): retain probe executable mode and resume preserved campaign safely
db4f40dd817c715e5bdc790beddb235df2c086f7 feat(hpc): stage sequential rank scaling SMT NUMA and resource gated refinement
596c1c319dad54d6ca9715d215236438439d592d fix(hpc): preserve text statistics and recover completed MPI output without rerun
cc5a0b748cba985312e49b9bb309eb6e8bd53bdc fix(hpc): preserve ASPECT plugin suffix and identify rank executables
212f3e4f2bb2c2391e25628ece83df4a42fd0759 fix(hpc): distinguish proc exit races from persistent inspection denial
db0e34b972f1ef40240b24f8dd37b79832f0ef0d fix(hpc): use system pidfds for isolated MPI supervision and scoped cleanup
```

Il commit di consegna di questo documento e del ledger si ottiene con `git log -1 --format=%H -- docs/arcana/R6_G44_FAIR_HPC_QUALIFICATION_CLOSURE_20261128.md`; è separato dagli SHA eseguiti e dal manifest, per evitare identità circolari. Ricevuta verificabile: `experiments/r6_thermo_provider_pilot_v1/g44_hpc_fair_receipt_v1.json`.

Comandi di audit (read-only; non rilanciano esperimenti):

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_G36R2_DEV
git branch --show-current
git status --short
git log -1 --format=%H -- docs/arcana/R6_G44_FAIR_HPC_QUALIFICATION_CLOSURE_20261128.md
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$PWD/experiments/r6_thermo_provider_pilot_v1:$PWD/src:$PWD"
python - <<'AUDIT'
from pathlib import Path
import arcana_g38_aspect_hollow_sphere as g38
p=Path('/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G44_HPC_FULL_MANTLE_20261128_NEW01')
m=g38.verified_bundle(p,'8ef9676aa03875ea09452286e82edb20f755ab785f7a4f6d2b11d746a0322422')
print(m['status'],len(m['files']))
AUDIT
```

Ogni `config.json` conserva argv e ambiente completi del caso; ogni `rank.sh`/`cpus.txt` conserva il mapping. Il launcher `scripts/run_g44_hpc_campaign.sh` estrae e verifica blob di un commit. **Non rilanciare i runner write-once sul bundle sigillato**: una nuova campagna richiede nuovo root/ID e preflight, senza sovrascrivere questa. La procedura native è `arcana_native_runtime_candidate.py --base <BASE> --output <NUOVO_PATH_PRIVATO>`; il confronto scientifico completo resta obbligatorio per un vero rebuild. Non sono richiesti comandi manuali all'autore per completare questa campagna: esecuzioni già svolte direttamente.

## Scope scientifico e prossimi passi

`architecture=A_FULL_MANTLE_ADAPTIVE`, `physical_T1=null`, `scientific_promotion=false`, `physical_acceptance=false`, `mantle_initial_state_admitted=false`, `mantle_provider_qualified=false`, `global_solve_authorized=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; assegnazioni materiali0, solve ARCANA0, anni aggiunti0. Non usare raggio terrestre/CMB o una durata di benchmark come parametri/previsione canonica.

1. **Percorso B / prossimo task tecnico:** preparare contratto e test sintetici AMR + CBF MPI, senza disattivare le assert singleton. Qualificare distribuzione DOF/facce, ghost ownership, gauge, bilanci, convergenza e parità per 1/2/4/8 rank prima dell'uso scientifico. Usare il runtime HPC ora misurato; non cambiare provider numerico implicitamente.
2. **Percorso A / accoppiamento:** preservare G36-R2/G37/G37B; qualificare trasferimenti conservativi su mesh reali e reazione normale/radiale fisica, lavoro aggiunto, risultanti/momenti, moti rigidi, orientazione e copertura. Nessuna proiezione arbitraria RHS/torque o mantello fermo prescritto.
3. **Percorso B / stato mantellare:** G43 termico sotto-LAB quasi radiale è supporto condizionale, non inizializzazione convettiva3D. M01 non autorizzato; CMB, EOS, acqua/composizione, pressione assoluta, reologia, flussi e perturbazioni richiedono fonti. Non colmare UNKNOWN con zero.
4. **Percorso C:** G15 corretto162anni con FB2 slopey/sinA, CSR e band, halving/restart, massa/energia e termomeccanica resta da riqualificare in una campagna separata. Chiusura documentaria G18 non è nuova qualifica dinamica.
5. **WORLD_HISTORY intera:** sottoinsieme fisico minimo realmente chiuso secondo D-024, poi topografia/carichi→gFlex→erosione/acqua/FastScape, risorse naturali/Deep, clima/suoli, flora/fauna, popolazioni/civiltà. Scheduler con timestep adattivi, archivio causale/restart/eventi e query per regione/epoca/processo, raffinamento locale con lineage e bilanci,12anchor/CHA-1/H0 e limite500GB preservati. Physical T1 è una tappa, non l'obiettivo finale. Nessun benchmark sintetico autorizza210Ma o pubblicazione canonica.

I vecchi file cumulativi del ledger sono conservati byte-per-byte in `PROJECT_LEDGER/archive/G44_20261128_PRE_CLOSURE_NEW01/`; la nuova vista operativa ha un solo CURRENT. I documenti storici di dettaglio, decisioni e log non vengono riscritti.

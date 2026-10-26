# GEODYN-1A — preparazione del forward driver geodinamico

Data: 2026-10-26
Branch osservato: `r6/multiphysics-integration-20261026`
HEAD osservato: `5bec08287da671f73fbe31d7f3fe7d259714de57` (commit locale SURF-2).
Ambito: ricognizione del codice e dei contratti; nessuna esecuzione ASPECT, ShellSet o evoluzione geologica è stata effettuata.

## Decisione

**ASPECT è un candidato complementare per la dinamica continua Stokes–energia–composizione; non è ancora selezionabile come motore principale della storia ARCANA.** Il ledger R6 resta proprietario dell’orchestrazione, dell’identità degli stati territoriali, dei materiali, dei trasferimenti superficiali e della storia interrogabile. ASPECT potrebbe diventare un provider geodinamico per finestre temporali soltanto dopo aver definito condizioni iniziali e al contorno, reologia e forcing ARCANA con autorità verificabile, oltre a una mappa spaziale conservativa.

Verdetto operativo: **GEODYN-1A_PREPARATION_COMPLETE__ASPECT_RUNTIME_UNAVAILABLE__ARCANA_FORWARD_PHYSICS_UNRESOLVED**. Non è un PASS di benchmark o un’autorizzazione all’esecuzione.

## Inventario degli input T0 e autorità

| Dato | Disponibilità effettiva | Classificazione e limite |
|---|---|---|
| Partizione delle placche a 210 Ma | Contratto B4/B5: griglia sferica 1°, 64.800 facce parent, 12 placche; appartenenza ai supporti deriva dall’incidenza faccia/nodo | Base spaziale T0 versionata. Non è una mesh volumetrica, né descrive l’evoluzione successiva |
| Cinematica Euler | Vettori e velocità relative derivati per il solo istante T0; gauge dichiarato nel rapporto B5 | Diagnostica cinematica istantanea. Nessuna legge temporale, interpolazione, calendario di eventi o autorizzazione a imporla per durata positiva |
| Profili termici/materiali ridotti | Schema R6 e bundle ingegneristici documentano colonne di 73 nodi su supporti selezionati; campi includono temperatura, coordinata materiale, ruolo, densità, Cp, k e sorgente radiogenica | Input di colonne ridotte, non campo 2D/3D globale. In questa sessione `ARCANA_EXTERNAL_ROOT` è vuoto; i payload provider non sono stati ri-verificati |
| Geometria termica ridotta | `ReducedState`: larghezza, spessori crostale/litosferico, frazione crostale, strain accumulato e profilo termico | Stato del kernel 1D di shear/termico. Non definisce geometria FEM geodinamica, elevazione globale, pressione o stress 3D |
| Materiali | `NodeMaterial` contiene `role_id`, `rho_kg_m3`, `cp_j_kg_k`, `k_w_m_k`, `radiogenic_w_m3` | Proprietà presenti nei contratti/provider selezionati. Ruoli crosta/mantello non determinano composizione mineralogica o reologia |
| Supporti territoriali e interfacce | B5 fornisce ID, placche, bordo e geometria topologica T0; i pilot C028/C029 e le griglie regionali hanno mapping esplicitamente limitati o sintetici | Non dimostrano un mapping volumetrico continuo né un contatto meccanico persistente. Nessuna continuità materiale/idraulica si deduce dalla sola adiacenza |
| Elevazione/batimetria, superficie, idrologia e Deep | Dati e consumer sono parziali; i pilot SURF-2 e precedenti sono sintetici | Non costituiscono campi globali T0 completi o condizioni al contorno geodinamiche |
| Pressione, densità profonda/EOS, reologia ARCANA, E, ν, Te, composizione, mineralogia, fasi, plasticità, carichi e forze | Non stabiliti per il dominio di forward evolution | UNKNOWN; nessuna analogia con benchmark può riempire questi campi |
| Condizioni al contorno e forcing a T>0 | T0 Euler/topologia non definiscono vincoli di velocità/traction, termici o cambi topologici nel tempo | UNKNOWN e bloccanti per un forward run ARCANA |

Il materiale canonico ARCANA, gli output derivati e i parametri benchmark sono tre classi distinte. La legge dry-olivine non viene assegnata a nessun materiale ARCANA. I parametri di un benchmark restano sintetici anche se il solver li esegue correttamente.

## ASPECT: equazioni, input e modello minimo

ASPECT dichiara modelli 2D/3D con Stokes, continuità di massa, energia e campi composizionali advettivi. La forma completa documentata include dipendenza della densità dalla temperatura, conduzione, sorgenti radiogeniche, riscaldamento viscoso e termini adiabatici/fase quando configurati ([equazioni ufficiali](https://aspect-documentation.readthedocs.io/en/latest/user/methods/basic-equations/index.html)). La scelta di un modello ridotto deve specificare quali termini sono attivi, anziché presumere che tutti siano pertinenti.

Per un **benchmark indipendente** bastano i parametri chiusi dalla specifica del benchmark: dominio cartesiano 2D, mesh e raffinamento dichiarati, gravità e scale adimensionali, condizioni termiche e cinematiche complete, materiale benchmark e criterio d’arresto. Per un **forward ARCANA** sono invece indispensabili almeno:

- dominio e mappa coordinate/supporti/aree, profondità e topografia/batimetria con maschere;
- campi iniziali di temperatura, composizione e densità sulla mesh, con unità, provenienza e rimappatura verificata;
- modello costitutivo e parametri di viscosità/elastanza/plasticità eventualmente adottati, EOS/densità e dipendenze da T/P/composizione;
- Cp, conducibilità e sorgenti termiche nel volume, più gravità e formulazione (incomprimibile, Boussinesq o compressibile) coerente con le ipotesi;
- condizioni al contorno di velocità/traction e temperatura/flusso su ogni bordo, più un’evoluzione temporale autorizzata della forzante e delle interfacce;
- risoluzione/spessore elementi, passo temporale e criteri di convergenza, bilanci, checkpoint e restart verificati.

Le proprietà mancanti sono bloccanti per la simulazione ARCANA, ma non per eseguire il caso sintetico ufficiale.

## Modello iniziale consigliato

Per la prima prova usare **Blankenbach 1989, caso 1a**, benchmark 2D cartesiano di convezione mantellare con configurazione ufficiale, parametri adimensionali, condizioni e statistiche di riferimento. La pagina benchmark ufficiale segnala casi 1a–2b e fornisce passi tipici; per il livello di risoluzione 3 il caso 1a elenca 72 passi, mentre le configurazioni più fini richiedono molto di più ([specifica e statistiche ufficiali](https://aspect-documentation.readthedocs.io/en/latest/user/benchmarks/benchmarks/blankenbach/README.html)). L’esecuzione futura deve usare un tag rilasciato pinning sorgente e file `.prm` upstream, senza cambiare il benchmark per adattarlo ad ARCANA. Non trasferire geometria o parametri del caso al pianeta.

Questo benchmark verifica un solver transiente Stokes–temperatura; non verifica tettonica a placche, margini ARCANA, erosione, sedimentazione o Deep. Per un primo run circoscritto, usare un solo rank MPI e la discretizzazione grossolana ufficiale (level 3) e raccogliere log, campi, bilanci, convergenza, checkpoint e restart. Durata wall-time/RAM attesa è **UNKNOWN** finché non è misurata sul build selezionato; non viene fissato un budget arbitrario in questa preparazione.

La release stabile pubblicata consultata è ASPECT 3.1.0. Il relativo annuncio richiede deal.II 9.6 o successivo e compilatore C++17; la pagina ufficiale segnala Trilinos 17/Tpetra con deal.II 9.8+ come opzione. La documentazione `latest` si identifica già come 3.2.0-pre: non usarla per presumere che una build installata sia 3.1.0 né mescolare le due configurazioni ([release ufficiale 3.1.0](https://github.com/geodynamics/aspect/releases), [documentazione ASPECT](https://aspect-documentation.readthedocs.io/en/stable/)). La documentazione descrive inoltre la dipendenza da deal.II e, per alcune configurazioni, Trilinos e p4est. Il build, le versioni dipendenze, MPI e risorse del runtime target vanno fissati e misurati prima del benchmark.

**Disponibilità locale:** `aspect` non trovato nel PATH Windows. `wsl.exe --status` ha restituito `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`. `ARCANA_EXTERNAL_ROOT` non è configurato nel processo corrente. Nessun solver ASPECT e nessun payload provider sono stati eseguiti/letti; non dichiaro runtime PASS né disponibilità ASPECT su Linux/Fair.

## Contratto minimo con R6

Un adapter di finestra futura deve ricevere e conservare:

1. `source_state_id`, tempo iniziale/finale e identità del run/attempt;
2. ID immutabili mesh, nodi/celle, placche, supporti, sistema coordinate e unità;
3. hash indipendenti di sorgenti, build ASPECT, configurazione, provider e dati iniziali;
4. campi iniziali espliciti (T, composizione, densità/material model) e BC/forcing con autorità e validità temporale;
5. recipe di remapping sorgente→mesh solver con copertura, pesi, conservazione di massa/energia e residui; mapping inverso solver→supporti R6 altrettanto esplicito;
6. output distinti per velocità, pressione, strain rate, stress, temperatura, composizione e spostamento incrementale, con statistiche convergenza, passo, bilanci e checkpoint solver;
7. record HistoryStore immutabili che distinguono risultato solver, derivazioni, trasferimenti e incertezze.

Non passare soltanto la topografia finale: per alimentare il sottosuolo servono anche il campo di spostamento incrementale e la storia di carico. Non sommare spostamenti assoluti a quote già aggiornate; distinguere deformazione del letto, deposizione/erosione e deflessione. Mapping conservativo non significa autorità fisica dei campi di origine.

### Cosa co-evolve e cosa può consumare archivi

- In un ASPECT forward window, Stokes, temperatura e composizione/material fields devono evolvere congiuntamente quando viscosità/densità/energia dipendono da tali campi. Non eseguire in parallelo il kernel termico 1D sullo stesso volume/tempo come se fosse indipendente; può restare un confronto o consumer di un altro supporto dichiarato.
- Idrologia, erosione/deposizione e Fastscapelib possono consumare snapshot topografici archiviati in modalità unidirezionale. Se cambiano carico o BC meccaniche nel medesimo intervallo, occorre accoppiamento a finestre/substep con scambio di carico conservativo, sincronizzazione e test di convergenza; il replay offline non rappresenta feedback.
- gFlex può consumare incrementi di carico solo con supporto/area e parametri elastici validi; l’esperimento F1D/F2D corrente è benchmark sintetico.
- Deep resta indipendente finché non esistono leggi validate che associno materiali, carichi o temperatura a energia/accessibilità. Non trasferire calore, lavoro o deformazione al Deep per semplice coincidenza di tempo.
- HistoryStore deve indicizzare gli stati secondo dominio/provider, tempo, supporto, build/config e provenienza; checkpoint riavviabili devono contenere lo stato necessario e il runtime richiesto, non solo output diagnostici.

## Criteri di correttezza per il benchmark successivo

- Pinned tag e source hash, versione build/deal.II/MPI, configurazione originale e comando;
- raggiungimento di criteri di convergenza del solver a ogni passo e assenza di NaN/Inf;
- confronto delle quantità benchmark ufficiali (ad es. Nusselt e velocità) con i dati pubblicati, usando l’accuratezza/risoluzione specificata dal benchmark e senza soglie create per ARCANA;
- convergenza al raffinamento almeno su una coppia di mesh, simmetria e risposta al variare del benchmark secondo il reference;
- bilancio energia termica (accumulo, flusso ai bordi, sorgenti e dissipazione incluse se attive), massa/continuità, integrale delle composizioni e assenza di campi persi;
- checkpoint/restart contro esecuzione continua alla stessa sequenza di passi; dichiarare differenze floating-point e non richiedere identità bitwise se la decomposizione cambia;
- runtime, peak RSS, output volume e residui effettivamente misurati.

Per il successivo test ARCANA, criteri ulteriori sono: copertura del mapping, conservazione mass/energy dopo remapping, chiusura delle BC e una legge temporale indipendente di forzante. Senza questi, nessuna traiettoria ARCANA T0→T1 è interpretabile.

## Problemi fisici e decisione

La release ASPECT documenta anche campi composizionali advettivi e modelli materiali che forniscono i coefficienti delle equazioni ([composizioni](https://aspect-documentation.readthedocs.io/en/stable/parameters/Compositional_20fields.html), [modelli materiali](https://aspect-documentation.readthedocs.io/en/stable/user/extending/plugin-types/material-models.html)). La sua capacità numerica non colma i dati ARCANA mancanti: reologia, EOS, profilo 3D, carichi, BC, tempo della cinematica Euler e transizioni topologiche. L’uso di Euler T0 come velocità prescritta lungo T0–T1 resta vietato senza legge autorizzata.

**Scelta: ASPECT COMPLEMENTARE, candidato non selezionato per il motore principale.** È appropriato come potenziale solver di continuum Stokes/energia/composizione dopo benchmark indipendente e chiusura degli input. R6 deve restare l’orchestratore e store della storia; se la selezione del motore geodinamico ARCANA sia ASPECT, ShellSet o altro rimane aperta.

### Prossimo esperimento concretamente preparabile

1. Acquisire o abilitare in un ambiente autorizzato una build identificata di ASPECT 3.1.0 e registrare deal.II/MPI/toolchain; nessuna installazione condivisa implicita.
2. Eseguire il benchmark ufficiale Blankenbach 1a, mesh level 3, un rank, file `.prm` e plugin upstream non modificati (se la release richiede il plugin); verificare la specifica esatta e i file di input al checkout del tag prima del comando.
3. Sigillare output e log fuori da `outputs/` canonici, validare i criteri sopra e provare restart.
4. Solo dopo, aprire una decisione distinta per definire ingressi/BC ARCANA e un esperimento positive-time su un dominio realmente supportato. Questo benchmark da solo non autorizza una simulazione ARCANA.

## Verifiche e stato repository

- Ricognizione statica dei contratti R6 e dei report B5, FLEX-1, LAND-1 e SURF-2; nessuna suite numerica eseguita perché non è stato modificato codice e ASPECT non è installato.
- Nessuna esecuzione ASPECT, ShellSet, MPI, Fair, nessun provider payload letto, nessun output numerico nuovo.
- Le cancellazioni preesistenti sotto `visualization/exports/VIEW1B_T0_V1*` e gli output untracked sono rimasti intatti; non sono inclusi nel deliverable.
- Il diff globale può segnalare errori di lettura/permessi su artefatti VIEW preesistenti; verificare il diff staged del solo pacchetto GEODYN con `git diff --cached --check`.

## Fonti ufficiali consultate

- Release ASPECT 3.1.0 e requisiti: https://github.com/geodynamics/aspect/releases
- Equazioni di base (manuale ASPECT): https://aspect-documentation.readthedocs.io/en/latest/user/methods/basic-equations/index.html
- Blankenbach benchmark: https://aspect-documentation.readthedocs.io/en/latest/user/benchmarks/benchmarks/blankenbach/README.html
- Benchmark e loro scopo: https://aspect-documentation.readthedocs.io/en/latest/user/benchmarks/index.html
- Campi composizionali: https://aspect-documentation.readthedocs.io/en/stable/parameters/Compositional_20fields.html
- Modelli materiali: https://aspect-documentation.readthedocs.io/en/stable/user/extending/plugin-types/material-models.html

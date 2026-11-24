# ARCANA WorldSim R6 — S3-D4-D: contratto numerico fail-closed (candidato non eseguibile)

**Data:** 2026-11-24. **Decisione:** `S3_D4_D_NUMERICAL_SCREEN_SOURCE_CANDIDATE_CREATED__FAIR_TEST_PENDING__SCIENCE_AND_RUN_BLOCKED`.

Questa revisione aggiunge un modulo software distinto da S2 e distinto dal parser nativo S3-D3. Non esegue MAGEMin, Julia, Perple_X, MEEMUM, l'orchestrazione WorldSim o qualsiasi calcolo fisico. Non crea artefatti di esecuzione. La matrice scientifica originale rimane **50/50 UNKNOWN / NOT_APPROVED**.

## Files e provenienza obbligatoria

- `experiments/r6_thermo_provider_pilot_v1/s3_d4_numeric_gate_candidate_v1.json`: numeri e regole dichiarati prima di eventuali risultati S3. Non un contratto ratificato per eseguire motori.
- `experiments/r6_thermo_provider_pilot_v1/s3_d4_numeric_screen.py`: convalida lo schema e analizza due riepiloghi **già ottenuti dal parser S3-D3**, senza eseguire alcun engine.
- `tests/test_r6_thermo_s3_d4_numeric_screen_v1.py`: test sintetici e negativi. Eseguire sul nuovo commit esatto in FAIR prima di qualificare il software.
- Input pin: design `s3_pt_design_candidate_v1.json` Git blob `1a69ac7be3d9970c94f91fe7e7213a8037af8286`; rischio scientifico `s3_d4_primary_source_model_risk_v2.json` Git blob `708830146ecb18287e6c6800be83f6c160a11003`; ultimo codice D3 già verificato su FAIR `9a9c996b909d7752114165f7f036ebf2b00fb966`; S2 REAL MANIFEST SHA256 `74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604`; modello Perple_X pin Git blob `564742a569998a768c2d8e15d2b9599ee90438d1`.

## Distinzione obbligatoria: tre tipi di affidabilità

| Livello | Esempio | Stato |
|---|---|---|
| **Controllo di formato / qualità ingegneristica** | P/T letti nel formato nativo; fasi non vuote; somme e residui; Gibbs/densità MAGEMin finiti; intervalli di stampa molari Perple_X | S2/D3 hanno già test di lettura, il nuovo wrapper è da testare |
| **Ripetibilità numerica stessa P/T** | Differenze fra processi indipendenti, masse delle fasi, Gibbs, densità; disaccordi nell'insieme delle fasi | **Nessuna soglia S3 ratificata**: `null`, un output uguale non è un PASS |
| **Accuratezza scientifica P/T-X** | Validità dei modelli G25 per l'originale bulk, rischio I1/C1 `Fsp(C1)`, fase `Augite(G)` ricca di Na, anfibolo Fe3/Ti, condizioni redox/acqua | **50 punti UNKNOWN**; il calcolo numerico non valida la geologia |

Le soglie di screening già presenti nel parser D3 (MAGEMin closure 1e-10, source closure 1e-12, residual 1e-9, somma phase 1e-8; Perple_X phase sum stampata 0,05 percent points e intersezione degli intervalli decimali) sono **controlli tecnici per la lettura**, non errori sperimentali né nuovi limiti S3 di ripetibilità.

La tolleranza di serializzazione è diversa dalla fisica: MAGEMin 16 ULP sul setpoint dei campi `P_kbar` e `T_C` espressi in float64; Perple_X il problema stampato usa fino a 0,1 nelle unità di sorgente; nessuno dei due equivale al confine geologico ±1kbar/50°C indicativo nel corrigendum G25.

## Comportamento diagnostico

La funzione `compare_readbacks(a,b)` impone:

1. **Stesso provider**: rifiuta ogni confronto diretto di MAGEMin contro Perple_X con `D4_CROSS_PROVIDER_COMPARISON_FORBIDDEN`.
2. **Stessa P/T, fasi diverse**: `SAME_PT_PHASE_DISAGREEMENT_REQUIRES_ADJUDICATION`, non la regola "mancante = zero" e non un falso PASS.
3. **Stessa P/T, stesse fasi**: registra differenza massima della frazione ponderale; per MAGEMin anche `G_system` assoluto e differenza relativa di densità. Per Perple_X NON inventa questi campi, mancanti nel report. `numeric_acceptance=NOT_RATIFIED`, `repeatability_pass=null` anche se i valori stampati coincidono.
4. **P/T diverse**: variazioni delle fasi sono `CROSS_PT_OBSERVATION_ONLY__NOT_PHASE_BOUNDARY_PROOF`. Non forzare l'uguaglianza fra punti. Le cautele modelli G25 e BL691 sono riportate.
5. **Input non convalidati**: rifiuta provider sconosciuti, P/T estranei alla griglia candidata, campi non finiti, Gibbs/densità inesistenti o inventati, chiusure native incompatibili, componenti molari originali Perple_X rinominati, ed escalation non autorizzate di stato scientifico.
6. **Sorgenti immutabili**: prima del confronto verifica i byte Git-blob dei due JSON originari, l'identità dei 50 punti, gli anchor S2, `D-024`, i limiti numerici del parser e tutte le autorizzazioni ancora false.

**Limite importante:** le sintesi D3 non contengono hash dei singoli file originali né l'intero contenuto numerico nativo. Il nuovo modulo è un analizzatore di riepiloghi, NON un validatore di manifest delle prove. Il futuro adapter S3 deve prima verificare e conservare l'output nativo completo in evidenze write-once; mai accreditare una sintesi arbitraria come prova scientifica o autentica.

## Passo successivo

Eseguire su FAIR **soltanto** il test Python D4-D con l'ambiente `arcana-r6-linux`, insieme ai 60 test D3 già qualificati, su branch/commit esatto; acquisire conteggio PASS e source SHA. Non eseguire Julia o MEEMUM. In caso di errori, creare nuova revisione del sorgente, mantenendo vecchi commit ed evidenze.

Dopo il PASS software, proseguire con D4-C sulle composizioni e le fasi reali e progettare un micro-pilota Earth-only con budget RSS/IO/timeout esplicito. Solo una distinta autorizzazione potrà consentire esecuzioni future. La campagna 25+25 non è autorizzata e l'uso come materiale originale ARCANA è vietato.

**Governance:** `D-024=ACTIVE`; `physical_T1=null`; `mechanical_solve_authorized=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. S1 e S2 immutabili. Il primo T0→T1 geodinamico regionale della roadmap D-024 è una linea parallela, non dipendente da ogni validazione termodinamica.

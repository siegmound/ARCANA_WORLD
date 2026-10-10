# Roadmap R6 — dipendenze e gates, non roadmap a timestep fissi
**Aggiornata:** 2026-10-10. Stati: `EVIDENCED` = verifica nel proprio scope; `PARTIAL` = lavoro qualificato ma gap; `BLOCKED` = autorità o evidenza insufficiente; `PLANNED` = da realizzare. Evitare percentuali arbitrarie.

| Track | Stato | Completato / riferimento | Gap e next gate |
|---|---|---|---|
| A. Governo e architettura ARCANA | PARTIAL | R6 contratti T0, dominio, authority/provenance, schemi storia; `VISION.md` | Portare adapter+scheduler+pubblicazione a esecuzione qualificata |
| B. WORLD_HISTORY core | EVIDENCED nel scope | B0 HistoryStore/query/replay/refinement/retention; B6M0 T0 genesis a 210 Ma in store governato | closure replay per più domini e finestre reali |
| C. Prima cinematica / rift B6 | PARTIAL/BLOCKED | B6K candidato isolato; B6N4-A significatività; B6N6 contratto temporale adattivo | B6N5 autorità evoluzione post-rift `UNKNOWN_NOT_GOVERNED`; non inventare dt2 |
| D. ShellSet runtime upstream | EVIDENCED nel scope | Fair: esempi stock, 9/9 modelli, esecuzione parallela, LAPACK smoke; carico runtime ARCANA qualificato separatamente | Non equivale a ARCANA T0 full mechanics |
| E. ShellSet ARCANA SI1/BW1 | PARTIAL/BLOCKED | BW0/F1 assemblaggio; F2-A recovery; F2A-V NVFortran compile PASS, MPI stop 75 | **adesso:** writer CSV corretto localmente; recovery intrabundle parziale, **bloccato sul companion sealed F2-A**; acquisizione/validazione F2-A reference, rerun recovery offline, adjudication. Decisione meccanica/solver F2-B separata |
| F. Modelli ambientali e risorse | PARTIAL/BLOCKED | BIOME4 input contract frozen; HRAB/parent-material research legacy da rivalutare come riuso | provider temporalmente idonei, adapter geologia/clima/idrologia/soil |
| G. Deep, ecosistemi e dinamiche biologiche | PLANNED per integrazione R6 | Canon/contratti Deep e backends legacy riutilizzabili con verifica | fisica/authority e interfacce causali, mai imporre risultati legacy |
| H. Popoli, civiltà, distribuzione risorse | PLANNED per integrazione R6 | Esperienza R3–R5, non target | co-evoluzione governata con biosfera/ambiente/Deep |
| I. Produzione WORLD_HISTORY 210 Ma -> 0 ka | BLOCKED | infrastruttura e T0 parzialmente pronti | run su finestre, accoppiamento, verifica, significativa retention, replay/reconstruction |
| J. Analisi, interrogazioni e replay locali | PARTIAL | primitive query/refinement/replay B0 | analisi multi-dominio su storia prodotta e tolleranze autorizzate |

## Dipendenze e parallelismo
I track non sono strettamente seriali. Qualificare ShellSet NON blocca ricerca provider o implementazione di adapter/event extraction. Un provider alternativo può essere valutato se ShellSet non è adatto. Non rifare prove parallele upstream già qualificate per il solo scopo di ripeterle.

## Milestones operativi prossimi
1. Acquisire F2-A recovery sealed via GitHub LFS, verificare manifest, ri-eseguire F2A-V recovery offline in output nuovo; ottenere `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION` solo se tutti i check PASS. No nuovo MPI per correggere il CSV.
2. Adjudication numerica F2A-V (asimmetria, scala, dominanza, IEEE, DOF mapping). Decisione se F2-B, aggiustamento strettamente ingegneristico, o altro approccio.
3. Qualifica di un solve **solo su autorizzazione esplicita**, con criteri residui/condizionamento/interpretazione, separata da validazione fisica ARCANA.
4. Definizione interfaccia e copertura dei gap del provider tettonico in ARCANA; parallelamente qualificare altri provider ambientali.
5. Prima finestra candidata multistrumento noncanonizzata -> eventi/stati selezionati -> ricostruzione dimostrata -> eventuale pubblicazione canonica.

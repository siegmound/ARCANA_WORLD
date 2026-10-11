# Roadmap R6 — dipendenze e gates, non roadmap a timestep fissi
**Aggiornata:** 2026-10-10. Stati: `EVIDENCED` = verifica nel proprio scope; `PARTIAL` = lavoro qualificato ma gap; `BLOCKED` = autorità o evidenza insufficiente; `PLANNED` = da realizzare. Evitare percentuali arbitrarie.

| Track | Stato | Completato / riferimento | Gap e next gate |
|---|---|---|---|
| A. Governo e architettura ARCANA | PARTIAL | R6 contratti T0, dominio, authority/provenance, schemi storia; `VISION.md` | Portare adapter+scheduler+pubblicazione a esecuzione qualificata |
| B. WORLD_HISTORY core | EVIDENCED nel scope | B0 HistoryStore/query/replay/refinement/retention; B6M0 T0 genesis a 210 Ma in store governato | closure replay per più domini e finestre reali |
| C. Prima cinematica / rift B6 | PARTIAL/BLOCKED | B6K candidato isolato; B6N4-A significatività; B6N6 contratto temporale adattivo | B6N5 autorità evoluzione post-rift `UNKNOWN_NOT_GOVERNED`; non inventare dt2 |
| D. ShellSet runtime upstream | EVIDENCED nel scope | Fair: esempi stock, 9/9 modelli, esecuzione parallela, LAPACK smoke; carico runtime ARCANA qualificato separatamente | Non equivale a ARCANA T0 full mechanics |
| E. ShellSet ARCANA SI1/BW1 | PARTIAL/BLOCKED | BW0/F1; F2-A/F2A-V; D1A/D1B; D2; D3–D3D-RO6; N1/T1; N2A; N2B synthetic cross-language fixture PASS separately reported with GNU Fortran 13.3 and NVFORTRAN 25.11 | Synthetic interop does not qualify real SI1 capture, solver, numerical acceptance or Fair resources. Proposed next F2B-N2C: default-disabled post-VBCs/pre-Solver A0/b0 snapshot capture, offline fixtures only, explicit FEM-call/iteration binding and fail-closed gate. All scientific and Solver prohibitions remain. |
| F. Modelli ambientali e risorse | PARTIAL/BLOCKED | BIOME4 input contract frozen; HRAB/parent-material research legacy da rivalutare come riuso | provider temporalmente idonei, adapter geologia/clima/idrologia/soil |
| G. Deep, ecosistemi e dinamiche biologiche | PLANNED per integrazione R6 | Canon/contratti Deep e backends legacy riutilizzabili con verifica | fisica/authority e interfacce causali, mai imporre risultati legacy |
| H. Popoli, civiltà, distribuzione risorse | PLANNED per integrazione R6 | Esperienza R3–R5, non target | co-evoluzione governata con biosfera/ambiente/Deep |
| I. Produzione WORLD_HISTORY 210 Ma -> 0 ka | BLOCKED | infrastruttura e T0 parzialmente pronti | run su finestre, accoppiamento, verifica, significativa retention, replay/reconstruction |
| J. Analisi, interrogazioni e replay locali | PARTIAL | primitive query/refinement/replay B0 | analisi multi-dominio su storia prodotta e tolleranze autorizzate |

## Dipendenze e parallelismo
I track non sono strettamente seriali. Qualificare ShellSet NON blocca ricerca provider o implementazione di adapter/event extraction. Un provider alternativo può essere valutato se ShellSet non è adatto. Non rifare prove parallele upstream già qualificate per il solo scopo di ripeterle.

## Milestones operativi prossimi
**Evidence transport checkpoint 2026-10-10:** D3D Windows access-blocked report remains immutable and valid for that attempt. Later RO1–RO6 Fair selected-member results are consolidated in `docs/arcana/SI1_BW1_F2B_D3D_RO6_FAIR_EVIDENCE_CONSOLIDATION.md`; they are not full-manifest validation or scientific promotion. Preserve all no-Solver gates. Next actions: optional historical accounting retrieval; separate numerical residual/threshold authority; separate operator authorization before any Solver.

1. **DONE 2026-10-10:** F2-A sealed + F2A-V offline recovery, 139 PASS / 2 SKIP e adjudication offline; outcome GO **design** F2-B, NO solve. **DONE:** codice Windows `61dad0fa`; PR #1 ledger integrato e derived recovery pubblicata come Git LFS evidence `2b03fa558b02cb865c4f234e45f0386fab678822`; D3A, D3B-P0, D3C e acquisizione RO1–RO6 documentate nei rispettivi scope. Nessuna esecuzione HPC autorizzata.
2. **DONE, scope distinto:** F2B-D1A — mapping/permutazione, FEG/runtime e staging F2A-V; manifest `5002d7bdb1c24d7d3c945b4edc1970b45c86b6daffb55268b67201616ea6653a`. **DONE, source audit:** F2B-D1B — slot 1 South/+theta, slot 2 East/+phi nel frame ShellSet storico. Restano UNKNOWN attribuzione geografica/plate delle dieci asimmetrie e autorità ARCANA del frame. **DONE:** D2 `OPERATOR_CLASS_UNVERIFIED`, simmetria teorica SI1 `INDETERMINATE`; D3–D3C completi nei rispettivi scope. **PROSSIMI WORKSTREAM DISTINTI:** (a) acquisizione read-only di eventuale accounting storico esistente; (b) autorità per residuo e criteri numerici F2B; (c) gate separato di qualifica/autorizzazione dell'operatore prima di qualsiasi Solver. Nessun nuovo job/run, MPI, Solver, fattorizzazione o gauge.
3. Futura qualifica di un solve **solo dopo un nuovo gate di autorizzazione esplicita** con criteri di residuo/errore/risorse e validazione fisica ARCANA separata.
4. Definizione interfaccia e copertura dei gap del provider tettonico in ARCANA; parallelamente qualificare altri provider ambientali.
5. Prima finestra candidata multistrumento noncanonizzata -> eventi/stati selezionati -> ricostruzione dimostrata -> eventuale pubblicazione canonica.

## Aggiornamento F2B-D3B-P0 (2026-10-10)
D3B-P0 consolidato con `D3B_P0_REVIEW_PASS_WITH_BOUNDED_SCOPE`: 24 test PASS, 2 SKIPPED per impossibilità di creare symlink nel runtime Windows, zero failure. La garanzia TOCTOU è riferita ai byte snapshot autenticati; test runtime POSIX e atomicità delle sostituzioni concorrenti Windows non attestati. D3C ha completato la ricognizione locale senza accesso Fair. Il tentativo D3D è bloccato perché non esiste accesso Fair in questo contesto; esistenza e disponibilità dei file remoti non sono state verificate. Il prossimo passo è l'handoff all'operatore già autorizzato per acquisire evidenze preesistenti, senza nuovo run. ABI NVHPC F2A-V, RSS/memoria/enforcement Fair e qualificazione operatore restano aperti. Solver non autorizzato.

## F2B-N1 / N1-T1 (2026-10-11)
N1 definisce le precondizioni numeriche ma l'accettazione resta non attestata (`N1_NUMERICAL_PRECONDITIONS_DEFINED__ACCEPTANCE_NOT_YET_ATTESTED`; `THRESHOLD_UNJUSTIFIED`). T1 passa soltanto la prova sintetica di snapshot A0/b0 separati da buffer operativi distruttivamente sovrascritti (9 passed); non prova il percorso ShellSet reale. Prossimo: F2B-N2, design/review di una strategia di preservazione verificabile senza presumere memoria HPC. `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, Solver/mechanics/WORLD_HISTORY gates restano invariati.


## Aggiornamento F2B-N2A-R1 (2026-10-11)
N2A-R1 `N2A_SPARSE_SNAPSHOT_SYNTHETIC_VERIFIED__SI1_INTEGRATION_NOT_QUALIFIED`: test sintetici passati, nessuna qualificazione SI1 o modifica Fortran. Il prossimo lavoro proposto è N2B, design offline del contratto di cattura A0/b0 post-VBCs e fail-before-Solver. Le risorse Fair, la strategia di identità reale, `THRESHOLD_UNJUSTIFIED`, `OPERATOR_CLASS_UNVERIFIED` e il blocco F2A-V restano aperti; Solver non autorizzato.


## Stato preliminare N2B prima della verifica runtime NVFORTRAN (storico; superato dall'aggiornamento N2B-V)
N2B GNU cross-language interop è riportato dall'operatore Fair come `N2B_SYNTHETIC_CROSS_LANGUAGE_INTEROP_PASS__SI1_CAPTURE_NOT_QUALIFIED` (21 passed, exit 0) sul commit `9ebc78bbccc6ae5cb64eac15b67fd88f4c9ea406`; il log resta su Fair e il digest non è stato ricalcolato in Windows. NVFORTRAN 25.11-0 ha soltanto compilato la fixture (`N2B_NVFORTRAN_FIXTURE_COMPILE_PASS`): runtime interop non dimostrata. Prossimo proposto F2B-N2B-V: runner Windows con scelta esplicita GNU/NVFORTRAN e flag specifici; seguire il workflow sezione G di `PROCEDURE.md`. Nessuna promozione SI1; gate Solver e scientifici invariati.


## Aggiornamento F2B-N2B-V (2026-10-11)
GNU Fortran 13.3 ha superato 21 test fixture sul commit `9ebc78bbccc6ae5cb64eac15b67fd88f4c9ea406`; NVFORTRAN 25.11 ha superato 29 test fixture sul commit `2d6021ff0036d350b12a583d9eff1d03e32a7239`. Esiti/log SHA sono riferiti dall'operatore Fair, non ricalcolati in Windows. `N2B_SYNTHETIC_CROSS_LANGUAGE_INTEROP_PASS__SI1_CAPTURE_NOT_QUALIFIED`; nessuna promozione SI1. Next F2B-N2C è la cattura diagnostica sintetica, disabilitata per default e fail-closed post-VBCs/pre-Solver; non autorizza Fair o Solver.

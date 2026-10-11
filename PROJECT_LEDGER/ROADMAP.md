## F2B-N2C-W3-C-C — review avversariale (2026-10-11)
- `W3C_C_REVIEW_REQUIRES_TARGETED_CORRECTIONS`. Il modello accetta `pure_call_sequence=2` pur asserendo first-Pure-call, accetta Boolean `worker_rank`, e il Solver boundary è un rifiuto costante non collegato a un evento FEM né alla latch. Riferimenti e riproduzioni: `docs/arcana/SI1_BW1_F2B_N2C_W3C_ADVERSARIAL_PROTOCOL_REVIEW.md`.
- Next: W3-C-B-R1, correzione e regressioni offline circoscritte. W3-B/C restano sintetici; nessuna prova MPI-wide o runtime. Tutti i gate di esecuzione/scienza restano bloccati.

# Roadmap R6 — dipendenze e gates, non roadmap a timestep fissi

## F2B-N2C-W3-A — contratto provenance (2026-10-11)
- **W3-A DESIGN_DEFINED:** `W3A_IDENTITY_CONTRACT_DEFINED__RUNTIME_BINDING_AND_MPI_WIDE_STOP_UNPROVEN`; contratto byte-esatto SHA256 `6f94d4cbcda52eab351e1aa106bcd7d2c1c25f00b78834d2b2b7f3f8d41e2df9`. `ModNum` non è un ID autorevole, `rpeat=0` ammissibile nel caso SF, rank 0 coordinatore, stop W2 soltanto locale nel codice, non MPI-wide.
- **E1 preservato:** 103/103 hash/membership e 14+2 oggetti NVFORTRAN compile-only riferiti dall'operatore Fair; nessuna prova di esecuzione.
- **NEXT W3-B:** context owner-backed + validator e fixture offline in isolamento, fail-closed; nessun MPI/ShellSet/Solver runtime. **W4 distinto:** codec streaming, I/O e risorse reali SI1; blocchi scientifici invariati.


## N2C-W2-E1 — verifica checksum, source e oggetti (2026-10-11)
- **E1 EVIDENCED, operator-reported Fair:** `sha256sum -c` exit 0, 103 voci corrispondenti a 103 file; audit sorgenti/manifest e 14+2 oggetti concluso `E1_SOURCE_AND_OBJECT_INTEGRITY_PASS`. Fonte `FAIR_EXTERNAL_EVIDENCE` e SHA primari in `EVIDENCE_INDEX.md`. Nessun rehash indipendente dei file in Windows.
- **W2 stato:** NVFORTRAN 25.11 compile-only, source identity `fcb94f5c...`; **nessun linker/runtime** e nessun sistema A0/b0 SI1 verificato. Il precedente record di compilazione è preservato.
- **NEXT W3:** contratto di identità autorevole, invocation/sidecar/digest con test offline e fail-closed; rank 0 MPI legittimo. **W4 distinto:** scala codec, I/O/risorse. Ogni gate scientifico/Solver invariato.


## N2C-W2 — Fair NVFORTRAN compile-only operator-reported (2026-10-11)
- **W2 COMPILE-ONLY reported PASS, NON runtime:** `mpifort` con backend `nvfortran 25.11-0`, OpenMPI 4.1.9a1, 14/14 oggetti; writer+bridge exit 0, full candidate exit 0. Commit codice `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`; evidenze Fair fuori checkout in `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2C_W2_COMPILE_ONLY/W2_NV_20261011T132801Z_juuO3l`; hash/log da riconciliare con E1.
- **W2 E1 (NEXT):** raccolta mirata e verifica read-only di `RESULT.txt`, `SHA256SUMS.txt`, manifest e log preesistenti. Non ripetere la compilazione per produrre evidenza mancata.
- **W3/W4:** restano separati e bloccati; nessuna autorità runtime/provenance/scala SI1 derivata dal compile PASS. `RESOURCE_2GB_SCOPE_UNRESOLVED`. Tutti i divieti Solver/mechanics/WORLD_HISTORY persistono.


## N2C-W2 checkpoint — 2026-10-11
- **W1 EVIDENCED sintetico:** 25/25 GNU + 25/25 NVFORTRAN su fixture, commit `7a411911`; nessuna integrazione runtime ShellSet.
- **W2 IMPLEMENTED / COMPILE PENDING:** overlay source-locked isolato, 15 membri + parametro verificati dal builder, gate dopo VBCs prima di Solver, Windows 13 PASS / 1 SKIP, commit `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e` su GitHub e Fair detached HEAD. Fair preflight toolchain/CLI completato, ma compilazione candidata NON eseguita.
- **Prossimo gate W2:** generazione di candidate copy nuova fuori checkout; manifest/SHA; compile-only bridge e call graph completo, con toolchain idonea e log esterni. Niente eseguibile ShellSet o MPI run; stop in assenza di autorità.
- **W3 BLOCKED:** identità autorevole run/model/rank/input/state/build/DOF e sidecar, una FEM invocation specifica; nessun ID fittizio.
- **W4 BLOCKED:** adeguamento codec/validator a `n=128884`, `LDAB=2182`, 281224888 elementi AB e I/O/verifica grandi file. `RESOURCE_2GB_SCOPE_UNRESOLVED`; niente tetto RAM arbitrario, W1 `MAX_STORAGE=2000000` indica elementi.
- Invariati tutti i gate F2A-V, Solver, mechanics e WORLD_HISTORY.

**Aggiornata:** 2026-10-11. Stati: `EVIDENCED` = verifica nel proprio scope; `PARTIAL` = lavoro qualificato ma gap; `BLOCKED` = autorità o evidenza insufficiente; `PLANNED` = da realizzare. Evitare percentuali arbitrarie.

| Track | Stato | Completato / riferimento | Gap e next gate |
|---|---|---|---|
| A. Governo e architettura ARCANA | PARTIAL | R6 contratti T0, dominio, authority/provenance, schemi storia; `VISION.md` | Portare adapter+scheduler+pubblicazione a esecuzione qualificata |
| B. WORLD_HISTORY core | EVIDENCED nel scope | B0 HistoryStore/query/replay/refinement/retention; B6M0 T0 genesis a 210 Ma in store governato | closure replay per più domini e finestre reali |
| C. Prima cinematica / rift B6 | PARTIAL/BLOCKED | B6K candidato isolato; B6N4-A significatività; B6N6 contratto temporale adattivo | B6N5 autorità evoluzione post-rift `UNKNOWN_NOT_GOVERNED`; non inventare dt2 |
| D. ShellSet runtime upstream | EVIDENCED nel scope | Fair: esempi stock, 9/9 modelli, esecuzione parallela, LAPACK smoke; carico runtime ARCANA qualificato separatamente | Non equivale a ARCANA T0 full mechanics |
| E. ShellSet ARCANA SI1/BW1 | PARTIAL/BLOCKED | BW0/F1; F2-A/F2A-V; D1A/D1B; D2; D3–RO6; N1/T1; N2A/N2B; W1 25/25 per toolchain; W2 NVFORTRAN compile-only; E1 103/103 Fair operator-reported; W3-A; W3-B/B1; W3-C-A; W3-C-B synthetic coordinator model (21 focused tests); W3-C-C adversarial review found target-coordinate and Solver-boundary gaps | W3-C-B-R1 targeted offline correction next; owner/runtime authority, MPI-wide agreement/stop, identity A0/b0, runtime linking and operator class/thresholds remain unproven; W4 size/I/O separate. Nessuna autorità Solver/World History. |
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


## F2B-N2C-W3-B — synthetic owner binding validator (2026-10-11)
- `W3B_SYNTHETIC_OWNER_BINDING_VALIDATOR_PASS__RUNTIME_AUTHORITY_UNKNOWN`; typed fixture contexts, synthetic evidence joins, N2A/N2C payload oracle integration and simulated worker coordination. The implementation is published at `2bb34525c4098eded5ee65eca02428c92d5c68b3`; the former `WINDOWS_WORKTREE_ONLY` label is stale and corrected in the current ledger.
- B1 semantic correction permits multiple unique FEM calls under one immutable assignment, rejects reused physical coordinates independent of state/system/payload/sidecar contents, rejects conflicting assignment-sequence model/worker/owner bindings, and validates a terminal capture-state transition. Current focused regression suite: 41 passed, 1 compiler skip; no runtime authority follows.
- No production owner authority, real callgraph binding, payload persistence, MPI-wide stop, SI1 codec scale, resource attestation or runtime was established. W4 remains separate.
- **Next W3-C:** specify real owner-provider binding and coordinated job-wide capture/abort authority before any candidate runtime integration. Gates remain blocked and execution unauthorized.
## F2B-N2C-W3-C-A — authority owner / coordinated-stop design (2026-10-11)
- **Complete, design-only:** `W3C_A_DESIGN_COMPLETE__RUNTIME_AUTHORITY_AND_MPI_STOP_UNPROVEN`; report `docs/arcana/SI1_BW1_F2B_N2C_W3C_RUNTIME_AUTHORITY_AND_MPI_STOP_DESIGN.md`.
- Source call graph establishes local rank/dispatch/call coordinates and post-VBCs/pre-Solver boundary, but no owner-backed run/attempt, immutable assignment/model, effective state/constraints, linked executable/process, runtime DOF order, independent system digest, or all-rank stop authority.
- Proposed first candidate is one selected worker's first reachable FEM boundary under an immutable job-wide no-Solver decision, with coordinator/all-rank digest ACK and terminal-status/stop handshake. MPI failure and launcher semantics remain unverified. W3-B synthetic tests are not runtime proof.
- **Next proposed:** W3-C-B offline typed decision/coordinator state-machine and negative tests. It grants no ShellSet/MPI/Fair/Solver authorization. W4 remains separate.

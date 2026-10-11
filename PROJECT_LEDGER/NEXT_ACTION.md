# NEXT: F2B-N2C-W3-C — real owner authority and coordinated-stop contract

## W3-B completion (offline synthetic scope only)
`W3B_SYNTHETIC_OWNER_BINDING_VALIDATOR_PASS__RUNTIME_AUTHORITY_UNKNOWN`. Report: `docs/arcana/SI1_BW1_F2B_N2C_W3B_OFFLINE_INVOCATION_BINDING.md`. The typed validator binds synthetic owner envelopes to run/attempt, process/role/rank, master assignment/model, SH/SF and Shells/Pure/iteration/FEM sequence, effective input/state/constraints, implementation/build, DOF order, and A0/b0 identity. It reuses N2A decoding plus N2C independent-oracle verification.

Windows offline regressions: W3-B + N2A + N2C writer + W2 overlay = 34 passed, 1 skipped, 0 failed; the skip is the compiler-dependent Fortran writer execution (`gfortran` unavailable). `py_compile` and diff/encoding checks passed. No production identity, ShellSet runtime binding, snapshot publication, MPI-wide stop, SI1 capture, or Fair execution was established.

Current changes remain `WINDOWS_WORKTREE_ONLY`: GitHub DNS prevented verification of the remote branch, so no commit/push has occurred. First review and publish the explicit W3-B code/test/report/ledger set after a successful fetch and fast-forward check.

## Next bounded task: W3-C design/implementation gate
Before candidate integration, define and review a real authority provider for run/job, master-issued assignment and stable model, communicator/process role, effective inputs/state/constraints, candidate build/executable, DOF ordering, and independent A0/b0 oracle. Specify one job-scoped capture-mode decision and coordinated worker failure/stop; the W3-B synthetic coordinator is only a model. W3-C must remain offline/static until separately authorized. Do not alter W1/W2 or invoke ShellSet, MPI, Solver, Fair, or SI1. W4 scale/streaming/durability/resource work remains a separate gate.

## Preserved gates
`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

---

## Storico: incarico precedente W3-A (completato come contratto)

## Stato verificato e fonte
- W2 source commit `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`; E1 `N2C_W2_E1_FAIR_OPERATOR_REPORTED_INTEGRITY_PASS__RUNTIME_NOT_QUALIFIED`. Su Fair checksum manifest 103/103, `CHECKSUM_EXIT=0`, controllo Python `E1_SOURCE_AND_OBJECT_INTEGRITY_PASS`, 14 oggetti intero candidate call graph e 2 bridge objects, builder/manifest e source lock/15 membri conformi secondo transcript dell'operatore.
- Il risultato è un **PASS locale Fair riferito dall'operatore**, non prova autonoma Windows; hash primari e locator in `EVIDENCE_INDEX.md`. Compilazione W2 con NVFORTRAN 25.11, senza linking, runtime MPI, ShellSet, Solver o DGBSV.
- Non ripetere W2 per abitudine. Nessuna autorizzazione a run diagnostici o produzione deriva da questa chiusura.

## Prossima attività: W3, prima design/review con Codex Windows
1. Audit sorgenti/contratti del punto `ShellSetMain → Shells_v5p0 → Pure → FEM` e dei provider/authority già presenti: individuare gli **owner autentici** dei metadati di `run_id`, `model_id`, communicator rank (0 incluso), `rpeat`, iterazione e ordinale FEM, input/state/constraint digest, source/build identity e DOF-order. I cinque campi locali W2 non sono sufficienti. Non creare ID fittizi o source digest forniti dal solo writer.
2. Definire contratto tipizzato per associazione univoca `FEM invocation → A0/b0`, sidecar, digest indipendente e validatore di provenienza; flag UNKNOWN e fail-closed obbligatori quando un'autorità manca. Dichiarare la semantica e l'ambito del rank MPI 0: nel W2 attuale `process_rank < 1` rifiuta erroneamente rank 0 se usato in `CAPTURE_ONLY`.
3. Definire test sintetici di validazione positiva/negativa del contratto e dell'assenza di attraversamento del gate pre-Solver. Verificare incompleti, duplicati/collisioni, mismatch di snapshot/sidecar, interleaving rank/modello/iter/FEM, stato/source/build/DOF incompatibili e digest non autenticati. Nessuna esecuzione ShellSet/MPI/Solver; eventuali modifiche al codice solo dopo audit e scope approvato, via Codex Windows → commit/push → Fair.
4. W4 separato per `n=128884`, `LDAB=2182`, `281224888` elementi, streaming/durabilità, file e quote scheduler. Nessun cap RAM universale 2 GB (`RESOURCE_2GB_SCOPE_UNRESOLVED`).

## Invarianti
- `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`
- `RUNTIME_CAPTURE_AUTHORIZED=false` come vincolo operativo; nessuna pubblicazione canonica. Il nuovo W3 è progettazione offline, non autorizzazione ad assemblare/catturare SI1.

---

## Storico: piano W2-E1 read-only completato (2026-10-11)

# NEXT: F2B-N2C-W2-E1 — riconciliazione read-only evidenze compile-only Fair

## Checkpoint e risultato
- 2026-10-11, Fair, checkout W2 `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`: operatore riporta `N2C_W2_NVFORTRAN_COMPILE_ONLY_OPERATOR_REPORTED_PASS__RUNTIME_NOT_QUALIFIED` e marker `PASS_N2C_W2_NVFORTRAN_COMPILE_ONLY_CANDIDATE`.
- `BRIDGE_COMPILE_EXIT=0`, `FULL_COMPILE_EXIT=0`, `FULL_OBJECT_COUNT=14`, `EXPECTED_FULL_OBJECTS=14`; `LINK_PERFORMED=false`; `SHELLSET_MPI_SOLVER_RUNTIME_EXECUTED=false`. Wrapper `mpifort` ripristinato nel PATH sessione, backend `nvfortran 25.11-0`, OpenMPI 4.1.9a1.
- `FAIR_EXTERNAL_EVIDENCE`: `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2C_W2_COMPILE_ONLY/W2_NV_20261011T132801Z_juuO3l`. Log/manifest/SHA esistono secondo lo script e il transcript, ma **non** sono stati letti o rehashati fuori da Fair; compilazione qualificata solo come **operator-reported compile-only**. Il precedente W2 `COMPILE PENDING` resta storico, superato per il solo scope NVFORTRAN compile-only.

## Unico prossimo incarico (sola lettura, nessuna nuova compilazione)
1. Sul path Fair già esistente, leggere `RESULT.txt`, `SHA256SUMS.txt`, `PREFLIGHT.txt`, `candidate/N2C_W2_CANDIDATE_OVERLAY.json`; riportare conteggi, SHA e membership dei file, e sezioni circoscritte di `builder.log`, `bridge.log`, `full_compile.log`. Non dare per acquisiti byte/hash dalla sola console precedente.
2. Controllare senza modificare che gli SHA listati corrispondano agli artefatti esistenti, che manifest e sorgente blocchino alle identità note e che 14 oggetti siano presenti; preservare path e log originari. Se manca una prova, registrare UNKNOWN, non rigenerarla di nascosto.
3. Consolidare il nuovo record documentale su Windows tramite procedura ledger; nessun commit di output voluminosi sul branch codice. Non usare `git add .` / `git add -A`; nessun nuovo job, `mpiexec`, linking, ShellSet run, MPI run, Solver/DGBSV o WORLD_HISTORY.
4. **Dopo** l'adjudication evidenze, definire W3: binding autorevole run/model/rank/rpeat/iter/FEM-call/input/state/source/build/DOF, sidecar, SHA indipendente, semantica rank MPI 0. W4 distinto: codec e I/O a scala SI1, misure e budget veri. Modifiche codice solo via Codex Windows → GitHub → Fair.
5. Rimangono `RESOURCE_2GB_SCOPE_UNRESOLVED`, `THRESHOLD_UNJUSTIFIED`, `OPERATOR_CLASS_UNVERIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

---

## Storico: piano precedente di integrazione W2 (superato dal commit fcb94f5c)


## Stato N2C-W1
Decisione `N2C_W1_SYNTHETIC_FORTRAN_CAPTURE_CROSS_COMPILER_PASS__SI1_INTEGRATION_NOT_QUALIFIED`: 25 passed per GNU Fortran 13.3 e 25 passed per NVFORTRAN 25.11, entrambi sul commit `7a4119112a16e32c8cbdae5248ebd91f4020a458`, Fair Conda `arcana-r6-linux`, Python 3.12.14 / pytest 9.1.1. Esiti e SHA dei log sono riferiti dall'operatore; Codex Windows non ha letto i log remoti. I precedenti run falliti sul commit `57b2bd1f` restano storici e distinti; il cwd dell'harness è stato corretto nel commit testato.

## Incarico immediato proposto: F2B-N2C-W2
Progettare un overlay candidato separato dal source lock storico per collegare il writer W1 al punto ShellSet post-`VBCs` e pre-`Solver`. Prima di implementare, chiudere/documentare questi requisiti:

1. Propagazione verificabile dell'identità worker → ciclo FEM e binding autorevole di run, modello, rank, rpeat, iterazione, stato di ingresso, input e ordinamento DOF.
2. Sidecar/metadati d'invocazione e validazione esterna del payload; il digest B ricevuto dal writer non è prova autonoma.
3. Stop obbligatorio prima di Solver per `CAPTURE_ONLY` e per ogni fallimento, dimostrato nel flusso candidato.
4. Separazione esplicita dal source lock storico tramite identità e build della variante candidata.
5. Verifica dell'applicabilità al sistema SI1: i limiti dimensionali correnti sono quelli del codec/test sintetico e non budget RAM Fair; risorse e enforcement vanno attestati separatamente, senza cap arbitrari.

Per W2 mantenere review/sviluppo su Windows e workflow `PROCEDURE.md`. Nessun test Fair, build ShellSet, run SI1, MPI o Solver è autorizzato implicitamente dal PASS W1.

Preservare `THRESHOLD_UNJUSTIFIED`, `OPERATOR_CLASS_UNVERIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

---

## Storico next action precedente

## Stato RO6
Il JSON RO6 e sidecar hanno SHA256 locale concorde; report consolidato `docs/arcana/SI1_BW1_F2B_D3D_RO6_FAIR_EVIDENCE_CONSOLIDATION.md` (SHA256 `1b9c46b43079fbc5002d3719bc935175cd6f1bea5489f6026abe7d870e1a4579`). Decisione `D3D_FAIR_EVIDENCE_RECOVERED__RESOURCE_ATTESTATION_INCOMPLETE`. Ciò avanza la provenance dei membri selezionati, non la qualifica scientifica. Il D3D bloccato resta valido per il precedente tentativo Windows.

## Next workstreams — distinti e non esecutivi
1. **Acquisizione accounting storico (opzionale, sola lettura):** consultare solo record preesistenti se un job ID o locator puntuale è disponibile. Il mancato ritrovamento nei percorsi RO5 non prova assenza globale. Nessun nuovo job o uso della configurazione corrente come proxy.
2. **Residuo e criteri numerici F2B:** definire e giustificare il contratto di residuo/backward error e le eventuali soglie; `THRESHOLD_UNJUSTIFIED` resta. I test sintetici non qualificano SI1.
3. **Qualifica operatore prima di Solver:** gate separato con autorizzazione esplicita, dopo revisione dei prerequisiti numerici e delle risorse. Solver non autorizzato.

La pubblicazione distinta di JSON+sidecar+manifest nel solo evidence branch può essere proposta dopo review; non fare commit/push automatici né includere `outputs/` nel commit codice.

### Handoff storico: operatore Fair autorizzato

## Stato D3D
`D3D_BLOCKED_EXISTING_EVIDENCE_UNAVAILABLE` / `REMOTE_EVIDENCE_ACCESS_UNAVAILABLE`. Nessun accesso Fair è stato fatto e nessun artefatto è stato acquisito; non è stata verificata l'esistenza dei file remoti. Il blocco è di accesso da questo ambiente, non prova di assenza delle evidenze.

## Procedura per operatore con accesso Fair già autorizzato
Non richiedere credenziali e non stabilire connessioni alternative. Se l'accesso già autorizzato non è disponibile, fermarsi senza eseguire comandi remoti. Leggere soltanto questi locator, separatamente e a profondità limitata:

```text
$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2AV_COMPILE_ONLY/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T125317Z
$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2AV_RUN/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z
```

Per ciascun locator, inventariare solo file/metadati preesistenti (niente scansioni ricorsive estese). Cercare con priorità binario e identità build, log di compilazione/link, comando effettivo, toolchain/flags, nomi/hash delle librerie e accounting storico/job ID. Non eseguire il binario, `--version`, MPI, compile o job. Non assumere che compile-only e run usino lo stesso eseguibile.

Per ogni file effettivamente letto/acquisito annotare host, path, identificatore del run, metodo e data di acquisizione, dimensione e SHA256 dei byte letti, eventuale digest storico indipendente e confronto. Un hash del file corrente prova solo i byte acquisiti ora, non il collegamento al processo storico senza evidenza contemporanea. Prima identificare scheduler/job ID dai record esistenti; poi consultare solo l'accounting di quel job. Non usare configurazione corrente come prova storica. Se un dato non è nei record, lasciarlo UNKNOWN; non dichiarare file remoto assente senza averne verificato il path.

Conservare gli artefatti acquisiti in una directory locale nuova con manifest solo se vi sono file realmente acquisiti. Se non è disponibile una sessione già autorizzata, chiudere il tentativo con `REMOTE_EVIDENCE_ACCESS_UNAVAILABLE`; nessun run HPC sostitutivo.

## F2B-D3C completato — ricognizione locale delle evidenze runtime/risorse
Decisione `D3C_RECONNAISSANCE_COMPLETE__EXECUTION_AUTHORITY_GAPS_REMAIN`; report `docs/arcana/SI1_BW1_F2B_D3C_FAIR_RUNTIME_RESOURCE_RECONNAISSANCE.md`, SHA256 `76a5a65adbbc7d6a9b6a64b35497ee9cd3f4642f286d672579d2779f7f53d058`.

Risultato: il runtime upstream qualificato non è il runtime F2A-V per identità dimostrata. L'eseguibile F2A-V non ha hash verificato; toolchain, ABI e linkage dinamico effettivi non sono attestati. Nessun eseguibile F2B è stato identificato. RSS/PSS/cgroup e limiti Fair effettivamente imposti restano sconosciuti; le formule D3A sono stime condizionali. I due test symlink sono ancora `NOT_TESTED_RUNTIME_WINDOWS`. D3C non ha acceduto a Fair né avviato job.

### F2B-D3D — acquisizione di evidenze Fair preesistenti
Proposta limitata a leggere e verificare artefatti già prodotti: identità/hash del binario F2A-V e build/link metadata, toolchain/librerie/ABI attestabili, scheduler/process/cgroup limit records, rank/PID e misure RSS/PSS già disponibili. Non avviare job o processi, non compilare, non eseguire MPI/ShellSet/Solver né diagnostici numerici. Se una prova non esiste negli artefatti preesistenti, registrarla come gap e richiedere un'autorizzazione separata per l'acquisizione necessaria. La verifica POSIX dei due casi symlink è requisito separato e non è prova Fair.

Questo next gate non autorizza build, job, Solver, diagnostici numerici, mechanics o evoluzione canonica.

## F2B-D3B-P0 completato — review circoscritta
Decisione: `D3B_P0_REVIEW_PASS_WITH_BOUNDED_SCOPE`; source baseline parent `f571516ce09c726bffd262d172a922968bdab944`; implementazione dei quattro validator/test inclusa nel commit documentale corrente. SHA256: resource validator `cae86cd5d16d3f4633d45a9ae4ffb6a9808838c41fd2c8ac6e3bf317f5c548ae`; numerical validator `275714d7615cffa062c8ac1d4a992edd5a2070744653a6b4cf0cfec914e7b46e`; resource tests `7e2ddf108836229e79475ffe47b2f2cd19d256beaa8459bd51451b93b1c2fec1`; numerical tests `5b00d4a6b4220b0675183e43a1f028572a437825bfc383ce55d3b9cd1a8ce8aa`.

Esito suite D3B-P0: 24 PASS, 2 SKIPPED, 0 FAIL. I rilievi della prima review e il TOCTOU HIGH sono chiusi nello scope offline. I due test symlink sono `NOT_TESTED_RUNTIME_WINDOWS` (creazione negata); WSL è risultato inaccessibile. La prova POSIX dir-fd/O_NOFOLLOW non è stata eseguita. Atomicità contro sostituzioni concorrenti Windows, ABI NVHPC, RSS/memoria ed enforcement Fair restano non attestati. Il validatore non autentica oggetti Git storici. Nessuna qualificazione del caso SI1 reale.

**Proposta storica D3C (completata; esito sopra), ricognizione read-only:** identità/hash dell'eseguibile e librerie collegate, ABI, richieste e enforcement scheduler, limiti memoria/tempo, evidenze RSS/PSS/cgroup. Se disponibile un ambiente POSIX appropriato, verificare separatamente i controlli runtime symlink. Non avviare job Fair, MPI, ShellSet o Solver.

Preservare: `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

---

## Storico workpack D3B-P0

**Completed D3A audit:** `docs/arcana/SI1_BW1_F2B_D3A_ATTESTABILITY_AUDIT.md`, SHA256 `CA2FF09491BBDCB995FC79FB9E4CF66B461C519A2FC67F652E09099C70884989`; result `D3A_AUDIT_COMPLETE__SOLVER_PREFLIGHT_NOT_ATTESTABLE_FROM_CURRENT_EVIDENCE`. D3 report SHA256 `1666D30701D8365CAF7CB8C5C7192C46E04AB19D2C6E9179EE2917DCB056E3FF` and its contents remain unchanged.

**D3 arithmetic erratum:** historical A0/b0-copy estimate was about `4.82684 GiB`; corrected total is `5,183,806,076 bytes + 112 × (LRn+1)` (about `4.82780 GiB` plus LR term). The omitted `1,031,072 bytes` are the complete copied RHS b0. This is an arithmetic correction only; no copies were allocated and no strategy was selected.

Preserve `DOF_MAPPING_PARTIAL`; `DOF_COMPONENT_BASIS_SOURCE_VERIFIED__F2AV_GEOGRAPHIC_ATTRIBUTION_UNADJUDICATED`; `OPERATOR_CLASS_UNVERIFIED`; and original `BLOCKED_F2AV_QUALIFICATION`. `F2B_SOLVER_EXECUTION_AUTHORIZED=false`.

## D3B-P0 workpack

This is an offline Python validator task, not a qualification of the SI1 operator and not Solver authorization. Keep resource and numerical validators separate and use only small synthetic fixtures.

### Resource validator
- Inputs: SI1 dimensions from the engineering contract, explicit ABI widths, and an independently transcribed named-array inventory from D3A. Optional budget scenario is `NO_PRESERVATION`, `COPY_A0_B0`, or a separately specified replayable matvec representation.
- Compute element counts/bytes with checked integer multiplication and addition. Reject negative/invalid dimensions, overflow, missing/unsupported ABI sizes, duplicate/missing inventory rows, formula mismatch, incomplete budgets, or any request to certify peak/total process memory while overhead is UNKNOWN.
- Reconcile each array family independently against D3A; report matrix, fixed arrays, `112*(LRn+1)`, optional preservation increment, and excluded descriptors/compiler temporaries/stack/MPI/LAPACK/allocator/OS overhead separately. Never label a named-array subtotal as a peak or upper bound.
- Positive tests: known SI1 arithmetic; small alternate dimensions; ABI-width cases supported by an explicit schema; the independent A0 and b0 copy deltas. Negative tests: overflow boundaries, absent/mismatched dimension, unsupported ABI, duplicate or missing allocation family, arithmetic disagreement, and an incomplete/UNKNOWN total-memory budget. Acceptance is deterministic arithmetic plus explicit scope/UNKNOWN fields; incomplete required inputs fail closed.

### Numerical validator
- Build tiny general-band matrices in test code and encode LAPACK DGBSV storage: `LDAB=2*KL+KU+1`, diagonal at one-based row `KL+KU+1`. Implement band matrix-vector multiplication and original-matrix norms without invoking DGBSV or any solver. Ignore reserved factorization-fill rows as original coefficients.
- Keep immutable synthetic `A0,b0`; give a destructive mock disposable copies and verify the originals remain byte/value-identical. These fixtures validate arithmetic only and say nothing about SI1 symmetry/operator class.
- Compute `r=b0-A0*x`, `||r||∞`, normwise backward error `||r||∞/(||A0||∞||x||∞+||b0||∞)`, and componentwise backward error `max_i |r_i|/(sum_j |a_ij||x_j|+|b_i|)`. Use robust scaled products/sums or a declared extended/compensated accumulation strategy; report subnormal/underflow behavior and reject silent overflow/underflow or nonfinite operands/results.
- Positive tests: diagonal and off-diagonal bands with nonzero KL/KU, padded storage, exact solution and known nonzero residual; compare against an independent dense reference. Negative tests: shape/index errors; NaN and ±Inf in A0/b0/x; extreme large/small values; overflow/underflow; zero denominator with zero numerator; zero denominator with nonzero numerator. Define the latter as undefined/infinite and fail closed. Do not add an arbitrary pass/fail tolerance.
- Acceptance is only algorithm correctness on synthetic cases, complete special-value classification, and A0/b0 preservation. No synthetic test may qualify or accept the SI1 solve.

### Separate Fair read-only reconnaissance procedure
- Without submitting jobs or launching processes, record executable path/size/SHA256 and existing build identity; compiler, MPI and linked LAPACK identity from available metadata/read-only inspection; scheduler memory/wall-time request; process limits; job/cgroup memory limits and enforcement; rank mapping; and existing per-PID RSS/PSS/cgroup peak evidence.
- Distinguish operator-declared requests, scheduler configuration, enforced limits, and observed measurements. If a value or link identity requires job launch, mark `PENDING_HPC_MEASUREMENT`; do not infer it from upstream ShellSet benchmarks or F2A-V’s pre-Solver stop.

### Prohibitions and gates
- No Fair job, MPI, ShellSet, Solver, factorization, assembly, gauge, simulation, canonical change, or WORLD_HISTORY access.
- Preserve `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, original `BLOCKED_F2AV_QUALIFICATION`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
- D3B-P0 cannot establish numerical acceptance, resource sufficiency, or authority for execution. A later gate must separately close Fair resource enforcement, A0/b0 retention/reconstruction, numerical thresholds, operator/nullspace/gauge questions, and explicit execution authorization.

## Prior D2 handoff (preserved)
F2B-D2 static operator classification audit: `docs/arcana/SI1_BW1_F2B_D2_OPERATOR_CLASSIFICATION_AUDIT.md`. Result `OPERATOR_CLASS_UNVERIFIED`; theoretical SI1 symmetry is `INDETERMINATE`. Active pointwise alpha values are not retained and the ten global asymmetries remain unexplained. Geographic/plate attribution remains `DOF_MAPPING_UNVERIFIED`; original F2A-V remains `BLOCKED_F2AV_QUALIFICATION`. Do not symmetrize the matrix or infer nullspace from diagonal dominance.

## D2 restrictions retained
- Static source/evidence audit only; no Fair, MPI, Solver, factorization, assembly, simulation, gauge change, or canonical/WORLD_HISTORY access or mutation.
- No solver selection, solver authorization, geographic attribution of anomaly indices, conditioning/singularity claim, or scientific qualification.

---
# PRIOR HANDOFF: F2B-D2 — operator semantics and asymmetry reconciliation (design/audit only)

**Completed gate:** F2B-D1B report docs/arcana/SI1_BW1_F2B_D1B_GEOGRAPHIC_BASIS_AUDIT.md, audited at checkout HEAD d539a9ffa281d3dac8489db4820715cb136e9ae6; report SHA256 baa9e450f866f29a42230ad01bd490de6ed6c96f02df3d901e6af77388a41546. The exact historical ShellSet source commit df670c8c4faaed641997f5c4bdb701e2ba0afc7d establishes slot 1 = +South/+theta and slot 2 = +East/+phi, with matching inspected assembly, forcing, boundary-condition and output paths. This does not adjudicate the ten asymmetry pairs or ARCANA frame authority. Preserve DOF_MAPPING_UNVERIFIED for anomaly-to-geography/plate/physical attribution and preserve BLOCKED_F2AV_QUALIFICATION.

## Next scope
F2B-D2 should examine expected operator semantics, assembly/linearization, boundary treatment, and the ten asymmetry records without inferring cause from their indices. F2B-D3 resource/residual design remains a separate gate. This is a recommendation only; it authorizes no Fair/MPI/Solver/factorization/gauge/simulation.

## D1B restrictions retained
- Audit was static/read-only. No Fair, MPI, Solver, factorization, gauge, assembly, simulation, or canonical/WORLD_HISTORY mutation.
- No plate/geographic attribution by index analogy and no solver authorization or scientific qualification.

---

## Historical D1A handoff and evidence publication (preserved)
D1A produced DOF_MAPPING_PARTIAL at checkout HEAD f7b66b2276ef9c33af7012f453b0f01902575cd6. Result: outputs/r6_si1_bandwidth_f2b_d1a_attestation/D1A_RESULT.json; manifest SHA256 5002d7bdb1c24d7d3c945b4edc1970b45c86b6daffb55268b67201616ea6653a, result SHA256 74328b449f41fbf7b467582adb53715c518a09327807401a1dbb4a789aff07a9. Final review added protected output-root checks and independent original FEG/runtime hash plus Git-blob validation; revised attestor reproduced the same result and manifest hashes. It attests node permutation, FEG/runtime reordering, staged F2A-V pair and raw DOF-to-node/component-slot mapping; it does not establish geographic basis semantics.

D1A evidence Git LFS publication is recorded by commit c6bc94c0cac134146722b0c751f55255c68f03dc; archive SHA256 b9fc3a7053e5c18a3d38e67ae367f418e5041f018d3ac9eafe82fa3dce1e9f9d; manifest SHA256 5002d7bdb1c24d7d3c945b4edc1970b45c86b6daffb55268b67201616ea6653a. The publication ledger update is preserved in remote commit bb529b32c4571241c90160423f277248bb9a35a7.

Original F2A-V historical decision remains BLOCKED_F2AV_QUALIFICATION; F2B_SOLVER_EXECUTION_AUTHORIZED=false. D1A geographic component meaning had remained DOF_MAPPING_UNVERIFIED until the bounded D1B source audit above; geographical attribution of the ten anomalies remains unverified.

## Historical design checkpoint
F2B-D1 design defined offline, read-only verification of the raw matrix DOF -> reordered node/component -> original node chain. D1A attests that nodal/index portion; D1B separately resolves ShellSet source component semantics. F2B-D2 operator semantics and F2B-D3 resource/residual design remain distinct.

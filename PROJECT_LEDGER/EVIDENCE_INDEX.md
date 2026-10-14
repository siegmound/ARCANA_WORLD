## INT-1B — evidence density and distinct-regime design (2026-10-13)

## INT-2C-C3 — imported executable replay verified (2026-10-14)

Report `docs/arcana/INT2C_C3_EXECUTABLE_R4_REPLAY_CLOSURE.md`, SHA256 `462dff6628bed482b23b9e8be815239ba53008b5ef11853f59a073e4f6538c6d`.
Source `9fb4fc0286cc09bcb6b8eef07bb92a19f4ca5963`. Local imported bundle:
`outputs/r6_functional_development/INT2C_C3_REPLAY_20261014_01/`.
WINDOWS_REHASH_VERIFIED: manifest `da913ccef5850ae943afadfd90672853db9d1b625eed2ebcc2d508fc599a2852`;
result `d55e9302ff85c9007679c916124aa1c163304aa88e84b86da62291675901fd4e`;
computed-state file `def81afa18361d7961e9bd777cc03c6ec536be9d587c952f007f69efe2ec2108`;
supervision `2c709d8a3d1a3872e63bbb176006c1912a9d64fb7c5ee05bb1e2a39585f22682`.
All 21 members + manifest verified, 22 files / 143,807 bytes. Full state ID and
both historical per-support payload digests match unchanged R4. Eleven typed
records and 16 copied-store files / 78,945 bytes reconcile; no original mutation.
OPERATOR_REPORTED parent log SHA256
`4f8b0f778e2c476d1335dd033cc3bc47af8b8e6ca0200e9faea9b3f067ed6c30`;
Linux supervisor 28 PASS / 1 expected SKIP (parent/test logs not imported).
Local offline 52 PASS / 6 Linux SKIP. No outputs staged or new replay executed.
Decision `INT2C_B0_EXECUTABLE_R4_REPLAY_VERIFIED__SCIENTIFIC_AUTHORITY_UNCHANGED`;
engineering R4 only, no broader physical/canonical qualification. STOP.

## INT-2C-C3 — launcher source and offline tests (2026-10-14)

Report `docs/arcana/INT2C_C3_SUPERVISED_REPLAY_LAUNCHER_PREFLIGHT.md`, SHA256 `ec49f8e894692c79467f44f32bdd73d109ed9af705ca7cfd93c106ecbcb4c2a6`.
Launcher `scripts/r6_int2c_replay_launcher.py` byte SHA256
`bbc05c19795a2c2bb4630c6c429491b06b317d77ec2dd294a1301ab367c33e06`.
Tests `tests/test_r6_int2c_replay_launcher.py` byte SHA256
`cbe13bdc0655e1d938591ff0fee2655b4a889fd3fda6bb56bb8b7ed4983e7e69`.
86 local offline PASS, 6 Linux supervision SKIP/NOT_TESTED_WINDOWS, 1 real Windows
store-publication test deselected. No new numerical trajectory or Fair execution.
C2 store path and isolated runtime prefix are supplied by the operator; historical
C1/C2 result/log hashes remain OPERATOR_REPORTED. No outputs staged. Original
R4/technical records, source and historical reports remain unchanged. Current
decision is launcher CODE_READY only; Linux self-test/preflight and authorized
real numerical execution remain separate prerequisites.

## INT-2C-C1/C2 — operator-reported Fair evidence (2026-10-14)

Report `docs/arcana/INT2C_C1_C2_FAIR_EVIDENCE_RECONCILIATION.md`, SHA256 `df21e291f3b4779fbee90235db0566f34a206261fb92ea67a88e30d64d97a75d`. Evidence identifiers
`INT2C_RUNTIME_CHECK_BXFon4Yd`, `INT2C_C1_zC7ONJo8`, `INT2C_C2_ljWdyPsq`.
C2 result SHA256 `ae1e99c652a064fb60d691590c76c4150981b11ce42e1bc6d9381a9719c28932`;
C2 log SHA256 `3392ebf60061734e5a86f7061281ba6f3c2befa545af7b18688eeeb93451064a`.
Both are OPERATOR_REPORTED; no imported C1/C2 files or independent Windows rehash.
C1 reports exact runtime/technical closure; C2 reports 11 atomic registrations,
reopened/readback/input-validation PASS, 16 files / 78,945 bytes and no kernel run.
Local technical manifest `8b172002968c9fcd7620d78b456054ac7ca0e7a9afa49f2f9e91ca81e9b1731d`
and its three members were independently verified, separately from Fair claims.
Full Fair paths/source commit/runtime binary hashes remain UNKNOWN. C3 is pending
final authorization and preflight. No historical outputs were changed or staged.

## Historical INT-2C-B — technical input closure; Fair runtime blocked (2026-10-14)

Implementation byte SHA256: `scripts/r6_int2c_checkpoint_attest.py` =
`9f8388fbcbc32c0099a64f232493eb83926ecfd987f6e11c971e64b8d2b2b65f`;
`tests/test_r6_int2c_checkpoint_attest.py` =
`b4ada2dca311f360022490e6ba8b7cee41621e18df98d920e81514af75f9a5cc`.

Decision: `INT2CB_BLOCKED_FAIR_RUNTIME_IDENTITY_MISMATCH`. Entry source
`f49de047ff560f707428b395b7373d46301fdee9`. Report `docs/arcana/INT2C_B_TECHNICAL_CHECKPOINT_RUNTIME_PREFLIGHT.md`,
SHA256 `35defa80a702d3adea30e3c307c8eb2666bb8b4c8b8023dc1c05780b75db025c`. R4's nine files and original identities were reauthenticated
and retained unchanged. New checkpoint/recipe are VALIDATED only in
`TECHNICAL_ENGINEERING_INPUT_CLOSURE_ONLY`; no numerical validation or physical
promotion. Existing adapter/kernel/B0 contract unchanged.

Direct read-only SSH observation on Fair: Miniforge base Python 3.14.7 without
NumPy; existing `arcana-r6-linux` Python 3.12.14 / NumPy 2.5.3. Required Python
3.12.10 / NumPy 2.3.5 was not found in the inspected existing environment roots.
No installation, environment recreation, job or numerical replay occurred.
Do not infer global absence of another runtime or historical binary identity.

Final local attestation: `outputs/r6_functional_development/INT2CB_TECHNICAL_ATTESTATION_20261014_02/`,
three-member manifest SHA256 `8b172002968c9fcd7620d78b456054ac7ca0e7a9afa49f2f9e91ca81e9b1731d`.
The `_01` provisional preparation remains preserved. No outputs are committed.
63 offline tests PASS, 0 FAIL, 0 SKIP, 1 actual Windows store-publication test
deselected. Typed `validate_replay_inputs()` passed through a test reader only;
real transactional publication/reopened-store readback and numerical replay
remain unexecuted. Exact runtime check rejects both alternate Fair versions.

Next decision: either separately authorize exact-runtime provisioning, or
review an explicitly new binding for Fair 3.12.14 / 2.5.3 with its own source,
configuration, checkpoint/recipe identities and future numerical equivalence
against the unchanged R4 full-state and per-support payload oracles. No relaxed
runtime check, store-contract weakening, new scenario or execution authorization.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`,
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

- Report: `docs/arcana/INT1B_EVIDENCE_DENSITY_AND_DISTINCT_REGIME_DESIGN.md`; decision `INT1B_NEXT_EVIDENCE_EXPERIMENT_DEFINED__EXECUTION_NOT_AUTHORIZED`. The R4 bundle was rechecked locally using `scripts/r6_int1a_retention_audit.py`: manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`; sample JSON SHA256 `ca9c5a4bc6ff4441b198219183e4e564a391d239dfda6e2f87598b7bd14bebad`; provenance validation PASS. INT-1A regression: 12 passed.
- Existing edge evidence: R4 `EDGE_AUDIT_MATRIX.json`, member SHA256 `d89bd4d9cca8928f8e6b913ad6bf1955c429ac2e2e1bb4dc6b6263f7165a59c7`. Proposed boundary `R6BND-T0-27e4d497530e681071fb` is eligible, admitted normal-continent support on both sides and nonjunction; support IDs `R6G1D-R094-C026` / `R6G1D-R094-C025`. Artifact provides geometric/thermal class and edge kinematics but not full candidate materialized profiles.
- No new execution or output. Future run requires separate authorization, exact validated boundary selection, full profile/material re-materialization, provider preflight, new absent destinations and active monitoring. `RESOURCE_2GB_SCOPE_UNRESOLVED` and all scientific/Solver gates remain open/blocked.

## INT-0B-R4 — provider audit finale read-only
- Commit sorgente: `50fbf6dfe1b8068a243ffa60df9ef22e1f5d6876`; provider audit `audit_pair_5_11` exit 0, Python 3.12.10 / NumPy 2.3.5, con `GIT_OBJECT_DIRECTORY` e `GIT_ALTERNATE_OBJECT_DIRECTORIES` assenti e `ARCANA_EXTERNAL_ROOT` risolto al payload governato.
- Source-composite SHA256: `c20e45ec398e331ae423e63d9387a53d8659a47a5a2bd8efa3b9ea1d17b808d4`. Pair 5:11; boundary `R6BND-T0-3eb57747e6f0a3f3305f`; supporti `R6G1D-R091-C029` e `R6G1D-R091-C028`; 73 profili nodali per supporto.
- Provider identities: physical geography `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`; vector partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`; field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`; support index `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00`; kinematics artifact/semantic `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2` / `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`; event census `e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e`; mapping join `b8d57495bc6e196a0b9fe7afd466079bebd97d0f63baafe232f215e45897a09f`.
- Esito read-only, nessuna evoluzione e nessuna mutazione canonica. Il JSON è stato emesso a console e non è conservato come artefatto sigillato; ripetere l'audit immediatamente prima di qualunque esecuzione separatamente autorizzata. Report: `docs/arcana/INT0B_R4_OFFLINE_E2E_VALIDATION.md`.

## INT-0A — codice di orchestrazione multi-provider, run non eseguito (2026-10-12)
- Decisione: `INT0A_INTEGRATION_CODE_READY__NONCANONICAL_RUN_NOT_YET_EVIDENCED`. Report `docs/arcana/INT0A_MULTI_PROVIDER_INTEGRATION.md`. `src/arcana_worldsim/r6/int0a_pipeline.py` lega l'audit T-F2B esistente a due profili T0 e al kernel ridotto esistente; test sintetici dimostrano data flow forcing/profilo → output. Il runner serializza record B0 typed ma non li registra in `HistoryStore`.
- Verifica offline: suite mirata 20 PASS, 0 FAIL, 0 SKIP; non include l'audit reale dipendente da payload esterno. Nessuna esecuzione INT-0B, nessun nuovo output, nessun input esterno acquisito e nessuna modifica WORLD_HISTORY.
- Gap: `R6_INITIAL_PHYSICAL_GEOGRAPHY.npz` richiesto dai provider non è presente nel checkout locale; T0 scenario/materiali e forcing congelato non costituiscono evoluzione geologica qualificata; eventi, validità temporale, fisica sezione/Xe e replay B0 chiuso restano UNKNOWN/non qualificati. INT-0B richiede autorizzazione distinta.

## 2026-10-12 — riallineamento INT-0; nessuna nuova evidenza

- `R6_INT0_REPRIORITIZED__INTEGRATED_RUN_NOT_YET_EVIDENCED`: cambio della priorità operativa, non un nuovo run o una prova numerica/scientifica.
- Per INT-0 consultare il codice T-F2B e i report B6K/B6N8-A/B6N8-Q nel rispettivo scope. I vecchi HEAD e NEXT nei record seguenti sono storici; conservare hash e verdetti immutati. La NEXT attiva è solo `NEXT_ACTION.md`.

## F2B-N2C-W3-C-C — review evidence (2026-10-11)
- Report: `docs/arcana/SI1_BW1_F2B_N2C_W3C_ADVERSARIAL_PROTOCOL_REVIEW.md`; decision `W3C_C_REVIEW_REQUIRES_TARGETED_CORRECTIONS`.
- Local verification only: W3-C focused suite 21 passed; W3-C + W3-B 43 passed. Two direct probes reproduced an accepted later Pure-call coordinate and Boolean worker rank; source inspection showed the Solver boundary is unconditional and does not read the latch. These are review probes, not production evidence.
- No new evidence bundle, no Fair/MPI/ShellSet/Solver execution. Remote HEAD was not verifiable because GitHub DNS failed. Existing untracked evidence/output directories were preserved.

## F2B-N2C-W3-C-A — static owner and coordinated-stop design (2026-10-11)
- Report: `docs/arcana/SI1_BW1_F2B_N2C_W3C_RUNTIME_AUTHORITY_AND_MPI_STOP_DESIGN.md`; decision `W3C_A_DESIGN_COMPLETE__RUNTIME_AUTHORITY_AND_MPI_STOP_UNPROVEN`. Design-only; no new run artifacts or evidence manifest.
- Source references: locked ShellSet `ShellSetMain.f90:88-98,244-260,427-433,553-575,690-700,783-794,853-860`; `SHELLS_v5.0.f90:735-759`; `MOD_Shells.f90:3707-3734,6940,6996-7010,8626-8673`; candidate W2 overlay/bridge. Report separates observed local values from owner authority.
- Recommended protocol: freeze one owner-issued CAPTURE_ONLY decision before dispatch, distribute/ACK identical digest across coordinator and all ranks, dispatch one first-reachable FEM target, latch no-Solver on every worker/call, collect typed terminal status from every rank, then coordinator stop; fail-stop and launcher semantics remain unverified. W3-B coordination tests are synthetic only.
- Unresolved: no R6 SI1 run/assignment trust provider; stable model binding; effective runtime state/constraints; executable-to-process identity; actual runtime DOF order; independent A0/b0 binding; real MPI-wide stop. W2 compile-only is not linked/runtime evidence. Gates unchanged; next proposed W3-C-B offline state-machine model only.

## F2B-N2C-W3-A — documento di contratto recuperato, no nuova evidenza runtime (2026-10-11)
- Documento `docs/arcana/SI1_BW1_F2B_N2C_W3A_IDENTITY_PROVENANCE_CONTRACT.md`, SHA256 `6f94d4cbcda52eab351e1aa106bcd7d2c1c25f00b78834d2b2b7f3f8d41e2df9`; Git blob `c3fdf5dbc92454e406b7bde84765e0cab76d90de`. Ricostruito dalla patch di recupero `f6d0ff2f17547d530ae8a37145c94e788732ef2e` con parent `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`, confrontato al blob Git e integrato sul ramo aggiornato senza perdere le registrazioni W2/E1.
- Scope `WINDOWS_WORKTREE_ONLY` per l'audit originario, oggi `GITHUB_BRANCH` per il contratto documentale. Esito `W3A_IDENTITY_CONTRACT_DEFINED__RUNTIME_BINDING_AND_MPI_WIDE_STOP_UNPROVEN`. Non sono stati eseguiti nuovi test, compilazioni o prove MPI/Fair; no SI1 A0/b0, no build/run attestati, no independent snapshot SHA. Source lock (identità dichiarata nell'audit) `8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2` resta invariato.
- Gap: assignment/model/run identity, input/state/build/DOF, digest e stop MPI-wide; W3-B solo offline sintetico. Il precedente E1 su Fair resta una prova distinta di integrità locale riferita dall'operatore, NON rehash Windows.

## F2B-N2C-W2-E1 — verifica locale Fair di hash e membership (2026-10-11)
- **Provenance:** `FAIR_EXTERNAL_EVIDENCE` sotto `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2C_W2_COMPILE_ONLY/W2_NV_20261011T132801Z_juuO3l`, commit W2 `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`. Tutti i risultati e i digest qui sono **operator-reported** su Fair; non sono stati trasferiti/rehashati indipendentemente in Windows né estratti dalla chat come bytes.
- **Checksum audit:** `sha256sum -c --status SHA256SUMS.txt` → `CHECKSUM_EXIT=0`; `MANIFEST_ENTRIES=103`; `ACTUAL_FILES=103` escluso `SHA256SUMS.txt`. La verifica mostra concordanza con il manifest presente sullo stesso host, non autenticazione esterna del manifest.
- **Digest SHA256 riportati dall'operatore:**
- `RESULT.txt`: `673b0b19fcb81495b95eb7a8a2570093d9cf5144ee581e9462d041d75b9ab8f7`
- `SHA256SUMS.txt`: `9953c830fcf353bee97340596254f775af8e4882a42c57da7ef97ee74f2f1ee9`
- `candidate/N2C_W2_CANDIDATE_OVERLAY.json`: `52c86d094122edd2db007a16f6e82efb12066e7cdabb3d52eaf7d447414fb318`
- `bridge.log`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (log di compilazione vuoto, non indicatore di errore)
- `full_compile.log`: `18c728e3448d137c01bc5b1c2ae4f4514da45a16012ffb8fe9faef4c78cff078`
- **Script di audit read-only (console operatore):** `E1_SOURCE_AND_OBJECT_INTEGRITY_PASS`. Checks PASS per source commit, bridge/full compile exit 0, no linking/runtime **reported**, JSON builder == candidate manifest, SHA lock pinned `8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2` e lock bytes on Fair, 15 membri source-locked, candidate hashes, writer/bridge/MOD_Shells/SHELLS_v5.0/ShellSetMain, 14 oggetti full exact membership, 2 oggetti bridge. Object files non sono stati collegati né eseguiti.
- **Interpretazione:** `N2C_W2_E1_FAIR_OPERATOR_REPORTED_INTEGRITY_PASS__RUNTIME_NOT_QUALIFIED`; confermata coerenza locale delle evidenze riferite, non provenance indipendente del sorgente scientifico, linking, MPI runtime, ShellSet runtime, A0/b0, Solver o produzione WORLD_HISTORY.
- **Next:** W3 design identity/provenance; preservare `RESOURCE_2GB_SCOPE_UNRESOLVED`, `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-N2C-W2 — NVFORTRAN compile-only on Fair (operator-reported; 2026-10-11)
- **Provenance tag:** `FAIR_EXTERNAL_EVIDENCE`; checkout commit `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`; reported run path `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2C_W2_COMPILE_ONLY/W2_NV_20261011T132801Z_juuO3l`. Non verificati da questa chat né scaricati sul PC Windows: membri, SHA256, log e bytes non attestati indipendentemente.
- **Toolchain confermata da output del terminale:** `mpifort` a `/opt/nvidia/hpc_sdk/Linux_x86_64/25.11/comm_libs/mpi/bin/mpifort`, `mpifort --showme:command` = `nvfortran`, compiler 25.11-0, `mpiexec --version` = OpenRTE 4.1.9a1; l'esistenza del wrapper non è prova di esecuzione MPI.
- **Transcript `RESULT.txt` riportato:** `HEAD=fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`, `BRIDGE_COMPILE_EXIT=0`, `FULL_COMPILE_EXIT=0`, `FULL_OBJECT_COUNT=14`, `EXPECTED_FULL_OBJECTS=14`, `LINK_PERFORMED=false`, `SHELLSET_MPI_SOLVER_RUNTIME_EXECUTED=false`; marker `PASS_N2C_W2_NVFORTRAN_COMPILE_ONLY_CANDIDATE`. Flags di compilazione: `-O0 -Kieee -Mnodaz -Mnoflushz -Mbounds -Mbackslash`.
- **File attesi dal comando nel locator:** `PREFLIGHT.txt`, `builder.log`, `bridge.log`, `full_compile.log`, `RESULT.txt`, `SHA256SUMS.txt`, `candidate/N2C_W2_CANDIDATE_OVERLAY.json`, directory `build-bridge` e `build-full`; i SHA specifici non sono stati forniti. `SHA256SUMS.txt` è un indice prodotto dal comando ma ancora da leggere/verificare.
- **Interpretazione:** `N2C_W2_NVFORTRAN_COMPILE_ONLY_OPERATOR_REPORTED_PASS__RUNTIME_NOT_QUALIFIED`. Niente linker/ShellSet/MPI runtime/Solver/DGBSV, nessun A0/b0 reale; test di 14 unità di compilazione del candidato, non prova di linking né di integrazione dinamica. Precedente W2 non compilato rimane record storico corretto per quel checkpoint.
- **Next evidence gate:** E1 read-only verifica selettiva di manifest/hash/log esistenti. Tutti i blocchi SI1/scientifici inalterati.

## F2B-N2C-W2 — overlay e trasferimento Fair (NON build) — 2026-10-11
- Branch `r6/si1-bandwidth-f2av`; commit W2 `fcb94f5c3b821273bc82b4f11e6a444ffb28d16e`, parent `8645a48f7ca716c2e3c4b3cee087e7e6f7333262`; push GitHub verificato. Fair checkout detached allo stesso commit riportato dall'operatore. Il transcript della console Fair non costituisce un build log con SHA in questo gate.
- Windows W2 review: 13 passed, 1 skipped, nessun compilatore Fortran; py_compile/UTF-8/LF/whitespace/diff-check PASS. SHA256 riferiti: builder `3c29bca5e28dc2d997d3edbcf06433e1469afd933acbde7596aacebc42972872`, bridge `6cb4879400ac425e334d19e771ecf10f68ed45418a1ce2712f42fe31cd3d6a85`, test `e851b05da6b3fb4040315ddc0dfdd56722f40321e52aa43d13d386a2c930717d`, report `89a6fe264f2e37cea7f69f4329b98661d441ccaa08cad7b9552c8bc4cacaa4ff`.
- Fair preflight riferito: checkout `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV`, Conda `arcana-r6-linux`, Python 3.12.14, GNU Fortran 13.3.0, NVFORTRAN 25.11-0; builder `--source-package` opzionale, `--output` obbligatorio. Nessuna copia candidata generata, nessun manifest/compilazione/test runtime W2.
- Identità sorgente: source lock SHA256 pinned `8c3174c08cb021ae90257e04880f7e96b9ecd9d4d830034bfc0ea6462ef867f2`, 15 source membri, parametro `c07834e17d9c6e21bad0d7cd81af20e8a670e0ae9ed481f999c881129ee4a89e`. Il vendored commit `9fef54f6cd17e6e756db3ec28bfc43ee0230fc27` è claim dal lock, NON oggetto Git verificato in questo gate.
- Storici N2B/W1 e relativi log Fair restano separati; W2 checkout/compilers-on-PATH non è compile PASS, capture PASS né autorità Solver.

## F2B-N2B-V — test cross-language sintetici su Fair (2026-10-11)
- GNU Fortran 13.3.0; commit testato `9ebc78bbccc6ae5cb64eac15b67fd88f4c9ea406`; Fair Conda `arcana-r6-linux`, Python 3.12.14, pytest 9.1.1; 21 passed, 0 failed/skipped, exit 0. Log locator `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2B_GFORTRAN/N2B_GFORTRAN_TEST_20261010T233835Z.log`; SHA256 `b7a953072d9b142a8836190454cccbebb5399f3fc8b71b50057c6998a94cf0ef` riferito dall'operatore, non ricalcolato da Codex Windows.
- NVFORTRAN 25.11-0; commit testato `2d6021ff0036d350b12a583d9eff1d03e32a7239`; flag `-O0 -Kieee -Mnodaz -Mnoflushz -Mbounds`; 29 passed, 0 failed/skipped, exit 0. Log locator `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2B_NVFORTRAN_RUNTIME/N2B_NVFORTRAN_TEST_20261010T235701Z.log`; SHA256 `b219f790e1c45369a55c12cf60a635d71068a05bda774e5a1577116cb02c945b` riferito dall'operatore, non ricalcolato da Codex Windows.
- La precedente `N2B_NVFORTRAN_FIXTURE_COMPILE_PASS` e il relativo executable digest restano evidenza storica separata, sostituita per lo scope runtime dall'esito successivo; non confondere compile e runtime.
- Questi sono risultati Fair riferiti, non acquisizione indipendente dei log; sono limitati a fixture sintetiche e non qualificano cattura SI1 o solver.

## F2B-N2B — evidenza preliminare prima della prova NVFORTRAN runtime (storica; preservata)
- GNU fixture cross-language: commit testato `9ebc78bbccc6ae5cb64eac15b67fd88f4c9ea406`; Fair Conda `arcana-r6-linux`, Python 3.12.14, pytest 9.1.1, GNU Fortran 13.3.0; 21 passed, 0 failed, 0 skipped, exit 0. Log locator `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2B_GFORTRAN/N2B_GFORTRAN_TEST_20261010T233835Z.log`; SHA256 riportato dall'operatore `b7a953072d9b142a8836190454cccbebb5399f3fc8b71b50057c6998a94cf0ef`. Il file non è stato ricalcolato in Windows in questo consolidamento.
- NVFORTRAN: solo `N2B_NVFORTRAN_FIXTURE_COMPILE_PASS`, NVFORTRAN 25.11-0, flag `-O0 -Kieee -Mnodaz -Mnoflushz -Mbounds`, exit 0. Eseguibile Fair riportato e SHA256 dichiarato `72aadbf9eb9c953816c8816bbe1050f1afdcc08302a3d1bb9313c3e022759719`; nessun test runtime Python↔NVFORTRAN attestato.
- Entrambi i risultati sono limitati a fixture sintetiche e a quanto riferito dall'operatore; non qualificano SI1 e non modificano i gate. Nessun nuovo artefatto Fair è stato acquisito/rehashato da Windows.

# Indice minimo delle evidenze (identità e scope)

## INT-1C — distinct-regime candidate preparation (2026-10-13)
- Report: `docs/arcana/INT1C_DISTINCT_REGIME_EXECUTION_PREPARATION.md`; decision `INT1C_DISTINCT_REGIME_CODE_READY__EXECUTION_PENDING_AUTHORIZATION`.
- Preparation baseline HEAD `8585d4fdd29ba5f1019421bf8310ef06883fb78b`. Existing R4 manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`; edge-matrix SHA256 `d89bd4d9cca8928f8e6b913ad6bf1955c429ac2e2e1bb4dc6b6263f7165a59c7`. Candidate boundary `R6BND-T0-27e4d497530e681071fb`; supports `R6G1D-R094-C026` and `R6G1D-R094-C025`. Local T0 rematerialization: 73 nodes/support, 35 km crust, 135 km model base, q=0.06 W/m², identical admitted material tuple references; explicit thermal bound `952777777777.7762 s`.
- Full provider audit and candidate-HEAD source-composite identity are pending because `ARCANA_EXTERNAL_ROOT` was unset. No evolution or new candidate output. Focused offline suite 87 passed; two provider-backed tests deselected. Proposed output and supervisor destinations were checked absent.
- Runner preserves the old three-factor default; the explicit preparation adds 0.000125 and binds diagnostics to it while retaining 0.0005 as R4 reference/checkpoint/replay and 0.00025 for the common-rung edge comparison. Sample count and execution costs remain estimates.

## INT-0B-R4 — synthetic E2E and supervisor diagnostics; no evolution (2026-10-13)
- Report: `docs/arcana/INT0B_R4_OFFLINE_E2E_VALIDATION.md`; decision `INT0B_R4_OFFLINE_E2E_VERIFIED__FOURTH_RUN_PENDING_AUTHORIZATION`.
- Scope: offline Windows tests only. A synthetic fixture traverses the production numerical observer, R3 sequence validator, sample document serializer, replay/restart, trajectory builder and runner output-bundle writer. Readback, manifest-last order, exact membership/length/SHA256 and overwrite refusal are tested. Supervisor tests verify PID tree and existing limit/exit-race behavior plus raw stdout/stderr logs, their SHA256 and output-limit accounting.
- Final focused suite: 70 passed, 0 failed, 0 skipped; Python 3.12.10/NumPy 2.3.5. No provider-backed audit, numerical evolution, or new run artifact was created. Output and supervision destinations `_04` were checked absent and remain uncreated.
- Sample-size calculation: 12 intermediate fields, 22 endpoint fields; 10,001 records/support × 2; type-aware numeric-entry total 4,521,036. Production-serializer stress projection approximately 179,442,031 bytes for the sample artifact; older more conservative planning estimate 333,657,599 bytes. Both are estimates, not observed output/RSS. The 512 MiB limit is an actively sampled stop threshold.
- The bounded synthetic fixture's diagnostics JSON serialized to 5,474 bytes (two supports, two samples/support, three nodes/support); this is a fixture measurement only.
- Not provider/runtime evidence and not a trajectory. Final-source provider audit and a separate execution authorization remain outstanding. Prior three failure reports/evidence remain unchanged. All scientific, solver, canonical and INT-1 gates remain blocked.

## INT-0B-R3 — endpoint schema e supervisor classification (2026-10-13)
- Report: `docs/arcana/INT0B_R3_ENDPOINT_VALIDATION_FORENSIC.md`, SHA256 `50a1ee00fe9d10b2d12e6d5e9aa8f029c7cdbb0754f6dae867455d36d6e7d437`; decisione `INT0B_R3_ENDPOINT_VALIDATION_CORRECTED__REEXECUTION_NOT_AUTHORIZED`. L'analisi del sorgente storico del run individua `elapsed_years` come primo campo assente nel payload finale, mentre l'observer lo derivava da `time_s`; nessun sample byte-level del tentativo precedente era stato persistito, quindi i suoi valori numerici effettivi restano non disponibili.
- Modificati runner `scripts/r6_functional_development_t_f2b.py`, observer `src/arcana_worldsim/r6/int0a_pipeline.py`, test endpoint `tests/test_r6_functional_development_t_f2b_samples.py`, supervisor `scripts/r6_int0b_supervisor.ps1` e test supervisor `tests/test_r6_int0b_supervisor_environment.py`. L'endpoint ora confronta il payload completo e le trasformazioni derivate; l'osservazione ha support ID e schema V2. Il supervisor ricontrolla `HasExited`, distingue classificazioni di terminazione e non usa più la label R1.
- Test offline Python: 62 passed, 0 failed, 0 skipped; comprende self-test supervisore con subprocess sintetici (exit naturale nonzero dopo snapshot senza root e root omesso mentre ancora vivo). Non sono state eseguite evoluzioni provider-backed. I risultati sintetici non validano il precedente run.
- Il report R2 originale SHA256 `e6c029d6778aa218f163d6411e433010d730b84f7d89776a84622fc350f406dc` e le evidenze supervisor precedenti sono preservati. Nessun nuovo output numerico creato. Nessun quarto run autorizzato; INT-1 bloccato.
- SHA256 aggiornati: runner `def870816d33a1de524641906285c668a693b875d994bbd72803e73da61106e1`; pipeline `19b05d2459dd14b2d0333a240879e976305fe6d77017883e5e847ede53a2a530`; supervisor `25b006fd178769d4629c4b5037493b8f9ab83b98f54e9b0e78a5756125194a07`; endpoint tests `4159a450564a5c77b41573d62fb990d90bd70659d8ddb5860768f0a7b1a3448a`; supervisor tests `9915d2a9c60046f09368c30a4301f9b2fca3e1f74f161267c7b208b8ee345a8d`.

## INT-0B-R2 third/final attempt — endpoint validation failure (2026-10-13)
- Report: `docs/arcana/INT0B_R2_THIRD_ATTEMPT_FAILURE.md`, SHA256 `e6c029d6778aa218f163d6411e433010d730b84f7d89776a84622fc350f406dc`. Source branch `r6/si1-bandwidth-f2av`, HEAD `311550d4402f6c2fac422eac1c7f1eed46c58c64`, parent `d9d87fe8853b5c17f5bc8fd27d496aaf9aa45b57`. Decision `INT0B_R2_THIRD_ATTEMPT_FAILED_DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH`; no retry/fourth run authorized.
- Final provider audit local artifact `outputs/r6_functional_development/INT0B_R2_SUPERVISION_20261013_FINAL_311550_PROVIDER/provider-audit/provider-audit-result.json`, SHA256 `8c9fc82a8ee4457a34a57efaa0bb53109047413562b237db733ddb9e3fbca58c`; source identity `a19070287adedb0bb009ce5c56380892ca173d4eee30b662c6c1a7d34406b34a`. Input/provider IDs: field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`; index `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00`; vector partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`; event census `e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e`; kinematics artifact `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2`; kinematics semantic identity `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`. Pair 5:11; selected boundary `R6BND-T0-3eb57747e6f0a3f3305f`; supports `R6G1D-R091-C029`, `R6G1D-R091-C028`; each profile has 73 nodes.
- Supervisor evidence `outputs/r6_functional_development/INT0B_R2_SUPERVISION_20261013_RUN/`: `run-summary.json` 1,122 bytes SHA256 `b699666d0c5e33db350b02404b544065f57fda290f49d0721011be02f475a271`; `run.ndjson` 69,221 bytes SHA256 `7c2812bbda0daa38d8c228555737c662fb07e385a185984d87391bb01d3ea993`. Recorded PID 33688, exit 1, 22.190863 s, peak sampled process-tree working set 151,773,184 bytes, output 0 bytes, 194 100-ms polls. Summary stop reason/label are inaccurate (`MONITOR_ROOT_IDENTITY_LOST`/stale R1); foreground runner error is endpoint mismatch. Summary and monitor log do not contain a byte-preserved runner stderr transcript.
- `_03` candidate output directory was absent before and remains absent. No samples, final-state artifact, replay/restart or run manifest were produced. These are local observed artifacts; numerical/scientific qualification and INT-1 remain blocked.

## INT-0B-R1 second authorized attempt — pre-output failure (2026-10-13)
- Report: docs/arcana/INT0B_R1_SECOND_ATTEMPT_FAILURE.md; SHA256 `3476333ef583cc41a0cbf2dd129ad63af0e600f5aa59de8ad72e9da0420f1cca`. Outcome: INT0B_R1_SECOND_ATTEMPT_FAILED_PRE_OUTPUT_VALIDATION_GIT_OBJECT_ENV_REINSERTED. Source branch/HEAD/parent: r6/si1-bandwidth-f2av / 4cc7a78d95ee7e529394173933817a7266db251d / e95c7dbf281ede5312512654262b9925fa87eb02.
- Final runner/test SHA256: 2b5ab1af081fae9ad2a0681a4ba9b95dfca032839caba52cdc440525cf77fc1c / 87b3f5dae80cd27d356e28b75c94bdc4d31e83f29691b18aa26b7d6b0ee0f843. Provider audit passed directly on HEAD; HEAD-bound source identity c30510e3b743954fd10385f02a6c282448843247db69e1da26de5ae22ac7a25d. Python 3.12.10 / NumPy 2.3.5.
- Run summary/trace/supervisor SHA256: 6ba6718d0050ad23fd5c642dc611a56997f729b14af85434b3589c7b02f9960a / a12e1cb3363d4122b5f53f4c3a59881e1ec8ce96e5fd54a225504fe6dd79e471 / 346ae1d5dadfa67bf6a6b113e50577633d02040a79cbf9f7dcee4664d00986a8. Failure JSON SHA256: dc9c61eb074620e2438ccb99dda43ff919bc20b327a0bcb6368b91a691998c56; it is stored alongside supervision evidence.
- Process 31248 python.exe, natural exit 1 after 0.951220 s, 7 samples/100 ms, peak process-tree working set 48,848,896 bytes, output 0. No numerical artifact; candidate _02 absent. The runner failed at source identity query because the supervisor re-sourced r6-env.ps1 and passed its GIT_OBJECT_DIRECTORY / GIT_ALTERNATE_OBJECT_DIRECTORIES values into the child. Reproduction: Git tree query exits 128 under bootstrap environment and succeeds after unsetting both.
- Provider audit and run failure are distinct: direct audit was run with Git object variables unset; the nested runner was not. The runner did not reach trajectory evolution, result validation, replay or manifest generation. No evidence of WORLD_HISTORY access/change. _01 was not accessed or changed.
- Supervisor self-test output and detailed polling traces: outputs/r6_functional_development/INT0B_R1_SUPERVISION_20261013/. Sampled limits are not OS hard quotas. There is no numerical trajectory and INT-1 cannot proceed.

## INT-0B — provider preflight, input verificati; run in attesa di autorizzazione (2026-10-13)
- Report `docs/arcana/INT0B_PROVIDER_PREFLIGHT.md`; esito `INT0B_PROVIDER_INPUTS_VERIFIED__EXECUTION_PENDING_AUTHORIZATION`. Fonte di codice controllata: branch `r6/si1-bandwidth-f2av`, HEAD `dde79ebe4d26ab7b21eff08245fc83330239c0bc`; root esterna `F:\\corsiiiuu\\Magistrale\\Arcana\\ArcanaWorld\\_ARCANA_EXTERNAL_SOURCES`.
- Rehash locale del payload initial geography: SHA256 `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`, 1,169,900 bytes. Rehash locale vector partition: `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`, 5,681,184 bytes. B6N8-N field package SHA `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`; binding index `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00`. Provider audit checked B4/B5 source/manifest lineage, 63,620 admitted support and 14,258 continental; mapping identity `b8d57495bc6e196a0b9fe7afd466079bebd97d0f63baafe232f215e45897a09f`; source-set identity `2ffc49375f9e59c7f7abf9140ba7041c64ad0deb0a182df9242184a55ce76109`; kinematics semantic identity `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4` and artifact SHA `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2`; event census SHA `e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e`.
- Pair result is limited to an engineering provider audit: `R6BND-T0-3eb57747e6f0a3f3305f`, row 91/column 28 EAST, support IDs `R6G1D-R091-C029` and `R6G1D-R091-C028`, positive frozen instantaneous Euler extension `0.11467052868814648 m/year`; pair census `ELIGIBLE_QUIESCENT`, not activation authority. Each thermal profile has 73 nodes and admitted material-role binding.
- Sampling correction: middle resolution captures initial + every numerical substep, bounded at 10,001 records/support and 73 nodes; formula-based sample artifact size estimate 333,657,599 bytes (350,000,000-byte proposed ceiling). Focused suites 59 PASS, 0 FAIL/SKIP; py_compile and diff-check PASS. No candidate numerical run or new output evidence. Exact command and pending authorization/resource boundaries are in the report and NEXT_ACTION.
- Windows point-in-time memory availability was 7,662,350,336 bytes, with 12 logical processors; no process RSS was observed. Proposed 2 GiB working-set and 15-minute limits require operator monitoring and are not OS-enforced. No push was possible: GitHub DNS resolution failed; no push attempted.

## Aggiornamento F2B-N2A-R1 (2026-10-11)
- Report `docs/arcana/SI1_BW1_F2B_N2A_IMMUTABLE_SNAPSHOT_FEASIBILITY.md`, SHA256 `f9fb44697f2aea551f962ef35a2cbf0110abee8dee295a0575d6f9429d663520`; decisione `N2A_SPARSE_SNAPSHOT_SYNTHETIC_VERIFIED__SI1_INTEGRATION_NOT_QUALIFIED`.
- Prototipo `scripts/r6_si1_bandwidth_f2b_n2a_snapshot.py`, SHA256 `90c6707f48dcb1bec35097b25b9e0f317463d4a08d28d54c4611e3cebf463156`; test `tests/test_r6_si1_bandwidth_f2b_n2a_snapshot.py`, SHA256 `faf456601864b38da0c55d3496c84f62a3e2d14d280004156f66eeb9db9b9389`. Suite con D3B numerica: 15 passed. Evidenza interamente sintetica; nessuna matrice SI1, assembly o runtime Fortran.
- SHA snapshot esterno e identità dell'assembly sono distinti: il prototipo non attesta run/iterazione reale; digest interno non è autorità indipendente. Il punto sorgente candidato è dopo `VBCs` e prima di `Solver`/`DGBSV`.
- Nessuna evidenza `outputs/` nuova. Integrità file/prototipo non promuove `BLOCKED_F2AV_QUALIFICATION` né autorizza Solver.


## F2B-N1 / N1-T1 — 2026-10-11
- Report N1: `docs/arcana/SI1_BW1_F2B_N1_NUMERICAL_ACCEPTANCE_PRECONDITIONS.md`, SHA256 `88790af7a35f0cb58568d7d69afd27664b5a2b1fdeeff5a4ef807dfcca87f978`; un blank line finale ridondante è stato rimosso per superare `git diff --check`; il contenuto semantico non cambia. Definisce precondizioni e metriche, non attesta l'accettazione del solve SI1. `THRESHOLD_UNJUSTIFIED` resta.
- Test aggiornato `tests/test_r6_si1_bandwidth_f2b_d3b_numerical.py`, SHA256 `95c6bfe54f70f37f685dc1add355f9bb8d83b47e25500fba35ccdfe2eabdac3e`; 9 passed, 0 failed, 0 skipped. T1 è `N1_T1_SYNTHETIC_DESTRUCTIVE_BUFFER_ISOLATION_PASS` solo per matrice sintetica KL=1/KU=2, snapshot A0/b0 separati, overwrite dei buffer operativi e confronto con oracolo denso indipendente. Il validator di produzione non è stato modificato.
- Non è prova della preservazione A0/b0 in ShellSet, non determina la strategia SI1 e non qualifica operator, residuo accettabile, conditioning o fisica. Prossimo lavoro proposto F2B-N2: design della strategia di preservazione senza ipotesi di memoria HPC.

## F2B-D3D-RO6 Fair attestation trasferita — 2026-10-10
- Report `docs/arcana/SI1_BW1_F2B_D3D_RO6_FAIR_EVIDENCE_CONSOLIDATION.md`, SHA256 `1b9c46b43079fbc5002d3719bc935175cd6f1bea5489f6026abe7d870e1a4579`.
- `outputs/r6_si1_bandwidth_f2b_d3d_ro6_fair_attestation/D3D_FAIR_RO6_ATTESTATION.json`: 4,133 byte, SHA256 `320344b6cfb74042e450bac4347f5a8b820e5702fa4b15c3bf4ff240ec764ec0`; sidecar `.json.sha256` concorde. JSON parse PASS; schema identifier `ARCANA_D3D_FAIR_RO6_ATTESTATION_V1`; nessuna definizione schema separata individuata.
- Report di consolidamento `docs/arcana/SI1_BW1_F2B_D3D_RO6_FAIR_EVIDENCE_CONSOLIDATION.md`. Trasferiti solo attestazione e sidecar: nessun binario, log, manifest storico, output RO2–RO5 o accounting Fair allegato. Il JSON dichiara `full_manifest_membership_verified=false`.
- RO6 riferisce i due binary copies del run a SHA uguale (`7e913914…b221bc0cf`), distinto dal compile-only (`4ef42e11…74e6e91a4`); build/MPI log selezionati corrispondono ai digest dichiarati. I byte dei membri non sono stati autonomamente rehashati in questa review.
- Stato `D3D_FAIR_EVIDENCE_RECOVERED__RESOURCE_ATTESTATION_INCOMPLETE`. Codice storico 75 e toolchain version excerpt registrati. ELF LP64 BLAS/LAPACK/MPI è affermazione dell'handoff ma il JSON non riporta i nomi/hash delle librerie. Librerie storicamente caricate, ABI completa, enforcement, limiti aggregati e RSS/PSS/cgroup restano non attestati.
- Cinque membri selezionati sono riportati verificati contro il manifest originale (compile-only binary, due run binary copies, build log, MPI log); il manifest completo da 79 membri non è stato verificato (`full_manifest_membership_verified=false`). I membri raw e i record distinti RO2–RO5 non sono trasferiti nel worktree.
- Risorse: 32 GiB per-process e 80 GiB aggregate sono dichiarazioni; enforcement cgroup false/non provato. RSS/PSS non acquisiti. RO5 non ha trovato accounting nei soli percorsi circoscritti, senza inferenza di assenza globale.
- Il precedente D3D bloccato e il suo report restano immutati; questo RO6 non è verifica completa del manifest né qualifica scientifica. Proposta di pubblicazione immutabile su evidence branch separato solo dopo review; non includere `outputs/` nel commit codice. Gate invariati: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## F2B-D3A resource/numerical attestability audit — 2026-10-10
- Report: `docs/arcana/SI1_BW1_F2B_D3A_ATTESTABILITY_AUDIT.md`; SHA256 `CA2FF09491BBDCB995FC79FB9E4CF66B461C519A2FC67F652E09099C70884989`.
- Decision: `D3A_AUDIT_COMPLETE__SOLVER_PREFLIGHT_NOT_ATTESTABLE_FROM_CURRENT_EVIDENCE`; offline source/evidence review only. The named-array arithmetic is conditional on ABI assumptions and explicitly excludes unknown compiler/runtime/OS overhead; no RSS/cgroup/Fair enforcement measurement or numerical solve evidence was produced.
- D3 source report remains unchanged, SHA256 `1666D30701D8365CAF7CB8C5C7192C46E04AB19D2C6E9179EE2917DCB056E3FF`. D3A records the corrected A0/b0-copy estimate `5,183,806,076 bytes + 112 × (LRn+1)`; difference from D3's approximate `4.82684 GiB` is the copied RHS b0 accounting. No copy was allocated.
- Original `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, and all execution prohibitions remain. Proposed D3B-P0 is offline validators only; no new execution/evidence artifact.

## F2B-D3 — resource and residual preflight design (2026-10-10)
- Report: `docs/arcana/SI1_BW1_F2B_D3_RESOURCE_RESIDUAL_PREFLIGHT_DESIGN.md`; SHA256 `1666D30701D8365CAF7CB8C5C7192C46E04AB19D2C6E9179EE2917DCB056E3FF`.
- Scope: design/source audit of historical ShellSet `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`, SI1 engineering dimensions, and existing F2A-V diagnostics. Decision `D3_DESIGN_COMPLETE_PENDING_RESOURCE_AND_NUMERICAL_ATTESTATION`; no new run, assembly, Solver, memory measurement, or Fair resource measurement was made.
- Source-derived band allocation formula `8*nKRows*nRank` gives 2,249,799,104 bytes under the report's dimensions; broader process/job memory depends on ABI, LRn, runtime/library overhead and enforced system limits, not measured here. DGBSV overwrites AB and B; residual validation requires exact A0/b0 identity. No residual threshold is authorized (`THRESHOLD_UNJUSTIFIED`).
- Next proposed gate F2B-D3A is preliminary and non-executing; it grants no Solver authority. Original `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `DOF_MAPPING_PARTIAL`, and geographic/anomaly `DOF_MAPPING_UNVERIFIED` boundaries remain unchanged. `F2B_SOLVER_EXECUTION_AUTHORIZED=false`.

## F2B-D1A LFS evidence publication — 2026-10-10
- GitHub evidence branch `evidence/r6-bw1-f2av-20261010` commit `c6bc94c0cac134146722b0c751f55255c68f03dc`: `evidence/F2B_D1A_ATTESTATION_d539a9ff_20261010.tar.gz` Git LFS plus `.tar.gz.sha256`; archive SHA256 `b9fc3a7053e5c18a3d38e67ae367f418e5041f018d3ac9eafe82fa3dce1e9f9d` matches sidecar downloaded from GitHub and operator's archive digest.
- Payload carries `D1A_RESULT.json`, `D1A_REPORT.md`, `RAW_DOF_NODE_COMPONENT_MAP.csv`, `F2AV_CENSUS_INDEX_MAP.csv`, `D1A_ARTIFACT_MANIFEST.json` (per source/test contract and Windows verified packaging). Internal manifest SHA256 `5002d7bdb1c24d7d3c945b4edc1970b45c86b6daffb55268b67201616ea6653a`; result SHA256 `74328b449f41fbf7b467582adb53715c518a09327807401a1dbb4a789aff07a9`.
- Source code commit `d539a9ffa281d3dac8489db4820715cb136e9ae6`. D1A output identifies precommit checkout `f7b66b22...`; final revised code reproduces same hashes per Windows run. LFS archive not independently extracted by this GitHub metadata check.
- Decision is `DOF_MAPPING_PARTIAL` only; geographic component basis `DOF_MAPPING_UNVERIFIED`, original `BLOCKED_F2AV_QUALIFICATION`, BW1 `BLOCKED_BW1`, solver not authorized. Evidence transport PASS does not upgrade these.

Questa pagina NON è un manifest sostitutivo. Le identità precise dei payload sono nei manifest originali. Verificare disponibilità, hash e scope prima di dichiarare PASS.

## F2B-D1B — historical ShellSet geographic component-basis source audit (2026-10-10)
- Report: `docs/arcana/SI1_BW1_F2B_D1B_GEOGRAPHIC_BASIS_AUDIT.md`; SHA256 `baa9e450f866f29a42230ad01bd490de6ed6c96f02df3d901e6af77388a41546`.
- Audited exact historical F2A-V ShellSet source commit `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`; source-level finding: slot 1 = +South/+theta and slot 2 = +East/+phi. Static source audit only; no Solver/runtime qualification.
- Scope boundary: ARCANA frame authority, universal seam behavior and mapping the 10 asymmetry pairs to geography/plates/causes remain unverified. Preserve `DOF_MAPPING_UNVERIFIED` for those claims and original `BLOCKED_F2AV_QUALIFICATION`.

## F2B-D1A — offline DOF provenance attestation (2026-10-10)
- Output: `outputs/r6_si1_bandwidth_f2b_d1a_attestation/D1A_RESULT.json`, report, raw DOF/node/component map, F2A-V census index map e `D1A_ARTIFACT_MANIFEST.json`.
- Manifest SHA256 `5002d7bdb1c24d7d3c945b4edc1970b45c86b6daffb55268b67201616ea6653a`; result SHA256 `74328b449f41fbf7b467582adb53715c518a09327807401a1dbb4a789aff07a9`.
- Decisione `DOF_MAPPING_PARTIAL`: bijezione/inversa 64.442 nodi; FEG 64.442 node rows, 128.880 triangoli, 386.640 riferimenti; runtime 64.442 record e 3.222.100 campi; staged FEG/runtime identici ai derivati BW1; raw DOF component-slot mapping verificato secondo sorgente storico.
- Determinismo: una seconda esecuzione in root distinto ha prodotto gli stessi hash di result, report, mappe e stessi contenuti manifest. Originali F2A-V non modificati; nessuna esecuzione Fair/MPI/Solver/fattorizzazione.
- Limite esplicito: `component_geographic_basis_mapping=DOF_MAPPING_UNVERIFIED`; attribuzione geografica/placche delle coppie census vietata. Originale F2AV resta `BLOCKED_F2AV_QUALIFICATION`.
- Review finale: i payload FEG/runtime sono confrontati con gli SHA indipendenti riportati dal BW1 source report; i manifest locali corrispondono ai rispettivi blob Git HEAD. Il writer output rifiuta sovrapposizioni con BW1, recovery, ShellSet ed evidenza sorgente. Rerun con codice rivisto riproduce manifest/result SHA sopra; regressioni finali 11 passed.

## F2B-D1 design (2026-10-10; non è un'attestazione)
- `docs/arcana/SI1_BW1_F2B_D1_DOF_PROVENANCE_CONTRACT.md` — `DESIGN_COMPLETE_PENDING_ATTESTATION`. Registra path e SHA256 candidati per permutation, FEG/runtime riordinati, BW1 manifest/report/staging contract, manifest/result originali F2A-V e otto input staged. La revisione è design-only: verifica esaustiva dei contenuti resta D1A. Non trattare D1 come PASS di bijezione, trasformazioni FEG/runtime o base geografica.
- `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md` — design-only F2B; supporta la separazione D1/D2/D3 e non conferisce autorità di esecuzione.
- Il locator dell'evidenza originale F2A-V e gli hash per-file sono nel contratto D1. Gli output recovery locali restano non tracciati e preservati, fuori da questa consolidazione documentale. Manifest recovery `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f` distinto dal manifest originale F2A-V `e59a1a31a450c7028b7a405cd6641454d9d67e082c7b62bd2132a0e452852854`.

| Evidenza | Identità / percorso | Conclusione consentita |
|---|---|---|
| ShellSet Fair upstream parallel capacity | `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json` | 9/9 modelli ListEx1 in parallelo, capacity patch, LAPACK smokes; NON ARCANA mechanics |
| Fair OrbData/ARCANA loading | `R6_T0_ORBDATA_ARCANA_FAIR_RUNTIME_QUALIFICATION.json` | qualified runtime integration, NON full physical solve |
| R6 B6N5 structural gap | `docs/arcana/B6N5_POST_RIFT_STRUCTURAL_TRANSITION_AUTHORITY.md` | `BLOCKED_B6N5_INSUFFICIENT_STRUCTURAL_TRANSITION_AUTHORITY` |
| R6 B6N6 model | `docs/arcana/B6N6_ADAPTIVE_PROPAGATION_STATE_EXTRACTION_ARCHITECTURE.md` e 2 contracts R6 | architecture only |
| BW1 F1 | `$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F1/3b8ab7a588d3b658255e41bd5a92e5a31b78604a-memory-cap32-20261008T185921Z` (Fair) | bounded assembly-only |
| F2-A original | Source commit `e1694e18ddf1843c6709dd7e78f5de7bd6a281b4`; manifest SHA `605559ef61a652ae565d7240da33a089b5cda08cb1159052cb77fc2d58f4a1cd` | original `BLOCKED` preserved |
| F2-A recovery | `$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2A_RECOVERY/dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3-20261008T222906Z`; manifest SHA `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936` | recovery reconstructed, review required |
| F2A-V compile-only | Fair `BW1_F2AV_COMPILE_ONLY/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T125317Z` | compile only PASS |
| F2A-V full assembly-only | Fair `BW1_F2AV_RUN/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z`; source `df670c8...`; MPI rc75 | `BLOCKED_F2AV_QUALIFICATION` (invalid saturation indicator) |
| F2A-V original transferred archive | GitHub evidence branch `evidence/r6-bw1-f2av-20261010` commit `f318a217dfee2f99d51e834948bcf765d5d45c6b`; LFS SHA256 archive `0a67103b04959e4f4c0c211a29800f31262f4950ebe34bee60ffa14166041c64` | same original evidence, no scientific promotion |

**F2A-V recovery parziale (2026-10-10, report Codex locale non ancora committato/verificato indipendentemente):** Windows `outputs/r6_si1_bandwidth_f2av_offline_recovery/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z/F2AV_RECOVERY_RESULT.json`; derived-manifest SHA256 dichiarato `e2c945442ab49397bc94164c41498b38fc3f091d65db60481c19ca8ec7612ec4`; decisione `BLOCKED_F2AV_RECOVERY_MISSING_F2A_REFERENCE`. 79 file originali e 8 staged inputs riportati integri; CSV normalizzato e diagnostica intrabundle riconciliata. Nessuna promozione.

**F2-A sealed reference ora presente e verificato nel worktree Windows** (aggiornamento 2026-10-10): percorso Fair `BW1_F2A_RECOVERY/dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3-20261008T222906Z`, richiesti `F2A_RECOVERY_RESULT.json`, `F2A_RECOVERY_ARTIFACT_MANIFEST.json` e manifest SHA256 `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`. Non dichiarare F2A-V recovered prima di comparazione incrociata effettiva.

**External evidence boundary:** Fair file paths and copied Windows paths are locators, **not** proof that current session has mounted/read those files. GitHub LFS pointer alone is not the binary; `git lfs pull`, archive SHA and inner manifest must be checked.

## Nuovo trasporto F2-A sealed (2026-10-10)
- GitHub evidence branch `evidence/r6-bw1-f2av-20261010`, nuovo commit **`72df050f1dc6616426fd25b33fd7de0cc15d83ac`**, che aggiunge `evidence/F2A_RECOVERY_dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3-20261008T222906Z.tar.gz` (Git LFS) e `.sha256`.
- Fair SHA256 del **manifest interno** verificato prima del push secondo il log: `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`. Non inventare il SHA256 del tar: leggerlo dal file `.sha256` al download.
- Windows archive download, SHA verification e unpack: **PASS** (report di esecuzione utente 2026-10-10). Result F2-A verificato presente. Nuova F2A-V recovery con `--f2a-recovery-root`: exit 0; decision `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`.

## F2A-V complete offline recovery — 2026-10-10
- Windows output (non committato): `outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/F2AV_RECOVERY_RESULT.json`, companion CSV/report/manifest in quella directory.
- Recovery evidence manifest SHA256 dichiarato da runner: **`3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`**. Verifica indipendente del contenuto e codice rimane fase successiva.
- Decisione esatta: `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`, exit code `0`; cross-reference F2-A accettato dal runner.
- Contrasto rigoroso: **originale** `BLOCKED_F2AV_QUALIFICATION`; **precedente recovery parziale** `BLOCKED_F2AV_RECOVERY_MISSING_F2A_REFERENCE`; **nuova recovery completa** senza ancora giudizio sulla matrice/solver. Non sostituire/seal originali.

## F2A-V read-only numerical adjudication report (Windows, 2026-10-10)
- Sorgente: report Codex presentato dall'operatore, **non** file sigillato né repository commit. La review ri-verifica recovery manifest `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f` e 3 artefatti; originale F2A-V 79 membri + manifest e normalized CSV fields6/7; F2-A manifest `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`, result SHA reported `5dde558e…5968fe762` (digest parziale nel report, non inventare caratteri mancanti).
- Misure riconciliate: n 128884; band kl=ku=727 nKRows 2182; valid 186996964, nonzero 1804327, nonfinite 0; paired 93434040, mismatches 10 (1 zero/nonzero e 9 nonzero mismatch), max rel 1; diagonal dominance strict/near 0, nonstrict 128884; 18.41 decades coeff range. Full CSV/report nel worktree Windows da consultare.
- IEEE inherited `underflow=true`, `inexact=true`, `overflow=false`; phase inexact in `BUILD_F`, `BUILD_K`, `MATRIX_SYMMETRY`, `ROW_COLUMN_STATISTICS`, `OUTPUT_AGGREGATES`; 0 observed new overflow/underflow per phase. Non dedurre causa.
- Code/review tests `139 passed, 2 skipped`, py_compile/JSON/diff check PASS; default pytest temp directory failure workaround `--basetemp`. NVHPC corrected writer / automated sealed E2E fixture / SciPy BW0/BW1 tests outstanding.
- Decisione **`GO_FOR_F2B_PREFLIGHT_DESIGN_ONLY` come classificazione operativa**; non è un seal scientifico e `BLOCKED_F2AV_QUALIFICATION` resta invariato. No Solver, factorization, mechanics.

## R6 codice di recupero F2A-V pubblicato (2026-10-10)
- Branch `r6/si1-bandwidth-f2av`, commit verificato `61dad0fabaa4f2bb72c386d85a77564894a91ce2`: 4 file writer/recovery/tests; no derived evidence output incluso.
- Il recovery completo resta untracked Windows ma ora è pubblicato separatamente in Git LFS commit `2b03fa558b02cb865c4f234e45f0386fab678822` (manifest `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`). La pubblicazione non è un seal scientifico né aggiorna il verdict originale.
- Test `139 passed, 2 skipped` precedentemente riportati; questo commit non dimostra NVHPC compile del writer corretto, run end-to-end automatico con F2-A sealed o solve.

## F2A-V complete derived recovery transport — PASS (2026-10-10)
- Evidence branch `evidence/r6-bw1-f2av-20261010` at commit `2b03fa558b02cb865c4f234e45f0386fab678822`; original Fair F2A-V and F2-A sealed remain in preceding evidence commits.
- Git LFS pointer `evidence/F2AV_OFFLINE_RECOVERY_F2AV_WITH_F2A_REFERENCE_V1.tar.gz` and SHA sidecar published. Archive SHA256 `bdde8d4320b1fa6de577988bf911817918e910373bdbff9922c9d9c98f646562` confirmed from GitHub sidecar and Windows log. LFS binary not independently downloaded in this update.
- Internal manifest of derived complete recovery SHA256 `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f` (3 artifact members + manifest verified locally). `PASS_F2AV_RECOVERY_SOURCE_INTEGRITY` and `PASS_F2AV_RECOVERY_EVIDENCE_PUSH` from Windows logs.
- Recovered decision `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`; later numerical adjudication only authorizes F2B DESIGN. Original `BLOCKED_F2AV_QUALIFICATION` immutable.

## F2B design reconnaissance (report Codex, 2026-10-10)
- Fonte secondaria: report read-only eseguito dal checkout Windows `6e6bd36f3db2e6e07f406d757721f7a4b552cf8b`, riportato dall'operatore. Nessun run, test, commit o output di evidence prodotto in quel checkout. GitHub era già a `bb3b6c781e6d8dac20c446ab9b0e97fe634cb61d`; questa ricognizione è stata integrata solo a livello documentale.
- DOF mapping candidato con permutation `new_to_old/old_to_new`; FEG/runtime staged individuati nel report. SHA **solo prefissi** `a0895fd9…`, `18d78ec0…`, `a68c0730…`; non sono verifiche complete, no seal DOF/geografia.
- Confermati dal report `DGBSV` (source code verified), `nRank=128884`, banda `727`, `nKRows=2182`, un array REAL*8 `2249799104` byte. Residual/backward-error/INFO/gauge restano futuri gate. Non esiste una nuova matrice né un solutore qualificato.
- Documento derivato `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md`, **design-only**. L'originale `BLOCKED_F2AV_QUALIFICATION` e la recovered evidence LFS `2b03fa558b02cb865c4f234e45f0386fab678822` rimangono distinti.

| 2026-10-10 | F2B-D2 ShellSet operator classification audit | docs/arcana/SI1_BW1_F2B_D2_OPERATOR_CLASSIFICATION_AUDIT.md; historical ShellSet df670c8c4faaed641997f5c4bdb701e2ba0afc7d; recovered F2A-V result SHA256 ff32569dc56f500725ca45c790d7e3ea925bc1e99df5d28138e6342ab4b9979f, manifest SHA256 3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f | OPERATOR_CLASS_UNVERIFIED; theoretical SI1 symmetry INDETERMINATE; sufficient alpha reciprocity conditions derived but active tangent values unavailable; ten census discrepancies unexplained. Original F2A-V blocked decision preserved. No execution | Next F2B-D3 resource/residual acceptance design only; Solver unauthorized |

## F2B-D3B-P0 offline validator consolidation — 2026-10-10
- Branch `r6/si1-bandwidth-f2av`; source baseline parent `f571516ce09c726bffd262d172a922968bdab944`; implementation and tests are contained in the consolidation commit recorded in Git history.
- Decision `D3B_P0_REVIEW_PASS_WITH_BOUNDED_SCOPE`; 24 passed, 2 skipped, 0 failed. Resource snapshot TOCTOU HIGH closed: parsed result bytes are the exact bounded snapshot checked against the independently pinned manifest digest. Case/report/manifest and every member have separate hash/size checks; Git source commit identity remains declared-only.
- Four file SHA256: resource `cae86cd5d16d3f4633d45a9ae4ffb6a9808838c41fd2c8ac6e3bf317f5c548ae`; numerical `275714d7615cffa062c8ac1d4a992edd5a2070744653a6b4cf0cfec914e7b46e`; resource tests `7e2ddf108836229e79475ffe47b2f2cd19d256beaa8459bd51451b93b1c2fec1`; numerical tests `5b00d4a6b4220b0675183e43a1f028572a437825bfc383ce55d3b9cd1a8ce8aa`.
- Symlink runtime tests `NOT_TESTED_RUNTIME_WINDOWS` (creation denied; WSL unavailable); POSIX descriptor-based behavior not executed. Windows concurrent path replacement is not claimed atomic. NVHPC ABI, Fair memory/RSS/enforcement, and historical Git objects remain unauthenticated. No real operator qualification.
- Proposed next gate `F2B-D3C — FAIR_RUNTIME_AND_RESOURCE_AUTHORITY_RECONNAISSANCE`, read-only, including a separate POSIX symlink check if a suitable environment exists. No job or Solver authorization.

## F2B-D3C Fair runtime/resource authority reconnaissance — 2026-10-10
- Report: `docs/arcana/SI1_BW1_F2B_D3C_FAIR_RUNTIME_RESOURCE_RECONNAISSANCE.md`; SHA256 `76a5a65adbbc7d6a9b6a64b35497ee9cd3f4642f286d672579d2779f7f53d058`; decision `D3C_RECONNAISSANCE_COMPLETE__EXECUTION_AUTHORITY_GAPS_REMAIN`.
- Riconcilia tre identità senza trasferire qualifica: runtime upstream storico con binario/hash/toolchain registrati; F2A-V con run/source/log/input attestati nel recovery ma senza SHA dell'eseguibile, ABI/linkage/toolchain effettivi UNKNOWN; candidato F2B non identificato. Le formule D3A sono stime condizionali all'ABI.
- Limiti Fair effettivamente imposti, RSS/PSS/cgroup e headroom non dimostrati; i valori del contratto sono dichiarati e aggregate enforcement è esplicitamente false. I due test symlink restano `NOT_TESTED_RUNTIME_WINDOWS`. Nessun accesso Fair o job in D3C.
- Next proposto: `F2B-D3D — FAIR_EXISTING_EVIDENCE_ACQUISITION`, sola lettura di evidenze preesistenti. Non autorizza job, build, Solver o diagnostici numerici. Gate scientifici e divieti invariati.

## F2B-D3D Fair existing evidence acquisition — blocked handoff (2026-10-10)
- Report `docs/arcana/SI1_BW1_F2B_D3D_EXISTING_FAIR_EVIDENCE_ACQUISITION.md`; SHA256 `fb5194bc6ed5bfa4e5d08bec322afae25a09373a0981d24bb7df2fefdab26701`.
- Decisione `D3D_BLOCKED_EXISTING_EVIDENCE_UNAVAILABLE`; stato `REMOTE_EVIDENCE_ACCESS_UNAVAILABLE`. Nessun accesso Fair e nessuna acquisizione di file. Non è stata verificata l'esistenza dei locator remoti; non inferire assenza dell'evidenza.
- Nessun manifest di acquisizione creato. Prossimo passo invariato: operatore già autorizzato legge esclusivamente i due locator compile-only/run descritti in `NEXT_ACTION.md`; identità dei due eseguibili va verificata separatamente. No job/build/Solver.
- Gate invariati: `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `BLOCKED_F2AV_QUALIFICATION`, Solver/mechanics/WORLD_HISTORY production non autorizzati.

## F2B-N2C-W1 — Fair synthetic cross-compiler verification (2026-10-11)
- Decisione `N2C_W1_SYNTHETIC_FORTRAN_CAPTURE_CROSS_COMPILER_PASS__SI1_INTEGRATION_NOT_QUALIFIED`; entrambi i run hanno testato commit `7a4119112a16e32c8cbdae5248ebd91f4020a458` in `arcana-r6-linux`, Python 3.12.14, pytest 9.1.1.
- GNU Fortran 13.3: 25 passed, 0 failed, 0 skipped, exit 0. Fair log locator `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2C_W1/N2C_W1_gfortran_20261011T105150Z.log`; SHA256 `a8bb7959edcf10c125597f0b00a5bbe912358201176de6ee84336fe5c4d5a892` riferito dall'operatore.
- NVFORTRAN 25.11-0: 25 passed, 0 failed, 0 skipped, exit 0. Fair log locator `/home/jlpfritas/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_N2C_W1/N2C_W1_nvfortran_20261011T105152Z.log`; SHA256 `19edadd6dfdb1d1395894a5e05117782d348270237dec12c541009b36f347782` riferito dall'operatore.
- Due precedenti run sul commit `57b2bd1f` restano 24 passed / 1 failed ciascuno. Il difetto cwd dell'harness è stato corretto nel successivo commit `7a411911`; i rerun positivi sono identità distinte e non riscrivono i fallimenti. Codex Windows non ha acquisito o ricalcolato i log Fair.
- Scope sintetico: writer ARCNSNP1, bande variabili, payload/oracle, failure paths e pre-Solver marker nella fixture. Non attesta integrazione ShellSet, binding invocation/FEM, identità runtime, hash autonomo, durabilità, SI1 matrix, risorse, accettazione numerica o autorità Solver. Nessun nuovo run HPC in questa consolidazione Windows.
- Prossimo gate `F2B-N2C-W2`: candidato separato dal source lock, binding d'identità e sidecar, validazione esterna, stop pre-Solver e analisi dei limiti di scala senza confondere i limiti del codec/test con RAM Fair.


## F2B-N2C-W3-B / B1 — offline synthetic only (2026-10-11)
- W3-B baseline source is already published at `2bb34525c4098eded5ee65eca02428c92d5c68b3`; this is not `WINDOWS_WORKTREE_ONLY`. B1 is recorded as a distinct follow-up correction. No external evidence bundle was created.
- Report: `docs/arcana/SI1_BW1_F2B_N2C_W3B_OFFLINE_INVOCATION_BINDING.md`, SHA256 `ae7f5e5d3e4cd60adf99b621711c8db2354a8901341314d09bb2a4d6243a8810`. Validator `scripts/r6_si1_bandwidth_f2b_n2c_w3b_provenance.py`, SHA256 `5fbddee8c59a25eb76155cc2feb7ba0a2534aa264dbfb3ab02adf147847a50a2`; fixture tests `tests/test_r6_si1_bandwidth_f2b_n2c_w3b_provenance.py`, SHA256 `a47326842c9afe8c9c86e5da5e80d247533386ff562c3b781f12ba8f600e1370`. These identify repository artifacts only; they are not evidence for runtime identities.
- B1 keeps assignment sequence bound to one immutable assignment/model/worker/owner identity while allowing multiple distinct FEM call coordinates. A separate coordinate key excludes mutable state/system/payload/sidecar content, so such content changes cannot disguise duplicate calls. `Pure` loop/FEM call source references: `external/ShellSet-v1.1.0/src/MOD_Shells.f90:6940,6996`.
- Offline suite (W3-B, N2A, N2C writer, W2 overlay): 41 passed, 1 skipped (compiler-dependent writer runtime; default `gfortran` unavailable). Windows-local; no Fair/MPI/ShellSet/Solver run. Synthetic fixture authority is not production owner authority; no external evidence bundle was created.
## F2B-N2C-W3-C-B — modello sintetico coordinator (2026-10-11)
- Codice: `scripts/r6_si1_bandwidth_f2b_n2c_w3c_protocol.py`; test: `tests/test_r6_si1_bandwidth_f2b_n2c_w3c_protocol.py`.
- Report/addendum: `docs/arcana/SI1_BW1_F2B_N2C_W3C_RUNTIME_AUTHORITY_AND_MPI_STOP_DESIGN.md`.
- Test locali Windows: `python -m pytest -q -rs --basetemp .pytest-tmp-w3cb-focus-final-20261011 tests/test_r6_si1_bandwidth_f2b_n2c_w3c_protocol.py` — 21 passed, 0 failed, 0 skipped. Output/evidence Fair: nessuno; nessun manifest aggiunto.
- Regressioni integrate W3-C-B + W3-B + N2A + N2B + N2C writer + W2 overlay: 73 passed, 4 skipped, 0 failed. Tre skip richiedono gfortran per N2B e uno per il writer N2C; il compilatore non è disponibile su Windows.
- Autorità: soli dati fixture con `SYNTHETIC_FIXTURE_ONLY`; il digest lega la decisione serializzata ma non autentica un owner o un run. Runtime authority resta UNKNOWN. Nessuna prova MPI, stop coordinato reale, ShellSet, Solver o acquisizione SI1.

## INT-0B — singolo tentativo fallito (2026-10-13)
- Source branch/HEAD/parent: `r6/si1-bandwidth-f2av` / `683230f5e66397478642c2b8a48550eb1d00cca7` / `dde79ebe4d26ab7b21eff08245fc83330239c0bc`. Provider audit ripetuto sul source HEAD; Python 3.12.10, NumPy 2.3.5; output path assente prima del run.
- Una sola esecuzione del comando registrato nel preflight; exit 1 dopo 25.427 s. Eccezione a runner line 114: `TypeError` perché `zip(times, times[1])` usa uno scalare al posto della sequenza rimanente. Nessun candidate artifact/manifest; replay, restart ed endpoint validation non raggiunti. Nessun retry.
- Osservazioni supervisor (campionamento 250 ms): peak working set 4,509,696 byte, peak/final run-output bytes 0, 97 poll. Uscita naturale, il supervisor non ha terminato il run. `Process.Kill(true)` verificato separatamente su un sleeper innocuo. Limiti monitorati, non hard OS quotas.
- Failure evidence post-run in `outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01/`: `ATTEMPT_FAILURE.json` SHA256 `317c0a48e3ea75d68b951a5ca94bd743ddd3797592e3d92a9cb588c6328919ac`; `RUNNER_STDOUT.txt` SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; stderr transcript SHA256 `c9ab97c5d1694c33bca1e571a5432786e313b18d22390e990c50f1e3daba2590`; failure manifest SHA256 `5a3ac90fe43211b9a6cb698b7375d70d9b5a6369ca24647cf0f6af9eb9c97ef3`. Transcript is a transcription from supervisor output, not re-read original stderr bytes. The failure manifest lists the three members and is not the absent candidate-run manifest.
- Report: `docs/arcana/INT0B_EXECUTION_REPORT.md`. No numerical trajectory result; original scientific gates remain blocked. Next `INT-0B-R1` offline correction and regression only; any further run needs new explicit authorization.

## INT-0B-R1 — offline runner correction (2026-10-13)
- Report: `docs/arcana/INT0B_R1_RUNNER_CORRECTION.md`; decision `INT0B_R1_RUNNER_VALIDATION_CORRECTED__REEXECUTION_PENDING_AUTHORIZATION`; records regression against the former scalar slice, 40 relevant local tests, provider audit on `e95c7dbf`, and bounded synthetic supervisor observations. No trajectory or candidate evidence bundle was produced.
- Proposed output `_02` was absent when checked; old failed `_01` evidence was rehashed read-only and preserved. Do not reuse `_01`.
- Current provider audit source identity `9e027419bd47b551e9d883fde9f0d2e5f08bd415b06872db300161cd3a8b6ea0` is HEAD-bound to `e95c7dbf`; recompute after the correction commit. Provider source/payload identities remained aligned with the preflight table. Synthetic supervisor evidence does not retroactively corroborate the prior run's 4,509,696-byte observation because its PID/image were not retained.
## INT-0B-R2 — child environment isolation and provider audit (2026-10-13)
- Correction commits: supervisor/test `d9d87fe8853b5c17f5bc8fd27d496aaf9aa45b57` (parent `cac78c08e8f3d946b5ec089c3b3778f8cc2a2496`); previous chain includes `33acb129ab9ba8d8a319bad3a8a0ef7f348560ae`, `a0188150f21db80d7e4a9804f828245992754387`, `4cc7a78d95ee7e529394173933817a7266db251d`, `e95c7dbf281ede5312512654262b9925fa87eb02`. No history rewrite.
- Report: `docs/arcana/INT0B_R2_EXECUTION_ENVIRONMENT_ISOLATION.md`. Decision `INT0B_R2_EXECUTION_ENV_CORRECTED__THIRD_ATTEMPT_PENDING_AUTHORIZATION`.
- Offline supervisor self-test used invalid parent `GIT_OBJECT_DIRECTORY` and `GIT_ALTERNATE_OBJECT_DIRECTORIES`; unsanitized child failed Git object access, sanitized child verified repository discovery, exact HEAD, `git cat-file` commit type, Python 3.12.10, NumPy 2.3.5, retained PATH/PYTHONPATH/external root and required external payload. Process-tree termination/resource stop/exit propagation checks also passed. 41 relevant tests passed; `py_compile` and `git diff --check` passed.
- Provider audit ran through the sanitized supervisor launch path on source HEAD `d9d87fe`; source identity SHA256 `7438690f5b7d59b1ab0177a0ac270deb188fcfc233308131da6d6515998461bd`. Result `outputs/r6_functional_development/INT0B_R2_SUPERVISION_20261013_FINAL/provider-audit/provider-audit-result.json`, 101132 bytes, SHA256 `2db09f684c59acb40a1115794f47b0e06c9d8e4dd33c67360948339cd3a994b1`. Child diagnostic confirms both object-store variables absent, correct `ARCANA_EXTERNAL_ROOT`, and required physical payload present.
- Provider hashes unchanged: field package `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`; support index `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00`; vector partition `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`; event census `e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e`; kinematics `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2` and semantic identity `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`.
- Proposed `_03` destination was absent when checked; `_01` and `_02` evidence preserved. No trajectory output, numerical evolution, Fair/MPI/ShellSet/Solver, INT-1, or WORLD_HISTORY operation. Await separate explicit authorization.
## INT-0B-R4 - fourth noncanonical trajectory (2026-10-13)
- Source branch/commit: r6/si1-bandwidth-f2av / 91fc83d50ec15d8bb9b826926ac2f2dc859281e8; parent 50fbf6dfe1b8068a243ffa60df9ef22e1f5d6876; runner SHA256 a0a1f87aeb865b4cecf56c515310286a3bdaa9e399548c59e5976013e2b5814b; supervisor SHA256 9c942383f298a602acba77e313d876ec1dd50c3c0cb92b5ee345495f16baea98.
- Provider audit: outputs/r6_functional_development/INT0B_R4_PREFLIGHT_20261013_91fc83d5/provider-audit/provider-audit-result.json, 101132 bytes, SHA256 1bfbc52d26a4d7565d9b9fcd1d823aca56197eb77ba8fb7ff3f0e6cb84011a17; source composite b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca; pair 5:11 and admitted supports are detailed in the execution report.
- Candidate: outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/; decision CONTINENTAL_ENGINEERING_SLICE_PASS; candidate manifest SHA256 191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236; RUN_RESULT SHA256 b7625dfc636bc86f062ab38db42ee04215864de2390b78f69fbfe17c2438124a. Seven listed artifacts and RUN_RESULT size/hash checks pass; nine expected directory entries.
- Sampling/restart: four samples per support at 0, 484.6791203689449, 969.6005802980742, and 1000 years; temporal order, finiteness and endpoint agreement pass. Replay/restart flags pass; restart/uninterrupted maximum temperature difference 9.992213563236874e-07 K per support. Per-artifact hashes are in docs/arcana/INT0B_R4_EXECUTION_REPORT.md.
- Supervisor evidence: outputs/r6_functional_development/INT0B_R4_SUPERVISION_20261013_04/; natural exit 0, 20.633493 s, PID 39408, peak sampled tree working set 164384768 bytes, final cumulative output 691140 bytes; captured stdout 296 bytes SHA256 8fb2b0294f2c87c996c8c40bd0502bee675a092e23c387e6109d8f1e93cfe0f0, stderr 0 bytes SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. Operational thresholds are sampled, not OS-enforced.
- Decision: INT0B_NONCANONICAL_INTEGRATED_RUN_EVIDENCED__SCIENTIFIC_PROMOTION_NOT_AUTHORIZED. This does not qualify the physical section, long-term temporal validity, ARCANA mechanics, Solver, or canonical state. Prior _01-_03 failures stay immutable.
# INT-1A — empirical retention/reconstruction baseline (2026-10-13)
- Source: immutable R4 candidate `outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04/`; candidate manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`; run result SHA256 `b7625dfc636bc86f062ab38db42ee04215864de2390b78f69fbfe17c2438124a`; source commit `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`; source-composite identity `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`. The offline verifier rechecked exact nine-file membership, all expected member bytes/SHA256 and cross-artifact endpoint/checkpoint/replay provenance; no source bundle mutation.
- Reviewed INT-1A output: `outputs/r6_functional_development/INT1_RETENTION_20261013/FINAL/`. Analysis-manifest SHA256 `ad2bc118c4c7a15d56a87a3056b4d16ddedcf410f7a65a89c782d8ba41b522ce`; metrics JSON `7915d6786d31be3b9d6b7ea19568dbe1982cea87b561bed309d6a9de38430096`; storage CSV `47e789aa247b9d06db06f3efea2f5cf77a0d12afebbfcbe491daeecb3dc2931f`. Sidecar matches the analysis manifest. Earlier first-pass and intermediate analysis folders from this task remain preserved and are superseded by `FINAL/`.
- Decision `INT1A_RETENTION_EMPIRICAL_BASELINE_EVIDENCED__GENERAL_POLICY_NOT_QUALIFIED`. Four samples/support, two distinct interior times, two supports with identical observed numerical series. Full diagnostics: 85,583 bytes; checkpoint pair: 83,624 bytes; endpoints-only deterministic subset: 58,905 bytes; one-interior subsets: 72,233 / 72,261 bytes. Reconstruction metrics and field inventory are in the metrics JSON/report. Retrospective adaptive selector is not online evidence; event retention and general policy UNKNOWN.
- Validation: 12 new offline synthetic tests passed. Combined attempted collection of `test_r6_functional_development_t_f2b_samples.py` and `test_r6_int0a_pipeline.py` was blocked because NumPy is absent in active Windows Python; no packages were installed. No new evolution, Fair/MPI/ShellSet/Solver, canonical publication or WORLD_HISTORY access.
## INT-1D — provider preflight blocked (2026-10-13)
- Report: `docs/arcana/INT1D_PROVIDER_PREFLIGHT_BLOCKED.md`; source commit `ffeb02e90abc4c3a542ac9a794c57ee8496b211b`; requested boundary `R6BND-T0-27e4d497530e681071fb`.
- Python 3.12.14 / NumPy 2.3.5 available. `ARCANA_EXTERNAL_ROOT` was unset. Read-only `audit_pair_5_11` failed with exact error `KinematicsAuthorityError: governed payload unavailable: CANONICAL_T0_PHYSICAL_PAYLOAD`.
- No provider-backed verification/source-composite identity, evolution, candidate output, or new numerical evidence. Existing R4 evidence preserved; its manifest SHA256 remains `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`.
## INT-1D supervisor recovery (2026-10-14)
- Report: `docs/arcana/INT1D_SUPERVISOR_RECOVERY.md`. Recovery starts at `54c0cce119da9e061545792840f9b7c430159c7c`; tracked code change is confined to the supervisor plus targeted environment/command tests. The prior `_01` failed-launch record remains immutable: failure JSON SHA256 `5bcbf21abdd0f09a362b784808dad2cc1b19add350168aad10a74ebe647b40a6`, copied launcher SHA256 `8541230c6b6e96fd6f3ffd9ba311bf6381b0592018c85871a54e5f4c176b67db`.
- Failure classification: process start was not called; numerical runner did not start; no candidate output or process measurements. Root cause was relative trace path resolution under differing PowerShell and .NET current directories. Existing R4 evidence is not modified.
- Recovery verification: provider-support + supervisor/environment tests 19 passed using Python 3.12.10 / NumPy 2.3.5 / pytest 9.1.1 and configured `ARCANA_EXTERNAL_ROOT`. Cross-CWD path/command plan tests do not execute numerical evolution. Final-commit provider audit and source-composite SHA remain mandatory before the conditionally authorized single `_02` run.
- Reserved fresh paths (must be absent immediately before execution): `outputs/r6_functional_development/INT1D_TF2B_5_11_R094C025_C026_20261014_02` and `outputs/r6_functional_development/INT1D_SUPERVISION_20261014_02`. No new trajectory is yet evidenced.


## INT-1D — distinct-boundary candidate trajectory and R4 retention comparison (2026-10-14)
- Final source: `r6/si1-bandwidth-f2av` commit `3fa149b7639f59c934a4d722acb388eacc4c9628`, parent `54c0cce119da9e061545792840f9b7c430159c7c`. Provider audit result `outputs/r6_functional_development/INT1D_PROVIDER_AUDIT_20261014_02/provider-audit/provider-audit-result.json`, 101,193 bytes, SHA256 `3102121346ba63c0cd266d9799c33f5300e1eda79f4e2bd8bb95a2337458a8c3`; source-composite SHA256 `a1a4503fe57206750884e454d8a12d778caee38e34b35586805241ad51c01954`. Exact requested/selected boundary `R6BND-T0-27e4d497530e681071fb`, pair 5:11; two admitted `CONTINENTAL_NORMAL` supports `R6G1D-R094-C026` and `R6G1D-R094-C025`, 73 nodes each; signed Ux `0.10694074272424924 m/year`.
- Candidate bundle `outputs/r6_functional_development/INT1D_TF2B_5_11_R094C025_C026_20261014_02/`: exact nine-file membership; manifest SHA256 `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`; run result SHA256 `603c4e36c7f25d29df300bedb5496bd8ecfb5fa471fb07c29a41af096e3a469b`; diagnostic samples SHA256 `540c668b7e0e186e7c0efe36e5fc94d1afe09550a2f5b235ef3485e8b77b1916`; all member bytes/SHA and cross-artifact endpoints reconciled.
- Nine strictly ordered finite samples/support at 0, 129.57192262500018, 259.1600417403285, 388.7643593705462, 518.3848775404676, 648.0215982751603, 777.6745235999448, 907.3436555403949 and 999.9999999999998 years. Each support: width +106.9407427242 m; crust -33.7324888783 m; lithosphere -130.1110285306 m; max nodewise temperature change 0.02181131702935 K. Resolution comparison, endpoint/checkpoint binding and restart/replay digests are in `docs/arcana/INT1D_EXECUTION_REPORT.md`.
- Supervision: `outputs/r6_functional_development/INT1D_SUPERVISION_20261014_02/`; natural exit 0, 24.314529 s, PID 37920, peak sampled process-tree working set 173,670,400 bytes, output 821,761 bytes. These are monitored observations; thresholds were sampled and not OS-enforced.
- R4 bundle revalidated with its original manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`, sample SHA256 `ca9c5a4bc6ff4441b198219183e4e564a391d239dfda6e2f87598b7bd14bebad`. INT-1A evaluator measured endpoint and retrospective subsets at recorded times; case-specific byte/error results are in the report. The retrospective selector uses future endpoint/full trajectory; general/online/event retention remains unqualified.
- Decision `INT1D_DISTINCT_BOUNDARY_TRAJECTORY_EVIDENCED__GENERAL_RETENTION_POLICY_NOT_QUALIFIED`. Earlier `_01` failed-launch and INT1D provider-blocker records remain immutable historical evidence. No Fair, MPI, ShellSet, Solver, DGBSV, physical post-rift evolution, or WORLD_HISTORY publication. No scientific promotion.
## INT-2A — offline historical query and reconstruction baseline (2026-10-14)
- Decision: `INT2A_OFFLINE_HISTORICAL_QUERY_RECONSTRUCTION_EVIDENCED__B0_EXECUTABLE_BINDING_NOT_QUALIFIED`. Report: `docs/arcana/INT2A_OFFLINE_HISTORICAL_QUERY_RECONSTRUCTION.md`. Read-only input verification used the pinned INT-0B R4 and INT-1D bundles; the produced result is `outputs/r6_functional_development/INT2A_HISTORICAL_QUERY_20261014_07/INT2A_QUERY_RESULTS.json` (230,323 bytes, SHA256 `e12c139ddc85d9a29a4edd5bcd03e080b35237df3e03382e5b46e0d0614c849f`). Output manifest SHA256 `b613c94c95c41df503abf0a83ed26f817e00ea6de52822b436152cdc1d84b33d`; sidecar SHA256 `b848dd1d786780714dc20df659d61c8a71fb4056558aaf497b9087b38474af6b`.
- The offline query supports exact observed-time selection, strict bracketing and labeled piecewise-linear reconstruction only on matching material coordinates. It refuses nearest-sample substitution, coordinate interpolation and physical refinement without an authorized evolution kernel. Retention/error comparisons reuse INT-1A evaluation on actual timestamps. R4 has 4 samples/support; INT-1D has 9 samples/support. Support histories are identical within each experiment and are not independent replicates.
- Tests: INT-2A + INT-1A `27 passed`. Combined B0 history tests were also attempted: `28 passed, 9 failed`; the nine failures were blocked at existing immutable `HistoryStore` setup because Windows denied `os.link` (`WinError 5`). No B0 source changed. No source bundles or canonical data were modified; no physical run, B0 registration, executable replay, scientific promotion or WORLD_HISTORY mutation occurred. Next: proposed INT-2B, a minimal noncanonical adapter from verified bundles to typed B0 query records, subject to separate review and authorization.
## INT-2C-A — R4 executable replay binding preparation (2026-10-14)
- Decision: `INT2C_EXECUTABLE_REPLAY_BINDING_CODE_READY__NUMERICAL_VALIDATION_PENDING`. Entry source `6a719da728baa11c4a972195d357fde7c32d21b3`; INT-2B closure now published by verified fast-forward from remote `14208a1e4c4462414e571477a662ba3e06ca4a09`. New focused adapter/test/report; no new numerical evidence output.
- Reused/authenticated R4 nine-file bundle (manifest `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`), complete initial/candidate payloads, historical typed descriptors and pretty-JSON/LF direct-output hashes `2b4836954e688d7aac6d9e26ccb61aa02fa94e9e40550c395922b30fa1b45d7b` for both sides. Original files/IDs retained. INT-1D remains a separate later replay case, reverified read-only by existing regressions.
- Local historical/current kernel normalized bytes independently match SHA256 `bddedfd7439b328951389012b2af371d106d042018ac4be928325a6395666542` at R4 execution commit `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`. Original source-composite field remains sealed bundle identity; full historical runtime binaries are UNKNOWN. Required numerical runtime versions 3.12.10/NumPy 2.3.5 differ from known Fair Python 3.12.14.
- New dependency-consistent checkpoint/recipe/provenance records retain `CANDIDATE_NONCANONICAL`. Current B0 rejects their execution until a separately justified technical validation issues new identities. No B0 contract modification or actual validated R4 checkpoint was made. Full inline expected state ID binds arrays; no external expected payload reference was invented.
- New tests: 24 fixture/contract tests, kernel mocked on every adapter dispatch. Combined INT-2C-A/INT-1A/INT-2A/INT-2B 58 passed, 0 failed, 0 skipped, 1 existing real-store test deselected. No Windows store publication, new numerical replay, scientific promotion or canonical access. Report: `docs/arcana/INT2C_A_EXECUTABLE_REPLAY_BINDING_PREPARATION.md`.
- Windows-recalculated identities: report (11,827 bytes) SHA256 `0f8d6e9d001d21d3073bea75d23600127bc30e0fc5bee2e1f57b4de9a326b6bc`; adapter (20,672 bytes) SHA256 `3a44e797676ceac3a4764bdaa1311157f57910315ead3ea2e4aa20e740cfc11d`; test file (13,138 bytes) SHA256 `b987756986212e0ca816d1d5e537ec4eea2940a022412d8a985c32787be6528b`. These describe source/test/report bytes, not a numerical replay result.

## INT-2B final Fair closure — isolated noncanonical B0 state/query binding (2026-10-14)
- Decision: `INT2B_NONCANONICAL_B0_STATE_QUERY_BINDING_EVIDENCED__EXECUTABLE_REPLAY_NOT_QUALIFIED`; Fair-tested source commit `14208a1e4c4462414e571477a662ba3e06ca4a09`. Imported output: `outputs/r6_functional_development/INT2B_B0_BINDING_FAIR_20261014_01/`. Consolidated report SHA256 `c49a9530abcfb3006c3baa201efca5715aee20606f838a1dc192a8d71a9daa22`.
- Windows-recalculated: result 5,561 bytes SHA256 `287600535bf787a404d15b0ee383f51a651384b42b6ba58b4b0829b6d91713ee`; output manifest 587 bytes SHA256 `64b7aad35f7c880ce39939ab3337c29153b1e37037859c3b0724b1193ecfd4ad`; sidecar file 93 bytes SHA256 `4746c87bc6d2bf1cbaf11ec253e3a29a7407f0eccd1349e6f95a2a7937f8eb30`, whose contained digest matches the manifest. Manifest membership contains the result JSON only.
- Windows independently hashed all 33 isolated-store files (26 states, 2 provenance, 5 metadata/visibility/lock files): total 163,086 bytes. All 28 state/provenance documents match records read-only rebuilt from source bundles pinned by R4 manifest `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236` and INT-1D manifest `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`. Full per-file SHA256 inventory is in the INT-2B report.
- Fair JSON records successful transactional publication/readback, 26 observed-state readbacks, two provenance records, 33 files/163,086 bytes, four timings of 88,782,369–89,818,730 ns, and `MISSING_TIMESTAMP`, `OUTSIDE_SUPPORT`, `CONFLICT` query semantics. Operator reports Linux hard-link PASS, B0 regression 85 PASS and adapter exit 0. No Fair logs were transferred; those execution outcomes are not independently recalculated or log-hash verified on Windows.
- Evidence discrepancy disclosed: `filesystem_capability.volume=NTFS` is not trusted because the Fair-tested adapter hardcoded that label; actual Fair filesystem type remains UNKNOWN. The result's `limitations` also contains stale `NO_B0_STORE_QUERY_PASS` despite successful fields/decision. Original result is unchanged. Earlier Windows `WinError 5` blocked attempt remains immutable and environment-specific.
- Code correction: adapter now detects filesystem type dynamically on Windows/Linux and reports `UNKNOWN` when unavailable; focused regression added. It does not modify the old Fair evidence. Reduced checkpoint payload deserialization is not executable replay; replay and scientific/canonical promotion remain unqualified.
- Windows checks: default project Python 3.12.10 initially lacked NumPy. With existing pytest 8.4.2 and workspace-provided NumPy 2.3.5 on temporary `PYTHONPATH` (no install), the full adapter module reported 7 passed, 1 skipped; the skipped real store/query test is blocked by Windows hard-link denial. `py_compile`, UTF-8/LF, `git diff --check` and direct filesystem-helper smoke test PASS.

## INT-2B — initial Windows noncanonical B0 HistoryStore adapter (2026-10-14)
- Initial Windows checkpoint, before the Fair closure addendum: checkout `r6/si1-bandwidth-f2av` / `a2e3fd8608e7a736bc4aa06073be982b4a6cfd55`. Implementation: `scripts/r6_int2b_history_adapter.py`; tests: `tests/test_r6_int2b_history_adapter.py`. The initial Windows-only report revision had SHA256 `574a28783e0031539ccd9e4ecaa1a2b9dbb64e22014449e8c58227dea0918cd`; the current consolidated report has a new SHA256 recorded at closure.
- Existing INT-2A source loader revalidated the R4 nine-file bundle (manifest SHA256 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`) and INT-1D nine-file bundle (manifest SHA256 `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`) against their pinned identities. Input bundles remained unchanged.
- Adapter constructed 26 observed `DomainStateEnvelope`s (R4 8, INT-1D 18) and two provenance records. It uses separate history/branch IDs, exact observed engineering elapsed-time keys, source execution commits/source-composite identities, manifest/run/sample hashes, provider references, boundary, support, resolution, units, `DERIVED_SUPPORTED`, `AuthorityClass.NONE`, explicit noncanonical applicability, and unknown uncertainty. Reconstructed/interpolated rows are rejected.
- F: volume was reported NTFS. A disposable probe and a probe in output directory created/read the probe file but `os.link` returned `PermissionError [WinError 5]`; probe files were cleaned. WSL distro access was denied (`Wsl/E_ACCESSDENIED`). No Fair B0 test was run. Prior Fair compiler-fixture use of Conda `arcana-r6-linux` identifies a candidate environment only, not B0 storage qualification.
- Focused INT-2B tests: 6 passed, 1 skipped (actual isolated store/query skipped on hard-link capability failure). Related INT-2A/core/B0 group: 16 passed, 9 failed during `HistoryStore` initial manifest installation at `os.link`, before query assertions. `py_compile` and `git diff --check` passed. No B0 store or query executed.
- Output `outputs/r6_functional_development/INT2B_B0_BINDING_20261014_01/`: result 4,284 bytes SHA256 `b11a6d1b057a1676f8da6afb6598a682a9f7255458a37055866f3e481d33006f`; manifest 553 bytes SHA256 `b85216bafd82836f72a0720ef970c84137e5d98acc0092256ca8c562d9290440`; sidecar SHA256 `9b4c497b4bd8f7acd2060cdcd262d623201c23d79d33876f4c1c55a5480a83e1`. Manifest/member readback verified. It records the blocker and no store/query measurement.
- Four checkpoint candidate payloads deserialize via `state_from_payload()` into reduced states, but no B0 checkpoint envelope, closed runner/configuration, forcing binding or deterministic engine adapter is present; executable replay remains unqualified. No canonical `WORLD_HISTORY` access/write, provider evolution, Fair, MPI, ShellSet, Solver or replay execution.
- Decision: `INT2B_BLOCKED_STORE_ATOMIC_PUBLICATION_UNAVAILABLE`. Scientific gates remain `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

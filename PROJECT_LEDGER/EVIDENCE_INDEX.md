# Indice minimo delle evidenze (identità e scope)

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

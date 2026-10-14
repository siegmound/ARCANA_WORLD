# INT-2B — Minimal noncanonical B0 HistoryStore binding

## Final Fair closure addendum — 2026-10-14

Current decision: `INT2B_NONCANONICAL_B0_STATE_QUERY_BINDING_EVIDENCED__EXECUTABLE_REPLAY_NOT_QUALIFIED`.

The earlier Windows result below remains an immutable historical result for that environment: Windows denied the B0 writer's hard-link publication, so that attempt did not create a store or execute queries. A separate Fair run, reported as testing source commit `14208a1e4c4462414e571477a662ba3e06ca4a09`, completed the isolated noncanonical adapter with exit code 0. This is a distinct observation and does not alter or rewrite the Windows result.

### Imported Fair bundle and independently recalculated hashes

Imported bundle: `outputs/r6_functional_development/INT2B_B0_BINDING_FAIR_20261014_01/`.
Windows independently recalculated the byte count and SHA256 of every file currently present in this imported bundle. The result JSON is 5,561 bytes, SHA256 `287600535bf787a404d15b0ee383f51a651384b42b6ba58b4b0829b6d91713ee`. The output manifest is 587 bytes, SHA256 `64b7aad35f7c880ce39939ab3337c29153b1e37037859c3b0724b1193ecfd4ad`; its sidecar file is 93 bytes, SHA256 `4746c87bc6d2bf1cbaf11ec253e3a29a7407f0eccd1349e6f95a2a7937f8eb30`, and the digest written inside the sidecar matches the manifest SHA256. The manifest authenticates the result JSON only; it does not enumerate or seal the isolated store.

The imported store contains 33 regular files totaling 163,086 bytes: 26 state records, two provenance records, one store manifest, two history-visibility files and one writer-lock file. Windows independently hashed each file; the complete per-file inventory is recorded below. The 28 state/provenance JSON files were also compared read-only against records independently rebuilt from the locally verified R4 and INT-1D source bundles using the existing adapter. All 28 matched exactly as parsed JSON, with no missing, mismatched or extra record files. This does not reproduce the historical Fair API readback operation or independently authenticate the execution environment.

| Store path | Bytes | SHA256 |
|---|---:|---|
| `.history_visibility/CURRENT.json` | 128 | `06b4bc820726f73be32cfaeb593ce5277a038d0ab1961a3473e07b263cc58726` |
| `.history_visibility/WRITER.lock` | 1 | `6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d` |
| `.history_visibility/views/view_6cc41e030fe471a95b823555bf04d09a508c24952c96a98e930972d542eab912.json` | 317 | `ac99ec8cc78ae735f44562bb295e698233a210ddeb4f608e6e002260f9740c56` |
| `.history_visibility/views/view_edceda3d478107c3bd01d39ae1889fffa903474072a41bd9a6487e5fe963c89d.json` | 2,413 | `f30a95c967af21dc850493675f0bc852a8d6810dfb1240717a645fde164b398c` |
| `metadata/store_manifest.json` | 151 | `5687a8d346effd3122b59a4f8e3a73cdb14a0769d93d68265aa6373ac692a8d0` |
| `provenance/r6prov_59fbcd51b39736cadc303a2f7ff5d368952b2ff9473579e2bb74c3999bc126f6.json` | 3,104 | `da60548fd8c6c1980fcc75c495eb8c51089c19ded551840f2684808b90d52efd` |
| `provenance/r6prov_ddb28ae55cd97e098113589a0d28c8a91ce5f9e25f02eb56f9a776857bed34be.json` | 3,092 | `bd0132726c0a0135ef8b04b6e79784d0acf35afdd87c2c711af241134f47757a` |
| `states/r6state_07bf9410b986787a25c55895ccb69ac149a216740e37a0542df59acd571034f3.json` | 5,441 | `c64086da64c4ea16dbe47f16981417d5f2e3acaba7866d362ba606bc2fdf0e7d` |
| `states/r6state_1d29ff45c24d11f998d12ea2f9dcaee49630de801be4b379ca65e7017291de68.json` | 5,742 | `62ddbe10eec60f9b0d32dc27b4fd31dc307087d30bd6764f3838bd4150b1c96c` |
| `states/r6state_20ebfe59100d22dbe9dbe0182d6396ce1bf3a2ffd436a87e92604ea8875a3482.json` | 5,740 | `64c5ec34cc567feeca9e182fa305a0e5ab75bc855a425dd69a3cea0c32ed775f` |
| `states/r6state_239905646770756effbfb688a90ce6ef88d67064df4f1e96d11884227ff1d620.json` | 5,441 | `11517f7d6a4f6c0ec4f7d8da1ec19ffdf878b3db9d2893f4634e41e16d775958` |
| `states/r6state_29784871a85e947a81a1b7855ca0320c2128fc2fc619ef51abfaaad3d2ea756a.json` | 6,062 | `7c606a50ab247bef188480a7e83a5d85f4890f4c6af682c6bd9cfb33c4504638` |
| `states/r6state_2e568e28f3abb1828f0900694884524ce3033bb1dbbecab6499afba14f340df8.json` | 5,773 | `8858ce4006c3b26faab257c339965f91e6dcb754257b697e06cf42622e1a35f5` |
| `states/r6state_33a36acc79a5c31e82eb7e0f3aff2be63d916f734afa8288145fbb61966419df.json` | 5,740 | `81abd07bf9ce52e72a6745b8abfbccda8d09f7c178335e19b41e096dd2fd796a` |
| `states/r6state_3ef41313cfc78f2312e096aca2e1ea6a92f7b52ec6e7e87aa92658c5f67a1f51.json` | 6,055 | `a3b9cd882628c00d42acf1f14d0b79870b483560cfca5c4fc157141a77a10fe6` |
| `states/r6state_45dedbd9e904d130d27e5dee523df6a9f2315e90a0dcc826741302ed0c15b6b0.json` | 6,055 | `39b061f866588c744fc03c85f8f0a45abb19a46529d97e2e92f6aaf1a596cc8a` |
| `states/r6state_48a44088f3c478da16497c48de7f851c169d6acd07705e9e28df34c4cde16f2c.json` | 6,055 | `1b44f146c6cb48d3d196f192b8faf92862398de3a76538e30205316f26808d7b` |
| `states/r6state_499d7d8c2ad3acea815d52a53da38b60385835d7b20f0d81c37c69e0dfe65d5e.json` | 5,773 | `7f3928feae0286bd13fcc10cef7ec7d071eec46903849f6021bce6f627539552` |
| `states/r6state_586282968a6ac743ee683b8b181e136105924387054c59959e59c911b49297a7.json` | 5,742 | `fdc3f4129fff90f4866785c900580c00624bdd17c59bfb6d1ced16ddd88870c6` |
| `states/r6state_61c193dbdfe17341629de15c55f82e70f9b32a4e674754b9af60c51f079aa836.json` | 6,066 | `7928c8ecbbdb79dd32c590882dae46e1472d57ee4a9079e7a02c62bd2f9f8379` |
| `states/r6state_6cb40af207254f966c37999f097054a9a4f3ce65e5d2b9d987b336add996acc9.json` | 6,060 | `11588dc75f0ac7ada563140c3863f1b2bfbbc33459a9246ca989cda801f13f56` |
| `states/r6state_6df752b76c01676455c81246287f5fde7fe34bdde6e5e63a6d9fcf2d5e19f290.json` | 6,062 | `d4245a7487f5d53c9aae11e1c0428f88d7bd1461a0f8410b5457d562a9b10dbb` |
| `states/r6state_84e997b0a6e3a7faefe2c05838c3d93fc129aef7017000ef520145063c1b29c0.json` | 6,067 | `b0127a646d63970e528166c2093b56db09ba64f6b625fe40ab72332af5fe6232` |
| `states/r6state_863b02e24d7b8c496d81faaaacd94889319572affc96a915c6c8cf3a4c48f1fe.json` | 6,067 | `d2425f44e22370552292cc58ed1372c06db793696f1a5e0b811cc99e92a3b0e8` |
| `states/r6state_938ba16d98c1236472511693641b8635decc8a46890c7aaa887d79fbfabedadf.json` | 6,055 | `a8795bfabd03b06f97719e4f6fc6519089c89f695e91b12d2534a753ddb36b3c` |
| `states/r6state_9505fcfb16a4225c3afe9dc736931fb639896e506442dc381b613270df5c471b.json` | 6,066 | `6cbbc7289e63cb4d2562adbb6aaaf41982f5cf2efbf5d3b697ea4d7f2fb7b89a` |
| `states/r6state_b134ef3c67b69d3180dab5962dbfee94e4ef7d8b38efab6f73c75b178e41fdcf.json` | 5,759 | `dc46c1c400c041395db016cbbf3a0e21a09137990a83beac93735aeb29a8e0dc` |
| `states/r6state_bea7c11b1b605f21c71d75d7238b90c34fb54d827f91a48d403fec609a95b44d.json` | 6,058 | `92977d372674da939505a6980faa91e3b889d1fb7d4d109a06b74673445a6917` |
| `states/r6state_d53e86c155f5237ec590c6488bd7655e1e17765e75aaacf806a3b3bdc51e05aa.json` | 6,058 | `2707abf05096086367170313df7831a24d297ab5bddbd21abe99e19775169031` |
| `states/r6state_da4aec2ef7da958383c6a4e42f335c3dd2cd6806d7759baf5d20e1b97389add8.json` | 5,759 | `de1a3af0e3d03b27653f3e19bfc2a422555995e03fb24dfa8ac03141cb479d0f` |
| `states/r6state_e0c4510dd04ab737a457e40cd8505c0b3f8bd880d61b291de5305ef9406bbcaa.json` | 6,062 | `fe7148931385193a16ea1bcc223ae796aa12328dfc5728f8109d9a00094ca73e` |
| `states/r6state_e9a29b7a9474d8425f624c60045bf4e01e6def7aaaa5c9284e12f292b10c0175.json` | 6,062 | `8687661f115441a1bc79d1d9d66e888f47d6ebe32d57cca49e3b0f916cdb446f` |
| `states/r6state_f16a0664bd90ad0749b5767018ab2f1f11332ec4978a99165dfbcda958e41529.json` | 6,060 | `93984e990d2c085e90f912a15753557b623a4221f99a5716d5d468fde2d5922c` |

### Fair-reported execution and semantic results

The transferred result JSON records the final decision, `history_store.created=true`, `registration=TRANSACTION_COMMITTED_AND_READBACK_VERIFIED`, `queries_executed=true`, 26 observed-state readbacks, two provenance records, 33 store files and 163,086 store bytes. It reports four exact-query samples with latencies from 88,782,369 to 89,818,730 ns. It records `MISSING_TIMESTAMP`, `OUTSIDE_SUPPORT` for a missing support selector, and `CONFLICT` for an ambiguous query without a cell selector. These are Fair-reported outcomes preserved in the transferred record; Windows did not replay the Fair API operation.

The operator reports the Linux hard-link probe passed, the B0 regression suite had 85 passes, and the real INT-2B adapter exited 0. No Fair log was included in the imported bundle, so Windows cannot independently recalculate the hashes of those logs; those three execution facts remain operator-reported. The imported result itself has matching current Windows byte count and SHA256, but its `limitations` array still contains the stale token `NO_B0_STORE_QUERY_PASS`, contradicting its own successful store/query fields and decision. This inconsistency is disclosed and the original JSON is left unchanged; the outcome is recorded as Fair-reported and bounded by the verified imported artifacts, not as an independently repeated Fair run.

The JSON also says the filesystem volume is `NTFS`. The source adapter at the Fair-tested commit used a hardcoded `NTFS` label. Therefore the hard-link probe PASS is reported, but the actual Fair filesystem type is `UNKNOWN`. The adapter has now been corrected to detect the filesystem at runtime for future executions, with a focused regression; this code change does not rewrite or reclassify the historical Fair result. On Windows, the default project Python 3.12.10 initially could not collect the focused test because NumPy was absent. Using the already-installed pytest 8.4.2 from that environment and NumPy 2.3.5 from the existing Codex workspace Python dependency path (no installation or environment mutation), the full INT-2B adapter module completed with 7 passed and 1 skipped. `py_compile`, `git diff --check`, UTF-8/LF checks and a direct smoke test of the filesystem helper also passed. The single skip is the real `HistoryStore` integration test gated by the observed Windows hard-link denial.

The two registered source bundles remain R4 manifest `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236` and INT-1D manifest `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`. Persisted observations remain distinct from INT-2A diagnostic interpolation and from executable physical replay. The four candidate checkpoints deserialize only as reduced states; executable replay remains unqualified. No canonical `WORLD_HISTORY` access/publication or scientific promotion is claimed.

---

Date: 2026-10-14
Checkout: `r6/si1-bandwidth-f2av`, HEAD `a2e3fd8608e7a736bc4aa06073be982b4a6cfd55`
Decision: `INT2B_BLOCKED_STORE_ATOMIC_PUBLICATION_UNAVAILABLE`

## Scope

This work validates the existing R4 and INT-1D noncanonical bundles, maps their observed rows into existing B0 typed records, and attempts the required isolated `HistoryStore` write/query path. It does not access or modify canonical `WORLD_HISTORY`, execute a provider-backed trajectory, or qualify physical authority or executable replay.

The bundle loader reused from INT-2A verified the pinned nine-file membership, member sizes and SHA256 values, run/result/sample cross-references, support identities, and provenance for both input bundles. The inputs remained unchanged. The pinned manifest identities are R4 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236` and INT-1D `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`.

## B0 mapping implemented

`scripts/r6_int2b_history_adapter.py` builds a `ProvenanceRecord` per experiment and a `DomainStateEnvelope` per verified observed sample. The output records comprise 8 R4 states (4 samples × 2 supports), 18 INT-1D states (9 × 2), and 2 provenance records. Each state carries its source experiment, manifest/run/sample digests, source commit and source-composite identity, provider digest references, boundary, exact support cell, resolution rung, stored engineering elapsed time, field values and units. Time keys preserve the exact parsed floating-point observation with `repr`; they are not rounded or converted to geological time keys.

R4 and INT-1D receive distinct deterministic `HistoryId` and `BranchId` values. The B0 classification is `SupportClass.DERIVED_SUPPORTED` with `AuthorityClass.NONE`; applicability explicitly says noncanonical engineering observation, physical/geographic authority not claimed, and canonical publication false. Uncertainty remains `UNKNOWN_NOT_REPORTED_BY_SOURCE`. The adapter rejects reconstructed rows and mismatched source/support identities. It reuses `HistoryStore.append_transaction()` and `HistoryQueryService.state_at()` if the filesystem capability precondition succeeds; it does not implement a second store or query path.

## Filesystem capability and blocked store test

The bounded probe ran in a new disposable directory on the intended F: NTFS volume. File creation and probe-byte readback worked. Creating a same-directory hard link with `os.link` failed with `PermissionError: [WinError 5] Accesso negato`; probe-created names were removed and the directory was empty afterward. The adapter repeated the actual probe in the new INT-2B output directory and recorded the same failure. It therefore did not instantiate `HistoryStore`, register records, or execute queries. No monkeypatch or relaxation of B0 atomic publication was used.

The focused INT-2B suite result was **6 passed, 1 skipped, 0 failed**. The skipped test is the actual B0 registration/readback/query integration test, skipped only after the hard-link capability probe failed. Related INT-2A/B0 regressions produced **16 passed, 9 failed**; all nine failures occurred while the existing `HistoryStore` tried to install its initial immutable manifest through `os.link`, before query assertions. These are Windows filesystem-environment failures, not evidence that the B0 store/query path passed or that the B0 implementation is defective. `py_compile` and `git diff --check` passed.

Windows reports the target volume as NTFS; same-volume format alone does not establish that the current managed process token can create hard links. WSL is installed but listing/running the configured distribution was denied (`Wsl/E_ACCESSDENIED`), so it was not an available local POSIX test environment. The repository procedure records a pre-existing Fair Conda environment `arcana-r6-linux`, where prior compiler-fixture work was run. That is a candidate environment for a later bounded B0 test after code publication and fetch; no B0 store/query test was run there in this gate, and prior compiler tests do not qualify B0 storage.

## Result bundle

New disposable result directory: `outputs/r6_functional_development/INT2B_B0_BINDING_20261014_01/`.

| File | Bytes | SHA256 |
|---|---:|---|
| `INT2B_B0_BINDING_RESULT.json` | 4,284 | `b11a6d1b057a1676f8da6afb6598a682a9f7255458a37055866f3e481d33006f` |
| `INT2B_OUTPUT_MANIFEST.json` | 553 | `b85216bafd82836f72a0720ef970c84137e5d98acc0092256ca8c562d9290440` |
| `INT2B_OUTPUT_MANIFEST.json.sha256` | 93 | `9b4c497b4bd8f7acd2060cdcd262d623201c23d79d33876f4c1c55a5480a83e1` |

The manifest binds the result JSON size/digest and both source manifest identities; the sidecar matches the manifest digest. The result records the planned 26 states and 2 provenance records, but reports `history_store.created=false`, `queries_executed=false`, and no store-byte or query-latency measurement. It is therefore not a B0 registration/query PASS.

The four existing candidate checkpoint payloads (two per bundle) successfully deserialize through the existing `state_from_payload()` into reduced states. They are not complete registered B0 checkpoint envelopes and do not bind a closed runner/configuration, forcing, and deterministic engine adapter. This proves payload deserialization only; executable replay remains unqualified.

## Validation and next step

Observed bundle-to-B0-record construction and reduced-state deserialization are verified offline. Store immutability, transactional publication, exact readback, query outcomes, store bytes, and latency remain untested because the required hard-link operation is denied on this Windows filesystem. Continue with the same isolated-store tests in an already qualified Linux environment after ordinary code publication/fetch, preserving these Windows results and output bundle. Do not change `HistoryStore` atomic-write semantics to bypass the environment restriction.

The scientific gates remain unchanged: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

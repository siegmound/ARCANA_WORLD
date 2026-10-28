# R6-INT10K E0 — Windows source-loader qualification and sealed transfer bundle (2026-10-28)

**Decision:** `R6_INT10K_E0_WINDOWS_LOADER_PASS__TRANSFER_BUNDLE_SEALED__FAIR_IDENTITY_PENDING`  
**Qualification:** `WINDOWS_SEMANTIC_LOADER_PASS_OPERATOR_REPORTED`; FAIR byte/source-loader identity remains `PENDING`.  
**Original data scope:** `NONCANONICAL_SYNTHETIC_LAYERED_CONTINUUM_ENGINEERING_EXPERIMENT`. No numerical evolution run or production authorization.

## Windows original and loader evidence

- Exact input directory: `F:/corsiiiuu/Magistrale/Arcana/ArcanaWorld/ARCANA_WORLD_R6_UBUNTU_PORT/ARCANA_WORLD_R6_BW0/outputs/r6_experimental_multiphysics/MATERIAL_RHEOLOGY_PROVIDER_20261025_03`.
- Windows git HEAD where the operator ran the loader: `3c566ea61c79b8dad96274a5d68d845704aeae96`; source-data origin separately preserved: `ec79bf8954a4922f84249fbe23e2657bc5beee23` on `r6/si1-bandwidth-f2av`. Do **not** confuse origin with current code checkout.
- `RESULT.json` SHA256 `24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5`.
- `MANIFEST.json` SHA256 `a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21`.
- `RESULT.json.sha256` *file* SHA256 `8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0`.
- Original `load_verified_r6_initial_columns`: `LOADER=PASS`, Python exit `0`. Loaded module `src/arcana_worldsim/r6/geological_surface_microdomain.py` SHA256 `612d59415e25909a593914d627ea40253d44c3e352039a765c717879793d23fa`. The loader validates manifest sidecar sizes/digests, exact R6 73-node initial states and topological binding.
- Supports `R6G1D-R091-C028` (cell [91,28], plate 11) and `R6G1D-R091-C029` (cell [91,29], plate 5); `time_s=0`, 73 nodes each. Both initial state digests are `2507efbde9b9e98dccfc9e4cd7bb0eac59a7307b8adcc91955e7a5feb10914ec`: **identical initial profiles by payload SHA**. This does not prevent engineering tests but must not be misinterpreted as evidence of independent spatial material heterogeneity.
- Boundary `R6BND-T0-3eb57747e6f0a3f3305f`; positive finite length `111194.92664455874` m; ordered plate pair [5,11], `GEOMETRIC_SHARED_INTERFACE`; vector-partition payload SHA256 `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`.
- Source result identity `6e729d3662af349b10c85d54f964513270b7e32595ba0f160fa442996348a8fe`; ENG10K original archive SHA256 `7dda60c8fa1f535d9e257eb2d04fdfde4643a92765eca8631bd766058240d8cb`.

## Sealed original transfer package

The operator-created Windows bundle `F:/corsiiiuu/Magistrale/Arcana/INT10K_E0_WINDOWS_TRANSFER_20261028/MATERIAL_RHEOLOGY_PROVIDER_20261025_03.tar.gz` SHA256 `fc5cda6e543f5f96673ba71e60c085566659672abff9728eb5ed74c2ab47c8b0`. Bundle made only after original-hash and original-loader PASS, with three original files as archive root members. The Windows report `WINDOWS_INPUT_PREFLIGHT.json` and sidecar `BUNDLE.sha256` are external local artifacts, not independently uploaded or rehashed in this ledger update. The reported bundle digest is not a proof that FAIR has received it.

## Exact next admissible step: FAIR read-only verification

1. Transfer the bundle via operator-approved SSH/SCP/SFTP to a **new** external FAIR evidence directory, never to or over the stale `ARCANA_WORLD_F2AV` checkout or any GEODYN-3C/ENG10K prior evidence.
2. On FAIR verify tarball SHA256 exactly `fc5cda6e543f5f96673ba71e60c085566659672abff9728eb5ed74c2ab47c8b0`. Before extraction require exactly three unique basename-only regular-file entries with the expected names, no links, traversal or special members; extract to a fresh directory; verify each file SHA256 against this report.
3. Pin the **same original Windows loader bytes** via `git show 3c566ea61c79b8dad96274a5d68d845704aeae96:src/arcana_worldsim/r6/geological_surface_microdomain.py`, compare extracted module SHA256 `612d59415e25909a593914d627ea40253d44c3e352039a765c717879793d23fa`; execute this module isolated via Python 3.12 importlib against the extracted three files, without moving HEAD/index/worktree. Compare entire source_identity object to the Windows-recorded JSON (`docs/arcana/qualifications/R6_INT10K_E0_WINDOWS_INPUT_OPERATOR_REPORT.json`) and support SHA, not just a loose string status. Any difference ⇒ `BLOCKED` and preserve evidence.
4. The pinned module verification establishes only loader/input equivalence; the new integration runner source must be separately pinned to a reviewed commit and qualified with its own tests. This is **not** E1/E2/E3/E4 numerical execution.

## Important interpretation

- Source-data `source_head=ec79bf89…` is historical origin; loader-code `HEAD=3c566ea6…` is another provenance; current R6 documentation HEAD is newer. This is normal **if all bytes and recorded identities agree**.
- Identical C028/C029 T0 states are a *scientific representativeness gap* even if the actual harness tests are numerically reproducible.
- The Windows `_01` and `_02` candidates remain separate historical data. No retroactive rewrite of earlier FAIR or ENG10K results.
- Parallel physical/environmental provider gap matrix remains OPEN.
- `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`.

See the exact [machine-readable Windows source identity report](qualifications/R6_INT10K_E0_WINDOWS_INPUT_OPERATOR_REPORT.json).

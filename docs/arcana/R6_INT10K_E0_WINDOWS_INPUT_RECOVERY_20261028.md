# R6-INT10K E0 — Windows original material/rheology input discovery (2026-10-28)

**Decision:** `R6_INT10K_E0_WINDOWS_INPUT_TRIADS_FOUND__MANIFEST_SIDECAR_PASS__LOADER_FAIR_PENDING`. **Authority:** `OPERATOR_REPORTED_WINDOWS_HASH_CHECKS`. Source code inspected at `a811e4bb67b14dec5fac9a975475ab7e5e5e62e5`; the original source files have not been independently uploaded or rehashed here.

## Windows observations

The operator found 3 distinct directories under `F:/corsiiiuu/Magistrale/Arcana/ArcanaWorld/ARCANA_WORLD_R6_UBUNTU_PORT/ARCANA_WORLD_R6_BW0/outputs/r6_experimental_multiphysics`. Each contains `RESULT.json`, `MANIFEST.json` and `RESULT.json.sha256`. The operator's PowerShell diagnostic compared the manifest result/sidecar hash entries, manifest schema and the exact ASCII sidecar content; all three were reported PASS. This diagnostic did not explicitly check manifest byte-length fields, R6 T0 hashes, 73-node state structures or the boundary binding enforced by the source loader.

| Candidate | RESULT.json SHA256 | MANIFEST.json SHA256 | RESULT.json.sha256 SHA256 | Manifest+sidecar |
|---|---|---|---|---|
| MATERIAL_RHEOLOGY_PROVIDER_20261025_01 | `d6bc25acada380e296d34a42c036e14d0168f06b9985ad9ad23c8ec2badabdb8` | `d72e4ef8870d21979a690d7a90ac367a92ef2b5521bf1a6bc28968b80ec1d2df` | `0722c4a449d4aab5d119fd3a0a0ccba4508b12bebdd35abe1b8714d5fb316608` | PASS (reported) |
| MATERIAL_RHEOLOGY_PROVIDER_20261025_02 | `64d7468a97561ec4b7e8afa200e71db8e778c007a65dff44967d3851a3c40613` | `f467f4db957aad8c25248ef41e6645f3f96638ad81c789982b0c65c43b0b8a17` | `8d593e38b9494fc90e136082f3b2f33b16727e15c6bbbbc28433505a1cf9453d` | PASS (reported) |
| MATERIAL_RHEOLOGY_PROVIDER_20261025_03 | `24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5` | `a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21` | `8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0` | PASS (reported) |

**Selected next validation target:** `MATERIAL_RHEOLOGY_PROVIDER_20261025_03` because the regional and unified runners explicitly use this path by default. The earlier `_01` and `_02` remain distinct and must not be overwritten or substituted. The original `F:/corsiiiuu/Magistrale/Arcana/ENG10K_LUNA_ANALYSIS/ENG10K_ARCHIVE_ec79bf89_01.tar.gz` has reported SHA256 `7dda60c8fa1f535d9e257eb2d04fdfde4643a92765eca8631bd766058240d8cb`, exactly matching the `ARCHIVE_SHA256` constant in the integrated microdomain source; this verifies an expected byte identity *by operator report*, not scientifically authenticated provenance.

## Next exact test and transfer

1. On Windows run the **original** `load_verified_r6_initial_columns` on the exact `_03` directory, recording Python and local module identity, validating the three hashes against this table, the manifest byte lengths and the `UNCoupled_reference` case. Loader must accept the two 73-node `R6G1D-R091-C028/C029` T0 columns, grid [91,28]/[91,29], plate pair [5,11], `GEOMETRIC_SHARED_INTERFACE`, original support-state hash and positive finite boundary length.
2. Only on loader PASS, prepare a new external, immutable transfer package containing the three exact source bytes. Record SHA256 for the package plus the original three members. Do not copy one version over another.
3. Transfer to a **new** FAIR evidence staging directory through approved SSH/SCP/SFTP process. Verify package SHA256 and all three extracted SHA256 again. Execute the same original loader from **exact pinned R6 source** in an isolated source tree, not from stale F2AV checkout; compare returned source identity JSON Windows vs FAIR. Neither operation authorizes the engine to run.
4. After E0 input/host qualification, implement the new compact-streaming runner, verify 3-year/10-year parity and separately authorize bounded 10→100→1000→10000-year engineering stages based on measured resources and conservation.

**Boundary:** triad manifest/sidecar PASS is not semantic loader PASS, FAIR transfer PASS, geodynamic validation or a simulation result. The parallel scientific provider gap matrix and prior ENG10K/GEODYN-3C records remain unchanged. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`.

# ARCANA R6 local work consolidation — 2026-10-26

## Repository and publication

The source worktree remains at `ec79bf8954a4922f84249fbe23e2657bc5beee23` and was not modified during reconciliation. The remote branch advanced by the single child commit `ed0140ea962315f8993c1adfceeef23855f93b8b` (`docs(ledger): record ENG10K closure and prototype-first multiphysics roadmap`). Integration was prepared in a separate worktree based on that remote HEAD. The fetched commit's eight ledger updates were retained as the starting point; no reset, rebase, stash, clean, or force operation was used. The implementation commit is `d723f9d160e1e90cdb679a68ab9ac2596c6b9a6d`; the VIEW commit is `ec4c8264c7440def7e4da7a88ecd4b06a10169ef`.

The original local worktree and untracked files were copied to the external recovery directory `ARCANA_R6_CONSOLIDATION_BACKUP_20261025_01` before integration. The backup manifest records 2,818 copied files (111,942,461 bytes), source paths, sizes and SHA256; every copied file was rehashed against its source. The original worktree, outputs, and ignored caches remain preserved. This report records that the local changes were integrated into a new descendant branch; it does not claim that the original worktree itself became clean.

## Consolidated local code and tests

The integration candidate includes the incremental segment-archive hashing/readback change in `scripts/r6_int3_eng10k.py`, the optional verified B5-source reuse path in `functional_spatial_support.py`, and its regression. It also includes the local segment-continuation, tectonic/Deep, constitutive, surface, hydrology, integrated microdomain and regional-evolution prototypes with their focused tests. These are bounded engineering components; their synthetic inputs and unsupported physical couplings remain explicit.

The focused Windows suite used Python 3.12.10 with NumPy 2.5.1: **134 passed, 6 skipped, 2 deselected**. The two deselected functional-spatial tests require the governed canonical provider payload; `ARCANA_EXTERNAL_ROOT` was unset, and the attempted provider-backed collection reported `KinematicsAuthorityError: governed payload unavailable: CANONICAL_T0_PHYSICAL_PAYLOAD`. These tests were not replaced with fixtures and are not reported as passing. Skips are recorded as skips, not passes. `compileall` passed for `scripts`, `src/arcana_worldsim/r6`, and `tests`.

The VIEW-only viewer suite passed **16/16** tests and `npm run typecheck` passed. No viewer build was run, so existing generated `dist` files were not rewritten. Only nonignored source, tests, static display exports and their bounded evidence are included; dependency trees, local tool caches and generated build output are excluded.

## Numerical and artifact evidence preserved outside Git

No files under `outputs/` were added to the source commit. Existing output bundles remain local, immutable evidence. Their checked results include:

- Segment continuation `_01`: manifest SHA256 `55ce95c85de39fb5d1ecb75c756da8cfd573d7f69afaa52c871de81a3f69bdf3`; result SHA256 `c4784216fde8085fab017d9d6e61b29fe6b4488c771064714e2218b13b2d7e9b`.
- Segment continuation `_02`: manifest SHA256 `130549b01f093924c3452efb45d84696d8159dbd985b8f7eb74a32b2b2c29f50`; result SHA256 `1b391f73b5263eb806d49d76a47f681471e044c319195d8c5b93950bfa9c3a01`.
- Segment continuation `_03`: manifest SHA256 `51736a4500d4526d4f05127916b8daeec67d257380b835334efc8aa442a293ba`; result SHA256 `294abba6382bbc4d3b1c339dff513412f1b2a1b1044c1d77334332285c649fff`. The continuous and restarted final checkpoint state hashes agree (`5ae328a04bf532abbf6a74a73f3206c32e2f68c66f4c111d80614a2469e39032`). This is prototype continuation evidence, not a qualification of raw ENG10K archive records as restartable checkpoints.
- Regional evolution V2 manifests and all listed members were independently rehashed locally. The synthetic 3×3 case changed routing from C04 sink to C07 after erosion/deposition; no uplift was imposed and this is not a geological event claim. Water and Deep balance residuals were zero. Solid-mass residual was `-0.00048828125 kg` against the bundle's `0.03125 kg` tolerance. The regional outputs remain untracked under `outputs/`.
- The D3D-RO6 recovery attestation is published as a bounded report only. Its source JSON was locally checked at 4,133 bytes, SHA256 `320344b6cfb74042e450bac4347f5a8b820e5702fa4b15c3bf4ff240ec764ec0`; the original transferred evidence bundle is not copied into this code repository.

The multiphysics prototypes include synthetic Deep modal parameters and experimental constitutive/hydrologic laws. The ASPECT-style dry-olivine adapter is a benchmark constitutive law only: no ASPECT PDE solver was integrated or executed. T0 B5 kinematics remain diagnostic, not positive-duration forcing. Vertical response, historical material/climate inputs, and global spatial mapping remain unresolved.

## Scope and authority

The consolidation does not promote engineering outputs to scientific qualification or canonical history. Preserve `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. No Fair/Linux qualification is claimed for code tested only on Windows. Historical FAIR reports not imported to this machine remain operator-reported with their original provenance and scope.

## Next bounded R6 activity

After synchronization, define the smallest executable geodynamic forward-driver experiment supported by actual time-dependent inputs and boundary conditions. First resolve the positive-duration forcing, material/reology and spatial-support gaps using existing repository contracts. Treat ASPECT as a candidate reference, not an integrated solver; do not start a long historical run or assign benchmark parameters to ARCANA materials without evidence.

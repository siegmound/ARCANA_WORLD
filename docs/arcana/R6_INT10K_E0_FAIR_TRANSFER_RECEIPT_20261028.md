# R6-INT10K E0 — Windows-to-FAIR bundle transfer SHA receipt (2026-10-28)

**Decision:** `R6_INT10K_E0_FAIR_TRANSFER_SHA256_PASS__MEMBERS_AND_LOADER_PENDING`  
**Evidence level:** `PASS_OPERATOR_REPORTED_SHA256_TRANSFER`, based on terminal output from FAIR. **Not a semantic-loader PASS.**  
**Windows qualification:** `docs/arcana/qualifications/R6_INT10K_E0_WINDOWS_INPUT_OPERATOR_REPORT.json` at `d0d5b02c0ec922add32ff881433b429b47f66540`.

## Operator-reported FAIR transfer output

Location: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E0_WINDOWS_TRANSFER_20261028_01`.

- `BUNDLE.sha256` transferred, listed at 113 bytes.
- `MATERIAL_RHEOLOGY_PROVIDER_20261025_03.tar.gz` transferred, listed as 111 KiB.
- `WINDOWS_INPUT_PREFLIGHT.json` transferred, listed as 2.4 KiB.
- On FAIR, `sha256sum -c BUNDLE.sha256` returned `MATERIAL_RHEOLOGY_PROVIDER_20261025_03.tar.gz: OK`.
- On FAIR, a second SHA256 check against **the known original Windows digest** `fc5cda6e543f5f96673ba71e60c085566659672abff9728eb5ed74c2ab47c8b0` also returned `MATERIAL_RHEOLOGY_PROVIDER_20261025_03.tar.gz: OK`.
- These two checks establish an **identical tarball digest** relative to the Windows-created bundle. They are not independent measurements of member hashes or semantic state validity. Both use SHA256.
- No tar extraction, member byte comparison, loader execution, numerical model execution, full FAIR evidence import or full input identity comparison is yet claimed.
- The destination is outside the stale linked checkout; original FAIR source checkout was not touched by these checksum commands. No post-transfer `git status` or source tree integrity result is claimed from this output.

## Next required validation

Read-only acquisition of pinned Git source objects and Windows attestation. Inspect tar member inventory **before extraction**, requiring exactly three unique root-level regular files, no links, traversal, specials or unexpectedly large expansion. Extract to a **new external** staging subdirectory, verify original member SHA256:
- `RESULT.json`: `24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5`.
- `MANIFEST.json`: `a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21`.
- `RESULT.json.sha256`: `8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0`.

Pin original loader from source commit `3c566ea61c79b8dad96274a5d68d845704aeae96` and compare its module SHA256 with Windows `612d59415e25909a593914d627ea40253d44c3e352039a765c717879793d23fa`. Use `load_verified_r6_initial_columns` against verified extracted triad and compare full `source_identity` and the two 73-node support state hashes to the operator-reported Windows JSON. Require existing checkout HEAD+tracked worktree unchanged. Only if all checks pass write a new separate FAIR qualification record; never revise Windows report in place.

Scientific boundary: source identity `ec79bf89...` is original material origin, not current loader code provenance; identical initial C028/C029 payload hashes remain a representativeness gap. Benchmark 10k engineering execution, physical provider calibration and canonical WORLD_HISTORY production remain unauthorized. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`, `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`. Do not reinterpret earlier ENG10K or GEODYN-3C runs.

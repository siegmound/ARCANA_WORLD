# GEODYN-3C — FAIR experimental archive qualification handoff

**Date:** 2026-10-27
**Branch:** `r6/multiphysics-integration-20261026`
**GEODYN-3B baseline:** `e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa`
**Parent:** `0256458553f5ee856739cd0abff7561d90ad1198`
**Status:** `GEODYN_3C_FAIR_QUALIFICATION_PREPARED__NOT_EXECUTED`

## Scope

This package prepares a read-only qualification of the existing GEODYN-2A-R1 rigid-shear PVD/PVTU/VTU files. It does not run ASPECT, MPI, an ARCANA forward model, or any canonical operation. It has not been executed on FAIR; this document makes no FAIR PASS claim. The source bundle, independent numeric audit, and prior adapter evidence remain at their previously reported locations and are not represented as locally rehashed evidence.

Authoritative implementation/API references are [the ratified GEODYN-3A contract](GEODYN_3A_EXPERIMENTAL_TRAJECTORY_ARCHIVE_CONTRACT.md), [the GEODYN-3B MVP report](GEODYN_3B_EXPERIMENTAL_TRAJECTORY_ARCHIVE_MVP.md), `src/arcana_worldsim/r6/experimental_trajectory_archive.py`, and `src/arcana_worldsim/r6/adapters/aspect_snapshot_reader.py`.

## FAIR handoff script

Script: `scripts/r6_geodyn3c_fair_qualification.sh`. It uses only the APIs actually implemented: `RunIdentityClaim`, `SourceDigest`, `index_existing_aspect_series`, `ExperimentalTrajectoryArchive.open`, `verify_integrity`, metadata/query methods, `get_snapshot`, and `get_field`, plus `AspectSnapshotSeries.audit/read_snapshot`.

Transfer this reviewed script outside the FAIR checkout (for example to a controlled temporary location), verify its SHA256 from the Windows handoff, and invoke it there. This avoids adding an untracked file to the existing checkout. After finalizing the R1 repair commit, set `GEODYN3C_EXPECTED_COMMIT` to that exact full SHA-1 before invocation:

```bash
GEODYN3C_EXPECTED_COMMIT='<R1 full commit SHA>' bash /path/outside/checkout/r6_geodyn3c_fair_qualification.sh \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2_RIGID_SHEAR/20261026T234423Z_transient_rank1 \
  '<PVD relative path, identified in that directory>' \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2C_NUMERIC_AUDIT/20261027T000139Z_numeric_audit/NUMERIC_AUDIT.json \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2A_R1_FAIR_QUALIFICATION/20261027T105033Z_exact_commit/SOURCE_INVENTORY.json \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2A_R1_FAIR_QUALIFICATION/20261027T105033Z_exact_commit/RUN_IDENTITY_CLAIMS.json \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
```

`SOURCE_INVENTORY.json` and `RUN_IDENTITY_CLAIMS.json` above are required input schemas for the handoff, **not assertions that files with those names are already present in the historical evidence directory**. Before invoking, inspect the existing qualification evidence and supply equivalent files from its preserved records. Do not fabricate them. The source inventory schema is `{"files":[{"relative_ref":"...","byte_length":N,"sha256":"<64 lowercase hex>"}, ...]}` and must cover exactly the PVD-referenced source files. The claims file schema is `{"run_identity":{...RunIdentityClaim fields...}}`; required values must come from the prior run/evidence record. Preserve the exact IDs in `solver_source_commit` (ASPECT `30eb77ee5da186137d436dbad35c6cb3cab64b69`), `repository_commit` (GEODYN-2A-R1 `1fd5e8d8f21e28876da9ef89423755615efc6162`), and `adapter_commit` (the exact GEODYN-3B implementation commit supplied via `GEODYN3C_EXPECTED_COMMIT`). Declare their algorithms in the three string fields `declared_provenance.solver_source_commit_algorithm`, `declared_provenance.repository_commit_algorithm`, and `declared_provenance.adapter_commit_algorithm` (each `sha1`); this remains caller-supplied unauthenticated metadata. The archive validates syntax and preserves exact strings; length does not authenticate a commit. `configuration_sha256` and every `input_identities` entry still require exact 64-character lowercase SHA256 values recovered from the original records. The time-unit source and original attempt token must also come from evidence. If any inventory, claim or digest cannot be established, stop before the script; the result is BLOCKED.

The script refuses a different branch, HEAD, parent, staged index, or tracked dirty checkout. It creates a new evidence directory below the supplied pre-existing evidence parent, copies and hashes the exact launcher used, extracts exactly the committed source with `git archive`, and runs the two focused test modules from that extraction. The committed script requires the exact Linux test count recorded in `EXPECTED_TESTS` and zero skips; any nonzero exit, count mismatch, or skip stops qualification. It does not install packages, require root, change the existing FAIR worktree, or write to the ASPECT source tree. Its generated archive index and all negative mutations are isolated under the new evidence directory.

If the PVD filename/location or the historical inventory/claim files differ from the example, pass the actual relative PVD reference and exact existing evidence paths as arguments. Do not select a guessed PVD or use a newly calculated inventory as if it were an independently preserved historical digest. The script prehashes every declared original, the indexer independently hashes the PVD-referenced files, and the script rehashes the same originals afterward; pre/post mismatch is FAIL. These checks establish byte preservation during this qualification, not source authorship.

## Qualification performed by the script

1. Verifies branch, full HEAD, parent, commit object, clean tracked/index state, and captures tracked worktree status before/after. Extracts source via `git archive`; it never checks out or edits the existing worktree.
2. Runs the archive and adapter test modules from the extracted commit and requires all tests to pass with no skips.
3. Builds a new metadata-only index with the externally supplied source inventory and claims. The original PVD/PVTU/VTU files remain in place; numeric arrays are not copied into the index.
4. Requires 11 strictly increasing native times from 0 through 1.0142299266 s, a stable 1152-point/512-cell single quadrilateral mesh, nine point fields, and the separate 1.098612289 s solver-completion time. It asserts `SYNTHETIC_ENGINEERING_ONLY`, unauthenticated provenance, `restart=NOT_AVAILABLE`, and `reconstruction=NOT_CLAIMED`.
5. Exercises exact-time, inclusive interval, mesh/field catalog and on-demand snapshot/field queries. A query at solver completion and a point in the unarchived tail must return `MISSING_SNAPSHOT`; no interpolation or synthesized terminal state is accepted.
6. Compares per-time, per-field typed numeric `sha256_bytes` values with the independent audit. The audit parser accepts only explicit snapshot records (`snapshots`, `snapshot_audits`, or `snapshot_records`), native time keys (`time`, `time_value`, `timestep`, or `time_s`), and named field SHA256 records under `fields`/`field_arrays`. Unknown or ambiguous audit structure fails closed. It does not compare mesh fingerprints from different algorithms; mesh verification uses the adapter's numeric dimensions, stable identity, and the independent audit's field values.
7. Tests incomplete-index status, missing payload status, altered payload on an isolated copy, external symlink rejection, traversal rejection, output collision preservation, invalid sealed-manifest rejection, and archive relocation. Relocation must preserve `archive_id`; payload resolution becomes available only after explicitly supplying the source-root mapping.
8. Records pre/post hashes of all original referenced files, source commit/parent, test log and exit code, generated manifest and sidecar, integrity report, query outcomes, per-field numeric comparison, negative checks, and qualification result. A failed phase remains in the new run directory with a nonzero exit and is not overwritten or retried.

Expected evidence root:

`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN3C_<UTC timestamp>/`

Principal outputs include `source.tar` and its digest, extracted commit source, pytest log/exit code, copied input audit/inventory/claims with hashes, `archive_index/manifest.json` and `manifest.sha256`, `INTEGRITY_REPORT.json`, `QUERY_RESULTS.json`, `NUMERIC_COMPARISON.json`, `NEGATIVE_CHECKS.json`, original pre/post hash maps, `QUALIFICATION.json`, launcher exit code and logs. No raw ASPECT outputs are copied by the indexer; negative payload mutation is confined to an isolated copy under this evidence directory.

## Acceptance and failure classification

The script may write `QUALIFICATION.json` with `status=PASS` only after every stated check passes. Any mismatch, unavailable source payload, unknown audit schema, missing identity/inventory evidence, Linux security-test skip, symlink privilege failure, checkout mutation, or query/integrity discrepancy is FAIL/BLOCKED and must be preserved. The final `PASS` would qualify only this read-only index and its comparison against the existing synthetic engineering trajectory. It would not authenticate operator provenance, qualify restart/reconstruction, interpret `T=0`, validate the rigid-shear physics, authorize ARCANA forward evolution, or promote WORLD_HISTORY.

No FAIR command has yet been run for GEODYN-3C. The updated handoff is pending its exact repair commit and recovery of the historical configuration/input hashes, source inventory and attempt metadata. Missing values are BLOCKED, never synthesized. Only after an actual complete PASS could the verdict advance to `GEODYN_3C_EXPERIMENTAL_TRAJECTORY_ARCHIVE_FAIR_VALIDATED__ARCANA_FORWARD_NOT_AUTHORIZED`. The gates remain `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` and `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`.

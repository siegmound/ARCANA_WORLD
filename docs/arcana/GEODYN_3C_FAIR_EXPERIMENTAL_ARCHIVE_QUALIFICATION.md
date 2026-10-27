# GEODYN-3C — FAIR experimental archive qualification handoff

**Date:** 2026-10-27
**Branch:** `r6/multiphysics-integration-20261026`
**GEODYN-3B module origin:** `e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa`
**GEODYN-3B module source revision:** `ab8fad9282b45c30f1df3653ce447cf5e13c6be4`
**R1 repair baseline / parent:** `ab8fad9282b45c30f1df3653ce447cf5e13c6be4`
**R1 local result:** `GEODYN_3C_R1_LAUNCHER_REPAIR_LOCAL_TESTS_PASS__FAIR_PENDING`

## R1 repair addendum — Windows preparation

This addendum supersedes earlier handoff statements that required the FAIR checkout to be on the qualified branch/HEAD, parsed a generalized audit schema, and equated the run's adapter claim with the qualification commit. The repaired launcher verifies the exact remote branch ref, candidate commit object and parent; if needed it fetches the verified object without checking out or moving a branch, then extracts the candidate with `git archive`. It records and rechecks the actual checkout branch, HEAD, tracked status, worktree diff and index diff.

Provenance identities are separate: launcher candidate and its parent are supplied for each R1 run; the archive module originated at e3946... and its latest source revision on the baseline is ab8fad...; the qualified ASPECT reader source is 1fd5... . Historical `RunIdentityClaim` values remain evidence-supplied claims and are not rewritten to the candidate launcher SHA.

The embedded comparison now accepts only GEODYN-2C `snapshots[].point_fields[]` and fails on unknown/incomplete schema. It compares all 99 field hashes and metadata plus all 11 mesh digests using the auditor's numeric serialization order: coordinates, connectivity, offsets, types; for each array, NumPy `dtype.str` bytes followed by C-order data bytes. No digest from a different fingerprint algorithm is compared.

The focused Windows suite completed with 82 passed and 3 skipped: two established symlink-privilege skips and the numeric mesh-digest test because this Python environment has no NumPy. The FAIR launcher requires all 85 Linux tests with zero skips. FAIR Bash syntax validation and real-file qualification have not been run. Recovery of historical inventory/config/input hashes and attempt metadata remains a prerequisite; missing values remain BLOCKED, never fabricated.

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

`SOURCE_INVENTORY.json` and `RUN_IDENTITY_CLAIMS.json` are required input schemas, not claims that files with those names already exist in the historic directory. Recover values from preserved records; never fabricate them. The inventory must cover exactly the PVD-referenced source files. The run's solver/repository/adapter commit values are historical caller claims, distinct from the launcher candidate, its parent, the GEODYN-3B module source revision, and reader provenance. The script records those code identities separately. Git algorithm declarations remain caller-supplied unauthenticated metadata. `configuration_sha256` and every `input_identities` entry require the original exact 64-character SHA256 values. The time-unit source and attempt token must also come from evidence. If any required inventory, claim, or digest is unavailable, stop as BLOCKED.

The repaired script does not require a particular current branch or HEAD. It captures and rechecks the checkout branch, HEAD, tracked status, staged diff, and worktree diff. It verifies the exact remote R6 ref, exact candidate commit object and parent, then uses `git archive`; it never checks out the candidate. The committed script requires 83 Linux tests with zero skips; any nonzero exit, count mismatch, or skip stops qualification.

If the PVD filename/location or the historical inventory/claim files differ from the example, pass the actual relative PVD reference and exact existing evidence paths as arguments. Do not select a guessed PVD or use a newly calculated inventory as if it were an independently preserved historical digest. The script prehashes every declared original, the indexer independently hashes the PVD-referenced files, and the script rehashes the same originals afterward; pre/post mismatch is FAIL. These checks establish byte preservation during this qualification, not source authorship.

## Qualification performed by the script

1. Verifies the remote branch ref, exact candidate commit object, parent, and source-file provenance. It captures checkout identity/state before and after without requiring the checkout to match the candidate.
2. Runs the archive, reader, and qualification helper test modules from the extracted commit and requires all 85 Linux tests to pass with no skips.
3. Builds a new metadata-only index with the externally supplied source inventory and claims. The original PVD/PVTU/VTU files remain in place; numeric arrays are not copied into the index.
4. Requires 11 strictly increasing native times from 0 through 1.0142299266 s, a stable 1152-point/512-cell single quadrilateral mesh, nine point fields, and the separate 1.098612289 s solver-completion time. It asserts `SYNTHETIC_ENGINEERING_ONLY`, unauthenticated provenance, `restart=NOT_AVAILABLE`, and `reconstruction=NOT_CLAIMED`.
5. Exercises exact-time, inclusive interval, mesh/field catalog and on-demand snapshot/field queries. A query at solver completion and a point in the unarchived tail must return `MISSING_SNAPSHOT`; no interpolation or synthesized terminal state is accepted.
6. Parses only GEODYN-2C `snapshots[].point_fields[]` and compares 99 typed field hashes/metadata plus 11 numeric mesh digests. Mesh digest serialization follows the auditor: coordinates, connectivity, offsets, types; each array contributes NumPy `dtype.str` bytes followed by C-order bytes. Unknown/incomplete schema fails closed.
7. Tests incomplete-index status, missing payload status, altered payload on an isolated copy, external symlink rejection, traversal rejection, output collision preservation, invalid sealed-manifest rejection, and archive relocation. Relocation must preserve `archive_id`; payload resolution becomes available only after explicitly supplying the source-root mapping.
8. Records pre/post hashes of all original referenced files, source commit/parent, test log and exit code, generated manifest and sidecar, integrity report, query outcomes, per-field numeric comparison, negative checks, and qualification result. A failed phase remains in the new run directory with a nonzero exit and is not overwritten or retried.

Expected evidence root:

`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN3C_<UTC timestamp>/`

Principal outputs include `source.tar` and its digest, extracted commit source, pytest log/exit code, copied input audit/inventory/claims with hashes, `archive_index/manifest.json` and `manifest.sha256`, `INTEGRITY_REPORT.json`, `QUERY_RESULTS.json`, `NUMERIC_COMPARISON.json`, `NEGATIVE_CHECKS.json`, original pre/post hash maps, `QUALIFICATION.json`, launcher exit code and logs. No raw ASPECT outputs are copied by the indexer; negative payload mutation is confined to an isolated copy under this evidence directory.

## Acceptance and failure classification

The script may write `QUALIFICATION.json` with `status=PASS` only after every stated check passes. Any mismatch, unavailable source payload, unknown audit schema, missing identity/inventory evidence, Linux security-test skip, symlink privilege failure, checkout mutation, or query/integrity discrepancy is FAIL/BLOCKED and must be preserved. The final `PASS` would qualify only this read-only index and its comparison against the existing synthetic engineering trajectory. It would not authenticate operator provenance, qualify restart/reconstruction, interpret `T=0`, validate the rigid-shear physics, authorize ARCANA forward evolution, or promote WORLD_HISTORY.

No FAIR command has yet been run for GEODYN-3C. The updated handoff is pending its exact repair commit and recovery of the historical configuration/input hashes, source inventory and attempt metadata. Missing values are BLOCKED, never synthesized. Only after an actual complete PASS could the verdict advance to `GEODYN_3C_EXPERIMENTAL_TRAJECTORY_ARCHIVE_FAIR_VALIDATED__ARCANA_FORWARD_NOT_AUTHORIZED`. The gates remain `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` and `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`.

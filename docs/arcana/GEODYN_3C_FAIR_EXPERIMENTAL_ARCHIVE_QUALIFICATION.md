# GEODYN-3C — FAIR experimental archive qualification handoff

**Date:** 2026-10-27
**Branch:** `r6/multiphysics-integration-20261026`
**GEODYN-3B module origin:** `e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa`
**GEODYN-3B module source revision:** `ab8fad9282b45c30f1df3653ce447cf5e13c6be4`
**R1 repair baseline / parent:** `ab8fad9282b45c30f1df3653ce447cf5e13c6be4`
**R1 local result:** `GEODYN_3C_R1_LAUNCHER_REPAIR_LOCAL_TESTS_PASS__FAIR_PENDING`

## R3 Git-gate repair — local preparation

R3 replaces the launcher's `.git`-directory assumption with `git rev-parse` worktree validation, so linked worktrees whose `.git` entry is a file are accepted without checkout changes. The candidate and its parent are both required as explicit `GEODYN3C_EXPECTED_COMMIT` and `GEODYN3C_EXPECTED_PARENT` SHA-1 environment values. The launcher resolves the candidate's actual parent and compares it with the supplied parent; it never infers the expected value. The R2 commit `cd573f9328f856078218edb5273f0b55460f403a` has parent `8ab6218be5c389d5682e85d281b7ab582d9950d5`.

Archive-module origin/source revisions (`e3946add...` / `ab8fad...`) and ASPECT reader provenance (`1fd5e8d...`) remain independent provenance checks and are not launcher-parent values. Regression coverage exercises a normal repository, linked worktree, incorrect parent, and omitted parent without changing HEAD, branch, or index. The focused suite remains at 85 collected tests; no test case is added. Windows combined suite: 82 passed, 3 skipped (two symlink-privilege restrictions and NumPy unavailable for the mesh digest test). The Windows `bash` command resolves to an unavailable WindowsApps stub, so shell syntax was not checked locally. R3 has not been run on FAIR; `bash -n`, Linux test results and remote-object checks remain pending.

## R2 compatibility addendum — local Windows verification

R2 corrects three verified compatibility defects without changing the ASPECT reader, archive schema, or scientific gates. The comparator now accepts the original GEODYN-2C `snapshots[].point_fields[]` record: NumPy dtype names such as `float32`, required `min`/`max`, and optional `norm_max` for `velocity`. It preserves the source dtype spelling and explicitly maps it to the reader's VTK type for comparison. Numeric values and typed field digests are not rewritten. Extrema and vector norm are compared using dtype-specific floating-point tolerances; integer extrema compare exactly.

Mesh SHA256 now matches the original auditor serialization exactly: for coordinates, connectivity, offsets and types in order, hash `str(np_array.dtype).encode()` followed by C-order array bytes. A regression fixture independently reconstructs the original Float32/Int32/UInt8 sequence and checks all 11 synthetic mesh records; the full fixture comparison checks 99 field digests.

The FAIR launcher writes JUnit XML and validates testcase outcomes rather than scraping a pytest terminal summary. Acceptance is exactly 85 total, 85 passed, 0 failures, 0 errors and 0 skips. Windows combined suite collected 85 tests and reported 82 passed, 3 skipped: two symlink tests skipped because Windows denied symlink creation (WinError 1314), and the NumPy mesh digest test skipped because NumPy is unavailable in this environment. `py_compile` passed for the helper and tests. The Bash launcher's syntax, Linux zero-skip suite, and comparison against authentic FAIR files remain unverified; no FAIR PASS is claimed.

## R1 repair addendum — Windows preparation

This addendum supersedes earlier handoff statements that required the FAIR checkout to be on the qualified branch/HEAD, parsed a generalized audit schema, and equated the run's adapter claim with the qualification commit. The repaired launcher verifies the exact remote branch ref, candidate commit object and parent; if needed it fetches the verified object without checking out or moving a branch, then extracts the candidate with `git archive`. It records and rechecks the actual checkout branch, HEAD, tracked status, worktree diff and index diff.

Provenance identities are separate: launcher candidate and its parent are supplied for each R1 run; the archive module originated at e3946... and its latest source revision on the baseline is ab8fad...; the qualified ASPECT reader source is 1fd5... . Historical `RunIdentityClaim` values remain evidence-supplied claims and are not rewritten to the candidate launcher SHA.

The embedded comparison accepts only GEODYN-2C `snapshots[].point_fields[]` and fails on unknown/incomplete schema. R2 preserves NumPy dtype names and normalizes them only for comparison with VTK type labels. It compares all 99 field hashes and metadata, including extrema and optional velocity norm, plus all 11 mesh digests using the original auditor's serialization: coordinates, connectivity, offsets, types; for each array, `str(dtype)` bytes followed by C-order data bytes. No digest from a different fingerprint algorithm is compared.

The focused Windows suite completed with 82 passed and 3 skipped: two established symlink-privilege skips and the numeric mesh-digest test because this Python environment has no NumPy. The FAIR launcher requires all 85 Linux tests with zero skips. FAIR Bash syntax validation and real-file qualification have not been run. Recovery of historical inventory/config/input hashes and attempt metadata remains a prerequisite; missing values remain BLOCKED, never fabricated.

## Scope

This package prepares a read-only qualification of the existing GEODYN-2A-R1 rigid-shear PVD/PVTU/VTU files. It does not run ASPECT, MPI, an ARCANA forward model, or any canonical operation. It has not been executed on FAIR; this document makes no FAIR PASS claim. The source bundle, independent numeric audit, and prior adapter evidence remain at their previously reported locations and are not represented as locally rehashed evidence.

Authoritative implementation/API references are [the ratified GEODYN-3A contract](GEODYN_3A_EXPERIMENTAL_TRAJECTORY_ARCHIVE_CONTRACT.md), [the GEODYN-3B MVP report](GEODYN_3B_EXPERIMENTAL_TRAJECTORY_ARCHIVE_MVP.md), `src/arcana_worldsim/r6/experimental_trajectory_archive.py`, and `src/arcana_worldsim/r6/adapters/aspect_snapshot_reader.py`.

## FAIR handoff script

Script: `scripts/r6_geodyn3c_fair_qualification.sh`. It uses only the APIs actually implemented: `RunIdentityClaim`, `SourceDigest`, `index_existing_aspect_series`, `ExperimentalTrajectoryArchive.open`, `verify_integrity`, metadata/query methods, `get_snapshot`, and `get_field`, plus `AspectSnapshotSeries.audit/read_snapshot`.

Transfer this reviewed script outside the FAIR checkout (for example to a controlled temporary location), verify its SHA256 from the Windows handoff, and invoke it there. This avoids adding an untracked file to the existing checkout. After finalizing the current launcher repair commit, set both `GEODYN3C_EXPECTED_COMMIT` and `GEODYN3C_EXPECTED_PARENT` to their exact full SHA-1 values before invocation. The expected parent is an independently reviewed input, not inferred from the candidate:

```bash
GEODYN3C_EXPECTED_COMMIT='<R3 full commit SHA>' \
GEODYN3C_EXPECTED_PARENT='<R3 parent SHA>' \
bash /path/outside/checkout/r6_geodyn3c_fair_qualification.sh \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_F2AV \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2_RIGID_SHEAR/20261026T234423Z_transient_rank1 \
  '<PVD relative path, identified in that directory>' \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2C_NUMERIC_AUDIT/20261027T000139Z_numeric_audit/NUMERIC_AUDIT.json \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2A_R1_FAIR_QUALIFICATION/20261027T105033Z_exact_commit/SOURCE_INVENTORY.json \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2A_R1_FAIR_QUALIFICATION/20261027T105033Z_exact_commit/RUN_IDENTITY_CLAIMS.json \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
```

`SOURCE_INVENTORY.json` and `RUN_IDENTITY_CLAIMS.json` are required input schemas, not claims that files with those names already exist in the historic directory. Recover values from preserved records; never fabricate them. The inventory must cover exactly the PVD-referenced source files. The run's solver/repository/adapter commit values are historical caller claims, distinct from the launcher candidate, its parent, the GEODYN-3B module source revision, and reader provenance. The script records those code identities separately. Git algorithm declarations remain caller-supplied unauthenticated metadata. `configuration_sha256` and every `input_identities` entry require the original exact 64-character SHA256 values. The time-unit source and attempt token must also come from evidence. If any required inventory, claim, or digest is unavailable, stop as BLOCKED.

The repaired script does not require a particular current branch or HEAD. It captures and rechecks the checkout branch, HEAD, tracked status, staged diff, and worktree diff. It verifies the exact remote R6 ref, exact candidate commit object and parent, then uses `git archive`; it never checks out the candidate. The R2 script requires exactly 85 Linux tests with zero skips; any nonzero exit, count mismatch, or skip stops qualification. Pytest JUnit XML is retained and its testcase results are independently counted.

If the PVD filename/location or the historical inventory/claim files differ from the example, pass the actual relative PVD reference and exact existing evidence paths as arguments. Do not select a guessed PVD or use a newly calculated inventory as if it were an independently preserved historical digest. The script prehashes every declared original, the indexer independently hashes the PVD-referenced files, and the script rehashes the same originals afterward; pre/post mismatch is FAIL. These checks establish byte preservation during this qualification, not source authorship.

## Qualification performed by the script

1. Verifies the remote branch ref, exact candidate commit object, parent, and source-file provenance. It captures checkout identity/state before and after without requiring the checkout to match the candidate.
2. Runs the archive, reader, and qualification helper test modules from the extracted commit and requires all 85 Linux tests to pass with no skips.
3. Builds a new metadata-only index with the externally supplied source inventory and claims. The original PVD/PVTU/VTU files remain in place; numeric arrays are not copied into the index.
4. Requires 11 strictly increasing native times from 0 through 1.0142299266 s, a stable 1152-point/512-cell single quadrilateral mesh, nine point fields, and the separate 1.098612289 s solver-completion time. It asserts `SYNTHETIC_ENGINEERING_ONLY`, unauthenticated provenance, `restart=NOT_AVAILABLE`, and `reconstruction=NOT_CLAIMED`.
5. Exercises exact-time, inclusive interval, mesh/field catalog and on-demand snapshot/field queries. A query at solver completion and a point in the unarchived tail must return `MISSING_SNAPSHOT`; no interpolation or synthesized terminal state is accepted.
6. Parses only the original GEODYN-2C `snapshots[].point_fields[]` schema (`type` is a NumPy dtype name, with `min`, `max`, optional velocity `norm_max`) and compares 99 typed field hashes/metadata plus 11 numeric mesh digests. Mesh digest serialization follows the auditor: coordinates, connectivity, offsets, types; each array contributes `str(dtype)` bytes followed by C-order bytes. JUnit acceptance requires exactly 85 passed and zero failed/error/skipped. Unknown/incomplete schema fails closed.
7. Tests incomplete-index status, missing payload status, altered payload on an isolated copy, external symlink rejection, traversal rejection, output collision preservation, invalid sealed-manifest rejection, and archive relocation. Relocation must preserve `archive_id`; payload resolution becomes available only after explicitly supplying the source-root mapping.
8. Records pre/post hashes of all original referenced files, source commit/parent, test log and exit code, generated manifest and sidecar, integrity report, query outcomes, per-field numeric comparison, negative checks, and qualification result. A failed phase remains in the new run directory with a nonzero exit and is not overwritten or retried.

Expected evidence root:

`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN3C_<UTC timestamp>/`

Principal outputs include `source.tar` and its digest, extracted commit source, pytest log/exit code, copied input audit/inventory/claims with hashes, `archive_index/manifest.json` and `manifest.sha256`, `INTEGRITY_REPORT.json`, `QUERY_RESULTS.json`, `NUMERIC_COMPARISON.json`, `NEGATIVE_CHECKS.json`, original pre/post hash maps, `QUALIFICATION.json`, launcher exit code and logs. No raw ASPECT outputs are copied by the indexer; negative payload mutation is confined to an isolated copy under this evidence directory.

## Acceptance and failure classification

The script may write `QUALIFICATION.json` with `status=PASS` only after every stated check passes. Any mismatch, unavailable source payload, unknown audit schema, missing identity/inventory evidence, Linux security-test skip, symlink privilege failure, checkout mutation, or query/integrity discrepancy is FAIL/BLOCKED and must be preserved. The final `PASS` would qualify only this read-only index and its comparison against the existing synthetic engineering trajectory. It would not authenticate operator provenance, qualify restart/reconstruction, interpret `T=0`, validate the rigid-shear physics, authorize ARCANA forward evolution, or promote WORLD_HISTORY.

No FAIR command has yet been run for GEODYN-3C. The updated handoff is pending its exact repair commit and recovery of the historical configuration/input hashes, source inventory and attempt metadata. Missing values are BLOCKED, never synthesized. Only after an actual complete PASS could the verdict advance to `GEODYN_3C_EXPERIMENTAL_TRAJECTORY_ARCHIVE_FAIR_VALIDATED__ARCANA_FORWARD_NOT_AUTHORIZED`. The gates remain `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` and `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`.

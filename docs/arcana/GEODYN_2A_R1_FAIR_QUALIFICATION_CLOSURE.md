# GEODYN-2A-R1 — FAIR numeric validation closure

Date: 2026-10-27
Branch: `r6/multiphysics-integration-20261026`
Implementation commit: `1fd5e8d8f21e28876da9ef89423755615efc6162`
Parent: `60e13475ce04d005ebdd8e0152738611eb5e8943`

## Decision and scope

`GEODYN_2A_R1_ASPECT_READONLY_ADAPTER_FAIR_NUMERICALLY_VALIDATED__ARCANA_FORWARD_NOT_AUTHORIZED`

The decision is limited to the read-only adapter's compatibility with the existing single-rank ASPECT 3.2.0-pre snapshot series and the reported numeric comparisons. It validates neither an ARCANA forward model nor physical interpretation, ARCANA spatial remapping, or canonical-state authority. The returned records remain `SYNTHETIC_ENGINEERING_ONLY`.

## FAIR evidence — operator-reported, not independently rehashed on Windows

Evidence directory reported by the operator:

`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2A_R1_FAIR_QUALIFICATION/20261027T105033Z_exact_commit`

Reported evidence for exact source commit `1fd5e8d8f21e28876da9ef89423755615efc6162` (parent `60e13475ce04d005ebdd8e0152738611eb5e8943`):

- Linux pytest: 32 passed, 0 failed, 0 skipped.
- Read-only adapter execution: exit code 0.
- Independent NumPy-reference comparison: exit code 0.
- Mesh numeric SHA256 comparisons: 11/11 passed.
- Typed numeric field SHA256 comparisons: 99/99 passed.
- Each of the five dynamic fields had 11 distinct states. Reported static fields and duplicate fields agreed with the earlier audit.
- No snapshot was synthesized at solver completion. The original ASPECT output files and FAIR worktree were reported unchanged.
- ASPECT `3.2.0-pre`, source commit `30eb77ee5da186137d436dbad35c6cb3cab64b69`.

The runner, independent comparison report, manifest and raw FAIR evidence were not transferred into this Windows worktree during this closure. The above exit codes and counts therefore remain operator-reported; Codex did not inspect the Linux runner or comparison output and did not independently rehash FAIR files. The implementation commit, its parent, and the Windows source/test/report are locally inspectable. Do not describe the FAIR evidence as locally reverified.

## Failure preserved and repair recorded

The first real-file probe remains a historical failure at:

`ARCANA_WORLD_EVIDENCE/R6/GEODYN_2A_REAL_VTU_PROBE/20261027T100741Z_probe`

Its reported error was `SnapshotFormatError: every numeric array needs a safe, non-empty Name`. The coordinate `Points/DataArray` had no `Name`, which is valid VTK. The probe also exposed separately Base64-encoded header and compressed-payload sections with internal padding. The original failed evidence was not overwritten or reclassified.

R1 commit `1fd5e8d8f21e28876da9ef89423755615efc6162` permits the absent name only for coordinates and preserves `source_name=None`; fields without safe names still fail. It decodes continuous and separately encoded Base64, including zlib blocks and connectivity, checks endian-aware UInt32/UInt64 headers, sizes, decoded lengths, padding, zlib completion and trailing bytes, and exports typed-value SHA256 for fields and coordinates. Windows tests on the repair were 31 passed and 1 platform skip (external symlink creation unavailable), with `py_compile` and `git diff --check` passing. The Linux qualification above is a distinct test and evidence level.

## Qualified parser boundary and remaining limits

The qualified contract is restricted to the formats exercised by the adapter and the reported original series: PVD with part 0; one rank; one VTU Piece or one PVTU Piece source; inline ASCII or Base64 binary; uncompressed payloads or VTK zlib blocks; supported UInt32/UInt64 headers and declared byte order. Appended data, multi-rank or multi-piece layouts, unsupported compressors/encodings, and files outside the declared root remain rejected. Parser size limits are guardrails, not OS memory guarantees.

The reader does not invoke ASPECT, authenticate caller-supplied run/provenance claims, remap onto ARCANA supports, generate geology, create a `DomainStateEnvelope`, or write `WORLD_HISTORY`. The reported `T` field remains constant zero with its discrepancy from the initial expression unexplained. No field is inferred at solver completion time `1.098612289 s`; the last reported snapshot is earlier. Scientific ARCANA initial conditions, material/rheology closure, boundary conditions, time-dependent forcing and spatial mapping remain unresolved. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` remains unchanged.

## Bounded next phase — GEODYN-3 experimental trajectory archive contract

Prepare a noncanonical, read-only-queryable archive contract for the actual output of a bounded experimental trajectory. Minimum record groups:

1. **Run manifest:** immutable run ID; exact solver/build/source identity and hashes; input/configuration hashes; runtime/toolchain; experiment classification; completion status; manifest version; external evidence root; payload members with immutable relative references, byte lengths, and SHA256.
2. **Snapshot index:** exact model time and declared unit as produced by the solver; snapshot ordinal and source file identity; stable mesh identity based on explicit mesh data and algorithm/version; point/cell counts; coordinate and connectivity payload references; schema identity.
3. **Field index:** stable field ID, association (point/cell), scalar type, component count, tuple count, declared units, source/model meaning with provenance, payload reference and typed-byte SHA256. Unknown semantics or units remain `UNKNOWN`; names alone do not establish physical meaning.
4. **Query surface:** enumerate times and snapshots, select fields by stable ID, return immutable payload references and metadata, and verify payload hash on read. Queries do not interpolate or manufacture states.
5. **Completion and integrity:** only mark a run complete after all declared snapshots and payloads verify; interrupted or partial runs remain explicitly incomplete and cannot masquerade as complete.

This phase must not create canonical states, convert solver time to geological time, infer resource generation, or couple surface processes or Deep. A future adapter may consume the archive only after explicit spatial mapping, units and scientific interpretation are separately supplied and verified. GEODYN-2A does not unblock ARCANA forward evolution.

## Gates

`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; ARCANA forward remains unauthorized. No solver, MPI, ShellSet, remapping, canonical write or new numerical evolution was performed in this closure.

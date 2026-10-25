# ARCANA WORLD — VIEW-1B (2026-10-14)

Decision: `VIEW1B_STATIC_T0_EXPORT_VERIFIED__SCIENTIFIC_AUTHORITY_UNCHANGED`.
Location: `WINDOWS_WORKTREE_ONLY`; no commit, push or PR.

Entry branch `r6/si1-bandwidth-f2av`, HEAD
`8c75c439ab45a9d4e79930bd506e686e088e151d`, unchanged from VIEW-1A. Entry worktree
had five VIEW-1A ledger edits and 658 untracked files (nine VIEW-1A files plus 649
unrelated entries). Existing VIEW-1A hashes matched their ledger pins before
changes. Repository instructions, current ledger, VIEW-1A report, audit, TypeScript
contract and complete export schema were inspected. Cached remote divergence is
0/0; live remote was verified during VIEW-1A, not reverified in this task.
The user separately authorized this static presentation export; scientific
INT-2C NEXT_ACTION remains STOP.

Initial pending Python check: mypy 1.20.2 with `--check-untyped-defs` found 11
errors in VIEW-1A's test harness (optional import spec/loader and undeclared class
attributes). Added explicit import guards and class declarations only. The audit
implementation, source lock, inventory, TypeScript contract, proposed layers,
original schema and historical report remain unchanged. The original test hash
in historical VIEW-1A evidence is retained; VIEW-1B records the repaired test hash.
Final check: PASS, no issues in all four audit/export/test Python files. No check
was weakened or suppressed. TypeScript static typechecking remains outside this
Python export milestone; browser/toolchain qualification belongs to VIEW-2A.

Complete JSON Schema validation: PASS with standards-compliant
`jsonschema.Draft202012Validator` 4.25.1. The original Draft 2020-12 schema passes
its metaschema and all 74 proposed layer instances pass. The new static-export
envelope passes its metaschema; both complete export manifests and embedded
datasets pass. The original schema is unmodified. The validator and dependencies
were installed into repository-local tooling with installer temporary files
inside that same owned directory. Two installer attempts overlapped and the
second emitted existing-directory warnings; imported pinned versions were then
verified and all standards-based validations passed. NumPy 2.3.5 was reused from
the bundled runtime, with no provider or scientific runtime installation.

Delivered dataset:

- `visualization/exports/VIEW1B_T0_V1/manifest.json` and 30 NPY v2 arrays.
- `visualization/exports/VIEW1B_T0_V1_REPEAT/` independently prepared and published
  a second byte-identical export: all 31 relative file paths/hashes match.
- Export ID:
  `viewexport_b0ff6b261de6640dce02256a94340b4c1d1f390e85914ddb48ada08493ba6df1`.
- Manifest file SHA256:
  `6b008eea5035a3749cb58de275a5c2f2f033dc62724c475ef72fb56f299b87f5`.
- Numerical NPY assets total 6,847,500 bytes per export. Every asset's full-file
  and element-data hash is recorded in the manifest and verification evidence.

The export authenticates both external source byte counts and SHA256 before
decoding immutable byte snapshots. Geography preserves all 14 original arrays,
180×360 logical shapes, uint8/int8/int16/float32/bool dtypes, C ordering, supported
land values, categorical codes and boolean support/UNKNOWN/uncertainty masks.
Partition preserves all 16 native arrays: 64,800 faces with float64 [64800,5,2]
latitude/longitude vertices and the original 1,983 edge records. These are the
original finite-volume cell faces and edge indices, not a new geometry mapping.
R6 remains spherical, radius 6,371,000 m; rows south-to-north, columns west-to-east,
with periodic longitude. Only T0=210 Ma and elapsed years `[0.0]` are exported.

Numerical identity: all 30 outputs match source shape, dtype descriptor, array
ordering and element bytes exactly. An independent standard-library NPY-header
reader compared the original archived element byte streams directly with exported
NPY element streams, without interpreting floating-point values. Thus NaN payloads
and integer/boolean bit patterns, not merely equal_nan equality, were checked.
Synthetic regression includes distinct quiet/signaling/signed NaNs, positive and
negative zero, categorical -2/0 and boolean masks. Replacing a NaN payload with
another NaN is detected as inequality.

Validity and authority: 14,258 supported land cells and 50,542 ocean elevation
NaNs remain intact. Ocean elevation is unsupported, not bathymetry. 3,909 boundary
cells and all 1,983 boundary-edge sides retain UNKNOWN process classification.
Categorical 0 is retained; province -2 remains NOT_APPLICABLE. Domain UNKNOWN
boolean masks remain boolean masks, with authority NONE; no numerical Deep,
climate, hydrology, bathymetry or grid-motion fields are created. Source authorities,
units, spatial/temporal support, validity rules, original state references and
uncertainty rules remain visible in every embedded dataset layer. `viewexport_`
and `viewarray_` identities are separate presentation identities, never new
scientific StateId records. Kinematics JSON and engineering trajectories are
excluded from this two-NPZ export.

Transaction: fresh same-parent staging directory, complete NPY reread plus exact
manifest/file-set/hash checks, standards-based schema validation and consumed-input
rehash precede Windows no-clobber rename. Existing output directories and racing
destinations are never overwritten. On a handled failure, only the invocation's
owned staging directory is cleaned. POSIX publication is explicitly unsupported;
no cross-platform atomic-publication claim is made. File flush/fsync and atomic
visibility are evidenced, not crash/power-loss durability. Concurrent source writer
exclusion is not claimed; the output binds an authenticated immutable snapshot.

Focused regressions: 23 PASS, zero failures/skips (11 VIEW-1A plus 12 export cases).
Coverage includes real array identity/masks; NaN payloads; coordinate/seam behavior;
manifest and source SHA/size integrity; deterministic complete exports; missing
sources; unsupported integer/object dtype and disabled pickle; invalid schema and
contract; prepublication source changes; corrupt staged arrays; and existing/racing
destination preservation with no partial publication. Test directories were created
and cleaned solely by this execution inside `visualization/`; no historical sandbox
cleanup was attempted. All 59 original VIEW-1A source SHA256 values were independently
rechecked after export and tests and remained unchanged.

Evidence: `VIEW_1B_VERIFICATION.json` contains raw-byte comparisons, complete output
hashes, versions, schema/typecheck/regression outcomes and the decision. Implementation:
`export_t0.py`; envelope: `export-manifest.schema.json`; tests: `tests/test_export_t0.py`;
runtime pins: `requirements-view1b.txt`; commands/boundaries: `VIEW_1B_USAGE.md`.
Only visualization additions, the small VIEW-1A test typing repair and additive
ledger notes belong to VIEW-1B. Unrelated files/evidence are preserved; final diff,
reference/hash and whitespace checks close the workstream.

Shared-worktree change disclosed: during final inspection the unrelated untracked
count increased from 649 to 757. Newly appearing INT-3/ENG10K code/configuration,
tests and output artifacts were not created, edited, executed or cleaned by
VIEW-1B. Their appearance is outside this scope and their contents/authority were
not audited here. Subsequent INT-3 notes added to the shared ledger were also
retained. Branch/HEAD and the 59 pinned VIEW-1A source identities remained
unchanged at closure. This report's non-execution statements describe VIEW-1B's
actions, not other activity in the shared workspace.

VIEW-2A decision: **static numerical input dataset READY for separately reviewed
browser integration scope**. No browser implementation is authorized by VIEW-1B.
Remaining VIEW-2A work includes TypeScript/toolchain qualification, immutable loader
hash/schema verification, mask-aware picking and exact support labels, plus native
small-circle latitude edges, antimeridian and polar rendering. No Cesium runtime
was executed. No Solver, scientific model, replay, provider, temporal interpolation,
WORLD_HISTORY constructor/write or canonical promotion occurred; scientific gates
and NEXT_ACTION STOP remain unchanged.

# VIEW-1B — static T0 export

Use an existing Windows CPython 3.12.10 runtime with the versions in
`requirements-view1b.txt`. The verified local session used bundled NumPy 2.3.5,
existing mypy 1.20.2 and jsonschema 4.25.1 plus its pinned dependencies installed
only into `visualization/.view1b-tools/packages`. No global environment was
changed. Local tooling and owned test/cache directories are ignored; published
exports remain visible and are not staged automatically.

For this checkout's verified environment, from the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = (Resolve-Path visualization/.view1b-tools/packages).Path + ';C:\Users\jose_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages'
python -m visualization.export_t0 --output visualization/exports/NEW_REVIEWED_EXPORT_NAME
python -B -m unittest discover -s visualization/tests -v
python -m mypy --check-untyped-defs --no-incremental --cache-dir=visualization/.mypy-cache-view1b visualization/audit.py visualization/export_t0.py visualization/tests/test_audit.py visualization/tests/test_export_t0.py
```

The output parent must already exist and the destination must be fresh, inside
this repository's `visualization/`. `--external-root` optionally supplies an
explicit relocated root containing `initial_world/` and `tectonic_t0/`; original
byte counts and SHA256 are mandatory. There is no search, download or replacement
generation. VIEW-1A source inventory, proposal, schema, source lock, audit code and
TypeScript contract are authenticated against their preserved review digests.
Changing a review pin requires a separately reviewed contract revision.

The exporter first authenticates immutable byte snapshots, runs the original
geometry/mask checks and validates the entire original proposal with a full
Draft 2020-12 validator. It writes 30 NPY v2 assets using NumPy's
`write_array(..., allow_pickle=False)`, keeps original native dtype and C order,
and rereads every asset with `np.load(..., allow_pickle=False)` for exact element
byte comparison. Header serialization is deterministic in the recorded runtime.
All 14 geography fields/masks and 16 native partition arrays are retained.
NONE-authority boolean masks express UNKNOWN; they never create numerical
bathymetry, Deep, climate, hydrology or grid-motion values.

`manifest.json` is an `ARCANA_VIEW_STATIC_T0_EXPORT_V1` envelope. Its embedded
dataset validates against the unchanged `ARCANA_VIEW_EXPORT_DATASET_V1` schema.
The stricter envelope adds separate `viewexport_`/`viewarray_` identities,
per-array NPY version/dtype descriptor/shape/order/data SHA256, provenance inputs,
declared runtime and false scientific governance flags. `sourceStateId` and
embedded layer `stateId` remain original source references; no scientific record
is created. Export identity hashes canonical manifest contents excluding its own
`exportId`; the full manifest byte hash is separate and recorded in verification.
Paths are relative within the dataset, never temporary staging paths.

Publication is currently supported only on Windows: same-parent directory rename
fails if any destination already exists, including one created concurrently.
POSIX publication fails closed until a separate no-clobber implementation is
reviewed. Files are flushed/fsynced, the complete staged manifest/assets are
validated, and all consumed input hashes are checked again before publication.
Failures clean only that invocation's newly created staging directory. Existing
destinations, historical sandbox artifacts and inputs are never removed.
Atomic visibility is tested; power-loss recovery/durability is not qualified.

The two retained exports in `exports/VIEW1B_T0_V1/` and
`exports/VIEW1B_T0_V1_REPEAT/` are byte-identical across all 31 files. Neither
contains imagery, interpolation, a browser runtime, scientific model output or
WORLD_HISTORY writes. `VIEW_1B_VERIFICATION.json` records independent source NPY
element-byte checks and all output file hashes. `VIEW_1B_REPORT.md` contains the
scope decision and remaining VIEW-2A requirements.

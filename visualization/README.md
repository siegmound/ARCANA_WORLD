# VIEW-1A — independent viewer source audit and export proposal

This directory is an isolated visualization workstream. It imports no ARCANA
runtime, constructs no HistoryStore, and exposes no replay, evolution or write
operation. The INT-2C numerical STOP boundary and every scientific gate remain
effective. No implementation beyond VIEW-1A is authorized by these files.

Run from the repository root with the existing Python standard library:

```powershell
python -B visualization/audit.py
python -B -m unittest discover -s visualization/tests -v
```

The CLI prints JSON to stdout only. Exit 0 means all pinned inputs and the
implemented structural checks verified; 2 means `INPUT_UNAVAILABLE`; 1 means
`FAIL_CLOSED` (hash, size or unsupported structure). Redirect only to a fresh
visualization evidence destination, never to a source file. There is no output
path argument. Paths are resolved from the repository selected by `--repo` and
the recorded external locators. To relocate external payloads, supply
`--external-root <directory containing initial_world and tectonic_t0>`.
No recursive payload discovery or replacement generation occurs. A missing
payload leaves its actual SHA, fields, dtype and shape unobserved; declarations
in the source manifest cannot supply its numerical values.

`source-lock.json` pins the requested source documents, every B3 evidence file,
the two external T0 payloads and the preserved engineering bundles cited in the
reports. Each pin declares its basis. Current tracked-document byte pins are
specific to reference HEAD; bundle members use the original authenticated
manifest identities. The historical B3 inventory is evidence, not proof of
today's external file presence. Actual file digests differ from semantic/state
identities and are never substituted for them. The lock is a reviewable trust
anchor, not signed provenance; any later revision requires review. Original
source paths and authority labels must remain visible.

`source-inventory.json` is the local audit observation, with per-file identities,
observed field structure, array dtypes/shapes, finite/NaN counts, categorical
counts, boolean-mask counts, declared support metadata and contract checks.
JSON structure describes the first list element and list length; it is not a
schema qualification of every engineering record. Engineering units/support
are carried separately from the source's explicit units and support records.
The audit hashes each verified source again after inspection. This detects
ordinary concurrent changes but provides no filesystem snapshot guarantee.

`layer-contract.ts`, `export-dataset.schema.json` and `proposed-layers.json`
describe version 1 of a future dataset. The example is a proposal with null
numerical/imagery assets, not an exported dataset or a viewer. It lists geography
fields and masks, partition fields, selected per-plate kinematics and the exact
engineering diagnostic samples. Engineering layers require an explicit display
opt-in and a persistent NONCANONICAL_ENGINEERING label. NONE-authority mask
layers describe missing-domain support; they cannot supply numeric domain data.

Future export requirements (not implemented here):

- Authenticate the lock and every asset before decoding or displaying values.
  Abort the whole dataset on SHA mismatch. Missing inputs remain unavailable.
- Preserve original numerical dtype, endianness, C order, NaN and exact samples
  in separate binary assets (e.g. original NPY members). Store support, UNKNOWN,
  invalid, NOT_APPLICABLE and uncertainty masks as separately hashed assets or
  explicit categorical rules bound to the original field. Do not use PNG colors
  as numerical values, cast all values to uint8 or fill NaN/UNKNOWN with zero.
- Keep zero as a valid measurement where supported. For elevation, the original
  elevation_support_mask selects land; ocean NaN is unsupported elevation and
  ocean bathymetry is UNKNOWN. province_class -2 is NOT_APPLICABLE; boundary_class
  0 is UNKNOWN. These states stay distinct in picking, legends and imagery alpha.
- Retain source identity, B3 semantic state ID where applicable, source authority,
  units, support and uncertainty for every layer. A display derivative never
  acquires scientific authority. Numeric asset dtype/shape and byte count must
  agree with the source; imagery may independently use a palette and north-first
  pixel orientation, with a declared row transform `imageRow = 179 - sourceRow`.
- Index `row*360+column`; centers are `(-89.5+row, -179.5+column)` degrees.
  Bounds are `[-90+row,-89+row] × [-180+column,-179+column]`. Longitude is periodic:
  +180 maps to -180/column 0. Internal cell bounds are half-open; the north pole
  is explicitly assigned row 179. No extra column becomes new spatial support.
- T0 is a single 210 Ma instant. Per-plate Euler records do not authorize motion
  animation or a grid velocity field. R4/INT-1D have separate stored engineering
  elapsed-year coordinates and material profiles; do not synthesize intermediate
  samples, map them to global fields, extend support, or merge the experiments.
  C3 is replay verification evidence for R4, not a new global historical state.
- Use the schema for structural validation only. A future exporter must also
  check source authority, per-field masks, monotone exact time arrays, layer ID
  uniqueness, cross-asset support and all content hashes. Proposed layers with
  null numeric assets cannot be loaded as numerical data by a viewer.

CesiumJS / TypeScript / React / Vite boundary:

The future React/Vite application consumes only a versioned, authenticated
export directory through an immutable TypeScript loader. It does not access
WORLD_HISTORY or import Python scientific/provider modules. It must instantiate
the R6 sphere explicitly with three equal 6,371,000 m radii throughout scene,
coordinate conversion and geometry. Cesium documents a custom three-radius
[Ellipsoid](https://cesium.com/learn/cesiumjs/ref-doc/Ellipsoid.html).
Package versions and browser runtime qualification remain a later reviewed step.

R6 cell latitude edges are small-circle arcs and meridians are great-circle arcs.
Connecting the four corners with generic geodesic polygons does not preserve
those faces. A later rendering adapter must retain the finite-volume latitude/
longitude rectangles, split antimeridian presentation geometry deterministically,
and handle the shared polar point. Any display tessellation is a rendering
approximation, not subcell evidence; exact face IDs remain available for picking.
Raster textures may be vertically reversed for display without reversing the
numerical arrays. A neutral spherical base is presentation geometry only;
external terrain, Earth imagery and invented ocean depths are outside the contract.

No Cesium application, dependency installation, provider engine, export writer,
HistoryStore replacement, generic plugin system or full UI is included. Review
the next bounded scope separately: a dtype-preserving static T0 export and its
offline schema/hash/mask validation, before any browser integration.

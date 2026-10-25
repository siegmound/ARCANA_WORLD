# ARCANA World Viewer — VIEW-2A

VIEW-2T adds a bottom historical timeline. Drag or use the range input's keyboard
Home/End/arrows to browse 210 Ma to 0 ka. Only 210 Ma is available: unsupported
requests display UNAVAILABLE and explicitly retain the last rendered T0 globe.
The T0 diamond or Previous checkpoint returns to T0. Next and Play are disabled
when no corresponding verified checkpoint exists. Time zoom changes only the
navigation window, down to single-year precision; Full history restores its span.
See `../TEMPORAL_CATALOG_CONTRACT.md` and `../VIEW_2T_REPORT.md` for the separate
timeline scope and evidence. All commands below remain valid.

Local React / TypeScript / Vite / CesiumJS application for the verified synthetic
R6 T0 geography at 210 Ma. It reads VIEW-1B data; it imports no scientific runtime
and provides no simulation, replay, history-write or canonical-promotion action.

From this directory, with Node.js 22.23.1 and npm 10.9.8 (verified Windows runtime):

```powershell
npm ci
npm run dev
```

Open [the development viewer](http://127.0.0.1:5173/). The locked dependencies
are installed locally. Package installation needs npm registry access; essential
rendering after installation uses only localhost and verified in-memory images.
No Cesium ion account/token, online basemap or HPC connection is required.
If npm reports a registry certificate-chain error on this Windows host, use its
existing certificate store with `$env:NODE_OPTIONS = '--use-system-ca'` before
`npm ci`. TLS verification remains enabled. Within the Codex restricted sandbox,
the server may need host-access permission to accept localhost browser sockets;
a normal host PowerShell session can use the command above.

Verification / packaged preview:

```powershell
npm test
npm run typecheck
npm run build
npm run preview
```

The preview serves the build at [localhost:4173](http://127.0.0.1:4173/).
`npm run build` includes verified staging and TypeScript checking. The Cesium
bundle is currently about 4.18 MB before compression; Vite's size warning remains
visible. Bundle splitting/optimization is a later reviewed step, not a runtime
qualification substitute. Vite's `preserveSymlinks` avoids the observed Windows
sandbox `realpath` denial without modifying inputs or resolving alternate data.

Drag the globe to rotate, scroll to zoom and Ctrl-drag to tilt. Accessible camera
buttons also provide rotation, zoom, tilt and reset. The land/ocean checkbox hides
the complete display layer and reveals a neutral sphere. Epoch, synthetic
classification, expected dataset identity, loading/verification/error state remain
visible. The Cesium logo is local package attribution, not an online basemap.

Transport and authority boundary:

- `scripts/stage-cli.ts` reads `../exports/VIEW1B_T0_V1/`. It authenticates the
  pinned full manifest byte digest, performs strict Draft 2020-12 validation,
  checks original source identity/authority/210 Ma support and authenticates
  the two selected NPY files before decoding them. No direct F: browser URLs.
- Five files are staged under `public/arcana-t0/`: unchanged manifest and two NPY
  masks, deterministic PNG and its provenance. The other 28 numerical assets
  stay in VIEW-1B; the globe's verification scope is the two geographic masks.
  Staging uses a new sibling directory and Windows no-clobber rename. Existing
  stages are reused only if all expected file identities/membership match.
  Mismatched existing data is never overwritten. Output is confined to viewer/;
  failed staging cleanup touches only the exact owned temporary directory.
- `arcana-availability.json` is a mutable development receipt. A missing/invalid
  source makes it UNAVAILABLE, so a prior cache cannot silently become a fallback.
  `npm run dev` still starts a neutral viewer with the error; `npm run build`
  fails when staging is unavailable. Runtime validation also detects missing or
  altered staged assets. The receipt is not a scientific state or trust anchor.
- PNG derivation preserves 360 columns and 180 rows, with
  `imageRow = 179 - sourceRow`, unchanged column order and bounds
  [-180°, -90°, +180°, +90°]. Categorical 0=OCEAN/1=LAND; coastline 1 highlights
  that original cell. No interpolation, upsampling, extra seam column or invented
  geographic detail. Palette is a DISPLAY_ONLY choice, recorded in provenance.
- The browser reauthenticates the manifest and both NPY assets, verifies PNG byte
  hash and provenance, then compares all 259,200 decoded RGBA bytes with the
  expected source-cell colors before creating its Blob URL. The imagery layer
  applies NEAREST to both minification and magnification, with anisotropy 1.
- The globe, terrain sphere, map projection, image provider and Cartesian camera
  conversions explicitly use radius 6,371,000 m on all three axes. There is no
  default modern imagery, terrain service, Earth displacement or height sampling.
  Geographic texturing retains latitude/longitude cell support; Cesium's sphere
  mesh is a presentation tessellation, not new subcell scientific evidence.
- The core `CesiumWidget` avoids the legacy Knockout widget's eval dependency.
  CSP forbids remote connections and JS eval; local Blob access is allowed for
  the authenticated PNG. All Workers, ThirdParty, Assets and Widgets directories
  are served locally from `/cesium/`, as specified in the official
  [Cesium static-asset guidance](https://cesium.com/learn/cesiumjs-learn/cesiumjs-quickstart/).

Automated tests cover orientation/all cell centers/seam/poles, exact category
semantics, all actual PNG cells, hashes/provenance/authority rejection, deterministic
derivation, immutable original inputs and fresh/reused/failed staging. The separate
manual Windows browser evidence is in `../VIEW_2A_BROWSER/`; it includes development
and production rendering, camera/visibility interactions, explicit unavailable
receipt behavior and observed local-only resource origins. The controlled error
receipt was restored; no original VIEW-1B file was changed.

The source contract and 1B export remain immutable. Scientific qualification gates
stay separate. VIEW-2B needs its own reviewed scope; suggested next work is bounded
read-only cell picking with source identity, units, authority, validity and UNKNOWN.
Topographic displacement, historical playback, charts and resource providers are
outside VIEW-2A.

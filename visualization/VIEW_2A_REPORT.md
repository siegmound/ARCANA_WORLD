# ARCANA WORLD — VIEW-2A (closed 2026-10-15, Europe/Rome)

Decision: `VIEW2A_T0_BROWSER_GLOBE_VERIFIED__SCIENTIFIC_AUTHORITY_UNCHANGED`.
Location: `WINDOWS_WORKTREE_ONLY`; VIEW-2A performed no commit, push or PR.

The React/TypeScript/Vite/CesiumJS local application runs with the actual verified
VIEW-1B R6 T0 dataset at 210 Ma. Both development and packaged production builds
were observed rendering synthetic land/ocean/coastal cells in the Windows Codex
in-app browser. This is a presentation-runtime qualification only.

Session opened 2026-10-14 and closed after local midnight on 2026-10-15.
Entry branch `r6/si1-bandwidth-f2av`, HEAD
`8c75c439ab45a9d4e79930bd506e686e088e151d`; five pre-existing ledger edits and
1,183 untracked entries. Required ledger, VIEW-1A/1B reports, original layer/schema
contracts, VIEW-1B manifest and Cesium boundary documentation were inspected.
`VIEW_2A_ENTRY.json` records initial status names and all 62 original VIEW-1B file
hashes. During this task independent INT-3 commits advanced the shared checkout to
`16e4fa94bab659879a871222bd96ec72c561dfc3`; cached remote divergence 0/0 at inspection.
Nine initially untracked INT-3 code/configuration/report/test files became tracked,
and 45 additional unrelated untracked entries appeared at that inspection. These
were not deleted or changed by VIEW-2A. INT-3 notes and scientific next-action
boundaries are preserved; the viewer remains bound to the old, immutable 1B export
identity rather than silently rebinding to a new checkout/scientific authority.
At closure, additional concurrent tracked edits were visible in
`scripts/r6_int3_eng10k.py` and `src/arcana_worldsim/r6/int3_eng10k.py`; these were
left untouched and their behavior was not assessed by this visualization milestone.
Later closure checks also observed concurrent edits to
`scripts/r6_int3_eng10k_supervisor.py` and `tests/test_r6_int3_eng10k.py`, likewise
preserved outside the viewer scope.

Delivered source: `visualization/viewer/`, including pinned package-lock, strict
TypeScript, local asset staging, source/texture verification, accessible camera and
visibility controls, loading/error states and instructions in its README. The UI
always displays `210 Ma` and `SYNTHETIC_AUTHORIAL_INITIALIZATION`. It does not offer
historical playback, scientific inspection, charts or topographic displacement.

Source export:
`viewexport_b0ff6b261de6640dce02256a94340b4c1d1f390e85914ddb48ada08493ba6df1`.
Manifest file SHA256:
`6b008eea5035a3749cb58de275a5c2f2f033dc62724c475ef72fb56f299b87f5`.
Selected arrays remain exact 180×360 C-order uint8:

| Field | Original NPY SHA256 |
|---|---|
| land_ocean_mask | a220bc6c9b356968f17e965954f4a93ec9b58480102a43ef088895744829de5b |
| coastline_mask | 27ee898132aecb577a2ce2bd335f9d189dd216ff18f1a213b9038d28c3f1b663 |

Display texture: `viewer/public/arcana-t0/t0-display.png`, 360×180 RGBA, 2,882 bytes,
SHA256 `a8558c0123241f9ec6cfe3cb687a30c84af9c71f2b8b81966c4a666570b31761`.
Decoded RGBA SHA256
`c93619c54604206f5a7b3f540edaa6d205c55b2be35493591187d3f9fb30fdea`.
`texture-provenance.json` records both source identities, original export/manifest
identity, palette, bounds, row transform, periodic seam, sampling and DISPLAY_ONLY
status. Source row 0 maps to image row 179, column unchanged. Zero retains ocean
semantics; coastline 1 selects the original coastal cell. No categorical resampling
or extra longitude column occurs. Browser PNG decoding and automated PNG tests both
compare all 64,800 source cells. Derived imagery remains separate from original
numerical NPY values and cannot confer scientific authority.

The sphere has three equal 6,371,000 m radii. Globe, ellipsoid terrain, projection,
image provider and camera conversions explicitly use it. Default imagery and
modern terrain are disabled. Sun, moon, skybox, atmosphere and animation are off;
the viewport displays an ellipsoid surface until a separate topography scope is
qualified. NEAREST minification/magnification and anisotropy 1 retain categorical
texture sampling. Cesium's globe mesh is presentation geometry, not finer evidence.

Local transport: strict schema validation and fixed byte-digest authentication
precede decoding. Only the manifest, two selected NPY assets, PNG and provenance
are staged in a fresh owned directory and published with Windows no-clobber rename.
Matching stages can be reused; mismatches fail closed. A separate development
availability receipt gates the browser even when an older cache exists. Missing,
corrupt or unavailable data leaves a neutral globe with an explicit error. No F:
URL, source regeneration, ion credentials, online basemap or HPC connection is
needed. All Cesium static folders are copied locally and served under `/cesium/`.

Automated verification (distinct from browser observations):

- `npm test`: **8 PASS, 0 FAIL, 0 SKIP**. All 64,800 cell-center mappings, seam and
  poles; row orientation/corner semantics; invalid codes; all actual texture cells;
  DISPLAY_ONLY provenance and PNG/RGBA/source hashes; authority/hash/header rejection;
  repeatable bytes; original input immutability; fresh/reused/failed staging.
- `npm run typecheck`: PASS, TypeScript 5.9.3 strict with library checking enabled;
  includes the original readonly VIEW-1A layer contract.
- `npm run build`: PASS, Vite 7.1.12, 1,602 modules transformed. Production JS
  4,176.77 kB (gzip 1,122.30 kB); its >500 kB bundle warning is disclosed and retained.
- Both full original VIEW-1B exports (62 files) and all 59 original audited source
  digests rechecked unchanged. Original 1A/1B contracts, exports and evidence remain
  untouched; final source/hash/whitespace/scope checks are indexed separately.

Manual agent-driven Windows browser verification, not an automated browser test
suite: development `http://127.0.0.1:5173/` and production
`http://127.0.0.1:4173/` reached VERIFIED after actual tile rendering. Saved screenshots
and DOM observation transcript are in `VIEW_2A_BROWSER/`. Observed radii match the
specified sphere, sampler values are 9728/NEAREST, source-pixel check is
`64800_SOURCE_CELLS_EXACT`, and resource origins contain only the current localhost
origin with zero observed external resources. CSP also restricts connections to
self, verified in-memory Blob images and local development WebSocket; JS eval and
remote basemaps are disallowed. Camera rotation/zoom/tilt buttons changed actual
camera coordinates/pitch; canvas pointer input responded; visibility hid the map
and showed a neutral sphere. A controlled UNAVAILABLE transport receipt produced
the expected explicit error/neutral globe and was restored using verified staging.
No original numeric asset was altered for that fixture.

Observed setup/runtime failures and resolutions:

- npm initially failed registry certificate verification. Retried using the
  existing Windows system CA store; TLS verification was retained.
- Three initial TypeScript diagnostics were fixed with optional-object guards and
  a copied invalid test fixture that respects the readonly source contract.
- Vite sandbox native realpath failed on F:. Supported `preserveSymlinks` resolution
  fixed it without changing dataset inputs.
- Sandbox loopback access timed out/was denied. Host-access-authorized localhost-only
  servers responded and were used for browser verification; no LAN binding or
  firewall/security setting was changed.
- Legacy Cesium widget Knockout initialization required JS eval. The application
  uses core `CesiumWidget` instead, retaining the eval restriction. Authenticated
  Blob loading additionally required local Blob access in connect-src. Both were
  verified after correction, with no scientific/external network dependency.

Verified runtime: Windows 10.0.26200, Node 22.23.1, npm 10.9.8, React 19.2.0,
CesiumJS 1.146.0 / engine 26.4.0 / core 0.1.0, TypeScript 5.9.3, Vite 7.1.12.
The node_modules, installed static-library cache, build cache and temporary tools
stay isolated under viewer/ and ignored. Test cleanup removed only newly owned
directories. No historical sandbox cleanup or deployment was performed.

VIEW-2B recommendation: separately review bounded read-only cell picking that
reports source cell ID, coordinates, native units/value, authority and validity/
UNKNOWN without interpolating. Do not add topography, temporal playback or new
providers under this outcome. Cross-platform staging, automated browser regression,
bundle optimization, production hosting and scientific qualification remain outside
this milestone. VIEW-2A executed no Solver, scientific model, replay, provider
evolution, WORLD_HISTORY constructor/write or canonical promotion. All numerical
STOP/qualification gates remain unchanged.

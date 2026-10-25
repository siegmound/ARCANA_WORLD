# ARCANA WORLD — VIEW-2T (2026-10-15, Europe/Rome)

Decision: `VIEW2T_HISTORICAL_TIMELINE_FOUNDATION_VERIFIED__SCIENTIFIC_AUTHORITY_UNCHANGED`.
Location: WINDOWS_WORKTREE_ONLY. No commit, push, PR, simulation, replay, provider
execution, WORLD_HISTORY write or canonical promotion was performed.

The production React/TypeScript/Cesium viewer now provides a responsive bottom
timeline from 210 Ma to 0 ka, draggable and keyboard-accessible scrubbing, available
checkpoint markers, directional checkpoint navigation and time-window zoom down
to integer years. Selected time and rendered dataset time are visibly separate.
T0 is the sole verified globe checkpoint. Unsupported ages show UNAVAILABLE while
the globe is explicitly labeled **Last rendered state: 210 Ma**. The browser title
also distinguishes selected and rendered ages. Navigation never interpolates,
retimes imagery, constructs missing scientific states or silently selects T0.
Play remains disabled because there is only one compatible renderable epoch.

Initial inspection read repository AGENTS, current ledger/procedure/roadmap,
VIEW-1A/1B/2A reports, layer/export contracts, the VIEW-1B manifest and the existing
Cesium integration documentation. Entry branch was `r6/si1-bandwidth-f2av`, HEAD
`84c04fddac0fe078958dc0fe2ccbbe9e7c2c23fd`, cached remote divergence 0/0.
Staged/unstaged ledger edits, staged INT-3 supervisor/test/report edits and 1,947
untracked file paths were already present. `VIEW_2T_ENTRY.json` records entry
status and preservation hashes. Independent concurrent INT-3 work advanced HEAD
to `5ea8f6604bc4583a01b600f12f68eff3f9cd14f2`, cached divergence 0/0 at recheck.
Its staged files became committed independently; this milestone made no Git
publication. INT-3 supervisor, tests and natural-exit report retain their entry
byte hashes. All initial untracked paths remain present. Existing ledger text was
retained and the five required ledger files received additive visualization notes.

Implementation:

- `viewer/src/temporal.ts`: typed readonly temporal catalog, deep-frozen detached
  snapshot derived from the authenticated export manifest; explicit HISTORICAL_BP
  integer-year time domain, exact selection, stable chronological/tie ordering,
  compatibility/history/branch isolation, availability filtering, checkpoint and
  time-window helpers. Per-entry original layers retain units, authority,
  provenance, validity/UNKNOWN, source and numerical identities and spatial support.
- `viewer/src/Timeline.tsx`: responsive panel, range control, T0 diamond, selected/
  rendered labels, availability, previous/next, disabled playback with explanatory
  help and geological-to-year navigation zoom. Returning to a checkpoint outside
  the current window recenters that window. Playback controller advances only
  exact renderable checkpoints and stops at the end; multi-epoch renderer dispatch
  is not admitted in this milestone, so playback cannot activate with current data.
- `TEMPORAL_CATALOG_CONTRACT.md`: versioned contract and admission boundary for
  future epochs, resolutions, branch histories, checkpoint/event metadata, UNKNOWN
  gaps and per-state authority/provenance. No uniform temporal spacing or legacy
  R3/R5 merge. Relative engineering time is rejected as historical time.
- Existing globe effect, sphere, camera controls, source/PNG authentication, local
  staging, texture and NEAREST sampling remain in use. Timeline changes do not
  reload the dataset or move the camera. Cesium attribution is positioned above
  the new timeline; original camera and land/ocean controls remain available.

Automated verification, separate from browser inspection:

- `npm test`: **16 PASS, 0 FAIL, 0 SKIP**. Eight existing raster/staging tests plus
  eight temporal tests cover Ma/ka/year conversion, ordering and tie determinism,
  nonuniform exact checkpoints, invalid time and engineering-time rejection,
  unavailable/UNKNOWN and branch/resolution isolation, selected/rendered separation,
  no nearest fallback/interpolation, disabled single-state playback/navigation,
  zoom boundaries and actual UI markup. Existing tests still verify all 64,800
  source cells, seam/orientation, provenance, source/authority rejection and staging.
- `npm run typecheck`: PASS, strict TypeScript 5.9.3 including the new tests and
  original readonly layer contract. An initial readonly test-fixture assignment
  failed checking; it was replaced with a copied invalid fixture. No contract was
  weakened. Final standalone typecheck after the UI-markup test also passed.
- `npm run build`: PASS, verified staging + typecheck + Vite production build,
  1,604 modules. JS 4,182.29 kB, gzip 1,124.20 kB. Existing >500 kB bundle-size
  warning remains disclosed; no build warning was suppressed.
- Rehashed **59 audited sources**, **62 original VIEW-1B export files** and the
  existing five staged T0 assets. All unchanged. Entry preservation inventory
  totals 93 files, including previous visualization reports/contracts/browser
  evidence and the three concurrent INT-3 files; every recorded digest matches.
  All 1,947 initial untracked paths still exist. Broader unrelated output contents
  were not requalified. `VIEW_2T_VERIFICATION.json` records the verification scope.

Manual agent-driven Windows browser verification (not an automated browser suite):

- Built application served at `http://127.0.0.1:4173/` using the actual verified
  VIEW-1B T0 dataset. Source-cell verification remains `64800_SOURCE_CELLS_EXACT`,
  both sampler values 9728/NEAREST, equal radii 6,371,000 m. Only localhost resource
  origins were observed; external resource list and browser warning/error logs
  were empty. No online basemap, ion credentials or scientific network dependency.
- Pointer drag selected an unsupported intermediate age (~104.1 Ma), changing
  selected time and UNAVAILABLE status while preserving the original camera and
  the explicitly labeled last-rendered 210 Ma map. Keyboard End selected 0 ka
  with the same explicit unsupported result. Neither operation created a state.
- At T0, previous/next/Play are disabled. At 0 ka, Previous returns to the existing
  T0 while Next/Play remain disabled. T0 marker selection also returns to T0.
  Time zoom at 0 ka showed [21 Ma, 0 ka]; Previous returned to T0 and recentered
  to [210 Ma, 189 Ma] with the slider representing the exact selected value.
  Full history restored [210 Ma, 0 ka].
- At 390×844, timeline, unavailable/retained labels, slider, marker and zoom controls
  remained reachable without horizontal overflow. Mobile land/ocean hiding showed
  the neutral sphere; restoring it restored the same verified map. Desktop camera
  rotation, zoom-out and tilt changed camera coordinates/pitch; reset restored the
  exact original camera. Temporary viewport override was reset.
- Screenshots and DOM-backed observations: `VIEW_2T_BROWSER/`. Browser assertions
  reconcile selection/rendered times, camera invariance under scrubbing, changed
  camera after navigation and exact reset, disabled controls and source/transport
  status. The production server and deliverable tab remain available locally.

During implementation the zoomed-window checkpoint issue was corrected before
final browser qualification. One CSS append command used a duplicated relative
path and failed without modifying a file; the intended CSS change was then applied
to the correct file and included in the final verified build. No source data or
pre-existing sandbox was removed or repaired. Test cleanup remained restricted to
the staging tests' newly owned temporary directories.

No current blocker for the bounded VIEW-2T foundation. Multiple historical datasets
and multi-state browser playback remain unverified because those inputs do not
exist; no fixture was registered as a real epoch. Future dataset admission/rendering
needs its own reviewed scope and integrity/compatibility qualification. Recommended
next bounded VIEW-2B: read-only cell inspection at the actual rendered epoch,
retaining native value/units, source identity, authority, validity and UNKNOWN;
selected unsupported epochs must not retime inspector values. No numerical gate,
INT-2C STOP, INT-3 Fair regression next action or canonical authority changed.

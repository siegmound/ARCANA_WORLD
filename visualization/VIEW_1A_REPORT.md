# ARCANA WORLD — VIEW-1A (2026-10-14)

Decision: `VIEW1A_READ_ONLY_SOURCE_AUDIT_AND_EXPORT_CONTRACT_READY`.
Location: `WINDOWS_WORKTREE_ONLY`; uncommitted, no push or PR. This is a
visualization preparation result, not a scientific qualification gate.

Entry branch `r6/si1-bandwidth-f2av`, HEAD
`8c75c439ab45a9d4e79930bd506e686e088e151d`, exactly the requested baseline.
Tracked worktree/index initially clean; 649 existing untracked files preserved.
No upstream is configured. Cached `origin/r6/si1-bandwidth-f2av` divergence is
0/0; a read-only live `git ls-remote` verified the same HEAD after the sandbox
DNS attempt failed. No fetch, commit, push, branch or remote change occurred.
The repository AGENTS, required ledger documents, ROADMAP, NEW_CHAT and the four
requested B3/engineering reports were inspected. The separately authorized
VIEW-1A visualization scope leaves the INT-2C numerical STOP boundary in force.

Evidence: `source-lock.json` and `source-inventory.json` pin/audit 59 files,
including all requested documents, all nine B3 files and original R4 (9 files),
INT-1D (9 files) and imported C3 (22 files) bundles. Every inspected file verified
against its pin, including a second post-inspection hash. The B3 artifact
manifest's nine referenced members also matched original byte counts/digests.
No original source/evidence was regenerated or written. Full per-source paths,
SHA256, observed schema/fields/shape/dtype and support metadata are in the JSON
inventory; file identities remain separate from semantic state identities.

| Source | Observed support and interpretation |
|---|---|
| Physical specification | Authorial design document; SPHERE, 6,371,000 m; historical NOT_MATERIALIZED label is not today's payload availability |
| Materialization manifest + physical NPZ | Synthetic authorial initialization, governed DERIVED_AUTHORITY field labels; 14 C-order arrays, each 180×360, uint8/int8/int16/float32/bool; only T0=210 Ma |
| Partition manifest + NPZ | MODEL_DERIVED_FROM_CANONICAL_T0; 64,800 parent faces, vertices float64 [64800,5,2], 1,983 boundary edges, categorical/index integer arrays, lengths float64 in m; only T0 |
| Kinematics JSON | 12 plate records, original JSON numbers, Euler rad/year and deg/Myr, velocities m/year, area m²; STOCHASTIC_CANONICAL_MODEL_REALIZATION; synthetic gauge, only T0; no grid-motion layer |
| B3 evidence | Read-only historical ingest/authority evidence; 14 semantic states including eight UNKNOWN domains; GRID per-cell HistoryStore queries remain unsupported |
| R4 / INT-1D | NONCANONICAL_ENGINEERING; 2 supports each, 73 material-profile nodes, 4 / 9 exact diagnostic samples; source units K, m, s, year and unitless; original JSON-number serialization retained |
| C3 | Verified historical replay evidence for the same R4 case; technical checkpoint closure does not promote scientific authority or produce global spatial/temporal support |

Both external T0 payloads are locally present under
`F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES\r6\`.
Their original full locators are recorded in the source lock. The physical
manifest's relative path would resolve to an absent location from this nested
checkout; the observed external root supplies the existing file, without copying
or modifying it. Explicit relocation remains hash-bound through `--external-root`.

- Geography NPZ SHA256:
  `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`.
- Partition NPZ SHA256:
  `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`.
- Kinematics file SHA256:
  `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2`;
  distinct semantic identity
  `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`.

Geometry checks independently reconcile the spherical area
510,064,471,909,788.25 m², 180×360 south-to-north/west-to-east indexing and all
64,800 closed finite-volume face bounds. Parent plate/crust/boundary categories
match each face. All 1,983 boundary edges match adjacent parent categories and
spherical lengths, including two periodic seam edges. Longitude +180 and -180
map to column 0; terminal polar rows share the polar point. These are geometry
and identity checks, not numerical evolution.

Validity: 14,258 supported land-elevation cells, 50,542 ocean NaNs preserved as
unsupported elevation; no bathymetric depths. The elevation support and synthetic
uncertainty masks match land support. 3,909 grid boundary cells are UNKNOWN, and
both boundary-side support arrays are UNKNOWN on all 1,983 edges. Province -2 is
NOT_APPLICABLE; categorical zero is never globally interpreted as invalid.
Bathymetry is UNKNOWN over ocean; grid motion, Deep, climate and hydrology masks
are UNKNOWN everywhere. B3 also records weak-zone and junction physical semantics
as UNKNOWN. No numerical fields for those domains are proposed or inferred.

R4 exact elapsed times are 0, 484.6791203689449, 969.6005802980742 and 1000 years.
INT-1D's nine exact samples end at 999.9999999999998 years, preserved without
rounding to a new timestamp. The experiments remain distinct and their two
supports are not independent scientific observations. All other times/locations
are unsupported. No interpolation, profile-to-grid field or history reconstruction
is performed by VIEW-1A.

Delivered: a standard-library stdout-only inventory CLI, TypeScript layer
contract, proposed versioned JSON Schema and 74 per-field layer declarations
with separate numerical/imagery slots, plus the Cesium/React/Vite boundary in
README. Every declaration retains identity, units, native shape/type, support,
authority, validity/UNKNOWN and uncertainty rules. Numerical and imagery assets
remain null because no exporter or browser UI was implemented.

Verification: 11 focused unittest cases PASS (all 64,800 coordinate roundtrips,
seam/poles, radius rejection, masks/NaN, SHA/size mismatch, missing external inputs,
authority fail-closed and object-array rejection); local full-source audit exit 0,
VERIFIED. Missing-root audit returns 2/INPUT_UNAVAILABLE without inferred payload
fields; mismatch audit returns 1/FAIL_CLOSED and disables contract checks.
Initial temporary-fixture tests encountered sandbox access errors; the final tests
use in-memory archives/read-only files and pass without temporary filesystem writes.
Cleanup of the two initial sandbox temporary directories remains unverified after
permission-denied cleanup errors; no further outside-repository changes were attempted.
TypeScript syntax parsing via Node's strip-types mode passes; TypeScript static
typechecking, a full JSON Schema validator and Cesium browser runtime remain
unverified (no compiler/validator packages installed). JSON artifacts parse;
final whitespace/diff and original-source rehash checks are recorded in the ledger.

Blockers: no local required T0 payload is missing, but unsupported scientific
domains remain unavailable as numerical layers. B3's HistoryStore GRID query
membership is not replaced by viewer geometry indexing. A reviewed export writer,
asset/mask bindings, browser loader, dependency versions and rendering qualification
are still required. Exact latitude small-circle/polar/seam rendering requires a
dedicated presentation adapter; corner-to-corner geodesic polygons are insufficient.

Next bounded proposal (requires separately reviewed scope): a static T0 export
writer retaining original dtypes/NaN, hashed validity/UNKNOWN assets and exact
source support, with offline schema/hash/mask validation. Scientific NEXT_ACTION
remains STOP. No solver, replay, provider evolution, WORLD_HISTORY constructor/write
or canonical promotion occurred. All work stays within VIEW-1A.

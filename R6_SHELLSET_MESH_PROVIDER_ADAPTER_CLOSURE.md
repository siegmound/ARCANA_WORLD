# R6 ShellSet mesh-provider and adapter closure

**Decision:** `R6_SHELLSET_MESH_ADAPTER_IMPLEMENTED__READY_FOR_AUTHORIAL_SELECTION_AND_MATERIALIZATION`

## Canonical geometry audit

- Manifested parent grid: `180×360`; 64,800 cells, confirmed against the NPZ cell IDs and rings.
- Face arity: 64,080 quads and 720 pole-collapsed triangles.
- Coordinates are closed five-point lat/lon rings. Meridians are great-circle arcs; latitude edges are small-circle arcs.
- Direct triangle reuse is unavailable. A fixed per-cell diagonal produces a closed topology without moving vertices.
- FEG geodesic edges approximate canonical latitude small-circle arcs. Acceptance is based on exact endpoints, topology/ownership preservation, analytic containment within incident cell support, and deviation materially below local support; no arbitrary metric tolerance was introduced.

## Deterministic mesh topology

- Nodes: 64,442; triangles: 128,880; edges: 193,320.
- Edge incidence: `{'2': 193320}`; Euler characteristic `2`; components `1`.
- Outward orientation corrections: 0; zero-area triangles: 0.
- Canonical boundaries: 1,983; junctions: 20; plates: 12.
- Three identical normalized builds: `6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad`.

## Geometry approximation

- Across 1,983 boundary edges, maximum great-circle deviation is 121.296388 m (0.00109084°); mean 57.167128 m, p95 120.631674 m, p99 121.222578 m.
- Maximum normalized deviation: 0.00210734 of local cell scale; endpoint error is zero; affected edges 1276; subdivision required: False.
- Nearest nonincident canonical-boundary clearance lower bound: at least 28778.342 m across the audited edges.
- Chords remain inside an incident canonical cell, preserve boundary topology/plate membership, and do not cross nonincident grid boundaries. The source grid cell is the governing support; no arbitrary acceptance tolerance was introduced.

## Provider and limits

Selected provider is `ARCANA_CANONICAL_GRID_FACE_TRIANGULATION`. Gmsh and CGAL are rejected from the minimum path because no gap is demonstrated. OrbWin remains reference implementation only.
The derived branch registry contains 30 junction-to-junction chains and assigns all 1983 canonical segment IDs exactly once. Registry IDs are deterministic derived IDs, not historical IDs.
The FEG reader/writer round-trip is implemented for the ARCANA-supported subset. ShellSet itself was not run. Global solve uniqueness and iPVRef behavior remain runtime assertions.

- Full-grid TEST_FIXTURE_ONLY normalized FEG SHA-256: `b1d0472603fb6aed2f7df26dfd7eac40ea3d4df909f7cdf8f46f3ce4fa84f96e` (64,442 nodes and 128,880 triangles). Compact fixture round-trip hash: `88cf0ba8f22643eec3c5fdabc131afa15b89a4c78a0510f1145d902e8d1926d1`; that fixture exercises LR and fault records. Neither is a production input.

## Runtime gates and governance

Static mesh/geometry/branch/FEG adapter gates are closed. ShellSet runtime qualification remains unauthorized; authorial physical field and rheology selections remain a separate user-directed stage. No forward interval or `dt` is authorized.

No physical field, ShellSet/OrbData execution, runtime qualification, first interval, or `dt` was created or authorized.

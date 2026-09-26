# R6 pyGPlates deforming-network feasibility (P1)

This is a synthetic, noncanonical feasibility fixture for pyGPlates 1.0.0. It
does not import or adapt canonical R6 geometries or state classes. Its output
is labelled `NONCANONICAL_FEASIBILITY_DIAGNOSTIC` and cannot change scientific
authority registers.

The fixture uses a square on a sphere with four individually identified
boundary sections, plate IDs 101–104, a fixed interior sample, and explicit
finite rotation sequences. IDs for the fixture, sections, plate assignments,
sample locations, and rotation values are specified in source. pyGPlates
internally assigns feature IDs; those IDs are not used as fixture identity or
included in diagnostic output.

`get_point_velocity` is called with an explicit 1 Myr interval, the
`t_plus_delta_t_to_t` convention, centimetres per year, and a 6371 km radius.
`get_point_strain_rate` is reported only as a pyGPlates diagnostic. The 1.0.0
API documents its strain rate as using a 1 Myr interval and the equatorial
Earth radius. This is not an ARCANA strain convention. The triangulation
vertices and triangles are counted without assigning an algorithmic
interpretation in this report. pyGPlates 1.0.0 documentation describes
`NetworkTriangulation` as a Delaunay triangulation; the fixture does not claim
that it is a constrained Delaunay triangulation.

The fixture reconstructs sample points from the resolved snapshot time to one
million years older, solely to exercise the incremental point reconstruction
API. This is a local synthetic query, not ARCANA forward evolution: no `t1`,
canonical time advance, rift progress, or `W_model` is created or selected.

## Run on fair

From the repository root, with the R6 Python environment active:

```bash
PYTHONPATH=src python scripts/r6_pygplates_deforming_network_feasibility.py
```

The executable returns JSON. If the runtime is absent, it prints
`PYGPLATES_RUNTIME_UNAVAILABLE` and exits with status 2. No diagnostic JSON is
written into canonical artifact directories.

Authority remains ARCANA-owned. pyGPlates is only a candidate bounded
numerical/topological solver; its outputs remain noncanonical diagnostics
until separately audited and explicitly governed.

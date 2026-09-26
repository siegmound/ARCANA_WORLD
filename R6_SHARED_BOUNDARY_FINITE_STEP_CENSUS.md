# R6 shared-boundary finite-step census

t0-only evaluation at synthetic 210 Ma; no proposed transition or geometry update was run.

- Segments: 1983
- Status counts: `{"BLOCKED": 1983}`
- t0 component classes: `{"MIXED_CLOSING_SHEAR": 1091, "MIXED_OPENING_SHEAR": 892}`
- Junctions: 20
- Junction status counts: `{"BLOCKED": 20}`

Every segment status is individually recorded in the JSON by its stable boundary ID and blocking reason. The existing rift-progress value is the only opening source of truth and is not advanced. No shortening or slip state is created.

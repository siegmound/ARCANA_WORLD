# Canonical junction membership topology diagnostics V2

Decision: `OVERLAP_DERIVED_PATCH_BOUNDARY_DIRICHLET_INCOMPATIBLE`. Evaluated widths: `[100000, 250000, 500000, 1000000]`.
Port identity is derived from mesh adjacency between the central multi-corridor component and exclusive singleton masks; normal probes are retired.
Bounded dyadic local domains are capped strictly before the next canonical junction. Branch persistence uses three deterministic interior samples per source edge; sample non-detection is `BRANCH_SCAN_NOT_CONVERGED`, not proof of absence. Corner gates precede trace refinement; conflicting Dirichlet data are never averaged.

## W = 100000 m
Status: `INVALID_AT_JUNCTION_GATE`; topology pass 20/20; trace pass 0/20; triangulation 0/20.
## W = 250000 m
Status: `INVALID_AT_JUNCTION_GATE`; topology pass 19/20; trace pass 0/20; triangulation 0/20.
## W = 500000 m
Status: `INVALID_AT_JUNCTION_GATE`; topology pass 18/20; trace pass 0/20; triangulation 0/20.
## W = 1000000 m
Status: `INVALID_AT_JUNCTION_GATE`; topology pass 9/20; trace pass 0/20; triangulation 0/20.

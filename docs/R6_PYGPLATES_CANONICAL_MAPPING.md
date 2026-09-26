# R6 pyGPlates canonical mapping (P2 diagnostic)

This adapter reads the manifested `R6_T0_VECTOR_PLATE_PARTITION.npz` through
the existing R6 external-payload path resolver and cross-checks the existing
shared-boundary junction census. It verifies payload size and SHA-256 before
loading arrays with `allow_pickle=False`. The arrays are treated as read-only.

When pyGPlates is available, the diagnostic constructs geometry candidates
for the 64,800 canonical faces grouped by their 12 plate IDs, all 1,983
positive-length boundary segments, and the 20 source junction points. It does
not create a `TopologicalModel`, resolve topologies, assign rotations, or run
time evolution. The P1 synthetic result establishes generic deforming-network
API capability; it does not assign any of the canonical boundary graph to a
deforming region.

Boundary process class, convergence/divergence law, boundary velocity, strain
semantics, and junction motion/topology semantics remain unbound. Canonical
face geometry uses finite-volume latitude/longitude cell edges, including
parallel small-circle support. pyGPlates geometry candidates are reported
without claiming exact curve-semantic equivalence; no geometry-loss tolerance
has been selected. A completed `PASS` means the inventory and candidate
construction ran. It is not a solver selection or scientific-authority
decision.

On a machine without pyGPlates, the script still validates and reports the
canonical inventory, writes a diagnostic marked `FAIL` with
`PYGPLATES_RUNTIME_UNAVAILABLE`, and exits nonzero. That output is an
environment-specific diagnostic, not a substitute for the Fair run.

Run from the repository root with the R6 Python environment active:

```bash
PYTHONPATH=src python scripts/r6_pygplates_canonical_mapping.py
```

The JSON and Markdown reports are written to the repository root under the
names `R6_PYGPLATES_CANONICAL_MAPPING_REPORT.json` and
`R6_PYGPLATES_CANONICAL_MAPPING_REPORT.md`. Both are explicitly noncanonical.
The diagnostic keeps `canonical_state_changed`, `forward_evolution`,
`dt_first_authorized`, `w_model_selected`, and `rift_advanced` false.

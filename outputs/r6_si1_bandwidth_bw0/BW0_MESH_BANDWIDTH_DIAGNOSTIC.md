# R6 SI1-BW0 Mesh Bandwidth Diagnostic

Decision: `DIAGNOSTIC_ONLY_NO_CANONICAL_OR_RUNTIME_REORDERING`.

This report reads the governed FEG/runtime pair. RCM is an in-memory diagnostic only; neither input was changed and no mechanical solve was run.

## Input and topology

- Branch / HEAD: `r6/si1-bandwidth-bw0` / `477877c0a401bb87621c107e164b1bfee7a27ad2`
- FEG SHA256: `34b81c0df350d3b9a4c7df526c9171c89fe2d44d7e17b8662f5a92a9ee4c40b6` (governed match: `34b81c0df350d3b9a4c7df526c9171c89fe2d44d7e17b8662f5a92a9ee4c40b6`)
- Runtime package SHA256: `2dc83a759d4cdd4851ad57a37fc725841da24f0f2ca4312391283348703d3584` (governed match: `2dc83a759d4cdd4851ad57a37fc725841da24f0f2ca4312391283348703d3584`)
- Nodes / triangles / fault elements: 64,442 / 128,880 / 0
- Unique edges: 193,320; connected components: 1; edges with incidence other than 2: 0
- Edge incidence histogram: `{'2': 193320}`
- Euler characteristic V−E+F: 2; duplicate triangles: 0; duplicate coordinate records: 0.

## ShellSet KSize reproduction and RCM estimate

| Metric | Original FEG IDs | SciPy RCM (in memory) |
|---|---:|---:|
| Maximum node-ID span | 64,440 | 363 |
| nLB / nUB | 128,881 / 128,881 | 727 / 727 |
| nRank | 128,884 | 128,884 |
| nCodiagonals | 128,881 | 727 |
| nKRows | 386,644 | 2,182 |
| Estimated REAL*8 matrix bytes | 398,657,802,368 | 2,249,799,104 |
| Estimated GiB | 371.279 | 2.095 |
| RCM calculation seconds | — | 0.005025 |
| Reduction | — | 99.436% (177.197× smaller) |

The implementation reproduces `KSize`: it widens node rows over every triangle-local pair, calculates lower/upper node bandwidth, doubles for two DOFs, then uses `nCodiagonals=max(nLB,nUB)` and `nKRows=3*nCodiagonals+1`. With `nFl=0`, no fault-element widening is present.

## Maximum-span connections

There are 1 mesh edges at the maximum node-ID difference of 64,440. First records (up to 100):

| Node IDs | Span | Endpoint lon/lat | Angular span (rad) | Triangle IDs | Incidence | Polar guard |
|---|---:|---|---:|---|---:|---|
| [2, 64442] | 64440 | [[-89.9999999999996, 89.50000000000013], [-154.23968671316499, 88.88980982895598]] | 0.0174532925 | [128879, 128880] | 2 | False |

## Geometry and integrity diagnostics

- Longitude range: -180.000000000° to 179.997480802°; latitude range: -89.500000000° to 89.500000000°.
- Nodes exceeding ShellSet's `|latitude| > 89.99°` singularity guard: 0.
- Raw-longitude jumps >180° across unique edges: 595; these are reported as dateline crossings, not treated as topology defects.
- Spherical edge arc range: 0.00030459809–0.0246820564 rad; longest edge [32385, 32746] (157.249 km on a 6371-km reference sphere).
- Spherical triangle area: min 2.65808606e-06 sr; nonpositive 0; nonfinite 0.
- Topology checks show a connected closed triangular sphere (all edge incidences 2 and Euler characteristic 2), with no duplicate triangles/coordinates; therefore the max node-ID span is a numbering/bandwidth issue, not a detected connectivity defect.
- Coordinates use the rigidly rotated runtime frame recorded by the governed manifest; BW0 makes no coordinate transformation.

## Runtime alignment and BW1 recommendation

Runtime records are sequentially bound to node IDs; each record has 51 fields total including the node ID, as required by MOD_ArcanaRuntime's ARCANA_FIELD_COUNT. BW0 did not apply its permutation. Any BW1 must apply a bijective mapping to FEG connectivity and reorder/relabel the runtime records coherently, then refresh hashes and prove inverse-permutation equivalence for all node-bound data.

**BW1 recommendation: `GO` for an isolated, noncanonical permutation/compatibility prototype only.** This recommendation is based on estimated matrix storage reduction, not on solver stability, correctness, compile, MPI runtime, or canonical authority. Ubuntu Fair validation remains necessary.

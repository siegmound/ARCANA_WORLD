# R6 SI1-BW1 Isolated Mesh Reordering Report

Decision: `BLOCKED_BW1` — Isolated derived pair and Fair staging contract are complete, but no preflight-only Fair runner is provided to mechanically enforce immediate termination after KSize; do not launch ShellSet until that guard is independently implemented and verified.

Classification: `NON_CANONICAL_ENGINEERING_REORDERED_INPUT`. This is an input-compatibility and KSize preflight candidate, not a canonical mesh or physical-state change.

- Nodes / triangles / fault elements: 64,442 / 128,880 / 0.
- Runtime record fields including node ID: 51.
- SciPy: 1.18.1.
- Permutation SHA256 (little-endian int64 maps): `544dcadea16cd8097b6c9461b4a50fd16edc41a4aa2d13878268592dd1486475`.

## KSize comparison

| Metric | Original | Reordered |
|---|---:|---:|
| nCodiagonals | 128,881 | 727 |
| nKRows | 386,644 | 2,182 |
| Estimated REAL*8 matrix bytes | 398,657,802,368 | 2,249,799,104 |
| Memory reduction | — | 99.435657% (177.197x) |

## Preservation checks

All node-record text except the node identifier is retained in its source spelling. Triangle element order and local vertex order are unchanged; all node references are remapped. Both derived files pass byte-identical inverse reconstruction.

The derived files are duplicated into the isolated Fair staging `INPUT` directory under ShellSet's expected filenames. The accompanying contract is deliberately preflight-only. No compile, MPI, ShellSet, OrbData, mechanics, or solve was executed on Windows.

Original governed FEG/runtime files and WORLD_HISTORY were not modified. RCM changes only node numbering/order and is not a scientific or canonical authority decision.

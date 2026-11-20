# ARCANA R6 — FAIR moving 3D source contact diagnostic and parallelism assessment

**Date:** 2026-11-20. **FAIR tested source HEAD:** `d510a13d60157b86ddd53165c248a6072c65f265`.
**Reported Python tests:** 40/40 PASS (0.70 s).
**Driver:** `PASS_SOURCE_MOVING_3D_CONTACT_GEOMETRY_DIAGNOSTIC__CONTACT_PHYSICS_OPEN`.
**Scientific decision:** `PASS_OBJECTIVE_MOVING_POINT_PAIR_GEOMETRY_DIAGNOSTIC_AND_SERIAL_PARALLEL_PARITY__BLOCK_MOVING_3D_CONTACT_CLOSURE`.

The FAIR operator supplied a terminal summary. **Full remote FAIR REPORT.json and MANIFEST.json were not independently read here.** The receipt JSON is based on that summary.

## Genuine-source scope and data meaning

The previous 36/36 source regional KKT run used source-original plates 5:8 and 5:8:11, **13** and **39** distinct pair-node contact links respectively. The latter has real triple-junction parent node `34587`, with four source Euler initially closing links. Its `gap_T0` is a **time integral of the relative velocity projected onto a fixed T0 normal**, not a geometric separation between current material surfaces.

This new diagnostic reconstructs moving material points from **exact source Euler SO(3) rotation plus the KKT nonrigid residual**, explicitly subtracting the previously integrated rigid Euler component to avoid double counting. It uses source-authenticated boundary edge ownership to derive a current 3D edge normal, then measures the signed **point-pair** separation along that normal. This is more informative than the fixed-normal gap, but **not** a complete closest-feature edge-edge / face-face nonpenetration test. The 3D geometric normal is **not yet used to constrain the trajectory**.

## Critical 16×16 discrepancy

| Checkpoint (model years) | Min signed 3D point-pair gap, all 39 links | Min signed 3D gap among 4 T0-KKT active links | Maximum absolute geometric minus T0 gap |
|---|---:|---:|---:|
| 100 | 0.5281696736 m | **1.0739293265 m** | 2.1654363371 m |
| 500 | 3.1816483317 m | **5.4153964325 m** | 10.9937281283 m |
| 1000 | 7.7444286377 m | **10.9088848062 m** | **22.3600111404 m** |

No signed *point-pair* geometric gap below **−1 µm** was reported at any of these three checkpoints, but this must NOT be upgraded into full evolving 3D nonpenetration. All four links remain **active in the old T0 KKT reaction set**, while their new 3D geometric gap is strictly positive. Consequently, **the old T0-normal reactions do not satisfy complementarity for the new geometric gap**: `lambda_T0 > 0` together with `gap_3D > 0` for these links.

The reconstructed separated-point reaction couple diagnostic rises from **0.5475** at 100 years to **10.11236** at 1000 years in arbitrary normalized units. This signals potential mismatch of reaction application points/lever arms; it is NOT a proven physical moment/torque or a numerical stability failure.

The maximum current edge normal angle relative to the transported source normal is **0.48521541774 rad** at 100y and **0.48521541812 rad** at 1000y (~27.8 degrees), nearly constant despite 10× longer motion. This invites a **T0 baseline consistency test**: compare how the triangle-centroid source normal and edge-derived normal were defined *even before moving*, rather than attributing ~0.485 rad exclusively to rotation or local deformation. This is a hypothesis, not yet demonstrated.

## 8×8 opening-only control

| Checkpoint | Min signed 3D gap | Max signed 3D gap | Max |3D−T0 gap| |
|---|---:|---:|---:|
| 100y | 11.5767161859 m | 15.7461741705 m | 1.3895798248 m |
| 500y | 57.8834166432 m | 78.7308799416 m | 6.9478982251 m |
| 1000y | 115.7664225681 m | 157.4617825976 m | 13.8957942024 m |

All **13** source pair-node links remain nonreactive; the artificial separated-point reaction couple is **0**. The maximum normal-angle diagnostic is about **0.47673246 rad** and similarly almost constant between horizons. There are no reported signed negative point-pair gaps below −1 µm at the sampled checkpoints.

## Serial vs two-process parallel

| Performance on FAIR | Measured |
|---|---:|
| Workers | 2 (independent 8×8 / 16×16) |
| Exact numerical SHA256 parity against serial rerun | **PASS**, both regions |
| Serial region work elapsed | **0.5073307604 s** |
| Two-process parallel region work elapsed | **0.6903865226 s** |
| Serial / parallel speedup | **0.7348503248×** |
| Parallel slower than serial | **36.08%** |
| Full driver wall time incl. validation/replay | **2.0959337950 s** |

There is **no speedup for these two small regional jobs**; process spawn and communication overhead plausibly dominates. One measurement is not a definitive scale-up model. Default to one worker for this small scope; keep two-worker execution as a deterministic benchmark/regression. Avoid nested BLAS threads.

A better parallelism candidate is genuine **full 12-plate source-element FEM assembly** (previously ~22.94 s serial), or larger independent material scenarios, with deterministic sparse reduction, source owner records and measured RSS/CPU cost. Do **not** parallelize sequential dependent steps of one stateful contact evolution without a validated domain-decomposition algorithm. No GPU acceleration result has been established.

## Next gate and fail-closed constraints

1. At exactly **t=0**, calculate source pair-normal angular mismatch **per authentic boundary segment and plate pair**, before applying deformation.
2. Establish geometric contact features: point-segment/edge-edge (and, if applicable, face-face) nearest points; orient the signed separation consistently in a common Cartesian frame, with source IDs.
3. Validate objective SO(3) gap and **analytical / finite-difference gap Jacobians**, including at parent triple node 34587 and degeneracies.
4. Replace the fixed-T0 Jacobian in the solver with an updated geometric Jacobian/normal and constraint on actual defined current signed gap; verify complementarity **on that same gap** and pair-force/torque virtual work, with source-parametric synthetic material only.
5. Require regional manufactured 100/500/1000-year restart, timestep refinement and source SHA PASS before considering global 12-plate contact runs.
6. If parallel assembly is undertaken, measure parallel/serial timings and peak parent plus worker RSS, not just CSR storage, and demand deterministic source ownership and reduction.

```text
GLOBAL_ENGINEERING_G1_G2_P1_1000Y=PASS_FAIR_29_29
REGIONAL_T0_KKT_TIME=PASS_FAIR_36_36
REGIONAL_MOVING_3D_POINT_PAIR_DIAGNOSTIC=PASS_FAIR_40_40
SERIAL_PARALLEL_SHA256_PARITY=PASS
REGIONAL_2WORKERS_WALL_SPEEDUP=0.73485X
MOVING_3D_CONTACT_KKT_COMPLEMENTARITY=NOT_QUALIFIED
FULL_3D_CONTACT_FACE_EDGE_NONPENETRATION=NOT_QUALIFIED
D_024=ACTIVE
physical_T1=null
```

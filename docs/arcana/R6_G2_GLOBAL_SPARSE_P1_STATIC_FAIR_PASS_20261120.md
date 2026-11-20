# ARCANA R6 — FAIR genuine spherical P1 sparse G2 static global operator PASS

**FAIR tested HEAD:** `313b2f40ed7066cbd1b424b7237551d4d2b39d78`, **2026-11-20**.
**Decision:** `PASS_REGIONAL_DENSE_SPARSE_P1_PARITY_AND_12_PLATE_GLOBAL_STATIC_ENGINEERING__PHYSICS_OPEN`.

This register relies on **operator-terminal evidence**. The raw FAIR report
and manifest were not independently downloaded into the GitHub authoring environment.

## Automated code checks

```text
HEAD 313b2f40ed7066cbd1b424b7237551d4d2b39d78
28 passed in 0.41s
```

## Exact regional P1 dense/sparse parity

| Quantity | 8×8 / 162 DOFs | 16×16 / 578 DOFs |
|---|---:|---:|
| Relative `Kx` discrepancy | 1.6363342437298538e-16 | 2.056827514811535e-16 |
| Reciprocal virtual-work discrepancy | 1.0870632738612268e-16 | 5.233091205951177e-16 |
| Max relative matrix-entry discrepancy | 1.8188823171182822e-16 | 3.3110155069960594e-16 |
| CSR nonzeros | 1988 | 7556 |
| CSR byte size | 24508 | 92988 |

These values show faithful sparse representation of the original **faceted**
P1 elementary membrane. **Not** smooth covariant ShellSet parity,
fixed-extent spatial convergence, or real creep law validation.

## Authentic 12-plate source-global P1 assembled and solved

- 64,442 distinct source parent nodes; **66,435 plate-local material views**,
  **128,880 triangles**, **132,870 tangential EN mechanical DOFs**.
- CSR: **1,828,144 nonzeros**, **22,469,212 bytes**; this measures the
  matrix only, not peak process RSS or memory required for a physical
  nonlinear solver.
- Maximum relative asymmetry **4.245971308495533e-18**.
- Piecewise-facet area **510032102866499.2 m²** versus spherical
  area **510064471909832.7 m²** (relative deficit
  6.346069000e-5).
- Genuine source plate-Euler rigid-rotation mode residual
  **1.2767850120272625e-17**, near machine precision. A separate
  manufactured nonrigid tangent test produces **1.9057136036085815e-4**,
  showing the operator responds to deforming modes.
- Preconditioned CG on manufactured static `(I+K/C)v=g` converges
  **66 iterations**, relative residual **8.972450618882282e-9**,
  manufactured work residual **4.518189319573849e-16**.
- Static target RMS speed **0.05376418193655341 m/model year**;
  synthetic coupled speed **0.053763970659344976 m/model year**,
  relative field correction `||v-g||/||g|| = 0.00027974002653868363`
  (approximately 0.027974%). Small correction is explained by
  independent rigid plate views and small manufactured nonrigid
  target; it **does not** mean real global lithosphere is undeformed.

Timings: **0.30235 s** regional parity, **22.93879 s** global sparse P1
assembly, **0.10558 s** static CG solve, **23.40236 s** end-to-end.
Assemblage dominates. Source target shapes were checked against
sealed T0 and no cross-plate P1 stiffness entries were allowed.

## Forward action

The sparse matrix is finally the **same implemented 6×6 faceted
spherical P1 constitutive tangent as regional G2/G3 engineering**,
rather than the earlier graph surrogate. Before any long-term
global time stepping:

1. Preserve all 12 plate-local material views and make explicit a
   source-verified contact policy: baseline **unwelded**
   (the present run), then separate synthetic welded, slip or
   contact-with-opening variants. Never infer actual fault dynamics
   from an Euler weighted-average.
2. Define a static T0 frame and the matching drive and displacement
   coordinates so rotating rigid plates do not accidentally generate
   numerical elastic stress from frame inconsistency.
3. Reuse the sparse P1 tangent for an ENGINEERING_ONLY 100/1000-year
   global Kelvin–Voigt time integration with checkpoints,
   restart, dt halving, residual/work and area diagnostics. Refuse
   solutions if numerical error/conditioning grows.
4. Benchmark global assembly memory, subsequent CG cost and actual
   runtime across checkpoints, and preserve all source SHA.
5. Do not call any such engineered output a geological prediction:
   real cold/wet/pressure-dependent G2 laws, G3 mantle traction,
   normal support, GPE, fault contact, material/energy transport,
   event evolution and authorial rock ratification remain open.

```text
G2_GLOBAL_REAL_SPHERICAL_P1_STATIC=PASS_FAIR_OPERATOR_28_28
GLOBAL_SPARSE_CSR_NNZ=1828144
GLOBAL_CG_ITERATIONS=66
GLOBAL_MANUFACTURED_100_1000Y=NOT_RUN
REAL_G2_MATERIAL_LAW=UNKNOWN
REAL_G3_PHYSICAL_FORCING=UNKNOWN
D_024=ACTIVE
physical_T1=null
```

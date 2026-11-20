# ARCANA R6 — FAIR regional unilateral time complementarity PASS

**Date:** 2026-11-20. **FAIR tested commit:** `4ec52f3a3e8815ccf495a8611b17bef994f6f592`.
**Operator reported:** `PASS_SOURCE_REGIONAL_UNILATERAL_COMPLEMENTARITY_TIME__MOVING_GEOMETRY_OPEN`. **36/36 pytest PASS (1.34 s)**.

The original FAIR `REPORT.json` / `MANIFEST.json` have not been independently fetched into the authoring environment. This adjudication preserves the exact operator-visible numbers and does not claim independent reruns.

## Scientific milestone and exact restriction

Previous source-verified finite normal penalty still left **4/4** large-region contact links with negative normal velocity after the STATIC solve. The next driver replaces that approximate penalty with a normalized primal-dual nonnegative KKT solve and checks **all time steps** using genuine regional source-identified plate-pair contact links.

**What PASS establishes:** `gap_n >= 0` to floating point error, `lambda_n >= 0`, and `gap_n * lambda_n ≈ 0` for the *linearized, fixed-T0-normal gap variable*. It **does not** establish actual minimum 3D physical surface distance, evolving collision topology, or a qualified natural fault law. K is the constructed source P1 tangent, not ARCANA temperature/water-dependent constitutive physics.

## Source inventory

| Source | 8×8 | 16×16 |
|---|---:|---:|
| Plates | 5,8 | 5,8,11 |
| Real parent nodes | 81 | 289 |
| Source contact edges | 12 | 36 |
| Plate-pair-node links | 13 | 39 |
| Independent plate-local material views | 94 | 327 |
| EN mechanical DOFs | 188 | 654 |
| Source Euler initially closing links | 0 | 4 |
| Source triple junction | none | parent node 34587 |

## Reported 100 and 1000 model-year results

| Quantity | 8×8 at 100 y | 8×8 at 1000 y | 16×16 at 100 y | 16×16 at 1000 y |
|---|---:|---:|---:|---:|
| Maximum EN material displacement (m) | 11.9650660808 | 119.6506608084 | 12.3526457998 | 123.5264579985 |
| Minimum fixed-source normal gap (m) | 11.5371418905 | 115.3714189049 | -2.421673972e-15 | -3.674838212e-14 |
| Maximum fixed-source normal gap (m) | 14.3833294428 | 143.8332944279 | 14.3832393400 | 143.8155199659 |
| Active KKT link reactions | 0 | 0 | 4 | 4 |
| Negative source normal rates at checkpoint | 0 | 0 | 0 | 0 |
| dt5-vs-dt1 max EN displacement error (m) | 2.664535259e-14 | 1.548983164e-12 | 0.00468312192 | 0.02157129106 |
| dt10-vs-dt1 max EN displacement error (m) | 2.842170943e-14 | 1.662670002e-12 | 0.01048111104 | 0.04847480200 |

Across the annual dt1 run:
- 8×8 maximum relative force residual **6.884280594676643e-16**; maximum scaled complementarity **0.0**; minimum gap over run **0.11537141890493016 m**; maximum normalized reaction **0**.
- 16×16 maximum relative force residual **7.103269307344319e-16**, maximum scaled complementarity **4.436305020138318e-17**, minimum gap over all steps **-4.8253068207770866e-14 m**, maximum normalized reaction **0.1190766823562935**.
- **500+500 restart discrepancy = 0.0 m** at both scales.
- For 16×16 at 1000y, the dt10 error is **0.03924%** of reported maximum displacement; dt10/dt5 error ≈**2.247**. This is compatible with first-order time integration, not independent analytic convergence order.
- In 8×8, dt discretization differences ≲1.7e-12m, close to floating-point roundoff; no meaningful convergence order is extractable.

The negative gaps in 16×16 are **~10^-14 m** and hence consistent with numerical error inside the linearized constraint tolerance, not material interpenetration at the model's precision. The 100 and 1000-year active counts are both 4; per-link activation histories would require examining the full FAIR report (the summary omits detailed step traces).

## Critical geometric gate still open

The reference `gap` is computed by integrating `J_T0 v dt` in the initial source East/North basis, with a fixed tangent stiffness and a fixed source contact-normal direction. It is **not** recomputed from rotated/deformed 3D surface geometry. Even very large positive values (up to **143.8155 m** at 1000y in 16×16) have not been independently validated against the true distance between the evolving plate-boundary surfaces. Physically, paired source nodes start coincident at T0 and require an independently defined contact geometry and thickness/ownership model.

Hence the correct release decision is **`PASS_REGIONAL_LINEARIZED_UNILATERAL_KKT__MOVING_GEOMETRY_OPEN`**, not physical contact closure or canonical geodynamics.

## Next engineering experiment

Source-bound **objective moving-geometry gap verification**:
1. Preserve real `R6BND-T0-` source edge/triangle ownership and the source triple-junction node 34587;
2. Construct explicitly declared finite Euler rotations, moving tangential bases and plate-local material point trajectories;
3. Define and validate a signed 3D geometric contact gap and updated normals in one objective Cartesian frame; compare it with `J_T0` integration, including the active 4/39 links;
4. Check actual geometric nonpenetration and pairwise action-reaction, torque, contact work, restart and temporal discretization;
5. Only if regional geometry closes use the same P1 topology for global synthetic moving contact, before ever considering calibrated G2/G3/G4 and canonical T1.

```text
PREVIOUS_SOURCE_STATIC_CONTACT_SO3=PASS_FAIR_32_OF_32
SOURCE_REGIONAL_UNILATERAL_KKT_TIME=PASS_FAIR_36_OF_36
SOURCE_GEOMETRIC_3D_CONTACT_GAP_AND_UPDATED_NORMALS=OPEN
SOURCE_GLOBAL_DYNAMIC_CONTACT=NOT_RUN
REAL_G2_G3_MATERIAL_AND_FORCE=UNQUALIFIED
physical_T1=null
D_024=ACTIVE
```

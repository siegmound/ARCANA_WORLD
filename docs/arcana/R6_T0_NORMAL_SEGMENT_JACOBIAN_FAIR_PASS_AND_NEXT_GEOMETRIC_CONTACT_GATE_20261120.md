# ARCANA R6 — FAIR T0 normals, moving 3D nearest-segment SO(3)/Jacobian: PASS diagnostic

**Date:** 2026-11-20. **FAIR source commit:** `28bc02c49d86b15dc9dae3388b66202ae4d8beb4`.

**Reported driver:** `PASS_SOURCE_T0_CONTACT_NORMAL_AND_MOVING_3D_EDGE_JACOBIAN_DIAGNOSTIC__GEOMETRIC_KKT_OPEN`, exit code 0, 2.4125 s. The operator-provided terminal excerpt includes the manifest status and `REPORT.json` SHA256 `f8747af7f62df89039c7ec641b8c64917cf7c52cb30001058b17d6fed89a2a04`. **The full FAIR REPORT/MANIFEST were not independently fetched; the excerpt starts mid-JSON and does not show the pytest headline, so 45/45 must not be asserted from it.** See the operator receipt JSON beside the driver.

## Verified in visible FAIR excerpt

- Previous near-parallel SO(3) signed feature error `4.876e-7 m` no longer blocks the driver. Across six visible checkpoint records, maximum absolute rigid SO(3) error of point-pair signed gap `9.161e-10 m`, unsigned segment distance `1.063e-9 m`, signed nearest-segment projection `9.509e-10 m`, all below the **unchanged** `1e-7 m` gate.
- 16x16 original T0 centroid-derived versus edge-derived max angle is `0.4852154177400637 rad`, confirming the large normal mismatch already exists at source time T0. It is not solely Euler drift.
- All displayed finite-difference Jacobian refinement discrepancies are small: maximum visible `2.837e-9`, below prescribed `3e-4`; the diagnostic derivative is not a full virtual-work contact Jacobian.
- Original 16x16 36 source edges; triple-junction source parent `34587`; four previous **T0-model** KKT-active links remain **geometrically separated**: minimum reconstructed current point-pair gap `1.073929, 5.415396, 10.908885 m` at 100/500/1000 model years.
- In 16x16 the **signed nearest-segment projection** has 6/7/5 negative feature values (<−1 μm) at years 100/500/1000; minimum `−0.668775, −3.037951, −5.601532 m`, respectively. This diagnostic is NOT a physical separating-surface gap. Do not infer rock interpenetration from these projections alone.
- The 8x8 source domain is opening-only, previous T0 KKT has zero active reactions and visible later horizons reproduce the earlier point-pair gaps. No physical reaction law was run.

## Decision

`PASS_ENGINEERING_SOURCE_T0_NORMAL_SEGMENT_JACOBIAN_DIAGNOSTIC__PHYSICAL_CONTACT_STILL_OPEN`.

The objective nearest-segment diagnostic and source-bound point-pair Jacobian may support the NEXT **geometrically consistent contact-feature contract**, but they **cannot serve unchanged as a signed Signorini gap**. In particular, an endpoint witness, nearly-parallel nonunique closest-point set, or feature switching can make `(closest_q−closest_p)·n` unsuitable for smooth unilateral complementarity. The same *signed gap functional* must supply state, derivative/Jacobian, and reaction/virtual work; prove its objectivity and contact sign before any nonlinear KKT qualification.

## Next scientific gate (design-first; not yet implemented)

**Name:** `R6_G2_UPDATED_GEOMETRY_CONTACT_FEATURE_ADMISSIBILITY_GATE`.

1. Preserve original FEG/PRE, SHA pins, R6BND-T0 IDs, plate owners, and triple node 34587. Distinguish current source-edge contact candidate from physical solid-rock contact. Never manufacture missing source faces or loads.
2. Build explicit candidate/witness inventory for original paired boundary edges: node-edge, edge-edge interior, endpoint-endpoint, nearly-parallel feature degeneracy, and triple-junction coupling; record contact topology and witness selection, including when it changes.
3. Define an **admissible oriented gap** `g(q)` only on feature configurations with a justified separating normal; otherwise return AMBIGUOUS/NOT_QUALIFIED, not an invented signed value. Preserve unsigned closest-segment distance as separate diagnostic.
4. Numerically verify the *same* gap's consistent two-sided Jacobian, SO(3) objectivity, correct equal-opposite force application, virtual work / moment balance and finite-feature transitions. Check independent analytic manufactured cases, opening, closing, grazing, parallel and near-parallel, and arbitrary rigid rotations. No relaxation of `1e-7m` existing SO(3) gate.
5. Only on admissible features, attempt **manufactured ENGINEERING_ONLY** geometrically updated unilateral KKT solve with `g>=0`, `λ>=0`, `λ*g≈0`, dt refinement, energy/work, 500+500 restart, and all-step/source replay on 8x8 and 16x16; no G3 natural traction, no physics T1.
6. Block physical contact qualification on a failure or ambiguity; no `physical_T1`, `D-024` remains active. Preserve tiny regional execution serial until global P1 element-assembly benchmarking proves parallel benefit.

The goal remains physically governed, high-resolution replayable WorldSim history, not promotion of numerical surrogate contact to a validated geological model.

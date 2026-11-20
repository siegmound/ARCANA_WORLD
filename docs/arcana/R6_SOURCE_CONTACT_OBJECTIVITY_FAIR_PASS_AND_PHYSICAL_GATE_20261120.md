# ARCANA R6 — FAIR source-contact and SO(3) element-objectivity numerical PASS

**Date:** 2026-11-20. **Tested source HEAD:** `2da20adf7637fc4a325bd2d3239143f41c6027ca`.
**Reported status:** `PASS_SOURCE_REGIONAL_CONTACT_POLICY_AND_FINITE_ROTATION_OBJECTIVITY__PHYSICS_OPEN`.
**Test suite:** 32 passed / 0 failed in 0.88 seconds.

This evidence is transcribed from the user's **FAIR terminal output**;
the original FAIR `REPORT.json` and `MANIFEST.json` were
**not independently fetched** by the authoring environment.
Detailed original operator-visible metrics are in the companion JSON file.

## Source-keyed topology

| Metric | 8×8 (5,8) | 16×16 (5,8,11) |
|---|---:|---:|
| Parent nodes / source triangles | 81 / 128 | 289 / 512 |
| Authenticated source contact edges | 12 | 36 |
| Parent nodes on a source contact | 13 | 37 |
| Pair-node links | 13 | 39 |
| Plate-local material views / EN DOFs | 94 / 188 | 327 / 654 |
| Predicted Euler closing pair-node links | 0 | 4 |
| Predicted Euler opening pair-node links | 13 | 35 |
| Triple junction original parent node | None | 34587 |
| Objective SO(3) element-frame parity max | 4.354764094313804e-14 | 4.7497799392329336e-14 |
| SO(3) element test instances | 18 | 18 |

The 16×16 region truly includes all three original source
contact plate pairs **5:8**, **5:11**, **8:11**. At the
triple-junction parent node there are pair-specific plate
contacts, not one arbitrarily welded parent node.

## Three different *static* manufactured contact policies

| Indicator | 8×8 unwelded | 8×8 welded penalty | 8×8 normal-only | 16×16 unwelded | 16×16 welded penalty | 16×16 normal-only |
|---|---:|---:|---:|---:|---:|---:|
| Active links | 0 | 13 | 0 | 0 | 39 | 4 |
| CG iterations | 32 | 75 | 32 | 35 | 92 | 63 |
| Max relative contact speed (m/model-year) | 0.15766438 | 0.00410167 | 0.15766438 | 0.15766438 | 0.00434258 | 0.15766380 |
| Relative velocity correction to G1 | ~0 | 0.44203139 | ~0 | ~0 | 0.33181178 | 0.04266686 |
| Closing links **after** solve | 0 | 0 | 0 | 4 | 4 | 4 |
| Maximum relative force residual | 7.358e-11 | 6.173e-11 | 7.358e-11 | 5.174e-11 | 8.446e-11 | 8.048e-11 |
| Virtual-work identity error | 3.378e-16 | 2.475e-15 | 3.378e-16 | 4.144e-16 | 9.797e-16 | 2.279e-15 |

The **welded penalty** reduces the worst relative
source-contact velocity by factors **38.44×**
(8×8) and **36.31×**
(16×16), but is a **finite velocity penalty**, not exact
welding. Synthetic P1 internal work under the welded
policy grows to ~7.0223e24 and ~1.6179e25 in these
artificial normalized equations, versus a tiny near-rigid
source Euler P1 work under unwelded motion. This is
**constructed work**, not measured tectonic force or joules.

**Critical physical blocker:** in 16×16 the
`CLOSING_NORMAL_ONLY` artificial solver activates 4
closing links, but the report still shows **4 closing
relative-velocity links after the solve**.
Even the artificial full welded penalty leaves 4
closing signs. Neither test enforces a true
nonpenetration condition. The report does *not*
include each active link's final normal rate or
gap. The largest domain-wide velocity difference may
belong to an opening contact, and cannot substitute
for active-pair penetration/gap reporting.

In 8×8, all Euler contact pairs open and
the normal-only policy correctly becomes identical
to the unwelded baseline (zero active constraints).
That is a legitimate **zero-interaction control**,
not evidence of any realistic fault force.

## Frame objectivity and limits

Six genuine contact-adjacent source facets per extent
were tested under the original Euler rotations at model
years **100 and 1000**, plus a synthetic finite rotation
of norm ~0.734915 rad. The Frobenius parity errors
are ~4e-14. The **implemented faceted P1 tangent**
transforms correctly under the tested SO(3) rotations.
This is **element-level objectivity**, not a
deforming/rotating global FEM with transport of
stress, updated contact normals, actual fracture or
geologically valid work along trajectories.

**No time evolution of contact stress or opening/closing
was executed**; the 100/1000 years describe rotation
test inputs, not the evolution of the three contact
policies. No production HistoryStore or T1 updated.

## Next gated experiment (not executed)

1. On true source parent edges, **record every** closing
   link with source parent node, plate pair, original
   boundary ID and computed normal/tangent at both
   t0 and postsolve. Quantify final normal velocity
   *on active links*, not only a domain maximum.
2. Design an independently verifiable, fully
   **ENGINEERING_ONLY** unilateral normal-contact
   algorithm that either enforces a feasible no-
   penetration state, or clearly proves when the
   chosen global Euler boundary velocities make
   the constraints infeasible. Require `gap >= 0`,
   reaction normal sign and complementarity. No
   made-up physical friction coefficients or
   actual G3 mantle force.
3. In a co-rotating 3D objective geometry update,
   verify pairwise traction action/reaction,
   full Cartesian force and torque balance, contact
   virtual work, restart and dt sensitivity; begin
   regionally with source 5:8, 5:8:11.
4. Only after such **regional** contact and geometry
   gates pass, extend the test to real global
   12-plate P1 and a **manufactured** 100/1000-year
   time integration. Real physical G2/G3/G4
   remains separate and production unauthorized.

```text
REGIONAL_CONTACT_TOPOLOGY=PASS
REGIONAL_SYNTHETIC_STATIC_FORCE_WORK=PASS
REGIONAL_SO3_ELEMENT_OBJECTIVITY=PASS
EXACT_UNILATERAL_NO_PENETRATION=NOT_QUALIFIED
REGIONAL_DYNAMIC_CONTACTS=NOT_EXECUTED
GLOBAL_DYNAMIC_CONTACTS=NOT_EXECUTED
PHYSICAL_SOLVER_RUNS=0
physical_T1=null
D_024=ACTIVE
```

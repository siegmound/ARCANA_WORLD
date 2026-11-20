# ARCANA R6 — G1↔G2 manufactured regional 100/1000-year FAIR PASS

**Date:** 2026-11-20. **FAIR tested commit:** `ea908ad3387892911d866e4836f586f6b6b3c4a7`.
**Decision:** `PASS_G1_G2_MANUFACTURED_TWO_WAY_FEEDBACK__REAL_PHYSICS_OPEN`.

## Operator-reported FAIR evidence

The Linux FAIR operator fetched and checked out the **exact** source commit,
then ran the specified test bundle and manufactured regional driver:

```text
HEAD ea908ad3387892911d866e4836f586f6b6b3c4a7
....................................... [100%]
39 passed in 0.39s
status: PASS_G1_G2_MANUFACTURED_TWO_WAY_FEEDBACK__REAL_PHYSICS_OPEN
physical_solver_runs: 0
physical_T1: null
```

Raw FAIR `REPORT.json`/`MANIFEST.json` have **not been independently
retrieved** into the GitHub authoring environment. Detailed numbers below
are copied from the operator's terminal, not a second run.

### 100 and 1000 years (source-keyed regional comparisons)

| Indicator | 8×8 (plates 5/8) | 16×16 (plates 5/8/11) |
|---|---:|---:|
| Nodes / source triangles / mechanical DOF | 81 / 128 / 162 | 289 / 512 / 578 |
| 100y maximum displacement, m | 11.0183582215 | 12.1292156689 |
| 1000y maximum displacement, m | 104.6758848839 | 117.3120962423 |
| 1000y G1 target RMS velocity, m/year | 0.06527641628 | 0.06484436267 |
| 1000y coupled RMS velocity, m/year | 0.04998021590 | 0.05745406002 |
| 1000y coupled-minus-target RMS velocity, m/year | 0.02618434366 | 0.01599653816 |
| Relative max implicit balance | 5.801227875e-17 | 5.324199544e-17 |
| Max backward Euler energy identity error | 5.020690835e-14 | 2.557946766e-14 |
| 500+500 restart error, m | 0 | 6.938893904e-18 |
| 1000y maximum absolute area Jacobian change, fraction | 0.0003118934694 | 0.0003122886520 |
| 1000y manufactured mass proxy residual | 0 | 1.559951743e-16 |
| 1000y max error dt5 vs dt1, m | 0.05411143958 | 0.04284066823 |
| 1000y max error dt10 vs dt1, m | 0.12156346333 | 0.09620544633 |

Both domains passed all in-code numerical acceptance gates.
Time-step errors relative to 1y reduce by ratios ~2.247 (8×8)
and ~2.246 (16×16) on changing 10-year to 5-year steps.
This is **compatible with** first-order implicit integration; it
does not independently establish temporal convergence order
because the 1-year reference is not an exact solution.

Feedback at 1000 years is nontrivial: RMS difference from Euler
target is ~40.1% (8×8) and ~24.7% (16×16) of the Euler target RMS.
Note these are **ratios of RMS magnitudes** (not pointwise slowdown
fractions). Synthetic parameters determine these effects.

The maximum 1000y relative area change ~0.0312% is much smaller
than the acceptance threshold (5%); it does **not** establish
physical strain/fracture model validity. The reported mass residual
is approximately zero **by construction** under
`h_new=h_T0/J_area`, and is not an independent mass transport test.

**Important distinction:** Extents 8×8 and 16×16 are different
geographic domains with distinct source plate membership. Their
~12.636m displacement difference at 1000y does **not** establish
spatial mesh convergence. Source node `34587` is present in both;
the 8×8 crop contains plate 5/8 only, so its presence alone is
NOT evidence of a 3-plate mechanical junction in the 8×8 mesh.

## What this numerical pass *actually* establishes

The **invented** Kelvin–Voigt + P1 depth-integrated membrane has
a numerically consistent discrete feedback from plate-Euler
driving to the corrected velocity field and its displacement
memory, over 100 and 1000 model years. SPD/PSD linear algebra,
implicit balance, energy identity, checkpoint restart and stable
source-geometry area ratios passed the configured gates.

Original G1 Euler source and G2 T0 PRE source were not changed
by the driver; the code includes source SHA recheck. Each scale
reports **1300 primary modal updates + 1300 modal updates repeated
for restart**, plus `physical_solver_runs=0`.
That count concerns an *engineering calculation*, not a physical
T1 solver, and is not the same as Newton iterations.

However:
- Material viscosities `1e20/1e21 Pa s`, time constant 200y and
  driving dashpot multiplier 0.5 are **made up numerical hypotheses**
  without ARCANA petrology/calibration.
- Euler target at multi-plate nodes is a weighted incident-triangle
  mean with a synthetic welded DOF, **not actual fault/contact physics**.
- The implementation uses initial-geometry, faceted P1 tangent and
  a synthetic drive. **No real G3 cut traction, mantle flow,
  basal normal pressure or GPE is solved.**
- G2 is **linearized viscoelastic**, not the fully nonlinear
  temperature/pressure/water-dependent brittle–ductile rock law;
  T0 thermal columns are passive. G4 physical transport is absent.
- Sufficient evidence for real physical T1, canonical history,
  geological landform/resource shifts, tectonic events or
  full-shell dynamic simulation does **not** follow from PASS.

## Next experiment: scientific numerical robustness, not arbitrary centuries

First test sensitivity to the invented viscosity contrast,
`tau`, and drive dashpot, with explicit manufactured thresholds.
Then test mesh refinements **on the same physical extent**, not
8×8 crop versus larger 16×16 crop. Include step refinement below
1y, objective force/torque/work under rotated frames, contact
sliding/opening versus welded constraints, and nontrivial separate
layer mass/energy evolution with independent diagnostics.
Only after software robustness is established revisit source-qualified
G2 materials, water and real G3 force/pressure closure.

```text
G1_G2_PASSIVE_100_1000_FAIR=PASS_32_32
G1_G2_MANUFACTURED_TWO_WAY_FAIR=PASS_39_39
G2_PHYSICAL_CONSTITUTIVE_CALIBRATION=false
G3_REAL_FORCE_PRESSURE_CLOSURE=false
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
```

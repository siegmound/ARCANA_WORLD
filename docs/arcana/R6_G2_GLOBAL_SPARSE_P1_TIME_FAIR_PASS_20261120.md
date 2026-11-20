# ARCANA R6 — Genuine global source P1 manufactured 100/1000-year integration FAIR PASS

**Date:** 2026-11-20. **FAIR tested source commit:** `a57fdbac0216c0d7b240681a0222a5fe6aa0fa45`.
**Decision:** `PASS_SOURCE_GLOBAL_SPARSE_P1_G1_G2_MANUFACTURED_100_1000Y__PHYSICS_OPEN`.

This assessment records an operator-provided FAIR terminal transcript. The full
`REPORT.json` and `MANIFEST.json` have **not been independently fetched**.
The source code was previously authored and SHA-linked; the operator reported
a clean checkout of that exact commit.

## Automated checks and global source scale

- **29/29 pytest PASS** in **0.63 seconds**.
- Authentic 12-plate geometry, 64,442 distinct source nodes,
  128,880 source triangles, 66,435 plate-local material views,
  **132,870 East/North DOFs**.
- **Actual spherical P1 sparse tangent**, 1,828,144 CSR nonzeros,
  sourced from the prior 28/28 static-P1 PASS.
- For the first time, this **manufactured** P1 tangent is reused
  through 100 and 1000 model-year implicit time updates on the
  whole 12-plate source topology.
- **Fixed T0 source geometry and tangent**, **UNWELDED** independent
  plate contacts, **invented** Kelvin–Voigt viscoelastic memory and
  a small nonrigid synthetic driving perturbation.
- The source Euler plate-rigid component remains a stiffness null
  mode, by design. This is not source-valid physical fault contact
  or real G3 mantle forcing.

## Exact operator-provided numerical results

| Metric | 100 model years | 1000 model years |
|---|---:|---:|
| Max nodal material displacement, m | 15.025221782306831 | 150.22014195248983 |
| Manufactured target RMS, m/model-year | 0.05376418193655341 | 0.05376418193655341 |
| Coupled RMS, m/model-year | 0.05376386854243191 | 0.05376300292357609 |
| RMS corrected-minus-target, m/model-year | 2.111419026950393e-5 | 6.835697632784933e-5 |
| Relative feedback norm | 0.00039271852577280145 | 0.001271422234388626 |
| Max displacement difference dt5 vs dt1, m | 0.0007778331504737501 | 0.0014150378499662164 |
| Max displacement difference dt10 vs dt1, m | 0.0017387808551485584 | 0.0031801085245288796 |
| Normalized synthetic elastic energy | 0.037054511957343356 | 3.4943635325165148 |
| Minimum signed triangle area ratio J | 0.9999867403485484 | 0.9998919112639771 |
| Maximum signed triangle area ratio J | 1.0000135912780335 | 1.0001110530370412 |
| Maximum |J-1| | 1.3591278033464604e-5 | 0.00011105303704117553 |
| Sum signed plate-local area ratio | 0.9999999995546689 | 0.9999999900435214 |
| Inverted source triangles | 0 | 0 |

1000-year **relative feedback norm** is ~**0.12714%**;
this is principally a property of the constructed nonrigid
perturbation and split-plate boundary semantics. It cannot be
interpreted as naturally slow lithospheric deformation.

At 1000 years, dt5 differs from dt1 by 0.001415 m and
dt10 differs by 0.003180 m: the ratio is ~2.247, compatible
with first-order implicit time convergence, **not** a proof of
exact global source convergence order. No dt<1 year GLOBAL
reference or fixed-extent spatial mesh convergence was run here.

## Numerical cost and restart

- Annual dt1 run (1000 steps): **23,102 total CG iterations**,
  mean **23.102** per step.
- Five-year dt5 run (200 steps): **5,712 iterations**,
  mean **28.56** per step.
- Ten-year dt10 run: **100** steps; its CG iteration count
  is not included in the terminal summary.
- Annual restart from model year 500 → 1000: 500
  replay steps, max reported displacement error **0.0 m**.
- Total time for assembly, 1/5/10-year runs, restart and
  geometry checks: **87.5943544022739 seconds** on FAIR.
- Global stiffness already uses a source-authentic P1 sparse
  matrix; detailed full-process RSS, CG iteration distribution
  and stepwise max force/energy residuals are present, if
  recorded, only in the full FAIR report, not this excerpt.

**`energy_normalized` is NOT total geological elastic energy
in joules.** Its increase from 0.0371 to 3.4944 cannot alone
be interpreted as physical energy growth or instability.
The reported area check is a geometric validity bound, not
a true G4 matter/heat conservation law. No normal support,
fault slip/opening, or evolving stress-dependent tangent
has been implemented.

## Most important next test — genuine contacts and objective geometry

The original long-term WorldSim goal is to generate mechanically
credible geological history and then material/resource, ocean,
flora/fauna, ecosystems and population distribution histories
that support local/time-window higher-resolution queries.
This manufactured numerical milestone does not yet supply
that geological history.

Before interpreting future timelines, introduce explicit
source-keyed contact ownership with three **different,
ENGINEERING_ONLY** policies: independent / artificially welded /
synthetic slip-with-opening. Test contact distance and tangent
mismatch at plate junctions, force action and torque in one
frame, frame-objective transport under true rigid Euler motion,
restart and timestep behavior, with a source-safe region-first
suite before scaling the assembled sparse P1 operator globally.

Then qualify, separately, constitutive G2 rock/microphysical
data, water/temperature/P/timescale domains, mechanical LAB,
G3 basal normal/shear + exterior constraints and G4 material
mass/heat transport. No new geological history store,
physical T1 or production solve is authorized.

```text
GLOBAL_SOURCE_G2_SPARSE_P1_STATIC_FAIR=PASS_28_OF_28
GLOBAL_SOURCE_G1_G2_P1_MANUFACTURED_100_1000_FAIR=PASS_29_OF_29
GLOBAL_CONTACT_AND_OBJECTIVE_FRAME_PHYSICS=UNQUALIFIED
REAL_G2_CONSTITUTIVE_AND_G3_FORCE_PROVIDERS=UNQUALIFIED
ENGINEERING_SOLVER_EXECUTED=true
PHYSICAL_SOLVER_RUNS=0
D_024=ACTIVE
physical_T1=null
```

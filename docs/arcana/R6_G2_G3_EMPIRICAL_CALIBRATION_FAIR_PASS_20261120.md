# ARCANA R6 — G2/G3 empirical calibration: FAIR 10/10 PASS

**Record date:** 2026-11-20. **Source commit verified by FAIR operator:**
`2a6bd6500cb453959e7d2bf44d94e8c241162c05`. **Branch:** `r6/multiphysics-integration-20261026`.

## Operator-provided terminal evidence

```text
From https://github.com/siegmound/ARCANA_WORLD
 * branch r6/multiphysics-integration-20261026 -> FETCH_HEAD
HEAD is now at 2a6bd650 feat(r6): add source-gated G2/G3 empirical calibration and identifiability report
2a6bd6500cb453959e7d2bf44d94e8c241162c05
.......... [100%]
10 passed in 0.14s
```

The preceding FAIR command targeted
`tests/test_r6_g2_g3_empirical_calibration.py`.
This passes the 10 *synthetic mathematical verification* tests for
source-gated dislocation-creep regression and basal-drag regression,
including checks that absent or unidentifiable physical observations
cannot produce an authorized fit. The raw FAIR evidence directory
was not independently inspected in this commit; this report registers
the operator's terminal output.

## Physical interpretation and unchanged hard gates

- G2 real ARCANA crust/mantle material identity, valid temperature-
  pressure-rate laws, water fugacity and pore-pressure/Biot remain unknown.
  The GT95 quartzite law does not cover the reported cold T0 crust
  (280–1051.558 K vs ~1173.15–1373.15 K experimental window).
- G3 real north/south and other exterior tractions, deep-mantle flow,
  basal tangential drag, normal support and physical GPE closure remain
  unqualified. Euler velocities alone cannot identify basal traction
  coefficient beta.
- The source PRE thermal base must not be treated as a mechanical LAB.
- No source-referenced measured laboratory stress/rate samples or observed
  deep-mantle traction/velocity pairs were fitted. The physical parameter
  values and authorial ratification flags stay null/false.
- No mechanical solve was authorized or run from this work;
  `physical_T1 = null`, D-024 remains active.

## NEXT scientific action (no more redundant unit-test loops)

Acquire *individual experimental measurement tables* for a **scoped,
explicitly selected** crustal/mantle analogue, recording sample identity,
mineralogical and hydration conditions, pressure, temperature, strain rate,
stress convention and uncertainty. Check true temperature-pressure-rate
coverage *before* fitting; use independent experimental holdouts. Do not
treat any terrestrial analogue as ARCANA material identity without
authorial approval.

For G3, independently locate a source for deep mantle reference flow,
basal shear/normal state and the physically supported regional boundary
provider for plates 5, 8 and 11; a synthetic drag beta or force-zero
fitting is not admissible. If no authentic providers exist, retain an
explicit non-identifiability decision rather than fabricating forces.

# ARCANA R6 — Synthetic 1000-year thermal-column follow-up (noncanonical)

**Date:** 2026-11-22
**Status:** DEVELOPMENT_ONLY__FAIR_PENDING
**Development branch:** `r6/experimental-thermal-column-1000y-noncanonical-20261122`
**Parent R6 main:** `b3f2891b2d98523f419c5e7dfc0e13d0b3f0409a`
**Science decision:** separate, independently verified 1000-year study is allowable as an experiment; **physical WORLD_HISTORY T1 remains NO-GO**.

## 1. Immutable 100-year oracle

This intervention does not edit:
- `src/arcana_worldsim/r6/experimental_thermal_column.py`;
- `tests/test_r6_experimental_thermal_column_100y.py`;
- the old experiment's configuration, FAIR logs, receipt or result.

Source-authenticated original T0 **model** cell: `R6G1D-R089-C359`, original plate 8, model oceanic-crust thickness 6500 m. The simulated **1000 m** thermal column is explicitly synthetic, as are its initial temperature and boundary conditions.

The new module first verifies the unchanged 100-year configuration Git blob `ea1355175145894edf8a8e24268bf843b9368bdf`, then calls the original read-only 100-year source-backed experiment to check provenance and produce a numerical comparison in memory. It does not rewrite the old FAIR report.

The permanent noncanonical policy remains pinned to Git blob `75658d37b12ac3d2c3b3fed5b9e56203a6ae3cf1`. Its initial-pilot-100-year field **does not authorize extending the old pilot**; the new 1000-year study has a separate schema, module, config, tests, manifest and evidence directory.

## 2. First component: 1000-year insulated cosine continuation

Governing **synthetic** model:

```text
rho Cp dT/dt = k d2T/dz2 + Q
0 <= z <= 1000 m
T(z,0) = 300 K + 15 K cos(pi*z/L)
dT/dz(0,t) = dT/dz(L,t) = 0
```

Use original nominal authored **reference**, not real cell-measured properties:
- rho 2890 kg/m3, Cp 1000 J/(kg K);
- k 2.2 W/(m K), Q 3e-7 W/m3.

Use exactly the original refinement levels (n, dt years):
`(50,1), (100,0.25), (200,0.0625)`, now 1000/4000/16000 steps over 1000 Julian years. Each is cell-centred conservative FV explicit Euler. Convergence is verified against the same exact synthetic cosine-decay + uniform-source solution, and the integrated heat budget must close.

These are **not** ARCANA temperatures at 209.999 Ma. A 1000-year numerical horizon is not a qualified full planetary geodynamics timestep.

## 3. Reference-coefficient sensitivity

The reference V1 document is byte-verified using its Git blob `e041e7dc91f617cf7f755b46ab36e7417d486fd0`. Hold all but one coefficient nominal and run its declared **authorial sensitivity endpoints** at the 100-cell/0.25-year level:

| Parameter | Low | Nominal | High |
|---|---:|---:|---:|
| rho [kg/m3] | 2850 | 2890 | 2930 |
| Cp [J/kg/K] | 800 | 1000 | 1200 |
| k [W/m/K] | 1.8 | 2.2 | 2.8 |
| Q [W/m3] | 0 | 3e-7 | 5e-7 |

There are eight independent one-factor cases. Report the difference in mean final temperature and the maximum absolute difference at exactly five matched sampled cell centres, not a claim of whole-field sensitivity or a posterior probability. This is **parameter sensitivity**, not inference about mineral composition.

## 4. Boundary-condition study — separate numerical qualification

To avoid treating a different boundary condition as automatically validated by the Neumann test:

1. **Manufactured Dirichlet solution.** Fixed top/bottom T = 315/285 K. Define steady state
   `S(z) = 315 + (285-315)z/L + Q*z*(L-z)/(2*k)`
   with initial `S(z) + 8 sin(pi*z/L)`. The exact solution is
   `S(z) + 8 sin(pi*z/L) exp[-alpha*(pi/L)^2*t]`.
   Verify all three resolutions and conservative energy accounting, including **boundary-face heat flux**. Merely balancing radiogenic Q is insufficient for an open-heat column.
2. **Matched initial condition boundary sensitivity.** Reuse precisely `300 + 15 cos(pi*z/L)` at all cell centres and impose fixed top/bottom 315/285 K. Compare five aligned sample centres at the finest resolution against the insulated nominal solution. This comparison does **not** assert an independent exact continuum solution or physical ocean-floor forcing.

Boundary and material experiments are still synthetic, not historical predictions.

## 5. Validations and evidence

- Independent local arithmetic/numerical checks were carried out while preparing the implementation; these are **not FAIR evidence**.
- **Expected** targeted collection: 30 new pytest cases; **expected** selected R6 regression: 368 total (previous 338 plus new 30). Exact counts remain unverified until FAIR.
- Required on FAIR: pinned real original NPZ source readback, old-100y baseline retest, new 1000-year convergence + heat budget, Dirichlet manufactured analytic error + external heat accounting, sensitivity case count/source bounds, no-canonicity, no HistoryStore, read-only hash/manifest, non-overwriting evidence.
- Runner: `bash scripts/r6_experimental_thermal_1000y_fair_gate.sh` at checkout root with `arcana-r6-linux`; all evidence goes to a **new** path below `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6`.
- Do not rerun or overwrite original 100Y evidence. On a failed run retain the failure, use new paths for any later attempt.
- Only after successful FAIR output and review on the exact source SHA, consider a software-only fast-forward integration into `r6/multiphysics-integration-20261026`. Do not merge the new study's numeric trajectory into ARCANA world history.

```text
EXPERIMENTAL_1000Y_FAIR = PENDING
EXPERIMENTAL_1000Y_CANONICAL = FALSE
PHYSICAL_WORLD_T1 = NULL
HISTORYSTORE_MUTATIONS = 0
D_024 = ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED = FALSE
```

## 6. After this study

This tests only the reduced homogeneous 1D heat equation under narrowly defined conditions. It does not close actual source T0 thermal profile, material phases/fluids, 3D thermal domains, global G2/G3 force balance and fault law, topography or tectonic boundary histories. **D-024 still prioritizes a genuinely coupled, small regional physical T0→T1 when its physical input gaps are closed.**


## 7. First FAIR gate: 29/30 FAIL, JSON boundary scalar — retained

On the initial FAIR checked-out SHA `b19d2bc90982f2172322efed933f3db38efb7d21`, the operator reported **29 passed, 1 failed** in the new targeted suite. The failed case was `test_write_once_sha_and_no_overwrite`, at `json.dumps(result, allow_nan=False)`. The terminal error was `TypeError: Object of type bool is not JSON serializable`. This first attempt stopped before the selected 368-case regression and before the source-anchored 1000y report/manifest. **Do not call it a 1000y FAIR pass.** The original `R6_EXP_THERMAL_1000Y_TARGET_30_NEW01.log` is preserved; no evidence overwrite or retroactive correction.

Cause independently reproduced: in `dirichlet_fv` the boundary-flux accumulator becomes `numpy.float64` after adding the first NumPy-computed face flux; its energy residual therefore becomes NumPy float and `abs(residual) <= 1.0` returns `numpy.bool_`, which standard-library `json.dumps` rejects. This is a **report-serialization type issue**, not a demonstrated failure of the thermal PDE/flux calculations. Do not infer broader numerical qualification from the other 29 passing tests alone.

Bounded change in same experimental branch:
- Cast accumulated boundary energy and energy-balance residual to built-in Python `float` *after* numerical stepping; cast pass predicate to Python `bool`; retain strict JSON serialization `allow_nan=False`. No change to FV equations, grids, physical/reference coefficients, source/authority or 100-year baseline.
- Extend existing tests to assert native `float`/`bool`, strict JSON roundtrip for manufactured and matched boundary cases, and full nested report. **Test count remains 30 targeted and 368 selected**.
- Use dedicated `NEW02` paths in the fail-closed FAIR runner:
  `R6_EXP_THERMAL_1000Y_TARGET_30_NEW02.log`,
  `R6_EXP_THERMAL_1000Y_FULL_368_NEW02.log`,
  `R6_EXP_THERMAL_1000Y_NONCANONICAL_NEW_02/`.
- **Status after patch: FAIR RETEST PENDING**. A local scalar-type reproduction is not the complete FAIR run. Freeze a new exact Git SHA and revalidate before considering integration.

Permanent scope unchanged: `EXPERIMENTAL_NONCANONICAL_ONLY=true`; `physical_T1=null`; no `WORLD_HISTORY` or `HistoryStore` writes, no mineral/ore/Deep claims; `D-024=ACTIVE`.

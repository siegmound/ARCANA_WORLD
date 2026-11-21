# R6 G2/G3 — Empirical rate-and-state normalized stability from original Earth laboratory model fits

**Date:** 2026-11-21. **Parent R6 engineering baseline:** `d071c98c4d6917f535e7eaea38a75045a79af462`.
**Scientific experiment branch:** `r6/g2g3-rsf-normalized-stability-20261121`.
**Decision:** `SOURCE_MODEL_FIT_TO_NORMALIZED_STIFFNESS_IMPLEMENTED__REAL_66_ROWS_FAIR_REPLAY_PENDING__ARCANA_PHYSICAL_FAULT_OPEN`.

## Research question and scientific step

R6 now has an externally acquired **PANGAEA 921284** dataset with 66 published *model-extracted* rate-and-state fits (57 one-state and 9 two-state), validated through an immutable corrected `INGEST_NEW_02` report at raw SHA256 `b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d`. The fits have 20 reported negative, 3 zero and 43 positive `a-b` signs; those counts do not imply independent faults or earthquake occurrence. The individual experimental effective normal stresses, ARCANA fault absolute friction, elastic stiffness and real 3D side geometry are still unbound.

**Instead of inventing those fields, compute a true mechanical **conditional stability threshold** for the published laboratory parameter sets, normalized by effective normal stress**: `K_crit / sigma_eff` [1/m]. This ratio requires no assignment of `sigma_eff` in Pa, and does not generate a physical force or predict seismicity.

Primary references:
- Ikari & Kopf (2020), model-extracted Table 2: https://doi.org/10.1594/PANGAEA.921284
- Ikari & Kopf (2017), original test contexts, nominal 10 MPa with prior Tohoku 7 MPa: https://doi.org/10.1126/sciadv.1701269
- Ruina (1983), *Slip instability and state variable friction laws*: https://doi.org/10.1029/JB088iB12p10359
- Laboratory fault critical stiffness and limitations: https://doi.org/10.1029/2018JB016803
- 1- vs 2-state model differences: https://doi.org/10.1029/2026GL121839

## Equations — fixed-normal-stress, massless quasi-static slider, Dieterich aging

The reference state at `v0` is assumed steady, not independently observed:

```text
theta_i0 = Dc_i/v0
delta_mu = a ln(v/v0) + sum_i b_i ln(theta_i*v0/Dc_i)
dtheta_i/dt = 1 - v*theta_i/Dc_i
d(tau_elastic)/dt = K*(v_load - v)
tau_friction = sigma_eff*(mu_ref + delta_mu)
```

In the **linearized** quasi-static spring-slider, define `x = lambda*Dc_ref/v0`, `q = (K/sigma_eff)*Dc_ref`, `d_i=Dc_i/Dc_ref`, where `Dc_ref=min_i(Dc_i)`. The characteristic equation (up to multiplication by harmless, stable state factors) is:

```text
(q+a*x)*PROD_i(1+d_i*x)
    - x*SUM_i[b_i*PROD_{j!=i}(1+d_j*x)] = 0
```

For **one state** this gives:

```text
a*x^2 + (a-b+q)*x + q = 0
K_crit/sigma_eff = max(b-a,0)/Dc       [1/m]
```

For **two states** the cubic coefficients are:

```text
c3 = a*d1*d2
c2 = q*d1*d2 + a*(d1+d2) - b1*d2 - b2*d1
c1 = q*(d1+d2) + a-b1-b2
c0 = q

asymptotic stability iff c3,c2,c1,c0 > 0 and c2*c1 > c3*c0.
```

For admissible velocity-weakening fits `a>0`, `b_i>=0`, the critical normalized ratio is obtained from the physically relevant positive root of `c2*c1=c3*c0` with `c1,c2>0`. **We do not average `Dc1,Dc2` or apply the one-state formula to a two-state fit.** `roots_at_normalized_stiffness` can additionally calculate eigenvalues for a user-supplied *hypothetical* `K/sigma_eff` ratio without choosing an actual planetary stiffness or stress.

This is the mathematical stability of a *spring-slider surrogate*, not an earthquake nucleation length, 3D rupture dynamics, contact traction, or self-consistent original 210 Ma plate motion/force evolution. Heterogeneous gouge, inertia, dilatancy, nonlinear slip paths, changes in fluid pressure and test-history uncertainty are not represented.

## Conservative source qualification

- Unknown/negative `a` or negative state weights `b_i`: **exclude** from this stability inference, retaining the source fit row for provenance; no silent `abs(b)` or model repair.
- Published `a-b == 0` due to rounding: exclude from unique threshold estimates.
- Source-reported sign conflicting with reconstructed `a-sum_i b_i`: exclude, not choose one silently.
- If a two-state positive Routh-Hurwitz threshold cannot be identified uniquely: exclude that row from critical-stiffness claims but do not discard it from the 66-row scientific inventory.
- Velocity strengthening with admissible signs: the surrogate is stable at all **strictly positive** normalized elastic stiffness values, `Kcrit/sigma=0`; a free `K=0` mechanism is not a stable spring.
- No physical `sigma_eff` or absolute `K` is inferred; `K_crit (Pa/m)=null`, all ARCANA fault nodes/side orientations are null.
- Dataset row counts and unique IDs are not claims of statistically independent experiments.

## Source-bound execution and evidence

Implemented:
- `experiments/plate58_deforming_explore_v1/g2_g3_rsf_linear_stability.py`.
- `tests/test_r6_g2_g3_rsf_linear_stability.py`.

The parser **reopens the actual publisher TSV**, requires its exact SHA, independently reconstructs the full 66 model fits, validates the previously stored `INGEST_NEW_02/REPORT.json` and `MANIFEST.json` SHA chain and confirms all 66 prior pressure-scaled shear stresses remain `null`. Writes a **new immutable report** including full per-source-row normalized stability results and explicit exclusions, plus SHA-bound manifest. It does not rewrite `INGEST_NEW_01`, `INGEST_NEW_02`, FEG/PRE, the canonical universe or HistoryStore.

**Local authoring QA:** `19 passed in 0.09s` on Python 3.13.5, including one- and two-state analytic limits, exact eigenvalue stable/unstable checks, mismatched fitted signs, finite-source requirements, and a 66-row *synthetic* end-to-end SHA replay with manifest tamper rejection. The exact published Python/test file Git blobs were checked against the locally tested file hashes (`031993b95d851be06a4db0e1c914f0a6b5981e1a`, `739a0ee90da6b6f90f231903b7a354ff278131ff`).

**Real PANGAEA 66-row stability output on FAIR: PENDING.** Do not claim empirical critical `K/sigma` distributions before running the new code on real publisher data. **Full prior G2/G3/RSF regression on this branch: PENDING** (147 existing + 19 new = 166 expected tests).

## FAIR source material locations

```text
RAW=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_PANGAEA921284_RAW_NEW_01/pangaea_921284.tab
INGEST_DIR=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_PANGAEA921284_RAW_NEW_01/INGEST_NEW_02
NEW_REPORT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_PANGAEA921284_STABILITY_NEW_01
```

Use the exact Git SHA of the development branch, target 19 tests first, then full G2/G3 166-test regression and scientific execution against the unchanged existing publisher bytes in a new report directory. Preserve logs and actual exit codes. Any failure is a source/physics issue to diagnose, not permission to fabricate source states.

## Remaining physical requirements before ARCANA T0→T1

1. Original ARCANA **crust/mantle lithology and water**: existing T0 PRE 51 columns and material-configuration codes are not a source-supported mineral fraction or rate/P/T/full-column plastic law.
2. ARCANA fault **actual contact surface, slip-side DOF orientation**, independent sidedness and gouge occurrence: original 5:8:11 contact graph and node 34587 are still shared parent-node topology, not three independent fault nodes. Source original FEG is a thin-sheet, not a closed 3D contact volume.
3. ARCANA fault **effective normal pressure** and independently validated true stiffness `K` and reference friction `mu_ref`; only then can a sample's `K/sigma` and tractions be meaningfully compared with conditional laboratory surrogates under applicability restrictions.
4. Source physical G3 outer-cut, basal normal/tangential, mantle flow and one-owner GPE closure, with solver and force/torque/virtual-work validation.

```text
PHYSICAL_FAULT_INSTABILITY_PREDICTED=false
G2_REAL_ROCK_HYDRATION_PT_RATE_RATIFIED=false
G3_FAULT_INTERFACE_SLIP_AUTHORIZED=false
G3_SOURCE_BASAL_AND_CUT_TRACTIONS_QUALIFIED=false
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

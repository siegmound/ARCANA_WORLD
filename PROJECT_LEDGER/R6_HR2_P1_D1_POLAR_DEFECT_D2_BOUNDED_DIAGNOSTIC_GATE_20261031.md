# ARCANA R6 — HR2-P1-D1: analytically demonstrated polar inconsistency, D2 bounded diagnostic next gate

**Date:** 2026-10-31. **Authority:** FAIR operator report `docs/arcana/R6_HR2_P1_D1_FAIR_20261031.md` submitted in conversation; this GitHub documentation write does not run or independently rehash the FAIR case. Original FAIR branch `r6/runtime-copy-r1-fair`, base HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787` intentionally dirty.

## Frozen history and exact result

`HR2_P1=BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE`: earlier Q1 had 29 PASS, 1 FAIL; 317 pinned source/test identities remained unchanged. `HR2_P1_D1=BLOCKED_REQUIRED_SPATIAL_DIAGNOSTICS_NOT_RETAINED`: D1 read-only analytical diagnosis, not an additional numerical execution.

**Established analytically**: using exact latitude-longitude spherical cell **area averages** as if they were point samples at angular cell centers produces a polar-row spatial consistency defect. First-polar-row ratio area-average/center-sample tends to **4/3** for the nonaxisymmetric degree-one mode. The frozen EW and NS face contributions fail to cancel their leading polar terms. **Measured earlier Q1**: L1 drops ~order1, area-weighted L2 plateaus ~4.43e-7 m and Linf roughly doubles from 2.20e-6 to3.60e-5m under successive refinement 16x8..256x128. Existing results are compatible with this failure mechanism. Scalar/independently verified harmonic cell-average formulas appear correct, no specific seam-connectivity fault established, temporal main/half-dt difference is much smaller than spatial L2. **Unknown**: actual signed per-cell or latitude-band contributions and position of Linf because Q1 saved global norms, not the final spatial arrays; no evidence to assign a numerical percentage of actual Q1 error to poles/EW/NS.

D1 original Q1 file manifest104 members and nested73 verified; Q1 source contract SHA256 `544f8d2ca95a2213026b8106d05dd4114d1171033e2c832964a288f3d454f186`; model SHA256 `6a60a90f00976e4b130d083468a0fbdca15d12686e8f86f11f82e327d8ea6c2f`; manufactured source `af52447e5d23023450ff3679ed23defd24a59285e99eed23422b2db27087930c`; method checks `b938b2ee513c32dedc6c155926fb07091bc5fe911390154ba32e437c1ae51ea0`; acceptance `ac827231ed3c5ea66c1b9731d31e0e3103b6f19cccae17204596476190e3f213`. Pins must be checked against actual FAIR bytes; hashes listed here are documentation, not substitutes for an actual verification.

## Proposed D2: an isolated, minimal, frozen-V1 **diagnostic numerical probe**

**Status:** proposed and not yet run or explicitly authorized in this documentation-only action. Objective: collect only absent *spatial* diagnostics to confirm/quantify the analytical mechanism **without changing original solver implementation, original Q1 pass/fail, frozen acceptance criteria, or prior evidence**.

1. Read and SHA-verify actual FAIR D1/Q1 reports, `DIAGNOSTIC_MATRIX.csv`, `FACE_METRIC_AND_ORACLE_AUDIT.md`, `formula_v2`, `SOURCE_CONTRACT.json`, original `model.py/manufactured.py/checks_method.py/acceptance.json`. Snapshot files and source hashes, keep Q1/D1 outputs immutable. Do not automatically import old artifacts into a new qualified scientific state.
2. A **new additive, versioned diagnostic driver only** may call exact frozen V1 operator, same manufactured `kappa`, `R`, positive mean+harmonic, actual spherical meshes `16x8,32x16,64x32,128x64,256x128`, final time **0.0001 model-year**, configured accepted dt schedule as the Q1 spatial study. Do not edit V1/acceptance/original Q1 scripts or run a second full Q1 under the same contract. Design driver to persist actual initial area-average arrays and original analytic reference arrays, full final main and half-dt `V,h`, accepted dt histogram, coordinate/row orientation, dtype, identities and SHA. Before first run verify exact original code bytes and that driver has no hidden source modification.
3. At manufactured T0, independently compute per-cell instantaneous consistency defect `A_i [L_h(h_exact) - (-2 kappa/R^2) (h_exact-H0)]` in m3/year with both **EW** and **NS** signed face flux/transfer components, canonical shared-face pairing, exact integral/spherical reference and roundoff estimates. Check sign, dimensions and that EW+NS exactly reconstruct the frozen stencil. Optional `cos(phi) sin(lambda)` shifted harmonic is a **separate explicitly identified diagnostic arm** because it has nonzero seam flux, unlike Q1 cosine mode; never silently substitute it for the frozen case.
4. Produce signed error maps at every grid and T0 defect maps, global area-weighted L1/L2/Linf with argmax cell and lat-lon, 10-degree latitude band counts and contributions to squared global weighted L2, first/last 1/2/4 polar-row exclusions (NA if selection empty), `|lat|<=60/75/85`, EW/NS local terms and cancellation residuals, seam vs interior norms. Derive errors from **persisted real arrays**, not fitted global norms. Compare to Q1 global norms with exact matching solver/parameters, fail investigation on undocumented deviation, and preserve original Q1 as history.
5. Retain exact wall/CPU/RSS, field arrays size, per-face kernel timing, dt/substep count, input/source/driver hashes, manifest/finalization and immutable V1 reference in a **new exclusive D2 evidence root**. Repeat only if a fresh separate human-approved recovery gate exists; no automatic reruns, no modified thresholds, no 1000Y/10k/100k or source admission.
6. **Outcome:** `HR2_P1_D2=PASS_MEASURED_POLAR_ERROR_AND_FLUX_ATTRIBUTION` only with all source-pinned per-cell evidence and confirmed Q1-compatible norms; otherwise `HR2_P1_D2=BLOCKED_<specific_reason>` with retained logs. D2 PASS means diagnostic localization **only**, not corrected method.

## Post-D2 proposed R1 (not implemented or authorized by this record)

If polar inconsistency and band attribution are confirmed, separately design `HR2_P1_R1` **cell-average-consistent face reconstruction** and polar flux treatment that remains conservative (each shared face one antisymmetric flux), positive under derived CFL and genuinely convergent for nonaxisymmetric harmonics. Require independent face-moment/flux analytical oracles, include shifted-longitude nonzero seam-flux adversarial mode, both harmonic spatial/temporal convergence across five grids, all originally frozen Q1 numerical tests and 3Y/10Y true native/B0 restart. Do not relax original >=1.5 spatial order or 5% dt requirement. Distinguish method numerical PASS from source-validated geological parameters, real ARCANA global T0 admission, and production/global 1000Y authority.

```yaml
HR2_P1_Q1: BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE
HR2_P1_D1: BLOCKED_REQUIRED_SPATIAL_DIAGNOSTICS_NOT_RETAINED
HR2_P1_D2: PROPOSED_ISOLATED_BOUNDED_DIAGNOSTIC_NOT_EXECUTED
HR2_P1_R1: NOT_IMPLEMENTED_NOT_AUTHORIZED
GLOBAL_1000Y_PHYSICAL_RUN: NOT_AUTHORIZED
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
```

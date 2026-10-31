# ARCANA R6 — HR2-P1-D2 PASS, polar defect quantitatively attributed; propose HR2-P1-R1-DESIGN

**Date:** 2026-10-31. **Authority/source:** FAIR user-supplied report `docs/arcana/R6_HR2_P1_D2_FAIR_20261031.md`, evidence `ARCANA_WORLD_EVIDENCE/R6/HR2_P1_D2_20261031_01`. Connected GitHub documentation did not independently execute or rehash FAIR runtime. Original worktree `r6/runtime-copy-r1-fair` at `2c71370eb9a959c78121ce1c88ec8e9e37187787` remains intentionally uncommitted.

## Verified operator-reported results

`HR2_P1_D2=PASS_MEASURED_POLAR_ERROR_AND_FLUX_ATTRIBUTION`

Exactly **10 isolated frozen V1 diagnostic cases** (2 original manufactured modes × 5 meshes 16x8 through256x128), at final time 0.0001 manufactured model-year, reproduce original Q1 global norms, dt differences, accepted-step counts/histograms *exactly*. **340 NPY arrays** persisted and authenticated, full cellwise initial/reference/main/half/geometry/flux/defect evidence; one diagnostic numerical launch (no repeated Q1). Runtime wall **3.638596304s**, driver peak process-tree sampled RSS **61.515625MiB**. The 317 original source/test/acceptance pins, V1 solver, Q1 and D1 artifacts remain unchanged. Original Q1 historical status is **BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE** and D1 remains **BLOCKED_REQUIRED_SPATIAL_DIAGNOSTICS_NOT_RETAINED**; D2 PASS does not rewrite either status or imply corrected solver.

**At 256x128 nonaxisymmetric harmonic**: global weighted L2 error `4.42572818e-7 m`, Linf `3.60365774e-5m`; first polar row at EACH pole together contributes **99.857575989% of global squared area-weighted L2 error**, first 4 rows each pole **99.999987993%**. L2 excluding these eight rows `1.53729227e-10m` (selection renormalized by retained area). Maxima at every tested grid occur in a polar-adjacent row. This is a per-cell measured result; percentages are **squared-error contributions**, not norm percentages.

**Measured initial flux consistency**: first polar-row frozen/exact face rate ratios by direction trend to **4/3 EW and 8/9 NS**: at256x128 EW=1.333239626, NS=0.888763947. Actual error versus `T*(initial consistency defect/area)` area-weighted cosine **0.999999661572**, relative L2 mismatch **0.00501412761** at256x128. The directional EW/NS signed rate decomposition sums to V1's own transfers; shared-face antisymmetry is retained. Both EW/NS participate in the non-cancelling polar defect. No isolated seam-connection issue is demonstrated for the original cosine mode; shifted sine/nonzero-seam test remains unrun. Existing temporal remainder is small, without claiming rigorous continuous-time error control.

**Immutable identities:** frozen source-contract SHA256 `544f8d2ca95a2213026b8106d05dd4114d1171033e2c832964a288f3d454f186`, V1 model `6a60a90f00976e4b130d083468a0fbdca15d12686e8f86f11f82e327d8ea6c2f`; D2 additive driver `040c6ebbf6b51211129db80698eefb8b59fa1476173532b538132631f37a474a`. Use actual FAIR manifest and SHA files to verify, not just these copied claims.

## Proposed next R1-DESIGN gate — not automatically an implementation GO

The next task should be a **reviewable method design** for a NEW versioned solver R1; no changes to V1, no post-hoc Q1 tolerance modifications, no 1000Y/10k/100k, production or science promotion.

Objective: approximate `dh/dt=kappa Laplace_Beltrami(h)` for **cell-area averaged height** `hbar_i` with a conservative spherical finite-volume method, including first/last polar rows and both meridional and zonal face-normal fluxes.

1. Derive from integration over each cell `dV_i/dt=-sum_{f in boundary} F_{i,f}`, `V_i=A_i*hbar_i`; each interior face is evaluated **once** and applied with opposite sign to its two neighboring cells. Use true spherical cell areas, face lengths and integrated directional gradients. Produce independent analytic cell-average and continuum face-flux references (including exact polar asymptotics) using the already sealed D1/D2 formulas.
2. Design at least one **general, method-consistent** face reconstruction from cell averages (e.g., a local tangent-plane/spherical moment reconstruction with an explicitly symmetric shared-face numerical flux), accounting for polar moments in EW and NS simultaneously. No fitted correction factors 4/3 or8/9 hard-coded for the particular harmonic, no axisymmetric special casing, no clipping/mass renormalization, and no fake high-resolution display. Alternatives (e.g., moment-preserving polar patches) must declare actual mesh topology/geometry changes and new interface/source identity. Do not assume the originally monotone two-point formula remains monotone under reconstruction.
3. Prove or give a defensible falsifiable strategy for positivity/maximum principle and timestep/CFL under the revised stencil, including extreme polar areas and nonnegativity without mass creation or hidden clipping. If a high-order scheme cannot be made positivity preserving under declared conditions, BLOCK rather than drop positivity or relax original spatial order. Assess stencil locality, computational cost, halo exchanges and tile/memory scaling.
4. Establish **independent method oracles before execution**: constant-state invariance, exact rational unequal-area 2x2 local flux, at least two nontrivial low-order spherical modes, exact continuum area-average and EW/NS face fluxes, polar row cancellation, seam shifted longitude harmonic (nonzero seam flux), pole sign symmetry, arbitrary rotations/phase, and nonharmonic smooth positive fields. Retain time-error separation, all five original 16x8→256x128 grids and dt/2 arm. The full original Q1 acceptance stays frozen: spatial observed order >=1.5 in L1/L2/Linf at all successive refinements and <=5% half-dt continuum-error difference; temporal first order ~0.9..1.2; conservation, CFL, positivity, full native B0 3Y/10Y direct/split/child restart and negatives. Add per-cell error/flux/defect retention from D2, not only global norms.
5. Cost-aware diagnostics: record mean/min CFL at poles, numerical substeps vs annual output frequency, operator face visits/sec, memory per cell and checkpoint state shape; avoid assuming 2K×1000Y physical feasibility from HR1 streaming of simple arrays. Only source-backed R6 T0 materials/forcing/cover and physical kappa admission can establish geology; manufactured R1 remains synthetic verification.
6. Deliver a decision memo comparing two or more viable discretization strategies with predicted formal order, conservative shared-face flux, positivity/CFL contract, analytic polar treatment, complexity and independent failure modes. Identify a **single smallest R1 prototype** and strict test-first implementation plan. Gate `HR2_P1_R1_DESIGN=PASS_REVIEWED_POLAR_CELL_AVERAGE_CONSERVATIVE_METHOD` only if mathematical, proof and adversarial-test contracts are concrete enough for implementation, otherwise `BLOCKED_<reason>`. Design PASS is not solver numerical PASS.

## Governance

No new physical execution, R1 implementation, rewrite of frozen V1, automatic commits/pushes on FAIR, source/admission of planetary geological data, or scientific/production promotion authorized by recording D2. Explicit new user authorization to implement/test R1 required. Document deliverables separately from FAIR source; original 317 pin lineage and external evidence remain immutable.

```yaml
HR2_P1_Q1: BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE
HR2_P1_D1: BLOCKED_REQUIRED_SPATIAL_DIAGNOSTICS_NOT_RETAINED
HR2_P1_D2: PASS_MEASURED_POLAR_ERROR_AND_FLUX_ATTRIBUTION_OPERATOR_REPORTED
HR2_P1_R1_DESIGN: PROPOSED_NOT_EXECUTED
HR2_P1_R1_IMPLEMENTATION: NOT_AUTHORIZED
REAL_GLOBAL_2K_1000Y_PHYSICS: BLOCKED
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
```

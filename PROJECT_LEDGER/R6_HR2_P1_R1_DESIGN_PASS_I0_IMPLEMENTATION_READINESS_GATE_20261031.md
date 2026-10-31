# ARCANA R6 — HR2-P1-R1-DESIGN PASS; next R1-I0 staged implementation readiness gate

**Date:** 2026-10-31. **Status:** proposed next gate; no R1 solver is implemented or executed by this ledger record. Source for this statement: FAIR operator report `docs/arcana/R6_HR2_P1_R1_DESIGN_FAIR_20261031.md` supplied in conversation, not an independent connected GitHub runtime verification.

## Current authority and provenance

`HR2_P1_R1_DESIGN=PASS_REVIEWED_POLAR_CELL_AVERAGE_CONSERVATIVE_METHOD`. The report documents a **design/internal mathematical-contract review**, not peer-reviewed numerical validation. User reports 317 frozen pins unchanged, Q1/D1/D2 source and archives preserved. No R1 source implementation, stencil matrix assembly or numerical advance has occurred.

Historical records retain their distinct verdicts:

- `HR2_P1_Q1=BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE`: V1 manufactured method 29 PASS / 1 FAIL.
- `HR2_P1_D1=BLOCKED_REQUIRED_SPATIAL_DIAGNOSTICS_NOT_RETAINED`: analytic proof, missing recorded spatial arrays in D1 scope.
- `HR2_P1_D2=PASS_MEASURED_POLAR_ERROR_AND_FLUX_ATTRIBUTION`: 10 matched frozen-V1 probes, 340 verified arrays; at 256x128 first 4 rows per pole 99.999987993% of squared area-weighted L2; first-row face ratios EW→4/3 and NS→8/9.
- R1 design PASS **does not** change Q1, D1 or D2 and must not be called globally qualified R6 physics.

FAIR evidence: `ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_DESIGN_20261031_01/` containing `MATHEMATICAL_SPECIFICATION.md`, `ALTERNATIVES_AND_COST.md`, `ORACLES_AND_TEST_FIRST.md`, `TEST_FIRST_PLAN.csv`, `NATIVE_B0_AND_OBSERVABILITY.md` and independent manifest/finalization. Compare actual saved artifact hashes before implementation; do not infer them from old Q1 contract.

## Chosen candidate A — method contract (design only)

**Spherical conservative finite volumes on scalar native cell volumes**, reconstructing a degree-4 tangent polynomial from **true integrated spherical cell moments** (15 total-degree<=4 coefficients), with source-/geometry-bound QR/SVD rank and condition certificates. Evaluate the **integral of the covariant normal gradient on each shared face once**, use equal/opposite face volumes and a conservative invariant-domain high-minus-low flux correction (same face alpha at both endpoints). Treat both EW and NS together, including near-polar rows.

No ad-hoc 4/3 or 8/9 multiplier, no hard-coded harmonic branch, no point-as-cell-mean substitution, no polar cap/cell change unless separately versioned, no clipping or global mass renormalization. A design-level conditioned positivity bound and its real-arithmetic maximum principle are **not** executed proof that the implemented limiter preserves original convergence, floating-point nonnegativity, or correct polar accuracy.

Alternative B curved SIPDG changes dynamic state to 15 coefficients per cell, increasing stabilization/trace/checkpoint complexity; not selected for the smallest prototype.

## Next proposed gate HR2-P1-R1-I0: test-first isolated numerical implementation

**Implementation/testing permission is a new human scope decision; this record alone does not authorize FAIR numerical execution.** The smallest defensible authorized I0 scope is to construct a new versioned, isolated `experiments/hr2_p1_r1/` method with no import-shadowing of `experiments/hr2_p1` V1 and no modification of existing Q1/D1/D2 evidence, plus independent tests and source-contract pinning. Maintain the intentionally dirty FAIR working tree unchanged except new additive files / explicit reports; no auto git commit/push.

1. **Independent geometry/moment preconditions first:** analytic integration / high-precision independent quadrature of cell and face moments for every 2:1 sphere; row orientation, seam periodicity, zero outer polar faces, unique shared faces; 15-monomial reproduction and patch rank/conditioning and error certificates, especially polar rows and across longitude periodic seam. No silent fallback to midpoint gradients or fitted special cases; if certificate fails at an intended mesh, return BLOCKED with diagnostic matrix before running evolution.
2. **Prototype flux:** shared covariant face normal-gradient integral from reconstructed moments; preserve signed EW/NS per-face budgets, source/receiver IDs and dimensions `m3/year`, equal and opposite contribution. Compare against independent exact continuum face-integral oracles (original latitude, longitude cosine, shifted sine with nonzero seam rate, rotated/degree-two and smooth nonharmonic positive data). Confirm both directions participate and cancel consistently near poles.
3. **Limiter and CFL:** use low-order invariant-domain update and single shared high-minus-low limited correction per face. Prove/verify donor available-volume and receiver range-capacity bounds with a falsifiable CFL condition; reject bad time step before mutation. Log every face alpha, limiter activation rate and correction, positivity/maximum-principle and conservation residual. Do not silently clip/renormalize or grant order>=1.5 if the limiter activates and destroys smooth-mode accuracy.
4. **Stage scope and stop rules:** begin with rational 2x2 unequal-area local oracle and tiny spheres 16x8, 32x16. Require geometry+moment certificates, exact face flux checks, constant field and positivity before any 64x32/128x64/256x128 tests. If these prerequisites fail, stop and seal the actual failing numerical evidence; no automatic patch/tuning/retry. No automatic 2K/1000Y.
5. **Qualification contract to be run only as a separate approved later subgate R1-Q1:** port original Q1 **mathematical intents** (not import-shadowed V1 tests) and retain spatial order>=1.5 for L1/L2/Linf on **every** refinement 16x8→256x128 in both original harmonics at T=0.0001Y and half-dt<=5% of continuum L2 error, temporal order0.9..1.2 against valid **same-R1 semidiscrete oracle** (not V1's eigenvalue), conservation/nonnegativity/CFL, shifted-sine seam/rotation/degree-two/nonharmonic adversarial cases, native+B0 full-state direct/split 3Y/10Y separate-process restart plus corruption/stale/wrong-input negatives. For nonlinear/active limiter, do not fabricate an exponential exact-in-time R1 oracle; block until separately justified.
6. **Scalability preflight before larger meshes:** report actual patch-cell cardinality S, condition numbers, coefficient geometry packet sizes/hash, face count, assembly CPU/RSS, per-face kernel throughput, limiting and accepted CFL dt/substeps. Polar reconstruction patches can cover long latitude rings; do not promise bounded 3x3 stencil or near-linear scaling. Separate initialization costs from repeated numerical work, checkpoints, B0 and history outputs.
7. **Archive and recovery:** full native volumes, geometry/coefficient packets (or authenticated available bytes), source/runtime/config/mesh/initial-field identities, clock and pending accepted-step state, limiter regime and cumulative numerical budgets; exact B0 predecessor/high-water semantics, fail closed for corrupt, wrong/stale source. No unqualified same-directory orphan-tail recovery claims.

**Required I0 deliverables:** versioned source+test suite and finite numerical/geometry receipts where specifically authorized; `MOMENT_CERTIFICATES.csv`, `POLAR_FACE_ORACLES.csv`, `LIMITER_AND_CFL.csv`, `R1_SOURCE_CONTRACT.json`, `I0_BOUNDARIES_AND_STOP_REASONS.md`, full SHA/manifest and performance traces for actually executed tests only. If I0 is preparation-only, mark `CREATED_NOT_RUN`, not numerical PASS. Qualification status must be explicit and separate from design status.

## High-level scientific boundary

No qualified global time evolution exists across six HR1 grids, despite global T0 input data and 2K synthetic archive throughput. R1 is still a **manufactured test-only diffusion equation** with artificial `kappa`, `h`, no source-backed ARCANA cover/material/ecology/Deep forcing or full coupling. A method qualification at256x128 would not certify 2K×1000Y global scientific history. Distinguish physical integration resolution, retained causal data resolution and visualization pixels.

```yaml
HR2_P1_R1_DESIGN: PASS_REVIEWED_POLAR_CELL_AVERAGE_CONSERVATIVE_METHOD_OPERATOR_REPORTED
HR2_P1_R1_I0_IMPLEMENTATION: PROPOSED_NOT_AUTHORIZED_NOT_EXECUTED
HR2_P1_R1_Q1_NUMERICAL_QUALIFICATION: NOT_EXECUTED
HR2_P1_V1_Q1: BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE
HR2_P1_D1: BLOCKED_REQUIRED_SPATIAL_DIAGNOSTICS_NOT_RETAINED
HR2_P1_D2: PASS_MEASURED_POLAR_ERROR_AND_FLUX_ATTRIBUTION_OPERATOR_REPORTED
GLOBAL_1000Y_PHYSICAL_RUN: NOT_AUTHORIZED
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
```

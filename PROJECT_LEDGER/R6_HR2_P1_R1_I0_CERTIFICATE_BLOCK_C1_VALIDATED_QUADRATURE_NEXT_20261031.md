# ARCANA R6 — HR2-P1-R1-I0 blocked at first geometry certificate; next C1 certified integration audit

**2026-10-31.** Recorded from operator-provided FAIR report `docs/arcana/R6_HR2_P1_R1_I0_FAIR_20261031.md`, evidence `ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_I0_20261031_01`. This GitHub document is a handoff and not an independent execution on FAIR.

## Sealed outcome

`HR2_P1_R1_I0=BLOCKED_GEOMETRY_ENCLOSURE_AND_RANK_CERTIFICATION`. **One** actual staged launcher execution with **4 PASS groups**, followed by required FAIL on first `16x8` pole-adjacent EW seam face, ID 15→0, center latitude -78.75 deg, longitude 180 deg, a 48-cell radius-3Rdelta tangent patch. Original 317 frozen source/test/acceptance pins unchanged; old V1/Q1/D1/D2, R1 mathematical design, and existing archives intact; no auto repeat/patch, commit/push. R1 versioned additive code `experiments/hr2_p1_r1/{geometry,certification,limiter}.py` and tests/launcher were authored; no sphere state flux/time advancement, all-face pass, 32x16, full native/B0 or global numerical convergence occurred. R1 is **not qualified**.

Actual measured provisional packet:
- Numerical 15x15 rank 15, SVD cond **86.38407144247768**, min singular value **0.012927934870767792**. Observed quartic monomial reproduction residual **6.177934860990772e-15**; Gauss 16/32 moment matrix max difference **1.7763568394002505e-15**, normalized face derivative integral max difference **2.34187669256869e-17**.
- Independent certified moment *interval width* **13.39788393330181** against frozen width **2^-50 = 8.881784197001252e-16**; independent normalized-face interval width **6.000000000000001** against frozen width **2^-45 = 2.842170943040401e-14**.
- Weighted moment perturbation upper bound **10.42920026883136**, resulting singular-value lower estimate **-10.416272333961356**; actual rank / inverse and face derivative accuracy **NOT CERTIFIED**.
- Root: current Decimal60 whole-cell analytic-range interval enclosure is too dependent/loose to certify integrals; lacks validated tight integration remainder and full floating geometry error bounds. A pessimistic *valid bound* is not evidence the numerical matrix is singular. **Gauss16/32 agreement is not a rigorous integration-error bound**. Their observed difference larger than 2^-50 does not prove actual error must exceed the target; cannot silently accept it.
- Rational 2x2 low-order flux, rational shared limiter, constant/zero/invalid input controls, 16x8 sphere topology/area/face count passed within limited scope. These do not establish qualified spherical evolution.
- R1 source contract SHA256 `cf1ca8f7b8ab8a6ea59cec7867bf8e52521d2e3589b23b8336b24cd967fe46f8`; first failed coefficient packet SHA256 `ea34e081abe3cdca7c71e9d9c34d6dc01b8da8b11fa465706db6313f38bce48d`; packet remains `PROVISIONAL_NOT_CERTIFIED`.

## Next proposed gate: HR2-P1-R1-C1 (certification-mathematics only)

**Status PROPOSED_NOT_EXECUTED.** Do not resume I0 nor relax its frozen thresholds. Work in isolated new files/evidence roots; preserve original failed I0 coefficient packet, logs and source hashes. Goal: design/validate a truly tight, independently checkable **mathematical enclosure** of original integrated spherical cell moments and covariant face derivatives (including pole-adjacent patches), then rigorously bound matrix inverse / reconstructed face weights for original R1 candidate.

1. **Audit exact integrands, chart and numerical proof obligations**: current logarithmic tangent chart, sphere/polar geometry, area Jacobian, integration domain, face chart and covariant normal, polynomial basis scaling, indices/units and all mathematical singular/branch locations; identify integrand analytic regularity and whether the first face patch crosses chart branch/cut or a pole. Record independently exact/analytical spherical area and directional flux identities. Determine whether a claimed conservative inclusion genuinely encloses all errors including float input geometry and quadrature math.
2. **Replace coarse whole-cell natural interval arithmetic with rigorous localized bounds** *as a new optional certifier*, not altered physics. Candidate tools: spatial subdivision into angular boxes/cells, interval/Taylor models with explicit derivative-remainder bounds and outward rounding, rigorous high-order quadrature remainder, or exact analytic moment integrals wherever possible. Each algorithm must have independent error upper proof and explicit termination, not merely Gauss16/32 differences. Library availability on FAIR must be checked before use; no assumed installation, network acquisition or dependency upgrade. If independent directed rounding is unavailable, do not claim binary64/Decimal60 alone is interval-certified; design a separate high-precision reference and clearly label uncertainty.
3. **Matrix rank/inverse a posteriori**: instead of accepting float SVD rank as a proof, use interval enclosure of M and an approximate inverse R, bound a subordinate norm of `I - R M` (e.g. strictly <1) to prove invertibility/Neumann error, and propagate face functional plus solve/floating errors into certified face-derivative weights. Check units/normalization and any floating QR/SVD failure modes. Avoid using a crude all-entry perturbation norm if a tighter validated residual proves rank.
4. **Feasibility and precision check before programming a full solver**: the requirements are absolute widths `2^-50` on normalized moments and `2^-45` on normalized face integrals. Quantify binary64 ULP budgets, scaling/conditioning and whether full geometry+arithmetic enclosures can actually meet those numbers on the first polar patch. If mathematically unattainable under the declared representation, report `BLOCKED_CERTIFICATION_PRECISION_INCOMPATIBLE` and propose a **new reviewed contract** rather than changing the original thresholds. A rigorous tight bound must be understood as a source- and precision-specific claim, not a claim about geological accuracy.
5. **First-face evidence before further mesh work**: generate an independent single-patch C1 witness with enclosure widths for all15 moments, all face functionals, coordinate/normal/Jacobian error budgets, certified inverse residual and face weights. Compare source contract and saved I0 provisional matrix/coefficients but do not mutate them. A new additive certifier/test may run **only bounded certificate evaluations** on first face where authorized; do not advance time, run 32x16, launch full Q1, or modify R1 geometry/limiter until reviewed.
6. **Stop and deliver**: explicit `C1_INTEGRAND_AUDIT.md`, `CERTIFICATION_METHOD_AND_ERROR_BUDGET.md`, `FIRST_POLAR_FACE_ENCLOSURES.csv/json` with observation/certificate distinction, independent certification tests, tool/runtime/SHA/manifest and numeric resource costs only if actually run. Emit `HR2_P1_R1_C1=PASS_CERTIFIED_FIRST_POLAR_FACE_AND_INVERSE` only with rigorous, source-bound evidence fully satisfying frozen criteria; otherwise `HR2_P1_R1_C1=BLOCKED_<specific_reason>`. Either decision is **certificate-only**; never an I0/R1 convergence or physics PASS.

## Separate follow-up only after valid certificate

A revised I0 attempt must be separately versioned and explicitly authorized; rerun the original rational/limiter/topology tests and all-face geometry checks before any sphere flux/time. A correction to certificate implementation is **not** a physical-law correction. Remaining requirements: polar EW+NS moment-accurate flux, positivity/invariant-domain limiter under CFL, shifted-sine seam, original spatial order>=1.5 across 16x8→256x128, temporal convergence, full native/B0 restart and provenance. No real 1000Y global physical simulation permitted by this engineering certificate.

```yaml
HR2_P1_R1_DESIGN: PASS_REVIEWED_POLAR_CELL_AVERAGE_CONSERVATIVE_METHOD_OPERATOR_REPORTED
HR2_P1_R1_I0: BLOCKED_GEOMETRY_ENCLOSURE_AND_RANK_CERTIFICATION
HR2_P1_R1_C1: PROPOSED_NOT_EXECUTED
HR2_P1_R1_Q1: NOT_EXECUTED
V1_Q1: BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE
D1: BLOCKED_REQUIRED_SPATIAL_DIAGNOSTICS_NOT_RETAINED
D2: PASS_MEASURED_POLAR_ERROR_AND_FLUX_ATTRIBUTION_OPERATOR_REPORTED
ORIGINAL_317_PINS: UNCHANGED_OPERATOR_REPORTED
GLOBAL_1000Y_PHYSICS: NOT_AUTHORIZED
SCIENCE_AND_PRODUCTION_PROMOTION: false
```

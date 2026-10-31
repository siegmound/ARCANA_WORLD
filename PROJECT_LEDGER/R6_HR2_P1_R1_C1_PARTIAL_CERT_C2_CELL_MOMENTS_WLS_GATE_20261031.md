# ARCANA R6 — C1 partial rigorous certificate; C2 true cell moments, represented geometry and weighted LS next gate

**Date:** 2026-10-31. **Evidence basis:** user-supplied FAIR report `docs/arcana/R6_HR2_P1_R1_C1_FAIR_20261031.md` and sealed FAIR root `ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_C1_20261031_01`. GitHub ledger is documentary, not an independent FAIR run. FAIR worktree `r6/runtime-copy-r1-fair` at original HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787` is intentionally dirty, do not checkout/reset/merge/commit/push. **325 original source/test/config pins reportedly unchanged.**

## Closed factual outcome

`HR2_P1_R1_C1=BLOCKED_VALIDATED_CELL_MOMENT_AND_LS_INVERSE_BOUNDS_MISSING`.

C1 only analyzed the first 16x8 south pole-adjacent EW seam face (face15→0) and 48-cell reconstruction patch. `M` has 48×15 entries (720), one constant column (48 entries), 672 nonconstant entries; `J` has 15 face functionals; approximate left inverse `R` is 15×48. No old I0 retry, R1 sphere flux or time advance, 32×16, 1000Y, long run or solver edit.

Actual **partial rigorous** results:
- All 15 **ideal-chart normalized face polynomial derivative functionals** enclosed using mathematically justified exact-rational/dyadic 200-bit series/parity integrals: max rigorous width **3.758428878745978e-20**, satisfying unchanged `2^-45=2.842170943040401e-14` *for ideal J only*; 13 functionals exactly zero by ideal geometry/parity. These are not represented-chart J or propagated effective face weights.
- 48 constant cell moments have exact ideal integral [1,1], width 0.
- Exact rational Neumann residual `||I15-RM_archived||_infty ≈1.929488709969284e-14 <1` proves the **archived binary64 point matrix** full column rank. Does **NOT** validate true integral matrix or prove R equals the desired weighted least-squares inverse `(M^T W M)^-1 M^T W`.
- 672 nonconstant true cell moments, floating represented frame/chart and actual numerical geometry errors, weighted normal inverse, final face-weight propagation remain **UNCERTIFIED**. Old range-family residual norm≈617.218≥1 is inconclusive.
- A constant **stored approximation** differs from exact integral 1 by `1.1102230246251565e-15`, greater than frozen `2^-50=8.881784197001252e-16`. Thus one interval simultaneously enclosing both that stored approximation and exact target cannot have the frozen width; this does **not** prohibit a thin certificate of the true integral [1,1] **plus separate approximate-coefficient error budget**. Clarify these separate targets, rather than silently weakening the threshold.
- C1 found no proved precision incompatibility. Its first certifier wrapper failed before numerical certificate due to Path/string mismatch; that failure is preserved. A repaired separate v2 ran one mathematical certificate (0.706856s observed, 20MiB kernel RSS) with no original R1 import, solver run or I0 retry. Do not claim zero failed tool executions.
- Method evidence: ideal-chart fixed 8-term sine/geometric polynomial, explicit remainder, Machin rational pi bounds, 200-bit outward dyadic endpoints. Chart normal derivative has a removable near-zero limit; naive floating `(a*q-1)/s²` is unstable there. Localized moment integration remains unimplemented.

Immutable source/packet identities from historical report:
- I0 contract `cf1ca8f7b8ab8a6ea59cec7867bf8e52521d2e3589b23b8336b24cd967fe46f8`
- I0 first face coefficient packet `ea34e081abe3cdca7c71e9d9c34d6dc01b8da8b11fa465706db6313f38bce48d`
- I0 original FAIL `HR2_P1_R1_I0=BLOCKED_GEOMETRY_ENCLOSURE_AND_RANK_CERTIFICATION`; unchanged V1 Q1 FAIL, D1 BLOCKED, D2 diagnostic PASS, R1 mathematical design PASS.

## C2 proposed objective and precise authority

`HR2_P1_R1_C2` is a **new mathematically validated certification-only gate** for the same original first polar face and same I0 width criteria; **PROPOSED_NOT_EXECUTED** by this entry. C2 may implement and run a separate opt-in *certificate script* only under explicit new operator/user scope; no R1 geometry/stencil/limiter edit or physical time advancement.

The goal is a fully source-bound certificate for **ALL 720 true moments + all 15 represented-face functionals + weighted-LS mapping/effective shared-face weights** with explicit precision, and finite a-posteriori inverse bounds. Begin with a small nonconstant moment pilot, stop upon proved breakdown. Do not attempt full all-face I0 or 32x16 until C2 closure.

### C2 stage 0 — meanings of the two geometries and original thresholds

Before implementation or numerical certificate:
1. Freeze the full mathematical source target: ideal spherical face-frame/chart `T0`, represented binary64 frame/chart `T1`, archived Gauss16/32 estimates `M_hat,J_hat,R_hat`, exact integral target `M_true,J_true`, and active solver effective coefficients. Specify whether each width condition measures enclosure of an **exact target**, difference from a stored approximation, or total propagated solve/flux error. Do not conflate. The frozen acceptance `moment_width<=2^-50` and `normalized_face_width<=2^-45` are unchanged; any semantic ambiguity is a BLOCK requiring reviewed addendum, not a unilateral reinterpretation.
2. Map 48×15 moments, per-cell owner topology, quadrature domains, normalized tangent basis, spherical measure, weights `W`, and exact representation of frame vectors/trigonometric/normal/derivative limits. List independent float and roundoff error terms and target-sensitive ULP budgets for each.
3. Use **strict deterministic, hash-pinned** first-face archived packet. Verify old 325 pins, C1 inputs and manifests, and old I0 FAIL. Work only in exclusive external C2 evidence root.

### C2 stage 1 — rigorous nonconstant moment integration

Use the mathematically motivated expansion `acos(q)/sqrt(1-q²)` in nonnegative powers of `1-q` (with coefficient ratio `c_{n+1}/c_n=(n+1)/(2n+3)<1/2`) on a **proved** patch-wide `q` range; derive explicit tail and derivative bounds. Integrate finite monomials/products using analytic spherical trigonometric identities with exact rational pi bounds, or rigorous localized interval/Taylor/adaptive quadrature with outward arithmetic and a proven termination criterion. Do NOT claim Gauss16 vs Gauss32 agreement is a proof. Preserve exact cancellations and correlations, including chart dependencies and polar-area weighting. If q bounds/series convergence cannot be globally proven or chart crosses a branch, fail explicitly. Demonstrate on one selected nonconstant moment then all 672. Retain exact rational/dyadic interval endpoints, widths, code SHA, proof formula, and independently checked cancellation/constant controls. Do not materialize expensive symbolic expressions without measured memory/time bounds.

### C2 stage 2 — represented geometry and weighted-LS/inverse

Certify the **represented** T1 geometry and how actual binary64 trigonometric inputs, tangent basis, normal vectors, Jacobian, quadrature and summation perturb integral targets. Distinguish ideal-to-represented differences from representation-to-archived coefficient errors. Obtain interval matrices `M_true`, `J_true` and bound `A=M_true^T W M_true`, `B=M_true^T W` with proper SPD/weighted assumptions; certify `A^-1 B` through a *mathematically correct* residual bound (e.g. `||I-R_A A||<1` in a specified submultiplicative norm, where R_A approximates A^-1), then propagate to effective face weights `w=J_true A^-1 B`. The earlier `||I-R_hat M_archived||<1` only proves point-matrix rank and cannot replace this. Explicitly quantify error between certified `w_true` and effective R1 **implemented** face weights. If solver uses `J_hat R_hat` or QR instead of normal-equation weights, prove its precise relationship to the intended WLS map; no symbolic sleight of hand. Check floating arithmetic/condition of normal equations vs QR; prefer validated QR or residual-based bound where tighter, while preserving exact target definition.

### C2 stage 3 — independent tests and closure

Require a separate independent verifier and negative controls (deliberately corrupted moments, frames, face derivative, W, R, source and packet), exact constant [1,1], sum/orientation checks, moment/face asymptotics and bound interval inclusion for all 720+15 components. Independent reproduced arithmetic must have explicit outward-rounding semantics, not unverified Decimal60/float assumption. Test numerical leakage across both EW and NS eventually, but **C2 scope is this first EW face only**.

Artifacts: `C2_TARGET_AND_PRECISION_SEMANTICS.md`, `CELL_MOMENT_ANALYTIC_PROOF.md`, `FIRST_FACE_720_INTERVALS.csv/json`, `REPRESENTED_FRAME_ERROR_BUDGET.md`, `WEIGHTED_LS_INVERSE_CERTIFICATE.json`, `FACE_WEIGHTS_PROPAGATION.csv`, `SOURCE_AND_PRECISION_CLOSURE.json`, manifest/finalization, actual CPU/RSS/cost for any executed certificate, and `STOP_REASON.md`.

Gate `HR2_P1_R1_C2=PASS_COMPLETE_FIRST_POLAR_FACE_CELL_MOMENT_AND_WLS_CERTIFICATION` **only if** all original width/accuracy/geometry/singularity/rounding and effective face-weight conditions are met with independently checkable bounds. Otherwise `BLOCKED_<specific_reason>` with complete partial evidence. A partial face/moment bound is not an R1 numerical PASS, does not authorize I0 rerun, all-face geometry, any sphere solver steps, native/B0, or 2K×1000Y.

## Preservation and long-term goal

Original 325 pinned code/test/config files and old Q1/D1/D2, R1-DESIGN, I0, C1 sealed archives remain immutable. No automatic FAIR commit/push, source rewrite, data download, precision/threshold change, full solver or long physical run. ARCANA's goal remains source-grounded multi-domain geologic/Deep/biotic causal history with true spatiotemporal query/zoom, not mere HD serialization. R1 is still an artificial-coefficient manufactured diffusion test and not an admitted global geology operator.

```yaml
HR2_P1_R1_C1: BLOCKED_VALIDATED_CELL_MOMENT_AND_LS_INVERSE_BOUNDS_MISSING
HR2_P1_R1_C2: PROPOSED_NOT_EXECUTED
HR2_P1_R1_I0: BLOCKED_GEOMETRY_ENCLOSURE_AND_RANK_CERTIFICATION
HR2_P1_R1_Q1: NOT_EXECUTED
ORIGINAL_PINS: 325_UNCHANGED_OPERATOR_REPORTED
GLOBAL_PHYSICS_1000Y: BLOCKED_NOT_AUTHORIZED
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
```

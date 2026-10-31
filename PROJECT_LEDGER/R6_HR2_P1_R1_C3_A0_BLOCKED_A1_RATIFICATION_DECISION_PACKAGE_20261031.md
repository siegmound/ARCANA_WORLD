# ARCANA R6 — HR2-P1-R1-C3-A0 blocked: C3-A1 authorial target/error-budget decision package

Recorded 2026-10-31. Documentary status ONLY. Source is the FAIR operator's full pasted report `docs/arcana/R6_HR2_P1_R1_C3_A0_FAIR_20261031.md`, external sealed root `ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_C3_A0_20261031_01`. FAIR operator verified 325 original pins and 699 historical members unchanged; 26 new file members sealed. This connected GitHub document is not an independent run, source audit or authorial ratification.

## Current immutable stop

`HR2_P1_R1_C3_A0=BLOCKED_REQUIRES_TARGET_AND_ERROR_BUDGET_RATIFICATION`.
`C3_B=NOT_AUTHORIZED_NOT_EXECUTED`.
C3-A0 was read-only source-bound design review. No integrals, reconstructed coefficients, inverses, geometry assembly, new numerical method tests, I0 retries or sphere evolution. C1/C2 partial mathematical witnesses remain valid **only within their named ideal/archived-point targets**, while full represented first-face and WLS accuracy is uncertified. Original 325 pins unchanged. The C3-A0 revised addendum status is `REVIEW_COMPLETE_REQUIRES_DESIGN_RATIFICATION_NOT_ADOPTED`; it must NOT be silently marked adopted by this GitHub handoff.

### Important direct-source facts (FAIR review, not newly verified here)

- `sphere()` creates a grid by `linspace`; `moments()` independently constructs rounded `pm/lm` and affine Gauss nodes, divides by its own rounded angular-area denominator, not necessarily `mesh.areas`.
- `W` uses normalized mesh areas and rounded `sqrt(W)` in weighted SVD. The exact mathematical geometric `W`, archived `What`, and the actual machine's sqrt-weight vector should not be conflated without a source/packet proof.
- `face_integrals()` uses face centers, true east/north conormal convention, geometric R factor cancellations. On face15→0 longitude seam, orientation is eastward.
- For a unit physical position p and *possibly not exactly normalized* frozen frame vector ubar, use `gamma=||ubar||`, `Q=(p·ubar)/gamma`, and analytic `a=acos(Q)/(gamma*sqrt(1-Q²))`. Its analytic removable zero limit is `1/gamma`, while `chart()` uses literal fallback `1`; `face_integrals()` has a direct near-zero division. Do not silently equate analytic T1a to the rounded T1b implementation, claim an implemented fix, or ignore float errors.
- Actual source computes a rounded row `ghat=-Jhat Rhat`, then `kappa*dot(ghat,h-h_anchor)`. Define `H=I-1 e_anchor^T` with dimensionally/orientationally checked vector slots; the exact linear form on h is `g_eff=ghat H=ghat-e_anchor^T sum(ghat)`. A true WLS construction for any chosen target is `P=(M^T W M)^-1 M^T W` and shared-face physical sign is `g_true=-JPH`. Arithmetic in subtraction, dot, multiply and limiter remains separate.

## Recommended choices requiring authorial ratification (NOT yet decisions)

| ID | Issue | Recommended candidate, conditional on checking exact source/archived bytes | Not allowed |
| --- | --- | --- | --- |
| D1 | Represented angular domains and normalization | Define **T0** immutable ideal sphere/frame/true cell area; **T1a-code** as real-analytic continuation with precisely named rounded source-domain endpoints/face centers/normalizer, using source's `N_code` denominator for *operator-fidelity*. Define independent **T1a-mean** with the exact area of the chosen represented domain for cell-mean/oracle comparison. Track both and their bias, do not label N_code an exact mean. **T1b** captures all actual rounded node/trig/sqrt/QR/dot operations. The source intermediate `pm/lm/d/area/face-node/sqrt` values not in the packet must be captured under separate instrumentation/evaluation authority or fully enclosed from executable operations. | Silently select ideal area for the source's N_code or reconstruct missing intermediate bits as though archived. |
| D2 | Weighted-LS W | Use the actual source **weighted-SVD objective** as primary operational target: explicitly capture weighted data and (if appropriate) `sqrt(What)` binary64 values and distinguish the exact mathematical `Wop` defined by those represented weights from an independent `Wgeo` on ideal areas. Determine whether the archived `What` truly corresponds to weights squared in the source's QR/SVD; if unproved, keep D2 BLOCKED. | Reinterpret `Wgeo` as source W or assume `What` equals rounded `sqrt(W)^2` without comparing source bytes. |
| D3 | J normalization | Preserve frozen ideal T0 normalized face width semantics as source of historical C1, and separately define T1a-code face normalization using the **actual code's** rho, face length, true/shared orientation, conormal sign and physical units. Width `2^-45` applies separately to exactly named normalized face target; do not average ideal/represented intervals. | Hard-code 4/3 or8/9 correction; alter orientation/units silently. |
| D4 | Integral enclosure vs coefficient bias | Keep existing **`2^-50` moment width** and **`2^-45` normalized-face width** as separate upper limits on rigorous exact-target integral interval widths. Independently report true-target-to-archived-point bias and numerical coefficient errors; no additional joint-hull requirement without distinct ratification. Preserve original intended scientific target T0 and require a separately certified T0→represented deviation. | Pretend intervals enclosing exact1 must include a stored approximate entry at1+1.11e-15 under the same frozen width. |
| D5 | Propagated-weight/runtime errors | Define separate **dimensionless** `||g_true-g_eff||_1` row-weight bound (source orientation checked), `m3/model-year` signed face-rate bound `E_Q<=|kappa| ||g_true-g_eff||_1 ||h-h_anchor||inf + E_float`, and derived state-height error via time-step/area and shared face counts. Require positive, predeclared, *independently justified numeric* error budget against original manufactured method acceptance before any source-complete geometry PASS. **Propose** at most 10% of an independently derived analytic a-priori allowed truncation/consistency error for each required mesh/mode as a certification error allocation; do not confuse it with the original 5% main/half-dt lane. That 10% is a new recommendation pending approval, NOT an old criterion or presently computable numerical claim. If its numerical reference and independent bound cannot be fixed before new runs, D5 remains BLOCKED. | Quietly reuse 2^-45 as an effective-weight bound, drop runtime floating errors, or determine budgets from failing data post hoc. |
| D6 | Quartic pilot and complexity | After ratification, separately authorize a first owner-cell0 `xi² eta²` quartic moment, analytical interval remainder and independent verifier tests frozen before launch, with bounded local terms/bit growth and measured resource checks. Report source's N24 expansion structural maximum **176851 distinct monomial keys** as a calculated upper bound, NOT observed use or full-memory cap; cap peak intermediate objects separately, fail without auto tune. Stage only ONE pilot before 671 remaining integrals. | Claim linear pilot generalizes to degree4 or run automatic mass generation. |
| D7 | Claim scope | First certify **only the frozen 16×8 first polar seam face and its specific packet / source runtime instance**. Do not claim arbitrary caller dtypes, unseen f32 inputs, alternate BLAS/libm, other mesh faces or generic API. Later separate gates for full faces, other grids and caller/runtime contracts. | Promote one packet/first-face proof to universal R1 method accuracy. |

This is a *recommendation for authorial decision*, not a statement that the user already ratified it. Requested authorial choice should be captured in an append-only `AUTHORIAL_RATIFICATION.json` specifying IDs D1-D7 accepted/modified/rejected, full exact clauses, source SHA, reviewer ID, date and explicit new output authority. If the author chooses only some decisions, make status PARTIAL, and block any C3-B stage requiring unresolved choices. If a decision changes frozen I0 design/meaning, require a separate versioned ratification with original unaltered and do not pass it off as simple clarification.

## Next proposed gate: C3-A1 signed ratification package, REVIEW ONLY

1. Read the complete FAIR C3-A0 report, `REVISED_TARGET_ADDENDUM.json`, `TARGET_MATRIX.csv`, `SEMANTIC_CHANGE_LOG`, `RANK_AND_SCALE_ADDENDUM`, `ERROR_BUDGET_AND_WLS_CONDITIONS`, `C3_B_TEST_FIRST_PLAN.md`, original design, I0 source and captured packet. Independently adjudicate all seven exact choices, especially exact source `Wop` and N_code vs N_mean. The SHA-pinned C3-A0 file remains the actual proposal authority.
2. Draft source-versioned ratification packet; tie T0/T1a/T1b and archived values to explicitly hashed data/algorithm. Include separate mathematical target, true integral interval-width requirement, approximation bias, certified WLS/inverse/effective recentered weights, binary64 runtime error, and conservation/positivity impact.
3. For the proposed D5 10% allocation, provide a **rigorous analytic allowed-error derivation and numerical units**, or present it as pending (not approved) if preconditions missing. No new acceptance thresholds may be smuggled into I0 without explicit authorial ratification.
4. Decision gate is `C3_A1=PASS_EXPLICIT_AUTHORIAL_TARGET_AND_ERROR_BUDGET_RATIFICATION` **only after actual explicit user/authorial adoption**. Without it, `C3_A1=BLOCKED_AUTHORIAL_RATIFICATION_PENDING` even if a review packet is well formed. A source-bound technical review and a source-operator audit cannot sign on behalf of the author.
5. No new analytic integrals, certificate numerical runtime, solver changes, I0 retry, 32x16, long physics, Git commit/push on FAIR or scientific promotion in review-only A1.

## Only after adoption: possible C3-B

First source-bound quartic pilot (independent trigonometric-integral remainder; no unqualified cost guess), then staged 671 ideals and corresponding represented M/J, true WLS validation and effective-weight propagation with preserved thresholds. Stop at first actual certificate failure. This is a separate approval and execution scope. Even C3-B first-face PASS cannot substitute numerical sphere convergence or a physically admitted ARCANA global 2K×1000Y.

```yaml
C3_A0: BLOCKED_REQUIRES_TARGET_AND_ERROR_BUDGET_RATIFICATION
C3_A1: PROPOSED_REVIEW_AND_AUTHORIAL_DECISION_PENDING
C3_B: NOT_AUTHORIZED
R1_I0: BLOCKED_GEOMETRY_ENCLOSURE_AND_RANK_CERTIFICATION
R1_METHOD_QUALIFICATION: NOT_EXECUTED
ORIGINAL_325_PINS: REPORTED_UNCHANGED
REAL_GLOBAL_1000Y: NOT_AUTHORIZED
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
```

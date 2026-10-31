# ARCANA R6 — C3-A1 prepared, NOT ratified; authorial disposition and D5 quantitative proof next

Date: 2026-10-31. Documentary note from operator-supplied FAIR C3-A1 report and 25-file sealed evidence `ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_C3_A1_20261031_01`. This GitHub update is not FAIR execution, independent rehash or an authorial approval.

## Preserved state

`C3_A1=BLOCKED_AUTHORIAL_RATIFICATION_PENDING`. Seven clauses are prepared and remain UNSIGNED, with all recorded decisions null. Exactly 325 source/test/config pins and 725 historical members reportedly authenticated and unchanged. No new integrals, quartic pilot, weighted inverse, I0 retry, numerical R1 test or physics. Original C1/C2 partial certificates and prior Q1/D1/D2/design/I0 BLOCKED/PASS statuses retain scope. No C3-B authority.

## Decision recommendation (not approval)

Present the exact FAIR `FINAL_DECISION_CLAUSES.json` and `APPROVAL_SHEET.md` to the human author. Recommend the following **candidate partial disposition** for explicit authorial selection, conditioned on not rewriting existing numerical method or thresholds:

- **D1 recommended APPROVE_COMPARISON_POLICY_ONLY:** separately preserve source-fidelity `N_code` vs exact mathematical cell mean `N_mean` and independent ideal T0. Neither the source's rounded denominator nor area row scaling may redefine the true physical conserved mean. Missing intermediate bits/ratio bounds remain technical.
- **D2 recommended APPROVE_COMPARISON_POLICY_ONLY:** operational weighted SVD and its rounded `sqrt(W)` factors vs mathematical geometric WLS are distinct. Actual factors, objective, inverse/rounding remain uncertified; author approval cannot supply measured identities.
- **D3 recommended ACKNOWLEDGE_BASELINE:** retain exact original J normalization, shared-face sign/units, and separately specify represented target. Do not loosen thresholds.
- **D4 recommended ACKNOWLEDGE_BASELINE:** widths `2^-50` and `2^-45` are true-integral enclosure requirements for named targets. Stored approximation bias and runtime propagation are additional independently bounded quantities, NOT silently replaced by the interval width.
- **D5 recommended PENDING_NUMERICAL_PROOF:** only endorse a framework for separately dimensioned row-weight, face-flux, height, accumulated-state and limiter sensitivity budgets, without any approved numerical 10% allocation or new row-weight threshold. Numeric budgets must be independently derived pre-execution and formally accepted in a separate reviewed clause.
- **D6 recommended APPROVE_PLAN_NOT_EXECUTION:** test-first single owner-cell0 quartic `xi²eta²` proof/complexity pilot and stop conditions. Does not permit C3-B execution.
- **D7 recommended APPROVE_NARROW_SCOPE:** first frozen 16x8 face15->0,48-cell packet and explicitly authenticated runtime/input envelope only. No claims about generic caller dtypes, other grid faces or six meshes.

Do not issue an authorial ratification receipt or mark any D as approved unless the human **explicitly accepts the exact clause(s)**. Partial approval must be recorded as PARTIAL and must not mark the bundle as PASS; in particular D5 still prevents source-complete gate.

## D5 missing proof: no ungrounded 10% allowance

Error envelopes must be separated into (i) certified integral intervals and geometric perturbations, (ii) WLS reconstructed effective row-weight error `b_g` including recentering H, (iii) floating-point row-evaluation error `E_float`, (iv) signed shared-face flux error `E_Q <= |kappa| b_g ||h-h_anchor||_inf + E_float` [m^3/model-year], (v) each cell update volume error `dt*sum_{faces} E_Q` and height error after dividing by true cell area, (vi) time accumulation, CFL/limiter nonlinear response and polar/timestep amplification.

No rule such as 10% of a theoretical truncation *upper* bound can establish an actual allowed error without an independently justified positive reference and full convergence requirements. One sufficient (possibly conservative) interval condition for observed intergrid spatial order p >= 1.5 when independent mathematical errors have certified bounds `E_h∈[L_h,U_h]` and implementation perturbations `<=δ_h` is `(L_h-δ_h) / (U_{h/2}+δ_{h/2}) >= 2^1.5`, with positive numerator, for each 16x8→256x128 grid pair, each original harmonic and each L1/L2/L∞ norm. This is an illustrative sufficient condition **not an adopted D5 criterion**, and its required L/U/δ values are currently unavailable. Temporal dt/half-dt condition <=5% remains separate. No fabricated numerical schedule.

## Next immediate action

Obtain **the author's explicit selection** of D1,D2,D3,D4,D6,D7 as policies/acknowledgments, or requested amendments; keep D5 formally PENDING. This can legitimately create an append-only `PARTIAL_AUTHORIAL_DISPOSITION` receipt only after actual user response; it is not C3-A1 PASS. Separately derive/test D5 error bounds in a new limited gate once the target semantics are approved and source/runtime intermediate bytes are available, then request explicit D5 ratification. Do not authorize C3-B until its prerequisites and a separate execution instruction.

```yaml
C3_A1: BLOCKED_AUTHORIAL_RATIFICATION_PENDING
D1_D2_D3_D4_D6_D7: RECOMMENDED_NOT_RATIFIED
D5: PENDING_INDEPENDENT_NUMERICAL_PROOF
C3_B: NOT_AUTHORIZED_NOT_EXECUTED
R1_I0: BLOCKED_GEOMETRY_ENCLOSURE_AND_RANK_CERTIFICATION
GLOBAL_1000Y_PHYSICAL: NOT_AUTHORIZED
```

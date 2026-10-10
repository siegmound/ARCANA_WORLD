# SI1/BW1 F2B-N1 — Numerical acceptance preconditions

## Decision

**`N1_NUMERICAL_PRECONDITIONS_DEFINED__ACCEPTANCE_NOT_YET_ATTESTED`**

This report defines what a later engineering solve would have to preserve and measure. It does not authorize a Solver run, qualify the SI1 operator, set a residual tolerance, or turn the historical F2A-V diagnostic into a successful solve. The original `BLOCKED_F2AV_QUALIFICATION` remains in force. `OPERATOR_CLASS_UNVERIFIED` and `THRESHOLD_UNJUSTIFIED` remain unresolved; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

No Fair, MPI, ShellSet, Solver, factorization, assembly, gauge, or simulation was run for N1. No ledger or canonical state was changed. The review is based on code checkout `dece4ac8c2279b0c30643a5166b77f02f3dfadd2`, the D2/D3A records and the historical ShellSet snapshot identified by source commit `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`.

## 1. Contract and identity of `A0 x = b0`

The numerical claim is about one exact pre-factorization linear system:

```text
A0 x = b0
r  = b0 - A0 x
```

`A0` means the assembled original SI1 matrix, before LU pivoting or any scaling/equilibration; `b0` means the original assembled forcing vector; `x` means the returned candidate solution, in the same DOF order, units and constraint formulation. A residual is bound to this system only if the matrix, RHS, dimensions, band parameters, ordering and any scaling/constraint transformations used for the solve have recorded identities. Hashing the post-factorization arrays does not identify `A0` or `b0`.

In the historical ShellSet source, `Solver` documents that `ab` is destroyed and the answer is written over `b` (`external/ShellSet-v1.1.0/src/MOD_Shells.f90:8630–8637, 8658–8672`). It passes `n=128884`, `kl=ku=727`, `nrhs=1`, `ldab=nKRows=2182`, and `ldb=nRank` (`:8644–8672`). The LAPACK driver contract agrees: its input band entries occupy rows `KL+1` through `2*KL+KU+1`; on return `AB` contains the LU factors and `B` contains `X` if `INFO=0` ([Netlib DGBSV](https://www.netlib.org/lapack/explore-html/db/df8/group__gbsv_gaff55317eb3aed2278a85919a488fec07.html), especially arguments `AB`, `B`, `INFO`). For SI1, `kl=ku`, so ShellSet's diagonal row `iDiagonal=1455` agrees with `kl+ku+1`; the reserved pivot-fill rows are not original matrix coefficients.

`INFO<0` denotes an invalid argument and `INFO>0` denotes an exactly zero diagonal entry in `U`, so the factor is exactly singular and the solve was not computed. `INFO=0` establishes only successful completion under LAPACK's routine contract; it is not a residual, conditioning, forward-accuracy, or physical-validity result.

### Ways to keep or recover `A0` and `b0`

The D3A dimensions are `n=128884`, `kl=ku=727`, `LDAB=2182`, one RHS. Under the explicit D3A assumption of 8-byte real values, the complete DGBSV band array is 2,249,799,104 bytes; a separate complete `A0`-layout copy plus `b0` is another 2,250,830,176 bytes (2,249,799,104 + 1,031,072). These are arithmetic estimates, not measured memory headroom or RSS limits. A compact rectangular original-band representation with `kl+ku+1=1455` rows would occupy at most 1,500,209,760 bytes at 8 bytes/value, plus 1,031,072 bytes for `b0`; edge padding, indexes, descriptors, conversion work and runtime overhead are not included. No strategy is selected by these estimates.

| Strategy | What must survive DGBSV | Cost / benefit | Identity proof needed | Present status |
|---|---|---|---|---|
| Full copies of `A0` and `b0` | A byte-preserving copy of the full original band array and RHS, made before the call | Direct residual and norm calculation; highest explicit memory cost: 2,250,830,176 bytes under D3A kinds, in addition to the existing arrays | Pre/post fingerprints of original and copy; dimensions/layout; verify the solver receives the same originals represented by the copies; preserve copy until all checks finish | Design option only; Fair headroom, ABI and actual memory are not attested |
| Reassemble after the solve | A deterministic recipe plus the exact inputs, state, ordering, geometry, constitutive tangent, options and assembly environment needed to reproduce the call inputs | Avoids retaining a full copy during the solve, but repeats assembly and can diverge due to changed state, accumulation order, runtime or implementation | Rebuild `A0'`,`b0'`; compare all logical original-band entries and RHS to pre-call identities (prefer exact binary identity for same-build replay); separately test the rebuild's independent correctness. Matching summaries or maxima are insufficient | Not demonstrated; F2A reassembly summary agreement does not prove a future solve's `A0` identity |
| Immutable matvec/norm representation | An immutable representation that can evaluate `A0*x`, `||A0||∞`, and, for componentwise metrics, each row of `|A0|*|x|`, plus `b0` | Could use compact band or sparse storage; storage may be less than full padded `AB`, but no particular compression or memory benefit is established | Prove representation covers every original coefficient exactly once, excludes LU fill/padding, preserves signed values and DOF order, and reproduces independent small-matrix oracles; bind it to pre-call source matrix identity | Candidate design only; no production format selected or resource-qualified |

An “independent assembly” is not automatically an oracle: it can share the same element, tangent, mapping or scatter defect. A post-hoc checksum alone also cannot reconstruct a residual. Whichever path is eventually selected must preserve enough information to calculate the residual against the actual pre-call problem and show that the validation path and Solver call share one identified `A0,b0`.

## 2. Metrics and what they establish

For finite binary64 inputs interpreted as their exact represented real values, the relevant equations are:

```text
r_i       = b0_i - sum_j A0_ij x_j
rho_inf   = max_i |r_i|
||A0||inf = max_i sum_j |A0_ij|
eta_inf   = ||r||inf / ( ||A0||inf ||x||inf + ||b0||inf )
eta_c     = max_i |r_i| / ( sum_j |A0_ij| |x_j| + |b0_i| )
```

`rho_inf` is an absolute residual, dependent on units and scale. `eta_inf` is a normwise backward-error measure for a stated perturbation model; `eta_c` is a componentwise relative backward-error measure. They describe proximity to a nearby algebraic system, not error against the exact physical solution. A zero denominator with zero residual may be reported as zero only under an explicit convention; nonzero residual over zero denominator is undefined/infinite and must fail closed. Non-finite inputs or results and overflow/underflow in a diagnostic path cannot yield an acceptance PASS.

Four separate questions must not be collapsed:

1. **Formula correctness:** the equations above and the row/column mapping must be correctly implemented for the original general-band matrix. The matrix is not assumed symmetric.
2. **Evaluation error:** conventional floating-point residual evaluation can lose information through cancellation or underflow. Under the usual model for a length-`m` dot product, with unit roundoff `u` and absent overflow/underflow, a standard forward error bound is expressed using `gamma_m = m*u/(1-m*u)` multiplying `|A0||x|`. Here the number of represented coefficients in a row is at most `kl+ku+1=1455`; this is a model bound under assumptions, not an observed SI1 error bound. The final subtraction and norm/reduction add their own rounding. Actual summation order, FMA behavior, compiler flags, BLAS/LAPACK implementation and subnormal mode must be known before applying a runtime bound.
3. **Acceptance threshold:** a threshold decides whether a measured algebraic error is acceptable for a specified engineering use. Neither a floating-point unit roundoff nor a dimension-based `O(nu)` estimate automatically supplies that policy. No current ARCANA authority connects a solve tolerance to a required engineering output tolerance. Therefore `THRESHOLD_UNJUSTIFIED` remains.
4. **Forward and physical accuracy:** forward error depends on conditioning as well as backward error; discretization, input uncertainty, model/operator validity and physical interpretation are further separate sources. A small backward error cannot by itself establish small forward error or physical validity.

The SI1 band is large and the historical matrix had a reported coefficient range of about 18.41 decimal orders, but magnitude range is not a condition number. The F2A-V evidence reported 10 above-threshold asymmetric pairs among 93,434,040 checked pairs; one is zero/nonzero, the largest pair-relative discrepancy is 1, while the maximum row-scaled discrepancy among those ten is approximately `1.91e-19`. The maximum absolute discrepancy over all compared pairs was `7.8652252401724544e16`. D2 leaves the cause unknown and finds theoretical SI1 symmetry indeterminate. None of these figures chooses an acceptance tolerance or attributes the asymmetry to geography, physics or an implementation defect.

### Robust calculation and numerical evidence required

The D3B-P0 validator computes exact rational diagnostics from the exact binary64 values supplied to its bounded synthetic fixtures. This avoids hidden rounding in its own algebraic oracle and reports undefined when a result cannot be represented under its declared binary64 output policy. A runtime validator could use this approach only after resource/runtime cost is bounded; another appropriate implementation would use scaled norms and compensated/wider accumulation with explicit IEEE status. It must never mistake reserved pivot-fill rows for `A0` values.

For a future numerical assessment, retain at least:

- exact pre-solve dimensions, `kl`, `ku`, original-band storage convention, DOF order, source/input identities and checksums for `A0` and `b0`;
- returned `x`, LAPACK `INFO`, pivot data as required, any equilibration/scaling factors, and the identity/version of the routine and linked library;
- `rho_inf`, `eta_inf`, `eta_c`, all norms/denominators, finite/subnormal/overflow/underflow status and diagnostic precision/algorithm;
- a condition estimate tied to the same `A0` and factorization, and an independently justified forward-error or engineering-output requirement before classifying the answer acceptable.

The general-band LAPACK family offers relevant *assessment tools*, not a selection or authorization here. `DGBCON` estimates reciprocal 1- or infinity-norm condition using a `DGBTRF` factorization and requires the norm of the original matrix; it is an estimate, not an exact condition number ([Netlib DGBCON](https://netlib.org/lapack/explore-html/db/d34/group__gbcon_gaaa2c67f1dcb6d881766d172334c6d634.html)). `DGBRFS` performs refinement and estimates error/backward-error information using original and factored data. `DGBSVX` provides a condition estimate, iterative refinement and error bounds, but has additional inputs/work/storage and may equilibrate/overwrite data; its estimates and flags still need interpretation for the stated model and installed implementation ([Netlib DGBSVX](https://www.netlib.org/lapack/explore-html/d1/da6/group__gbsvx_ga38273d98ae4d598529fc9647ca847ce2.html), [Netlib DGBRFSX](https://www.netlib.org/lapack/explore-html/d1/d58/group__gbrfsx_ga094fe80bcbf074a148570039c0e7caa7.html)). A driver's built-in machine-precision warning is not automatically an ARCANA acceptance threshold. No routine was executed and no installed Fair library identity was re-established in N1.

The minimum evidence to close the threshold gap is a predeclared engineering claim (which reported quantity matters, units, acceptable output uncertainty and intended use), plus an error budget that relates the acceptance test to measured backward error, a condition/forward-error assessment and operator/input uncertainty. It must be reviewed before looking at a candidate solve result. Without that link, retain `THRESHOLD_UNJUSTIFIED` and do not convert the metrics into PASS/FAIL acceptance after the fact.

## 3. Operator, asymmetry, conditioning and null modes

D2 remains authoritative for the source/operator boundary and is not repeated here:

- **Continuum formulation:** BuildK's reciprocity conditions on the state-dependent `alpha` tangent are identified in D2, but the effective SI1 pointwise tangents were not retained. Whether the active constitutive tangent is symmetric is unverified.
- **Assembled matrix:** the historical diagnostic found 10 above-threshold pairs. F2-A reassembly summary agreement supports reproducibility of the reported summary, not independent assembly correctness. The source, census and partial DOF map do not prove a cause. Preserve `DOF_MAPPING_UNVERIFIED` for anomaly-to-geography/plate attribution.
- **Conditioning/rank/null modes:** these are different properties from symmetry and residual size. No condition estimate, numerical rank, nullspace basis or validated candidate rigid-mode residual is present. Lack of strict diagonal dominance is not proof of singularity. `nCond=0`, `nFl=0` and `trHMax=0` do not by themselves establish absence of all constraints or null modes. Do not add gauge, pinning, projection, symmetrization or mode removal in N1.

Before a future result is interpreted, its provenance must bind (a) actual pre-solve `A0,b0`, (b) the operator/source configuration that assembled them, and (c) the solution and diagnostic routine. The ten historical asymmetries need not be “explained away” to compute an algebraic residual, but operator classification and intended physical meaning remain independent blockers for scientific interpretation.

## 4. D3B-P0 validator and test review

Reviewed `scripts/r6_si1_bandwidth_f2b_d3b_numerical.py` and `tests/test_r6_si1_bandwidth_f2b_d3b_numerical.py` at the current checkout. The validator uses the DGBSV general-band layout, validates the complete `LDAB × n` shape and rejects nonzero padding/fill entries, validates finite real inputs, bounds synthetic dimensions/work before copying/conversion, and preserves its arguments. Its arithmetic converts each binary64 operand to an exact `Fraction`, calculates the matvec, infinity norms and normwise/componentwise formulas, and explicitly returns `THRESHOLD_UNJUSTIFIED` as the solver-acceptance state. Undefined binary64 result/subnormal conversions do not silently pass.

Existing tests cover both `kl<ku` and `kl>ku`, upper/lower-only and edge bands, a hand-calculated residual and both backward errors, a separate test-only dense matvec oracle, immutability, non-finite and malformed inputs, reserved fill storage, zero/zero policy, extreme normal/subnormal/overflow values, and early synthetic size guards. This is adequate evidence for the bounded validator's formula/layout contract, not for ShellSet's Fortran call, SI1 data, LAPACK implementation, runtime IEEE behavior, resource use or scientific acceptance. The suite's previous D3B-P0 review reports 24 passed and 2 platform-skipped symlink tests across the resource and numerical test modules; those aggregate counts are not a new N1 run.

No demonstrated defect in the D3B numerical formulas or their independent fixture oracles was found in this review, so N1 adds no test or implementation change. A future test gap would arise only if a changed validator, LAPACK adapter or chosen A0-preservation path is introduced; then add focused tests for that interface and mutation boundary rather than a new framework.

## 5. Preconditions for an engineering solve decision

All of the following are prerequisites, not claims already satisfied:

| Precondition | What passes the check | Current evidence / gap |
|---|---|---|
| Original linear-system identity | `A0`, `b0`, dimensions, band format, DOF order and input configuration are captured/identified before the destructive call and remain available for post-solve checks | No pre-solve A0/b0 record or strategy qualified |
| Solver call semantics | Actual routine/backend, integer ABI, INFO, call count and modifications are recorded; `INFO=0` is not treated as acceptance | Source says DGBSV; exact historical loaded LAPACK identity and full ABI remain unverified |
| Residual calculation | Independent check computes `b0-A0*x` with validated original storage, finite checks, normwise and componentwise metrics, and explicit range/zero-denominator policy | D3B validates formulas only on small synthetic fixtures; no SI1 solve/result exists |
| Conditioning and forward relevance | A condition estimate/error bound is tied to the same unscaled/equilibrated operator and interpreted against the requested output claim | No condition or forward-error evidence; numerical policy absent |
| Operator interpretation | The operator and active tangent/support/state are identified; asymmetry is not silently assigned a cause; any physical conclusion has separate authority | `OPERATOR_CLASS_UNVERIFIED`; D2 reciprocity inputs and ten-pair cause remain unknown |
| Acceptance rule | A prior, domain-specific error budget justifies thresholds; no post-result threshold fitting | `THRESHOLD_UNJUSTIFIED` |
| Resources/operational safety | Actual backend/toolchain and enforced resource/run limits meet a separately approved one-attempt plan | D3D-RO6 leaves ABI/library identity, actual resource enforcement, RSS/PSS/cgroup and full manifest checks incomplete |
| Scientific authorization | Explicit separate approval permits the specific engineering Solver action; it does not imply mechanics or canonical authority | `F2B_SOLVER_EXECUTION_AUTHORIZED=false` |

## 6. Next technical action

Do not create another general design gate. The next technical action is to prepare a bounded **synthetic pre/post-call identity harness** around the existing D3B diagnostics: construct small nonsymmetric band `A0,b0`, preserve a copy, invoke no factorization, deliberately mutate working buffers to model DGBSV's documented overwrite, then prove the validator still checks only the immutable originals and returned `x`. Include wrong-band-order, changed-RHS and substituted-matrix negative cases. This closes an actionable software-interface gap without running DGBSV or SI1. Keep production strategy selection pending resource evidence; after that harness and independent numerical-policy authority, any real SI1 solve still needs explicit authorization.

## Sources reviewed

- Repository authority: `AGENTS.md`; `PROJECT_LEDGER/README.md`, `STATUS.md`, `NEXT_ACTION.md`, `ROADMAP.md`, `PROCEDURE.md`, `EVIDENCE_INDEX.md`.
- `docs/arcana/SI1_BW1_F2B_D2_OPERATOR_CLASSIFICATION_AUDIT.md` — D2 operator/tangent and ten-asymmetry status.
- `docs/arcana/SI1_BW1_F2B_D3A_ATTESTABILITY_AUDIT.md` — resource formulas, A0/b0 alternatives, residual/error definitions and threshold status.
- `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md` — F2B stage boundaries.
- `scripts/r6_si1_bandwidth_f2b_d3b_numerical.py`; `tests/test_r6_si1_bandwidth_f2b_d3b_numerical.py`.
- Historical ShellSet at `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`: `external/ShellSet-v1.1.0/src/MOD_Shells.f90:8626–8692`; the vendored LAPACK interface declarations in `external/ShellSet-v1.1.0/src/lapack.f90` are source declarations, not proof of the Fair-linked library.
- LAPACK primary routine documentation: [DGBSV](https://www.netlib.org/lapack/explore-html/db/df8/group__gbsv_gaff55317eb3aed2278a85919a488fec07.html), [DGBCON](https://netlib.org/lapack/explore-html/db/d34/group__gbcon_gaaa2c67f1dcb6d881766d172334c6d634.html), [DGBSVX](https://www.netlib.org/lapack/explore-html/d1/da6/group__gbsvx_ga38273d98ae4d598529fc9647ca847ce2.html), [DGBRFSX](https://netlib.org/lapack/explore-html/d1/d58/group__gbrfsx_ga094fe80bcbf074a148570039c0e7caa7.html), [LAPACK Working Note 165](https://www.netlib.org/lapack/lawnspdf/lawn165.pdf).

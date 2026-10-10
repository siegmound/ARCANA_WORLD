# SI1/BW1 F2B-D2 — ShellSet operator classification audit

## Decision

**OPERATOR_CLASS_UNVERIFIED. Theoretical symmetry is INDETERMINATE for the SI1 operator.** The source exposes sufficient reciprocity conditions under which the active continuum tangent would be symmetric, but the run evidence does not retain the pointwise tangent needed to verify those conditions. The measured assembled diagnostic is not exactly symmetric: ten pairs exceed the relative threshold. This neither proves an intrinsically nonsymmetric formulation nor identifies an assembly defect. No matrix was symmetrized and no Solver is selected or authorized.

Scope is static source analysis at historical ShellSet commit df670c8c4faaed641997f5c4bdb701e2ba0afc7d, plus review of the existing F2A-V original/recovered evidence. No Fair, MPI, Solver, factorization, assembly, simulation, gauge change, or canonical state access was performed for this audit.

## Provenance and run boundary

- Historical source: external/ShellSet-v1.1.0/src/MOD_Shells.f90 at the commit above. The D1B report records the exact source identity and source-verified local component convention.
- F2A-V original decision remains BLOCKED_F2AV_QUALIFICATION; its retained execution stopped with MPI status 75 before Solver.
- Offline evidence reviewed: outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/F2AV_RECOVERY_RESULT.json (SHA256 ff32569dc56f500725ca45c790d7e3ea925bc1e99df5d28138e6342ab4b9979f), F2AV_RECOVERY_ARTIFACT_MANIFEST.json (SHA256 3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f), and BW1_F2AV_ASYMMETRY_CENSUS_NORMALIZED.csv (SHA256 2d78c9ee6756c75e1d433340a39faf796bcb04027bc04c9e2d6a6c24f6614cde).
- Recovery verdict is F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION; it does not replace the original blocked qualification.
- D1A established a partial nodal/index map. D1B source-verified ShellSet component slots as slot 1 = +South/+theta and slot 2 = +East/+phi in the historical ShellSet basis. ARCANA geographic authority and attribution of census pairs to geographic locations/plates remain DOF_MAPPING_UNVERIFIED.

## BuildK formulation and reciprocity

BuildK assembles a two-component nodal continuum tangent over seven triangular quadrature points. Its continuum contribution has the structure:

K_e[(p,i),(q,j)] = (A_e/R^2) sum_m w_m detJ_m B_(p,i,m)^T C(alpha_m) B_(q,j,m)

B is the strain-rate operator formed from dXS, dYS, spherical factors, and fPSfer; C(alpha) is the constitutive tangent represented by alpha. This is a structural reading of source loops/products, not a newly evaluated matrix. The source includes factors involving 1/sin(sita), 1/tan(sita), and fPSfer; paired test/trial geometric factors enter the block assembly. Terms are weighted by quadrature weight, Jacobian determinant, area, and radius scaling, then scattered to global odd/even component slots.

For stress rows (t_xx,t_yy,t_xy) and strain columns (e_xx,e_yy,e_xy), the BuildK shear convention yields these sufficient alpha reciprocity identities for symmetry under the same real-valued quadrature measure and identical test/trial geometry:

- alpha(1,2) = alpha(2,1)
- alpha(1,3)/2 = alpha(3,1)
- alpha(2,3)/2 = alpha(3,2)

The factors of one half arise from the engineering-shear/constitutive pairing. For arbitrary independent strain components these identities are also necessary for the constitutive bilinear form to be symmetric. A particular assembled mesh can still exhibit cancellations, so an identity failure alone would not prove global asymmetry without evaluating assembly contributions.

Viscos describes alpha as derivatives of vertically integrated stress with respect to strain rate and obtains them through the active material calculation (Diamnd). Its nonzero-strain branch computes state-dependent tangent entries but does not impose or assert the identities above. A special zero-strain branch assigns symmetric normal entries and zero shear cross terms; that does not establish symmetry for SI1. Effective alpha values at quadrature points were not retained in F2A-V evidence, so the reciprocity test is unavailable for the observed run.

Keep three claims separate: constitutive reciprocity of the underlying law; reciprocity of the state-dependent linearized tangent returned by Viscos/material routines; symmetry of the realized floating-point matrix after quadrature and scatter. Current evidence establishes none of these for every active SI1 point; it does show the assembled diagnostic has ten above-threshold differences.

## Routine activity in SI1

| Routine/path | Source location | SI1 status and interpretation |
|---|---|---|
| BuildF | MOD_Shells.f90:1056–1245 | Active RHS construction. Starts with fBase (1113–1117) and includes continuum/prestress terms (1126–1151). Basal shear force requires trHMax > 0 (1153–1173); fault traction loops over nFl (1185–1243). With trHMax=0 and nFl=0 both paths are inactive. Aggregate force diagnostics do not separate fBase from continuum/prestress. |
| BuildK | 1247–1517 | Active continuum tangent; seven-point integration and global scatter. Optional basal drag (1457–1489) requires trHMax > 0 and pulled, so it is inactive. |
| AddFSt | 51–258 | Called from FEM; fault assembly loop starts at 111 and uses nFl. With nFl=0 it contributes no fault stiffness. |
| VBCs | 10012–10115 | Called from FEM; prescribed-velocity loop at 10056 uses nCond. With nCond=0 no such equations are imposed. This alone does not establish absence of every other constraint or null mode. |
| FEM call sequence | 3630–3785 | BuildF at 3707, BuildK at 3716, AddFSt at 3722, VBCs at 3727, Solver at 3732. F2A-V stops before Solver. |
| Solver storage/solve | 8626–8692 | LAPACK dgbsv at 8672 is a general real band driver. This identifies storage/driver, not operator symmetry or positive definiteness. It was not reached in F2A-V. |

KSize source path 5266–5392 sizes the general band system. Recorded dimensions: nRank=128884, kl=ku=727, nKRows=2182, iDiagonal=1455. General-band storage accepts nonsymmetric systems but does not prove the mathematical operator is nonsymmetric.

## Ten asymmetry records

The recovered comparison examined 93,434,040 upper-triangle pairs. Ten exceeded relative threshold 1e-12: nine NONZERO_VALUE_MISMATCH and one ZERO_NONZERO; no nonfinite pairs. Absolute discrepancy, pair-relative discrepancy, and row-scaled discrepancy are different quantities. The row-scaled metric divides by the larger L1 row scale.

| i,j | absolute difference | relative difference | row-scaled difference | classification |
|---|---:|---:|---:|---|
| 715,716 | 8.4696755077120016e13 | 2.7159541648303220e-1 | 3.8425066683416169e-18 | nonzero mismatch |
| 715,1258 | 1.4073748835532797e14 | 1.9999999999999996e-1 | 1.9088001878232093e-19 | nonzero mismatch |
| 63337,64061 | 6.8719853590891571e10 | 5.0655035721547392e-12 | 1.3483036467835701e-21 | nonzero mismatch |
| 64063,64787 | 6.8718731128134888e10 | 5.0680570851113771e-12 | 1.3482528723807624e-21 | nonzero mismatch |
| 64421,65145 | 2.0615870460364838e11 | 1.7518209105560345e-12 | 8.0900802323859013e-21 | nonzero mismatch |
| 127214,127215 | 7.0368547630322836e13 | 1.5646373086042331e-12 | 2.8069486661554114e-19 | nonzero mismatch |
| 128318,128873 | 1.4073748835532819e14 | 3.7037037037037090e-2 | 1.8887643310957950e-19 | nonzero mismatch |
| 128678,128873 | 1.4073748835532800e14 | 1.0000000000000000 | 1.9088001878231578e-19 | zero/nonzero |
| 128317,128874 | 7.0368744177663938e13 | 4.5454545454545414e-2 | 3.6446336918260586e-19 | nonzero mismatch |
| 128873,128874 | 1.3417477832704006e14 | 1.1700374531835211e-1 | 6.0872164461963597e-18 | nonzero mismatch |

The largest local relative discrepancy is 1 at (128678,128873), while row-scaled discrepancy is about 1.91e-19: large relative to that pair, tiny against the row scales. The maximum absolute discrepancy among these ten is 1.4073748835532819e14. Separately, the global maximum absolute difference across all compared pairs is 7.8652252401724544e16; it is not one of the relative-threshold census rows. No geography, plate, or physical cause is inferred from these indices.

F2A reassembly versus sealed F2-A passed the recorded tolerance (relative 1e-12, absolute 0): counts, maximum coefficient/forcing values, symmetry maxima and symmetry counts agree. This supports reproducibility of diagnostic summaries, not independent correctness of assembly or the intended physical operator.

## Other numerical observations and limits

- Matrix entries were reported finite; 128884 diagonal entries positive, none zero/negative. Reported 1804327 nonzero entries out of 186996964 valid band entries.
- Absolute diagonal-dominance classes: strict 0, near 0, nonstrict 128884, undefined 0; no zero diagonal or zero off-diagonal rows. Lack of strict dominance does not demonstrate singularity, ill-conditioning, or a nullspace.
- Maximum coefficient magnitude 3.6508239112970148e32; minimum nonzero magnitude 1.4073748835532800e14, about 18.41 decimal orders of magnitude. Range alone is not a condition estimate or error bound.
- F2A-V recorded inherited IEEE inexact and underflow flags, no inherited overflow. Phase inexact was recorded in BuildF, BuildK, symmetry, row/column statistics, and output aggregation; no phase overflow/underflow was recorded. Inexact is not a demonstrated cause of the ten differences. Underflow/flag attribution remains unknown. No new sticky-flag experiment was run.
- No condition estimate, spectrum, residual, backward error, nullspace test, or successful solve is available.

## Claim-to-evidence matrix

| Claim | Source/line | Equation or observable | Evidence | Status | Missing control |
|---|---|---|---|---|---|
| Continuum stiffness uses state-dependent tangent | BuildK 1247–1455; Viscos 10117–10513 | Quadrature sum of strain operators and alpha | Locked historical source; F2A-V BuildK ran | Formulation identified | Per-point alpha/state and independent reference assembly |
| Alpha identities suffice for reciprocal continuum blocks | BuildK 1310–1455; Viscos 10257–10258, 10399–10400 | Three identities above | Algebraic reading of paired products | Sufficient conditions derived; SI1 satisfaction unknown | Check active tangent and geometry/scatter pairing |
| SI1 tangent satisfies identities | Viscos 10391–10460 | Required weighted alpha relations | No pointwise alpha dump; general branch does not enforce relations | UNVERIFIED | Capture effective tangent or prove active-law reciprocity analytically |
| Basal drag contributes in SI1 | BuildK 1457–1489 | Scalar weighted paired products | trHMax=0 | Inactive | Not applicable to this case |
| Fault stiffness/traction contributes | AddFSt from 111; BuildF 1185–1243 | Loops over nFl | nFl=0 | Inactive | Not applicable to this case |
| Prescribed velocity equations constrain SI1 | VBCs 10056 onward | Loop over nCond | nCond=0 | Inactive | Inventory other constraint paths before nullspace claim |
| Realized matrix is exactly symmetric | Recovered F2A-V census/result | Ten above-threshold pairs of 93,434,040 | Result and normalized census hashes above | Exact diagnostic symmetry excluded at stated threshold; cause unknown | Pair-level contribution trace and accumulation-order analysis |
| Census indices map to geography/plates | D1A/D1B plus census | Raw DOF to node/component to frame | D1A partial; D1B source slot basis | DOF_MAPPING_UNVERIFIED for ARCANA attribution | Complete identity chain and ARCANA frame/support authority |
| No strict diagonal dominance proves nullspace | F2A-V dominance summary | Diagonal/off-diagonal row sums | No strict-dominance rows | Unsupported | Authorized independent nullspace/rank/residual evidence |
| Solver produced valid result/residual | FEM 3732; Solver 8626–8692 | dgbsv and outputs | Run stopped before Solver, MPI 75 | Not executed | Separate approved engineering preflight and numerical contract |

## Bounded next checks (proposals only)

Before a Solver decision, a separately approved diagnostic contract should specify how to:

1. retain active pointwise alpha, material state, derivatives, quadrature data, and element-local blocks without changing scientific assembly;
2. independently recompute selected blocks and compare scatter contributions, including orientation, component ordering, and duplicate accumulation;
3. evaluate reciprocity identities with scale-aware tolerances to separate constitutive, integration/scatter, and rounding effects;
4. link the ten pairs to element contributions only through an attested DOF chain, keeping geography UNKNOWN until ARCANA frame authority is proven;
5. characterize accumulation-order/precision sensitivity without mutating sealed inputs or promoting the original blocked run;
6. keep nullspace/gauge work independent, with explicit candidate modes, constraint inventory, and residual evidence rather than diagonal-dominance inference.

None of these checks was run. Any future Solver or factorization needs a distinct authorization and numerical acceptance contract.

## Preserved decisions and gates

- Original F2A-V: BLOCKED_F2AV_QUALIFICATION.
- Recovered diagnostic: F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION.
- Operator class: OPERATOR_CLASS_UNVERIFIED.
- SI1 theoretical symmetry: INDETERMINATE; sufficient reciprocity conditions identified, active values not attested.
- Anomaly-to-geography/plate attribution: DOF_MAPPING_UNVERIFIED.
- Nullspace/gauge/singularity/conditioning: UNKNOWN; not inferred from diagonal dominance.
- F2B_SOLVER_EXECUTION_AUTHORIZED=false. No symmetrization, solver selection, Fair/MPI/Solver/factorization/assembly/simulation, or canonical/WORLD_HISTORY change.

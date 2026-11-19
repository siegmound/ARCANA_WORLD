# HR2-P1-R1-DESIGN — conservative cell-average spherical method proposal

2026-10-31. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE. **Design only.**

`HR2_P1_R1_DESIGN=PASS_REVIEWED_POLAR_CELL_AVERAGE_CONSERVATIVE_METHOD`

Selected smallest prototype: **A, shared tangent-quartic cell-moment finite
volumes with conservative invariant-domain flux correction**. Same scalar native
cell volumes and true face topology; general polynomial reconstruction from
integrated spherical cell moments replaces the high-order midpoint gradient.
The4/3 and8/9 defects are diagnostic facts, never fitted correction factors.
A curved degree4 SIPDG formulation with additional dynamic moments was compared;
it needs a larger state, trace/penalty and coupled stability qualification.

This PASS records an internal mathematical/design-contract review, not external
peer review, numerical method qualification, solver implementation or execution
authorization. Actual geometry reconstruction certificates, limiter accuracy,
all original numerical orders, cost and native/B0 parity remain NOT_EXECUTED.
Failure of any future precondition blocks the candidate; no threshold relaxation
or automatic method tuning is part of this design. Q1/D1/D2 history stays intact.

## Read sources, identity and actual D2 evidence use

Read in full R6_HR2_P1_R1_DESIGN_TASK.md and the FAIR D2 report. Applicable ledger
and source instructions read; user no-commit/FAIR design scope overrides older
same-commit/Windows-first workflow. Same branch r6/runtime-copy-r1-fair,
HEAD2c71370eb9a959c78121ce1c88ec8e9e37187787, intentionally dirty.
47 pre-existing dirty files and measured sources captured before authoring.
317 frozen pins verified; all104 Q1,36 D1 and391 D2 manifest members independently
size/SHA checked with finalization bindings. All340 D2 NPY files had file/raw-C
SHA, headers, shapes/dtypes/C-order reauthenticated using stdlib only, without
model or NumPy imports. No R1 geometry matrix, flux or numerical state was built.

D2_ARRAY_ORACLE_MAP.csv maps every array field to geometry/moment, state/reference,
flux/cancellation or error/band oracles. D2_REQUIREMENTS_ANCHORS binds reused
measured facts to the original ATTRIBUTION.csv SHA. D2 at256x128 has99.857575989%
of global squared weighted-L2 in the first row at each pole together, and
99.999987993% in the first four rows each. Measured face ratios1.333239626EW and
0.888763947NS require correcting the joint gradient/cancellation treatment.
Seam-adjacent maxima do not establish a seam bug. The new shifted sine oracle
explicitly exercises a nonzero seam flux.

| Immutable identity | SHA256 |
| --- | --- |
| Original source contract | `544f8d2ca95a2213026b8106d05dd4114d1171033e2c832964a288f3d454f186` |
| V1 model | `6a60a90f00976e4b130d083468a0fbdca15d12686e8f86f11f82e327d8ea6c2f` |
| V1 acceptance | `ac827231ed3c5ea66c1b9731d31e0e3103b6f19cccae17204596476190e3f213` |
| Q1 manifest | `be581eacc7541e2bc5c659645394043748c67a14514887bd66fba8319c5b376b` |
| D1 manifest | `ecf269a4831fa5c30a275bd2703b71c984c169dbc1ea6fa7da852d8ed5f00a8d` |
| D2 manifest | `f8d7d167e094d4d03ab0a6a4c52b1c384f29ddbd2c79918a8f21e48f4007c815` |

New evidence root: ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_DESIGN_20261031_01.
Only this report and five ledger handoffs change in the worktree. Mathematical
specifications, comparison/test CSVs and proposed design contract live in that
exclusive external root. No runnable R1 source or test is delivered here.

## Choice and comparative assessment

| Property | A: moment FV + shared flux budgets | B: curved SIPDG + mean-flux correction |
| --- | --- | --- |
| Dynamic field | One V per original cell |15 polynomial coefficients per cell |
| Geometry | True cell means and face-integrated covariant gradient | True curved mass/face integrals and penalty |
| Polar accuracy | Conditional uniform order2 from quartic reconstruction bounds | Formal high order; polar trace/coercivity analysis required |
| Conservation | One shared limited transfer, opposite signs | Mean equation uses one shared face flux |
| Positivity/range | Explicit invariant-domain proof under low-flux CFL | Same mean budget possible; higher-mode positivity/stability remains separate |
| Time/CFL | Euler; inherited0.5 min(A/sum c), polar delta^4 bottleneck | Actual mapped trace/spectral bound, polynomial-degree factors |
| Computation | Geometry QR once, sparse cached face sums, budget passes | Element/mass/face quadrature,15N dynamic modes, penalty/limiter |
| Memory/native |8N volume bytes + approximately16S stencil bytes + geometry/state | At least120N coefficient bytes + mass/geometry/stages |
| B0 impact | New method/cache closure, same dynamic scalar shape | All higher coefficients and stages must be durable |

These are formal/shape estimates, not measured R1 CPU/RSS/storage results.
S is the sum of face patch-cell counts. Physical polar patches can span a whole
longitude ring; expected cache/work growth can be O(N log(height)), not a fixed
3x3 halo. No hardware-speed or2K/1000Y inference is drawn from HR1 or D2.
Merged polar caps/alternate mesh are a third, separate path: they change numerical
support and remapping, and cannot be disguised as the same original five meshes.

Full definitions, alternatives and cost assumptions:
[mathematical specification](../../../ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_DESIGN_20261031_01/MATHEMATICAL_SPECIFICATION.md),
[alternative assessment](../../../ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_DESIGN_20261031_01/ALTERNATIVES_AND_COST.md).

## Verifiable mathematical content and limits

A common face-centered sphere-log patch reconstructs all15 tangent monomials
through total degree4 from **area integrals**, then integrates its true surface
normal gradient once per face. QR/SVD rank and integrated moment error are
preconditions; no point-sampled substitute or per-harmonic adjustment is allowed.
First polar A scales as delta^3 while longest face scales as delta, so a quartic
face-gradient bound supplies a conservative O(delta^2) local tendency bound.
Its bounded reconstruction constant on actual patches is an explicit proof/
certification gate, not a property already measured in this design.

The low-flux Euler state is a convex combination under the stated CFL. Shared
high-minus-low correction volumes are bounded by each donor's available volume
and receiver's range capacity. The same alpha applies at both endpoints, giving
mass conservation and a real-arithmetic range/positivity proof. No final-stock
clipping or mass renormalization is involved. Floating budgets need enclosures,
strict nonnegative-state checks and the original unchanged8gamma volume budget.
The limiter may affect accuracy: record alpha/limiter defects and either show
inactivity or establish preserved frozen orders. Bounds alone do not prove order.

The conceptual flux-correction background is documented in the primary
[Zalesak paper](https://doi.org/10.1016/0021-9991(79)90051-2). The alternative
DG mean-flux approach has relevant primary work by
[Xiong, Qiu and Xu](https://epubs.siam.org/doi/10.1137/140965326). These sources
motivate structures; neither proves the proposed spherical method or its polar
accuracy. The present method equations/proofs and remaining gates are explicit.

## Test-first acceptance and independent oracles

The full [oracle/test contract](../../../ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_DESIGN_20261031_01/ORACLES_AND_TEST_FIRST.md)
and TEST_FIRST_PLAN.csv specify: independent rational unequal-area2x2 flux and
limiter calculations;15generic tangent-polynomial moment oracles; true spherical
harmonic cell means and directional flux integrals; pole-sign/phase/rotation
checks; conservation, positivity, zero diffusivity and invalid inputs; both
original modes, all five original meshes, T=0.0001 and main/half dt; first-order
time verification; full native/B0 direct/split/child3Y/10Y and corruption/stale
negatives; D2-level per-cell/polar/exclusion/seam retention and resource measures.

The original thresholds stay fixed: every successive spatial L1/L2/Linf order
>=1.5, half-dt L2 difference<=5% continuum L2 error, temporal order0.9..1.2,
original conservation/positivity contracts. Additional shifted mode
h=8+cos(phi)*sin(lambda) has exact eastward seam rate kappa*Dphi at T0, nonzero.
It supplements, never replaces, the original failing cosine arm. Additional
rotated degree-one, degree-two and smooth positive nonharmonic fixtures prevent
special-case harmonic fitting. Independent references are derived before execution.

V1's exact-in-time latitude eigenvalue is not an R1 oracle. A future R1 temporal
lane must use an independently enclosed same-R1 semidiscrete exponential when
alpha=1, otherwise stop for a separately reviewed nonlinear oracle. Frozen V1
test files cannot be run as R1 through import shadowing; a source-bound port of
all original mathematical intents and thresholds must be reviewed explicitly.
Undefined/floor-dominated orders or a5% failure remain failures, not exemptions.

## Native state, recovery and service contract

[NATIVE_B0_AND_OBSERVABILITY](../../../ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_DESIGN_20261031_01/NATIVE_B0_AND_OBSERVABILITY.md)
specifies complete current volumes and geometry/cache bytes, source/mesh/config/
initial-field identities, clocks, pending window, count/dt histogram and ledgers.
Only accepted-step checkpoint boundaries are proposed; a partly completed year
is allowed, a provisional low-order/limiter stage is not restart authority.
The immutable coefficient packet must be available and authenticated, not just
named by a hash. Restore rejects V1 schema and wrong R1 cache/limiter identities.
Reuse durable journal/native/pair/B0 expected-parent publication ordering with
verified causal high-water; unconfirmed tails remain preserved and unauthoritative.
No new crash/power-loss qualification follows from a design.

Numerical cells/CFL substeps, retained history and visualization pixels remain
separate. Geometry assembly/cache, kernel/budget/limiter, writer/fsync, checkpoint,
B0/query/restart need separate timings and memory/accounting. Annual outputs do
not justify annual numerical steps. All R1 performance and feasibility is unmeasured.

## Outcome and next authorization boundary

Design review is complete: mathematical update, positivity/conservation proof,
conditional accuracy prerequisites, two formulations, one smallest candidate,
independent adversarial oracles and strict test-first stop conditions are written.
Actual reconstruction certificates, numerical convergence/limiter behavior and
native/B0 qualification remain future gates. This design PASS does not approve
implementation or run commands. A separate explicit implementation/test scope is
required before any R1 code, geometry operator assembly or numerical evolution.

Q1 remains BLOCKED_NONAXISYMMETRIC_SPATIAL_CONVERGENCE; D1 remains
BLOCKED_REQUIRED_SPATIAL_DIAGNOSTICS_NOT_RETAINED; D2 keeps its diagnostic PASS.
All original evidence and317 pins remain unchanged. No new solver, package/data
installation, simulation,1000Y/10k/100k, commit/push or scientific/production
promotion occurred. No planetary cover/density/diffusivity is inferred from T0.
All design deliverables and before/after identity checks are sealed in the new
manifest; FINALIZATION binds that manifest separately.

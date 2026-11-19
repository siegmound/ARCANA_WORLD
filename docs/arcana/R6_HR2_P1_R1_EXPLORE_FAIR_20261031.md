# R1 EXPLORE — working conservative spherical quartic prototype

2026-10-31. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`R1_EXPLORE=WORKING_MANUFACTURED_PROTOTYPE_NOT_VALIDATED`

The new isolated prototype actually evolves manufactured spherical fields and
shows decreasing errors on16x8,32x16,64x32,128x64 and256x128. Conservation,
strict nonnegative stocks, roundoff-tolerant range controls, polar EW/NS flux
oracles, shifted nonzero seam flux, temporal order and a separate-process native
restart were measured. **This is EXPLORE, not VALIDATE or scientific qualification.**
The finest256x128 case does not satisfy the historical5% main/half-dt comparison;
that limitation remains explicit. No long physical history or global T0 use.

## New authority and preserved history

The user's explicit EXPLORE instruction supersedes the former requirement to
complete C3-A1/C3-B/formal intervals before experimentation. It authorizes isolated
implementation, short corrective iterations and gradual refinement. It does not
ratify historical D1–D7, close their old gates or authorize scientific promotion.
AGENTS/ledger continuity retained; user no-commit/FAIR scope overrides historical
same-commit handoff rules. No extra permission or certificate gate was introduced.

Branch `r6/runtime-copy-r1-fair`, HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787`,
intentionally dirty.325 old source/test/config pins and nine historical roots
Q1/D1/D2/design/I0/C1/C2/A0/A1 authenticated before implementation and again at
sealing.62 pre-existing dirty files and pinned sources captured in WORKTREE_BEFORE.
V1 and original R1/limiter/provider source bytes are untouched. The new namespace
is `experiments/hr2_p1_explore`; only this report and five ledger handoffs alter
pre-existing worktree documentation. No engine/default CI registration, commit,
push, package installation or original archive change.

Evidence: `ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_EXPLORE_20261031_01`.
PROTOTYPE_SOURCE_FINAL pins final model/native/probes/README; every attempt retains its
own source snapshot, stdout/stderr and whole-process `/usr/bin/time -v` receipt.
One failed driver attempt, three completed spatial batches and two completed
extra-check parents (each with a child restart) are retained. --help was executed once.
The second extra-check version explicitly includes H in the time-reference matrix;
model bytes are unchanged. Both versions and results are preserved. Offline saved-array
summarization/plotting is separate, not another trajectory.

## Implemented method and differences from frozen R1

The generic quartic design was viable; no harmonic-fitted alternative was needed.
A new implementation uses true-area-average quadrature targets,15 tangent
monomials, weighted SVD and one shared integrated gradient per actual face.
Gauss16 is primary; first polar packet Gauss24 gives observed sensitivity, not
an interval proof. East/north local frames and uniform-sphere rotational symmetry
allow caching one packet per latitude/axis rather than refactoring every longitude.
Fresh direct integration of three distinct faces agrees within1.85e-15 in maximum
coefficient difference. Cache coefficients are independent of the active field.
The chart derivative uses a small-s analytic series to avoid subtraction loss;
there is no4/3,8/9 or other harmonic correction factor.

True means are the target, evaluated with standard binary64 quadrature and analytic
area expressions. This is not a proof of exact normalization or formal T0/T1 error
bounds. Compared with literal frozen R1, frames/cache/normalization target and
numerical safeguards are explicitly new EXPLORE behavior. They do not retrospectively
repair or qualify the original I0 packet. Source conditioning maxima range90.23–116.06;
rank15 numerical SVD checks pass. Uniform reconstruction bounds remain unproved.

The numerical state is V=A*h. Low flux is kappa L/d times the neighboring height
difference. Euler dt respects0.5min(A/sum c). Conservative FCT budgets limit shared
high-minus-low transfers before a single final volume gather. Final stocks are
never clipped, and no mass rescaling is applied. Low-state range failures beyond
explicit numerical slack stop. Roundoff-negative budget slack is floored only
after that guard; inward64eps alpha margin and128eps height-range allowance are
experimental numerical safeguards, not formal positivity proofs. Stocks are
strictly tested>=0; the range principle is tested within the stated floating
allowance. Conservation residuals are checked against the original8gamma-style
magnitude accounting without correction.

Artificial R=6371000m,kappa=405896410000m²/year,mean8m; no density assigned.
No natural cover/diffusivity/material or global T0 field is invented. Spatial
studies use T=0.0001model-year, main/half32/64substeps up to128x64 and64/128on256x128.
These deliberately separate time error from spatial error. They are NOT a rerun
of frozen Q1's original timestep schedule. Numerical cells/CFL, retained arrays
and display pixels remain distinct resolutions.

## Actual errors and measured cost

Independent exact area averages/face rates cover z,x,shifted y,rotated(1,2,3)/sqrt14
and q=z²-1/3. Reference evolution uses continuum eigenvalues2or6, not output-fitted
rates. Main, half, analytic and flux/defect arrays are saved for every case/mode.
COMPARISON_FINAL contains all25mode/grid rows, all norms and observed orders.

| Mesh | Longitude L2 m | Longitude Linf m | Assembly s | Case wall s | Cumulative process HWM MiB | CSR cache MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 16×8 | 4.296893e-09 | 6.615123e-09 | 0.141726 | 0.219789 | 57.00 | 0.114 |
| 32×16 | 3.161313e-10 | 7.673764e-10 | 0.384868 | 0.559149 | 63.00 | 0.607 |
| 64×32 | 2.097429e-11 | 1.220588e-10 | 0.987439 | 1.519162 | 77.87 | 3.005 |
| 128×64 | 1.462823e-12 | 1.616307e-11 | 2.596377 | 4.515897 | 191.36 | 14.409 |
| 256×128 | 9.498723e-14 | 2.011724e-12 | 7.205415 | 21.392518 | 707.07 | 66.817 |

Case wall includes assembly, coefficient/array serialization, main+half for all
five modes, sensitivity and positivity controls. These columns overlap; do not
add them. CPU user/system and integration-only service are in each RESULT and
COMPARISON. HWM is cumulative in that process, not incremental cache allocation.
Whole256x128 process measured21.58s wall,21.11suser/0.46ssystem,724044KiB peak RSS
(707.07MiB); its case wall21.392518s and assembly7.205415s overlap that total.
The CSR itself is70063108B (66.817MiB). Python lists, packet retention, temporary
quadrature, array output and allocator behavior make process memory much larger.
Single-thread BLAS/OMP/MKL was explicitly selected for comparable small SVD work;
no scheduler/RAM/time quota or artificial application memory bound was imposed.

All five modes decrease in all three spatial norms; minimum successive observed
order is2.65236. Longitude L2 orders are roughly3.76,3.91,3.84,3.94. These are
measured EXPLORE trends, not a completed convergence theorem or original Q1 PASS.
On256x128 main/half L2 difference divided by main continuum L2 error is12.5482%
for x; on128x64 it is1.2586%. The finest result is sensitive to temporal/rounding
contributions near1e-13m. Their individual causes are not resolved here; no
threshold was relaxed and no formal gate is reported passed. No further grids
were launched after observing this limitation.

Shifted-sine seam maximum relative flux error decreases from0.00356942 to
9.12351e-8. EW and NS errors, including first polar/equatorward faces, are retained
in DIRECTIONAL_FLUX_ERRORS_FINAL; native-row and polar-exclusion norms are in
LATITUDE_ERRORS_FINAL. This is standard-numeric evidence that the original polar
cancellation pathology is substantially reduced, not a rigorous error certificate.

Across main/half smooth arms, limiter activation is0. Constant and zero states
remain exactly unchanged. Eight-step spike/random controls activate the limiter,
retain nonnegative stocks and floating range bounds, and have maximum observed
relative total-volume residual2.01217e-16. Smooth total-volume differences are at
most0.5m³ against approximately4.08e15m³ volume; every step respects its accounting
bound. Absolute volume residuals are not silently called exact conservation.

Independent rational2x2 low/limited results are(1.5,4.5,9,15) and(1,5,9,15),
with badCFL/NaN/negative-state rejections. Zero diffusivity preserves state exactly.
No whole original pytest suite or historical qualification was repeated.

## Temporal oracle and bounded restart

At16x8,T0.2year,2/4/8Eulersteps yield L2 errors2.26605e-6,1.13227e-6,
5.65948e-7m against scipy.linalg.expm of the independently assembled SAME spatial
matrix. Observed orders1.0009588 and1.0004791, with no limiter activation.
This standard-numeric oracle is not a certified interval exponential and does
not cover active-limiter nonlinear time behavior.

The new native checkpoint stores actual mesh/CSR/coefficient geometry,conductance,
volumes,kappa/order/CFL,completed steps/dt/time and source/runtime identity.
An8step16x8 random-field run equals4+restore+4 both in-process and in a separate
Python child, bit for bit. Native143394B,write0.000994s; child launch-through-four-
steps0.188683s. Wrong expectedSHA and a byte-corrupted copy are rejected. This is
an experimental accepted-step native test, not general admission hardening,
causal journal, REC1/B0/CAS, SIGKILL or crash-tail qualification. No historical
checkpoint code or archive is changed.

## Open work for VALIDATE

The best working prototype is the final isolated quartic implementation, with
reliable short trends through128x64 and an exploratory256x128 endpoint. Before
VALIDATE: resolve the finest temporal/roundoff floor; review true-mean/represented
bias and cache/pole stability; add independent nonharmonic smooth references,
longer bounded stability/limiter-active accuracy studies and precision/dt sweeps;
verify full clock/native admission and B0 only if required. The polar explicit
CFL still scales roughly delta^4 (finest2.26741e-6year). Cache/index assembly and
resident Python temporaries grow materially; no2K/1000Y feasibility inference.
The current loader is for known experimental files, not a hardened hostile-input
consumer. No global geology, hydrology, Deep or coupled-physics validation follows.

ITERATION_LOG_FINAL records the diagnostic shape fix and numerical guard changes,
including the failed attempt01. ARRAY_CATALOG_FINAL binds file/raw array identities;
EXPLORE_SCALING_FINAL.png shows saved measured data only. Manifest seals all attempts,
coefficients, arrays, source snapshots, reports and handoffs. Historical C3/I0
BLOCKED outcomes stay historical; EXPLORE authorization bypasses their prerequisites
for experimentation, not their scientific claims. No1000Y/10k/100k or long physics,
original archive edit, commit/push or scientific/production promotion occurred.

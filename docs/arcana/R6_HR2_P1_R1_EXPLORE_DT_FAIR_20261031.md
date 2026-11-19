# R1 EXPLORE-DT — resolved accumulation error, compact cache and reduced VALIDATE proposal

2026-10-31. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`R1_EXPLORE_DT=CORRECTED_TIME_ACCUMULATION_READY_FOR_REDUCED_VALIDATE`

**Yes: the corrected prototype is sufficiently stable and accurate in the measured
short scope to propose a reduced VALIDATE. VALIDATE has not been executed.**
At fixed archived256x128 geometry/initial volumes/parameters/T, Kahan volume
accumulation removes the observed timestep-refinement noise. The full corrected
FCT main128/half256 pairs are below the unchanged5% goal for x,y,z,q. Geometric
CSR bytes are unchanged. No moment-interval certificate chain was reintroduced.
A practical preallocated CSR constructor also removes most of the Python-object
memory overhead. Polar low-flux CFL remains restrictive and is not relaxed.

## Scope, authority and identities

The user's current EXPLORE request explicitly authorizes short timestep experiments,
implementation changes and repeated controls. It does not retroactively ratify
D1–D7 or change historical verdicts. No long physical run,1000Y/10k/100k, new input
acquisition, original provider edit, commit/push or scientific promotion.
AGENTS/ledger continuity remains; user no-commit/FAIR scope overrides the old
same-commit/Windows handoff procedure. No extra authorization gate was introduced.

Branch `r6/runtime-copy-r1-fair`, HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787`,
intentionally dirty.325 frozen source/test/config pins PLUS6previous EXPLORE source
pins are preserved (331total).69pre-existing dirty files/source bytes captured
before authoring. Ten historical manifest roots including the complete sealed
first EXPLORE are authenticated before/after. Existing V1,R1,hr2_p1_explore,
limiter and all historical reports/results remain untouched.

New namespace `experiments/hr2_p1_explore_dt`; new exclusive evidence
`ARCANA_WORLD_EVIDENCE/R6/HR2_P1_R1_EXPLORE_DT_20261031_01`.
Only this report and five ledger handoffs modify pre-existing documentation.
Old EXPLORE manifest SHA
`156818845696e8cf5ceca7b2e6e9f326d050694727cd798bd3007cffd2f82dd4`.
PROTOTYPE_SOURCE pins all8new files; immutable old CSR/template/initial NPZ data
are loaded, not refit or regenerated to improve errors. Regenerated low-flux mesh
fields match every archived field bitwise and the computed CFL equals its saved
value. Initial V0=A*archived_initial_h is identical for every timestep/method.
Artificial R,kappa,mean and T=0.0001year remain unchanged. No global T0 data used.

## Measured diagnosis: smaller steps alone do not fix the old summation

The original kernel stores a large positive volume V and repeatedly adds tiny
increments. At256x128, original errors relative to a same-geometry semidiscrete
reference worsen when stepping beyond128. A smooth plain diagnostic is bitwise
equal to the original full kernel at64/128/256steps, and original limiter counts
are zero. Thus limiter activation is not responsible in these tests.

| Steps at fixed T | Original full-FCT L2 vs semidiscrete m | Kahan diagnostic L2 m | Extended-state diagnostic L2 m |
| --- | ---: | ---: | ---: |
| 64 | 1.822342e-14 | 1.804149e-14 | 1.804147e-14 |
| 128 | 1.118274e-14 | 9.020748e-15 | 9.020780e-15 |
| 256 | 1.795834e-14 | 4.510376e-15 | 4.510312e-15 |
| 512 | 4.999889e-14 | 2.255193e-15 | 2.255091e-15 |

The Kahan and extended-state arms recover first-order Euler decay of temporal
error. Original512step error≈5.00e-14m is over22times the compensated diagnostic
error≈2.26e-15m. This controlled substitution identifies large-stock accumulation
roundoff as a concrete contributor. There is ALSO genuine first-order Euler
error: compensated64/128steps still have≈1.80e-14/9.02e-15m temporal error.
It would be incorrect to label the entire12.55% discrepancy floating noise.

The semidiscrete spatial/reference L2 error for x is≈1.07149e-13m. Time and
spatial errors partly cancel: smaller dt can INCREASE continuum error toward
that spatial limit while correctly decreasing temporal error. The original
9.50e-14m continuum endpoint was not evidence of better spatial accuracy.

## Independent standard-numeric reference and its limitations

The archived rotationally invariant face matrix is reduced by longitude Fourier
modes into latitude-block operators. Every longitude mode, including initial
rounding residuals, is propagated. The dominant m0/m1 block explicitly includes
the global anchor H=I-1e0^T; coupling of other tiny modes into m0 is neglected only
at a measured coefficient scale of≈3.77e-15/year, giving an estimated effect near
1e-32m over this T. This estimate is numerical analysis, not a formal interval bound.

An extended-precision vector Taylor exponential computes increments before adding
the8m background; SciPy dense expm is an independent time-algorithm crosscheck on
the dominant block. SixTaylor terms suffice numerically there; last term≈2.12e-29.
On this FAIR runtime longdouble has64mantissa bits and16storage bytes, not113-bit
quadruple precision. All-mode initial residual amplitude3.28e-14m evolves by only
3.75e-17m. Dense expm versus extended increment differs by at most1.99e-16m.
The all-mode reference also agrees with an independently assembled full-space
extended Taylor at16x8/32x16 to0/8.67e-19m Linf. These are ordinary numerical
crosschecks; no certified reference-error theorem is claimed or required here.
The main/half criterion itself uses the paired actual states and original saved
continuum array, so it does not depend on this semidiscrete reference approximation.

## Corrected full-FCT prototype and unchanged5% comparison

`compensated.py` stores native state as two binary64 arrays: physical volume is
**hi−correction**. Kahan accumulation retains lost low bits. Physical h is evaluated
with the available extended accumulator before the SAME binary64 flux matrix.
No geometry coefficient, forcing, initial array, PDE, Euler order or CFL is changed.
Low/high shared rates, conservative FCT, inward-alpha margin, numerical range and
volume-accounting guards remain. No final-stock clipping or mass normalization.

| Mode | Corrected128/256 main–half fraction | Fine256 continuum L2 m | Fine256 semidiscrete L2 m |
| --- | ---: | ---: | ---: |
| x | 4.473904% | 1.039322e-13 | 4.510377e-15 |
| y | 4.474045% | 1.039292e-13 | 4.510370e-15 |
| z | 3.487621% | 1.317028e-13 | 4.510291e-15 |
| q | 0.731674% | 2.879275e-12 | 2.095976e-14 |

At256/512 the fractions fall further to≈2.17%x/y,1.71%z and0.364%q.
No tolerance was adapted. Final corrected tests cover x,y,z,q on all five original
meshes16x8..256x128; high-resolution temporal errors show order≈1. The smooth
limiter remains inactive. Eight-step spike/random controls activate the real
limiter, preserve strict nonnegative represented stocks and stated numerical
range guards. Maximum observed relative total-volume residual over these controls
is5.90e-19. Constant/zero states remain exactly unchanged. BadCFL,NaN,negative
stock and checkpoint-hash controls reject. All fields/arrays are retained.

Compensation is part of the numerical state, not disposable telemetry. An8step
16x8 test equals4+restore+4 both in-process and in a separate child, bitwise in
BOTH hi and correction. The3144B new checkpoint stores those arrays and clocks,
and binds source and a required external geometry-cache SHA. The cache must remain
available; this is not a standalone all-geometry checkpoint, journal/B0, CAS,
crash-tail or hostile-input qualification. Dropping correction or using the old
single-array schema is not supported as an exact continuation.

## RAM: measured cause and implemented fix

The archived256x128 CSR has5816832entries and70063108B (66.817MiB). The previous
constructor temporarily expanded rows/columns/values into millions of Python/
NumPy scalar objects, then converted COO to CSR. Two fresh-process experiments
expand the SAME saved compact templates, excluding quadrature in BOTH arms:

| Identical template-to-CSR service | Wall s | Peak RSS during build MiB | CSR equality |
| --- | ---: | ---: | --- |
| Python-object lists |1.947942|695.51|Bitwise archived data/indices/indptr |
| Preallocated CSR arrays |0.312821|114.98|Bitwise archived data/indices/indptr |

This isolates a practical allocation problem, not a need to change the stencil.
`compact.py` implements preallocation with canonical row sorting. A complete fresh
quadrature+SVD+compact construction takes5.566981s and132.05MiB build HWM, also
bitwise equal to the archived geometry. Previous full EXPLORE process HWM707MiB
included other services; the matched template-only comparison above is the causal
memory evidence. Post-build hashing may increase whole-process HWM, reported
separately in time receipts. No synthetic application memory cap was imposed.

A separate fixed64step service benchmark alternates original/corrected branches
for3trials each. Median original full service0.919511s versus corrected0.592245s;
median G-matvec time0.240673/0.248520s. The remaining service drops from0.678838
to0.346105s, largely replacing repeated Python fsum reductions with extended-array
accounting while retaining guards. These are overlapping phase scopes, not sums
to double-count. Selecting128instead of64steps for accuracy still costs more steps;
per-step acceleration is not an end-to-end guarantee. The fresh service process
peaks134.39MiB. Dense Fourier diagnostic/reference processes have higher memory
(e.g.corrected study491.81MiB); those allocations are not the production step cache.
Single-thread BLAS/OMP/MKL was held fixed. Interactive-system load is uncontrolled;
these are observed small service measurements, not a dedicated-node benchmark.

## Polar timestep cost and practical next improvements

Unchanged low-flux positivity bound dt<=2.2674130355e-6model-year at256x128,
set by the pole-adjacent rows. Equatorial local bound is3320.72times larger.
The short T=0.0001 window needs at least45steps for this bound; accuracy128/256
uses additional refinement.441032steps for1model-year is **arithmetic only**;
no annual/long run or reliable annual wall-time forecast was performed.

Preallocation, cache reuse and compensated state are implemented and measured.
Further practical options are: reuse Fourier geometry blocks across diagnostic
fields; batch field matvecs; profile vectorized FCT/reduction work; and explore a
separate shared-flux local-subcycling or positivity-preserving implicit/time-
integration strategy. The low bound belongs to the monotone fallback, so simply
using the smooth high-order spectral scale or ignoring polar cells is not justified.
Any such timestep method must retain shared conservation, positivity and independent
short tests. No CFL relaxation, polar-cap merge or new method was tried here.

## Proposed reduced VALIDATE — not executed

Proceed with a small numerical VALIDATE, without returning to mandatory formal
moment intervals: fixed source/version/runtime; three representative meshes
32x16,128x64,256x128 plus cheap16x8 oracles; x/y/z/q and one genuinely nonharmonic
positive fixture with an independent numerical reference; main128/half256 on the
finest mesh and another temporal refinement; conservation/positivity/limiter-
active stability; and compensated-state direct/split/child/source/corruption checks.
Review the numeric reference, true-mean/cache consistency and field/dt error floors.
Native/journal/B0 integration may be a separate bounded integration test if required.
No global/physical dataset admission or scientific production claim follows from
this recommendation. Scientific and production authority remain false.

TIMESTEP_COMPARISON, SUMMARY, ITERATION_LOG, raw arrays and TIMESTEP_AND_MEMORY.png
preserve the actual evidence. All331preserved source pins and ten old archives are
rechecked at sealing; no old certificate or report is rewritten. New evidence,
sources and handoffs are sealed by manifest with separate finalization.

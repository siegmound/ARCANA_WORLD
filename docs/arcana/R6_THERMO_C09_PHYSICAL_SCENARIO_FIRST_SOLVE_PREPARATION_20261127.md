# C09 — Whole-column scenarios and first mechanical solve preparation

2026-11-27, Europe/Rome.

`C09_WHOLE_COLUMN_SCENARIOS_PREPARED__BLOCKED_REGIONAL_LOAD_AND_BASAL_SELECTION`

**Diorite2 on owner-bound PRE is the proposed native regional experiment.** The
constitutive scenario defines both layers across the column as a synthetic
effective model. The staged package is **NOT_EXECUTABLE**. North/south support,
basal closure and authorial selection are open. The diagnostic does not assign
materials, determine strain rates or compute a T1.

## C08 receipt and scope

C08 reported 728/728 in 6.88 s on
`dd6d22243dcfdcfcdb0c1c9cd4fefef2e009a76b`, without an explicit `C08_EXIT`.
Development verified the published schema, nine member byte counts and hashes,
source, C07 lineage and governance at manifest
`5ef64cd06b6be89f52fcd1f757928744ba8f1e5ade513fb3edccad710a6f60d0`.
All nine objects reproduced using `c08.build()`. No historical archive was
rewritten. The 35 material states, 14 source chemistries and 951 comparison
identities remain available for selective full G2/G3 coupling.

The existing state authority enum is unchanged. C09 records four scientific
categories: direct or derived canonical ARCANA T0 authority, external laws and
terrestrial analogues, proposed synthetic combinations, and prospective
simulation results. The 81 PRE/FEG parent nodes, thermal profiles, continental
reference density 2800 kg/m³, mantle and asthenosphere 3300 kg/m³, original
sensitivities and gravity 9.82 m/s² retain their provenance. Applying a published
constitutive hypothesis to that support is a model choice. None of the 81
effective columns has empirical validation as an ARCANA material.

## Physical scenarios compared offline

At each source PRE layer or explicit sublayer, 256 subintervals include the
interfaces. The conditional overburden is the depth integral of
`g * rho_ref * (1 - alpha*T)` with a single thermal correction. Pore pressure
is either zero in the dry sensitivity or `rho_water*g*z` with Biot 1 in the
hydrostatic sensitivity. Native equivalent dry uses Biot 0. Hydrostatic
uses the existing 1000 kg/m³ reference. These are named pore hypotheses.
Structural water, bulk concentration, fugacity and absolute pressure stay
separate. Native depth dependence is kept in its original `C*z` form.

**Native effective case.** Under pure strike-slip with invariant rate
`r = sqrt(J2)`, `eta = (A/2)*(2*r)^(e-1)*exp((B+C*z)/T)` and
`sigma_II = 2*eta*r`. For this diagnostic, the smaller of ductile strength,
physical `dCreep`, and the zero-cohesion Mohr–Anderson shear scale
`sin(atan(cFric))*P_eff` determines stress. This is the local invariant
envelope. Native integrated tensor branch interpolation, `sigHBi`, strain
orientation, `visMax` and numerical LR controls must be inspected separately
in the later operator. The numerical viscosity ceiling never supplies
a missing physical law. [ShellSet v1.1.0](https://gmd.copernicus.org/articles/17/6153/2024/),
[regional SHELLS](https://doi.org/10.1029/2001JB001544),
[Earth5 constitutive definitions and Table 1](https://doi.org/10.1029/2025JB032949).

| Native case | A, crust/mantle, Pa s^e | B, K | C, K/m | e |
| --- | --- | --- | --- | --- |
| Earth5-049 legacy sensitivity | 2.3e9 / 9.5e4 | 4000 / 18314 | 0 / .0171 | .333333 |
| Diorite2 proposal | 1.38e6 / 2.23e4 | 10524 / 16494 | .0079 / .0104 | .267 |

Both use `cFric=.85`, physical low-temperature cap `dCreep=500 MPa` for both
layers and cohesion 0 in this effective model. The modern effective crust and
mantle laws came from Earth model calibration. Their applicability to ARCANA
and geological-rate extrapolation are explicit assumptions. The range from
legacy to modern is model spread. Earth plate outlines, faults, loads and
runtime LR choices were left out. The local LR example and User Guide are
hashed in the source evidence. The [reproducibility package](https://doi.org/10.5281/zenodo.7986808)
returned HTTP 429 during retrieval. The pinned local example supplied the
legacy coefficients.

**Layered viscoplastic comparison.** Yu et al. Table 1 and Eq. 12–18 give
wet quartzite `(A,n,E,V)=(8.57e-28,4,223e3,0)`, wet anorthite
`(7.13e-18,3,345e3,0)` and dry olivine
`(6.52e-16,3.5,530e3,18e-6)` in SI. At shared stress, diffusion and
dislocation rates add. Mantle diffusion uses the published 5 mm grain size,
exponent 3, A 2.37e-15 in the published metre-based convention, E 375 kJ/mol
and V 10 cm³/mol. The initial 2-D Drucker–Prager comparison takes
`sigma_y=C*cos(phi)+P_eff*sin(phi)`, with 20 MPa cohesion and 30° friction.
The source pre-weakened endmember is documented but is not transferred.
The native PRE geometry is preserved. In one sensitivity the quartzite
analogue spans the crust. In the other, the lower half uses the anorthite
analogue, adapting the publication's 20+20 km geometry explicitly. The
wet calibrations do not establish water abundance or fugacity in ARCANA.
The existing nonlinear layered research operator supplies the separate-
exponent framework but is ductile-only in its present scope. The composite
and cohesive plastic results are offline envelopes, with deployment requiring
qualified tensor and tangent support in that route. No new solver or engine
was introduced. [Layered parameters and equations](https://doi.org/10.1029/2024JB030041),
[rift strength endmembers](https://doi.org/10.1029/2018TC005346),
[fault-network modelling](https://doi.org/10.1029/2022TC007659).

### Measured strength on the 100 km rate proxy

Results are min–max across 81 columns, in (10^{12}) N/m. The rate is
4.991e-14 s⁻¹. An integral of invariant stress is a scalar strength diagnostic.
It will not serve as a prescribed SHELLS membrane stress or inferred rate.

| Model | Hydrostatic crust | Hydrostatic mantle | Hydrostatic total | Dry total |
| --- | ---: | ---: | ---: | ---: |
| Native legacy | 0.671–1.228 | 0.607–7.663 | 1.278–8.876 | 1.462–9.643 |
| Native Diorite2 | 2.059–4.443 | 0.172–2.692 | 2.231–7.135 | 3.070–8.939 |
| Layered homogeneous crust | 1.036–1.922 | 0.870–8.219 | 1.906–10.141 | 2.193–12.787 |
| Layered quartzite/anorthite | 2.278–4.990 | 0.870–8.219 | 3.148–13.208 | 3.863–17.132 |

Diorite2 crustal crossings occur at 16.71–24.55 km, and the envelope records
each mantle crossing and mechanism by column. The shallow branch is brittle.
The cool and warm reference surface endpoint sensitivities, imposed as a
linear taper to the unchanged thermal LAB, change the Diorite2 hydrostatic
integral by +9.71–19.64% and −11.88 to −6.07% relative to the original PRE.
This is a constitutive sensitivity with a paired pressure correction. It does
not regenerate the transient thermal profiles. The source expansivity
endpoint sensitivity changes the integral magnitude by 0.36–0.51%.
The largest observed total integral difference between 128 and 256
subintervals is 4.96e-4 fraction across the four model forms, three rate
proxies from C08 and both pore sensitivities. Depth curves retain stress,
viscosity, regime and transition depths for all parents at 100 km.

The C08 (15/56) exponent and 3.083% partial mantle error remain a separate
result. C09 rescales A at the geometric rate pivot using the native (2r)
convention and compares the changed exponent on each full envelope. Across
C09 cases and rate/pressure combinations, local error is at most **0.146%**
for substitution in Diorite2, **11.78%** for legacy, **3.20%** for the
homogeneous layered analogue and **11.78%** for the two-crust analogue.
Diorite2 total integral error stays within **0.072%**. The two-crust total
error reaches **3.27%**. The latter comparison retains the same diffusion
and plastic branches, so it isolates the dislocation exponent substitution.
It does not reproduce that hypothesis in native SHELLS. Choose .267 for the
proposed native law, preserve separate exponents for the research comparison.
No acceptance tolerance is inferred from these errors. A later reduction
requires an independently stated deformation/mass budget and checks of work,
reactions, local stress and numerical caps. C08 laboratory eligibility masks
remain available. The fully extrapolative model design has no empirical
holdout on ARCANA.

## Regional, basal and global decision

**Route R, first.** Keep the 8×8 PRE/FEG continuum. It contains 128 triangles,
162 tangent DOFs and 32 exterior edges, with no explicit sided faults. The
existing rotated south/east mapping yields 36 distal components of rank 36,
leaving 126 tangent DOFs and no spherical rigid rotations. Fifteen parent
nodes are multiply owned by plates. The 13 mixed PRE owner records are
preserved separately. Fourteen N/S perimeter nodes lack a selected condition.
The existing outer continuation and stitch can transfer interface motion
and reaction forces. They need constitutive support to the outer edge,
a single compatible velocity trace or mechanically closed force exchange,
and consistent basal and GPE work. Move to the 16×16 parent domain only for an
extent sensitivity. Its 289 nodes and 512 triangles introduce plate 11 and
move the unknown outer cut.

Native `ReadBC` can represent a complete velocity trace. `Fixed` code 0
has its own weak-margin normal load and code -1 uses a ridge reference.
Neither fills missing N/S data. A generic exterior traction or impedance
needs a qualified force adapter or the existing coupled weak form. Avoid
double constrained nodes, plate averaging, invented periodicity and guessed
zero outer loads. The proposed free-slip limit explicitly sets tangential
basal exchange to zero via `trHMax=0` only if accepted. The normal closure
candidate is quasi-static hydrostatic/isostatic support against a common
reference surface, independently of tangential exchange. The actual
reference and consistency with PRE elevation and density remain open.
`zBAsth` is a separate mechanical parameter. `pltRef` and `iConve`
must be reconciled with the regional frame and wrapper. The User Guide
describes torque iteration in full ShellSet for `iConve=0` or 6.
Finite drag requires mantle motion in the chosen frame, a mechanical
interface and a coefficient. Native `Assign`/`ArcanaRuntimeSqueez` owns
native GPE; reactions are later residual and work diagnostics.

**Route G, deferred.** Direct source topology contains 64,442 PRE nodes,
128,880 triangles and 193,320 manifold edges, with no artificial cuts or
explicit native faults. The canonical 12-plate mesh records 1,983 boundary
edges. Its 64,442 numerical thermal profiles coexist with 63,620 D12-admitted
and 1,180 unadmitted cells on the 180×360 support. These populations differ.
Six crust domains need constitutive coverage and the 2,697 mixed PRE records
retain owner-based density. A proposed global gauge removes three rotations
by area-weighted orthogonality, subject to torque compatibility and actual
operator validation. Global motion still needs physical driving, basal
support and a model of plate interfaces. The 128,884-DOF historical reordered
band at `kl=ku=727` accounts for 2.250 GB of matrix payload and at least
2.933 GB of named arrays before overhead or snapshot copies. Factoring cost
scales with order (n k_l^2), about (6.81×10^{10}) proxy work units for that
band. At hypothetical rates of 1–10 Gwork/s this proxy alone corresponds to
6.8–68 s and supplies no end-to-end runtime forecast. F2A-V stopped before
Solver in 282.09 s, return code 75. F2AV remains blocked and F2B remains
unauthorized. Active memory, solve time and rank remain unmeasured.

## Package and remaining decisions

Development staged three actual fragments using the existing FEG serializer
and regional PRE specialization: `regional.feg`, `regional_PRE.dat` and
`MOD_ArcanaRuntime.regional.f90`. Parent geometry and all 50 PRE value
tokens per row were retained. Mapping, units, BC candidates, source IDs,
proposed native LR values and pending LR controls are in
`CANDIDATE_NATIVE_INPUT_PACKAGE.json`. The package has no runnable BC/LR
deck. A standalone gfortran reader/evaluator fixture reproduced all 81
records and 324 evaluations exactly against the full PRE reader. Count,
missing row and wrong magic controls rejected. The first fixture compilation
stopped at the Fortran 132-column limit on the 81-ID literal. The successful
fixture added continuation lines and changed no code under test. Its external
receipt is `R6_THERMO_C09_READER_DEV.mqTi36/RESULT.json`. The full native
executable and its active S1B route still require qualification.

The 107.406 km shortest edge, 0.157535 m/year largest opening and source
kinematic velocities give provisional bounds of 6.35 and 45.4 years at the
declared (10^{-4}) displacement/width or edge fraction. Propose a **1-year
trial and a 0.5-year same-start sensitivity** after an actual equilibrium
velocity solution, with limits recomputed from solved gradients and
geometry, thickness and transport constraints. The 27,123.405156-year
first event is a strict cap. Neither a mechanical clock advancement nor an
accepted deformation step occurred. A single model with two MPI ranks,
120 s and 1 GiB aggregate is a provisional regional operator budget,
conditioned on actual executable, resource controls and matrix measurement.

Authorial decisions are the Diorite2 effective scenario and pore
hypothesis, continuum accommodation and N/S continuation, and independent
normal closure with the tangential free-slip limit. Review the exact
proposed LR values, uncertainty spreads and rejected cases in the decision
sheet. After selection, stage executable identity and assembly/rank checks
before seeking solve authority. Then measure residuals, reactions, torque,
work, dissipation and solver sensitivity. Use the original G4 mapping for
velocity, EDot and stress IDs, update geometry and conserve material masses
with external flux terms explicit, and verify separate-process restart before
publishing a candidate T1.

D-024/D-025 are active. No physical solver, thermodynamic engine, Canon or
HistoryStore change. The intended path remains causal queryable WORLD_HISTORY
from 210 Ma to 0 ka with adaptive resolution, including tectonics, climate,
water, materials, Deep, resources, life and civilization.

## Independent FAIR qualification

Development results: 736/736 PASS including eight focused C09 tests.
The operator qualification directory is reserved for the SHA-pinned command.

```bash
set -e
trap 'rc=$?; printf "C09_EXIT=%s\n" "$rc"' EXIT
cd /home/jlpfritas/HPC-POMDP/Arcana
C09_BRANCH=r6/thermo-s3-pt-design-20261123
C09_VERIFY=ARCANA_WORLD_R6_THERMO_S3_DESIGN_VERIFY
# Export C09_SHA to the exact published SHA in the delivery.
git -C "$C09_VERIFY" fetch origin "$C09_BRANCH"
test "$(git -C "$C09_VERIFY" rev-parse FETCH_HEAD)" = "$C09_SHA"
C09_CHECKOUT=$(mktemp -d "$PWD/ARCANA_WORLD_R6_THERMO_C09_VERIFY.XXXXXX")
git -C "$C09_VERIFY" worktree add --detach "$C09_CHECKOUT" "$C09_SHA"
cd "$C09_CHECKOUT"
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
test "$(git rev-parse HEAD)" = "$C09_SHA"
test -z "$(git status --porcelain)"
python -c 'from experiments.r6_thermo_provider_pilot_v1 import run_c09_physical_scenario'
python -m pytest -q -ra --tb=short -p no:cacheprovider tests/test_r6_thermo*.py \
  tests/test_r6_g2_g3_physical_source_packet.py tests/test_r6_g2_g3_source_to_coupled_handoff.py
python -m experiments.r6_thermo_provider_pilot_v1.run_c09_physical_scenario \
  --expected-sha "$C09_SHA" --offline-physical-scenario-only
```

Output `ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_C09_PHYSICAL_SCENARIO_FIRST_SOLVE_PREPARATION_NEW01`
contains 10 JSON reports, three native input fragments and the manifest.
Capture `C09_EXIT` and `C09_MANIFEST_SHA256`. The command performs offline
construction and retains `NOT_EXECUTABLE` scope.

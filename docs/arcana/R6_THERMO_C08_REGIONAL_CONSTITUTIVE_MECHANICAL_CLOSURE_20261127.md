# C08 — Regional constitutive and mechanical candidates

2026-11-27, Europe/Rome.

`C08_REGIONAL_CONSTITUTIVE_AND_MECHANICAL_CANDIDATES_EVALUATED__AUTHORIAL_SELECTION_REQUIRED`

**The full-column constitutive law and the regional loading remain open.** The
8×8 plate 5:8 continuum now has depth-resolved strength sensitivities, a quantified
common-exponent reduction and an explicit distal velocity matrix. These are
offline results from FAIR development. Physical T1, material assignment and
mechanical solve authorization remain unset. D-024 and D-025 remain active.

## C07 closure and source inputs

The C07 operator reported 719/719 in 2.96 s at
`1bad34e117e41da27fe0d1890358ceb324220850`. No explicit `C07_EXIT` was supplied.
Development independently verified the nine payload hashes, byte sizes,
manifest schema, source SHA, candidate and C06 lineage, then reconstructed all
nine JSON objects with `c07.build()`. Manifest SHA-256
`7503dd802bea400749d8543fc3f39cc74a945f9eb23b9bca9838f62a78212149`.
The replay retains the 35 material states and 951 comparative query identities.

The original 81 parent PRE records in the 8×8 FEG were joined to the
source packet field by field. There are 68 uniform and 13 multiprovince
continental-role nodes, 15 plate-boundary nodes and 81 positive mantle-layer
geometries. The owner-bound S1B proposal retains the transient PRE, (g=9.82)
m/s² and a single native thermal correction to the reference density.
The 16×16 footprint remains a domain sensitivity. No EOS density, mechanical
LAB, new mineralogy or absolute pressure is introduced. For the analogue stress
calculations, the distinct P proxy is piecewise reference-density overburden.
At the Moho it spans 0.770–1.375 GPa.

## Quantitative constitutive comparison

The 81 columns use both original PRE polynomials, their material interfaces,
257 depth points per full layer and explicit clipping at scenario temperature
and pressure crossings. An independent static projection reproduces the
source-defined seven barycentric locations per triangle. Of 896 evaluated
locations, 133 have different source-node PRE phase labels at the projected Moho.
The calculation weights temperatures at a common depth and assigns no new
material to these locations. Source code controlling the projection is
`MOD_SharedVars.f90`, `MOD_ArcanaRuntime.f90` and `MOD_Shells.f90`.

- **Crustal creep.** The BHQ laboratory window 1173.15–1373.15 K at roughly
  1.5 GPa has zero eligible depth intervals. Nominal laboratory
  (n=4), (Q=223) kJ/mol and (A=1.1×10^{-4}) MPa⁻⁴ s⁻¹ are retained with
  published uncertainty and an explicit triaxial invariant conversion.
  The alternative wet-quartz temperature screen intersects 69 columns.
  Water fugacity, fabric and a jointly applicable P/T/rate domain remain open.
  At fixed other inputs, the wet-quartz (m=1,n=4) law would reduce stress by
  a factor 0.562 for tenfold greater fugacity. That factor supplies no absolute
  stress without a water model. The available low-T α-quartz Dryad experiment
  series used 1.39–3.1 GPa and laboratory rates 10⁻⁶–10⁻⁵ s⁻¹. Its pressure floor
  exceeds all the regional Moho proxies. The report binds the literature and
  dataset metadata without redistributing third-party files. [BHQ experiments](https://doi.org/10.1016/0040-1951(95)00011-B), [wet-quartz regimes](https://doi.org/10.1016/j.epsl.2018.10.017), [fugacity law](https://doi.org/10.1007/s005310000152), [low-T quartz publication](https://doi.org/10.1029/2025JB032753), [Dryad data](https://doi.org/10.5061/dryad.rbnzs7hqv).
- **Sliding analogue.** Under the conditional normal stress equal to reference
  overburden and Biot 1, the crust-only integral spans (7.685×10^{12})–
  (2.294×10^{13}) N/m for a dry plane and (5.275×10^{12})–
  (1.547×10^{13}) N/m for a hydrostatic-water plane. The branches meet
  at 170 MPa shear under 200 MPa effective normal stress. This gives a
  sensitivity to the pore model. The coefficient or slip plane for ARCANA,
  cold-crust strength, and the transition remain unassigned. The archive keeps
  Byerlee sliding physics, continuum `cFric`, fault `fFric`, `Biot` and
  offset-dependent `Byerly` distinct. [Byerlee 1978](https://pubs.usgs.gov/publication/70012542).
- **Mantle creep.** The conditional dry-olivine calculation uses (A=1.1×10^{-16})
  Pa⁻³⋅⁵ s⁻¹, (n=3.5), (E=530) kJ/mol and (V=14) cm³/mol, with 10 and
  20 cm³/mol sensitivities. The declared warm analogue band is 1373–1673.15 K
  and 1.8–8.8 GPa in the proxy. It includes 20.2–42.1 km per column. The
  Dixon–Durham pressure series supports only its laboratory slice at 1373 K
  and 10⁻⁵ s⁻¹. The regional rates are extrapolated 7.30–8.78 decades below that
  rate. There is no joint empirical applicability claim across the band. Diffusion
  and low-temperature plasticity require separate mechanism and material support.
  [Olivine dislocation review](https://doi.org/10.1029/138gm06), [activation volume](https://doi.org/10.1029/2018JB015853), [high-temperature forsterite](https://doi.org/10.1007/s00269-016-0805-x), [low-temperature olivine](https://doi.org/10.1029/2018JB016736).

| Width prior | Rate s⁻¹ | Partial mantle integral, (V=14), N/m | Worst relative error with shared (e=15/56) |
| --- | ---: | ---: | ---: |
| 10 km | 4.991e-13 | 4.654e10–2.646e11 | 2.991% |
| 100 km | 4.991e-14 | 2.410e10–1.371e11 | 1.081% |
| 300 km | 1.664e-14 | 1.761e10–1.001e11 | 3.083% |

These width-based rates are inherited kinematic sensitivities from the two
central contact segments. At 100 km the 10 and 20 cm³/mol alternatives span
2.012e10–1.024e11 and 3.162e10–2.124e11 N/m respectively. Depth integration
changes by up to 2.78e-5 fraction on halving 256 subintervals. At 100 km the
uncapped simple-shear stress scale spans about 0.63–8.63 MPa and the partial-band
mean viscosity spans 1.19e19–3.29e19 Pa s. A local `dCreep` below the local
threshold would clip that simple-shear stress. `visMax` limits the mean of the
full native creeping interval and regularizes the brittle response, so the
partial-band mean is only a scale for comparison. Actual activation requires
the native strain tensor, creeping interval, selected caps and `sigHBi`.
The depth curves retain local thresholds and the error distributions.

The native comparison uses `shells_lr_bridge` coefficients and the actual
`Diamnd` rate argument $2\sqrt{J_2}$. At $\dot\epsilon_{II}=\sqrt{J_2}$,
the raw creep `aCreep` requires a factor (2^{1-e}) to match
$\sigma_{II}=2\eta\dot\epsilon_{II}$. A regression checks this conversion.
At fixed P and T the power law factors, so the same relative error applies
to the integrated uncapped mantle band and the individual depths. A pivot at
the geometric mean of the rate endpoints and the midpoint in **inverse
exponents** minimizes maximum absolute log slope error for nominal (n=4,3.5).
Two held-out rates test interpolation of the representation, with errors about
1.51–1.53%. Matching the mantle exponent yields errors below 7e-15 fraction
there, but a crust-slope setting alone gives up to 6.26%. This computational
comparison supplies no empirical joint fit or acceptance tolerance. The 555
archived curve points are stress–strain records. The published 19-run wet-quartz
supplement has shared laboratory provenance and has not established a new
independent fit/test split. Whole crust ductile, whole mantle and combined
strength are null. No numerical cap fills an unsupported depth interval.
[Original transient curve archive](https://zenodo.org/records/8304793).

## Regional conditions and force ownership

The 128 FEG triangles carry the original parent topology. All 32 exterior
edges have a unique inner parent triangle and plate owner. West and east have
nine single-owner nodes each. Velocity candidates use plate 8 west and plate 5
east, the source Euler vectors and the proper `RX_PLUS_0P5_DEG` transform.
The report retains the 18 node IDs, spherical coordinates, south/east values in
m/s, and native ReadBC azimuth/magnitude. Kinematic validity is limited to the
open first segment before the 27,123.405156-year event horizon. No dt is selected
for deformation.

Of the 12 source 5:8 segments, eight have opening 0.1571–0.1575 m/year and four
are dominated by along-contact speeds of magnitude 0.1572–0.1575 m/year.
This geometric variation weakens the premise of along-strike uniformity. At
north parent 37463 and south parent 34587 the two full Euler targets differ by
about (4.99×10^{-9}) m/s on each shared node. No averaging or node duplication
is needed for **distal** continuous constraints; imposing both values at the
junctions is inconsistent.

| Algebraic velocity design | Rows | Rank | Remaining tangent DOFs | Remaining spherical rotations |
| --- | ---: | ---: | ---: | ---: |
| Full distal, native code 2 candidate | 36 | 36 | 126 | 0 |
| Distal conormal only, code 1 candidate | 18 | 18 | 144 | 0 |
| Dual Euler at both N/S nodes, rejected | 44 | 40 | 122 | 0 |

The inconsistent least-squares RHS residual is (2.492×10^{-9}) m/s. These ranks
apply to the kinematic matrices, with 162 variables, and test the three rigid
rotation modes. Stock `Fixed` assigns weak-margin normal traction for code 0
and the ridge reference for code -1. Neither is an unknown-load encoding.
Full distal data are the preferred proposal. The conormal-only option leaves
tangential support unresolved. North/south require the physically closed
exterior continuation A or separately justified traction. An explicit fault
route needs sided geometry, a contact law, effective pressure and G4 transfer.

Native `Assign`/S1B `ArcanaRuntimeSqueez` own the native potential-energy load.
The coupled weak-form route requires its own GPE accounting; it must exclude
duplicate native forcing. `pltRef` chooses the plate reference for native
velocities and is distinct from the kinematic gauge. `zBAsth` specifies basal
shear depth, `iConve` controls mantle motion, and `trHMax` limits basal coupling.
Each stays unresolved. Zero tangential exchange is a possible explicitly
selected limiting model with independent normal support. Linear drag requires a
mechanical interface, mantle velocity in the same frame and coefficient.
Reactions, work and torque are future solve diagnostics.

The static scalar `rhoBar` inventory retains every Fortran reference and review
by routine. Active S1B `Diamnd`, `Assign`, `Fixed`, `Mohr` and `Result`
select weighted column fields where their active branch applies. `Viscos`
still carries scalar fallback arguments and a native pore-pressure policy.
LR parsing and scalar sweep checks are separate. OrbData synthesis and
OrbScore fault diagnostics retain stock paths and remain outside this minimum
proposal. Active routing on a new native executable is still to be verified.
Full operator rank, residuals and solver resources were not evaluated.

## Decisions and FAIR qualification

Review the unselected owner-bound baseline and the shared-continuum
hypothesis with full distal velocity. Scientific decisions are the cold crust
and transition law, material and water/pressure applicability, N/S support,
basal closure and frame, and strain accommodation width. Retain the separate
exponents if a full-column native reduction cannot meet a mechanically derived
work, reaction and strain budget. The existing nonlinear layered research
implementation preserves two exponents but needs its own complete force and
material closure. The selective coupled thermodynamic route remains available
with the eight previous requirements. D-024/D-025, no assignment, no physical
T1, solver-authority false and WORLD_HISTORY authority false apply to both.
No solver or thermodynamic engine was invoked and HistoryStore is untouched.

Development ran the full 719-test selection plus nine focused C08 tests and
assembled all nine payloads offline. The independent SHA-pinned qualification
is a separate operator action. From the Arcana root, set `C08_SHA` to the
published commit and execute:

```bash
set -e
trap 'rc=$?; printf "C08_EXIT=%s\n" "$rc"' EXIT
cd /home/jlpfritas/HPC-POMDP/Arcana
C08_BRANCH=r6/thermo-s3-pt-design-20261123
C08_VERIFY=ARCANA_WORLD_R6_THERMO_S3_DESIGN_VERIFY
git -C "$C08_VERIFY" fetch origin "$C08_BRANCH"
test "$(git -C "$C08_VERIFY" rev-parse FETCH_HEAD)" = "$C08_SHA"
C08_CHECKOUT=$(mktemp -d "$PWD/ARCANA_WORLD_R6_THERMO_C08_VERIFY.XXXXXX")
git -C "$C08_VERIFY" worktree add --detach "$C08_CHECKOUT" "$C08_SHA"
cd "$C08_CHECKOUT"
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
test "$(git rev-parse HEAD)" = "$C08_SHA"
test -z "$(git status --porcelain)"
python -c 'from experiments.r6_thermo_provider_pilot_v1 import run_c08_regional_closure'
python -m pytest -q -ra --tb=short -p no:cacheprovider tests/test_r6_thermo*.py \
  tests/test_r6_g2_g3_physical_source_packet.py tests/test_r6_g2_g3_source_to_coupled_handoff.py
python -m experiments.r6_thermo_provider_pilot_v1.run_c08_regional_closure \
  --expected-sha "$C08_SHA" --offline-regional-closure-only
```

Expected output `ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_C08_REGIONAL_CONSTITUTIVE_MECHANICAL_CLOSURE_NEW01`
with nine JSON members (including depth curves, constraints, and decisions),
a manifest and the C08 status. Output is write-once. Capture `C08_EXIT` and
`C08_MANIFEST_SHA256`. No operator qualification was executed in development.

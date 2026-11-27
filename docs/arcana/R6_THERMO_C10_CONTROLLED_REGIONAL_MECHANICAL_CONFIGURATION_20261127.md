# R6 C10 — Controlled regional mechanical configuration

27 November 2026, FAIR/Linux, `arcana-r6-linux`. Entry
`230193c12463c0301b02c9e5f45ac91e853a7de3`.

`C10_CONTROLLED_REGIONAL_MECHANICAL_CONFIGURATION_COMPLETE__AUTHORIAL_RATIFICATION_REQUIRED`

The candidate `C10_R8_DIORITE2_KINEMATICALLY_CONTROLLED_FREE_SLIP_V1` has
a complete input deck and a verified native path through readers and
precomputation. The executable built for this stage stops before `Pure`.
Authorial selection and separate authority for operator assembly and a
mechanical solve are pending. D-024 and D-025 remain active,
`physical_T1=null`, physical material assignments are zero, and WORLD_HISTORY
production remains unauthorized.

## C09 consolidation

The operator reported 736/736 in 16.12 s on the entry SHA. The transcript
supplied no explicit C09 exit marker. Independent `run_c09_physical_scenario.build()`
recreated all 10 JSON reports and all three native fragments, with byte equality
for the fragments. Verified archive manifest
`19c2b072d7b74dd8f707170e36de25b8d5fdf0a0777b896ae59909df2b2969c2`.
The development regression selection passed 743/743 in 27.42 s, including seven
C10 regressions. The separate C09 development manifest
`c09d80060c51a5ad516cb05b85366a31887b9cb95d86a8689311fa5aeabe10c0` and its members
were verified as development evidence. C09's blocked status and earlier
lineage are retained. Its 35 research states, 14 chemistries, 951 comparisons,
alternative laws, exterior A, reduced global route and eight original closure
groups remain available. New equilibrium queries are zero.

## Boundary conditions

The original R8 FEG has 81 nodes, 128 triangles and 32 boundary nodes and
edges. Both traces preserve all 36 distal Euler components. North and south
cut lengths are 859.248 and 882.929 km. The construction parallel-transports
endpoint velocities along each source edge chain and blends in a shared
tangent frame with either normalized arc length or `3s²−2s³`. Each cut meets
the original endpoint values exactly. The full perimeter is single-valued
at the shared nodes and continuous at the corners. The two proposed shapes
are prescribed loads for a shared continuum with no sided faults, and
their mechanical reactions remain outputs. File records use rotated S1B
south/east SI components, native code 2 and azimuth clockwise from north.
Both candidates passed the actual native `ReadBC` round trip within
1.31e-24 m/s.

| Boundary hypothesis | Max edge velocity difference | Max edge gradient |
| --- | ---: | ---: |
| Linear arc length | 6.275e-10 m/s | 5.842e-15 s⁻¹ |
| Smooth distributed, recommended | 9.216e-10 m/s | 8.581e-15 s⁻¹ |

The maximum pairwise relative speed is 5.420e-9 m/s for both traces, and their
maximum same-node discrepancy is 4.706e-10 m/s. These are imposed accommodation
scales. C08's 10 km and 100 km bands are narrower than one source cut edge.
The actual constraint matrix has rank 64, a consistent RHS, 98 free tangent
DOFs and no remaining rigid rotations. Its rank only covers the constraints.
Native boundary interpolation and the `fPoint/fGauss` convention are specified
for later checks of distributed loads, nodal reactions, torque and work.
Exterior A is the separate mechanically closed continuation route.

## Vertical reference, pore pressure and free slip

The proposed effective Diorite2 law uses C09's paired crust/mantle parameters.
`aCreep` is 1.38e6/2.23e4 in Pa·s^e, `bCreep` 10524/16494 K, `cCreep`
0.0079/0.0104 K/m and `dCreep` 500 MPa in both materials. The common `eCreep`
is .267, continuum friction is .85 and effective continuum cohesion is zero.
Hydrostatic Biot 1 and dry Biot 0 are proposed hypotheses for this experiment.
The native pore head starts at the local surface with weighted PRE water
density near 1000 kg/m³. Surface elevation enters the sea-level vertical
reference and gives no additional land pore head. The maximum difference
against C09's pore term is 1.51e-7 Pa. The reconstructed native overburden
differs by up to 0.192 MPa from the comparator that projects owner-integrated
C09 values. The native pressure path weights PRE properties on the common
interval before applying the effective density correction. The fixture
evaluates the actual S1B density calls used in the pressure path and stops
before rheological iteration.

At 81 nodes and 896 integration points the independent replay reproduced
`sigma_zz = P_reference − P_column` with maximum absolute differences of
2.78e-6 Pa in basal stress and 0.124 N/m in integrated stress. S1B's native
reference is a 300 km sea-level profile with water, transition, crustal and
asthenospheric contributions. All fixture locations are land. The resulting
positive `sigZZB` ranges are 93.136–268.294 MPa at nodes and
93.270–243.919 MPa at integration points. The corresponding `tauZZ` ranges
are 1.737e12–1.863e13 and 1.747e12–1.571e13 N/m. `Fixed` owns integrated,
basal-slope and boundary GPE contributions in the thin-shell vertical
reduction. Chemical density stays at its compatibility zero and the nonzero
derived vertical diagnostics are retained. The candidate uses this reduced
vertical equilibrium as its vertical support assumption.

`trHMax=0` makes `pulled` false and `etaMax=0`. `THOnB` returned exactly
zero tangential traction and viscosity under a nonzero probe velocity.
The standalone reference token `RF` is a bookkeeping slot with zero mantle
and reference motion. Original PRE owner slots are mapped for reporting,
without substituting Earth plate geography or introducing a torque loop.
`FillIn` calls `OneBar` before checking `pulled`, so `zBAsth=1000 m`
keeps one compatibility cell and its `glue` finite. A 2000 m check changed
`glue` from 1.937e9 to 1.610e9 and preserved the fixed/GPE, thickness and
zero tangential response. The native probe rejected zero depth, the 400 m
empty interval, active mode 6 and reversed BC order. Hydrostatic and dry
precomputation gave identical geometric/GPE readback. These observations
apply to the proposed free-slip limit. Natural basal drag, LAB and mantle
reference motion are unresolved.

## Deck, limits and remaining decisions

The development evidence contains the actual FEG, PRE, S1B loader, `controlled.bcs`,
linear sensitivity BC, hydrostatic/dry LR files, 2 km compatibility LR file,
runtime control and reporting plate mapping. `COMPLETE_CANDIDATE_INPUT_PACKAGE.json`
pins all ten files and preserves the G4 crosswalk and later output schema.
`AUTHORIAL_RATIFICATION_SHEET.json` leaves all approvals unset. Its recommended
choices cover effective Diorite2, the pore hypotheses, smooth N/S trace, original
shared continuum, native vertical reference, tangential free slip, numerical
controls and the scope of any subsequent solve.

The proposed controls from the scoped engineering fixture are
`maxItr=50`, `okToQt=5e-4`, `refStr=50 MPa`, `okDelV=1e-11 m/s` and
`everyP=F`. Native `visMax` was 1.10125e24 Pa·s. Before interpretation,
record cap activation and repeat with tighter convergence controls and
half/double `okDelV`. Compare both boundary traces and both pore choices as
distinct sensitivities. Require residuals at free DOFs, reaction reconstruction,
force/torque and work balances including GPE, basal work and dissipation.
Fix application and condition-scaled numerical tolerances before observing
physical solve output.

The pre-solve entry linked under NVFORTRAN 25.11 with bounds and IEEE checks.
Actual dimensions were 162 unknowns, 21 lower and upper bands and 64 band
rows, with 82,944 bytes for the binary64 band payload. Build and hydrostatic
probe in development trial 03 took 2.54 s/70,108 KiB and 0.20 s/10,240 KiB
wall/peak RSS. One model, at most two MPI ranks, 120 s and 1 GiB aggregate
remain proposals for the later physical stage. Source-level omission of the
assembly/solve path provides the deterministic stop. Assembly, conditioning,
factorization and future operator resource measurements remain pending.

G4 keeps the provisional one-year update and same-start half-year comparison.
Their acceptance depends on solved gradients and the source event horizon.
A physical T1 requires positive spherical Jacobians and layer thicknesses,
explicit crust/mantle fluxes at the moving regional boundary, mass closure,
a chosen thermal transport policy, parent lineage and separate-process
restart. HistoryStore was untouched.

## FAIR operator runbook

Run from `/home/jlpfritas/HPC-POMDP/Arcana` after setting `C10_SHA` to the
exact published SHA in the handoff. These commands perform independent
offline qualification and create a fresh archive. Keep its terminal output,
`C10_EXIT` and `C10_MANIFEST_SHA256`.

```bash
set -euo pipefail
: "${C10_SHA:?set the exact published C10 commit}"
C10_BRANCH=r6/thermo-s3-pt-design-20261123
C10_VERIFY=ARCANA_WORLD_R6_THERMO_S3_DESIGN_VERIFY
git -C "$C10_VERIFY" fetch origin "$C10_BRANCH"
test "$(git -C "$C10_VERIFY" rev-parse FETCH_HEAD)" = "$C10_SHA"
C10_CHECKOUT=$(mktemp -d "$PWD/ARCANA_WORLD_R6_THERMO_C10_VERIFY.XXXXXX")
git -C "$C10_VERIFY" worktree add --detach "$C10_CHECKOUT" "$C10_SHA"
cd "$C10_CHECKOUT"
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
test "$(git rev-parse HEAD)" = "$C10_SHA"
test -z "$(git status --porcelain)"
python -m pytest -q -ra --tb=short -p no:cacheprovider tests/test_r6_thermo*.py \
  tests/test_r6_g2_g3_physical_source_packet.py tests/test_r6_g2_g3_source_to_coupled_handoff.py
if python -m experiments.r6_thermo_provider_pilot_v1.run_c10_controlled_region \
  --expected-sha "$C10_SHA" --offline-controlled-region-only; then c10_rc=0; else c10_rc=$?; fi
printf 'C10_EXIT %s\n' "$c10_rc"
test "$c10_rc" -eq 0
```

Operator output
`ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_C10_CONTROLLED_REGIONAL_MECHANICAL_CONFIGURATION_NEW01`
is separate from the development archive. It contains eleven JSON reports,
the native deck and compiled fixture receipt, and an inventory manifest.

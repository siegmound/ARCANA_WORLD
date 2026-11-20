# ARCANA R6 — source-exact contacts and objective finite-rotation gate

**Date:** 2026-11-20. **Branch:** `r6/multiphysics-integration-20261026`.
Previous full 12-plate source P1 manufactured 100/1000-year
time integration was **29/29 FAIR PASS** (source
`a57fdbac0216c0d7b240681a0222a5fe6aa0fa45`);
registered on GitHub at
`12bcbf2e201c28f095ace743f08790e35311247c`.

**Authorization:** source-preserving, **ENGINEERING_ONLY**, diagnostic
regional contact policies and objective SO(3) *kernel* tests.
**This is not a physically calibrated contact, friction or normal-force
solve, and does not produce physical T1.**

## Motivation and scope

The global full 100/1000-year manufactured sparse P1 integrator
uses 12 separate plate-local material views, with **no interaction
at shared T0 parent nodes**. It correctly demonstrates a
sparse P1 time pipeline but cannot predict geological
stress accumulation at real boundaries. Introduce *bounded*
interactions at authentic fault candidate edges and verify the
frame-objectivity requirement **before** attempting a global
dynamic contact mechanics evolution.

New files:

- `experiments/plate58_deforming_explore_v1/g2_source_contact_objectivity.py`
- `tests/test_r6_g2_source_contact_objectivity.py`

Use the sealed 8×8 and 16×16 regional source FEG and T0 PRE
already used by the manufactured solver. Reconstruct source
edge incidence from exactly the triangle parent IDs and
parent triangle plate IDs. Require strict equality with
`source_contact_edges` and each `R6BND-T0-...` source
boundary ID. Neither shared nodes without a source
cross-plate edge nor unbound source edges can generate
a mechanical contact.

The 8×8 source region must have plates 5 and 8. The 16×16
domain contains 5, 8 and 11, with authoritatively
source-referenced 3-plate junction parent node 34587.
Do not call the presence of a global parent node in a
smaller crop evidence of a 3-plate junction there.

### Independent plate-local mechanical DOFs

For each unique `(plate_id, parent_node_id)` participating
in the selected regional source triangles, create its
own pair `(East,North)` at the same T0 source location.
Build the P1 stiffness from the genuine
`spherical_element_tangent` function, as in the recent
full-global sparse P1 test. Reuse true source thicknesses,
but **invented** viscosities
`eta_crust=1e20 Pa s`, `eta_mantle=1e21 Pa s`,
`lambda_h=eta_h`. The original PRE and Euler vectors are
SHA verified and never updated.

At each source contact parent node and **actual plate pair**,
construct a local EN unit normal oriented from plate p's
adjacent triangle centroid toward plate q's centroid. Multiple
segments of the same plate pair at a node are averaged.
Three-plate junctions get **pair-specific normals**;
do not collapse them into a single ambiguous normal.

## Three manufactured contact policies (STATIC velocity test)

Given original T0 plate-Euler source velocities `g`,
`C=0.5 mean(diag(K)) I`, and
`beta=30*C` (both entirely artificial), solve

```text
(C + K + H_policy) v = C g
```

with Jacobi-preconditioned SciPy CG. The manufactured
source P1 K and contact H have compatible *test*
velocity-penalty units, not qualified natural mechanics.

- **UNWELDED:** `H=0`. Existing independent plate
  source-view baseline, no fault coupling.
- **PENALTY_WELDED:** a finite symmetric-positive
  penalty for **both** components of every plate-pair
  relative contact velocity. This is **not an exact
  welded displacement constraint**, nor does it prove
  conservation of true boundary tractions.
- **CLOSING_NORMAL_ONLY:** activate one symmetric
  penalty along each pair's source-normal only when
  its original Euler **relative normal velocity is
  closing**. Permit tangential velocity differences
  and source-normal opening. Active-set flags are
  **frozen from the source Euler target**, with no
  evolving gap, force-sign complementarity or Signorini
  contact dynamics. Hence this is NOT a real physical
  slip/open/friction law; do not call its output
  physical fault mechanics.

For every policy report: number of active penalty
links, CG iterations, relative force balance and
virtual-work identity, synthetic P1/contact/drag work,
RMS velocity correction and maximum per-link normal,
tangential and total relative velocity. Require
residual/work `<2e-9`, and require that the manufactured
welded penalty has **nonzero demonstrable response**.
Source hash changes must cause failure.

### SO(3) objective frame test (100/1000 and large angle)

Take authentic source P1 facets touching source
contacts, independently rotate their underlying
3D Cartesian coordinates with each **actual Euler
rotation** at 100 and 1000 model years, and with one
additional intentionally large finite 3D rotation.
Recompute local EN bases at the rotated physical
positions. Let `T` transform the original nodal EN
velocities into the rotated nodal EN basis.

Check the exact faceted membrane-element equivariance

```text
K_rotated ≈ T * K_source * T^T
```

to relative Frobenius error `<3e-9`.
The separate unit test also verifies objective normal
relative velocity and work under a large SO(3) rotation.

This is **element-level frame-objectivity**, not a
time-updated geometric stiffness solver. Even if
it passes, the original global 1000-year stiffness
remained frozen at T0 and its geometry was only
diagnosed afterward. A genuine moving, rotating FEM
with contacts requires a separate incremental test.

**Important horizon distinction:** model years 100
and 1000 here are used in the **frame rotation
objectivity tests only**. The contact-response
comparison is a **static manufactured velocity
experiment** at T0; it does **not** integrate contact
stress, gap or displacement 100/1000 years. Do not
misreport the distinction.

## FAIR command

The script's full source-backed run is **pending**.

```bash
set -euo pipefail

cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
test -z "$(git status --porcelain)"
git fetch origin r6/multiphysics-integration-20261026
git switch --detach FETCH_HEAD
git rev-parse HEAD

source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux

export PYTHONPATH=src:.
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

python -m pytest -q \
  tests/test_r6_g2_source_contact_objectivity.py \
  tests/test_r6_g2_global_sparse_p1_static.py \
  tests/test_r6_g3_spherical_exterior.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test -d "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01"
test -d "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01"

python -m experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --output "$BASE/G2_SOURCE_CONTACT_OBJECTIVITY_NEW_01"
```

The target evidence directory must be new and **exclusive**.
Do not overwrite or reinterpret old FAIR source evidence.

## Expected results and decisions

Accept only when authentic region source plate-edge
pairs, triple-junction ownership, P1 split-view source
assembly, contact penalty response and true SO(3)
equivariance all meet their declared gates. If
one fails, preserve the failing diagnostic instead
of inventing physical source constraints.

If PASS:
1. Build a **regional dynamic manufactured**
   contact engine with evolving gap and an actually
   enforced complementarity/contact-force sign
   condition, using objectively updated frames.
2. Check energy/traction balance, 100/1000 model-year
   restart, dt and fixed-extent mesh convergence.
3. Scale the explicitly declared contact operators
   and frame update to global 12-plate P1.
4. Independently qualify true G2 lithology,
   hydration and rate/P/T laws, G3 physical mantle
   forcing and normal support, and G4 thermal/mass
   transport before authorizing any geological T1.

```text
GLOBAL_12_PLATE_SOURCE_P1_100_1000_FAIR=PASS_29_OF_29
REGIONAL_SOURCE_CONTACT_POLICIES=NEW_FAIR_PENDING
SOURCE_SO3_ELEMENT_OBJECTIVITY=NEW_FAIR_PENDING
GLOBAL_DYNAMIC_CONTACTS=NOT_RUN
D_024=ACTIVE
physical_T1=null
```

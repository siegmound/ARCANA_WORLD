# ARCANA R6 — Integrated G1→G2 numerical experiment at 100 and 1000 years

**Date:** 2026-11-20. **Branch:** `r6/multiphysics-integration-20261026`.
**Parent:** `ebb60374a9be6093cb6182c4bed6ac1d3dac9e40`.
**Scope:** engineering source-bound one-way **G1 rigid kinematics + G2 passive
T0 thermal/material columns** on original 64,442-node source world; no
mechanical/contact force solve and no physical history.

## Decision

The author proposed a joined 100/1000-year integration test to detect
errors *before* committing to further G2 material research. This is
scientifically useful, with a precise semantic distinction:

- **GO**: test the actual G1 states at year 100 and 1000 against the
  original T0 51-field G2 nodal PRE, without replacing values.
- **NO-GO for a physical two-way 100/1000-year evolution**:
  material chemistry/mineralogy, water/poroelastic state, creep yield,
  G3 exterior/basal force closure, fault interface and thermal evolution
  are unratified. G2 cannot physically change G1 velocities or T1 today.
  Converged engineering parameters would not change this source authority.

Reuse the existing independently generated 100 and 1000-year G1 FAIR
checkpoints rather than rerunning global Euler transport. The new script
**does not integrate G2 over 1000 sequential years**, since no time
evolution law exists; it audits *the same source columns* at both genuine
G1 snapshots, with all original G1 time integration and restart evidence
SHA-checked. Be explicit about this limitation.

## Software added

Driver: `experiments/plate58_deforming_explore_v1/g1_g2_passive_100_1000y.py`.
Tests: `tests/test_r6_g1_g2_passive_100_1000y.py`.

### Full source and numerical audit

1. Use the original **G1 full-planet canonical source** and the same
   immutable 100-year and 1000-year FAIR receipts. Bind their
   `REPORT.json`, `MANIFEST.json` and checkpoint hashes; require
   original source PRE and FEG SHA, 100-year phase-1/phase-2 **bit
   identity** and G1-reported acceptance.
2. Associate each original 0-based G1 material-view node index + 1
   with the exact 51-field PRE line of that **1-based** parent node,
   including plate-shared view copies. Do not resolve contacts by
   assigning one plate velocity to multiple plate views.
3. Scan **all 64,442 source columns**, not only plate 5:8. Validate
   layer geometry, densities, thermal polynomial coefficients and
   exact cubic temperature bounds, surface/Moho/LAB temperature
   anchors, and the governed numerical ceiling 1900 K. Invalid
   source columns are counted with sample IDs and remain unfilled.
4. At years **100** and **1000**, independently calculate maximum
   within-plate relative edge metric change and maximum radial
   unit-sphere deviation on all original plate-local triangles.
   Threshold for each metric: `1e-10`; distinguish geometry drift
   from **physical contact divergence** between different Euler views.
5. Report original G1 numerical acceptance/restart data, G2 eligible
   vs unavailable columns, full-source source-temperature ranges and
   the source areal column mass proxy `rho_c h_c + rho_m h_m` for
   material metadata only (NOT actual FEM mass conservation).
6. Require original manifests and source PRE hashes unchanged;
   produce a **new exclusive** audit report + SHA-linked manifest.
   Never rewrite G1 original checkpoints, world canon or HistoryStore.

No invented G2 creep law, cold-crust wet/dry assumption, basal
coupling, stress or G4 mass evolution is employed. **Zero measured
rigid-plate strain in a pass is expected kinematically; it does not
demonstrate that real plate contacts are mechanically accommodated.**

### FAIR execution

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
  tests/test_r6_g1_g2_passive_100_1000y.py \
  tests/test_r6_global_100y_kinematic.py \
  tests/test_r6_global_1000y_kinematic.py \
  tests/test_r6_g2_exact_thermal_validity.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
python -m experiments.plate58_deforming_explore_v1.g1_g2_passive_100_1000y \
  --prior100 "$BASE/GLOBAL_T0_KINEMATIC_100Y_NEW_01" \
  --prior1000 "$BASE/GLOBAL_T0_KINEMATIC_1000Y_NEW_01" \
  --output "$BASE/G1_G2_PASSIVE_100_1000Y_NEW_01"
```

Paths are the original evidence names documented in the G1 baseline
readmes. If an operator's real directory differs, inspect the existing
evidence name and use that exact read-only path; do not fabricate a
replacement report. A fail-closed error or G2 column gap is a useful
diagnostic, not permission to edit T0 sources.

### FAIR interpretation

**Status not yet run for this new code**; unit tests are defined but no
new FAIR result is claimed.

Report to compare:
- G1 `prior_100y_prefix_bit_exact`, 1000-year restart error,
  drift, inverted triangles, contact gap;
- G1→G2 maximum relative edge change at 100/1000 and maximum
  radial norm error, **by real checkpoint**;
- G2 all-source eligible count and reasons if `<64442`;
- PRE temperature range and thermal anchor mismatch counts;
- source identity, material-view cardinality, source immutability.

If all numerical validations pass, this closes **passive one-way
integration/geometry/source consistency**, not the meaningful physics
question. Then run an intentionally synthetic, noncanonical **small
regional two-way G1/G2 engineering sensitivity** only after an explicit
bounded material scenario is chosen, while physical G2↔G3/T1 remains
blocked by D-024. A two-way 1000-year forecast needs a physically
qualified solver, pressure and basal/outer force closure, thermal and
material transport rules, events and timestep convergence.

```text
G1_100_1000_SOURCE=EXISTING_FAIR_QUALIFIED
G2_SOURCE_51_FIELDS=AVAILABLE
G1_G2_NEW_INTEGRATION_DRIVER=PUBLISHED__FAIR_PENDING
G2_CONSTITUTIVE_AND_G3_FORCES=UNQUALIFIED
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_T1=null
D_024=ACTIVE
```

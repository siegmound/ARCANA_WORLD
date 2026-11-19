# ARCANA R6 — FAIR G3 membrana planare PASS e nuovo operatore superficie sferica

2026-11-19. FAIR operator output: commit `92138970b052e7c1451d618a225ffeb53a46a5a9`, `tests/test_r6_g3_exterior_variational.py` **8 passed in 0.09s**. Tests use only synthetic viscosities and manufactured fields; not a calibrated solve or a new ARCANA world state.

## Substantial implementation: P1 FEM on embedded spherical facets

The new module `spherical_exterior.py` uses canonical T0 latitude/longitude plus the **existing R6 numerical radius** `prepare.RADIUS_M=6371000m` to embed source triangles in R3. The radius is the existing experimental metric convention, NOT a newly ratified ARCANA physical radius.

For each triangle:
1. Obtain 3D spherical vertex coordinates and **per-node east/north tangent vector bases**, not a single constant tangent-plane basis for the entire regional domain.
2. Construct a local oriented facet plane and exact P1 constant-strain triangular operator `B`.
3. Project each node's two east/north velocity degrees of freedom onto the facet via block transformation `T`; `B_surf = B @ T`.
4. With **explicitly supplied** positive depth-integrated Newtonian candidate viscosities, assemble `K_e=A_facet B_surf.T D B_surf`. There are no default material values, tractions, basal laws or authorial promotions.
5. Record both physical polygon facet/chord area and exact spherical geodesic triangle area (vector `atan2` spherical excess), with maximum distortion and whole-area relative difference.
6. Manufacture rotations `v=Ω×r` on three Cartesian axes: they are tangent to the sphere and the P1 faceted operator should have **zero in-plane symmetric strain**, which is asserted numerically.

**Important:** this is a piecewise-planar/faceted approximation to a spherical membrane, **NOT the covariant smooth-sphere viscous FEM used by SHELLS** and not a verified nonlinear `Mohr/OneBar/Diamnd` tensor equivalent. The former single regional planar map has been replaced by node-local bases for this new kernel. Area deficit and metric error are quantified; physical solutions still require mesh convergence and actual G2/G3 forces.

No physical `K`, material `eta_h`, `lambda_h`, load `f`, GPE/basal support or T1 is authored here. The geometry-only FAIR audit **does not accept a viscosity argument**.

The source replay `audit_fair_source` reads unchanged SHA-bound prior FAIR `CONTINUATION_A.json` and `MULTISCALE_INTERFACE.json`, verifies the original FEGs and source node orders, emits a new `SPHERICAL_AUDIT.json` and SHA manifest. It gives the actual max planar facet vs geodesic spherical triangle area loss for the **8×8 120 exterior triangles** and **16×16 504 exterior triangles**, the source identity of the largest discrepancy, and source parent IDs of the already confirmed three-plate junction without inventing them.

## Test and FAIR verification

8 locally executed synthetic tests PASS (including all 3 Killing rigid-rotation modes, surface metric winding, positive energy, missing material and source-geometry audit on 8×8 synthetic parent mesh); FAIR test and genuine FEG area audit **pending**.

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# If clean:
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
python -m pytest -q tests/test_r6_g3_spherical_exterior.py

MULTISCALE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01
MECHANICAL=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_MECHANICAL_INTERFACE_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_SPHERICAL_AUDIT_NEW_01
python -m experiments.plate58_deforming_explore_v1.spherical_exterior "$MULTISCALE" "$MECHANICAL" "$OUTPUT"
```

The next work **must target physical closure**, not more geometry-only variants: select source-supported and validity-limited G2 full-column ductile+brittle effective law and explicitly handle SHELLS shared-`eCreep` nonlinear effects; then construct the exterior G3 A force and basal/GPE balance under explicit boundary provider. Only after this qualification can a bounded noncanonical mechanical solve be proposed. D-024 still blocks T1.

# R6 full-planet T0 — Phase 1: 100 model years

**Scope:** source-bound noncanonical **rigid-plate kinematic baseline with PASSIVE T0 PRE**. No ShellSet/G2/G3 physics, no tectonic accommodation, no canonical T1/HistoryStore, no property or resource evolution.

The runner verifies canonical T0 node/triangle plate partition and its external SHA, 12 Euler vectors, the first-segment rift-event bound, PRE line count and source SHA, and source geometry binding. Then it builds one transient **material view per plate**, not a single multi-valued global continuous FEG DOF. All per-plate triangles are transported through 100 annual 1-year Euler rotations. Milestones 0,1,10,50,100 compare to direct quaternion rotation, signed triangle area, norm and shared boundary-node separation. The latter is missing contact accommodation, not drift. SHA-verified round-trip checkpoints at 0,50,100 and an independent 50+50 replay verify persistence. Wall/CPU/RSS and bounded checkpoint I/O are measured. Fixed admissibility limits 1e-11 in unit XYZ and steradians are **numerical fail-closed tolerances**, not geology acceptance.

Historical FAIR R2 1000Y ~110.02 s / 9 synthetic cells is not a global model performance result. The global runner measures its own actual cost.

## FAIR — isolated clean worktree, Phase 1 only

Verify the target remains clean before updating; preserve the original dirty worktree and all existing evidence.

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# STOP if any output is present; only when clean:
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

python -m pytest -q tests/test_r6_global_100y_kinematic.py

OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GLOBAL_T0_KINEMATIC_100Y_NEW_01
python -m experiments.global_t0_kinematic_baseline_v1.benchmark "$OUTPUT" --years 100
```

No source or evidence overwrite: new output folder only. The script refuses `--years 1000`: the 1000Y phase depends on 100Y FAIR numerical/resource qualification and a separately updated launch. A successful run writes `REPORT.json`, `MANIFEST.json`, and three `KINEMATIC_{000,050,100}.npz` checkpoints. Retain them on FAIR; return the printed JSON results for the next decision. Do not compare multi-plate nodal gaps with rigid-plate numerical drift.

**Expected status (not a claimed FAIR result):**
`PASS_GLOBAL_T0_100Y_KINEMATIC_BASELINE__CONTACTS_UNRESOLVED`.

## Invariants / limitations

- T0 Euler is held constant only within the first governed segment; the runner checks the source census event horizon.
- Passive PRE nodes are read/hashed but never evolved or extrapolated to create new temperature/material data.
- Contact opening/separation cannot be interpreted as newly created ocean, tectonic lithosphere or coastline without G2/G3.
- The area check is **per plate-owned triangle**, not the unresolved union of globally colliding/overlapping plate polygons.
- The benchmark measures only implemented kinematics + load/serialization. **Do not use its timing as an estimate for G2/G3 physical solve.**
- No physical T1 or canonical WorldSim state is produced. Author-ratified G3 architecture A remains the next physical target after this baseline.

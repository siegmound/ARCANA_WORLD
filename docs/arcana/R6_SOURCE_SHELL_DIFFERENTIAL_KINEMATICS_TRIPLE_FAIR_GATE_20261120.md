# ARCANA R6 — Differential kinematics of original matched shell boundary and triple junction

**Date:** 2026-11-20. **Engineering only; FAIR PENDING.**

## Verified source prerequisite

Prior FAIR source-shell midpoint co-normal opening driver at `32d91c0b3f32dfe20fd3ce88a4321a246a4bfb84`, tests 88/88 PASS and report SHA256 **independently verified by FAIR operator on its own files**: `2fa5615788eab08bd02cd4bd5d9a4d78e84aeb8b38425c17cadbaf5ed9fe4f27`. The old fixed T0 KKT model was *not* replaced by moving-contact mechanics. At 100/500/1000, region 8x8 has zero negative original matched-shell boundary gaps (all 12 mathematical shell gaps positive); region 16x16 has 9/9/7 negative source shell midpoint gaps among 36 original edges. This is NOT physical rock penetration; no closed solid source volume.

## New differentiable kinematic gate

**Driver** `experiments/plate58_deforming_explore_v1/g2_source_shell_differential_kinematics.py`. **Tests** `tests/test_r6_g2_source_shell_differential_kinematics.py`. Both source only; full FAIR tests and run not yet executed.

- Use EXACT original source FEG/PRE, original 8x8 / 16x16 R6BND-T0 plate-owned edges and their real per-plate adjacent triangles. Preserve source triple parent 34587 and 13/39 contact links; no made-up boundary geometry.
- Depend on the SHA-verified previous source shell REPORT and source hashes; replay ALL source edge IDs and signed midpoint gaps at 0,100,500,1000 to <1e-7m.
- Sample **0 and every 25 model years through 1000 inclusive = 41 samples**, reconstructing the existing source fixed-T0-KKT trajectory using its original manufactured forces and 1-year integrator. This does **not** solve a new KKT. In particular, the t=0 source Euler rate is not the constrained t=1 velocity; report the baseline explicitly.
- Differentiate the SAME material-matched geometric shell gap `g=(mid_q-mid_p)·n`, `n=(m_q-m_p)/||m_q-m_p||` from the original adjacent in-face co-normals. Use current authentic geometric point rates `v` from the old source-trajectory reconstruction and independently directional-perturb positions by ±0.05 and ±0.025 model-year units. Split `gdot = (midV_q-midV_p)·n + (mid_q-mid_p)·n_dot` where `n_dot` is finite-differenced from the SAME co-normal functional. Decomposition mismatch <1e-4m/model-year; independent rate refinement <1e-4m/model-year; arbitrary rigid SO(3) rate invariance <1e-5m/model-year at original source checkpoints.
- Record **sampled** sign transitions for each source edge under ±1µm diagnostic deadband: T0-zero departures, opposite definite signs between 25-year samples, and near-zero/ambiguous intervals. Sign-change time is **only bracketed**, NOT located exactly or proven exhaustive between 25-year intervals.
- At source triple 34587, inspect 3 original plate-owned point/velocity views (plates 5,8,11), vector separation loop closure, and material relative velocities at all samples. The vector closure is an indexing consistency identity, **NOT a new scalar gap compatibility law**, force equilibrium, 3-body Signorini contact or physical boundary response.
- If any source feature loses sidedness, return `NOT_QUALIFIED` with null rate; do not impute a signed physical contact value. No new physical contact forces or natural G2/G3/G4 rheology.

## FAIR clean-checkout command

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
test -z "$(git status --porcelain)" || exit 1
git fetch origin r6/multiphysics-integration-20261026
# switch to the EXACT commit SHA of this new driver once published
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH=src:.
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

python -m pytest -q -ra --tb=short \
  tests/test_r6_g2_source_shell_differential_kinematics.py \
  tests/test_r6_g2_source_shell_conormal_gap.py \
  tests/test_r6_g2_source_owned_face_topology.py \
  tests/test_r6_g2_contact_feature_admissibility.py \
  tests/test_r6_g2_t0_normal_segment_jacobian.py \
  tests/test_r6_g2_moving_3d_contact_parallel.py \
  tests/test_r6_g2_regional_unilateral_contact_time.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
test ! -e "$BASE/G2_SOURCE_SHELL_DIFFERENTIAL_KINEMATICS_NEW_01"
python -m experiments.plate58_deforming_explore_v1.g2_source_shell_differential_kinematics \
  --multiscale "$BASE/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01" \
  --nodal "$BASE/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01" \
  --prior-unilateral "$BASE/G2_REGIONAL_UNILATERAL_CONTACT_TIME_NEW_01" \
  --prior-shell "$BASE/G2_SOURCE_SHELL_CONORMAL_GAP_NEW_01" \
  --output "$BASE/G2_SOURCE_SHELL_DIFFERENTIAL_KINEMATICS_NEW_01"
```

## Decision

Passing this gate would demonstrate **ENGINEERING_ONLY** rate consistency and time-sampled boundary opening/closing diagnostics for the *same original mathematical shell gap*. It does not prove physical 3D solid nonpenetration, true contact KKT, interfacial shear/friction, geological loads or closed-volume authority. `D-024=ACTIVE`, `physical_T1=null`, no canonical or HistoryStore mutation, no physical solver runs.

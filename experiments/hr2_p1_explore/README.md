# EXPLORE: working spherical quartic diffusion prototype

This namespace is separate from frozen V1, hr2_p1_r1 and all historical gates.
User-authorized EXPLORE permits short iterations without formal interval proofs.
This is manufactured numerical engineering, NOT VALIDATE or ARCANA geology.
No global T0 package is consumed; no real cover, density or diffusivity is inferred.

`model.py` uses 15 generic tangent monomials through degree4, Gauss quadrature,
area-average cell moments, SVD and a shared integrated face gradient. Frames are
local east/north; one coefficient packet per latitude/face-axis is rotated across
longitude using exact uniform-sphere symmetry. Three independently built faces
check this cache against fresh integration. Coefficients do not depend on the
manufactured mode. Conductance-based low flux and conservative FCT budgets limit
shared correction transfers; final stocks are never clipped or renormalized.
Only roundoff-negative budget slack is floored, after a low-state range guard.
Floating range checks have an explicit128eps scale allowance. Conservation is
checked against the original8gamma-style per-step accounting, not corrected.

`probe.py` provides independent exact spherical cell averages and integrated face
rates for z,x,shifted-y,rotated degree1 and degree2 modes. It retains arrays,
coefficient packets, actual CSR geometry and main/half diagnostics. Temporal
substeps are explicit and separate from saved-state cadence or display pixels.
The current manufactured R=6371000m, kappa=R²*0.01/year, mean8m and T=0.0001year
are artificial. Constant, zero, spike, random and CFL/input negatives are short.
The local2x2 oracle checks low/limited results without any spherical reconstruction.

`extra_checks.py` uses a same-spatial-operator matrix exponential for an independent
standard-numeric time oracle at16x8, T0.2year. Native direct/split and separate-child
8-step checks use `native.py`; this stores all operative geometry, CSR coefficients,
volumes, source/runtime identity and clocks. No REC1/B0/crash-tail qualification is
claimed. The loader is an experimental known-file reader, not hardened admission.

Example explicit short run (new exclusive output required):

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK
PYTHONPATH=experiments PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B -m hr2_p1_explore.probe \
  --output /NEW/EXCLUSIVE/EXPLORE --heights 8 16 32 64 --order 16 --minimum-steps 32
```

An output height64 means128x64 cells. Height128/256x128 is implemented and measured,
but the recorded finest case fails the historical5% main/half error comparison;
its 1e-13m errors require precision/time-error investigation. Do not advertise a
complete original gate PASS. No default engine/CI registration exists.

Next VALIDATE must independently review discretization/temporal and limiter
stability, precision floors, additional nonharmonic data, true-mean/rounding bias,
full native clocks/source/admission/corruption tests and B0 if needed. Standard
quadrature agreement is numerical evidence only. Neither formal certificate
closure nor production/scientific authority is claimed by this prototype.

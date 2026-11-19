# HR2-P1 isolated preparation — CREATED_NOT_RUN

This directory is an opt-in numerical-method fixture, separate from the existing
R6 engine. No source file in src/arcana_worldsim is changed. The package initializer
does not import a model, register a provider, dispatch a simulation or load T0.

The current delivery prepares implementation, tests and acceptance. It does not
execute/import the new numerical model, collect tests or produce a numerical
PASS. P0's proposal status is not itself execution permission. The user's new
preparation request supersedes its old implementation block for these additive
files; it does not ratify geological input fields or scientific/production use.

## Explicit artificial problem

- Sphere radius6371000m. Fixed flat bedrock and closed external boundary are
  declared test-model choices, not assertions about natural ARCANA geology.
- Uniform diffusivity405896410000m2/year = R2*0.01/year; mean height8m and
  harmonic amplitude1m. These deliberately artificial values were not read from
  any world data and are not calibrated regolith properties.
- Density is absent by default. The optional2500kg/m3 value appears only as a
  declared uniform mass-conservation test; no material role is assigned a density.
- Native state is the binary64 per-cell volume V=A*h. One face is evaluated once,
  with equal/opposite transfers and simultaneous updates from the old state.
  Negative stocks, nonfinite values and excessive timesteps fail, without clipping,
  correction, renormalization or an invented natural source term.
- Explicit guard dt<=0.5*min(A_i/sum_j c_ij), c=kappa*face_length/center_distance.
  Longitude is periodic; polar external faces have zero length. Polar point
  contacts and the old geography graph's polar clique are not flux faces.

## Files and scope

model.py implements geometry, a conservative explicit step, a resumable window
schedule and a complete native checkpoint. manufactured.py contains the declared
fixture parameters and independent continuum cell averages. checkpoint.py prepares
native serialization and a bounded B0 adapter storing **full native values** plus
the committed observation/diagnostic-prefix binding. It does not merely reference
an already-stored HR1 array. Existing B0 is reused without changing its invariants.

The checks live in experiments/hr2_p1_checks/checks_*.py, outside the default
test_*.py discovery pattern; the runner names both files explicitly.

The native checkpoint includes actual area/face geometry, current volumes,
parameters and source/runtime identities, initial-field identity and total volume,
clock, accepted steps, pending window/substep position, completed windows, dt
histogram and cumulative balance allowance. No hidden constitutive/Deep state
exists in this isolated model. Such state would require a new checkpoint schema
if domains are coupled later. Integrity hashes are not external authentication;
the independently pinned source contract and expected input hashes remain required.

## Three distinct resolutions

1. **Numerical:** actual FV cell count and each accepted CFL-constrained physical
   substep. Tests specify16x8..256x128 meshes; no2K numerical qualification is
   implied. Spatial convergence uses the same fixed0.0001-model-year endpoint
   on every mesh, not annual256x128 evolution. Temporal convergence uses16x8
   and1model-year. Native direct/split3Y/10Y fixtures also use16x8.
2. **History:** B0 commits full numerical states at explicit checkpoint times and
   binds ordered observations/diagnostics. It does **not** claim that full values
   at every internal substep were archived or that missing states can be queried
   without numerical replay. A complete causal archive policy is a separate
   contract. Fsync, native checkpoints and B0 visibility are different operations.
3. **Visualization:** not implemented here. Display resampling cannot add physical
   resolution or create a restart state; no output pixel count is evidence of a
   physical mesh. No legacy history or rendered global states are generated.

## Predeclared verification

acceptance.json V1 freezes the inputs, criteria and scope before any execution.
The independent rational2x2 oracle is a local patch, not a2:1 spherical raster.
Geometry/seam/pole tests cover every requested test mesh. Both axisymmetric
sin(latitude) and non-axisymmetric cos(latitude)*cos(longitude) continuum modes
must satisfy spatial L1/L2/Linf observed order>=1.5 on all successive refinements.
Temporal tests isolate integration error with an independently derived exact
same-mesh latitude-mode decay; required order is0.9..1.2. A half-dt spatial arm
must show temporal contamination <=5% of the measured continuum L2 error.

**Unresolved until measured:** conservative/positive fluxes do not prove polar
consistency or convergence for non-axisymmetric cell-average fields. The
two-point center-gradient stencil must pass those tests too. An axisymmetric
PASS cannot bypass a failing longitude-mode/polar result. Keep failed evidence;
any discretization correction is a reviewed new source version, not tolerance
tuning or an automatic retry. No numerical qualification is claimed at delivery.

Native tests prepare direct/split3Y/10Y, true separate-process resume, pending-
window checkpoint detachment, corruption/wrong-source/mesh/config/clock/initial-
field negatives, B0 prefix/clock/parent matching and stale-view rejection.
Real SIGKILL and linked-tail continuation remain an independent future gate;
these prepared bounded B0 tests do not certify power-loss or production recovery.

## Future explicit bounded execution (not performed in this delivery)

Use the existing arcana-r6-linux interpreter; no installs or thread/resource caps.
Before future execution, review this source snapshot and the immutable preparation
evidence. Obtain the **reviewed** SOURCE_CONTRACT SHA from that evidence, not by
silently refreshing pins after modifying code. SOURCE_CONTRACT.json binds the
new solver/tests/acceptance and the308 old measured source/test pins.

```bash
PYTHONPATH=src:experiments PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B \
scripts/r6_hr2_p1_qualification.py \
--output /NEW/EXCLUSIVE/HR2_P1_BOUNDED_OUTPUT \
--expected-contract-sha256 REVIEWED_SOURCE_CONTRACT_SHA256 \
--execute-manufactured-method-tests
```

The output path and reviewed digest above are explicit unfilled run parameters,
not an already executed invocation. The runner disables unrelated pytest plugins,
conftest/cache/config and collects only the two new explicitly named checks files. No arbitrary
horizon/mesh/dataset/production mode exists in this CLI. It has no automatic retry.
It records source identity before/after, JUnit, actual convergence tables,
native/B0 service measurements, full subprocess CPU, sampled process-tree RSS,
stdout/stderr and a new manifest. Per-face service time includes checks/hashing;
it is not falsely labeled pure floating-point arithmetic. OS cache is uncontrolled.

Only successful real tests plus complete required evidence may emit the P1
manufactured-method PASS marker. That would still leave real input admission,
six-grid physics, crash-tail recovery and scientific/production authority false.

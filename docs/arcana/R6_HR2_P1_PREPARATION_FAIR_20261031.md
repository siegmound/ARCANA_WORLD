# HR2-P1 — isolated manufactured spherical diffusion preparation

2026-10-31. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`HR2_P1_PREPARATION=PREPARED_SOURCE_TESTS_AND_FIXED_ACCEPTANCE_NOT_RUN`

`HR2_P1=BLOCKED_NUMERICAL_QUALIFICATION_NOT_EXECUTED`

The requested preparation is complete. All new numerical code, test cases and
launcher remain **CREATED_NOT_RUN**. Only stdlib file/hash/JSON/AST checks were
performed; no numerical model was imported, no pytest collection/test or physical
advance occurred. No numerical PASS, convergence order, runtime/resource profile
or physical accuracy is claimed. No1000Y/10k/100k, commit, push, reset, merge,
installation, new dataset acquisition or original archive change.

## Authority, isolation and source identity

Read in full: `~/HPC-POMDP/Arcana/R6_HR2_P1_PROPOSAL.md`, the FAIR HR2-P0 report
and P0 `MINIMUM_PHYSICS_AND_VALIDATION.md`. The proposal's older pending
implementation authorization is superseded by the user's new **preparation**
request for these additive files. It is not silently promoted to execution
permission or geological input ratification. A future explicit bounded gate
can execute the prepared tests; no such execution occurred here.

Branch `r6/runtime-copy-r1-fair`, HEAD
`2c71370eb9a959c78121ce1c88ec8e9e37187787`; existing uncommitted R1/R2/REC1/L1
and HR1/P0 sources are preserved.308 measured pre-existing source/test pins and
31 pre-existing dirty files were captured before authoring. The P0 manifest
`d0581ef1ea25558b3246269c3cf36178a0bcb3d8807393a8b6e16ed1269a9963`
and all404 members were verified. Historical WORKTREE_BEFORE.tar and proposal/
P0 plan copies are in new external `HR2_P1_PREP_20261031_01`. The only pre-existing
files edited are the five ledger handoff documents; no old numerical/test source
or original history archive was modified. No core provider or default CI/engine
entrypoint registers the new operator.

New files:

| Path | Prepared responsibility |
| --- | --- |
| `experiments/hr2_p1/model.py` | Sphere/face metrics, explicit simultaneous finite-volume update, positivity guard, conservation ledger, resumable window/native state |
| `experiments/hr2_p1/manufactured.py` | Explicit artificial parameter/initial-field factory and independent analytic cell-average expectations |
| `experiments/hr2_p1/checkpoint.py` | Detached full native serialization and bounded B0 full-native/prefix adapter; no production crash/tail claim |
| `experiments/hr2_p1/acceptance.json` | V1 predeclared criteria, coefficients, scopes and forbidden promotions |
| `experiments/hr2_p1_checks/checks_method.py` | Independent rational2x2, sphere geometry/seam/poles, positivity/balance/guard and both-mode spatial/temporal convergence |
| `experiments/hr2_p1_checks/checks_restart.py` |3Y/10Y native/split/child resume, pending-window state, B0/context/source/prefix/stale/corruption negatives and service telemetry |
| `scripts/r6_hr2_p1_qualification.py` | Explicit-only isolated bounded future qualification and exclusive evidence; source pins before/after |
| `scripts/r6_hr2_p1_resume_probe.py` | Expected-SHA-bound native/B0 child continuation, target3Y or10Y only |
| `experiments/hr2_p1/SOURCE_CONTRACT.json` | Exact new source/test/acceptance hashes and308 preserved old pins |
| `experiments/hr2_p1/README.md` | Operator contract, limits, source authority and future runbook |

There are17 statically identified test functions with parameterized cases;
**zero tests collected or executed**. AST syntax/JSON validity does not establish
numerical correctness. Check files use `checks_*.py`, outside default pytest
`test_*.py` discovery; the explicit runner names only these two files and suppresses
unrelated configuration, conftest/plugins/cache.

## Manufactured equation and declared inputs

Numerical state: nonnegative per-cell volume V=A*h in m3, binary64. The proposed
physical method is dh/dt=kappa*Laplace_Beltrami(h) on a closed spherical surface,
with fixed flat bedrock and no external sources. One unique internal face has
c_ij=kappa*L_ij/d_ij [m2/year], Q_ij=c_ij*(h_i-h_j) [m3/year]. The step computes
all face transfers from one old state and applies equal/opposite contributions
simultaneously. There is no clipping, hidden mass correction or renormalization.

Explicit **test-only** values:

- R=6371000m; kappa=405896410000m2/year=R2*0.01/year, intentionally artificial.
- Mean cover height8m; degree-one harmonic amplitude1m. Inputs are analytic area
  averages, not samples replicated from nine regional cells or global T0 data.
- Density is absent by default. A separately declared uniform2500kg/m3 is used
  only in a mass-identity test. It is not assigned to any R6 material role.
- h=8+sin(latitude), and8+cos(latitude)*cos(longitude), with continuum decay
  exp(-2*kappa*t/R2). Constant/spike fixtures and a rational local patch are
  explicit independent tests. No real regolith, climate, geology or Deep field
  is supplied, inferred or filled with zeros.

The global T0 packages retain their original missing/authorial semantics. This
fixture reads none of them. It cannot establish scientific ARCANA geology,
calibrated diffusivity or observational cover/density. Scientific and production
flags remain false even after any future manufactured-method PASS.

## Geometry, stability and frozen acceptance

Actual numerical meshes are2:1 latitude/longitude spheres. Cell areas use
R2*dlon*(sin north-sin south); meridional shared-face lengths and positive
center distances are explicit. Longitude wraps by one face per row; external
polar faces have zero length. Point contacts and the original geographical
polar-row clique are not numerical faces. A face is evaluated once and its
represented transfer is used at both endpoints.

The explicit positivity guard is dt<=0.5*min(A_i/sum_j c_ij). Small polar cells
may force many substeps. The implementation never stretches dt to an annual
output interval. A zero-kappa state is a no-flux case with a finite requested
window, not an infinite serialized timestep. Rejection occurs before mutation
of the accepted integrator state.

`acceptance.json` is frozen **before execution**. It requires:

1. Independent rational2x2 **local patch**, not a global raster: areas1,2,3,4;
   h1,2,3,4; conductances1,2,3,4 on faces01/02/13/23; dt=1/10. Signed transfers
   are(-1/10,-2/5,-3/5,-2/5), resulting volumes(3/2,9/2,9,15), total30. Negative,
   duplicate/noninteger-face, bad-area/config/clock and unstable-dt cases reject.
2. Genuine16x8 spherical constant/positive/harmonic states, unique faces, area
   closure, explicit seam crossing, no polar-clique flux, nonnegative stocks
   and volume/declared-mass conservation. Per-step rounding budget is derived
   from gamma_m with m=2*max_degree+6 and magnitudes of old/new stocks/transfers,
   with a fixed8x allowance. Cumulative error cannot exceed accumulated bounds;
   there is no post-hoc balance correction.
3. Fixed-time spatial refinement16x8→32x16→64x32→128x64→256x128, at0.0001
   manufactured model-year on every mesh. Both axisymmetric and non-axisymmetric
   area-averaged continuum modes must attain L1/L2/Linf observed order>=1.5 on
   every successive refinement. A half-dt arm must differ by<=5% of continuum
   L2 error; source versions/criteria must not be changed to hide failure.
4. At16x8 and fixed1year, dt,dt/2,dt/4 must show temporal L2 order0.9..1.2.
   The temporal oracle is an independently derived exact-in-time **same-mesh**
   latitude-mode decay, rate2*kappa/R2*sin(dphi)/dphi. It isolates time error;
   the spatial study separately uses the continuum decay, not that discrete
   eigenvalue to manufacture convergence.
5. Full native3Y/10Y direct/split and separate-process continuation at16x8 with
   identical planned horizon/scheduling; mid-window state restored too. All
   source/mesh/config/initial-field/clock/prefix identities must match.

**Design risk remains open:** a conservative positive two-point flux stencil
is not automatically a consistent polar discretization for cell-average fields.
The difference between cell averages and angular midpoint values is particularly
important for the non-axisymmetric mode near polar rows. That test is mandatory;
axisymmetric success alone cannot qualify the method. There is currently no
measured result or proven all-mode convergence. A failure must remain evidence
and trigger a reviewed discretization revision, not altered thresholds or retry.

## Complete numerical state and B0 plan

Native checkpoints store actual area/face geometry, current volumes, all test
parameters and material identity, source/runtime hashes, initial-field identity
and volume total, current time, accepted-step count, completed windows, pending
window/end/step count/position, hexadecimal dt histogram and accumulated balance
allowance. Returned checkpoints own their containers. Geometry/state/source/
clock/CFL/ledger and authority are verified on restore; native state does not
contain a reference-only substitute for the actual current numerical arrays.

The prepared bounded B0 adapter embeds the full native checkpoint in the typed
restart state, alongside immutable fsynced journal-prefix identity, ordinal/time
high-water and parent checkpoint. It uses the existing unchanged B0 transaction
and expected-parent-view CAS. Initial-field identity is bound as well as mesh,
parameters and fixed manufactured forcing. Corrupt, wrong-source/config/mesh,
wrong-initial-condition, stale-parent and inconsistent-clock cases are prepared.

These are **unexecuted bounded adapter tests**. Real SIGKILL, storage durability,
linked continuation after crashes and production recovery are a separate gate.
No unconfirmed file is adopted or removed. Original HR1/10k failed roots must
remain immutable. Native/B0 pair serialization here is new fixture code, not a
claim that the old REC1 qualified implementation was changed or weakened.

## Numerical, historical and display resolutions

- **Native physics resolution:** actual FV cells and accepted CFL-limited
  substeps. Highest prepared spatial study is256x128 over a short fixed time,
  not annual256x128 or2K physical simulation. Longest prepared artificial native
  restart tests are3Y/10Y at16x8.
- **Recorded history resolution:** full state at explicitly published native
  checkpoint times, with ordered observation/diagnostic-prefix records. The
  adapter does not claim full values at every internal substep were persisted.
  Missing intermediate values need an explicitly qualified archive policy or
  numerical replay, not a fictional exact historical query. Journal fsync,
  checkpoint state and B0 restart visibility remain distinct operations.
- **Visualization resolution:** no renderer is implemented. Interpolation or
  extra pixels cannot add physical information, restore state or certify mesh
  convergence. No legacy export or global display artifact is generated.

## Future explicit run and evidence

Reviewed source-contract SHA256:
`544f8d2ca95a2213026b8106d05dd4114d1171033e2c832964a288f3d454f186`.

The following command is **prepared, not run**, for a later explicitly selected
bounded qualification. Its output path must be new and exclusive; the reviewed
SHA must come from this sealed preparation, not a silently refreshed contract.

```bash
PYTHONPATH=src:experiments PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B \
scripts/r6_hr2_p1_qualification.py \
--output /NEW/EXCLUSIVE/HR2_P1_BOUNDED_OUTPUT \
--expected-contract-sha256 544f8d2ca95a2213026b8106d05dd4114d1171033e2c832964a288f3d454f186 \
--execute-manufactured-method-tests
```

There is no arbitrary-mesh/horizon/dataset or production mode. The runner checks
source pins before and after, records actual JUnit, both spatial studies,
temporal convergence, native/B0/query timings, per-face kernel service throughput,
accepted dt histogram, subprocess user/system CPU and sampled process-tree RSS,
logical/allocated bytes/files, stdout/stderr and a new manifest. Kernel service
includes diagnostics/hashing; nested service timings are not summed as exclusive
phases. OS cache is uncontrolled. No artificial resource/thread limits or retry
are introduced, and existing FAIR rules still apply at any future execution.

Only successful real tests and complete required artifacts may emit
`HR2_P1=PASS_MANUFACTURED_SPHERICAL_DIFFUSION_CONSERVATION_AND_CONVERGENCE`.
This preparation emits no such marker. Global cover/material/forcing admission,
conservative mapping, coupled-domain physics, independent crash-tail recovery,
six-grid/2K qualification and scientific/production authority remain open.

New preparation evidence: `ARCANA_WORLD_EVIDENCE/R6/HR2_P1_PREP_20261031_01`.
It includes proposal/P0 plan, pre-authoring source/archive closure, AST-only
receipt, frozen contract, source snapshot, criteria, report and final manifest.
The user's no-commit instruction overrides the ledger's historical same-commit
rule; five handoff files are updated without commit or push.

# ARCANA R6 — HR2-P0 PASS; proposed HR2-P1 first conservative spherical physics gate

**2026-10-31. Provenance:** user-supplied FAIR report `docs/arcana/R6_HR2_P0_FAIR_20261031.md`. This GitHub ledger update is documentation and does NOT independently rerun any FAIR numerical or source audit.

## Closed reported state

`HR2_P0=PASS_GROUNDED_GLOBAL_PHYSICS_AND_ARCHIVAL_READINESS_MAP` (audit only).

- **24 SHA/source-bound provider components** in `ARCANA_WORLD_EVIDENCE/R6/HR2_P0_20261031_01/PROVIDER_MATRIX_FINAL.csv`. All `qualified_on_six_hr1_grids=false`. Components marked runnable are scoped to their stated bounded mesh/role, not globally integrated.
- Available global **T0 only**, not genuine globally evolved states: authorial 180×360 input geography with f32 elevation, categorical supports/UNKNOWN mask; distinct versioned PangaeaV2 f64 surface/thermal/crust fields on 180×360; 64,442 owner-bound PRE_ORBDATA thermal records with 51 fields/row. The 64,442 records are not 64,442 independent native 73-node temporal trajectories, and neither geography dataset is an observed ground-truth world.
- External genuine **ASPECT** historical benchmarks are available on Cartesian 64/256/512-cell problems. Not a verified spherical ARCANA six-grid solver. Build provenance and native restart caveats remain.
- The existing physical operators are limited: `GlobalGrid1Degree` 360×180 T0; R2 region 3×3 un-georeferenced synthetic; thermal/mechanics/Deep local C028/C029. No bidirectionally coupled global geology, hydrology, Deep, ecology or people. Existing regional latent refinement does not add independently qualified subcell physics.
- P0 did **not** import operators, execute a new solver or physical test, install dependencies, obtain datasets, run realistic entropy workload, or change old code. Previous 10k, A0, HR1 evidence and hashes preserved; original FAIR local source remains intentionally dirty.

Historical evidence root `ARCANA_WORLD_EVIDENCE/R6/HR2_P0_20261031_01` includes `PROVIDER_MATRIX_FINAL.csv`, `GLOBAL_T0_PAYLOADS.json`, `INPUT_CATALOG.csv`, `MINIMUM_PHYSICS_AND_VALIDATION.md`, `REALISTIC_ARCHIVE_DESIGN.md`, `JOURNAL_TAIL_DESIGN.md` and manifest+finalization.

## Authorial distinction

Three independently qualified dimensions must not be confused:
1. **Native numerical physics resolution**: the cells/volumes, equations, fluxes and actual internal timesteps at which physics is integrated.
2. **Complete causal history resolution**: which numeric states/events and exact time/space bindings are durably recorded and recoverable.
3. **Visualization/display resolution**: 480/720/HD/2K raster output; high pixel count can arise through visualization/refinement without any new physical information.

The prior HR1 2K×1000Y proved streaming of eight dyadic binary64 counters plus masks, **not planetary dynamics**. Its 104.686× compression and 391.74s run are not physical simulation forecasts.

## Next recommendation: HR2-P1 MANUFACTURED conservative surface-cover diffusion

**Status PROPOSED_NOT_EXECUTED, authorial authorization of implementation / bounded tests pending.** Do not silently treat this as a globally admitted ARCANA geology provider. This stage is a **numerical-method qualification fixture**, using completely declared, manufactured inputs and coefficients with precise units and explicit test-only authority.

Proposed state `h_i >= 0` in meters, finite-volume `V_i = A_i h_i` m³ (optional mass `M_i = rho V_i` only for declared uniform rho). Spatial operator: on a closed sphere, one unique shared edge `(i,j)` with `c_ij = kappa L_ij/d_ij` m²/year; flux of volume `Q_ij = c_ij (h_i-h_j)` m³/year, equal-and-opposite; `V_i(t+dt)=V_i(t)-dt sum_j Q_ij`; conservation over the sphere and nonnegative state under qualified timestep. Declare `kappa` in m²/year as test coefficient, **not geologically calibrated regolith diffusivity**. For explicit stability/positivity use a conservative `dt <= 0.5 min_i A_i / sum_j c_ij` test guard or prove a suitable bound, and keep the actual number of internal physical substeps separate from annual output cadence. Pole cells, small polar areas, zero-length outer faces, dateline periodic seam and point-only contacts need explicit conservative laws; never divide by zero or infer missing face fluxes. No physically sourced cover/rock thickness, density or kappa exists yet at the six target resolutions.

Test-first bounded verification:
1. Independent exact/rational **2×2 local patch** unequal-area oracle with flux signs, zero-gradient, positive states, closed volume, invalid timestep rejection (a local patch is NOT a global 2:1 raster).
2. Genuine spherical **16×8** manufactured field with constant-state invariance and positive degree-one harmonic `h=H0 + eps sin(lat)`, continuum decay `eps exp(-2 kappa t / R²)` under defined coordinates. Prove all-year volume/mass balance, seam and poles without inventing missing sources.
3. Fixed physical-time mesh refinement **16×8 → 32×16 → 64×32 → 128×64 → 256×128**, and time step `dt, dt/2, dt/4`, with area-weighted L1/L2/L∞ errors, conservation residual, positivity, pole/seam fluxes and convergence ratios; predeclare tolerances and target spatial order before running, do not tune thresholds post hoc. A global 256×128 PASS is still not a six-grid 2K scientific admission.
4. Native checkpoint/restart **3Y/10Y direct-vs-split** with full internal numerical state, exact or explicitly justified deterministic comparison, source/mesh/config/forcing hashes, B0 committed prefix, corruption/stale-parent/wrong-source negatives. Test process crash as an independent fault-injection gate only when pair+tail handling is qualified; don't reuse HR1 reference-only array checkpoint as a full native solver checkpoint.
5. Profile per-face numerical throughput, dt/CFL, total substeps, CPU/RSS/disk, checkpoints/query, positive-area geometry and residuals. Model and environmental input provenance must remain explicit; do not label manufactured field as real ARCANA history.

**Exit:** `HR2_P1=PASS_MANUFACTURED_SPHERICAL_DIFFUSION_CONSERVATION_AND_CONVERGENCE` only after real evidence, or `BLOCKED_<reason>`. Even PASS is only solver-method validation. **Later separate gate** must admit actual global cover, density, kappa, boundary/contact, map/source remap, forcing, coupling and uncertainty before 1000Y scientific R6 simulation.

## Parallel, independently gated storage reliability

`HR1_MRES_P1` proposed only: reproduce field entropy/correlation/sparse-change and uneven event loads with identical native precision/schema; compare codec, indexing/query and recoverability vs HR1 dyadic control. Qualify a **linked new segment after an unconfirmed journal tail**, preserving failed root read-only and global ordinal/parent/B0 chain. Do not delete or reuse orphan files, do not silently adopt uncommitted data. Do not rerun all six 1000Y arms without a separately authorized scope.

## Execution governance

Current message reports audit closure; **no new solver implementation, actual benchmark or long execution has been authorized here**. No code changes or numerical tests initiated by this ledger. No git commit/push on FAIR, original data modification, 1000Y/10k/100k physical runs, or promotion to planetary science/production authority. Distinct post-P1 scientific source-admission decision required.

```yaml
HR2_P0: PASS_GROUNDED_GLOBAL_PHYSICS_AND_ARCHIVAL_READINESS_MAP_OPERATOR_REPORTED
HR2_P1_MANUFACTURED_SPHERICAL_PHYSICS: PROPOSED_NOT_EXECUTED
HR1_MRES_P1_REALISTIC_ENTROPY_AND_LINKED_TAIL: PROPOSED_NOT_EXECUTED
GLOBAL_SIX_GRID_PHYSICS_1000Y: BLOCKED_MISSING_SOURCE_ADMITTED_GLOBAL_OPERATOR_AND_INPUTS
WORLD_HISTORY_PRODUCTION_AUTHORIZED: false
GEODYN_2B_ARCANA_FORWARD_AUTHORIZED: false
F2B_SOLVER_EXECUTION_AUTHORIZED: false
ARCANA_SI1_MECHANICS_QUALIFIED: false
```

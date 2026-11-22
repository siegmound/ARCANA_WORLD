# ARCANA R6 — Native-T0 Geological Research Query & short-Δt physical readiness gate

**Date:** 2026-11-22
**Parent FAIR baseline:** main R6 `34bdfd884a418cd54ba41c24ef79b1f51f9d41da`; 275/275 explicit selected R6 regression PASS; authentic source join at `R6G1D-R089-C359` plate 8, normal oceanic T0 crust thickness 6,500 m, specialist ocean crust reference density 2,890 kg/m³, 4 geometry-only child cells.
**Development branch:** `r6/geological-research-query-dt-feasibility-20261122`.
**Decision:** `SOURCE_BOUND_GEOLOGICAL_RESEARCH_QUERY_AND_100_1000_Y_DT_NO_GO_AUDIT_IMPLEMENTED__NO_HISTORY_PRODUCTION`.

## I. User objective / what we are and are not simulating

Keep ARCANA WorldSim computationally economical at global history scale: stable native grid identities, compact multi-physics coarse fields and causal events; request-scoped local geological investigations may later ask which material families are compatible with measurement and paleo-geological context. Do **not** eagerly compute a full global modal mineral and deposit map. Keep future local replay/refinement possible, subject to conservation, physical source/epoch eligibility and provenance.

The user also asks whether, after this task, **Δt from T0** of **100 years or 1,000 years** can be simulated. This is a scientific **feasibility review**, not permission to invent any T1 field. A calendar interval is not a valid global physical solver without qualified initial conditions, constitutive laws, forces, boundary histories, uncertainty and numerical validation.

## II. Source-bound research interface implemented

`src/arcana_worldsim/r6/geological_research_query.py` is a read-only consumer of the existing FAIR-qualified `geological_source_t0_adapter.extract`, `geological_coarse_state._density_screen`, and the governed R6 `hierarchical_refinement`. New test `tests/test_r6_geological_research_query_dt.py`; deterministic empty-sample T0 demonstration `experiments/geological_research_v1/DEMO_T0_READ_ONLY_QUERY.json`.

A research query includes: exact `210.0 Ma` epoch, 1–8 original native cell IDs, an explicit question ID, an **optional** user-declared or synthetic sample (density interval in kg/m3, author/source reference), **optional** declared uncalibrated candidate material density ranges, and optional parent-grid subdivision factor 2–8. The maximum child geometry count is 256. Inputs outside these bounds fail closed. Other epochs, even 209.9999 Ma, fail because no source-backed historical physical state exists at such a time.

The bridge:
1. Authenticates original field and vector NPZ SHA256 (via existing source adapter), exact plate/face support 0..11, source manifest Git blobs, and selected T0 cell state;
2. Returns T0 model/source attributes and **model reference density explicitly not a measured natural rock density**;
3. An optional density sample is labeled `SYNTHETIC_RESEARCH_SAMPLE` or `USER_REPORTED_UNVERIFIED_SAMPLE` (never authenticated observation); returns *interval overlap only* with supplied uncalibrated candidate intervals, with `posterior_probability=null`; no inferred rock, ore presence or resource yield;
4. Optional already implemented on-demand geometry generates child **support**, but no child rock, mass, chemistry, phase fractions, Deep accessibility or physical event;
5. Outputs deterministic query identity, read-only result, and SHA-manifest in a new non-overwriting directory. Nothing is added to World History, HistoryStore, or Canon.

The geometry-only demo contains no sample and no material prior. It is thus impossible to construe the demonstrated reference density as a sample measurement: density screening status must be `NOT_REQUESTED`.

## III. Physical short-Δt gate (100 / 1,000 years)

The command `python -m arcana_worldsim.r6.geological_research_query --repo-root . --dt-gate --output <NEW_DIR>` reads the exact **original** scientific authority audit `docs/arcana/research/B6N8H_T0_T1_PHYSICAL_STATE_MATRIX.json` at Git blob `3d27761f7f0558cf7bba7081a7cc76fad875e204`. These are **older B6N8H gate findings**, so the report explicitly does **not** pretend they are a complete current G2/G3 adjudication. No silent promotion of historical blockers to current positive authority; they currently remain documented blockers in conjunction with D-024.

The original matrix explicitly states:
- `H1_T0_GEOMETRY_AUTHORITY=PARTIAL_AUTHORED_CANDIDATE`
- `H2_T0_THERMAL_STATE_AUTHORITY=BLOCKED`
- `H3_THERMAL_PROPERTY_BINDINGS=PARTIAL_INCOMPLETE`
- `H4_T0_TO_T1_EVOLUTION_AUTHORITY=BLOCKED`
- `H5_T1_GEOMETRY_AVAILABLE=BLOCKED`
- `H6_T1_THERMAL_STATE_AVAILABLE=BLOCKED`
- `H8_UNCERTAINTY_VALIDITY_COMPLETE=BLOCKED`
- `evolution.status=NO_GOVERNED_REDUCED_EVOLUTION_AVAILABLE`.

Moreover the latest R6 G2/G3 audit trail still requires source-authoritative fault gouge and hydration, effective normal pressures, P/T/rate constitutive applicability and mantle/outer-cut/GPE load closure. Until contemporaneous, source-qualified G2/G3 and full/accepted reduced solver conditions actually pass, no physical global T0→T1 production.

**Both requested horizons are evaluated:**

| Requested Δt | Elapsed seconds (Julian years) | Arithmetic age coordinate ONLY | Physical T1 |
|---|---:|---:|---|
| 100 years | 3,155,760,000 | 209.9999 Ma before present | `null` |
| 1,000 years | 31,557,600,000 | 209.999 Ma before present | `null` |

Both receive `NO_GO_PHYSICAL_T0_TO_T1_FOR_100_OR_1000_YEARS`. The age coordinate is *only arithmetic*, not a computed landscape, mineral, mass, temperature or event state. The gate is independent of Δt: decreasing Δt cannot generate missing physics.

The report is a **GO/NO-GO diagnostic**, not a simulation and not a time integrator. It does not select a material, time-step algorithm, diffusion coefficient, or force.

## IV. Research vs physically governed continuation

A legitimate early experiment would be a **separate, explicitly noncanonical, one-column thermal-only model** in a selected parent cell, *after* choosing and validating its vertical T(z) initialization, thermal diffusivity/heat sources, surface/basal boundary conditions and timestep convergence. That cannot constitute natural ARCANA geology, a structural transition, active transport, ancient resources or the physical world-history state. This might evaluate whether a chosen 100-year or 1,000-year numerical increment is stable **in a toy/restricted scientific model**.

A physical full-world T0→T1 evolution needs independent source closure of:
- Physical T0 state, e.g. admissible P/T(z), materials, pore phases, geometry plus uncertainties;
- A governed pre-activation forcing/boundary history (no post-event rift forcing before activation);
- The G2 contact/rock constitutive equations including fault material/hydration and normal stress;
- The G3 mantle/cut forces, GPE and consistent nodal/boundary loads;
- Restartable substepping, mass/energy conservation and temporal/mesh convergence;
- Event/Checkpoint lineage for HistoryStore and optional local refinement, without reconstructing history arbitrarily.

The **next practical scientific decision** should be whether to pursue a *scoped noncanonical thermal-column Δt pilot*, or continue closing full mechanical model gates. Neither is authorized by this report alone.

## V. Validation gate / FAIR instructions

**PENDING** at this engineering development commit. The branch must pass:
- New unit tests in `tests/test_r6_geological_research_query_dt.py`, including real pinned older matrix integrity/no-go, invalid horizons, sample authority claims, non-T0 epochs, source-preserving query and deterministic geometry with synthetic *test-only* source fixture;
- Previous **275** selected FAIR R6 G2/G3+research regression tests plus new cases;
- Real ORIGINAL source-backed single-cell query from the existing B-v2 and plate NPZ sources on FAIR, no sample;
- Real source-pinned `--dt-gate` readback with 100/1,000 years explicitly **NO GO**, zero physical T1 or HistoryStore writes;
- Read-only report manifests and correct non-overwrite evidence paths.

**No FAIR results are asserted before the operator executes these steps.**

```text
R6_DT_REQUESTED_HORIZONS_YEARS=[100,1000]
R6_SOURCE_RESEARCH_QUERY_T0_ONLY=true
R6_NATIVE_CELLS_RESEARCH_MAX=8
R6_CHILD_GEOMETRY_BUDGET=256
R6_T0_MODEL_REFERENCE_DENSITY_NOT_NATURAL_MEASUREMENT=true
R6_REAL_MEASURED_SAMPLE_AUTHORITY=NOT_AUTHENTICATED
R6_CANDIDATE_MATERIAL_POSTERIOR_PROBABILITY=null
R6_RESEARCH_NATURAL_ROCK_ASSIGNMENT=null
R6_100Y_PHYSICAL_T1=null
R6_1000Y_PHYSICAL_T1=null
R6_MECHANICAL_SOLVE_AUTHORIZED=false
R6_WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
R6_D_024=ACTIVE
```

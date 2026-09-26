# R6 Geodynamic Law Authority Matrix

Baseline `main` / `origin/main`: `592b1651b405363373590092e133bd25569d99a5`.

| Domain | Present authority | Status | Narrow blocker |
|---|---|---|---|
| Plate/province identity | Synthetic t0 classes; latent geometry support | Partial | No evolving partition/motion state |
| Spherical plate motion | None bound for R6 | Insufficient | Kinematic law, parameters, integrator, deterministic semantics |
| Rift/breakup | Initial morphology envelope only | Insufficient | Seeded initiation/propagation and event law |
| Collision/orogeny | Designed t0 province/relief only | Insufficient | Convergence, boundary transition, uplift law |
| Coast/land-sea | t0 mask/elevation/datum; A1/R3 references | Partial | R6 vertical motion and sea-level forcing absent |
| Macro-topography | Static synthetic t0 relief | Insufficient | Uplift/subsidence/volcanism response absent |
| Erosion/sedimentation | Drainage-ready support, not a process result | Insufficient | Process laws, boundary conditions, engine suitability |
| Deep → geodynamics | No causal relation established | Unknown | No R6 coupling contract or geodynamic initializer |
| Dated forcing/events | A1/R3 reference/consumer support | Insufficient | No R6 forcing chronology or event schedule |
| Physical restart | Generic checkpoint/orchestrator patterns | Partial | Solver-specific restart schema awaits law/solver |
| Numeric bathymetry | Explicitly unknown at t0 | Not required for initial continental kinematics | Required before bathymetry-dependent ocean/basin/climate processes |

Deep's presence does not establish a mantle/tectonic coupling. A Deep physical initializer is **not shown necessary for an abstract continental-kinematic first phase**; if a future law chooses Deep coupling, both the physical initializer and an explicit Deep-geodynamic contract become prerequisites. This is not a decision that canonical coupling is absent.

Overall: `EXTERNAL_SCIENTIFIC_RESEARCH_REQUIRED`; no provider selected; no replay authorized; no numeric bathymetry materialized.

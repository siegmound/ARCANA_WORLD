# GEODYN-1G closure and GEODYN-2 preparation

Closure date: 2026-10-27
Branch: `r6/multiphysics-integration-20261026`
Windows source HEAD at review: `6ce1022d3b20b53c21b8a30655891d378e4b4032`
GEODYN-1B preparation parent: `48234eccc8b456a3a562ce956c87a96d2bc37603`

## Decision

`GEODYN_1G_FAIR_BLANKENBACH_INDEPENDENT_BENCHMARK_QUALIFIED__ARCANA_FORWARD_NOT_AUTHORIZED`

This closes only the independent, synthetic Blankenbach 1a solver benchmark as reported from FAIR. It does not qualify an ARCANA forward model, ARCANA constitutive properties, or any scientific/canonical output. No further Blankenbach benchmark is planned unless a specific numerical discrepancy or correctness question requires it.

## Evidence and provenance

The results and FAIR paths in this section were supplied by the operator. The original FAIR evidence directories were not imported into the Windows worktree, so Windows did not independently recalculate their file hashes.

| Item | FAIR-reported identity/result |
|---|---|
| ASPECT source | `3.2.0-pre`, commit `30eb77ee5da186137d436dbad35c6cb3cab64b69` |
| Dependencies | deal.II 9.6.0; Trilinos 13.2.0; p4est 2.2.0 |
| Runtime/build | udocker 1.3.17, PRoot P1, MPI rank 1; Blankenbach RELEASE plugin built with CMake and GCC 11.4 inside the container |
| Level 3 evidence | `ARCANA_WORLD_EVIDENCE/R6/GEODYN_1F_BLANKENBACH/20261026T213828Z_case1a_ref3_fixed`; 64 cells, 72 timesteps, 2.13 s; Nu 4.87452475, Vrms 42.849994; natural stop reported as `steady state velocity`; PASS |
| Level 4 evidence | `ARCANA_WORLD_EVIDENCE/R6/GEODYN_1F_BLANKENBACH/20261026T224533Z_case1a_ref4`; 256 cells, 128 timesteps, 9.99 s; Nu 4.88459743, Vrms 42.8656789; natural stop reported as `steady state velocity`; PASS |
| Reference | Nu 4.884409; Vrms 42.864947 |
| Hash checks | Level 4 stdout, stderr and exit-code SHA256 checks reported PASS. The actual digest strings and raw files were not supplied here; no Windows rehash is claimed. |
| Intermediate report | The 7.91 s level-4 report is an intermediate observation from that run, not another execution or a restart. |

### Metric comparison

Errors are calculated here from the reported metric values and references (not independently parsed from FAIR output):

| Level | Nu absolute error | Nu relative error | Vrms absolute error | Vrms relative error |
|---|---:|---:|---:|---:|
| 3 | -0.00988425 | -0.202363% | -0.014953 | -0.034884% |
| 4 | +0.00018843 | +0.003858% | +0.0007319 | +0.001707% |

From level 3 to level 4, reported Nu changes by +0.01007268 and Vrms by +0.0156849. This is evidence that these two reported discretizations move toward the stated reference. Two levels do not establish an asymptotic convergence rate, grid-independent error, restart reproducibility, broad solver robustness, or physical relevance to ARCANA. Level 3/4 cell counts and timings are reported, not independently inspected.

## Scope and unresolved provenance

The test exercised ASPECT's independent Blankenbach case 1a with its separately built benchmark plugin. The documented benchmark is a solver-verification case and its prescribed configuration is not an ARCANA material model or geological initial/boundary condition. See the [ASPECT 3.2.0-pre Blankenbach case](https://aspect-documentation.readthedocs.io/en/latest/user/benchmarks/benchmarks/blankenbach/README.html) and [ASPECT equations overview](https://aspect-documentation.readthedocs.io/en/latest/user/methods/basic-equations/index.html).

Not available for independent Windows verification: original logs/manifests; actual SHA256 strings; binary and container image digests; exact source archive/tree hash; CMake version; plugin/parameter-file/reference-file hashes; per-step nonlinear convergence records; memory and output-volume measurements; scheduler allocation; restart/continuation comparison. These remain `UNKNOWN` unless the corresponding immutable evidence is transferred and verified. The operator-reported PASS is retained with its original FAIR scope and is not expanded to those claims.

Restrictions remain: no Fair run was initiated by this closure; no ASPECT result was mapped to R6; no geologic event or ARCANA history was produced; Blankenbach parameters remain benchmark-only. ShellSet, SI1/Solver, mechanics and WORLD_HISTORY gates remain blocked/false.

## GEODYN-2: bounded positive-time experiment preparation

### Readiness decision

ASPECT is a demonstrated independent solver candidate on FAIR, but an ARCANA positive-time initial/boundary-value problem is not yet specified. Therefore GEODYN-2 is prepared as a **two-stage bounded candidate**, not authorized or ready to run as ARCANA:

1. **GEODYN-2A, time-dependent solver/exchange engineering case:** candidate is the official transient rigid-shear benchmark, using the exact ASPECT 3.2.0-pre source tree/build reported for FAIR and only its matching transient `.prm`, plugin and reference procedure. The published rigid-shear documentation (which identifies an earlier 3.1.0-pre manual) describes separate instantaneous, steady-state and transient variants and a required plugin; it is only a discovery pointer, not authority for 3.2.0-pre inputs. Use the candidate only if the exact 3.2.0-pre source tree contains and documents a compatible transient case ([documentation pointer](https://aspect-documentation.readthedocs.io/en/latest/user/benchmarks/benchmarks/rigid_shear/doc/rigid_shear.html)). The bounded candidate is one unmodified transient variant, one MPI rank, with its upstream mesh and time-stepping configuration. Its exact case path, duration, parameter/plugin hashes and acceptance references must be confirmed from the matching 3.2.0-pre source tree before authorization; they are currently UNKNOWN. This provides a time-positive solver and field-exchange test only. It is not an ARCANA trajectory. Do not use Blankenbach values as ARCANA properties or change the transient reference case to mimic R6.
2. **GEODYN-2B, ARCANA forward window:** remains blocked until source-backed R6 initial fields/supports and a physically authorized temporal forcing/material/boundary-condition closure are supplied. Do not substitute synthetic values into missing canonical fields and then label the result ARCANA.

For a separately authorized GEODYN-2A, require a new external evidence directory and exact source/build/config identity; confirm plugin compatibility; declare one-rank execution, termination criterion and resource/stop policy; capture all output/checkpoints and hash a complete manifest. Check positive model-time progression, finite fields, convergence at each step, stable material IDs, restart against continuous execution where the case supports it, and field-remapping coverage/integral residuals. Do not set an arbitrary run duration or accuracy tolerance in this preparation; take the case's own prescribed transient interval and reference method from the pinned version. If the matching source files or required plugin are absent, stop rather than substitute another version.

No ASPECT, MPI, Fair, ShellSet or geological evolution was run for this preparation. GEODYN-2 requires a separate exact-commit and resource-bounded authorization before execution.

### R6 inputs: available schema versus evidence-backed values

| Field | Current status |
|---|---|
| B4/B5 T0 plate/support identifiers and Euler diagnostic | Contracts and prior source review exist; Euler is instantaneous at 210 Ma only, not a positive-duration velocity law. |
| Reduced thermal/material state | R6 contracts and selected 73-node support fields exist in prior work; they are not a global 2D/3D continuum mesh or complete thermodynamic state. Current provider payload is not revalidated in this task. |
| Material roles, density, heat capacity, conductivity, radiogenic term, temperature and coordinates | Some reduced-state fields are represented for selected supports; role labels do not determine mineralogy or constitutive rheology. No claim that these alone close an ASPECT material model. |
| Spatial domain, global support coverage, exact mesh mapping | `UNKNOWN` for a GEODYN-2 ARCANA window. The synthetic 3x3 surface domain and B5 T0 edge do not supply a validated continuum domain or mesh. |
| Pressure/EOS, composition/mineralogy, temperature-dependent density and rheology | Missing/incomplete for a source-backed ARCANA model. Do not assign dry olivine or infer it from crust/mantle role. |
| Positive-time boundary/forcing history, free-surface or interface evolution, initial stress/load, and complete boundary geometry | `UNKNOWN`; T0 Euler must not be extrapolated. |
| Surface/hydrology/flexure coupling | Existing R6 operators can consume compatible fields diagnostically or in synthetic domains; they do not establish a verified mapping from a global ASPECT mesh. |

### Minimum exchange contract

An ASPECT-to-R6 exchange must be immutable and versioned per time window and include:

- **Identity/time:** run and attempt IDs; source R6 state ID; ASPECT source commit and binary/build identity; start/end model time in seconds plus any separately defined geological-age convention; solver step sequence and checkpoint IDs.
- **Mesh/support:** mesh ID and SHA256; coordinate frame and units; stable node/cell IDs, connectivity, boundary tags, geometric measures; explicit mapping from mesh entities to R6 support/material IDs. No location inferred from array order.
- **Fields:** temperature `K`; velocity `m s^-1`; pressure and stress `Pa`; strain dimensionless; strain rate `s^-1`; material/composition identifiers with declared semantics; displacement as an increment with `m` and reference state. Include component/coordinate conventions and valid/invalid masks.
- **Provenance/configuration:** exact `.prm`, plugin source and binary hashes; ASPECT/deal.II/Trilinos/p4est/compiler/MPI/container identities; initial-condition and boundary/forcing inputs and hashes; solver tolerances and per-step convergence/termination data; environment and command.
- **Remapping:** explicit source/target support IDs, intersection or interpolation weights, coverage, extrapolation policy (default reject), and algorithm version. Report pre/post integral checks for mass/composition and thermal energy where the mapped fields and measures support those quantities; record residuals and missing coverage. Never call a nonconservative point interpolation conservative.
- **Separation of effects:** distinguish solver displacement, surface erosion/deposition, water-load change and any flexural deflection. Apply only increments against a named prior state; do not double-count absolute displacement or infer mass from elevation alone.

### Existing R6 consumers

- `src/arcana_worldsim/r6/regional_geological_evolution.py` and `hydrology_surface_coupling.py` can consume surface elevation, water and material-flux fields on their explicitly defined experimental grid. They need exact area, cell mapping, units and compatible time steps; present synthetic-grid results are not a regional geological mapping.
- `src/arcana_worldsim/r6/geological_surface_microdomain.py` provides a small surface/material state; it can receive mapped displacement or material changes only after support identity and conservation checks.
- `src/arcana_worldsim/r6/fastscapelib_surface_coupling.py` is an optional synthetic SPL surface operator and may be considered for bedrock incision on a verified matched grid. It must not create a second sediment-accounting path or conflate area-drainage forcing with R6 discharge.
- `src/arcana_worldsim/r6/gflex_flexure_adapter.py` supports the prior experimental flexure adapter. It may consume a physically identified load increment only with area, density and justified flexural parameters/edge conditions; current benchmark coefficients do not qualify ARCANA lithosphere.
- `src/arcana_worldsim/r6/deep_geological_physics_pilot.py` remains decoupled: ASPECT temperature, stress, work or material changes do not become Deep energy/accessibility without a separate explicit exchange law.

### Acceptance gates for a later bounded run

Before requesting the separate execution authorization: revalidate exact source/provider input hashes and eligible R6 support; declare whether the run is GEODYN-2A synthetic engineering or GEODYN-2B ARCANA; pin compatible ASPECT source/build and all input hashes; close mesh/support and boundary coverage; state the governing equations and every synthetic/physical parameter with units and authority; bound duration, steps, memory/output and stop policy; use a new immutable external evidence directory. During/after an authorized run, verify natural/declared termination, finite fields, solver convergence, positive model-time progression, checkpoint/restart against continuous execution, required integral balances, remap coverage/residuals, runtime/RSS/output, and complete manifest hashes. A successful synthetic smoke test remains engineering evidence only.

## Sources

- ASPECT 3.2.0-pre Blankenbach 1a documentation: https://aspect-documentation.readthedocs.io/en/latest/user/benchmarks/benchmarks/blankenbach/README.html
- ASPECT transient rigid-shear benchmark documentation (use only after matching files are verified against the pinned source): https://aspect-documentation.readthedocs.io/en/latest/user/benchmarks/benchmarks/rigid_shear/doc/rigid_shear.html
- ASPECT governing equations overview: https://aspect-documentation.readthedocs.io/en/latest/user/methods/basic-equations/index.html

## Preserved gates

`BLOCKED_F2AV_QUALIFICATION`
`OPERATOR_CLASS_UNVERIFIED`
`THRESHOLD_UNJUSTIFIED`
`RESOURCE_2GB_SCOPE_UNRESOLVED`
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`
`ARCANA_SI1_MECHANICS_QUALIFIED=false`
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`
`INT3_ENG10K_EXECUTION_AUTHORIZED=false`

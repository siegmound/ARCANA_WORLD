# R6 Existing Capability Reconciliation and Core Interface Specification

**Status:** Repository-grounded design specification; not implementation or execution authorization
**Repository baseline inspected:** `main` at `592b1651b405363373590092e133bd25569d99a5` (equal to `origin/main` at inspection)
**Purpose:** Bridge the frozen R6 world-history architecture to a minimal, evidence-led bootstrap/core implementation.

## Executive finding

R6 is not a greenfield simulator. ARCANA already contains substantial scientific machinery, sealed or adjudicated stage outputs, domain contracts, provider inspections, external-engine wrappers, restart/replay tooling, and authority/provenance infrastructure. Reuse is real but bounded: much of it is stage-specific, diagnostic, cohort-limited, or tied to R5 execution context. R6 should reuse eligible code, contracts, validators, and provider bindings behind new stable interfaces; it must not make the R5 world state a runtime prerequisite.

The strongest near-term reuse candidates are (1) authority/provenance and manifest builders, (2) the R3.14 climate provider hierarchy and P7S climate inspection/binding components after separation of generic primitives from Krapp/Beyer-specific policy, (3) R5.17-B6 seasonal hydrology replay and its shoreline/land-mask validation after an R6 input adapter, and (4) selected R4 engine wrappers for genuinely integrated engines. The largest missing surfaces are a persistent global `WORLD_HISTORY(x,y,t)` store, generic cross-domain temporal/checkpoint scheduling, causal and feedback orchestration, stable query/search/refinement services, and scientifically authorized complete histories for multiple domains.

This reconciliation does not certify every historical artifact as canonical R6 input. `SIMULATION_RESULTS/MANIFEST.csv` records custody/status fields, but numerous rows remain pending repository adjudication or content inspection. `SIMULATION_RESULTS/SEMANTIC_CATALOG.md` explicitly documents only a limited subset and states that catalog presence is not scientific authority. Current state and authority register are consulted as indexes to evidence, not substitutes for the underlying contracts and outputs.

## Source boundary and evidence rules

Inspected baseline documents include:

- [`ARCANA_R6_CANONICAL_CLEAN_REPLAY_OBJECTIVE.md`](ARCANA_R6_CANONICAL_CLEAN_REPLAY_OBJECTIVE.md)
- [`R6_WORLD_HISTORY_ARCHITECTURE_FREEZE.md`](R6_WORLD_HISTORY_ARCHITECTURE_FREEZE.md)
- `ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md`
- `ARCANA_WORLD_CURRENT_STATE.md`
- `ARCANA_WORLDSIM_SCIENTIFIC_AUTHORITY_REGISTER.json/.md`
- `ARCANA_EXECUTION_REFERENCE_INDEX.json/.md`
- `SCIENTIFIC_ENGINE_SUITABILITY_GATE.md`
- `R5_15_R5_17_RECOVERY_LEDGER.md`
- `SIMULATION_RESULTS/MANIFEST.csv`, `SIMULATION_RESULTS/MANIFEST.json`, and `SIMULATION_RESULTS/SEMANTIC_CATALOG.md`
- relevant R3.10, R3.14, R3.18, R3.20, R3.21, R3.23, R3.27–R3.28, R3.34–R3.39, R4.0, R5.17-B6/B7, P7Q/HRAB, P7S, and BIOME4 contracts/results named below.

Evidence is classified as one of: direct governed authority, bounded execution evidence, provider metadata/binding, diagnostic/reference implementation, or unresolved/pending. A seal proves its stated scope, not global applicability. Historical chat summaries and filenames alone do not establish authority. The recovery ledger warns that R3.34–R3.39 are sealed legacy authorities and are not an R5 runtime dependency; its snapshot predates later R5.16/R5.17 work, so it is useful for provenance but not the latest state ledger.

The scientific authority register has 33 domain entries and a builder at `tools/build_arcana_worldsim_scientific_authority_register.py`. Its checked-in `authority_basis_head` is `9577f133…`, older than the inspected repository HEAD; treat it as a prior governed register snapshot pending a fresh, separately authorized rebuild/reconciliation, not as evidence that its basis equals current HEAD. The execution reference index is navigational evidence. Its protected staged blobs were not modified. The register/index do not promote an artifact merely because it is listed.

The provider decision order remains the repository policy in `SCIENTIFIC_ENGINE_SUITABILITY_GATE.md`: reuse canonical ARCANA evidence first, then an already validated specialist, audit a new specialist only if needed, and use minimum custom implementation last. First ask whether replay/state material already provides the required quantity; distinguish a provider from an engine and an engine output from ARCANA-owned state.

## A. Capability archaeology: R3–R5 scientific chain

The original development world produced useful laws, replay methods, testable contracts, provider knowledge, and bounded scientific results. The old world result itself is not R6's target. `R5 WORLD STATE != mandatory R6 target`; R3–R5 machinery is a candidate source of reusable capability subject to fresh R6 authority binding.

### Table 1 — R3–R5 scientific capability inventory

| Capability / domain | Concrete evidence and implementation | Inputs → outputs / demonstrated purpose | Scientific and implementation status | Authority, reproducibility, R6 reuse, limitation |
|---|---|---|---|---|
| Initial/physical world, geography | `references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz`; `src/arcana_worldsim/late_cenozoic/paleogeography.py`; R3.10 CHA1 bridge contract | 210–0 Ma land-mask and plate-code frames; paleogeographic endpoints/events; spatial state on the declared grid | Existing legacy world/geography and replay support; endpoint/derived transition organization exists | Reuse contract/reference and selected physical code only after canonical-initial-state adjudication. A1 is not a verified plate-rotation/topology model and does not supply lithology, crustal province, parent material, or soil. |
| Grid and spatial semantics | R3 manifests/contracts, R3.27–28 grids (90×180), R4 static selector/extractor validators, `src/arcana_worldsim/state_query/` | Cell IDs, masks, grids, exact selectors and bounded spatial replays | Mature in specific pipelines; no single universal domain-aware grid registry demonstrated | Reuse validators with an R6 spatial-support contract. Never describe resampled coarse inputs as native high resolution. |
| CHA-1 physical/biological event bridge | `CANONICAL_CHA1_HIGH_RES_EVENT_BRIDGE_CONTRACT_v0_6D1_R3_10.md`; `local_runs/v0_6D1_R3_10/*`; `R3_10_FULL_CHA1_EVIDENCE_AUDIT.md` | Event timing/forcing and bounded high-resolution physical and food-web diagnostics | Concrete event bridge and evidence; event effects remain specific to its contract | Reuse event-contract concepts and validators. R6 must bind canonical event timing, footprint, forcing, effects, uncertainty, and provenance independently; a legacy run is not an R6 initial state. |
| Climate provider/replay | `CANONICAL_LATE_CENOZOIC_PROVIDER_BINDING_ADAPTIVE_CLOCK_RESTART_CONTRACT_v0_6D1_R3_14.md`; R3.14 seals/bindings; `R5_17_B5_*PALEOCLIMATE*`; `R5_17_B6_*PALEOCLIMATE*` | Climate providers, time mapping, adaptive clock/restart, semantic inspection | Significant machinery exists; provider-level and stage-level, not globally complete R6 forcing | Reuse provider hierarchy/contracts, exact inspectors and validators behind provider adapters. Provider license, units, variables, time coordinate, masks, grid, and applicability remain distinct gates. |
| Recent exposure/transport integral | `CANONICAL_RECENT_H0_EXPOSURE_COMPLETION_TRANSPORT_PHASE_READINESS_CONTRACT_v0_6D1_R3_18.md`; `outputs/v0_6D1_R3_18/R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz` | Integrated exposure/transport phases over 125 ka–0, not a pointwise climate history | Sealed, scoped derived exposure evidence | Reuse as a derived diagnostic or constraint only where its declared semantics fit; not raw monthly climate or general historical climate. |
| CHA-2 Younger Dryas hazard | `CANONICAL_CHA2_YD_CLASS_HYDROLOGICAL_HAZARD_CONTRACT_v0_6D1_R3_20.md`; `local_runs/v0_6D1_R3_20/R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz` | 15–11 ka 50-year diagnostic hazard ranking | Bounded event-specific evidence | Reuse event/hazard contract pattern. Not flood depth, water volume, global hydrology, or global CHA-2 history. |
| Present lineages, components, historical closure | `R3_21_H0_PRESENT_LINEAGE_REGISTRY_CONTRACT.md`; `outputs/v0_6D1_R3_21/R3_21_PRESENT_LINEAGE_REGISTRY.json`, `R3_21_PRESENT_COMPONENT_REGISTRY.json`, `R3_21_HISTORICAL_LINEAGE_CLOSURE.json` | Lineage/component identities and governed temporal closure | Sealed identity/closure authority; 134 present species and 295 components in the related A3 census | Reuse identity and temporal-existence rules; not abundance or full spatial range history. |
| Functional/phenotype prior | `R3_23_FUNCTIONAL_ENSEMBLE_CONTRACT.md`; `outputs/v0_6D1_R3_23/R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz`, comparative calibration authority | Functional/phenotype ensembles and ancestral priors | Governed comparative-prior/latent macroevolution ensemble, not observed anatomy or direct measured ecological function | Reuse with epistemic labels and domain adapter; never promote prior draws to observations. |
| Hominin macro replay | `R3_27_HOMININ_MACRO_REPLAY_CONTRACT.md`; output macro replay trajectories/authority/checkpoints | Candidate human macro trajectories ending at 200 ka checkpoint | Bounded scenario/replay authority | Reference/diagnostic and selected contract reuse only; not canonical R6 population initializer. |
| High-resolution human replay | `R3_28_HIGH_RESOLUTION_200KA_TO_0_CONTRACT.md`; `R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz`; authority and config `configs/world1_r328_high_resolution_200ka_to_0_v0_6D1_R3_28.json` | 200–0 ka, 90×180, multi-resolution human replay; two cohorts and common-forcing ensemble | Bounded human-candidate replay with governed time clock; not parent-material state or material transition physics | Reuse temporal-clock/restart patterns only after contract verification. Time resolution does not confer state authority or spatial resolution. |
| Producer/domestication and human-support groundwork | `R3_34_PRODUCER_DOMESTICATION_CONTRACT.md` through `R3_39_SYMBOLIC_MEMORY_LANGUAGE_IDENTITY_CONTRACT.md`; sealed outputs under `SIMULATION_RESULTS/91_SUPPORT_SCIENTIFIC_REPLAY` | Producer taxa, genetics/selection, domestication, managed-forager economy, exchange, symbolic memory | Multiple sealed legacy stage results; coupled chain remains stage-specific and not integrated R6 macrohistory | Reuse selected models/contracts as bounded adapters/reference. No claim of complete human society, trade, polity, or resource history. |
| Scientific authority and reference infrastructure | `ARCANA_WORLDSIM_SCIENTIFIC_AUTHORITY_REGISTER.*`; `tools/build_arcana_worldsim_scientific_authority_register.py`; `ARCANA_EXECUTION_REFERENCE_INDEX.*` | Domain authority registry and artifact/reference discovery | Implemented governance infrastructure; register basis is older than inspected HEAD | Reuse schemas/builders and path-scoped checks after controlled basis refresh. Index is navigation, not authority. |

### Table 2 — R3/R4/R5 integration infrastructure and maturity

| Capability | Concrete evidence | What is reusable | What it does not yet provide for R6 |
|---|---|---|---|
| Replay/checkpoint/restart | R3.8 checkpoints; R3.11–R3.20 dual clocks/restart contracts; R3.14 adaptive clock; R3.27–28 replay checkpoints; R4 runtime contracts | Input identity, bounded checkpoint, restart, runtime capture patterns | A single schema-compatible checkpoint manager spanning every R6 domain and persistent history is not evidenced. |
| Orchestration and engine registry | `R4_0_MULTI_ENGINE_ORCHESTRATOR_CONTRACT.md`; `src/arcana_worldsim/scientific_engines/r40_multi_engine_orchestrator.py`; R4.2–R4.55 | Governed job plans, registry, runtime validation, evidence capture, seeds, specific preflights | Not a general causal-cone planner, global interval scheduler, or feedback-cycle coordinator for R6. |
| State querying | `src/arcana_worldsim/state_query/r50_query.py` and R5.1–R5.9 query modules | Selective nested replay/query patterns for bounded legacy domains | Not a persistent global history database, temporal search index, or cross-domain explanation engine. |
| Manifest and semantic catalog | `SIMULATION_RESULTS/MANIFEST.csv/.json`, `SIMULATION_RESULTS/SEMANTIC_CATALOG.md` | Custody/hash/status inventory; limited semantic summaries | Many inventory rows have pending repository/content status; only a few payloads are semantically documented. Catalog presence is not authority. |
| Deterministic seed / ensemble evidence | R3.23/R3.27/R3.28 outputs; R4 job configurations and evidence capture | Per-run seed/config lineage and scoped ensemble products | No cross-domain, versioned R6 ensemble family and uncertainty propagation contract is demonstrated. |
| Schema/hash/provenance/fail-closed gates | Stage contracts, seals, manifests, exact-source binders, tests, hash ledgers | Reuse validation idioms and bounded utilities | No unified provenance graph or global authority-aware history schema has been shown. |

## B. External scientific engines actually exercised

An engine is included because repository evidence records integration or bounded execution, not merely installation/provisioning.

### Table 3 — External engine inventory

| Engine | Demonstrated use / concrete evidence | Integration classification | R6 use and boundary |
|---|---|---|---|
| NEMO 2.4.2 | R3.6B/3.6D bounded population-genetics/QTL experiments; R3.7A–C selection/oracle runs; wrappers such as `nemo242_r36d_R2_QFREQ_FINALIZATION_FIX.py`, `benchmarks/r54/run_nemo_r54_suite.sh`, R4/R5 configs | Genuinely integrated and executed for bounded population-genetic questions | Preserve wrapper/protocol and validated readouts where scientifically matched. Not a whole-population, ecology, or world simulator. |
| Geonomics | R4.32–R4.50 J14/J18 spatial-genomics jobs; native parameter mapping, exact state injection, revalidation, readout extraction contracts | Deeply integrated for a specific spatial-genomics workflow | Reuse engine boundary, exact-state binding, and validators. New R6 domain adapter and causal semantics required. |
| CDMetaPOP | R4.7–R4.13 bounded demogenetic/dispersal and forcing-parity experiments; `benchmarks/r47`, `r48`, `r49`, `r53`, `r454` | Executed/evaluated, with comparability downgraded in later adjudication | Candidate specialized demographic/dispersal adapter; not canonical global history without fresh fit/authority. |
| SLiM + tskit/msprime/pyslim | R3/R4/R5 genetics and ancestry/admixture/selection benchmark suites; `benchmarks/r56/run_slim_r56_suite.sh`, `benchmarks/r56/slim_collect_r56.py`, R4.54 evidence | Genuine bounded execution/analysis toolchain | Reuse experiment wrappers and ancestry readout adapters for matching genetics questions; not ecological range or human-history engine. |
| RangeShiftR | `benchmarks/r52/*rangeshiftr*`, `benchmarks/r454/rangeshiftr_r454.R` | Benchmarked/source-bound and suitability evaluated; no canonical production R6 adapter evidenced | Do not invoke by availability. Consider only if its domain matches a governed range-dynamics need and canonical ARCANA evidence is insufficient. |
| Madingley | R4 benchmark script `benchmarks/r454/madingley_r454.R`; later P7 runtime/input audit for MadingleyR 1.0.6 / C++ 2.02 | Runtime/benchmark and input-authority exploration; production fauna run not authorized | No ARCANA species ontology, historical abundance authority, or production fauna history. Keep behind a future scoped adapter. |
| BIOME4 | P7R source/runtime binding and `R6_BIOME4_PRODUCTION_INPUT_CONTRACT.json/.md` | Runtime ready, contract frozen with provider gaps; production execution not authorized | External ecological opportunity solver only. ARCANA owns vegetation/flora semantics and must normalize outputs. |

## C. P7Q / HRAB reconciliation

P7Q's PRE1–PRE5* sequence produced external-authority audits, temporal-method and schema contracts, provider recovery/binding, static state, classifier/readiness evidence, and the 0 ka endpoint. PRE5I's bounded classifier records zero assigned bedrock, residual-regolith, and saprolite states, with explicit non-authorization for residual regolith and saprolite. PRE5N's static endpoint is eligible as an endpoint constraint for the sparse bridge, not as a universal initialization state.

HRAB artifacts include `R5_17_B7_A3F2_P7Q_HRAB_ARCHITECTURE_CONTRACT.json`, `...TEMPORAL_CLOCK_MANIFEST.json`, `...DRIVER_AUTHORITY_MATRIX.json`, `...CELL_RULE_INDEX_MANIFEST.json`, `...INTERVAL_CHECKPOINT_CONTRACT.json`, `...VALIDATION.json`, and `...ADJUDICATION.json`, plus temporal closure/binding and AA-aware GUM artifacts. The governing conclusion is:

> `SPARSE_TEMPORAL_PARENT_MATERIAL_CONSTRAINT_AUTHORITY`, not `FULL_CONTINUOUS_PARENT_MATERIAL_HISTORY`.

The latest HRAB authority says core ready, full temporal parent state false/pending driver authority; GUM alluvial/colluvial candidate cells = 1,907, positively authorized at 200 ka = 0, authorized forward families = `[]`, authorized forward cells = 0, persistence-authorized families = `[]`. HRAB preserves UNKNOWN. It forbids categorical interpolation, present-to-past inversion/backcast, unsupported persistence, fabricated continuity, and spatial resampling. Hard anchors are validation/constraint boundaries, not license to fill categorical state.

### Table 4 — P7Q reusable capability and ceiling

| P7 artifact family | R6 reuse mode | Reusable content | Scientific ceiling / missing authority |
|---|---|---|---|
| PRE1–PRE3 adjudication/method | `REUSE_CONTRACT_ONLY` | External source suitability, comparison method, explicit no-generic-interpolation rule | Does not create missing sources or material histories. |
| PRE4 temporal state schema and rule registry | `REUSE_WITH_R6_ADAPTER` | Temporal applicability, formation/occurrence intervals, event brackets, conflict and UNKNOWN concepts | R6 needs a generic schema/version and authoritative bindings; R5/P7 row semantics do not automatically cover all materials/domains. |
| PRE5 provider acquisitions / exact bindings | `REUSE_PROVIDER_ONLY` / adapter | Hash-pinned source identities and bounded validation logic | Scope and license remain provider/product-specific; no R5 world state is R6 input. |
| PRE5C/PRE5G/PRE5I static material pipeline | `REUSE_CONTRACT_ONLY` / `REUSE_VALIDATOR_ONLY` | Source/grid/metadata checks and bounded 0 ka static classification contracts | Current assignments include zeros; not physical soil, full geology, or historical persistence. |
| PRE5L/M/N eligibility and endpoint | `REUSE_CONTRACT_ONLY` | Cell-level eligibility/crosswalk evidence and static endpoint payload identity | Not temporal state; no abundance/continuous history or blanket endpoint propagation. |
| HRAB sparse anchor bridge | `REUSE_WITH_R6_ADAPTER` | Hard anchors, sparse cell rules, interval checkpoints, endpoint constraint, explicit UNKNOWN, conflict handling, no fake upsampling | It authorizes architecture/constraints, not forward evolution. No driver family presently authorizes full interval evolution. |
| AA-aware temporal provider recovery | `REUSE_PROVIDER_ONLY` / `REUSE_CONTRACT_ONLY` | Branch-specific provider and age/occurrence/applicability evidence | Candidate presence or a provider route is not evidence of a positive transition or persistence authorization. |

Generic R6 temporal infrastructure should take the abstract mechanisms—versioned temporal rule objects, hard-anchor/event registries, interval checkpoint descriptors, support masks, sparse state references, conflict/UNKNOWN representation, endpoint validation, deterministic clock binding, and no-backcast/no-interpolation guards. It should not copy PRE micro-gates into the R6 stage graph or assume HRAB's material-specific rule inventory is universally complete.

## D. P7S / physical soil and hydraulic capability

P7S contains useful endpoint physics, data-provider evaluation, model plumbing, and negative historical-applicability findings. These are intentionally distinct.

### Table 5 — P7S capability inventory

| Capability | Repository evidence | Status and R6 reuse mode | Limitation that must remain visible |
|---|---|---|---|
| SoilGrids present endpoint | P7S physical-soil/provider contracts and targeted profile bindings; bounded 65-cell cohort | Present-day provider endpoint / `REUSE_PROVIDER_ONLY` | Not an R6 canonical initial condition or historical soil authority. |
| Six-layer profile geometry | P7S contract and model proof: `dz_cm=[5,10,15,30,40,100]` | Bounded derivation logic / `REUSE_WITH_R6_ADAPTER` | Profile cohort and source semantics remain bounded; not full-grid coverage. |
| WHC and Ksat derivation | Top/bottom WHC depth aggregation and depth-weighted Ksat aggregation; dimensional contract | Proven endpoint calculations for their tested profiles / `REUSE_CONTRACT_ONLY` + validator | Do not reinterpret as historical transfer or global soil map. |
| Rosetta 3.0.2 code 3 | `R5_17_B7_A3F2_P7S_RUN_MINIMAL_SOIL_MODEL_PROOF.py`, `...MODEL_PROOF_RESULT.json`, adjudication | Executed for 390 complete cell-depth profiles from a 65-cell 0 ka SoilGrids cohort; endpoint-only physics | `HISTORICAL_KSAT_APPLICABILITY_PROVEN__TRANSFER_MODEL_UNRESOLVED`; historical soil state false, no nonzero-age Ksat; no GUM-to-texture mapping. |
| Soil provider comparison | P7S adjudication: SoilGrids 2.0; HWSD independent coarse cross-check/rootable depth; HiHydroSoil derived from SoilGrids | Provider/derivative relationships useful for authority graph | HiHydroSoil is not independent confirmation; coarse HWSD is not spatially equivalent. |
| Historical applicability | P7S driver recovery and temporal authority matrix | Historical transfer remains blocked/unknown | 65-cell endpoint proof does not identify historical soil or justify a 200–0 ka initializer. |
| Climate-conditioned hydraulic diagnostics | P7S climate binding/model proof and BIOME4 sensitivity artifacts | Bounded diagnostic methodology | No verified global/historical climate forcing or general transfer authority; no production BIOME4 run. |

Thus, **proven endpoint physics** means the tested derivation and consumer calculations at the bounded 0 ka cohort. **Unproven historical transfer** means the process/source rules and physical soil trajectories needed to extend those values to nonzero ages. P7S's existing adjudication is not reopened here.

## E. Historical-climate tooling inventory

The repository contains a meaningful climate acquisition/inspection/binding toolkit. The component boundary—not wholesale copying of a P7S runner—is the reuse objective.

### Table 6 — Historical climate tools and reuse classification

| Actual file / artifact | Function evidenced by name, code, or associated result | R6 classification |
|---|---|---|
| `R5_17_B5_LOCATE_AND_INSPECT_SEALED_PALEOCLIMATE_INPUTS.py` | Find candidate sealed paleoclimate inputs and inspect bounded metadata | Recovery/discovery utility; potentially reusable after genericization |
| `R5_17_B5_INSPECT_SEALED_PALEOCLIMATE_INPUTS.py` | Inspect selected sealed payload semantics | Inspection pattern; P7-era bounded utility |
| `R5_17_B5_SEALED_PALEOCLIMATE_PAYLOAD_INSPECTION_SUMMARY.json` | Inspection output/summary | Evidence only, not reusable runtime code |
| `R5_17_B6_LOCATE_AND_INSPECT_PALEOCLIMATE_SEMANTICS.py` | Locate and inspect paleoclimate semantics | Discovery utility; genericizable but stage-bound |
| `R5_17_B6_INSPECT_PALEOCLIMATE_SEMANTICS.py` | Semantic fields/coordinates/units/coverage inspection | Strong validator/reference utility; separate generic inspectors from policy |
| `R5_17_B6_PALEOCLIMATE_SEMANTIC_EVIDENCE.json` | Inspection findings | Evidence record; not climate state |
| `R5_17_B7_A3F2_P7S_ACQUIRE_CANONICAL_HISTORICAL_CLIMATE.py` | Canonical climate acquisition with bounded HTTP range, TLS/OpenSSL/runtime and cache handling, provider preflight | Provider-specific/P7S-only acquisition runner; extract safe transport/cache primitives only after review |
| `R5_17_B7_A3F2_P7S_TARGETED_PROVIDER_ACQUISITION_MANIFEST.json` | Acquisition/source manifest | Provider binding/provenance example |
| `R5_17_B7_A3F2_P7S_BIND_LOCAL_CANONICAL_CLIMATE_PROOF.py` | Bind local canonical cache to bounded historical-climate proof | P7S-specific adapter/proof runner; not generic history service |
| `R5_17_B7_A3F2_P7S_HISTORICAL_CLIMATE_BINDING_PROOF.json` | Krapp/Beyer bounded climate-binding evidence | Evidence, cohort-limited |
| `R5_17_B7_A3F2_P7S_HISTORICAL_CLIMATE_BINDING_ADJUDICATION.json/.md` | Applicability and status adjudication | Governance/evidence template; does not imply global binding |
| `R5_17_B7_A3F2_P7S_HISTORICAL_DRIVER_AUTHORITY_MATRIX.json` | Climate/soil driver status and support matrix | Reusable schema idea; P7S values remain scoped |
| `R5_17_B7_A3F2_P7S_HISTORICAL_DRIVER_RECOVERY_ADJUDICATION.json/.md` | Recovery result and unresolved driver decision | Current evidence of unresolved climate/temporal applicability; not a provider |
| `R5_17_B6_D2R_RECOVER_SEASONAL_CLIMATE_BASELINE.py` and `R5_17_B6_D2R_*BASELINE*` | Baseline recovery and seasonal baseline binding | R5-specific recovery; algorithm/contract may inform adapter after exact input review |
| `R5_17_B6_D2D1_RESOLVE_EXACT_SEASONAL_GENERATOR_RUNTIME_BINDING.py` | Exact seasonal-generator runtime identity | Reusable runtime-binding pattern, not climate value authority |
| `R5_17_B6_D2D3_VALIDATE_SERIALIZED_MARGIN_REPLAY_AND_RECONSTRUCT_I.py`; `D2D4_FLOAT32_ULP_EQUIVALENCE...py`; `D2D5_FULL_IN_MEMORY_F_CHAIN_REPLAY...py` | Serialized/in-memory replay, float32 ULP reconciliation, reconstruction | Strong bounded replay-validation/reference tools; do not generalize tolerances without contract |
| `R5_17_B6_D2C1_ADJUDICATE_SHORELINE_LAND_MASK_ADAPTER.py` | Shoreline/land-mask compatibility adjudication | Reusable adapter pattern for spatial applicability; not a universal shoreline law |
| R3.14 provider binding/adaptive-clock/restart contracts and R3.14 seals | Legacy climate hierarchy and bounded time/provider binding | Contract/reference implementation; exact source authority needs R6 binding |

The proved P7S comparison used a bounded 65-cell cohort and tested anchor/overlap and 0 ka comparisons plus absolute-vs-anomaly/seasonality semantics. It does not establish global climate coverage. Krapp provides annual temperature in the inspected product and lacks a sunshine series; Beyer supplies monthly climate and a cloud variable whose exact semantics/units still require binding. The current R6 BIOME4 input contract records missing monthly temperature at 200/125 ka, unresolved Krapp sunshine, unbound Beyer cloud semantics/units, unknown full-grid elevation, historical soil unknown except the bounded 0 ka cohort, and unverified full-grid compatibility. Historical climate is therefore not globally bound.

Generic enough to extract: bounded hash-verified acquisition mechanics, safe cache reuse checks, generic NetCDF/HDF5 metadata/coordinate inspectors, generic time/space applicability masks, exact unit/variable validation, and replay comparison primitives. Provider-specific: Krapp/Beyer variable and product mapping, absolute/anomaly adjudication, age-specific availability, cloud/sunshine mapping, source URLs/licensing, and provider-specific masks. Stage-specific: the P7S 65-cell cohort, its decision thresholds, and acquisition run ledger. Any extraction requires tests against the existing scripts and no change to their scientific semantics.

## F. BIOME4 capability boundary

`R6_BIOME4_PRODUCTION_INPUT_CONTRACT.json/.md` records `BIOME4_CONTRACT_FROZEN__INPUT_PROVIDER_GAPS_REMAIN`. P7R bound source/runtime (BIOME4 v4.2b2, pinned source commit `4ad9dff…`, GPL-3.0, locally built executable); a source-conformant synthetic smoke is non-scientific runtime evidence only. Production execution remains unauthorized.

The contract requires monthly `tmp[12]` in °C and `pre[12]` in mm/month, plus `sun[12]` in percent or a separately authorized cloud mapping; CO₂ is bound at the 12 governance anchors. Elevation remains UNKNOWN at required full-grid support and historical soil UNKNOWN outside the bounded 0 ka cohort. Krapp annual temperature does not fill monthly temperatures; provider presence does not satisfy availability/semantics. Existing top/bottom soil aggregation and WHC/Ksat dimensional contracts are candidate adapter logic only where source layers and units validate.

**R6 boundary:** ARCANA owns flora/vegetation state, taxonomy, persistence, spatial meaning, authority, and uncertainty. The BIOME4 adapter accepts a validated per-checkpoint climate/CO₂/elevation/soil bundle, records exact runtime/configuration, executes only when authorized, normalizes raw output, validates units/ranges/support, and returns a bounded ecological solver result. BIOME4 output is not `FLORA_HISTORY` and cannot independently define plant lineages or historical occurrence.

## G. Fauna and ecological capability

R3.21 owns present lineage/component identity and historical lineage closure; R3.23 provides functional/phenotype priors/ensembles; R3.27–28 provide bounded human replay, not fauna state. R5.17-B7 includes plant trophic materialization, wild-fauna authority census, and ecological/resource support contracts, but the A3/HRAB/P7 history has explicitly left exact historical wild-fauna ranges and historical abundance unmaterialized. Madingley runtime identity/input checks did not authorize a production scientific run. RangeShiftR has been benchmarked but was not selected merely by installation. Marine/aquatic biological resource support remains not materialized absent a separately governed biological authority.

| Concept | Exists | R6 interpretation |
|---|---|---|
| Species identity / component continuity | R3.21 present registries and historical closure | Reusable identity authority, not abundance. |
| Ecological functional state | R3.23 comparative ensemble/prior | Reusable as explicitly uncertain prior, not observed phenotype. |
| Range/dispersal | Historical candidate/replay machinery and provider evaluations | Some bounded mechanisms; no complete wild-fauna historical occupancy authority. |
| Population state/abundance | R3/R4 experiments and human replay | Engine outputs/scenarios do not constitute governed wild-fauna abundance history. |
| Trophic/resource state | R5.17 plant and natural-resource support work | Partial material support; do not turn into K or calories without separate contract. |
| Marine/freshwater ecology | Some physical/hydrology foundations; biological authority unresolved | Separate interfaces and aquatic connectivity requirements; no terrestrial proxy promotion. |

## H. Human support, macrohistory, and Deep

`ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md` makes population emergent and treats effective support as downstream of resource, technology, access, trade, infrastructure, Deep, and hazards. The R5.17 human-support bridge and B6/B7 work supply real contracts and bounded inputs, not the complete human-history engine.

### Table 7 — Human-support/Deep capability reconciliation

| Domain | Existing evidence/capability | Status | Missing for R6 |
|---|---|---|---|
| Freshwater support | R5.17 B6 canonical hydrology replay; D1 contract, D2/D2R baseline/seasonal recovery, D2D runtime and exact replay/reconstruction, D3 canonical paleo-hydrology replay, D4 freshwater access/reliability | Strongest recent physical-support chain; direct/derived authority scoped to declared replay | R6 inputs/initial state, generic time/grid adapter, persisted history and cross-domain checkpoint contract. |
| Plant/food support | R5.17 B7 A1 natural food-support bindings, A3 plant trophic materialization and wild-fauna census; earlier R3.34–39 food/producer experiments | Partial governed resource/support concepts, plus legacy bounded experiments | Complete independent natural-resource and food history, uncertainty, access, and R6 causal integration. |
| Population support / K | Macrohistory objective and bridge contract define downstream derived semantics | Contractual concept; not completed global history | First-class resource/access state and human-history laws; do not materialize K as substitute for resources. |
| Connectivity/migration | Geonomics, CDMetaPOP, R3.27–28 and R4 spatial replay | Bounded biological/human movement mechanisms | General world connectivity/accessibility state and coupled R6 migration rules. |
| Settlement/trade/technology | R3.34–39 producer/forager/exchange/cultural lineage artifacts | Bounded sealed legacy stage capabilities | Unified causal, spatially queryable human history; not all polities/infrastructure/war. |
| War/polity/conflict | Partial cultural/macro replay semantics may be present in old stages | Not evidenced as a complete governed R6 domain | Explicit event/state authority, process laws, uncertainty, persistence and queries. |
| Deep physical/background | Some early physical/Deep-related variables and R3.7 Deep-time jobs/exposure evidence; R4.0 contract says biological Deep coupling OFF | Partial/reference capability, not full R6 Deep history | Need inspect exact state semantics and establish canonical field, units, temporal/spatial support. |
| Deep intensity/accessibility/stability/hazard/resource value | Architecture freeze specifies desired outputs; scattered/derived legacy signals may exist | Mixed planned/partial; no complete authoritative coupled state demonstrated | Domain laws, values, coupling authority and history. |
| Deep biology/evolution/human/settlement coupling | R4.0 disables biological Deep coupling; macrohistory objective/freeze specify future role | Planned or missing as usable production implementation | Governed coupling processes and causal checkpoints. |

Do not infer that all Deep fields are absent: earlier Deep/background variables and exposure experiments are real. Conversely, they do not establish a complete queryable `DEEP_HISTORY(x,y,t)` with intensity, accessibility, stability, hazard, resource value, and biological/human/settlement coupling.

## I. R6 current capability maturity matrix

Readiness is about R6 readiness, not whether an earlier bounded run passed. `READY_REUSE` and `READY_WITH_ADAPTER` are local to the stated scope; missing-contract/data/model columns remain explicit.

### Table 8 — `R6_CURRENT_CAPABILITY_MATURITY_MATRIX`

| Domain | Capability | Existing implementation | Scientific maturity | Engine/provider | Reuse mode | Missing contract | Missing data | Missing model | R6 readiness |
|---|---|---|---|---|---|---|---|---|---|
| World | Canonical initial world | R3 A1 references and legacy world states | Candidate physical endpoints, not yet R6 canonical initial package | ARCANA | `REUSE_CONTRACT_ONLY` | R6 initial-state identity/boundary contract | Canonical input pack and provenance | Clean initialization law | `READY_CONTRACT_BINDING` |
| Geology | Geological/crustal state | Paleogeography/plate codes; P7Q source-material audits | Land/plate support only; no comprehensive physical composition | ARCANA/none | `REUSE_CONTRACT_ONLY` | Geological state semantics/authority | Lithology/crustal/province coverage | Geological formation/evolution | `MODEL_GAP` |
| Geography | Topography | Legacy terrain/physical fields and stage validators | Partial/stage-bounded | ARCANA | `REUSE_WITH_R6_ADAPTER` | Canonical topographic history/state schema | R6 boundary coverage | Global forward physical evolution | `READY_WITH_ADAPTER` |
| Geography | Shoreline | R3.14 shoreline bindings, B6 D2C1 adapter, land masks | Bounded valid transitions/baselines | ARCANA | `REUSE_WITH_R6_ADAPTER` | Generic temporal shoreline interface | Complete R6 interval support | Coupled shoreline evolution where absent | `READY_WITH_ADAPTER` |
| Climate | Climate | R3.14 hierarchy and replay machinery | Mature scoped legacy machinery | ARCANA/providers | `REUSE_WITH_R6_ADAPTER` | R6 climate state and forcing boundary | Canonical input/domain binding | Cross-domain climate law if needed | `READY_WITH_ADAPTER` |
| Climate | Historical climate | R3.14, B5/B6 inspectors, P7S climate binder | Bounded ages/cohort; provider gaps remain | Krapp, Beyer, R3.14 providers | `REUSE_WITH_R6_ADAPTER` | Provider-neutral applicability contract | Monthly/age/grid complete forcing | Missing intervals/variables | `PROVIDER_GAP` |
| Water | Hydrology | B6 D1–D4 canonical paleo-hydrology replay | Strong bounded replay/reconstruction | ARCANA seasonal generator | `REUSE_WITH_R6_ADAPTER` | R6 state/checkpoint mapping | Full supported interval/input binding | Cross-domain feedback scheduler | `READY_WITH_ADAPTER` |
| Water | Freshwater support | B6 D4 access/reliability | Derived support with bounded authority | ARCANA | `REUSE_WITH_R6_ADAPTER` | Separate support vs stock/resource schema | Full history/biological support | Accessibility/consumer integration | `READY_CONTRACT_BINDING` |
| Events | CHA-1 | R3.10 bridge and evidence | Bounded event execution/evidence | ARCANA | `REUSE_CONTRACT_ONLY` | R6 event package/replay contract | Canonical R6 forcing/event binding | Full clean replay integration | `READY_CONTRACT_BINDING` |
| Events | CHA-2 | R3.20 YD hazard; R3.27–39 stage event bindings | Event-specific/regionally bounded | ARCANA | `REUSE_CONTRACT_ONLY` | General R6 CHA-2 event applicability/effects | Full event boundary data | Global event process/coupling | `PARTIAL_SCIENTIFIC` |
| Geology | Parent material | P7Q PRE5 static 0 ka state and source contracts | Endpoint only; classifications constrained | P7 source products | `REUSE_WITH_R6_ADAPTER` | R6 semantic/state binding | Historical material occurrence/formation | Authorized transition laws | `MODEL_GAP` |
| Geology | Temporal parent material | HRAB sparse constraints/rule registry | Core architecture only; no forward families/cells authorized | HRAB/P7 | `REUSE_WITH_R6_ADAPTER` | Generic temporal state/checkpoint interface | Dated formation/persistence drivers | Transition processes | `MODEL_GAP` |
| Soil | Physical soil | SoilGrids cohort endpoint and six-layer proof | Bounded 0 ka endpoint profiles | SoilGrids 2.0 | `REUSE_WITH_R6_ADAPTER` | R6 profile/coverage and authority metadata | Full grid + historical profiles | Historical pedogenesis/transfer | `PARTIAL_SCIENTIFIC` |
| Soil | Hydraulics | WHC/Ksat derivations; Rosetta 3.0.2 code 3 | Proven tested endpoint calculation; historical transfer unproven | Rosetta / SoilGrids | `REUSE_WITH_R6_ADAPTER` | General units/error/support contract | Applicable historical texture/soil | Transfer model | `PARTIAL_SCIENTIFIC` |
| Ecology | BIOME4 vegetation solver | Frozen production input contract and runtime binding | Runtime ready; scientific production unauthorized | BIOME4 v4.2b2 | `REUSE_WITH_R6_ADAPTER` | Output normalization + flora ownership | Monthly climate/cloud/elevation/historical soil | ARCANA flora-history laws | `PROVIDER_GAP` |
| Ecology | Flora history | R3.34–39 producer/domestication plus BIOME4 consumer | Bounded food/domestication legacy states; no complete wild flora history | ARCANA + BIOME4 | `REUSE_CONTRACT_ONLY` | Flora state, origin, persistence, query contract | Historical flora coverage | Complete flora evolution | `IMPLEMENTATION_GAP` |
| Ecology | Fauna history | R3.21/23 and P7 census/contract | Identity/prior/census; no historical abundance or ranges complete | ARCANA; Madingley evaluated | `REUSE_CONTRACT_ONLY` | Fauna state and abundance/range boundaries | Historical occupancy/abundance authority | Coupled fauna processes | `MODEL_GAP` |
| Ecology | Species ranges | R3.21 closure, R3.27/28 time/spatial methods, provider studies | Partial lineage/occupancy candidates; no complete range history | ARCANA; RangeShiftR evaluated | `REUSE_WITH_R6_ADAPTER` | Species-range state/query contract | Dated historical spatial authority | Range dynamics where unsupported | `PARTIAL_SCIENTIFIC` |
| Genetics | Population genetics | NEMO, SLiM/tskit, Geonomics, CDMetaPOP bounded experiments | Mature for selected experiment classes | NEMO, SLiM, Geonomics, CDMetaPOP | `REUSE_WITH_R6_ADAPTER` | Engine-neutral genetics readout contract | R6 initial/founder distributions | General eco-demographic coupling | `READY_WITH_ADAPTER` |
| Ecology | Freshwater ecology | Hydrology and freshwater support foundations | Physical support; biology not complete | ARCANA | `REUSE_CONTRACT_ONLY` | Organism/habitat and connectivity contracts | Biological authority and history | Aquatic ecological processes | `MODEL_GAP` |
| Ecology | Marine ecology | No genuine governed support authority recovered in current P7 conclusions | Not materialized | None established | `ARCHIVE_ONLY` for unrelated proxies | Marine ecology contract | Marine biological authority | Marine ecosystem model | `NOT_STARTED` |
| Deep | Deep history | Partial early variables/experiments; R4.0 biological coupling off | Partial/reference only | ARCANA legacy | `REUSE_CONTRACT_ONLY` | Complete R6 Deep state/coupling contract | Spatial/temporal field inputs | Coupled Deep process laws | `IMPLEMENTATION_GAP` |
| Resources | Material resources | R5.17 resource component/candidate work; geology gaps | Partial/authority-limited | ARCANA/provider candidates | `REUSE_CONTRACT_ONLY` | Stock/occurrence/access semantics | Physical material authority | Resource formation/renewal | `PARTIAL_SCIENTIFIC` |
| Resources | Biological resources | Plant trophic support and R3.34+ food outputs | Partial, branch and time scoped | ARCANA/BIOME4 candidate | `REUSE_WITH_R6_ADAPTER` | Independent resource stock history | Wild resource availability | Ecosystem/resource dynamics | `PARTIAL_SCIENTIFIC` |
| Human support | Food support | R3.34–39 and R5.17 B7 food-support contracts | Bounded support/production evidence | ARCANA legacy | `REUSE_CONTRACT_ONLY` | R6 food/resource interface | Independent wild/domestic history | Full access/processing model | `PARTIAL_SCIENTIFIC` |
| Human support | Carrying support / K | Objective and human-support bridge semantics | Conceptual downstream quantity, not complete history | ARCANA contract | `REUSE_CONTRACT_ONLY` | R6 derivation/dependency contract | Resource/access inputs | Coupled support law | `IMPLEMENTATION_GAP` |
| Human | Human population | R3.27–28 candidate replay | Bounded legacy candidate trajectories | ARCANA | `REUSE_REFERENCE_IMPLEMENTATION` | Emergent R6 demographic model | Canonical R6 initial cohort/history | Clean demographic laws | `PARTIAL_SCIENTIFIC` |
| Human | Migration | Geonomics/CDMetaPOP and bounded replay | Specialized movement experiments | Geonomics/CDMetaPOP | `REUSE_WITH_R6_ADAPTER` | Cross-domain R6 migration interface | Canonical barriers/resources | Integrated migration/access model | `READY_WITH_ADAPTER` |
| Human | Settlements | R3.27–39 bounded human macro artifacts | Partial legacy outputs | ARCANA | `REUSE_REFERENCE_IMPLEMENTATION` | Settlement event/state schema | Canonical temporal settlement evidence | General settlement formation | `IMPLEMENTATION_GAP` |
| Human | Trade | R3.38 exchange/technology genealogy | Bounded concept and stage outputs | ARCANA | `REUSE_CONTRACT_ONLY` | Spatial network, flows, access semantics | Historical network data | Trade dynamics | `PARTIAL_SCIENTIFIC` |
| Human | Technology | R3.38 and R3.34–39 stage outputs | Bounded genealogy/producer technologies | ARCANA | `REUSE_WITH_R6_ADAPTER` | General technology state and effects | Cross-domain historical support | Technology evolution/diffusion | `PARTIAL_SCIENTIFIC` |
| Human | Polities | No complete R6-ready state system shown | Incomplete | None established | `REUSE_CONTRACT_ONLY` where evidence applies | Polity schema and authority contract | Historical spatial/temporal inputs | Polity emergence | `NOT_STARTED` |
| Human | War/conflict | Event/diagnostic fragments only | Not established as complete governed process | None established | `ARCHIVE_ONLY` pending authority | Conflict event/state contract | Evidence | Conflict dynamics | `NOT_STARTED` |
| Persistence | Historical state store | Stage manifests, NPZ/checkpoint outputs | Per-stage products only | ARCANA files | `REFACTOR_CORE` | Global versioned `WORLD_HISTORY` schema/store | Durable retention/index | Persistence/query implementation | `IMPLEMENTATION_GAP` |
| Query | Query engine | R5.0 `state_query/r50_query.py`, R5.1–R5.9 bounded modules | Selective scoped query/replay | ARCANA | `REUSE_WITH_R6_ADAPTER` | Cross-domain, support-aware query API | Global history/index | Query planner/explanations | `IMPLEMENTATION_GAP` |
| Search | Historical search | Execution reference index and manifests; not world-state search | Artifact navigation only | ARCANA tools | `REUSE_VALIDATOR_ONLY` | Spatial-temporal search index/schema | Persisted history | Historical search service | `NOT_STARTED` |
| Replay | High-resolution replay | R3.10, R3.14, R3.27–28, HRAB, R4 bounded replays | Mature selected patterns | ARCANA + external engines | `REUSE_WITH_R6_ADAPTER` | Generic causal-cone/refinement contract | Native fine evidence by domain | General refinement planner | `READY_WITH_ADAPTER` |

## J. R6 domain interface specification

These are conceptual interfaces aligned with `R6_WORLD_HISTORY_ARCHITECTURE_FREEZE.md`; they are not Python APIs or authorization to run. Every interface returns a typed state plus support class, authority references, uncertainty, provenance, and schema/version. Temporal and spatial support must be explicit per field; absence of support is not zero.

### Table 9 — Conceptual domain interfaces

| Interface | ARCANA-owned state / minimum inputs | Optional inputs → output | Authority + uncertainty | Time / space; checkpoint, persistence, query, refinement | Existing basis; adapter? |
|---|---|---|---|---|---|
| `R6_CANONICAL_INITIAL_STATE_INTERFACE` | Canonical initial state, laws, grid/cell registry, CHA definitions, seed/ensemble lineage | Optional source-specific initial packages → immutable run-input identity | Canonical authority IDs, hashes, compatibility and conflicts | Initial boundary to all; persists once; queryable and refinement parent; participates in first checkpoint | R3 world/A1 and R6 charter; **yes**, new R6 binding |
| `R6_PHYSICAL_GEOGRAPHY_STATE_INTERFACE` | Land, elevation, basins, terrain, masks, physical laws/events | Geology/shoreline drivers → physical geography state | Source/model support, native resolution, uncertainty | Domain time steps and physical grid; checkpointed/persisted/queryable; refinement with boundary conditions | A1/R3.10/legacy physical code; **yes** |
| `R6_SHORELINE_STATE_INTERFACE` | Sea/land boundary and dated shoreline support | Eustatic/physical forcing → shoreline/land applicability | Authority and transitions, coast uncertainty | Event/consumer checkpoints; persisted/queryable; refinement only at supported scales | R3.14, B6 D2C1; **yes** |
| `R6_CLIMATE_STATE_INTERFACE` | Time/space climate variables with units, masks, provider/model semantics | Seasonal/derived diagnostics → validated climate forcing/state | Provider/runtime/version, variable interpretation, uncertainty | Provider-supported times and native/coarse grid; checkpoint at consumer demand; persist/query; refinement only with valid native evidence | R3.14, P7S tools, Krapp/Beyer adapters; **yes** |
| `R6_HYDROLOGY_STATE_INTERFACE` | Water stores/flows and seasonal state under climate/geography | Soil/runoff or shoreline conditions → hydro state | Generator authority, mass/unit/invariant checks, uncertainty | Generator-supported seasonal/time steps; checkpoint/persist/query; refinement at causal dependencies | B6 D1–D4; **yes**, strip R5 path assumptions |
| `R6_PARENT_MATERIAL_STATE_INTERFACE` | Material class/identity/support and unknown mask; authorized temporal rules | Formation/event providers → sparse parent state or UNKNOWN | PRE4/HRAB rule/source refs, conflict and formation interval, uncertainty | Only supported age intervals; interval checkpoint, persistent sparse history and query; branch refinement | PRE4/PRE5/HRAB; **yes**, generic R6 schema |
| `R6_SOIL_STATE_INTERFACE` | Profile layers, depth geometry, texture/physical properties with units | Parent material, climate, hydrology → physical soil state | Provider/model, profile applicability, derivation lineage, uncertainty | Only supported profile ages/grids; checkpoint/persist/query; refinement requires temporal transfer authority | P7S SoilGrids/Rosetta; **yes** |
| `R6_HYDRAULIC_STATE_INTERFACE` | WHC, Ksat and hydraulic properties with depth and unit semantics | Validated soil/climate → hydraulic consumer fields | Formula/version, inputs, profile coverage, uncertainty | Consumer checkpoints, not necessarily every climate timestamp; persist/query derived provenance | P7S endpoint formulas/Rosetta; **yes** |
| `R6_FLORA_STATE_INTERFACE` | ARCANA taxa, presence/composition, persistence, distribution and uncertainty | Climate/soil/CO₂ plus optional BIOME4 diagnostics → flora history | Lineage/provider/model authority; unknown and prior-vs-observed markers | Species/consumer/event anchors; persist/query/refine by taxa and causal cone | R3.34–39, BIOME4; **yes**, ARCANA-owned semantics |
| `R6_FAUNA_STATE_INTERFACE` | Species/component identity, occurrence/range, population where authorized, trophic role | Flora/climate/hydrology/habitat → fauna history | R3.21 closure, R3.23 priors, range/population authority separately labeled | Lineage/event/consumer temporal support; persist/query/refine by species/region | R3.21/23, R5.17 censuses, Madingley/RangeShiftR candidates; **yes** |
| `R6_FRESHWATER_ECOLOGY_INTERFACE` | Freshwater habitat/organism state and connectivity | Hydrology/shoreline/biology → aquatic ecology | Biological source authority, habitat applicability and uncertainty | Hydro/event checkpoints; persist/query/refine by catchment | B6 hydro plus future biology; **yes** |
| `R6_MARINE_ECOLOGY_INTERFACE` | Marine organisms/resources and connected water body | Shoreline/ocean conditions → marine ecological state | Genuine governed marine biological authority mandatory | Marine event/domain times; persist/query/refine only if evidence supports | No complete current authority; **yes**, model/data gap |
| `R6_DEEP_STATE_INTERFACE` | Deep intensity/accessibility/stability/hazard/resource value where authorized | Geography, climate, biology, human state → Deep state/couplings | Independent Deep authority, causal links, uncertainty | Its own temporal/spatial support; checkpoint/persist/query/refine | Partial legacy/early Deep work; **yes** |
| `R6_RESOURCE_STATE_INTERFACE` | First-class material, biological, freshwater, marine, and Deep stock/support state | Accessibility/ecology/formation → resources separate from K | Domain-specific authority and stock-vs-flow semantics | Each resource’s natural support times/grid; checkpoint/persist/query/refine by resource | R5.17 B6/B7 and R3.34; **yes** |
| `R6_HUMAN_SUPPORT_INTERFACE` | Derived support from resources, access, technology, trade, infrastructure, Deep, hazards | Validated human-use rules → support/capacity diagnostics | Explicit dependencies, units, uncertainty; K remains derived | Consumer-driven, not forced at every tick; persists/query with dependency graph | R5.17 bridge + macrohistory objective; **yes** |
| `R6_HUMAN_STATE_INTERFACE` | Emergent population, demography, migration, settlements | Support/resources/technology/trade/polity → human history | Initial authority, model/runtime, seed/ensemble and uncertainty | Human event/checkpoint schedule; persist/query/refine | R3.27–39/Geonomics/CDMetaPOP; **yes** |
| `R6_EVENT_INTERFACE` | Immutable event identity, time, footprint, forcing/effect, before/after links | CHA-1/CHA-2 and governed modeled events → event records | Event authority, uncertainty, validation, provenance | Event-centered checkpoint; persistent/queryable; refinement boundary | R3.10/R3.20/R3.27–39; **yes** |
| `R6_WORLD_HISTORY_QUERY_INTERFACE` | Typed state, time, spatial selector, support/authority filters | Event/provenance relations → state/history/why result | Preserve source-vs-derived distinction and uncertainty | Arbitrary supported query over persisted history; query is read-only; refinement plan is separate | R5.0–R5.9 scoped query; **yes**, core new implementation |
| `R6_REFINEMENT_INTERFACE` | Parent history ID, valid anchor, target region/time, causal cone, resolution evidence | Domain adapters → immutable branch and comparison | Inherited + new authority, branch lineage and uncertainty | Local temporal/spatial refinement; separately checkpointed/persisted/queryable | R3.10/14/28 and HRAB principles; **yes** |

## K. Engine adapter specification

Conceptual boundary:

```text
ARCANA INPUT STATE
    -> ENGINE ADAPTER (semantic gate, units, time/grid mapping, config/seed)
    -> EXTERNAL ENGINE (identified runtime/version)
    -> RAW ENGINE OUTPUT
    -> ARCANA NORMALIZATION (schema, units, support and missingness)
    -> VALIDATION (domain, authority, uncertainty, provenance, invariants)
    -> ARCANA HISTORICAL STATE (or explicit BLOCKED/UNKNOWN result)
```

Minimum adapter record: adapter/schema version; input state and authority references; semantic/unit checks; spatial and temporal mapping with native-support declaration; engine name/version/source/runtime/executable identity; seed/configuration and environment; raw-output hash/path; normalized-output semantics; uncertainty and unknown masks; validation results and tolerance rationale; provenance dependencies; failure/partial-result policy. An engine failure cannot silently yield a plausible default. Adapter-specific controls remain scientifically distinct; a common envelope is not a claim that engines are interchangeable.

| Engine | Existing boundary evidence | R6 adapter decision |
|---|---|---|
| BIOME4 | Exact source/runtime binding, input contract, synthetic smoke, input mapping/soil aggregation requirements | Retain as ecological solver adapter, but no production until provider gaps/authorization close; ARCANA retains flora ontology. |
| SLiM + tskit/msprime/pyslim | Seeded bounded experiment wrappers and ancestry collectors | Preserve population-genetics adapter family; keep genealogical output distinct from demography/range. |
| Geonomics | R4 native schema mapping, parameter materialization, exact state injection, execution/readout gates | Reuse mature specialized adapter pattern, then define R6 interface/contract. |
| CDMetaPOP | Seeded bounded launchers and forcing-parity/comparability diagnostics | Optional specialized dispersal/demogenetic adapter; comparability adjudication must travel with output. |
| NEMO | 2.4.2 experiment wrappers, QTL/selection readouts | Keep bounded population-genetic oracle/engine wrapper; avoid treating it as global genetics history. |
| RangeShiftR | Benchmarks/source probes only | Not a selected or validated canonical adapter; provider/model suitability gate first. |
| Madingley | Benchmark and runtime/input audit | No production adapter authorization; if later used, separate species-level ARCANA input binding from functional ecosystem outputs. |

## L. Provider adapter specification

Providers supply observations, reconstructions, boundary data, or model products; they do not execute ARCANA's world transition rules. Conceptual flow:

```text
provider identity / rights / version
  -> bounded acquisition or validated cache
  -> byte hash and metadata capture
  -> semantic validation (variables, units, dimensions, CRS, time)
  -> temporal/spatial applicability and masks
  -> authority classification / conflicts / uncertainty
  -> normalized ARCANA provider state + provenance
```

Reuse climate/P7 patterns for exact metadata, hashes, bounded/resumable acquisition, cache integrity, applicability masks, overlap/endpoint comparison, absolute-vs-anomaly decisions, and fail-closed behavior. Keep Krapp, Beyer, SoilGrids, HWSD, and other provider semantics in provider-specific adapters. Do not silently resample or extrapolate; preserve coarse/native support and distinguish acquired bytes from scientifically bound state.

## M. Provisional do-not-reimplement list

This is provisional and evidence-based; it is not an unconditional approval to import a subsystem.

1. **Scientific Authority Register schema and builder** — `tools/build_arcana_worldsim_scientific_authority_register.py`; refresh its old `authority_basis_head` only through an authorized reconciliation.
2. **Execution-reference index tooling** — reuse for navigation/hash semantics, not authority adjudication; preserve protected staged versions.
3. **Simulation-results inventory and semantic catalog pattern** — reuse its custody/hash/status model; improve pending semantic resolution rather than replacing it with an ungrounded new list.
4. **R3.14 climate provider/adaptive-clock/restart contracts** — reuse validated contract concepts and validators; bind actual R6 providers anew.
5. **B5/B6 climate discovery/semantic inspectors and P7S provider binding/acquisition logic** — audit/extract utilities before reuse; retain Krapp/Beyer adapters and P7S cohort/decision semantics as scoped.
6. **R5.17-B6 hydrology replay chain and D2C1 shoreline adapter** — use as a candidate R6 domain adapter after exact input/output and R5-runtime decoupling.
7. **P7Q PRE4/HRAB sparse temporal rules, explicit unknown/conflict masks, endpoint constraints and checkpoint descriptors** — generalize only their proven abstractions; do not reimplement their scientific adjudication or claim evolution authorization.
8. **P7S six-layer WHC/Ksat derivation and Rosetta call/validation** — retain tested endpoint calculations with exact units and limitations; do not generalize historical transfer.
9. **Existing external-engine wrappers/tests** for NEMO, Geonomics, CDMetaPOP and SLiM/tskit, where their bounded domain matches the R6 question.
10. **R3.10/R3.14/R3.27–28 restart/replay and endpoint-validation patterns** — reuse the verified mechanism, not old world states as implicit R6 initial inputs.

## N. R6 true new implementation surface

Evidence supports the following as missing or not demonstrated in usable, generic form. Existing scoped query/manifests/checkpoints are inputs to the design, not proof that the complete service exists.

1. Versioned, persistent global `WORLD_HISTORY(x,y,t)` domain-state store with support, authority, uncertainty, provenance, schema and branch lineage.
2. Unified temporal object registry for hard anchors, event times, provider applicability, consumer-required times, intervals and domain-specific clocks.
3. Consumer-driven checkpoint planner coordinating domain schedules without forcing every specialist at every global timestamp.
4. Cross-domain causal scheduler and explicit feedback-cycle orchestration with fail-closed dependencies and deterministic replay metadata.
5. Generic causal-cone planner for high-resolution refinement; immutable branch/version manager and comparison/merge policy.
6. Read-only history query API plus temporal/spatial search indexes and cross-domain joins that preserve support and authority distinctions.
7. “Why”/provenance traversal from state through provider, initial state, events, rules, engines, checkpoints, and prior states.
8. Global uncertainty/UNKNOWN/conflict propagation and derived-view contracts, while preserving domain-specific meanings.
9. R6 checkpoint/restart compatibility and replay-equivalence contract across multiple adapters/domains.
10. Canonical initial-world package and explicit R6 CHA-1/CHA-2 event-binding/forward replay orchestration.

Not all listed items must land in one bootstrap. Reuse old implementations where validated; new R6 work should be the smallest durable, versioned core above those adapters.

## O. First R6 clean replay plan (design only)

```text
R6 bootstrap: canonical initial package + law/event/seed identities
  -> physical boundary state and applicable event contracts
  -> climate provider/model state at consumer-required checkpoints
  -> hydrology/freshwater replay where inputs and law validate
  -> CHA event engine at governed canonical event points
  -> domain consumers (soil/ecology/evolution) only when prerequisites bind
  -> resource/access state, then emergent human-support/human-history stages
  -> Year 0 endpoint as validation, never as a forced target
  -> continuously persist raw state, events, uncertainty, authority and provenance
```

This is a dependency sketch, not an authorized fixed timetable. The orchestrator should request domain outputs at causal/consumer checkpoints, reuse mature climate/hydrology machinery, and preserve partial domains as UNKNOWN or unavailable. Do not run P7S or BIOME4 at every historical timestamp by default. A consumer contract and exact temporal/spatial applicability determine when a solver runs. R5 results can be comparison evidence but are not required R6 initial state or endpoint targets.

## P. Smallest credible first implementation wave

### Table 10 — First-wave components

| Component | First-wave scope | Why evidence supports it | Exit evidence |
|---|---|---|---|
| R6 core identity/schema | Immutable run ID, canonical-input identity, typed domain-state envelope, authority/support/uncertainty/provenance refs | Architecture freeze and existing manifest/authority patterns are concrete | Schema validation and deterministic identity tests; no simulation |
| Historical state writer + event/provenance records | Append-only checkpoint and event records, immutable parent/branch IDs | R6 product requires persistent history; current per-stage files do not satisfy it | Tiny synthetic fixture round-trip and provenance query |
| Checkpoint/replay coordinator | Single-domain deterministic schedule first; dependency DAG and checkpoint contract | R3/R4 replay mechanics exist, global orchestration does not | Restart-equivalence fixture and explicit unresolved dependency behavior |
| One mature provider adapter | Climate metadata/applicability adapter using inspected R3.14/P7S utilities, no acquisition | Rich existing inspection/binding evidence; can prove adapter layering without claiming climate completeness | Fixture-based metadata, mask, hash and unknown tests |
| One mature domain adapter | Hydrology B6 replay contract behind R6 state envelope, in dry-run/fixture mode first | B6 is a substantial recent native replay and reconstruction chain | Semantic input/output binding and checkpoint persisted; no forced whole-history run |
| Query smoke | Query stored fixture by time/cell and return state + support + authority + provenance | Architecture requires queryability; R5 query is narrower | Demonstrates persisted read path and unknown semantics |

Do not begin with BIOME4 production, full fauna, soil evolution, or human-history simulation: their required inputs/models are not yet globally bound. This wave proves R6 architecture and adapter boundaries, not a scientific world replay. Exact first-wave selection remains subject to repository owner approval and separate execution authorization.

## Q. Migration without R5 runtime dependency

Allowed: source-code reuse, contract/schema reuse, provider reuse, validator reuse, and reference/test-fixture reuse after version pinning and authority checks. Forbidden by default: requiring an R5-produced world-state execution chain as an R6 runtime input. An artifact can enter only through an explicit canonical-initial-authority or provider contract that independently names its semantics, version, support, and role. R5 may be used for retrospective comparison, never as a hidden initializer or endpoint-fitting target. Keep adapters free of `local_runs/v0_6D1_R5_*` assumptions and test with explicit fixtures.

## R. Development history versus R6 production stages

PRE1–PRE5*, D2C1/D2D*, and other micro-gates remain useful audit provenance. R6 consumes their final governed contracts/results through stable domain/provider interfaces; it does not reproduce their gate sequence as runtime stages. R6 stages should represent scientifically meaningful causal/checkpoint units and can call multiple adapters under one persisted history transaction. Preserve provenance references to micro-gates without importing their naming, temporary files, or execution directories into R6's core model.

## S. Explicit answers to the 18 questions

1. **Which parts of the original ARCANA simulation can R6 reuse directly?** Authority/manifest/index schemas and builders, selected deterministic/restart/validation utilities, exact R3/R4 bounded engine wrappers, and tested domain formulas/contracts where their authority scope matches. “Directly” still requires versioned dependency and input identity; old world-state payloads are not automatically direct runtime inputs.
2. **Which parts need adapters but not scientific redesign?** R3.14 climate provider machinery, B6 seasonal hydrology replay, shoreline/land-mask binding, P7S climate/soil provider semantics, Rosetta/WHC/Ksat consumers, and specialized engines whose input/output scope matches the R6 domain.
3. **Which P7Q/HRAB capabilities become generic temporal infrastructure?** Rule registry shape, hard-anchor/event registry, sparse interval/checkpoint descriptors, support/applicability masks, UNKNOWN/conflict semantics, endpoint-only constraints, and deterministic clock validation. No generic interpolation or process authority is inherited.
4. **Which P7S capabilities become generic soil/hydraulic infrastructure?** Profile-layer geometry, unit-checked WHC/Ksat derivation, Rosetta invocation metadata, provider/profile masks, and endpoint validation. Historical soil/pedogenesis transfer remains unresolved.
5. **Which historical-climate tools are already generic enough for R6?** Bounded transport/cache integrity, generic NetCDF/HDF5 coordinate/metadata inspection, generic hash and mask validation, exact replay comparison primitives, and runtime binding patterns are extraction candidates. The current scripts are mostly stage-bound, so generic reuse requires isolating tested primitives.
6. **Which climate tools remain provider-specific?** Krapp/Beyer discovery, field mapping, annual/monthly interpretation, absolute/anomaly semantics, cloud/sunshine mapping, licensing/source routes, age availability and provider-specific masks.
7. **Which old climate artifacts are diagnostic/legacy only?** R3.18 exposure integral is not pointwise forcing; R3.20 hazard rank is not hydrology; R3.14 legacy values require fresh R6 authority/applicability binding; cohort-specific P7S comparisons are evidence, not global forcing.
8. **Is current hydrology machinery reusable as an R6 domain adapter?** Yes, as a candidate with a new R6 boundary: B6 D1–D4 binds generator, seasonality, shoreline mask, replay/reconstruction, freshwater access/reliability. It must be decoupled from R5 paths and validated against R6 inputs; it is not automatically a global continuous history.
9. **What existing mechanisms support checkpoint/replay?** R3.8, R3.11–R3.20, R3.27–28, R4 job/runtime evidence, HRAB interval descriptors, and R5 query/selective replay modules. No single global multi-domain checkpoint/history system is established.
10. **Which engines are integrated versus merely evaluated?** NEMO 2.4.2, Geonomics, CDMetaPOP, and SLiM/tskit have bounded actual integrations/runs. RangeShiftR is evaluated/benchmarked, not a canonical production adapter. Madingley has benchmark/runtime/input audits only, no authorized production run. BIOME4 runtime is bound but production is unauthorized.
11. **Which engine wrappers should survive?** Keep tested wrappers for NEMO/Geonomics/CDMetaPOP/SLiM when the scientific question matches, along with runtime/config/seed/readout validation. Keep BIOME4 source binding and adapter contract, not a false production status. Reassess RangeShiftR/Madingley only through suitability gates.
12. **Which schemas are reusable?** Stage output manifests/seals, exact source/provider bindings, R4 job/config/evidence contracts, R3.21 lineage/component schemas, PRE4 temporal rules, HRAB interval/cell-rule manifests, and P7S profile/unit/adjudication schemas. Version and wrap them in R6 domain state/provenance envelopes.
13. **What provenance infrastructure can become R6 core?** Authority register concepts, source/runtime/hash references, execution index/manifests, seal/output manifests, config/seed/job capture and fail-closed validators. The index is navigational; the authority register basis is stale relative to inspected HEAD and needs separate refresh. A dependency graph/history traversal still needs implementation.
14. **What truly needs new implementation?** Persistent global history store, temporal registry, consumer checkpoint scheduler, cross-domain causal/feedback orchestrator, causal-cone planner, branch/version manager, support-aware query/search, provenance “why” traversal and generic uncertainty propagation.
15. **Smallest credible R6 bootstrap wave?** Core state/provenance schema + append-only history/event writer + single-domain checkpoint/restart + fixture-based climate/hydrology adapter boundary + a query smoke returning state/support/provenance. Avoid production scientific runs in the bootstrap proof.
16. **How much scientific capability is already present?** Considerable bounded capability across physical replay, climate/hydrology, population genetics, lineages, human-support and specialist execution. It is not possible to reduce this to a defensible percentage: the remaining scientific gaps are domain-specific and several global histories lack authority.
17. **Which gaps are scientific versus architectural/integration?** Architectural: global persistence, scheduler, query/search, causal provenance, generic adapter envelope. Integration: exact R6 input binding, grids, time supports, runtime isolation and contracts. Scientific: geological/parent-material transitions, historical soil transfer, full historical climate support, fauna occurrence/abundance, marine ecology, Deep coupling and human macrohistory laws.
18. **Which provider gaps should wait for a real consumer?** BIOME4 cloud/sunshine/elevation/complete monthly climate, historical soil profiles, unsupported ages/regions, marine biology, and any external range/fauna/Deep provider whose target semantics are not required by an authorized R6 consumer. Preserve an explicit missing-input record; do not acquire data speculatively.

## Readiness, risks, and decision

**Strongest reusable capability:** governance/provenance patterns; selected climate and hydrology replay machinery; bounded genetics and spatial-engine adapters; P7's careful applicability, unknown, endpoint, and no-interpolation semantics.

**Largest integration gaps:** no persistent cross-domain history database, global temporal/checkpoint planner, causal/feedback orchestrator, cross-domain search/query, or general refinement branch manager.

**Largest scientific gaps:** geological/source-material causality; temporal parent-material and soil state; globally applicable historical climate; full flora/fauna ranges and abundance; freshwater/marine ecology; complete Deep fields and coupling; and governed integrated human population/settlement/trade/polity/conflict evolution.

**R6 readiness by broad domain:** physical/climate/hydrology and population-genetic machinery are `READY_WITH_ADAPTER` only within source-supported scopes; temporal parent material, historical soil, flora/fauna, Deep and resources are partial or have scientific/model gaps; persistent history/query/orchestration are implementation gaps; marine biology and several human-history mechanisms are not started as complete R6 domains. See the maturity matrix for per-capability classifications.

**Decision:** `REUSE_EXISTING_BOUNDED_CAPABILITIES__BUILD_MINIMUM_R6_HISTORY_AND_ORCHESTRATION_CORE__KEEP_UNSUPPORTED_DOMAINS_EXPLICITLY_UNKNOWN`.

**Verdict:** Architecture/capability reconciliation complete as a design artifact; no R6 implementation or scientific execution performed. R5 runtime dependency remains false.

**Recommended next action:** Review this inventory against the frozen architecture; then authorize a separate R6 bootstrap design/implementation task limited to versioned state/provenance, persistence, one adapter boundary, checkpoint/restart, and query smoke. Before implementation, reconcile the authority-register basis head and verify any specific source/result used by the first adapter.

## Scope and validation record

- Repository: `siegmound/ARCANA_WORLD`; branch `main`; inspected HEAD/origin `592b1651b405363373590092e133bd25569d99a5`.
- R5 runtime dependency required for R6: **false**.
- Scientific simulation executed: **no**.
- Provider acquisition executed: **no**.
- R6 implementation executed: **no**.
- Staging/commit/push: **no**.
- Protected execution indexes: not edited or regenerated.
- This document is a repository-grounded reconciliation, not an authority promotion, provider authorization, execution authorization, or seal.

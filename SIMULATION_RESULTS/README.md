# ARCANA WorldSim — Consolidated Simulation Results

## Purpose

`SIMULATION_RESULTS/` is the stable repository-local catalogue of WorldSim
simulation results that were previously distributed across `outputs/` and
`local_runs/`.

The objective is to stop rediscovering historical simulation payloads every
time a later stage needs environmental, biological, demographic, ecological,
or replay information.

The files in this directory are COPIES.

Their original historical locations were not moved, renamed, modified, or
deleted.

Every copied file was SHA256-checked against its source during consolidation.

---

## Consolidation snapshot

Consolidation source:

- `outputs/`
- `local_runs/`

Result:

- 863 copied source files
- 357.17 MB total copied data
- 100% post-copy SHA256 verification passed

Initial consolidation commit:

`0df810112f97619f8dc2025d0e99c20ecae1a0f6`

Machine-readable catalogues:

- `MANIFEST.csv`
- `MANIFEST.json`

The manifest records:

- source root
- source stage
- filename
- extension
- byte size
- SHA256
- original relative path
- consolidated path
- copy-verification state

Authority and detailed semantic descriptions are intentionally separate from
copy integrity and will be progressively adjudicated from repository contracts,
stage manifests, audits, and payload inspection.

---

# Directory structure

## `00_CORE_EARLY_SIMULATION/`

Early WorldSim baseline and development states.

Main covered stages include:

- R1
- R2
- R2.1
- R3
- R3.5

Important contents include:

### R1 — 210 Ma rebaseline

`WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz`

Common WorldSim state at the 210 Ma rebaseline.

Associated files include:

- H0 replay initialization
- HX replay initialization
- species registry
- state metadata
- fresh-extraction verification

### R2 / R2.1

Contains convergence and resolution experiments across the early 210–180 Ma
simulation interval.

Examples:

- `CONVERGENCE_210_205_62P5KYR_STATE.npz`
- `CONVERGENCE_210_205_125KYR_STATE.npz`
- `CONVERGENCE_210_205_250KYR_STATE.npz`
- `CONVERGENCE_FULL_210_180_500KYR_STATE.npz`
- `H0_REBASED_210_180_250KYR_STATE_v0_6D1_R2.npz`
- `H0_REBASED_210_180_R21_STATE.npz`

These are useful for provenance, convergence checking, and reconstruction of
the early WorldSim simulation chain.

### R3 / R3.5

Contains early dynamic and topology-related WorldSim outputs.

Examples:

- `R3B_210_205_FISSION_ON_STATE.npz`
- `DYNAMIC_STATE_210_208_q0.08.npz`
- paleogeographic event catalogue
- dynamic telemetry

These are retained as part of the historical simulation evidence.

---

## `01_CORE_WORLD_HISTORY/`

This is the most important directory for the long-duration physical and
biological WorldSim history.

It contains retained checkpoints and interval products from the canonical
R3-era simulation chain.

### R3.8 — 150 Ma

`WORLD1_150Ma_CANONICAL_CONTINUATION_CHECKPOINT_v0_6D1_R3_8.npz`

Retained continuation checkpoint at 150 Ma.

Companion JSON contains checkpoint state/metadata.

### R3.10 — 65.5 Ma

`WORLD1_H0_65P5Ma_POST_CHA1_500KY_CANONICAL_CHECKPOINT_v0_6D1_R3_10.npz`

Post-CHA1 checkpoint.

Additional scientific products include:

- extinction events
- physical food-web timeseries
- species diagnostics

### R3.11 — 61 Ma

`WORLD1_H0_61Ma_POST_CHA1_5MY_RECOVERY_CHECKPOINT_v0_6D1_R3_11.npz`

Post-CHA1 recovery checkpoint.

### R3.12 — 46 Ma

`WORLD1_H0_46Ma_POST_CHA1_20MY_DIVERSITY_RECOVERY_CHECKPOINT_v0_6D1_R3_12.npz`

Longer-term diversity recovery checkpoint.

### R3.13 — 30 Ma

`WORLD1_H0_30Ma_LONG_TERM_POST_CHA1_DIVERSIFICATION_REASSEMBLY_CHECKPOINT_v0_6D1_R3_13.npz`

Long-term post-CHA1 diversification/reassembly checkpoint.

### R3.15 — 250 ka

`WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.npz`

Late-Cenozoic biological state before the C2 bridge.

### R3.16 — 125 ka

`WORLD1_H0_125ka_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY_PRE_120KA_RESTART_CHECKPOINT_v0_6D1_R3_16.npz`

125 ka checkpoint preserving the C2 exposure state.

### R3.17 — 125–120 ka bridge

`R3_17_PENDING_125_TO_120KA_EXPOSURE_ACCUMULATOR.npz`

Environmental exposure accumulator bridging the restart boundary.

### R3.18 — 125 ka to present

`R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz`

Integrated recent environmental exposure and transport-phase product.

This is one of the important environmental inputs for later high-resolution
replay and human-support work.

### R3.19 — 0 ka

`WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.npz`

Present-day endpoint of the retained H0 natural-control WorldSim chain.

### R3.20 — 15–11 ka hydrological hazard interval

`R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz`

High-temporal-resolution CHA2 hydrological-hazard product.

Important semantic restriction:

This payload represents hydrological HAZARD / disruption fields.

It must not automatically be interpreted as terrestrial freshwater supply,
river discharge, usable water availability, or human carrying capacity.

Those meanings require separate source/semantic authority.

---

## `02_SCIENTIFIC_REPLAY/`

Scientific replay and derived-history products from R3.21 through R3.39.

This directory progressively bridges the natural WorldSim into biological,
human, ecological, demographic, technological, economic, and cultural
interpretation.

### R3.21–R3.26 — lineage and phenotype bridge

Contains:

- present lineage registry
- present component registry
- reduced genetic state
- functional phenotype specification
- primitive trait catalog
- derived capability graph
- H1/H2/H3 diagnostic arrays
- candidate dossiers
- reproduction and rare-tail diagnostics

These stages identify and characterize retained lineages and biological
capabilities.

### R3.27 — macro replay

Main payload:

`R3_27_MACRO_REPLAY_TRAJECTORIES.npz`

Also includes the human 200 ka checkpoint and candidate outcomes.

### R3.28 — high-resolution population replay

Main payload:

`R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz`

Includes population outcomes and human 0 ka checkpoint.

### R3.29 — community network replay

Main payload:

`R3_29_COMMUNITY_NETWORK_REPLAY.npz`

Represents lineage/community organization and connectivity products.

### R3.30 — census and group replay

Main payloads:

- `R3_30_CENSUS_AND_GROUP_TIMESERIES.npz`
- `R3_30_WEIGHTED_GROUP_ABM.npz`

Includes late-Pleistocene community history and group/census outcomes.

### R3.31 — cultural / technological ecology

Main payloads:

- `R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz`
- `R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz`

### R3.32 — subsistence transition

Main payloads:

- `R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz`
- `R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz`

### R3.33 — Holocene environment and domestication

Main payloads:

- `R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz`
- `R3_33_DOMESTICATION_TRAJECTORIES.npz`

This stage is particularly important for later human-support geography because
it contains explicit Holocene environmental/resource information used by the
existing replay chain.

### R3.34 — producer/resource landscape

Main payloads:

- `R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz`
- `R3_34_PLANT_COEVOLUTION_DOMESTICATION_TRAJECTORIES.npz`

Also includes the producer taxon registry.

### R3.35 — producer domestication genetics

Main payloads:

- `R3_35_PRODUCER_DOMESTICATION_GENETIC_REPLAY.npz`
- `R3_35_PRODUCER_GENETIC_PRIORS.npz`

### R3.36 — selection ecology

Main payloads:

- `R3_36_DOMESTICATION_SELECTION_ECOLOGY_REPLAY.npz`
- `R3_36_RESOURCE_SELECTION_ECOLOGY.npz`

### R3.37 — managed-forager economy

Main payloads:

- `R3_37_MANAGED_FORAGER_ECONOMY_REPLAY.npz`
- `R3_37_WEIGHTED_ECONOMIC_NODES.npz`

### R3.38 — technology / exchange / cultural networks

Main payloads:

- `R3_38_CONCRETE_TECHNOLOGY_REPLAY.npz`
- `R3_38_GROUP_IMPLEMENTATION_ANCHORS.npz`
- `R3_38_REGIONAL_CULTURAL_NETWORKS.npz`

Also includes a reticulate cultural genealogy.

### R3.39 — symbolic memory / language / identity

Main payloads:

- `R3_39_SYMBOLIC_MEMORY_REPLAY.npz`
- `R3_39_CHA2_REGIONAL_MEMORY_BINDING.npz`
- `R3_39_REGIONAL_SYMBOLIC_LANGUAGE_IDENTITY_ANCHORS.npz`

Also includes the symbolic-memory event ledger and lineage-level outcomes.

---

## `03_DERIVED_REPLAY/`

Later high-resolution or derived products retained separately from the original
R3 scientific replay chain.

### R5.0

Contains deterministic derived states at:

- 20 ka
- 17.5 ka

Payloads:

- `R5_0_20KA_DERIVED_STATE.npz`
- `R5_0_17P5KA_DERIVED_STATE.npz`

### R5.1

Contains the cradle-analysis products:

- `R5_1_CRADLE_CANDIDATE_REGISTRY.json`
- `R5_1_CRADLE_OPPORTUNITY_ATLAS.npz`
- `R5_1_REGION_FAMILY_TEMPORAL_SUPPORT.npz`

These are especially relevant for geographic persistence, environmental
opportunity, and later human-support analysis.

### R5.5

Contains contact-zone products:

- `R5_5_CONTACT_OPPORTUNITY_ATLAS.npz`
- `R5_5_CONTACT_ZONE_HISTORY.json`

---

## `04_VALIDATION_AUXILIARY/`

Validation, runtime, engine-comparison, calibration, adjudication, and
development evidence.

This includes material related to:

- NEMO
- Geonomics
- CDMetaPOP
- RangeShiftR
- SLiM
- multi-engine comparison
- parameter mapping
- execution diagnostics
- evidence recovery
- reconciliation

IMPORTANT:

Files in this directory are NOT automatically primary WorldSim state.

Use them when validating provenance, scientific robustness, engine behavior, or
historical implementation decisions.

Do not treat this directory as the default data source for world-state queries.

---

# Support directories

## `90_SUPPORT_CORE/`

Supporting authority/evidence for the early and core WorldSim history.

Contains:

- formal audits
- checkpoint validation summaries
- sensitivity analyses
- recovery summaries
- restart envelopes
- conservation audits
- endpoint audits

Use this directory to understand why a core result was retained and how it was
validated.

---

## `91_SUPPORT_SCIENTIFIC_REPLAY/`

Support material for R3.21–R3.39.

Contains, depending on stage:

- `OUTPUT_MANIFEST`
- integrated audit
- authority document
- sensitivity / robustness analysis
- replay provenance
- calibration authority

For semantic interpretation of an R3.21–R3.39 payload, this directory should
normally be consulted together with `02_SCIENTIFIC_REPLAY/`.

---

## `92_SUPPORT_DERIVED_REPLAY/`

Support material for the R5 derived replay products.

Contains:

- replay recipes
- provenance
- query summaries
- authority-resolution summaries
- output manifests
- integrated audits

Use together with `03_DERIVED_REPLAY/`.

---

## `93_SUPPORT_VALIDATION/`

Large collection of formal audit, seal, authority, execution-plan, repair,
reconciliation, and validation evidence.

This directory exists primarily for provenance and audit reconstruction.

It should not be searched first when answering ordinary scientific questions
about the simulated world.

---

# Recommended lookup order

For future WorldSim work, use this order:

1. `MANIFEST.csv` or `MANIFEST.json`
2. `01_CORE_WORLD_HISTORY/` for the long physical/biological history
3. `02_SCIENTIFIC_REPLAY/` for R3.21–R3.39 replay products
4. `03_DERIVED_REPLAY/` for later high-resolution products
5. corresponding `90/91/92` support directory for semantics and authority
6. `04_VALIDATION_AUXILIARY/` and `93_SUPPORT_VALIDATION/` only when a
   provenance, validation, engine, or audit question requires them

This ordering is intended to prevent future stages from repeatedly searching
the complete historical repository.

---

# Important current limitations

This consolidation currently covers ONLY:

- `outputs/`
- `local_runs/`

It does NOT yet constitute a complete census of every possible data payload in
the repository.

In particular, historical/local provider bindings may contain additional
environmental source payloads not present in these two trees.

One known example is the R3.14 paleoclimate/provider material previously bound
through local provider packages.

Therefore:

absence from `SIMULATION_RESULTS/` does not yet prove that a physical input
never existed.

It only proves that it was not found among the consolidated `outputs/` and
`local_runs/` stage-root result files.

---

# Authority policy

Do not infer canonical authority merely because a file is present here.

There are three separate concepts:

1. **Integrity**
   - Is this copied file byte-identical to its historical source?

2. **Semantics**
   - What exactly do its arrays, fields, units, clocks, grids, and masks mean?

3. **Authority**
   - Was this payload retained, sealed, superseded, diagnostic-only, or used
     only as validation evidence?

Integrity has already been established during consolidation.

Semantic and authority classification will be filled progressively from:

- stage output manifests
- authority documents
- formal/integrated audits
- final seal evidence
- repository contracts
- direct payload schema inspection

Until then, do not promote a field to a new scientific meaning solely from its
filename.

---

# Next cataloguing step

The next repository task is NOT another filesystem search.

It is semantic cataloguing.

For each scientifically relevant payload we will progressively record:

- stage
- temporal coverage
- spatial grid
- array names
- shapes
- dtypes
- units where authoritative
- physical/biological meaning
- producer
- dependencies
- source authority
- canonical status
- supersession status
- intended downstream use

Priority environmental bridge products currently include:

- R3.18 recent environmental exposure
- R3.20 CHA2 hydrological hazard
- R3.33 Holocene environmental/resource landscape
- R5.1 cradle opportunity atlas

These should be inspected before creating new environmental or
human-support models, because existing WorldSim results must be reused whenever
they already contain the required information.

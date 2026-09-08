# v0.6D1-R5.17 — Human Support Capacity & Civilization Geography Foundation

## Authority

```yaml
STAGE: v0.6D1-R5.17
STATUS: AUTHORIZED_IN_PROGRESS
PARENT: v0.6D1-R5.16 SEALED
OBJECTIVE_CHARTER: ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md
ROLE: WORLD_TO_HUMAN_CARRYING_CAPACITY_BRIDGE
SEAL_ACTION: false
AUTO_SEAL: forbidden
```

R5.17 is the first post-R5.16 scientific implementation stage. It does not simulate civilizations, polities, wars or a detailed Year-0 history. Its purpose is to translate existing SEALED WorldSim state into explicit human-support and settlement-geography layers sufficient to define a baseline human carrying-capacity field `K(x,t)` without prescribing a target population.

## Scientific question

Can the SEALED WorldSim physical, ecological, human and Deep state be transformed into a repository-proven, uncertainty-aware set of human-support layers that defensibly answer where sustained population is possible, where settlement concentration is favored, and what baseline regional carrying capacity is available before later trade/technology/polity dynamics are introduced?

## Required principles

1. **No target population.** R5.17 must not tune inputs to force a desired global or regional human population.
2. **No civilization outcome target.** No desired city, state, culture, empire, trade route or strategic capital may be used as a calibration target.
3. **No single civilization score as primary authority.** Independent opportunity/hazard axes must remain available even if later summary indices are derived.
4. **No blind scaling.** Any weighted/downscaled representation must carry explicit population-equivalent semantics and preserve density-sensitive nonlinearities when later demographic dynamics are introduced.
5. **No historical fabrication.** Missing material-resource, hydrological, transport or Deep settlement variables must be derived or marked missing; they may not be silently invented from narrative expectation.
6. **Existing authorities remain immutable.** R5.16 and earlier SEALED artifacts are read-only scientific parents.
7. **External runtimes are optional providers.** Geonomics, SLiM, NEMO, RangeShiftR, CDMetaPOP or another provider may be used only when a defined subquestion benefits from them; they are not canonical writers.
8. **Long local runs are permitted.** If a justified provider calculation is expensive, R5.17 may prepare repository-tracked runner/config/seeds/validation and accept user-local execution evidence.
9. **Deep biological coupling remains OFF unless separately authorized.** R5.17 may derive human settlement-facing Deep geography from physical/canonical Deep state without turning Deep into a direct taxonomic or hidden demographic shortcut.
10. **Uncertainty is preserved.** Diagnostic or proxy quantities must retain their original semantics and not be upgraded to exact historical truth.

## Stage decomposition

### R5.17-A — Existing-layer binding and capability census

Bind only repository-proven inputs needed by the bridge and classify each required domain as:

```text
READY
PARTIAL
MISSING
NEEDS_NEW_COMPUTE
```

Minimum domains:

- land/coast/accessibility geometry;
- climate/environmental support;
- hydrology and water reliability;
- terrestrial/marine ecological productivity or support proxies;
- current human lineage/population-support state;
- material resources;
- geographic connectivity and transport opportunity;
- hazard fields;
- Deep physical availability/accessibility/stability/value/hazard;
- carrying-capacity semantics.

R5.17-A must distinguish an existing raw WorldSim variable from a civilization-facing layer. For example, an existing hydrological hazard index is not automatically a complete water-reliability layer, and a Deep energy/runtime state is not automatically a settlement-benefit score.

### R5.17-B — Environmental and water support layer

Derive human-facing support variables from existing geography, climate, hydrology, ecology and hazard evidence. At minimum, the design must keep beneficial support and hazard separate.

Potential outputs include:

```text
LAND_ACCESSIBILITY
FRESHWATER_SUPPORT
HYDROLOGICAL_RELIABILITY
BIOLOGICAL_FOOD_SUPPORT
MARINE_SUPPORT
CLIMATE_SUITABILITY
ENVIRONMENTAL_STABILITY
ENVIRONMENTAL_HAZARD
```

The exact variable names and equations are implementation decisions, not pre-authorized scientific facts.

### R5.17-C — Material-resource geography

Create explicit repository-derived opportunity layers for resources that can materially affect later settlement and civilization dynamics where source data supports them, for example:

```text
BIOMASS / TIMBER
STONE
CLAY
SALT
METALS / ORES
MARINE RESOURCES
OTHER GEOLOGICALLY JUSTIFIED RESOURCES
```

Absence of a source-supported resource layer must remain an explicit gap rather than an invented value.

### R5.17-D — Deep settlement geography

Translate physical/canonical Deep state into settlement-facing dimensions without treating Deep as a generic bonus:

```yaml
DEEP_ACCESSIBILITY
DEEP_INTENSITY
DEEP_STABILITY
DEEP_RESOURCE_VALUE
DEEP_HAZARD
```

High Deep intensity may be beneficial, neutral or harmful depending on accessibility, stability and hazard. Deep biological coupling remains outside this stage.

### R5.17-E — Connectivity and strategic geography

Derive transport and strategic opportunity from physical geography and supported hydrology, including where data permits:

- coastal access;
- navigable-water opportunity;
- river mouths and junctions;
- natural-harbour opportunity;
- island stepping chains;
- land corridors;
- mountain passes;
- straits/isthmuses/chokepoints;
- access to complementary resource regions;
- defensibility and exposure;
- network centrality or equivalent connectivity measures.

This subphase identifies opportunity geometry; it does not materialize trade networks or polities yet.

### R5.17-F — Baseline human carrying capacity

Define a baseline `K(x,t)` or equivalent support-capacity field from the validated R5.17 layers.

`K(x,t)` must be interpreted as **effective human support capacity under the explicitly modeled baseline subsistence/technology assumptions**, not a unique observed population and not a fixed final historical population.

The first baseline may exclude later endogenous modifiers such as mature long-distance trade, state infrastructure, advanced technology and warfare, provided those exclusions are explicit. Later macrohistorical stages may modify effective carrying capacity dynamically.

## Required separation of quantities

R5.17 must not collapse the following into one opaque number before validation:

```text
environmental support
material resources
connectivity
strategic value
Deep opportunity
Deep hazard
environmental hazard
baseline carrying capacity
```

Derived summary classifications are permitted only if the underlying axes remain inspectable.

## Human population semantics

R5.17 does not yet need to generate the final Year-0 population trajectory. It must, however, make later demographic simulation possible.

The bridge must therefore specify:

- spatial support unit/cell/region semantics;
- units or calibrated interpretation of `K`;
- temporal interpolation/update semantics;
- treatment of inaccessible cells;
- how environmental shocks modify support;
- how later weighted population units will query the field;
- how uncertainty propagates to later ensemble runs.

If absolute-person calibration is not scientifically defensible in the first pass, R5.17 may initially produce a relative or bounded capacity proxy, but it must label it accordingly and must not call it physical population carrying capacity until calibrated.

## Provider/runtime utility rule

Before any external execution, record:

```yaml
scientific_subquestion:
why_native_arcana_is_insufficient:
provider_selected:
expected_information_gain:
canonical_role: EVIDENCE_PROVIDER_ONLY
local_long_run_allowed: true
```

Possible roles include:

- Geonomics / RangeShiftR: landscape accessibility, persistence, corridor or range connectivity;
- NEMO / CDMetaPOP: metapopulation robustness/demographic connectivity;
- SLiM / tskit / msprime / pyslim: ancestry/contact/founder-effect questions when they materially affect settlement/population interpretation.

No provider is required merely because it is available.

## Initial repository evidence

The stage begins from the following already established authorities:

- `ARCANA_WORLD_CURRENT_STATE.md` — R5.16 SEALED parent and post-R5.16 objective pointer;
- `ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md` — fixed macrohistorical destination and carrying-capacity principles;
- `CANONICAL_PHASE_AWARE_TRANSPORT_H0_PRESENT_CLOSURE_CONTRACT_v0_6D1_R3_19.md` — exact 0-ka accessible-support binding and H0 present biological closure;
- `CANONICAL_CHA2_YD_CLASS_HYDROLOGICAL_HAZARD_CONTRACT_v0_6D1_R3_20.md` — derived 15–11 ka hydrological/coastal hazard evidence at 50-year cadence;
- `DEEP_PRODUCTION_RUNTIME_CONTRACT_v0_6C.md` — Deep physical/runtime provenance and governance, with explicit prohibition on interpreting structural proxies as historical truth.

Additional stage-specific raw artifacts must be bound by exact repository path/hash before they are used numerically.

## R5.17-A immediate deliverable

Create a machine-readable capability census that lists, for every required bridge domain:

```yaml
status:
authoritative_sources:
existing_quantities:
missing_quantities:
can_reuse_without_rerun:
new_compute_required:
external_provider_required:
notes:
```

The census must identify the smallest next computation needed to move from current WorldSim evidence toward a defensible `K(x,t)`.

## Completion gate

R5.17 may be considered complete only when:

```yaml
source_binding_complete: true
human_support_layers_supported: true
material_resource_layer_supported_or_explicitly_bounded: true
deep_settlement_geography_supported: true
connectivity_strategic_geography_supported: true
baseline_K_semantics_explicit: true
population_target_imposed: false
civilization_target_imposed: false
unauthorized_canonical_mutation: false
open_blocking_scientific_gap_count: 0
```

A PASS does not imply SEALED. Any later seal decision must be explicit.

## Downstream boundary

Only after R5.17 establishes a defensible human-support/carrying-capacity foundation should the project authorize a demographic/migration stage capable of evolving population stocks or weighted population units through time. Settlement, trade, polity and warfare mechanisms remain downstream and must not be back-propagated as targets into R5.17.

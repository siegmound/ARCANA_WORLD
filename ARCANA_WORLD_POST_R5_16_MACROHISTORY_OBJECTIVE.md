# ARCANA WorldSim — Post-R5.16 Macrohistorical Reference Objective

## Authority status

```yaml
PROJECT: ARCANA WorldSim
PARENT_AUTHORITY: v0.6D1-R5.16 SEALED
DOCUMENT_ROLE: POST_SEAL_SCIENTIFIC_OBJECTIVE_CHARTER
STAGE_NUMBER: UNASSIGNED
STAGE_AUTHORIZATION: NOT_YET_GRANTED
OBJECTIVE_STATUS: AUTHORIALLY_FIXED_FOR_POST_R5_16_PLANNING
```

This document fixes the scientific destination for the post-R5.16 WorldSim program. It does not itself authorize or number the next implementation stage.

## Primary objective

Build a simulation-derived macrohistorical reference from the SEALED WorldSim state to narrative Year 0 in which the large-scale human world emerges from the simulated planet rather than being prescribed in advance.

The reference must be able to answer, with uncertainty rather than false precision:

- where sustained human population is plausible;
- where population can become dense enough to support durable settlements and civilization-scale organization;
- which locations are favored by water, food capacity, material resources, trade access, defensibility, chokepoints and other strategic geography;
- how Deep accessibility, Deep value, Deep stability and Deep hazard modify settlement and geopolitical attractiveness;
- how migration, trade, technological capacity, warfare, disease, environmental shocks, resource pressure, political fragmentation and collapse reshape population and settlement geography;
- what approximate global and regional human population is an emergent outcome by Year 0;
- what civilization/polity/trade-network landscape is a plausible emergent reference at Year 0;
- what broad macrohistorical path produced that reference state.

The simulation is intended as a **historical worldbuilding reference**, not as a claim that one exact detailed history is uniquely true.

## Population is an emergent state, not a target

The Year-0 population must not be fixed as an input merely to obtain a desired world size.

Population should emerge from coupled constraints such as:

```text
geography / climate / hydrology / ecology / resources / Deep
                         ↓
regional carrying capacity and accessibility
                         ↓
demography ↔ migration ↔ settlement ↔ trade
                         ↓
technology / institutions / infrastructure / Deep use
                         ↓
war / disease / famine / disasters / collapse / recovery
                         ↓
regional and global population trajectory
                         ↓
Year-0 population reference
```

The preferred final representation is probabilistic or ensemble-based, for example a median/reference value plus a plausible interval or quantiles. An exact single integer is not required to be canonical.

## Carrying-capacity principle

A regional effective carrying capacity `K(x,t)` is a core state variable or derived quantity. It may depend on, at minimum:

- fresh water and hydrological reliability;
- terrestrial and marine biological productivity;
- usable land and terrain;
- climate and seasonality;
- local material-resource availability;
- access to complementary resources through trade;
- technology and infrastructure;
- Deep accessibility and beneficial Deep use;
- Deep hazard;
- environmental disturbance and recovery;
- local and network-level resource pressure.

`K(x,t)` must be allowed to change through time. Trade, technology or infrastructure may increase effective support capacity; warfare, ecological degradation, disaster or network isolation may reduce it.

## Computational population representation

The simulation does **not** need to instantiate every human individual.

Permitted representations include:

- weighted population units;
- super-individuals;
- household/community agents representing many people;
- settlement-level agents;
- regional population stocks;
- hybrid adaptive representations that increase detail only where useful.

A simulated unit may therefore represent hundreds, thousands or more people when scientifically appropriate.

### Downscaled runs and scaling

It is acceptable to execute a computationally smaller simulation and infer a larger equivalent population **only if the scaling semantics are explicit and validated**.

Blind end-of-run multiplication is not sufficient where dynamics are nonlinear. At minimum the model must preserve or explicitly correct for effects whose behavior depends on absolute or local density, including where relevant:

- disease transmission;
- resource pressure;
- settlement/urbanization thresholds;
- market and trade-network effects;
- military mobilization and logistics;
- migration pressure;
- specialization and infrastructure thresholds;
- demographic stochasticity at small population size.

Preferred practice is to let weighted agents carry a `population_equivalent` during the run so that the dynamics operate on the intended demographic scale even when the computational agent count is much smaller.

## Historical resolution

The simulation does not need an exact event history for every year before Year 0.

Use adaptive temporal and spatial resolution:

- coarse steps in stable periods or low-interest regions;
- finer steps during demographic transitions, major migration, network reorganization or ecological stress;
- still finer resolution for wars, collapses or other events only when those events materially affect the macrohistorical state.

No fixed timestep hierarchy is prescribed by this objective charter; it must be selected from numerical and scientific need.

## Civilization and settlement geography

Civilization emergence must be grounded in multiple independent opportunity axes rather than one arbitrary scalar score.

Important axes include:

### Sustenance and environmental support

- water availability and reliability;
- biological productivity;
- usable land;
- climate stability and seasonality;
- coastal/marine support;
- environmental hazards.

### Material resources

- timber/biomass;
- stone;
- clay;
- salt;
- metals and ores;
- animal/marine resources;
- other geologically or ecologically useful materials available in the simulated world.

### Connectivity and trade

- coasts and navigable waterways;
- river junctions and river mouths;
- natural harbours;
- island chains;
- land corridors;
- mountain passes;
- access to complementary resource regions;
- interregional network centrality.

### Strategic geography

- straits and chokepoints;
- isthmuses;
- defensible plateaus and valleys;
- river crossings;
- protected bays;
- positions controlling resource or trade corridors;
- strategic depth and exposure.

### Deep geography

Deep must be represented as more than a generic bonus resource. Relevant dimensions include:

```yaml
DEEP_ACCESSIBILITY
DEEP_INTENSITY
DEEP_STABILITY
DEEP_RESOURCE_VALUE
DEEP_HAZARD
```

High Deep may favor some specialized settlements while making ordinary dense settlement less viable if hazard or instability is high.

## Macrohistorical dynamics

The long-term simulator should be capable, when later implementation stages authorize the corresponding mechanisms, of producing emergent transitions such as:

- migration and colonization;
- settlement growth and abandonment;
- interregional trade;
- trade hubs and chokepoint economies;
- settlement hierarchies;
- polity formation, integration, fission and succession;
- alliances and rivalries;
- warfare and conquest;
- displacement and demographic loss;
- resource competition;
- epidemic or famine shocks where justified;
- technological diffusion;
- network disruption and recovery;
- political/economic collapse;
- successor-state formation;
- civilization-scale regional systems.

These mechanisms should influence population and carrying capacity rather than exist as decorative event labels.

## Warfare principle

Warfare need not simulate every soldier or tactical action. It may operate through polity/region-level state variables such as:

- mobilizable manpower;
- logistics and supply;
- terrain and distance;
- fortification/defensibility;
- technology;
- Deep capability;
- maritime access;
- alliance support;
- political cohesion;
- attrition and demographic cost.

War outcomes must feed back into population, settlement, trade, resource access and political structure.

## Cultural and identity scope

The macrohistorical engine may use abstract, anonymous cultural, linguistic, institutional or polity identifiers when required for dynamics.

It must not invent named cultures, named religions, named languages, named ethnicities or a unique human identity merely because a macrohistorical model benefits from labels.

Named narrative materialization remains a separate authorial/scientific gate unless later explicitly authorized.

## External-runtime policy

Existing or future providers may be used when they answer a real scientific question. Relevant currently integrated tools include, where scientifically appropriate:

- Geonomics;
- SLiM;
- NEMO;
- RangeShiftR;
- CDMetaPOP;
- other justified providers.

Their likely roles include population persistence, landscape connectivity, migration, gene flow, ancestry, metapopulation robustness or related subproblems beneath the macrohistorical layer.

They are evidence/providers, not implicit canonical writers. No majority vote between engines defines ARCANA history.

### Long local executions

Long, high-resolution or multi-seed executions are explicitly permitted to run on the user's local hardware when that is the efficient way to answer the scientific question.

For such runs ARCANA should prepare and repository-track, as applicable:

- configuration;
- executable/runner;
- runtime identity and versions;
- seeds and ensemble design;
- validation checks;
- logs or summaries;
- output manifests and hashes;
- import/adjudication artifacts.

The fact that a run is too expensive for an interactive session is not a reason to omit scientifically valuable evidence.

## Ensemble and uncertainty principle

Macrohistory is expected to contain path dependence and stochasticity. Therefore one trajectory must not be treated as uniquely true merely because it was simulated first.

Where practical, use ensembles/sensitivity analysis to estimate distributions of:

- global and regional Year-0 population;
- settlement density;
- major civilization attractors;
- trade-network structure;
- polity count/scale;
- frequency and impact of wars or collapses;
- persistence of major geographic advantages.

The preferred narrative reference may use robust/median outcomes while retaining uncertainty and alternative plausible histories.

## Intended Year-0 outputs

The program should ultimately support a repository-bound Year-0 macrohistorical reference containing, at an appropriate level of precision:

- global population estimate/distribution;
- regional population distribution;
- major settlement/civilization attractor regions;
- major settlement concentrations or urban systems where they emerge;
- trade corridors, hubs and chokepoints;
- strategic/resource/Deep regions;
- abstract civilization/polity geography;
- broad conflict/alliance/expansion/collapse history where it materially explains the Year-0 state;
- uncertainty/ensemble statistics;
- provenance back to WorldSim environmental, biological and human-state authorities.

Exact names, exact borders for every year, exact individual histories and an exact single population integer are not required for objective completion.

## Completion criterion for the broader objective

The post-R5.16 macrohistorical objective is considered achieved when ARCANA can use the simulation as a defensible reference for questions such as:

> Where are large human populations most plausible at Year 0, approximately how many people can the world support under the simulated historical trajectory, which regions plausibly support civilizations or strategic powers, how are those regions connected by trade, resources and Deep, and what broad demographic/political history plausibly produced that world?

The answer must emerge from repository-tracked model state and simulation evidence rather than being imposed by authorial convenience.

## Planning rule

Do not force all of this into one implementation stage and do not predeclare an arbitrary number of phases.

For each post-R5.16 stage:

1. select one scientifically useful unresolved component of this objective;
2. inspect what sealed ARCANA state already provides;
3. determine the minimum new computation or provider evidence required;
4. authorize the stage with a repository-tracked contract;
5. preserve uncertainty and avoid false historical precision;
6. advance only when the output materially improves the final macrohistorical reference.

---

Authorial objective fixed on 2026-09-08 from SEALED v0.6D1-R5.16.

# R5.17-B7-A3F2-P7Q-PRE1

## External parent-material authority acquisition adjudication

This is a pre-authorization gate. It does not reopen P7Q, create parent material, initialize soil, install a provider, download full datasets, or run a simulation.

Repository authority: `f1ae458bbccb3fbbd8e348ffffede1b4afae3e11` for both `HEAD` and `origin/main`.

Scientific Authority Register preflight result: `PARENT_MATERIAL_ABSENT_AFTER_AUDIT__EXTERNAL_ACQUISITION_REQUIRED`.

Target temporal domain: `200 ka to 0 ka`, taken from the authoritative `P7T_TEMPORAL_SNAPSHOT_AUTHORITY` in `ARCANA_WORLD_CURRENT_STATE.md`.

## Exact gap

Required or potentially required initialization variables are: surface lithology; unconsolidated surficial-material class; genetic parent-material origin; regolith thickness; depth to bedrock; grain-size/texture; vertical layer structure; uncertainty; and a defensible 200 ka–0 ka temporal contract. Mineralogical composition, coarse fragments, bulk density, and soil/sediment thickness are optional conditioners unless a later physical model promotes them to requirements. No category is silently collapsed.

## Candidate adjudication

| Candidate | Accepted role | Temporal classification | Decision |
|---|---|---|---|
| GLiM | Surface lithology conditioner | Static bedrock approximation only; requires temporal adapter for surficial history | Partial; not parent material |
| Pelletier 2016 / ORNL 1304 | Soil/regolith/sediment thickness structural constraint | Present-day only; requires temporal adapter | Partial; no material identity |
| SoilGrids 2.0 | Present-day endpoint, calibration and qualified validation target | Present-day only | Not an initial-state or paleo provider |

GLiM documents 16 top-level lithological classes plus subclass levels and a 0.5° gridded product. Pelletier provides approximately 30-arcsecond global estimates of soil, intact-regolith and sedimentary-deposit thickness by landform. SoilGrids provides 250 m global predictions across six standard depth intervals, physical/chemical properties and prediction uncertainty. These semantics do not justify treating any one product as a complete physical parent-material profile.

## Composite result

The proposed composition—GLiM → lithology, Pelletier → thickness/depth structure, SoilGrids → present-day calibration, and ARCANA forcings → conditioning—is scientifically feasible only as a later prototype/materialization gate. It remains insufficient today because genetic surficial-material provenance, mineralogical parent-material identity, vertical layer identity, and a paleo temporal adapter are unresolved. SoilGrids is a shared-covariate modeled product, so overlapping ARCANA layers are not independent validation.

Serious supporting references are USGS World Geologic Maps/DDS60 and CGMW/OneGeology, but they are coarse geology references rather than demonstrated global physical parent-material authorities.

## Decision

`REQUIRE_ADDITIONAL_PARENT_MATERIAL_DATASET_RESEARCH`

Verdict: `PASS_P7Q_PRE1_EXTERNAL_PARENT_MATERIAL_AUTHORITY_ADJUDICATED`.

P7Q remains `SUSPENDED_PENDING_EXPLICIT_P7Q_REAUTHORIZATION`. No download, simulation, provider installation, pedogenesis, soil/regolith/parent-material materialization, or canonical mutation occurred.

## Primary sources

- GLiM publication: <https://doi.org/10.1029/2012GC004370>
- GLiM dataset: <https://doi.pangaea.de/10.1594/PANGAEA.788537>
- Pelletier publication: <https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2015MS000526>
- ORNL/NASA dataset catalog: <https://catalog.data.gov/dataset/global-1-km-gridded-thickness-of-soil-regolith-and-sedimentary-deposit-layers>
- SoilGrids official documentation: <https://docs.isric.org/globaldata/soilgrids/>
- SoilGrids layers and uncertainty: <https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html>
- SoilGrids WCS access: <https://docs.isric.org/globaldata/soilgrids/wcs.html>
- USGS World Geologic Maps: <https://www.usgs.gov/centers/central-energy-resources-science-center/science/world-geologic-maps>

# R5.17-B7-A3F2-P7Q-PRE2

## Targeted parent-material dataset completion and minimum-sufficient contract

PRE2 is a pre-authorization adjudication. It does not reopen P7Q, install a provider, download full datasets, materialize parent material, create soil, run pedogenesis, run BIOME4, or mutate the Scientific Authority Register.

Authority: `HEAD=origin/main=ac6cd67b3ec553cfa2585ff75f2e57d45d7c301d`. PRE1 is imported unchanged with decision `REQUIRE_ADDITIONAL_PARENT_MATERIAL_DATASET_RESEARCH`. Target temporal domain: `200 ka–0 ka`.

## Downstream minimum contract

The actual BIOME4/P7S evidence requires a six-layer `dz`/soil input plus `Ksat` and `WHC`; P7S also requires parent material/grain size, physical texture, weathering duration, drainage, erosion/deposition, vegetation/organic inputs and vertical profile. The minimum future parent-state contract therefore needs explicit material branch/class, genetic class for transported material, depth/regolith constraint, texture or an authorized uncertainty-bearing transform, vertical-layer contract, temporal applicability, provenance and uncertainty. Mineral-specific composition, coarse fragments and bulk density remain optional enrichment for the current minimum path.

## GUM

GUM v1.0 (Börker et al. 2018; [publication](https://doi.org/10.1002/2017GC007273), [PANGAEA dataset](https://doi.org/10.1594/PANGAEA.884822), CC-BY-3.0) contains 911,551 polygons from 126 input datasets, an approximately 0.5° gridded product and an average compiled scale near 1:3,000,000. Mapped unconsolidated sediment covers about half of global ice-free land. It supplies partial genetic/depositional authority for alluvial, aeolian, glacial, colluvial, lacustrine, coastal, marine, organic, evaporitic, pyroclastic and anthropogenic classes.

The coverage is not a complete land-surface partition. Grain size is reported for about 39% of polygons / 41.7% of area, mineralogy for about 8% of polygons, and age for about 73% of polygons. Thickness completeness and exact per-attribute provenance completeness were not quantified from available primary metadata. Laterites and other residual deposits are excluded. Therefore `no GUM polygon != exposed bedrock` and `no GUM polygon != residual parent material`; unknown, outside coverage and residual-excluded states remain distinct.

GUM grain-size information is categorical/incomplete and cannot directly become global sand/silt/clay fractions. A probabilistic class-to-texture transform is feasible only as a later authorized adapter.

## Complementary authorities

GLiM remains a surface-lithology conditioner only. It may serve the bedrock/residual branch only after an independent explicit classifier verifies that branch; GUM no-data cannot trigger the fallback. Pelletier/ORNL 1304 remains a partial present-day structural thickness/depth constraint, not material identity. GUM class plus Pelletier thickness is composable in principle, but disagreements are `DATASET_CONFLICT`, never silently resolved.

Ito–Wagai provides ten modern soil clay-mineral groups with topsoil/subsoil and Monte Carlo uncertainty; Journet provides modern clay/silt mineralogy with 12 minerals and three realizations under CC-BY-3.0. Both are optional modern mineralogical conditioners, not 200 ka parent-material authorities or independent validation of one another.

## Temporal adjudication

Bedrock lithology is a quasi-static candidate only for explicitly verified exposed bedrock. Residual regolith is temporally unresolved. Alluvial/colluvial/coastal/organic deposits are dynamic depositional materials; aeolian, glacial and pyroclastic materials are event-driven; lacustrine and other age-labelled deposits are age-constrained present surfaces. An age older than 200 ka does not prove uninterrupted occupancy of the same ARCANA cell. No complete temporal adapter is currently defensible.

## Composite result and decision

The static composition is conditionally feasible, but the dominant blockers are the 200 ka–0 ka temporal reconstruction method and an explicit residual/bedrock/unmapped classifier; texture and vertical-profile contracts also remain unresolved. The cell-level provenance schema is feasible conceptually, but no numerical uncertainty may be fabricated.

Scientific decision: `REQUIRE_P7Q_PRE3_TEMPORAL_PARENT_MATERIAL_RECONSTRUCTION_METHOD_RESEARCH`.

Verdict: `PASS_P7Q_PRE2_TARGETED_PARENT_MATERIAL_DATASET_COMPLETION_ADJUDICATED`.

P7Q remains `SUSPENDED_PENDING_EXPLICIT_P7Q_REAUTHORIZATION`. Large downloads: no. Simulation/provider/materialization: no. Scientific Authority Register mutated: no. CURRENT_STATE records PRE2 as complete and points to the temporal-method research gate.

## Additional references

- [Pelletier et al. 2016](https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2015MS000526)
- [ORNL/NASA dataset catalog](https://catalog.data.gov/dataset/global-1-km-gridded-thickness-of-soil-regolith-and-sedimentary-deposit-layers)
- [Ito & Wagai 2017](https://doi.org/10.1038/sdata.2017.103)
- [Ito & Wagai PANGAEA dataset](https://doi.org/10.1594/PANGAEA.868929)
- [Journet et al. 2014](https://doi.org/10.5194/acp-14-3801-2014)
- [USGS World Geologic Maps](https://www.usgs.gov/centers/central-energy-resources-science-center/science/world-geologic-maps)

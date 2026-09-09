# R5.17-B6 — Freshwater Physical Input Semantic Binding & Derivation Design

## Status

`DESIGN_READY_FOR_LOCAL_SEMANTIC_INSPECTION`

## Parent evidence

- R5.17-B4 confirmed that the already-bound R3.18/R3.19/R3.20 products do not contain a governed persistent freshwater-supply field.
- R5.17-B5 hash-validated the exact R3.14-bound v0.6.1 paleoclimate payloads and found a physically relevant spatial field: `precipitation_factor_relative_book[5,720,1440]`, plus 0.25-degree elevation/land geometry.

## Semantic classification

### Bind as physical input candidates

`precipitation_factor_relative_book`
: Relative spatial precipitation forcing at five paleoclimate snapshots. This may drive a later runoff/water-opportunity calculation only after its generating source semantics and snapshot chronology are confirmed.

`elevation_m`, `effective_land_mask`, `land_fraction`, `ocean_mask`, `closed_basin_below_sea_mask`, `lat`, `lon`
: High-resolution physical geometry suitable for drainage/topographic derivation after grid/time binding is explicit.

`paleo_land_mask`, `snapshot_year_before_book`
: Time-specific paleoland support and chronology for the five spatial snapshots.

### Preserve but exclude from local freshwater-supply semantics

`canonical_freshwater_pulse_sv`, `freshwater_forcing_sv`
: Freshwater forcing in Sverdrups used by the climate/ocean-circulation state. These are not local terrestrial water availability.

`cha2_flood_exposure`, `cha2_flood_memory_potential`, `cha2_megaflood_corridor`
: Event/hazard diagnostics. They are not persistent freshwater supply.

`cha2_primitive_culture_habitat_potential`
: Must not be used as a human settlement/civilization target or freshwater proxy.

`npp_factor_relative_book`
: Productivity-related forcing, not a water-supply field.

## B6 semantic gate

Before any freshwater/runoff computation, locally verify the exact R3.14-frozen source:

`src/arcana_worldsim/paleoclimate/model.py`

Expected SHA256:

`de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f`

The semantic inspector must:

1. verify the source and spatial-payload SHA256 values;
2. record exact `snapshot_year_before_book` values;
3. record per-snapshot precipitation statistics globally and on `paleo_land_mask` only;
4. inspect source text without executing it and retain bounded source excerpts around precipitation/hydrology-related identifiers;
5. determine only whether the source defines precipitation as relative forcing and whether any absolute precipitation, runoff, evapotranspiration, drainage, storage, soil-water, river/lake or recharge semantics already exist;
6. not derive freshwater supply, runoff or K during this inspection.

## Minimum downstream derivation rule

If B6 confirms only relative precipitation plus geometry, the next product may be a **relative hydroclimatic/drainage opportunity layer**, not physical freshwater volume. Calling a field physical freshwater supply requires defensible absolute water-balance semantics or an explicitly introduced and validated hydrological provider.

A native drainage graph may use elevation/land geometry, but precipitation alone is insufficient for persistent supply because evapotranspiration, infiltration/recharge, storage and routing/reliability can materially alter availability.

## Forbidden shortcuts

- no conversion of `precipitation_factor_relative_book` directly to persons/cell;
- no inversion of aridity as water supply;
- no use of CHA-2 hazard fields as persistent supply;
- no use of ocean-circulation freshwater forcing as local terrestrial supply;
- no extrapolation of five snapshots into a continuous physical water history without an explicit interpolation/forcing contract;
- no `K(x,t)` materialization in B6;
- no human population or civilization target calibration.

## Expected B6 evidence output

`R5_17_B6_PALEOCLIMATE_SEMANTIC_EVIDENCE.json`

A PASS semantic inspection authorizes design of the smallest scientifically defensible native hydrology computation; it does not itself authorize a freshwater-supply field.

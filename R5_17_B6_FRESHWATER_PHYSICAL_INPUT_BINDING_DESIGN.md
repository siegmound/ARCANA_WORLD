# R5.17-B6 — Freshwater Physical Input Semantic Binding & Derivation Design

## Status

`DESIGN_ACTIVE__NATIVE_HYDROLOGY_AUTHORITY_AUDIT_REQUIRED`

## Parent evidence

- R5.17-B4 confirmed that the already-bound R3.18/R3.19/R3.20 products do not contain a governed persistent freshwater-supply field.
- R5.17-B5 hash-validated the exact R3.14-bound v0.6.1 paleoclimate payloads and found a physically relevant spatial field: `precipitation_factor_relative_book[5,720,1440]`, plus 0.25-degree elevation/land geometry.
- `SCIENTIFIC_ENGINE_SUITABILITY_GATE.md` requires exact governed ARCANA channel/topography/hydrology authority and its generator to be inspected before any new hydrology provider is authorized.

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

## B6-H0 — Exact R3.14 paleoclimate semantic inspection

Before any freshwater/runoff computation, locally verify the exact R3.14-frozen source:

`src/arcana_worldsim/paleoclimate/model.py`

Expected SHA256:

`de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f`

The H0 semantic inspector must:

1. verify the source and spatial-payload SHA256 values;
2. record exact `snapshot_year_before_book` values;
3. record per-snapshot precipitation statistics globally and on `paleo_land_mask` only;
4. inspect source text without executing it and retain bounded source excerpts around precipitation/hydrology-related identifiers;
5. determine only whether the source defines precipitation as relative forcing and whether absolute precipitation, runoff, evapotranspiration, drainage, storage, soil-water, river/lake or recharge semantics already exist;
6. not derive freshwater supply, runoff or K during this inspection.

Expected H0 evidence output:

`R5_17_B6_PALEOCLIMATE_SEMANTIC_EVIDENCE.json`

H0 evidence is semantic discovery, not completion of B6.

## B6-H1 — Existing ARCANA native hydrology discovery

H0 source inspection shows that the R3.14-frozen paleoclimate model consumes:

`inputs/v0_5_5I_SEALED/channel_hydrology_state_I.npz`

with at least the following identifiers:

- `mean_discharge_m3_s`
- `drainage_area_km2`
- `receiver_flat`
- `lake_candidate_mask`
- `depression_depth_m`

Therefore B6 must not infer that hydrology is missing from the absence of runoff/water-balance equations in `paleoclimate/model.py` alone.

The governed H1 tool is:

`R5_17_B6_H1_LOCATE_AND_INSPECT_NATIVE_HYDROLOGY.py`

H1 must:

1. locate every direct or archived `channel_hydrology_state_I.npz` candidate under the authorized local search root;
2. calculate SHA256 identity for every candidate without assuming an authority hash in advance;
3. inspect NPZ contents with `allow_pickle=False`;
4. record array names, shapes, dtypes, finite statistics and presence of the hydrological fields above;
5. identify duplicate versus divergent payload hashes;
6. not adjudicate canonical authority merely from filename/path coincidence;
7. not execute historical generators;
8. not derive freshwater support, runoff, reliability or K.

Expected H1 evidence output:

`R5_17_B6_H1_NATIVE_HYDROLOGY_DISCOVERY.json`

A PASS H1 means only that candidate native hydrology payloads have been structurally inspected.

## B6-H2 — Authority lineage and generator semantic audit

After H1, B6 must establish which candidate belongs to the governed v0.5.5I/R3.14 lineage and locate the exact code/configuration that generated it.

H2 must determine, as evidence supports:

- whether `mean_discharge_m3_s` is a physical volumetric discharge or a calibrated/normalized proxy;
- how `drainage_area_km2` is constructed;
- how `receiver_flat` encodes routing and outlet/sink behavior;
- how `lake_candidate_mask` and `depression_depth_m` are derived;
- whether precipitation, evapotranspiration, runoff coefficients, infiltration, recharge, storage, snow/ice melt or groundwater participate in discharge generation;
- spatial resolution, temporal meaning and book-era/paleoclimate applicability;
- whether discharge is static geometry-derived evidence or time-varying hydrological state.

No field may be promoted to persistent human freshwater supply until these semantics are adjudicated.

## Scientific Engine Suitability Gate after H2

Only after native authority sufficiency is known may B6 select a computation path:

```text
A. governed ARCANA hydrology already sufficient
   -> REUSE_CANONICAL_ARCANA

B. governed topology/drainage sufficient but bounded derivation missing
   -> reuse authority + minimum specialist derivation

C. physical water balance/reliability genuinely missing
   -> evaluate dedicated hydrology provider

D. no suitable provider can preserve ARCANA semantics
   -> minimum custom ARCANA hydrology implementation
```

Candidate tools such as drainage-routing libraries or distributed hydrology engines remain candidates until explicitly audited, version-pinned and scientifically selected.

## Minimum downstream derivation rule

If B6 ultimately confirms only relative precipitation plus geometry/topology, the next product may be a **relative hydroclimatic/drainage opportunity layer**, not physical freshwater volume.

Calling a field physical freshwater supply requires defensible absolute water-balance semantics or an explicitly introduced and validated hydrological provider. A native drainage graph and even a book-era discharge layer do not automatically establish paleoclimate freshwater reliability through time.

## Forbidden shortcuts

- no conversion of `precipitation_factor_relative_book` directly to persons/cell;
- no assumption that `mean_discharge_m3_s` is canonical freshwater supply before generator/units semantics are verified;
- no inversion of aridity as water supply;
- no use of CHA-2 hazard fields as persistent supply;
- no use of ocean-circulation freshwater forcing as local terrestrial supply;
- no extrapolation of five snapshots or a static channel state into continuous physical water history without an explicit contract;
- no `K(x,t)` materialization in B6;
- no human population or civilization target calibration.

## B6 completion requirement

B6 is complete only when:

1. H0 paleoclimate semantics are captured;
2. H1 native hydrology candidates are discovered/inspected;
3. H2 authority lineage and generator semantics are adjudicated;
4. the Scientific Engine Suitability Gate records the selected next path and rejected alternatives;
5. no freshwater-support or K field has been silently fabricated.

A PASS H0 or H1 alone does not complete B6 and does not authorize a new hydrology provider.

# P7S historical climate-provider adjudication

## Decision

`AUTHORIZE_BOUNDED_HIERARCHICAL_CLIMATE_BINDING_PROOF`

This authorizes only a deterministic, proof-cell-limited comparison/binding exercise. It does not approve a provider hierarchy or authorize global climate acquisition, P7S historical replay, or BIOME4 production. The 65-cell overlap statistics are intentionally pending: no candidate climate payload was acquired for this adjudication.

## Provider findings

| Candidate | Native support | Authority class | Governed-anchor result | Main limitation |
|---|---|---|---|---|
| Krapp et al. 2021 | 800 ka to present; 1 kyr; 0.5°; monthly temperature, precipitation, cloud and bioclimatics | Statistical reconstruction/emulator based on HadCM3 snapshots, CO₂/orbital/surface-type forcing, bias-corrected to present climate | All 12 anchors lie on the documented 1-kyr time lattice. The present slice is not thereby identical to ARCANA's reconstructed 0-ka endpoint. | It is not direct transient GCM output. Published monthly-precipitation unit is mm/year and needs semantic reconciliation with P7S monthly mm before annual-total comparisons. |
| Beyer/Krapp/Manica 2020 | 120 ka to pre-industrial modern; 2 kyr from 120–22 ka and 1 kyr thereafter; 0.5°; monthly mean temperature and precipitation | Direct GCM-derived (HadCM3, with HadAM3H dynamic correction over the last 21 ka), then delta-bias-corrected/downscaled | Exact: 120, 20, 15, 14, 13, 12, 11, 10, 5, 0 ka. 125 ka: nearby-only at 120 ka. 200 ka: absent. | Not a continuous annual transient GCM; modern reference is observationally anchored and is not the ARCANA endpoint. One global NetCDF; subset/size not verified. |
| CHELSA-TraCE21k | 21 ka to present; 100-year time steps; 30 arcsec (~1 km); monthly mean `tas` and precipitation | Downscaled transient CCSM3 TraCE-21k model with terrain and evolving glacial/palaeo-orography | Exact: 20, 15, 14, 13, 12, 11, 10, 5, 0 ka. Outside scope/unavailable at 120, 125, 200 ka. | Fine native grid is not permission to upsample ARCANA. Precipitation includes liquid and solid phases; 0 BP is a 1950 reference while additional output extends to 1990. Actual selective-transfer bytes and package-license interpretation need confirmation. |

The Krapp paper explicitly describes a statistical extension of HadCM3 snapshots and says the direct-GCM-derived 120-ka product is preferred for the last glacial cycle; the papers therefore support different temporal roles, not one interchangeable authority class. [Krapp et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8397735/) [Beyer et al. 2020](https://www.nature.com/articles/s41597-020-0552-1)

CHELSA's paper and model documentation describe CCSM3 TraCE-21k downscaling, 100-year time steps, dynamic terrain/glacier inputs, and 30-arcsec climate fields. [Karger et al. 2023](https://cp.copernicus.org/articles/19/439/2023/) [CHELSA model documentation](https://www.chelsa-climate.org/models/chelsa-trace21k) [CHELSA dataset metadata](https://www.chelsa-climate.org/datasets/chelsa-trace21k-centennial)

## P7S feature semantics

- Temperature: retain monthly mean air temperature; calculate the arithmetic mean of the 12 monthly means and convert K to °C if needed. The P7S local endpoint arrays confirm this agrees with its `annual_temperature_c` field to float32 tolerance. Do not substitute minimum or maximum temperature.
- Annual precipitation: P7S endpoint `annual_precipitation_mm_yr` equals the sum of its 12 `monthly_precipitation_mm` values to float32 tolerance. Reconcile each provider's monthly units/aggregation semantics before comparing annual totals.
- Seasonality: verified against the local endpoint payload as population standard deviation (`ddof=0`) of the 12 monthly precipitation values divided by their arithmetic mean. It is dimensionless, has no ×100 factor, and is invariant under uniform positive unit conversion. Derive it from provider monthly values; do not assume a provider BIO15 field shares this exact scale.

## Architecture and overlap

The hierarchical arrangement (Krapp for 200/125 ka; Beyer for 120 ka through the pre-industrial endpoint; CHELSA as recent-period independent model-chain cross-check) is only a candidate. No hierarchy is approved until the bounded overlap comparison reports mean bias, median absolute difference, RMSE, correlation where meaningful, spatial/regional signatures, and precipitation relative differences for shared native timestamps. The same 65 proof-cell geography should be used where each source has a valid native-support mapping. No interpolation/resampling is authorized; unsupported cells must remain excluded and reported.

Neither absolute provider fields nor provider anomalies added to the ARCANA 0-ka baseline are selected yet. The next proof must compare both against the bound ARCANA endpoint without replacing it. Endpoint compatibility is not implied by a product's “present” or “0 BP” label.

## Bounded acquisition gate

For the 65 existing proof cells, requested monthly temperature and precipitation at 12 Krapp, 10 Beyer and 9 CHELSA anchor slices have a raw float32 lower bound of 193,440 bytes (~0.19 MB), excluding masks, coordinates, metadata, compression and storage chunk amplification. Remote subsetting is not verified for Krapp or Beyer; CHELSA is distributed as COG, but selective range reads on the exact endpoint have not been tested. The authorized proof has a hard 50 MiB transfer cap. Read exact file names, object sizes, license and range/subset metadata before requests. If selective extraction is unavailable or would exceed the cap, stop; whole-dataset fallback is not authorized. Published pastclim Krapp monthly files total about 3.6 GB (temperature plus precipitation); this is a reference repackaging size, not a confirmed original-OSF transfer estimate. Exact Beyer and CHELSA full payload sizes remain unverified.

Licensing also needs a source-record check before acquisition: CHELSA's catalogue identifies CC0, while paper/EnviDat records report CC BY terms; use the applicable data-package terms, not an assumed license. No provider payload has been acquired here.

## Governance and next action

Historical runoff, historical topography, cloud, humidity and wind are not justified for acquisition by this minimum P7S proof. WHC transferability remains unresolved; the endpoint BIOME4 sensitivity labels remain conditional diagnostics because sunshine was synthetic fixed 60%, and their NPP values are not ecological authority.

`historical_p7s_replay_executed = false`  
`historical_p7s_replay_authorized = false`  
`BIOME4_production_executed = false`  
`physical_soil_materialized = false`  
`P7Q_reopened = false`  
`scientific_authority_register_mutated = false`

**Next action:** `RUN_BOUNDED_65_CELL_CLIMATE_OVERLAP_AND_0KA_ENDPOINT_COMPARISON_WITH_50MIB_TRANSFER_CAP`

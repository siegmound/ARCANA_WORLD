# D3.2C RAW / Event-History Output Schema

## `paleogeographic_barrier_history_state.npz`

Carries the complete +20 Myr endpoint state and merged +5→+20 Myr snapshot history:

- root/final species IDs;
- deme IDs and current species assignments;
- root-species and guild indices;
- grid coordinates;
- snapshot times, richness, total population;
- endpoint population rasters;
- ecological traits and additive variance;
- resource-niche traits and variance;
- generation-time proxies;
- ecological, genomic and combined intrinsic RI;
- isolation clocks;
- contact connectivity;
- extended trait distance.

## `PALEOGEOGRAPHIC_EVENT_CATALOG.json`

Each event cluster exports plate code, transition direction, cell count, age range/mean and semantic status. These rows are derived endpoint-constrained reconstruction metadata, not observations.

## Biological event files

- `speciation_events_5_20myr.json`
- `deme_fission_events_5_20myr.json`
- `species_registry.json`
- `founder_viability_state.json`
- `founder_viability_stats.json`
- `vicariance_persistence_state.json`
- `vicariance_calibration_stats.json`

## Audit / calibration evidence

- `PALEOGEOGRAPHIC_HISTORY_AUDIT.json`
- `EVENT_HISTORY_PHYSICAL_SENSITIVITY.json`
- `event_history_sensitivity/EVENT_HISTORY_BIOLOGICAL_SENSITIVITY.json`
- `convergence_12_5/CRITICAL_WINDOW_CONVERGENCE_SUMMARY.json`
- `RPT_004_PROVIDER_SENSITIVITY_DIAGNOSTIC.json`
- `D3_2C_FINAL_CALIBRATION.json`
- `D3_2C_FORMAL_AUDIT.json`

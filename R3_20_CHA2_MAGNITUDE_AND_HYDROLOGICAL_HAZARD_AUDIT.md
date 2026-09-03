# R3.20 CHA-2 magnitude and hydrological-hazard audit — R1 repaired semantics

R3.20 is deliberately an audit/derived-physics stage. It does **not** recalibrate the sealed CHA-2 unless the repaired live magnitude gate fails.

## R1 correction
The first candidate audit conflated two internal model diagnostics with external Younger-Dryas reference quantities:

1. `global_temperature_anomaly_c` is a low-order scalar state used in the sealed climate/carbon/ice equations, not an area-weighted global-mean surface-temperature reconstruction. Its magnitude is therefore diagnostic only. The physically resolved regional temperature raster remains the hard magnitude authority.
2. `>=90%` baseline overturning is near-complete circulation recovery, not the end of the strong event. Event exit is now the first state after the contiguous <80% baseline suppression episode containing the overturning minimum. The 90% recovery is reported diagnostically and may be searched on exact sealed 100-y anchors after the 15-11 ka core.

The R3.19 parent parser is also repaired to use `formal_audit_checks` as the authoritative 73/73 field, with a backward-compatible fallback.

## Reference interpretation
The terrestrial Younger Dryas is conventionally ~12.9–11.7 ka and is characterized by a pronounced North Atlantic/Northern Hemisphere response, AMOC/circulation changes, and strongly heterogeneous hydroclimate. A transient-model study reproducing YD-like conditions reports ~2–4 C cooling over the North Atlantic/Europe and ~0.6 C simulated global-mean cooling, underscoring that regional and global metrics are distinct quantities rather than interchangeable thresholds.

The ARCANA freshwater pulse itself remains unchanged and peaks near 12.9 ka. R3.20 tests the resulting sealed response rather than tuning it to human outcomes.

## Hydrological hazard
Hydrological hazard remains derived from changes in effective moisture, wetland forage, exact land support and ecosystem resource state. It is population-free. The layer may later explain why distant communities experience severe water-related disruptions, but no community, myth or religion is used to create or tune those hazards.

## External reference anchors
- Younger Dryas timing ~12.9–11.7 ka and abrupt North Atlantic cooling: Earth-Science Reviews 2024, *Response of North American ice sheets to the Younger Dryas cold reversal (12.9 to 11.7 ka)*.
- Heterogeneous hydroclimate, North Atlantic/European cooling ~2–4 C, simulated global-mean cooling ~0.6 C: Quaternary Science Reviews 2018, *The global hydroclimate response during the Younger Dryas event*.
- Strong evidence for AMOC changes associated with the Younger Dryas: Annual Review of Marine Science 2017, *The Atlantic Meridional Overturning Circulation and Abrupt Climate Change*.

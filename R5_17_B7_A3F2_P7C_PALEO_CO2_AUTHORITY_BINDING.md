# R5.17-B7-A3F2-P7C

## Decision

**PALEO_CO2_AUTHORITY_READY_WITH_INTERPOLATION**. The exact P7T registry is bound to the cached NOAA/NCEI physical CO₂ authority over the 200 ka -> 0 ka human-support domain.

The selected policy is `RELATIVE_NATURAL_FORCING_DATUM_ALIGNMENT` with a 200-year modeling offset: `external_age_BP = (arcana_age_ka * 1000) + 200`. This uses the Earth preindustrial 1750 CE convention as a modeling datum only; ARCANA 0 ka remains a relative simulation endpoint, not a literal Earth calendar identity.

All 12 snapshots are within NOAA coverage with no extrapolation. The anthropogenic tail is excluded. CO₂ values are bound in the companion CSV for P7S/BIOME4 routing; no BIOME4 scientific run, physical NPP, soil, Madingley, animal resource support, `K(x,t)`, state/index update, staging, commit, or push occurred. `AQUATIC_MARINE_RESOURCE_SUPPORT = NOT_MATERIALIZED`.

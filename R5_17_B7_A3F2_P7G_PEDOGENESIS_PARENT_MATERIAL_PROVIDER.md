# R5.17-B7-A3F2-P7G

## Decision

**BLOCKED_PARENT_MATERIAL_AUTHORITY_INSUFFICIENT**. ARCANA has governed elevation/land geometry and environmental/hydrological proxies, but no physical lithology/material composition, grain-size fractions, regolith depth, bulk density, or initial vertical profile. Those non-equivalent fields are not translated into soil by this gate.

SoilGen3.8.2 can evolve an initialized 1-D soil/parent profile but is not shown to create ARCANA's missing parent state. LORICA-family models evolve initialized soilscape layers and material. SaLEM is a specialized periglacial/site-regional regolith model and is not a universal world provider. Rosetta3 remains downstream of physical texture/profile authority.

No provider was run and no soil or parent-material arrays were materialized. Recommended next operation: `TARGETED_PARENT_MATERIAL_AUTHORITY_RECOVERY_FOR_SYNTHETIC_WORLD_REGIMES`.

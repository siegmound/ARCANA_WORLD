# R5.17-B7-A3F2-P7S physical-soil provider and pedogenesis adjudication

## Decision

`AUTHORIZE_TARGETED_PHYSICAL_SOIL_PROVIDER_ACQUISITION_AND_MODEL_PROOF`

## Verdict

`PASS_PROVIDER_SCHEMA_ADJUDICATION__REQUIRE_MODEL_AND_INITIALIZATION_PROOF_BEFORE_PRODUCTION`

The minimum defensible architecture is:

`HRAB sparse constraints + bounded SoilGrids 2.0 endpoint/calibration authority + bounded HWSD v2 cross-check + existing ARCANA climate/hydrology/topography/time authorities + a model-proof implementation that preserves unknown initial soil states.`

SoilGrids is the preferred present-endpoint physical authority. Official documentation describes global 250 m predictions at the six standard depth intervals (0–5, 5–15, 15–30, 30–60, 60–100, 100–200 cm), with texture fractions, bulk density, coarse fragments, pH, CEC, carbon, nitrogen, and volumetric-water products plus prediction quantiles. It is a modelled present-day map and is not a paleosol state or a 200 ka initializer. Bounded access is available through the official ISRIC WCS.

HiHydroSoil v2.0 is useful as a hydraulic/pedotransfer parameterization at 250 m, including Mualem–van Genuchten and water-retention quantities. It is substantially dependent on SoilGrids inputs and must not be counted as independent evidence. HWSD v2.0 is a useful independent, coarser cross-check with seven layers from 0–20 through 150–200 cm, rootable depth, AWC, USDA texture and reference bulk density. It must retain its approximately 1 km native support and must not be upscaled into 250 m information. OpenLandMap is deferred because it is layer-dependent and composite/modelled; no required property currently justifies adding it to the minimum stack.

## Temporal and initialization adjudication

The accepted initialization is hybrid: use an authorized parent-material transfer only where HRAB supports it, retain `UNKNOWN_INITIAL_SOIL` elsewhere, and calibrate/validate against the modern endpoint. Present SoilGrids or HWSD values must not be copied backward to 200 ka. Formation age plus present occurrence does not imply continuous persistence. Where HRAB transition timing is unknown, the soil state remains unknown or its uncertainty widens.

A pedogenesis/state-evolution model is required before production. A minimal transferable state-space or process-based model is preferable to an elaborate uninitialized simulator. It must connect climate, hydrology, topography, sparse parent constraints, profile/depth evolution, hydraulic derivation and uncertainty across 200 ka → 0 ka. This model and its oldest-time initialization are not yet demonstrated.

## P7S consumability and blockers

P7S can consume the HRAB sparse interface **PARTIALLY**: endpoint, age-class, formation-refined, event-bounded, unknown and outside-scope states can be passed with provenance and masks. That interface does not itself create physical soil. Direct physical texture, bulk density, rootable/depth profile, hydraulic state and validated historical soil authority remain absent.

Primary blockers are the model gap and initialization gap. Secondary blockers are unresolved temporal parent-material transitions and unbound targeted present-endpoint payloads. No large provider payload was downloaded; no physical soil, BIOME4, Madingley, NPP, forward evolution, commit or push was performed.

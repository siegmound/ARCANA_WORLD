# R5.17-B6 - Freshwater / Paleohydrology Completion Register

## Status

STAGE: v0.6D1-R5.17
SUBPHASE: R5.17-B6
STATUS: COMPLETED
SEALED: false
CANONICAL_MUTATION: false
K_X_T_MATERIALIZED: false
NEXT_SUBPHASE: R5.17-B7

B6 is a substantive completed milestone inside active R5.17.
It is deliberately not promoted to a separate SEALED milestone.

## Scientific purpose

Recover and bind the physical hydrology required to derive natural
freshwater access and reliability without interpreting climate proxies,
forage fields, hazard indices, or human settlement states as freshwater
supply.

## Completed progression

### H1-H4 - native hydrology recovery and provenance

The B6 hydrology discovery/provenance chain recovered and adjudicated:

- native hydrology artifacts;
- root/source provenance;
- generator semantics;
- export sufficiency;
- the distinction between physical hydrology and environmental proxies.

### D1 - canonical hydrology replay contract

Established the governed replay contract for recovering native channel
hydrology instead of inventing a new water model.

### D2 family - canonical paleohydrology input binding

Bound and reconciled the paleoclimate, seasonal-climate, shoreline and
hydrology inputs required by the replay.

The D2 investigation included:

- seasonal-climate baseline identity and promotion;
- canonical seasonal reconstruction;
- shoreline land-mask recovery;
- replay diagnosis;
- source/stage-aligned reconstruction;
- no promotion by arbitrary replay tolerance.

Intermediate BLOCKED/diagnostic states are retained as provenance but are
superseded by the later successful replay path.

### D3 / D3R - canonical paleohydrology replay

The final replay path recovered the coast-state contract required by the
historical native hydrology generator and materialized governed
paleohydrology snapshots.

### D4 - freshwater access and reliability

Terminal B6 authority:

STATUS: PASS_R517_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY_MATERIALIZED
FRESHWATER_SUPPORT_MATERIALIZED: True
HYDROLOGICAL_RELIABILITY_MATERIALIZED: True
K_X_T_MATERIALIZED: False

B6 therefore supplies the physical freshwater component needed by the
human-support foundation while keeping K(x,t) downstream.

## Semantic guardrails retained

The following equivalences remain forbidden:

wetland_forage               != freshwater supply
aridity_index                 != freshwater supply
freshwater_forcing_sv         != local freshwater access
precipitation alone           != freshwater access
R3.20 hydrological hazard     != freshwater availability
R3.20 flood/drying indices    != water quantity

R3.20 remains useful only as independent hydrological/hazard semantic
cross-validation.

## B6 -> B7 boundary

B6 does not materialize:

human-edible biological food
calories
persons/cell
K(x,t)
settlement density
agriculture
trade
polity
civilization

Those remain downstream.

## Tracked B6 authority surface at transition

- R5_17_B6_COMPLETION_REGISTER.md
- R5_17_B6_D1_CANONICAL_HYDROLOGY_REPLAY_CONTRACT.json
- R5_17_B6_D1_EXTRACT_CANONICAL_HYDROLOGY_REPLAY_CONTRACT.py
- R5_17_B6_D2_BIND_CANONICAL_PALEOHYDROLOGY_INPUTS.py
- R5_17_B6_D2_CANONICAL_PALEOHYDROLOGY_INPUT_BINDING.json
- R5_17_B6_D2A_ADJUDICATE_ALTERNATE_SEASONAL_BASELINE_IDENTITY.py
- R5_17_B6_D2A_SEASONAL_BASELINE_IDENTITY_ADJUDICATION.json
- R5_17_B6_D2B_RECOVER_V055I_SEASONAL_PROMOTION_AUTHORITY.py
- R5_17_B6_D2B_V055I_SEASONAL_PROMOTION_AUTHORITY.json
- R5_17_B6_D2C_CANONICAL_SEASONAL_BASELINE_RECONSTRUCTION_PREFLIGHT.json
- R5_17_B6_D2C_PREPARE_CANONICAL_SEASONAL_BASELINE_RECONSTRUCTION.py
- R5_17_B6_D2C1_ADJUDICATE_SHORELINE_LAND_MASK_ADAPTER.py
- R5_17_B6_D2C1_SHORELINE_LAND_MASK_ADAPTER_ADJUDICATION.json
- R5_17_B6_D2D_RECONSTRUCTED/seasonal_climate_state_I_RECONSTRUCTED.npz
- R5_17_B6_D2D_SEASONAL_GENERATOR_REPLAY_AND_I_RECONSTRUCTION.json
- R5_17_B6_D2D_VALIDATE_SEASONAL_GENERATOR_AND_RECONSTRUCT_I.py
- R5_17_B6_D2D1_EXACT_SEASONAL_GENERATOR_RUNTIME_BINDING.json
- R5_17_B6_D2D1_RESOLVE_EXACT_SEASONAL_GENERATOR_RUNTIME_BINDING.py
- R5_17_B6_D2D2_DIAGNOSE_F_REPLAY_NONEXACTNESS.py
- R5_17_B6_D2D2_F_REPLAY_NONEXACTNESS_DIAGNOSTICS.json
- R5_17_B6_D2D3_SERIALIZED_MARGIN_REPLAY_AND_I_RECONSTRUCTION.json
- R5_17_B6_D2D3_VALIDATE_SERIALIZED_MARGIN_REPLAY_AND_RECONSTRUCT_I.py
- R5_17_B6_D2D4_FLOAT32_ULP_EQUIVALENCE_AND_I_RECONSTRUCTION.json
- R5_17_B6_D2D4_FLOAT32_ULP_EQUIVALENCE_AND_I_RECONSTRUCTION.py
- R5_17_B6_D2D5_FULL_IN_MEMORY_F_CHAIN_REPLAY_AND_I_RECONSTRUCTION.json
- R5_17_B6_D2D5_FULL_IN_MEMORY_F_CHAIN_REPLAY_AND_I_RECONSTRUCTION.py
- R5_17_B6_D2R_RECOVER_SEASONAL_CLIMATE_BASELINE.py
- R5_17_B6_D2R_SEASONAL_CLIMATE_BASELINE_RECOVERY.json
- R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY.json
- R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY.py
- R5_17_B6_D3_RECONSTRUCTED/channel_hydrology_state_I_RECONSTRUCTED.npz
- R5_17_B6_D3_RECONSTRUCTED/channel_hydrology_state_m012000ybp_RECONSTRUCTED.npz
- R5_17_B6_D3_RECONSTRUCTED/channel_hydrology_state_m012900ybp_RECONSTRUCTED.npz
- R5_17_B6_D3_RECONSTRUCTED/channel_hydrology_state_m014000ybp_RECONSTRUCTED.npz
- R5_17_B6_D3_RECONSTRUCTED/channel_hydrology_state_m021000ybp_RECONSTRUCTED.npz
- R5_17_B6_D3_RECONSTRUCTED/channel_hydrology_state_p000000y_RECONSTRUCTED.npz
- R5_17_B6_D3R_I_COAST_CONTRACT_AND_REPLAY.json
- R5_17_B6_D3R_RESOLVE_I_COAST_CONTRACT_AND_REPLAY.py
- R5_17_B6_D4_DERIVE_FRESHWATER_ACCESS_AND_RELIABILITY.py
- R5_17_B6_D4_DERIVED/freshwater_support_reliability_bundle.npz
- R5_17_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY.json
- R5_17_B6_EVIDENCE_MANIFEST.json
- R5_17_B6_FRESHWATER_PHYSICAL_INPUT_BINDING_DESIGN.md
- R5_17_B6_H1_LOCATE_AND_INSPECT_NATIVE_HYDROLOGY.py
- R5_17_B6_H1_NATIVE_HYDROLOGY_DISCOVERY.json
- R5_17_B6_H1_NATIVE_HYDROLOGY_DISCOVERY_ARCANAWORLD.json
- R5_17_B6_H2_AUDIT_NATIVE_HYDROLOGY_PROVENANCE.py
- R5_17_B6_H2_NATIVE_HYDROLOGY_PROVENANCE.json
- R5_17_B6_H3_AUDIT_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS.py
- R5_17_B6_H3_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS.json
- R5_17_B6_H4_ADJUDICATE_EXACT_EXPORT_AND_PHYSICAL_SUFFICIENCY.py
- R5_17_B6_H4_ADJUDICATE_V055I_EXPORT_AND_PHYSICAL_SUFFICIENCY.py
- R5_17_B6_H4_V055I_EXPORT_AND_PHYSICAL_SUFFICIENCY.json
- R5_17_B6_INSPECT_PALEOCLIMATE_SEMANTICS.py
- R5_17_B6_LOCATE_AND_INSPECT_PALEOCLIMATE_SEMANTICS.py
- R5_17_B6_PALEOCLIMATE_SEMANTIC_EVIDENCE.json
- R5_17_B6_RECOVER_AND_OPEN_B7_BUILD_INDEX_WINPS51_V4.ps1
- R5_17_B6_RECOVER_OPEN_B7_INDEX_COMPACT_EVIDENCE_WINPS51_V5.ps1
- R5_17_B6_RECOVER_OPEN_B7_INDEX_COMPACT_EVIDENCE_WINPS51_V6.ps1
- R5_17_B6_RECOVER_OPEN_B7_INDEX_COMPACT_EVIDENCE_WINPS51_V7.ps1
- R5_17_B6_RECOVER_OPEN_B7_INDEX_COMPACT_EVIDENCE_WINPS51_V8.ps1

## Disposition

B6_COMPLETION_DECISION: AUTHORIZE_R5_17_B7
NEXT_SCOPE: NATURAL_BIOLOGICAL_FOOD_SUPPORT
MICRO_SEAL_CREATED: false

# ARCANA WorldSim Scientific Authority Register

Governed cross-cutting authority inventory. It records only evidenced state and its semantic ceiling; it does not create science.

## Mandatory preflight

1. `REQUESTED_SCIENTIFIC_STATE`
2. `LOOKUP_DOMAIN_IN_REGISTER`
3. `IF_PRESENT_CHECK_AUTHORITY_STATUS_AND_SEMANTIC_CEILING`
4. `IF_SUFFICIENT_REUSE_OR_REUSE_WITH_ADAPTER`
5. `IF_INSUFFICIENT_DEFINE_EXACT_GAP`
6. `IF_UNRESOLVED_PERFORM_TARGETED_RECOVERY`
7. `ONLY_AFTER_ADJUDICATION_GATE_NEW_PROVIDER_OR_SIMULATION`

## Governance rules

- **RULE_1_PRESENCE_NOT_EQUAL_SUFFICIENCY** — Presence of authority does not imply sufficiency for every downstream use.
- **RULE_2_UPSTREAM_NOT_EQUAL_DOWNSTREAM_PROPERTY** — An upstream authority cannot be silently reinterpreted as a downstream physical property.
- **RULE_3_ABSENT_REQUIRES_AUDIT** — ABSENT_AFTER_AUDIT requires a sufficiently scoped recovery/audit and provenance evidence.
- **RULE_4_REGISTER_PREFLIGHT_REQUIRED** — Consult this register before broad recovery, provider introduction, new model, simulation, or materialization.
- **RULE_5_REUSE_BEFORE_RECOMPUTE** — Prefer reusable governed authority when its semantic ceiling covers the consumer.
- **RULE_6_SEMANTIC_CEILING_IS_BINDING** — No downstream stage may infer beyond the registered semantic ceiling without an explicit gate.
- **RULE_7_PARTIAL_AUTHORITY_REQUIRES_GAP_DEFINITION** — PARTIAL_AUTHORITY or SEMANTICALLY_LIMITED requires an exact gap definition before a new provider or simulation.
- **RULE_8_NEW_SIMULATION_REQUIRES_REGISTER_EVIDENCE** — A new simulation for a covered domain requires explicit adjudication of insufficiency.

## Domain inventory

| Domain | Primary authority status | Reuse disposition | Semantic ceiling |
|---|---|---|---|
| PALEOGEOGRAPHY | DIRECT_AUTHORITY | REUSE_ALLOWED | land/ocean endpoint state; derived transition organization |
| PLATE_KINEMATICS | DIRECT_AUTHORITY | REUSE_ALLOWED | plate/cell identity; endpoint-constrained transitions; 210–0 Ma kinematic scaffold |
| SHORELINE_LAND_OCEAN | DIRECT_AUTHORITY | REUSE_ALLOWED | shoreline/accessibility condition |
| CLIMATE | DIRECT_AUTHORITY | REUSE_ALLOWED | climatic forcing and diagnostics |
| PALEOCLIMATE | DIRECT_AUTHORITY | REUSE_ALLOWED | recent paleoclimate history |
| HYDROLOGY | DIRECT_AUTHORITY | REUSE_ALLOWED | paleohydrological reconstruction |
| PALEOHYDROLOGY | DIRECT_AUTHORITY | REUSE_ALLOWED | replayed hydrological state |
| FRESHWATER | DIRECT_AUTHORITY | REUSE_ALLOWED | freshwater support; hydrological reliability |
| HYDROLOGICAL_HAZARD | DIRECT_AUTHORITY | REUSE_ALLOWED | hazard ranking |
| FLORA | DIRECT_AUTHORITY | REUSE_ALLOWED | plant trophic support |
| VEGETATION | DIRECT_AUTHORITY | REUSE_ALLOWED | ecological/forage support |
| PLANT_ECOLOGY | DIRECT_AUTHORITY | REUSE_ALLOWED | plant ecological support |
| PLANT_TROPHIC_SUPPORT | DIRECT_AUTHORITY | REUSE_ALLOWED | plant trophic resource support |
| FAUNA | DIRECT_AUTHORITY | REUSE_ALLOWED | lineage and component identity |
| ANIMAL_ECOLOGY | DIRECT_AUTHORITY | REUSE_ALLOWED | ecological/functional traits |
| BIODIVERSITY | DIRECT_AUTHORITY | REUSE_ALLOWED | lineage existence/identity |
| SPECIES_EVOLUTION | DIRECT_AUTHORITY | REUSE_ALLOWED | existence intervals |
| SPECIES_REGISTRY | DIRECT_AUTHORITY | REUSE_ALLOWED | identity continuity |
| NPP_PRODUCTIVITY | PROXY_ONLY | NOT_REQUIRED_CURRENT_SCOPE | relative/normalized productivity proxy |
| GEOLOGY | ABSENT_AFTER_AUDIT | REQUIRES_TARGETED_RECOVERY | none |
| LITHOLOGY | ABSENT_AFTER_AUDIT | REQUIRES_TARGETED_RECOVERY | none |
| CRUSTAL_STATE | UNRESOLVED | REQUIRES_TARGETED_RECOVERY | kinematic conditioning only |
| PARENT_MATERIAL | ABSENT_AFTER_AUDIT | REQUIRES_TARGETED_RECOVERY | none |
| REGOLITH | ABSENT_AFTER_AUDIT | REQUIRES_TARGETED_RECOVERY | none |
| SOIL_PHYSICAL | ABSENT_AFTER_AUDIT | REQUIRES_TARGETED_RECOVERY | none |
| SOIL_CARBON | PROXY_ONLY | BLOCKED | proxy/process conditioning |
| WEATHERING | PROXY_ONLY | BLOCKED | process/proxy signal |
| BARRIERS | DIRECT_AUTHORITY | REUSE_ALLOWED | barrier/topology transitions |
| CONNECTIVITY | DIRECT_AUTHORITY | REUSE_ALLOWED | geographic connectivity conditioning |
| MARINE_AQUATIC_STATE | UNRESOLVED | BLOCKED | none |
| TOPOGRAPHY | DIRECT_AUTHORITY | REUSE_ALLOWED | elevation/topography conditioning |
| RELIEF | DIRECT_AUTHORITY | REUSE_ALLOWED | terrain conditioning |
| ENVIRONMENTAL_INTEGRALS | DIRECT_AUTHORITY | REUSE_ALLOWED | environmental exposure integrals |

## P7Q

P7Q is suspended pending review. The register confirms a reusable paleogeographic/kinematic scaffold, while physical geology, lithology, parent material, regolith, and physical soil remain unavailable or unresolved as explicitly stated in their entries.

# R6 Physical Evolution Reuse Map

| Repository path | Classification | Bounded reuse |
|---|---|---|
| `src/arcana_worldsim/r6/initial_world/generator.py` | `REUSE_DIRECTLY` | Synthetic t0 only |
| `src/arcana_worldsim/r6/initial_world/latent.py` | `REUSE_WITH_ADAPTER` | Regional procedural geometry, not geology/evolution |
| `src/arcana_worldsim/r6/initial_world/refinement.py` | `REUSE_WITH_ADAPTER` | Refinement preserving native support/provenance |
| `src/arcana_worldsim/r6/initial_world/topography.py` | `REUSE_DIRECTLY` | Initial relief only |
| `references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz` | `REFERENCE_ONLY` | SHA256 `9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f`; field-specific diagnostics only if separately authorized |
| `src/arcana_worldsim/post_cha1/paleogeographic_history.py` | `REFERENCE_ONLY` | Endpoint/event support reconstruction, not process tectonics |
| `src/arcana_worldsim/late_cenozoic/paleogeography.py` | `REFERENCE_ONLY` | 30→0 Ma endpoint-constrained support schedule, not R6 evolution |
| `src/arcana_worldsim/scientific_engines/r310_cha1_highres_bridge.py` | `REFERENCE_ONLY` | Tectonics frozen for a short event bridge |
| R3.14 contract | `EXTRACT_GENERIC_PRIMITIVE` | Adaptive scheduler only; not physics |
| R3.18 and R3.20 contracts | `VALIDATION_ONLY` | Downstream exposure/transport/hydrology boundary checks |
| R3.27/R3.28 contracts | `EXTRACT_GENERIC_PRIMITIVE` | Time/grid/checkpoint patterns only |
| `HISTORICAL_DEEP_COUPLING_BRIDGE_CONTRACT_v0_6D.md` | `REFERENCE_ONLY` | Biological/energy Deep semantics; no Deep→mantle law |
| `R4_0_MULTI_ENGINE_ORCHESTRATOR_CONTRACT.md` | `REUSE_WITH_ADAPTER` | ARCANA-owned solver adapter governance, not a geodynamic solver |
| `R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json` | `REUSE_DIRECTLY` | Governs t0 and explicit unknowns |

No governed R6 suitability adjudication for FastScape or another geodynamic/landscape engine was found. Do not acquire or run a candidate until the scientific law and model domain are defined. Machine-readable paths and detailed scope are in the paired JSON.

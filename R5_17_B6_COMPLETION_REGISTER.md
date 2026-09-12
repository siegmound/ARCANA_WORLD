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

## B6 authority/evidence surface

The authoritative evidence inventory and repository disposition are recorded in:

- R5_17_B6_EVIDENCE_MANIFEST.json
- ARCANA_EXECUTION_REFERENCE_INDEX.md
- ARCANA_EXECUTION_REFERENCE_INDEX.json

Compact control-plane evidence is committed in normal Git.

Large reconstructed/derived payloads are intentionally not committed as ordinary
Git blobs. Their path, size and SHA256 identity are registered in the B6 evidence
manifest and they remain reproducible execution products.

The completion register therefore does not treat the local presence of a payload
or diagnostic helper as equivalent to repository-tracked authority.
## Disposition

B6_COMPLETION_DECISION: AUTHORIZE_R5_17_B7
NEXT_SCOPE: NATURAL_BIOLOGICAL_FOOD_SUPPORT
MICRO_SEAL_CREATED: false

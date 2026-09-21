# R5.17-B7-A3F2-P7Q-HRAB GUM AA corrective adjudication

## Decision

`CORRECT_GUM_AA_TEMPORAL_SEMANTICS__PRESERVE_AGE_CLASSES__NO_FORWARD_EVOLUTION`

The earlier “no GUM temporal field” conclusion was caused by an invalid DBF record offset. The corrected parser seeks to the DBF `header_length` (353) after reading the field descriptors. The recovered `AA` field is an independent GUM age-class field; `Symbol` is not the concatenated `XXYYZZAADD` classification.

The global census contains 911,551 records and 13 explicit AA codes. `nn` is an explicit unknown/missing code (321,980 records); blank/null and unexpected codes are zero. The ARCANA association covers 4,602 target cells. It identifies 1,980 cells with a first-order HRAB-relevant age-class constraint and 900 cells with `nn`, while retaining native GUM support and boundary uncertainty.

## Scientific limit

AA supplies broad age-class constraints only. It does not supply exact formation events, persistence, removal/reworking, or a complete forward transition trajectory. Therefore no provider was acquired, no temporal forward evolution was executed, and no categorical interpolation or endpoint backcasting was performed.

External provider research is revised from “first-order age discovery” to age completion, event refinement, persistence, removal/reworking, and spatial completion. Existing provider-research artifacts remain preserved and provisional; this corrective adjudication does not modify the current-state ledger.

## Governance

- `P7Q_reopened = false`
- `scientific_authority_register_mutated = false`
- `current_state_updated = false`
- `physical_soil_created = false`
- `canonical_mutation = false`
- `forward_evolution_executed = false`
- unknown age state remains first-class

Primary sources: [Börker et al. 2018 GUM publication](https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2017GC007273) and the [ICS Quaternary charts](https://quaternary.stratigraphy.org/charts). ICS boundaries are used only as semantic context, not as invented event dates for individual GUM polygons.

# B6N8-N — Exact support, material, layer and property-tuple binding

**Baseline:** `912c135b4ff54ee65e3098c6e7701f5f986b59d8` (B6N8-M R1 attestation commit).
**Decision:** `PASS_B6N8N_ADMITTED_SUPPORT_BINDINGS_CLOSED_READY_FOR_T0_INITIALIZER_IMPLEMENTATION`.

## Scope and inherited authority

B6N8-M remains `PARTIAL_IDENTIFIABILITY_PROFILE_REQUIRED_FOR_FINAL_DECISION`; its qualified source is `92cf7605f5ec47d0646fe3b4ab1cf4d9ac18e65d`. N closes the exact support-to-reference-role/configuration join on restricted admitted support. It does not create a profile or establish physical material composition. Existing specialist values and sensitivities are referenced without selecting or changing them.

## Exact support inventory

Native grid: `R6_GLOBAL_GEOGRAPHY_1DEG_V1`, 180×360 = 64,800 cells. Stable IDs: `R6G1D-R{row:03d}-C{column:03d}`.

| Support class | Count | Treatment |
|---|---:|---|
| Continental classes 1/2/3 | 14,258 | Admitted (7,834 cold, 5,143 normal, 1,281 hot) |
| Positive-age ocean with valid HWR support | 49,362 | Admitted conditionally under existing reduced-model adapter |
| Positive-age ocean adjacent to unselected positive-normal ocean/ocean boundaries | 1,072 | Excluded; process/applicability remains UNKNOWN |
| Selected age-zero ridge cells | 108 | Excluded from this temporal initializer path |
| Other/unclassified | 0 | Partition closure |

The 1,072 exclusion is exactly reproducible from the 1,983-segment canonical boundary manifest: 634 unselected positive-normal ocean/ocean segments touch 1,075 unique ocean cells; 3 overlap the selected ridge set and 1,072 are positive-age. No boundary process is assigned. The rule and ID membership hashes are in [the support index](B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json).

## Role, geometry and property binding

Continental columns map to `CONTINENTAL_CRUST_REFERENCE` over authored crust thickness and `LITHOSPHERIC_MANTLE_REFERENCE` from Moho to authored thermal-class total thickness. Admitted ocean columns map to `OCEANIC_CRUST_REFERENCE` over authored ocean crust thickness and `LITHOSPHERIC_MANTLE_REFERENCE` under the HWR model interval. The grouping is the already-authorized B6N8-L reduced-model adaptation, not natural composition. No upper/lower crust split is supported or needed.

Surface `z=0` is the local column model datum; Moho comes from cellwise crust thickness. Continental total thickness and ocean HWR `zp` are model-domain bases, not physical LAB values. Positive mantle residual is present for all 14,258 continental and 49,362 admitted ocean columns.

The [tuple registry](B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json) binds existing references: continental crust `k=2.5 [2,3]`, `rho=2800 [2700,2900]`, `Cp=1000 [800,1200]`, `A_C=8e-7`; oceanic crust `k=2.2 [1.8,2.8]`, `rho=2890 [2850,2930]`, `Cp=1000 [800,1200]`, `A_C=3e-7`; mantle `k=3.3 [3.0,4.1]`, `rho=3300 [3200,3400]`, `Cp=1200 [1100,1250]`, `alpha=3e-5 [2.5e-5,3.5e-5]`, `A_M=2e-8` in their existing units. These are prior ARCANA specialist reference configurations, not new selections or cellwise observations. `alpha_M` is included because B6N8-J adiabat consumes it.

`kappa=k/(rho*Cp)` is a deterministic same-role derivation: continental crust `8.928571428571428e-7`, oceanic crust `7.612456747404845e-7`, mantle `8.333333333333333e-7 m2 s-1`. No independent diffusivity tuning or uncertainty cross-join is made. `A_C/A_M` are initializer model-scenario source terms; physical source history/constancy remains unknown.

## Join, readiness and boundaries

All 63,620 admitted support IDs resolve to exactly one scoped binding. Zero, duplicate, conflicting, ambiguous or unknown admitted matches: 0. The [exception ledger](B6N8N_BINDING_EXCEPTION_LEDGER.json) keeps excluded groups separate. The [column contract](B6N8N_INITIALIZER_COLUMN_CONTRACT.json) defines the future provider interface without any temperature values.

`INITIALIZER_INPUT_SCHEMA_COMPLETE=true`; `INITIALIZER_BINDINGS_COMPLETE_ON_ADMITTED_SUPPORT=true`; `INITIALIZER_PROVIDER_IMPLEMENTABLE=true`. The profile is unavailable (`INITIALIZER_INPUT_VALUES_AVAILABLE=false`), provider execution is false, and T0 is not materializable now. N14 therefore permits implementation only after this join; it does not authorize execution/publication. A later B6N8-F-selected section can retrieve columns by native support ID, but no Buck section or aggregation rule is selected here.

N1–N14 are individually recorded in [the readiness overlay](B6N8N_B6N8M_READINESS_OVERLAY.json). WORLD_HISTORY was not accessed. No physical parameter, material property, initializer or acceptance threshold was newly selected; no profile, state, evolution, mechanics, dt2 or T2 was created.

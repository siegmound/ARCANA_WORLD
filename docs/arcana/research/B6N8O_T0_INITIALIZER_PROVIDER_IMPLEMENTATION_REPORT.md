# B6N8-O — T0 initializer provider implementation

## Decision and scope

**PASS_B6N8O_T0_INITIALIZER_PROVIDER_IMPLEMENTED_VALIDATED_READY_FOR_IMPLEMENTATION_QUALIFICATION**

This is implementation and non-production validation only. It does not qualify or authorize evaluation on real ARCANA support. The implementation baseline is branch `r6/b6n8o-t0-initializer-provider`, starting HEAD `ff132fc36078afe0e278191cacf0f4c6838cdcce`; the B6N8-N governing attestation records qualified source `9d94170ae4a35267cbccd087e112841b4215d07e`.

## Architecture and equations

The provider is in [`pre_orbdata_t0_initializer.py`](../../../src/arcana_worldsim/r6/pre_orbdata_t0_initializer.py), following the existing R6 package pattern of typed dataclasses, explicit validators, deterministic identities, and pytest fixtures. It adapts the already selected kernels in [`pre_orbdata_thermal_column.py`](../../../src/arcana_worldsim/r6/pre_orbdata_thermal_column.py); it introduces no separate model framework or command-line production entrypoint.

The family remains `R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING`. Continental columns use the existing transient piecewise analytical solution and its rate closure to meet the authored basal adiabat at the model base. This closure constructs a snapshot; it is not T0→T1 evolution and is not a substitution with the rejected steady-state geotherm. Positive-age ocean columns use HWR-2, including its authored age-dependent surface flux, the shallowest HWR/adiabat crossing below the Moho, and the already governed model-base fallback. Ridge age zero and unresolved positive-age ocean support are excluded.

Profiles are represented by analytic piecewise segments (continental local quadratics and ocean Hermite cubics). This supports depth queries and preserves layer-specific properties without choosing a production vertical grid. Model-domain base and physical LAB remain distinct. The output is a synthetic candidate profile, never a canonical state.

The only thermal-kernel source change exposes explicit mantle `alpha` and gravity arguments and passes the selected mantle `Cp` in the ocean adiabat. Defaults preserve existing R6 behavior; B6N8-O passes the existing B6N8-N bindings explicitly. No new parameter or value was selected.

## Contracts, provenance, and safeguards

`ColumnBinding` carries support/class, geometry and datum, discrete material-role sequence, exact tuple/source references, derived diffusivity, T0/boundary scenario, configuration identity, uncertainty, lineage, units, and binding status. Validation rejects unknown/excluded support, non-T0 selection, a claimed physical LAB, invalid units/geometry, missing scenario or provenance, incoherent `k/rho/Cp/kappa`, missing mantle expansivity, nonfinite values, and unsupported model identity. `kappa = k/(rho Cp)` is derived from the same role tuple. Crust roles do not receive an invented expansivity; only the governed mantle tuple supplies `alpha`.

Output validation checks profile segment count/order, discrete role assignment, finite values, provenance/uncertainty, and the canonical UTF-8 JSON byte identity. Output records tuple values/references, source terms, configuration, support lineage, numerical configuration and uncertainty. It explicitly identifies the output as noncanonical.

Numeric evaluation is exposed only through `evaluate_synthetic_fixture`, which requires both the `NON_CANONICAL_` fixture marker and a `TEST_...` support ID. Production preflight is separate: it reads qualified manifests, authority hashes, and the field package, reconstructs support membership and deterministic plan identities, and never calls either thermal profile kernel. There is no WORLD_HISTORY import, canonical publisher, production runner, or state-write API.

## Preflight and verification

Metadata-only preflight closed the complete 64,800-cell partition:

| Support | Count | Preflight treatment |
| --- | ---: | --- |
| admitted continental | 14,258 | plan validated |
| admitted positive-age ocean | 49,362 | plan validated |
| unresolved positive-age ocean | 1,072 | excluded |
| zero-age ridge | 108 | excluded |
| other / residual | 0 | none |

The preflight also verified 634 candidate boundary segments, 1,075 adjacent oceanic cells, and 3 ridge-overlap cells; admitted unresolved and ambiguous bindings were both zero. The deterministic plan digest was `2b184bbf2dea3f2895af1ba7e257315a3bcb1da5108654858536c075a932c5d0`. One observed preflight took 4.57 s on this Windows environment; this is environment evidence, not a production runtime benchmark. No production `T(z,T0)` profile was evaluated.

The new focused numerical/contract module passed **27 tests**. The final related PRE_ORBDATA regression group passed **89 tests**. Coverage includes continental/ocean profiles, boundary/interface behavior, transient-rate presence, property perturbations (`k`, `rho`, `Cp`, source), discrete-role preservation, failure categories, deterministic serialized identity, excluded support, output contract, and real-binding metadata-only preflight. The full repository R6 suite was not run because this stage requires WORLD_HISTORY to remain unaccessed; broader validation stayed within the PRE_ORBDATA runtime surface.

The O1–O14 gate matrix and machine-readable provider/non-action status are in [`B6N8O_IMPLEMENTATION_READINESS.json`](B6N8O_IMPLEMENTATION_READINESS.json). O14 means ready for implementation qualification only, not permission to execute production initialization.

## Final authorization boundary

`provider_implemented`, unit/contract validation, and metadata preflight are true. Production execution authorization, real T0 profile/state generation, T1 generation, T0→T1 evolution, canonical checkpoint publication, Buck section selection/mechanics, dt2, T2, and WORLD_HISTORY access/change remain false. Next: implementation qualification on an authorized clean baseline; no production initializer run is authorized by this report.

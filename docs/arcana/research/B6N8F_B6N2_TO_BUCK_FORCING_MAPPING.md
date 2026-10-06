# R6 B6N8-F — B6N2 to Buck Forcing and Section-Support Mapping

## Decision

**PASS_B6N8F_LOCAL_KINEMATIC_DRIVER_DERIVABLE_BUCK_UX_REQUIRES_SECTION_ADAPTATION_XE_AND_INITIALIZATION_AUTHORITY**

This is a read-only authority audit at source baseline `771b8d3ea9706eb0d45903e72354b304e6979e69`, branch `r6/b6n8f-b6n2-to-buck-forcing-mapping`. It defines what a later adapter would need. It does not select or execute a physical rift model.

The findings are separated in the [mapping chain](B6N8F_KINEMATIC_TO_PHYSICAL_MAPPING_MATRIX.json), [section eligibility matrix](B6N8F_SECTION_SUPPORT_ELIGIBILITY.json), and [candidate forcing-interface requirements](B6N8F_FORCING_INTERFACE_REQUIREMENTS.json).

## Authority read and temporal boundary

The governing B6N2 artifact is `contracts/R6_POST_EVENT_KINEMATIC_AUTHORITY_V1.json` (SHA256 `966c63a8fa8347525568cb89bb280905d37a1aa3711856a13f31a39377a600c3`). It references the unchanged `R6_T0_CANONICAL_PLATE_KINEMATICS.json` realization (SHA256 `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2`) and binds its use as a restricted successor model to the exact POST_EVENT state `r6state_86b55139388fd6d01cb0ff640f9580e1e1331f2469fb5c4f296c6cf2578fc630`, payload SHA256 `9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a`.

The vector source remains an instant-only synthetic realization at 210 Ma. Its source provenance is not extended. B6N2 separately grants a restricted successor-model scope beginning at POST_EVENT, 209.97287659484368 Ma, and ending at the earliest applicable event/model/source boundary. It does not authorize rate changes, a fixed-plate interpretation, mechanics, topology change, or movement publication. This is the distinction:

`SOURCE_TEMPORAL_PROVENANCE = INSTANT_ONLY`

`SUCCESSOR_MODEL_AUTHORITY = EXPLICIT_RESTRICTED_POST_EVENT_MODEL`

The canonical POST_EVENT state retains the original geometry payload and topology identity, plate support and junction incidence. Its process state is `RIFT_PROCESS_ACTIVE`; that process state is not a boundary-type or accommodation law. The canonical record's support is global on `R6_GLOBAL_GEOGRAPHY_1DEG_V1`; it does not itself persist a Buck section or per-segment physical forcing record.

## Kinematics that are derivable

B6N2 carries one angular-velocity vector per each of the 12 plate IDs, in rad/year, with active right-handed XYZ column-vector action. The reference is the synthetic area-weighted least-squares no-net-rotation gauge: a kinematic gauge, not an Earth-fixed, mantle-fixed, or torque-balance frame. No single plate is fixed. The B6N2 pair-level rift scope is ordered pair `[1,3]`; it does not classify all interface segments as divergent.

The governed planet geometry is spherical, with mean radius 6,371,000 m in `R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json`. Thus, at a supported point with unit radial vector `r`, rigid surface velocity is a deterministic kinematic derivation:

`v_i(r) = R * (omega_i × r)`

At the same point on the 1:3 interface:

`delta_v_1_to_3(r) = v_3(r) - v_1(r) = R * ((omega_3 - omega_1) × r)`

The structural census governs an edge-local tangent convention (increasing latitude for EAST edges; increasing longitude for NORTH edges) and normal `n_AB` pointing from `plate_a` to `plate_b`. Under that diagnostic convention, positive `delta_v · n_AB` means kinematic opening. Components are:

`v_normal = delta_v · n_AB`

`v_tangential = delta_v · t_edge`

These are signed instantaneous kinematic diagnostics. Keep the tangential component; do not use absolute value to erase polarity. The pair's current T0 diagnostic is heterogeneous: 52 of its 71 edges classify as mixed opening/shear and 19 as mixed closing/shear. These T0 diagnostics are not post-event finite forcing, and they do not authorize a pair-wide physical opening rate.

The plate ordering and frame fix a **kinematic coordinate polarity** only. They do not establish geological polarity (including overriding/subducting identity), fault identity, or physical accommodation. B6N2 explicitly leaves junction physical accommodation unknown.

## Interface and section support

The canonical partition has 1,983 structural boundary segments and 20 junctions. The B6K relational candidate tied to the unchanged POST_EVENT geometry represents pair 1:3 with 71 segments, 72 shared node identities and separate side representations for plates 1 and 3. Its chain endpoints are nodes 34858 and 41750, which are the degree-three junctions `R6JNT-T0-4a67fe6607845a68` and `R6JNT-T0-f7f8b6413402335a`. These B6K records are derived relational support, not new canonical physical state. Boundary type remains `UNKNOWN_NOT_AUTHORIZED_BY_KINEMATICS_ALONE`; physical accommodation remains `UNKNOWN_UNCHANGED`.

An exact edge frame is available for a local kinematic decomposition, without smoothing. That does not define a cross-rift Buck section. The Buck x-axis, endpoint locations, endpoint plate identities, common-frame projection/transport, curvature eligibility, and section-selection rule still need an explicit adapter. `INTERFACE_NORMAL` is not interchangeable with `RELATIVE_VELOCITY_DIRECTION`; the latter can include a tangential component.

Do not equate 71 edges with 71 Buck experiments. Per-edge sections would overlap and have no independent support, forcing history, or aggregation authority. A small set of adaptively selected interior sections is a possible design, but selection, station spacing, curvature tolerance, coverage and aggregation are not yet governed. No numerical smoothing window, curvature threshold or endpoint buffer is selected. Both ends of this particular pair chain coincide with multi-branch junctions; no branch averaging or unique junction normal is authorized.

## What Buck consumes, and what ARCANA does not yet bind

The recovered B6N8-D registry distinguishes equation semantics from Buck's experiment settings:

| Quantity | Recovered meaning | B6N8-F status |
|---|---|---|
| `U_x` | Horizontal velocity difference across a finite pure-shear extension zone; paper units m/s | Not identical by authority to local interface-normal relative velocity; requires an ARCANA section adapter |
| `X_e` | Pure-shear zone width, a model geometry/forcing-support input | No ARCANA value or derivation rule; initialization geometry may inform a later decision but cannot be silently equated to lithosphere thickness |
| `epsilon_dot` | `U_x / X_e`, in s^-1 | Not derivable until both inputs and their support/sign are governed |
| `X_L` | Initially uniform lithosphere width in the experiment and its lateral section/domain support | No ARCANA mapping to uniform physical support or lateral boundary conditions is selected |
| finite strain/duration | Forcing history integrated over a finite interval | No interval or increment selected; Buck's `epsilon=0.25` is not an ARCANA choice |

Buck's experimental tie between `X_e` and initial lithosphere thickness and its 40 km lower bound are not universal ARCANA rules. Nor may the B6N3-A 8,214.051909-year model-scope revalidation bound or a B6N8-A diagnostic window be used as a physical forcing duration. B6N4-R1 reports no positive propagation interval established. Therefore no finite strain or `epsilon_dot` is materialized here.

A candidate endpoint adapter could evaluate rigid plate velocities at opposite section endpoints and project their difference onto a governed section x-axis. This preserves Buck's finite-zone meaning better than copying the local boundary normal component, but it is an **ARCANA model adaptation**, not a direct B6N2 output. It requires a finite section/endpoint rule (likely related to but not assumed equal to `X_e`), valid plate support at both endpoints, and a frame-transport/projection convention. Near junctions, chain endpoints, unsupported geometry, convergent motion and strongly oblique motion require explicit eligibility decisions. No extrapolation, interpolation, nearest-edge assignment or averaging is implicit.

## Coverage and uncertainty

The [eligibility matrix](B6N8F_SECTION_SUPPORT_ELIGIBILITY.json) distinguishes ordinary edge interiors, high curvature, endpoints, simple and multibranch junctions, ambiguous sides, near-zero normal motion, convergence, obliquity and unsupported geometry. Current edge-local kinematics can be derived on explicit supported edges, but no category is thereby declared physically suitable for a Buck run. In particular, the active pair chain ends at degree-three junctions and the entire pair cannot be assigned a uniform physical extension class from its mixed local diagnostics.

Preserve the following named uncertainties without inventing probability distributions: Euler-vector realization; geometry; frame/orientation; polarity; projection; section selection; `X_e`; `X_L`; obliquity/model mismatch; temporal validity; and junction/endpoint behavior.

## Future initialization integration boundary

B6N8-E is a sibling branch and was **not** imported or used as authority here. A later integration will need its qualified authority to provide, if it governs them, T1 lithosphere-base/thickness and crust/Moho geometry, material identity/applicability support, T1 validity/unknown masks, and associated provenance/uncertainty. Those inputs still would not decide that `X_e` equals a thickness or determine `X_L`: an ARCANA model binding is separately required.

## Implementability gates

1. **Can B6N2 produce a local relative-velocity driver?** Yes, by deterministic kinematic derivation on explicit supported geometry, using the governed sphere/radius, shared XYZ gauge, plate ordering and edge frame.
2. **Can that driver become Buck `U_x` now?** No direct equivalence is established. It requires an ARCANA section/endpoint adapter, `X_e` binding and initialization authority. The endpoint-velocity construction is a candidate, not yet an authorized mapping.
3. **Can `epsilon_dot` be derived?** No: neither Buck `U_x` nor `X_e` is currently governed as an ARCANA input.
4. **Can finite Buck forcing execute?** No. No physical forcing interval, `X_e`, section support or initialized Buck state is authorized.

This audit does not implement Buck, choose physical values, generate a Buck T1 state, select `dt2`, create T2, execute mechanics/propagation, change topology/support, or write WORLD_HISTORY. The candidate future field contract is [here](B6N8F_FORCING_INTERFACE_REQUIREMENTS.json).

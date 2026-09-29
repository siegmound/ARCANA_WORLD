# R6 PRE_ORBDATA A0.5 — Heat-flow physical-model adjudication

**Decision:** `R6_PRE_ORBDATA_HEAT_FLOW_ARCHITECTURE_SELECTION_BLOCKED__CONTINENTAL_REFERENCE_AUTHORITY_UNRESOLVED`

**Selected complete architecture:** none yet. Evidence supports selecting an oceanic model family, but it does not support choosing A, B, or C as a complete ARCANA T0 architecture without adding physical authority that the current contracts do not state.

## Authority and scope

The B-Pangaea-like v2 realization is ratified for T0 materialization but remains `CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION`. The qualified ShellSet evidence remains tied to branch `arcana-r6-runtime-capacity`, commit `62fd474f229b2676fd9d39c5def45137d22d2481`, executable SHA256 `4c0044fe4332184d63408960a2237d4edb7da891b71f74b82bd1d5a83b27e918`, and governed patch SHA256 `e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2`.

This is an architecture adjudication only. It does not choose numerical parameters, execute OrbData/SHELLS, modify ShellSet, promote canonical state, or authorize PRE_ORBDATA.

## Continental reference field: authority audit

The field's actual generator is `src/arcana_worldsim/r6/t0_materialization/b_pangaea_v2.py`: `HEAT_FLOW_MW_M2` maps the three `THERMAL_IDS` to constants, and the materializer writes those values on `land & (thermal_id == thermal)` cells into `continental_reference_surface_heat_flow_w_m2`. The manifest records this under `derived_fields.continental_thermal_reference_state`; the specialist report calls it continental domain references and explicitly says global and oceanic heat-flow fields are missing.

Therefore its present provenance is a deterministic ARCANA authorial/template configuration keyed by categorical thermal domains. The inspected producer cites no physical heat-flow model, observation set, inversion, or uncertainty model for those constants. It is a materialized reference field, not a field derived from the currently materialized crustal thickness, lithosphere thickness, or ocean age. Its support is the 180×360 cell grid on land thermal-domain cells; ocean cells are UNKNOWN. It has no FEG-node projection or per-node lineage yet.

The evidence establishes what the field is generated from, but not its stronger physical role. “Reference” does not by itself mean prescribed physical T0 flux. No current contract resolves whether it is (i) the continental T0 Neumann boundary condition, (ii) a target/constraint for a continental thermal model, or (iii) validation-only. Accordingly, it must not yet be supplied as final T0 heat flow. An explicit ARCANA authorial contract must ratify its role and uncertainty semantics. If used directly, its existing categorical construction and uncertainty must also be accepted or revised through governance.

Projection to the FEG can add numerical support only. Require homogeneous categorical incident support, retain incident-cell lineage and projection diagnostics, and leave mixed-domain or UNKNOWN nodes unresolved. Do not average heat flow across categorical ocean/continent boundaries or claim higher physical resolution.

## A/B/C comparison and finding

| Criterion | A — explicit global T0 flux | B — fully derived from primitives | C — hybrid domain-aware |
|---|---|---|---|
| Physical defensibility | Possible only with authorized complete field provenance; absent globally | Strong causal design after missing continental physics/configuration is supplied | Plausible, but direct-use premise for continental reference is not adjudicated |
| Existing ARCANA state | Partial continental reference only; ocean field missing | Uses domain, ocean age and structure, but those do not alone determine flux | Best matches current split of continental reference and ocean age |
| Duplicate state | High if model-derived flux also exists | Low if flux is derived/replayable and references have distinct roles | Moderate; avoid conflating reference and final flux |
| Provenance and causality | Clear if field is the sole declared authority | Strong input → model → flux direction | Clear only after continental reference is declared a prescribed flux or explicit constraint |
| Uncertainty | Must be field-attached, presently missing | Propagate primitive, material and model-form uncertainty | Must keep unlike continental and ocean uncertainties distinct |
| Selective replay | Good for tiled, lineage-bearing fields | Strong dependency-driven replay | Branch replay possible; transitions invalidate neighboring projection |
| T0→T1 | Initial condition only; evolution still separately governed | Natural replay path once temporal laws/forcing are specified | Both branch laws need time-dependent semantics |
| OrbData | Complete nonzero nodal field avoids zero-sentinel derivation, but limits/corrections still alter values | Must provide finite supported nodes or an authorized fallback | Can supply both branches only after continental role and ocean model are closed |
| Earth data authority | Can remain ARCANA-authored | Physical analogues may constrain model, not become ARCANA maps | Same; Earth model calibration transfer must be justified |
| Boundaries and gaps | Requires explicit join and UNKNOWN policy | Requires domain laws and interface policy | Categorical join required; current projection preserves mixed support as UNKNOWN |
| Reproducibility | Requires field source, masks, lineage, deterministic projection | Requires pinned model/config/input hashes | Requires separate pinned branches and deterministic join |

**Finding:** A is unsupported because there is no complete global field. B is deferred because continental model inputs and material configuration are not governed. C is the most natural *candidate structure*, but C as specified assigns the existing continental reference direct T0 authority, which is not established. Choosing C now would silently upgrade “reference.” Thus none is selected as a complete architecture. The smallest blocker is the explicit semantic ratification of that continental field; if it is not direct T0 flux, a governed continental derivation contract is also needed.

## Ocean model-family adjudication

For the full age range in this realization, prefer a **finite-thickness plate-cooling family** with age-dependent conductive surface heat flux. Do not use a single classical half-space cooling law over the full age range: its idealized cooling continues indefinitely, while plate formulations represent finite lithosphere thickness/basal heat resupply and better fit mature/old seafloor in the reviewed comparisons. Half-space cooling remains a useful young-age conductive reference/limit, not the full-range law. [Holdt et al. 2025](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JB029890), [Stein & Stein 1992](https://www.nature.com/articles/359123a0).

This selects only a model **family**, not GDH1, coefficients, temperature, plate thickness, or other values. Any implementation must be version-pinned and explain transfer from modern-Earth model evidence to ARCANA's authored 210 Ma age field. The field is a monotone distance transform from selected candidate divergent boundaries and makes no constant spreading-rate claim.

Very young oceanic crust is a limited-validity domain for an age-only conductive law: ridge accretion and hydrothermal circulation introduce spatially heterogeneous heat transport. Report whether flux is conductive surface flux or total heat loss, carry an applicability flag, and represent model-form uncertainty. Do not add a uniform hydrothermal correction from global Earth estimates. [Stein & Stein 1994](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/93JB02222), [Grose & Afonso 2013](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/ggge.20232).

### Age zero

**Physical policy:** age zero is a valid authored age-field boundary value on the generator's selected candidate divergent-source geometry, not missing data. It sits at the singular boundary of the classical half-space/GDH1 conductive formula. Age alone cannot supply a finite physical flux there. A finite-width/accretion young-ridge model must be selected, or the heat-flow output must remain unsupported/UNKNOWN until then. The distance-transform seed does not itself establish a resolved physical ridge-axis cell.

**ShellSet representation:** qualified ShellSet assigns `qLim1` when `ageMa <= 0` in its missing-heat-flow ocean route. This implementation behavior is not adopted as ARCANA physics. Exact zero `heatFl` also means “derive/fill” to ShellSet, so an exact-zero physical input cannot safely pass as ordinary data through that interface. The adapter must resolve a governed finite value or fail closed before OrbData; it must never silently substitute `qLim1`.

## qLim governance

`qLim0`, `dQL_dE`, and `qLim1` are ShellSet specialist configuration/model controls, not WORLD_HISTORY physical fields. The first two can only be retained as configured floor behavior if its effect is justified and sensitivity-tested. `qLim1` is both an upper cap and the age-zero output in the qualified source; its age-zero role must be decoupled from physical policy. Final disposition and values for all three remain unresolved. Capture pre/post clamp flux and any later geotherm correction; exact-zero nodes must not accidentally invoke `qArray`/age fill.

## Domain join and support contract

1. Read `physical_crust_domain_id` categorically and retain incident source-cell lineage.
2. Evaluate the ocean model only for homogeneous ocean support with valid age/model-applicability support.
3. Use the continental branch only after direct-reference versus derived-model semantics are adjudicated.
4. Mark mixed categorical boundary nodes UNKNOWN unless a separately governed interface rule resolves them. Never interpolate categorical IDs or average flux across domains.
5. Preserve UNKNOWN; do not map it to zero, because zero activates ShellSet's fallback route. If any node remains unresolved, do not start OrbData.
6. Attach source/model identity, input hashes, selected cells/weights, uncertainty, applicability and coverage to each node. Projection is numerical support, not a resolution increase.

## WORLD_HISTORY versus derived/runtime data

| Quantity | Recommended status |
|---|---|
| `continental_reference_surface_heat_flow_w_m2` | Persist under its current named authored-reference semantics and support. Do not relabel as final flux until ratified. |
| `oceanic_lithosphere_age_ma` | WORLD_HISTORY physical primitive with source and lineage. |
| Final global/cell T0 flux | `DERIVED_REPLAYABLE_STATE`: specialist result/cache tied to model, configuration and input hashes; not an independently authored primitive. |
| FEG nodal serialization | `NUMERICAL_RUNTIME_INPUT_ONLY`, derived from the supported cell field with lineage. |
| Model identity/configuration | Specialist configuration and provenance envelope, not physical WORLD_HISTORY state. |
| Uncertainty and support masks | Persist as field lineage/validity metadata alongside the derived result; preserve UNKNOWN. |

This separates causal inputs from replayable specialist results and avoids storing an ambiguous second “canonical” heat-flow field. A future `STATE_AT(t, domain)` still requires separately governed thermal evolution laws; this T0 decision does not provide them.

## Uncertainty contract

- **Continental reference:** uncertainty is currently UNKNOWN. Do not infer it from modern-Earth heat-flow compilations. If direct flux is ratified, its source must provide defensible uncertainty/covariance or expressly govern the field as deterministic authorial input and require sensitivity ensembles.
- **Ocean cooling:** record parameter covariance and structural model alternatives; ensemble alternatives where they can change decisions or downstream outputs.
- **Very young ocean:** mandatory validity flag and structural alternatives for ridge/accretion/hydrothermal treatment; otherwise output UNKNOWN.
- **Projection:** record source cells, categorical agreement, weights/method and coverage; quantify error with convergence/refinement evidence before assigning a numerical bound.
- **Structural uncertainty:** do not substitute qualitative metadata for ensembles when model alternatives materially affect a decision. Metadata/ranges may accompany exploratory non-decision outputs, but no central value is selected here.

## Remaining decisions and blockers

1. ARCANA authorial ratification: is the continental reference a prescribed T0 physical flux, model constraint/target, or validation-only? State uncertainty, support and boundary semantics.
2. If it is not a prescribed flux, select a source-pinned continental thermal/heat-flow model and govern its heat-production/material/basal inputs.
3. Pin a finite-thickness ocean cooling model and its transfer rationale, flux meaning, material/basal configuration and validity range.
4. Define finite young-ridge/age-zero treatment independently of `qLim1`.
5. Govern `qLim0`, `dQL_dE`, `qLim1`, and acceptance sensitivities; expose clamp/correction diagnostics.
6. Close categorical boundary, UNKNOWN, zero-sentinel and FEG projection policies.
7. Define uncertainty/covariance, structural ensembles and replay acceptance criteria.

**Gates preserved:** `PRE_ORBDATA_ready=false`; `t0_orbdata_executed=false`; `shellset_mechanics_authorized=false`; `dt_selected=false`; `t1_created=false`; `forward_evolution_authorized=false`. Canonical state and ShellSet remain unchanged.

# R6 B6N8-I — Thermal, Material and LAB Binding Authority Closure

**Baseline:** branch r6/b6n8i-thermal-material-lab-binding-authority, source commit 614cfb414155e5fbd6664e92d1b890430593cbf4 (B6N8-H attestation commit).
**Decision:** PASS_B6N8I_BINDING_CONTRACT_DEFINED_THERMAL_COLUMN_COMPATIBILITY_AND_LAB_AUTHORITY_REMAIN.

This is an authority inventory and contract definition. B6N8-I selects no new physical parameter, thermal initializer, LAB criterion, T0/T1 state or evolution law.

## 1. B6N8-H and reusable ARCANA authority

The B6N8-H attestation and its qualified artifacts agree on their source and verdict. They define provider requirements, while recording that T0 thermal profile/initializer, full thermal-material-boundary-LAB applicability, and T0-to-T1 evolution remain open.

This audit also found existing specialist ARCANA reference authority. It must not be mistaken for absent values or promoted to canonical world state:

- R6 gravity is the fixed Earth-scale-analogue model constant 9.82 m s-2.
- B-v2 authors cell-supported crust thickness/domain, continental thermal-class reference surface flux (0.045/0.060/0.085 W m-2), continental reference lithosphere thickness (200/135/80 km), and oceanic age. The continental q field is a prescribed authored reference boundary on its native support; it is not heat production, composition, or a geotherm.
- A0.6D supplies a shared specialist mantle/HWR tuple and sensitivity ranges: k=3.3 (3.0–4.1) W m-1 K-1, rho=3300 (3200–3400) kg m-3, Cp=1200 (1100–1250) J kg-1 K-1, alpha=3.0e-5 (2.5–3.5e-5) K-1, TSurf=280 (250–300) K, HWR Tb=1680 (1523–1737) K, zp=100 (80–140) km, and rhoH2O=1000 (990–1030) kg m-3.
- The A0.6G material/reference-column authority records specialist reference values for continental crust (rho 2800 [2700,2900], k 2.5 [2.0,3.0], Cp 1000 [800,1200], alpha 3e-5 [2e-5,4e-5]), oceanic crust (rho 2890 [2850,2930], k 2.2 [1.8,2.8], same Cp/alpha references), and mantle. It also records bulk production references: continental 8e-7 [4e-7,1.2e-6], ocean 3e-7 [0,5e-7], mantle lithosphere 2e-8 [0,4e-8] W m-3.
- These A0.6G selections are specialist configuration/proxies with literature-constrained ranges, not cellwise Earth observations, canonical composition, or new B6N8-I selections. The material authority marks the candidate column incompatible with required transient/ocean and authored geometry cases. A selected parameter tuple does not therefore establish a valid T0 profile.

The current reference taxonomy distinguishes continental crust, oceanic crust, lithospheric mantle, and conditional asthenosphere/seawater roles. ARCANA does not infer composition from physical_crust_domain_id, thermal class, province, or age. No upper/lower crust split is supported by present T0 material fields.

## 2. Binding-by-binding result

The [binding matrix](B6N8I_BINDING_MATRIX.json) records each quantity’s meaning, units, support, authority class, temporal role, uncertainty, persistence, derivation, status, and blocker.

- **Conductivity:** existing specialist values use constant k per bulk reference class. Temperature/pressure-dependent conductivity is not qualified. The existing values need a model-specific applicability and validity binding before use in a T0 initializer.
- **Density:** role-specific reference values exist. They do not provide a lateral pressure-density-gravity closure, complete rho(z), or a universal scalar for thermal, isostatic and Buck-force roles. Reference density, thermal correction, chemical anomaly and Buck reduced contrast remain separate.
- **Specific heat:** reference values exist. Mantle Cp feeds HWR diffusivity; crust Cp is retained for energy-model completeness. Neither may be inferred from k or density.
- **Diffusivity:** derive kappa=k/(rho Cp) from a single coherent material tuple. Do not fit/bind it independently. The existing mantle nominal tuple gives 8.3333e-7 m2 s-1; its recorded range is 7.0588e-7–1.1648e-6 m2 s-1. This is a configuration-derived coefficient, not historical state.
- **Radiogenic production:** specialist bulk references exist, distinct from surface q and T(z). No production field, vertical distribution, or ARCANA geochemical history is established. Do not invert surface heat flow to infer production.
- **Surface boundary:** TSurf=280 (250–300) K is an existing specialist reference, not a climate history. Continental authored q is supported on its existing field domain; the ocean branch and ridge/young-age handling have separate HWR rules. No complete time-dependent T0-to-T1 boundary history is established. B6N8-J must decide whether the effective reference boundary is sufficient or climate-coupled history is required; this audit does not assume climate coupling is unnecessary at 210 Ma.
- **Basal boundary:** HWR Tb and zp are finite-plate model parameters. A0.6G maps ocean zp to total thermal lithosphere thickness and derives an anchor under that model. This is not a validated global LAB or mechanically equivalent Buck thickness. The existing steady piecewise column failed compatibility checks against transient HWR flux and required authored geometries.

A steady-layer equation and a transient column recipe exist in the R6 contracts, but B6N8-I does not select an initialization model. A scalar surface flux, even with material parameters, does not uniquely specify T(z) without initial/basal conditions and a compatible model.

## 3. LAB semantics and circularity

LAB must remain typed by meaning: thermal, mechanical, rheological, seismic, compositional, or a model-domain base. The repository does not authorize equivalence among these terms.

The [LAB decision matrix](B6N8I_LAB_SEMANTIC_DECISION_MATRIX.json) evaluates the candidate routes:

- An independently authored geometric base is least circular, but continental reference thickness and conditional ocean HWR thickness do not yet provide one coherent global physical LAB field.
- A thermal isotherm needs an authorized T(z) and criterion. It is circular if it both sets the boundary used to construct that profile and is then inferred from it.
- A rheological threshold requires temperature, composition, pressure/stress/rate and constitutive laws; those remain unbound and likely require a coupled method.
- A combined thermo-mechanical LAB is also unselected and coupled.
- No external geometry provider is selected or implemented.
- An authorial synthetic geometric primitive is possible in principle, but B6N8-I ratifies no LAB field or value.

No LAB criterion, field, or iterative solver is selected or materialized. A future initializer may use independently authored geometry as a boundary only after explicit semantic binding. If LAB is diagnosed from temperature or rheology, compute it after solving on a larger independently bounded domain.

Moho geometry is available from authored cellwise crust thickness with a vertical datum. It binds interface geometry only, not mineral composition or material properties.

## 4. Provider and model boundary

No external thermodynamic provider is selected or required merely to define a conduction-only reference model. The repository capability audit describes Perple_X for equilibrium from a chosen bulk composition at prescribed P-T, and BurnMan for explicit assemblage/EOS or a radial layered reference calculation. Neither tool, database, nor dataset is ARCANA authority by itself. If the selected initialization requires phase equilibrium or pressure-dependent EOS density, provider and dataset identity, validity, support and provenance become an explicit closure; no such integration is authorized here.

## 5. Minimum rheology boundary and Buck crosswalk

A conduction-only thermal initializer/evolution law does not inherently require Buck brittle or ductile rheology. Rheology becomes necessary if the selected LAB is rheological, the interval model includes strain/advection/lower-crust flow, or the Buck force model is evaluated. Recovered Buck equations identify diffusivity, internal heating, density/expansion/gravity, geometry and creep/strength as separate dependencies; they do not authorize ARCANA values. Full Buck rheology remains outside B6N8-I.

Fixed material properties and laws belong in versioned material/model configuration. Time-varying geometry, composition or physical T(z) belongs in causal persistent state only when it is an evolving world state and cannot be exactly replayed from retained parents. Kappa, thermal density, interface temperatures and profiles can be replayable derived state only with pinned complete inputs, recipe, support and validity. Solver iterates are temporary; force/buoyancy diagnostics are not automatically canonical state.

## 6. B6N8-H/G overlay and I1–I12

The [readiness overlay](B6N8I_B6N8H_READINESS_OVERLAY.json) preserves the B6N8-H statuses and G’s 20-input inventory. I2–I6 now have identified specialist references or deterministic derivations, but H3 is not upgraded to full readiness: the references have not yielded a compatible, fully supported T0/T1 profile. H2/H4/H5/H6 and H10 remain blocked; H9 remains a requirements-only provider contract.

| Gate | Result |
|---|---|
| I1 material taxonomy | Role taxonomy defined; composition binding open |
| I2 conductivity | Existing specialist reference values identified |
| I3 density | Role-scoped reference values identified; full density state open |
| I4 specific heat | Existing specialist reference values identified |
| I5 diffusivity | Deterministically derivable from coherent k/rho/Cp |
| I6 radiogenic heat | Authorial specialist references identified; not a canonical field |
| I7 surface boundary | Partial existing authority; no complete temporal history |
| I8 basal boundary | Partial HWR binding; global LAB/profile compatibility open |
| I9 LAB semantics | Unresolved; no equivalence selected |
| I10 minimum rheology | Not needed for conduction alone; needed conditionally for rheological LAB/flow/Buck |
| I11 binding contract | Requirements and authority inventory defined |
| I12 ready for T0 initializer selection | **Not ready:** column compatibility and LAB route remain |

## 7. Exact finite work remaining before B6N8-J

1. Select a thermal initialization model compatible with the ratified continental reference flux, ocean HWR transient model and support/age-zero rules. The existing steady piecewise candidate failed compatibility checks.
2. Choose a non-circular thermal lower boundary/LAB meaning and bind datum, support, validity and uncertainty. Keep LAB meanings distinct from each other and from HWR zp/ZBASTH.
3. Decide whether conduction-only T0-to-T1 evolution suffices. Any advection, flow or rheological coupling requires its own law/driver.
4. Bind applicability of the existing specialist material tuple to the selected model and retain its source-range/covariance limitations; B6N8-I selects no replacement numbers.
5. Provide initial T(z) and surface/basal histories required by that model; decide whether the selected effective surface reference suffices or a climate-coupled boundary history is physically required.

**B6N8-J readiness:** not ready to select a defensible initializer/evolution law until model-form compatibility and the LAB/basal-boundary route are resolved. B6N8-I does not establish that long pre-T0 history is required or unnecessary. It does not close B6N8-F forcing/section mapping.

## 8. Validation and safety

Static authority review only. No literature values were newly imported or promoted to ARCANA world values; no numerical parameter was selected in this stage. Existing literature-constrained ranges remain attached to their prior specialist authority and validity caveats.

WORLD_HISTORY was not accessed. No T0/T1 state, material state, LAB field, section, forcing, Buck result, dt2, or T2 was created. No provider, mechanics or forward propagation was executed. Exact non-actions are recorded in the readiness overlay.

# ARCANA WorldSim R6 — PRE_ORBDATA A0.4 literature constraints

**Status:** research synthesis for parameterization options; no ARCANA thermal values or architecture selected. Earth observations below constrain candidate physics and uncertainty; they are not ARCANA 210 Ma ground truth.

## Executive findings

1. The positive-age ShellSet heat-flow expression is the GDH1 age relation attributed in qualified MOD_Data source comments to Stein & Stein (1992), after converting the published mW/m² coefficients to W/m². The branch at 55 Ma joins continuously at about 68.8 mW/m² and approaches 48 mW/m² at old age. It is an empirical plate-model fit to Earth age/heat-flow observations, not a universal law for ARCANA.
2. GDH1's young-age branch varies as age to the power -1/2 and diverges as age tends to zero. ShellSet's age<=0 assignment to qLim1 is not that published relation; it is a finite implementation branch using the configured upper cap. The literature does not make that cap a physical ridge observation.
3. Conductive age models do not by themselves reproduce all seafloor measurements. Hydrothermal circulation transports heat advectively, depresses measured conductive heat flow over much young crust, and can focus discharge. This is spatially heterogeneous and not represented by a universal scalar correction.
4. On continents, surface heat flow is a legitimate boundary condition for a forward geotherm. It does not uniquely determine the internal heat-producing structure. A common 1-D steady conductive relation is surface flux = reduced/basal flux + integrated crustal radiogenic production. Crust thickness alone is not a heat-flow predictor; global compilations report no positive crust-thickness/surface-flux correlation.
5. ARCANA v2 already has a cell-supported continental domain reference heat-flow field. It is partial and not a global or FEG-node flux field. It can constrain a continental input/model, but cannot supply ocean heat flow or unique internal geotherms.
6. Published numerical ranges are material-, temperature-, pressure-, tectonic-, and model-dependent. They are evidence for candidate priors/ensembles, not values to copy into ARCANA. ShellSet's q-limits and correction branches are consequential model controls and require separate governance/sensitivity analysis.

## Evidence table

| Evidence | Finding and evidence type | Relevance and limitation |
|---|---|---|
| Stein & Stein (1992), GDH1 | Joint model of global depth and heat flow versus ocean lithosphere age; original empirical/physical plate-model fit. [Nature paper](https://www.nature.com/articles/359123a0) | Direct provenance for ShellSet's positive-age relation, not validation for an ARCANA ocean or its T0 age generator. |
| Stein & Stein (1994) | Global observed heat flow differs from conductive cooling predictions; paper estimates hydrothermal contribution and age-dependent sealing, with sampling caveats. [JGR paper](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/93JB02222) | Observations/model inference about modern Earth oceans; not a per-node hydrothermal correction law. |
| Grose & Afonso (2013) | Comprehensive plate-model comparison; young-ocean heat flow varies with crust insulation and hydrothermal treatment, and alternative model forms differ substantially. [G3 paper](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/ggge.20232) | Demonstrates model-form uncertainty; fitted to Earth observations. |
| Holdt et al. (2025) | Current reassessment of plate models using revised depth/temperature data; plate models generally outperform simple half-space at old ages, but alternatives and inversion tradeoffs remain. [JGR paper](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2024JB029890) | Useful model-family review; results remain Earth calibration. |
| Korenaga & Korenaga (2021) | Variable-property half-space reference model with conduction, internal heating/secular-cooling corrections and age-dependent parameterization. [JGR paper](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2020JB021528) | Alternative physical model family; not identical to constant-property textbook HSC. |
| Hasterok (2007) | Continental steady 1-D geotherms; parameter examples for conductivity, heat production, adiabat and expansion; notes geotherms correlate poorly with continental age. [JGR paper](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2006JB004663) | Parameter examples and framework, not universal distributions or ARCANA material data. |
| Mareschal & Jaupart (2016) | Review of crustal radiogenic production and continental thermal evolution; vertical/lateral heterogeneity and lack of global crust-thickness/heat-flow correlation emphasized. [Lithos review](https://doi.org/10.1016/j.lithos.2016.07.017) | Supports rejecting thickness-only heat-flow inference and uniform crustal production. |
| Pollack et al. (1993) | Global heat-flow compilation, with estimated continental/oceanic means and corrections. [Reviews of Geophysics](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/93RG01249) | Modern Earth empirical context only; not a synthetic 210 Ma target. |
| Qualified ShellSet extraction | MOD_Data.f90 age law and q-limit/correction order; OrbData5.f90 compiled limit constants and input/output binding. [FAIR extraction in repository](R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.md) | Implementation authority for the qualified build, not independent physical validation. |

## A. Oceanic heat-flow model comparison

### Classical conductive models

For a constant-property, semi-infinite half-space initially hot and cooled at a fixed surface temperature, the surface conductive heat flux scales as:

**q(t) = k (T_i - T_s) / sqrt(pi kappa t)**

where k is conductivity in W m^-1 K^-1, kappa is diffusivity in m² s^-1, t is elapsed time in seconds, and temperature is in K. Thus q is proportional to t^-1/2. It is a useful young-lithosphere conduction approximation, but it has no finite old-age steady plateau: it continues cooling/subsiding without limit. Its q(t) also diverges as t approaches zero; the singularity identifies the idealized boundary condition, not infinite measurable ridge flux.

A plate-cooling model imposes a finite lithosphere thickness or fixed basal temperature/heat resupply. The thermal boundary layer approaches a steady thickness, yielding finite old-age depth and heat-flow asymptotes. Parsons & Sclater (1977) and Stein & Stein (1992) fit variants to seafloor depth and heat flow. Modern model comparisons generally find plate formulations fit old seafloor better than simple half-space cooling, while the inferred basal temperature/thickness depend on datasets, material properties, crustal insulation and hydrothermal treatment.

### GDH1 and the ShellSet expression

GDH1's published surface heat-flow fit is commonly written in mW m^-2 with age in Ma:

- q = 510 / sqrt(t), for 0 < t <= 55 Ma;
- q = 48 + 96 exp(-0.0278 t), for t > 55 Ma.

Divide by 1000 to express q in W m^-2. These become 0.510/sqrt(t) and 0.048 + 0.096 exp(-0.0278t), exactly the positive-age constants in the qualified ShellSet source. The 55 Ma switch joins the branches continuously (approximately 68.8 mW m^-2); the old-age asymptote is 48 mW m^-2. The source comments explicitly attribute this branch to the preferred GDH1 model and cite Stein & Stein (1992).

**Age <= 0 is different:** GDH1's inverse-square-root formula is undefined at zero and diverges from the positive side. Qualified ShellSet instead assigns qLim1 for age<=0. That is an implementation boundary treatment, not a GDH1 equation or observed finite ridge value. It is also coupled to qLim1's independent role as the upper cap.

GDH1 is an empirical age relation built from Earth depth and heat-flow constraints. The observed seafloor heat-flow database is affected by hydrothermal advection and sampling (heat-flow probes require suitable sedimented sites). Stein & Stein (1994) inferred that roughly 34% of their predicted global oceanic heat flux was carried hydrothermally and estimated a sealing age near 65±10 Ma, while warning that the global estimate was an upper bound because of sampling bias. Those are global Earth inferences with substantial observational limitations, not a correction that can be added uniformly to every young ARCANA cell.

### Young-crust hydrothermal effects and other formulations

At young ridge flanks, observed conductive flux can fall below pure conductive cooling predictions because seawater circulation moves heat advectively. At the ridge axis and focused discharge sites, local flux can instead be anomalously high. Hydrothermal effects depend on permeability, crustal structure, sediment cover, fluid pathways and age. Comprehensive models including oceanic crust and hydrothermal circulation can predict substantial departures from GDH1 over young ages; the sign and spatial location depend on whether flux means local measured conductive flux, total advective-plus-conductive energy loss, or area-averaged lithosphere cooling.

The 2021 Korenaga reference formulation adds variable material properties and corrections for internal heating/secular cooling to a half-space-style conduction solution. The 2013 Grose/Afonso comparisons include crust insulation and axial hydrothermal circulation; their preferred models differ from simple age^-1/2 over young ages. The 2025 Holdt reassessment fits plate models to updated age-depth/temperature evidence and shows inversion tradeoffs; it cautions that joint heat-flow/depth fits can pull parameters away from independent petrologic constraints. These are candidate model families, not a consensus that one single law is suitable for all synthetic planets.

**For ARCANA:** the existing oceanic_lithosphere_age_ma field is an age primitive on ocean support, generated from selected divergent-source geometry using a monotone distance transform with no constant spreading-rate claim. It may be supplied to a selected model. It does not prove that modern-Earth GDH1 coefficients, ridge/hydrothermal processes, or present-day Earth age-depth calibration apply to the 210 Ma synthetic world.

## B. Continental surface heat flow

For a one-dimensional steady conductive column, take z positive downward and upward heat flux q. Conservation gives dq/dz = -A(z), where A(z) is volumetric heat production in W m^-3. Therefore:

**q_surface = q_base + integral[0,H] A(z) dz**

where q_base is the upward flux crossing the base of the radiogenic layer. For an exponentially decreasing upper-crustal source A(z)=A0 exp(-z/D), the crustal contribution through thickness H is A0 D [1-exp(-H/D)] (W m^-2). This shows why surface flux, basal flux, heat-production amplitude/depth scale, layer thickness and thermal state are coupled. Conductivity controls the temperature gradient (Fourier law), while the flux divergence is controlled by internal sources; a flux boundary alone does not recover the source distribution.

Continental heat production is compositionally stratified and laterally variable. Upper crust is commonly more enriched in U, Th and K than lower crust; lower-crust and lithospheric-mantle contributions are lower and material dependent. The 2016 review reports no global positive relation between crust thickness and surface heat flow: crustal production is not constant. Continental thermal/geotherm state also does not map simply to tectonic or rock age. Lithospheric thickness constrains structural extent but does not uniquely fix surface flux.

A prescribed surface heat-flow field is a legitimate Neumann boundary condition for a forward thermal model. It is not necessary to separately expose all source layers if the only contract is “solve a geotherm consistent with prescribed q and other boundary conditions.” However, if the goal is to explain or evolve internal T(z), basal flux, density, or radiogenic decay, the layer source distribution, conductivity, geometry and basal/initial conditions are needed. Multiple internal source distributions can produce the same surface flux.

### Existing ARCANA continental reference

The B_PANGAEA_LIKE_LATE_TRIASSIC_v2 manifest contains continental_reference_surface_heat_flow_w_m2 and continental_thermal_domain_id. The specialist-materialization report classifies support as continental-only and reports global heat flow MISSING, oceanic field MISSING, per-node lineage NOT_YET_ASSEMBLED, and INCOMPLETE_CONTINENTAL_SUPPORT_ONLY. The field can constrain a continental branch or be directly used as its input only after ARCANA governs that role, uncertainty, domain transitions and projection. It cannot fill the ocean or supply a unique continental vertical heat-production profile.

For any coupled continental model, existing crustal_thickness_m and continental_reference_lithosphere_thickness_m provide geometry. Neither determines heat flow without assumptions about radiogenic sources, conductivity, basal flux, thermal/tectonic history and lateral heterogeneity. Existing topography/bathymetry may enter boundary conditions and isostatic calculations, but must not be converted into flux by an undocumented proxy.

## C. Thermal material parameters and ranges in literature

The values below are **Earth literature/model constraints**, not ARCANA recommendations. Ranges often combine different rocks, temperatures, pressures and inversion choices; they should seed evidence review or uncertainty axes only after selecting analogous synthetic material families.

| Quantity | Published examples/range | Meaning and evidence type | Variation/limitation |
|---|---|---|---|
| Crustal thermal conductivity k | 2.54–2.55 W m^-1 K^-1 is used as average crust in a continental geotherm study; Hasterok sets upper crust 3.0 and lower crust 2.65 W m^-1 K^-1 at STP for felsic/mafic crystalline analogues. | Model inputs grounded in rock/mineral properties; not one global measured interval. | Lithology, porosity, fluids, temperature and pressure matter. Chapman-style P/T-dependent conductivity and radiative mantle contribution are used in geotherm models. |
| Mantle/lithosphere conductivity | Example upper-mantle reference model 3.2 W m^-1 K^-1; other plate/geotherm models use temperature/pressure dependent conductivity and radiative terms. | Model parameter or experimentally constrained constitutive function. | Do not collapse into a fixed universal k; temperature/pressure dependence can materially change inferred profiles. |
| Volumetric thermal expansion alpha | Hasterok uses 3.0e-5 K^-1 in crust and 3.2e-5 K^-1 in mantle; cited mantle predictions 3.04–3.47e-5 K^-1. Other mantle model tables use about 4e-5 K^-1 at reference conditions. | Literature/model values for thermal buoyancy/geotherm calculations. | Material-, temperature-, pressure- and averaging-dependent; ranges are model-specific rather than a statistical confidence interval. |
| Radiogenic production A | Example upper continental crust 0.9–3.25 μW m^-3; lower crust 0.12–0.5 μW m^-3; lithospheric mantle examples about 0.01–0.1 μW m^-3. | Compiled rock/geochemical and thermal-model estimates. | Strong lithologic/province heterogeneity; crustal values decay over deep layers and through geological time. Review estimates crustal radiogenic surface contribution spans 18–48 mW m^-2, most likely 21–34 mW m^-2, under stated Earth compositional assumptions. |
| Density rho | Example geodynamic/geophysical models use bulk continental crust near 2,830–2,835 kg m^-3; upper/lower crust reference layers often differ (model examples around 2,700 and 2,940 kg m^-3); mantle reference values commonly around 3,200–3,300 kg m^-3 in specific models. | Seismic/compositional constraints or model reference densities. | Density is not a heat-flow coefficient, but couples thermal expansion and isostatic/geotherm corrections. Composition and depth vary; these are not ARCANA material assignments. |
| Surface/reference temperature | Studies commonly impose an explicit surface boundary; examples include 273 K (0°C) for ocean models and 293 K (20°C) in a continental thermal calculation. | Boundary-condition convention/model input, sometimes motivated by environment. | A 210 Ma synthetic climate/surface boundary is not given by the Earth examples. Govern independently; don't infer from heat-flow data. |
| Mantle/asthenosphere thermal reference | Hasterok's continental geotherm example uses potential temperature 1300°C with adiabat slope 0.3°C km^-1; Korenaga's 2021 ocean model uses initial potential temperature 1623 K (1350°C) and surface 273 K. | Model boundary/reference settings, constrained by geophysical/petrologic inversion. | Potential temperature is not identical to actual basal temperature; Earth-era/planet differences and inverse tradeoffs are material. These examples do not select ARCANA TADIAB/GRADIE. |
| Geothermal gradient | Not a free universal scalar when q, k and A(z) are specified: dT/dz follows Fourier conduction and varies with depth as q(z)/k(T,P). Hasterok's profile family spans surface flux 40–100 mW m^-2 as an Earth model sweep. | Derived profile/model output. | One gradient number cannot represent layered radiogenic crust plus mantle adiabat; do not set GRADIE as a whole-lithosphere gradient. |

Material contrasts are real: upper/lower crust, oceanic crust, depleted/enriched mantle lithosphere and asthenosphere need not share properties. Surface temperature or a chosen reference adiabat may be global specialist boundary settings for one run, but should be versioned and sensitivity-tested. Conductivity, expansion, density, heat production, temperature limits and geotherm parameters require material/domain treatment where the chosen model resolves those distinctions.

## D. Very young ocean and age zero

- In half-space cooling and GDH1 positive-age branches, q proportional to t^-1/2, so the mathematical conductive prediction diverges as t→0+. That is a singular idealization of a semi-infinite initial condition, not evidence for infinite finite-area ridge flux.
- A real ridge has a finite axial width, magmatic accretion/latent heat, three-dimensional advection and hydrothermal circulation. Point measurements may miss diffuse heat or sample sedimented lows; focused vent discharge can be locally high.
- A finite value at exactly age zero is therefore a model/interface requirement if a numerical field must be finite, but a chosen cap is a regularization/model rule unless linked to an explicit finite-width/ridge and advective physical model. It is not an observed universal ridge flux.
- Qualified ShellSet maps age<=0 to qLim1. Since qLim1 is also the global upper cap, its age-zero role should be reviewed independently and tested for sensitivity. Literature does not validate qLim1 specifically as physical age-zero heat flow.
- ARCANA's zero-age ocean cells are part of its governed age primitive; the physical semantics and relation to ridge/source boundaries remain an authorial/model decision. Do not treat age zero as missing data or automatically replace it with a modern Earth ridge observation.

## E. q-limit controls and geothermal corrections

Qualified source semantics, rather than parameter names, establish these effects:

| Control | Qualified ShellSet behavior | Literature interpretation |
|---|---|---|
| qLim0 | Lower heat-flow threshold at zero elevation; used in qLimit = qLim0 + dQL_dE * elevation. Current qualified source compiles 0 W m^-2. | A model control with direct flux effect. No reviewed literature establishes this exact threshold as universal physics. |
| dQL_dE | Slope of the lower threshold versus elevation; current qualified source compiles zero (W m^-2)/m. | Elevation-dependent floor is implementation/model parameterization. A physical relation needs explicit derivation; name alone does not make it a law. |
| qLim1 | Upper cap at all nodes; source also assigns it as heat flow for ocean age<=0. Current qualified source compiles 0.300 W m^-2. | As a generic cap it is a clipping/guard; when used as a value at age zero it changes the physical output. No universal geophysical cap at this exact level is demonstrated by these sources. |

The model first fills zero nodes from qArray, may replace that fill with the ocean age law, then clamps. Nonzero FEG values bypass both qArray and age-law fill, but remain subject to clamps and may be altered by the geotherm consistency branch. That later branch adjusts heat flow if the trial Moho temperature exceeds TAsthK, then reclamps. These are coupled specialist-model operations, not independent evidence that the input field was physically inconsistent.

Scientific disposition options: retain qualified behavior explicitly as inherited ShellSet configuration; govern bounded ranges with reasons; or change the model/control semantics only under a separately qualified patch. All alternatives require sensitivity of nodal flux, geotherm, and derived density/thermal outputs. No literature basis found here supports choosing the exact ShellSet defaults as ARCANA values.

## F. Three architecture options

| Dimension | A — explicit global T0 flux | B — derive from primitives/model | C — hybrid |
|---|---|---|---|
| Required data | Complete ocean+continent field on cells/nodes; masks, uncertainty, provenance, units; zero-safe adapter | Domain, age/history, continental structure/reference, material properties, heat production, model equations/version and boundaries | Governed continental reference field plus ocean age/model and explicit role/mask/interface; uncertainty for both branches |
| Existing ARCANA fit | Existing continental reference can cover/constraint only its current domain; ocean flux absent | Uses age and domains, thicknesses, thermal domains/references, elevation only where model justifies; none alone completes flux | Directly preserves the distinct evidence already available: continental reference plus ocean age primitive |
| Assumptions | Flux is authoritative T0 state or externally generated and then versioned | Physical model maps primitives and parameters to flux; ocean/continent models may differ | Continental reference is authoritative or target while ocean flux is model output; branch transition must be explicit |
| Duplicate-state risk | High if independent age/geotherm model also produces flux; settle input/reference/cache role | Lower if flux is derived cache; reference field remains separate constraint | Medium: controlled if continental reference remains its own named authority and ocean flux remains derived |
| Provenance | Per-cell/node lineage to authoring or model and projection | Model version plus all input hashes and parameter set | Separate field-level lineage per branch and transition |
| Uncertainty | Attach uncertainty to explicit field and interpolation | Propagate age, model form and material parameters | Combine distinct continental-reference and ocean-model uncertainties without implying same evidence type |
| Selective replay | Straightforward region updates if field is tiled with stable identities | Dependency-aware recomputation can update only affected regions | Branch-wise replay possible; domain transitions invalidate adjacent projections/coupled cells |
| Future T0→T1 | Initial state only; temporal evolution still needs a law | Supports recomputation if temporal model/forcing/history is specified | Can evolve the branches only after both continental and oceanic temporal semantics are defined |
| OrbData fit | Nonzero nodal flux bypasses qArray/age fill but still clamps/correction; exact-zero-safe export needed | Zero sentinel routes to qArray then possibly age override; avoid accidental sentinel or govern qArray | Can provide nonzero continental references and derived ocean flux, but limits/correction still apply; preserve lineage through mapping |
| Unsupported reconstruction risk | Low if explicit field has a source; high if gaps are filled by unjustified interpolation | High if models require unavailable ridge history/materials or infer flux from unsupported proxies | Reduced only for the already covered continental reference; ocean model and transitions remain assumptions |

No architecture is ranked. The explicit field has lower model-generation burden but still needs ocean flux and a role for the current continental references. Primitive-derived flux gives causal/replay structure but needs more model and parameter authority. Hybrid aligns with current field coverage but increases branch/interface governance and can duplicate state if reference flux is mistaken for both a target and a final output.

## G. Uncertainty, sensitivity, and limitations

1. **Separate uncertainty classes:** authored primitive uncertainty (including age support), model-form uncertainty (half-space/plate/variable-property/hydrothermal), material-property and heat-production uncertainty, and numerical projection/adapter uncertainty.
2. **Do not convert Earth spatial observations into independent cell samples.** Heat-flow observations have uneven geographic coverage, sediment/probe selection bias, corrections, and spatial correlation. Published global means or province averages are contextual constraints, not per-cell distributions for a synthetic 210 Ma world.
3. **Correlate parameters:** conductivity, radiogenic production, basal heat flow and crustal layering can trade off in geotherm inversions. The same surface flux may support multiple subsurface structures.
4. **Test branch sensitivity:** age near zero, the GDH1 55 Ma transition, old-age plateau, domain margins, qArray fallback, q limits, and geotherm corrections. Report before/after clipping and correction magnitude.
5. **No single exact ranges are universal.** The numerical examples in section C are model-specific published constraints; uncertainty and material applicability differ. ARCANA should first choose analogical material families/physics, then define ensemble distributions rather than copy a center value.

## H. Parameterization options, not selection

These are options for the next governance step:

- **Ocean:** GDH1 reference age relation; an alternative plate-cooling model with joint depth/heat-flow fit; variable-property half-space/plate model; or a model with explicitly represented hydrothermal/axial effects. Record whether output means conductive seafloor flux or total energy loss.
- **Continents:** use the existing reference flux as a prescribed boundary/reference; or derive flux from a layered steady/transient heat-production and basal-flux model constrained by that field. Do not infer layers from crust thickness alone.
- **Materials:** choose domain/material-family parameter distributions from cited rock/geochemical/experimental sources; carry covariance and P/T dependence where relevant.
- **Young ocean:** keep a finite interface rule as explicit numerical regularization, or select a physically resolved ridge/finite-width/advective model. In either case do not call qLim1 a measured physical cap without evidence.
- **q limits:** inherit the qualified behavior as an explicit model configuration, govern a sensitivity-bounded alternative, or modify the implementation only through separate review/qualification. These options are not endorsements.

## Exact next ARCANA decisions

1. Is continental_reference_surface_heat_flow_w_m2 the actual continental T0 flux, a constraint/target, or validation-only?
2. Is ocean heat flow an explicit T0 field or derived from oceanic_lithosphere_age_ma? If derived, which named/versioned physical model and what does its flux represent?
3. Does the GDH1 choice for ocean bathymetry also govern an ocean heat-flow law, or are those independent model choices?
4. What does ocean age=0 mean in the authored T0 state, and how is its interface value handled without silently treating qLim1 as physical?
5. What spatial support and interface rule applies at ocean/continent transitions, especially given ShellSet's exact-zero sentinel and age interpolation?
6. Which material families and layered thermal model govern conductivity, expansion, heat production, density, surface/reference temperature, adiabat and geotherm?
7. Are qLim0, dQL_dE and qLim1 retained, bounded, or replaced, and what sensitivity evidence is required for that disposition?
8. Are ShellSet geothermal corrections accepted as part of T0 specialist-derived state? What correction magnitude is acceptable under the selected configuration?
9. What uncertainty variables/correlations and acceptance diagnostics are mandatory for the approved model, its field projection, and selective replay?
10. What future thermal variables are state versus derived outputs in T0→T1, and what temporal physics/forcing must be authorized before evolution?

**Boundary preserved:** PRE_ORBDATA_ready=false; t0_orbdata_executed=false; shellset_mechanics_authorized=false; dt_selected=false; t1_created=false; forward_evolution_authorized=false. No ARCANA canon changed, no ShellSet source changed, no values selected, and no OrbData/SHELLS run.

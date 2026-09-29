# R6 PRE_ORBDATA Heat-Flow Targeted Research Closure

## Decision

**`R6_PRE_ORBDATA_HEAT_FLOW_PARAMETERIZATION_PARTIAL__TARGETED_RESEARCH_REMAINS`**

The heat-flow architecture remains `HYBRID_DOMAIN_AWARE_HEAT_FLOW`; this pass did not reopen A/B/C. HWR-2 is recommended as a transferable *model structure* with ARCANA-governed parameters. Numerical binding is not ready: ARCANA has no selected ocean age field, material/thermal parameter set, or finite ridge-axis state, and the existing ARCANA ocean OrbData branch replaces the supplied heat flow with legacy GDH1 values.

No producer was implemented; OrbData/SHELLS was not run; ShellSet was not modified; `PRE_ORBDATA_ready` remains false; no commit or push was made.

## Ocean model structure

### HWR-2

HWR-2 solves transient one-dimensional conduction through a finite plate with fixed surface and basal temperatures and constant properties. Let `kappa = k/(rho_m C_p)`. Its analytical surface conductive heat flow for positive age `t` is

```text
H(t) = k (T_b - T_0) / z_p
       * [1 + 2 sum(i=1..infinity, exp(-kappa i^2 pi^2 t / z_p^2))]
```

The corresponding thermal subsidence law also uses the plate thickness, temperature contrast, expansivity and densities. A finite series truncation and convergence tolerance are numerical choices. The required physical state is ocean lithosphere age (and a depth-temperature profile if the full profile is needed). Required parameters include conductivity, density, heat capacity, expansivity, surface and basal temperatures, and equilibrium plate thickness.

This is the preferred initial ARCANA candidate because it is compact, deterministic and provides an explicit heat-flow relation. That recommendation does not transfer Holdt et al.’s Earth fit values. In that paper, `k=3.8 W m-1 K-1`, `T_b=1326 C`, `z_p=105 km`, and the fixed ridge-depth value belong to an Earth calibration. A constant `k` in HWR-2 is an effective averaged property; ARCANA must govern its own value and domain.

HWR-2 heat flow scales directly with conductivity and temperature contrast, while conductivity, density and heat capacity also change diffusivity and therefore the age/thickness dependence. Plate thickness appears in both the leading factor and exponential modes. Published work highlights conductivity’s effect on fitted temperature and distinguishes near-surface conductivity sensitivity of heat flow from thickness-integrated effects on subsidence. It does not provide ARCANA-specific numerical bounds or a sensitivity sweep for ARCANA.

### HWR-3

HWR-3 numerically solves the one-dimensional transient heat equation with `k(T,P,X)`, `alpha(T,P,X)` and `C_p(T,X)`, a ridge initial thermal state, and optional insulating oceanic crust. The reported implementation uses a dunite conductivity parameterization, an expansivity relationship based on a particular figure in Bouhifd et al., and heat capacity for olivine composition 89% forsterite/11% fayalite. It uses a 6.4 km average crust in its Earth application. Those compositions, crust assumptions and fit values are not ARCANA defaults.

HWR-3 offers a richer temperature profile but requires composition, pressure/material laws, crust properties, initial and boundary profiles, discretization, convergence settings and deterministic replay. Current R6 T0 fields do not govern those inputs. The paper reports material sensitivity: adding its insulating crust changes the fitted temperature from 1174 C to 1326 C. That is evidence of model sensitivity, not an ARCANA heat-flow correction or uncertainty interval.

### Candidate comparison

| Candidate | Transfer judgment | Fit to current R6 T0 inputs |
|---|---|---|
| A. HWR-2 structure, re-govern parameters | **Recommend as structure.** Compact finite-plate conduction is transferable; Earth fitted values are not. | Better fit than HWR-3 for future low-dimensional ARCANA bindings, but actual ocean age and all thermal numbers remain unselected. |
| B. HWR-3 | Physically plausible when a composition-specific mineral/crust package is authorized. | Current fields do not supply its state or material/numerical inputs. |
| C. Another finite plate | No reviewed evidence shows a better structure for present R6 fields. | Could be reconsidered if an ARCANA-governed mechanism requires it. |

Holdt et al. find HWR-2 and HWR-3 both fit their Earth constraints well; HWR-2 is simpler, while HWR-3 represents property variation more directly. Neither result selects a model configuration for ARCANA. See [Holdt et al. (2025)](https://doi.org/10.1029/2024JB029890), especially its model equations, HWR-2/HWR-3 descriptions and sensitivity discussion.

## Earth-calibration transfer analysis

Do not inherit any best-fit or assumed Earth parameter. Separate candidate Earth fit parameters (`T_b`/`T_p`, `z_p`, ridge depth and effective HWR-2 conductivity) from material functions (conductivity, expansivity, heat capacity, density and composition). Laboratory-supported functional forms may inform an ARCANA material model after ARCANA selects the applicable materials and validity range. Earth olivine composition and effective averages remain model assumptions unless separately authorized.

The source paper’s HWR-2 calibration omits young observations under 5 Ma in its primary fit to avoid hydrothermal influence, and finds that adding young *subsidence* points barely changes its Earth fit. This fitting result does not establish an ARCANA minimum model age or authorize subtracting young-ocean heat-flow deficits.

## OrbData expected heat-flow quantity

The compatible input is **the upward conductive surface flux implied by the chosen thermal geotherm**, expressed in OrbData’s positive `heatFl` convention and W m-2. It is `q_s = -k grad(T) dot n_out`. OrbData’s `Assign` routine uses `heatFl/conduc(1)` as the crustal geotherm gradient and reduced flux after layer heat production for the mantle segment. The resulting profile is a piecewise conductive steady geotherm. There is no hydrothermal circulation or general advective heat-transport term in this path.

Therefore:

- Feed the conductive flux consistent with the selected producer geotherm/material model.
- Do not feed a young-seafloor measurement deficit caused by hydrothermal/advection as if it were a conductive flux.
- Do not label this input as total heat loss including advection.

There is an important consistency limit: passing HWR’s transient `H(t)` does not pass its full `T(z,t)`. OrbData reconstructs a separate steady layered geotherm and may adjust heat flow, curvature or thickness. The same conductivity/material definitions, heat production, boundary temperatures and selected thickness must be bound coherently before this hybrid can be considered physically consistent.

The current ARCANA ocean condition in the local source patch enters the age-dependent ocean branch, where positive ages replace `heatFl` with GDH1 and age zero assigns `qLim1`. The branch also computes oceanic mantle-lithosphere thickness using a GDH1 relation and hardcoded `h_plate=95000 m`. Thus the proposed ARCANA ocean path does not yet preserve a supplied producer flux or share an HWR thickness authority. This requires a source-path decision and later fair qualification; this research pass did not edit it.

## Young-ocean policy

For HWR-2, the Fourier sum has the small-age asymptote

```text
H(t) ~ k (T_b - T_0) / sqrt(pi kappa t),  as t -> 0+
```

So the idealized conductive flux is unbounded as positive age approaches zero. Exact `t=0` is not a finite-flux state of that fixed surface-temperature finite-plate solution. The plate model can specify the ridge boundary depth, but that does not provide a finite exact-age-zero surface flux. HWR-3’s numerical surface flux also depends on an explicitly specified initial ridge profile and discretization; the reviewed paper does not define a finite ARCANA ridge-axis flux boundary.

No positive minimum age is established by the reviewed evidence. It must come from an ARCANA finite-age cell averaging rule or spatial/time resolution decision, or from a separately governed ridge-axis boundary state. Hydrothermal effects remain outside this conductive producer and outside OrbData. A runtime cap is not a physical ridge boundary.

### Age-zero policy

**`MODEL_DOMAIN_UNKNOWN`**. The current governed T0 state has no finite ridge-axis condition or finite-age averaging convention. Keep exact-zero ocean cells unknown for the flux output until that choice is made; do not assign a finite number by clipping the mathematical limit.

## qLim compatibility

For an explicit nonzero FEG `heatFl=q` at elevation `E`, OrbData first computes

```text
qLimit(E) = qLim0 + dQL_dE * E
q_after_lower = max(q, qLimit(E))
q_after_upper = min(q_after_lower, qLim1)
```

The exact unchanged envelope is

```text
qLim0 + dQL_dE * E <= q <= qLim1
```

Below the lower line it raises the value; above `qLim1` it caps the value. If the lower line exceeds `qLim1`, the sequential operation returns `qLim1` for every input and no input can pass unchanged. The audited upstream constants are `qLim0=0`, `dQL_dE=0`, `qLim1=0.3 W m-2`; these are compiled source guards, not ARCANA-authorized physics.

At the `Assign` stage, the current patch’s ocean age branch replaces explicit `heatFl` before clamping. Later, if the computed Moho temperature exceeds `TAsthK`, the code reduces heat flow and clamps it again. Thus being inside the node-level envelope is necessary but not sufficient for end-to-end pass-through.

FEG zero also means “heat flow missing”: if any node is zero, OrbData reads `qArray`. Zero bypasses the node lower clamp but still passes through the upper `MIN`; a subsequent ocean age branch can replace it. The input format needs explicit validity/missingness separate from a numeric zero.

A finite nonbinding qLim envelope is possible only after the age domain and bounded material/model ensemble are selected. Derive the minimum and maximum producer flux over that domain, and derive the elevation term from an explicit physical rule (or explicitly declare an elevation-independent guard before setting its slope to zero). An arbitrarily near-zero age domain yields no finite HWR-2 upper bound, hence no finite nonbinding `qLim1`.

## Shared physical parameter authorities

| Parameter | Required class | Authority and binding rule |
|---|---|---|
| Conductivity `k` (`conduc_C/M`) | `FUNDAMENTAL_OR_MATERIAL_PROPERTY` | One material-specific authority shared by producer and OrbData. An HWR-2 effective constant that is fitted becomes an Earth-calibrated model parameter and must be re-governed for ARCANA. |
| Heat capacity `C_p`, density `rho`, diffusivity `kappa` | `FUNDAMENTAL_OR_MATERIAL_PROPERTY` for `C_p`/`rho`; `DERIVED_QUANTITY` for `kappa` | Derive `kappa=k/(rho*C_p)` from shared material values. Do not choose an inconsistent independent diffusivity. |
| Expansivity `alpha` (`alphaT_C/M`) | `FUNDAMENTAL_OR_MATERIAL_PROPERTY` | Share the same material law with producer and OrbData. It is needed for thermal subsidence if that output is selected. |
| Equilibrium plate thickness `z_p` | `ARCANA_AUTHORIAL_PLANET_PARAMETER` | Select one definition/distribution or derive it once from the selected model, then bind it into both producer and OrbData. Eliminate the independent GDH1/95-km ocean thickness source for ARCANA. |
| Basal or potential mantle temperature | `ARCANA_AUTHORIAL_PLANET_PARAMETER` | Govern whether this is actual basal temperature or potential temperature and bind the conversion consistently. Earth best-fit values are not authority. |
| Surface temperature `T_0` / `TSurf` | `ARCANA_AUTHORIAL_PLANET_PARAMETER` | One shared boundary value with explicit units and Celsius/Kelvin conversion; do not inherit Earth’s 0 C silently. |
| `TAsthK` | `DERIVED_QUANTITY` | OrbData computes `TADIAB + GRADIE * 100 km`; derive it from the selected adiabat. |
| `TADIAB`, `GRADIE` | `ARCANA_AUTHORIAL_PLANET_PARAMETER` | Govern the mantle adiabat together as one profile authority and bind it to the producer wherever the basal boundary uses that same adiabat. |
| `ZBASTH` | `ARCANA_AUTHORIAL_PLANET_PARAMETER` | Govern asthenosphere-base depth if part of the selected planetary structure; equate it to plate base only if definitions are explicitly identical. |
| `temLim_C/M` | `NUMERICAL_RUNTIME_GUARD` | Bound solver/profile temperatures after physical ranges are selected. It must contain the physical model range and must not replace boundary temperatures. |
| `qLim0`, `dQL_dE`, `qLim1` | `NUMERICAL_RUNTIME_GUARD` | Finite guards derived from supported elevation, age and physical parameter bounds. They are not the heat-flow authority. |

## Remaining numeric choices

No values are guessed. Still needed are: (1) ocean age field/support and finite age-zero rule; (2) material composition and conductivity, expansivity, density and heat-capacity laws; (3) surface and basal/potential temperature; (4) one equilibrium thickness authority; (5) ocean crust insulation and heat-production choices; (6) producer numerical tolerance/truncation if HWR-2 is adopted (or mesh/time controls for HWR-3); (7) `temLim` bounds; (8) a finite qLim envelope derived from the selected outputs and elevation range; and (9) an ARCANA-specific OrbData source path that consumes ocean flux and thickness without the GDH1 replacements.

## Implementation implications

Keep `HYBRID_DOMAIN_AWARE_HEAT_FLOW`. HWR-2 is the proposed candidate structure only. Preserve unknown age/flux support explicitly; do not use numeric zero as both value and missingness. Before implementation qualification, route the ARCANA producer’s conductive flux and thickness through OrbData without GDH1 replacement, bind shared material and boundary authorities, and derive guards from the bounded model domain. Verify both node-stage clipping and `Assign`-stage geotherm corrections. Keep stock-mode behavior unchanged and require the existing source qualification/regression path before claiming runtime qualification.

## Remaining unknowns and smallest blocker

The smallest scientific blocker is an authorial finite young/ridge-axis policy: either a finite boundary state at age zero or a minimum supported positive age justified by the declared spatial/time averaging. Until then HWR-2 flux has no finite maximum over the domain and no finite nonbinding `qLim1` can be established. Other model numbers remain deliberately unselected. Separately, the local source patch still replaces explicit ARCANA ocean heat flow with GDH1/qLim1 and derives thickness through GDH1/95 km; the runtime path must be corrected and fairly qualified before a numerical producer can actually feed OrbData.

## Preserved gates

- `PRE_ORBDATA_ready=false`.
- No producer implementation, OrbData/SHELLS run, ShellSet modification, fair qualification, commit or push occurred.
- Existing adapter and source-generalization gates remain in [R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json](/D:/corsi/Arcana/ARCANA_WORLD/R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json).

## Sources

- [Holdt, White & Richards (2025), *Revised Oceanic Plate Cooling Models*](https://doi.org/10.1029/2024JB029890): finite plate equations, HWR-2/HWR-3 parameterizations, young-observation treatment and conductivity sensitivity.
- [Grose & Afonso (2013), *Comprehensive plate models for the thermal evolution of oceanic lithosphere*](https://doi.org/10.1016/j.pepi.2012.12.001): physically richer oceanic plate modeling and thermal material parameterization.
- [Stein & Stein (1992), *A model for the global variation in oceanic depth and heat flow with lithospheric age*](https://doi.org/10.1038/359123a0): GDH1 legacy age relation referenced by the OrbData source branch.
- Local source evidence is recorded in [R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch](/D:/corsi/Arcana/ARCANA_WORLD/patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch); patch digest and qualification state are recorded in [R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json](/D:/corsi/Arcana/ARCANA_WORLD/R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json).

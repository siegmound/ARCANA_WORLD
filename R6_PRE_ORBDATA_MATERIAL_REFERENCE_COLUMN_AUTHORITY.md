# R6 PRE_ORBDATA Material / Reference-Column Authority

## Decision

**`R6_PRE_ORBDATA_MATERIAL_AUTHORITY_VALUES_SELECTED__THERMAL_COLUMN_COMPATIBILITY_BLOCKED`**

This pass audits existing values, then records a minimal authorial specialist reference set for the missing crust/asthenosphere properties, with literature priors and retained sensitivity ranges. It does **not** close the numeric thermal column: independent analytical checks show that HWR-2 transient surface fluxes and the authored thickness fields cannot generally be interpreted by OrbData's steady piecewise quadratic column while retaining one physical LAB/adiabat. Therefore the requested reusable `...MATERIAL_REFERENCE_COLUMN_V1.json` and heat-flow Config V1 are not created. The complete authority audit and numerical table are in the companion JSON.

## Existing authority audit

- **Already governed and reused:** A0.6D mantle `k=3.3 (3.0–4.1) W m⁻¹ K⁻¹`, `rho=3300 (3200–3400) kg m⁻³`, `Cp=1200 (1100–1250) J kg⁻¹ K⁻¹`, `alpha=3.0×10⁻⁵ (2.5–3.5×10⁻⁵) K⁻¹`, `T0=280 (250–300) K`, HWR `Tb=1680 (1523–1737) K`, `zp=100 (80–140) km`, and `rhoH2O=1000 (990–1030) kg m⁻³`. These are explicit specialist reference selections, not canon or Earth reconstructions.
- **Existing authored T0:** continental heat flow is 0.045/0.060/0.085 W m⁻² for COLD_STABLE/NORMAL/HOT_EXTENDED; total continental reference lithosphere thickness is 200/135/80 km. These remain field authorities and have no numeric uncertainty distributions. Physical crust thickness and ocean age remain authored fields.
- **Canonical:** `g=9.82 m s⁻²` remains the global planet parameter.
- **Absent before this pass:** crust bulk density, conductivity, expansivity, heat capacity and radiogenic production; asthenosphere reference density/potential-temperature binding; mantle-lithosphere heat production. No prior artifact was found governing them.
- **Examples explicitly excluded:** ShellSet Earth input values and `ZBASTH` example; HWR paper's Earth-fit parameters.

## Material classes

Use five classes only: `CONTINENTAL_CRUST_REFERENCE`, `OCEANIC_CRUST_REFERENCE`, shared `LITHOSPHERIC_MANTLE_REFERENCE`, `ASTHENOSPHERE_REFERENCE`, and `SEAWATER_REFERENCE`. Continental thermal classes continue to select authored surface flux and total thickness only; they do not become different compositions. No regional geochemistry or new historical field is asserted.

## Density authority

| Material | Nominal | Literature/sensitivity range | Binding |
|---|---:|---:|---|
| Continental crust | 2800 kg m⁻³ | 2700–2900 | OrbData continental `rhoBar_C` |
| Oceanic crust | 2890 kg m⁻³ | 2850–2930 | OrbData ocean `rhoBar_C` |
| Lithospheric mantle | 3300 kg m⁻³ | 3200–3400 | Existing shared HWR/OrbData `rhoBar_M` |
| Asthenosphere reference | 3300 kg m⁻³ at `Tp` | 3200–3400 | Same mantle authority at reference temperature; no invented chemical density jump |
| Seawater | 1000 kg m⁻³ | 990–1030 | Existing `rhoH2O` authority |

Crust selections are authorial reference proxies; they do not describe individual cells. Sources and provenance are linked in the JSON and reference list.

## Thermal property authority

For continental crust select `k=2.5 W m⁻¹ K⁻¹` (2.0–3.0), `alpha=3×10⁻⁵ K⁻¹` (2–4×10⁻⁵), and `Cp=1000 J kg⁻¹ K⁻¹` (800–1200). For ocean crust select `k=2.2 W m⁻¹ K⁻¹` (1.8–2.8), with the same reference alpha/Cp ranges. These are low-dimensional material proxies with literature priors, not inferred ARCANA composition.

Keep the existing mantle tuple intact. Derive `kappa=k/(rho Cp)`; do not add another independently tuned diffusivity. Surface `TSurf=280 K` stays shared where it is the same reference boundary.

## Radiogenic heat authority

Select one uniform bulk value per crust material, not layered B/C: continental `A_C=0.8 μW m⁻³` (0.4–1.2 sensitivity), oceanic `0.30 μW m⁻³` (0–0.50 sensitivity). Select mantle lithosphere `A_M=0.02 μW m⁻³` (0–0.04 sensitivity). These are authorial specialist values based on literature ranges, not T0 fields or reconstructed Earth history. Sammon et al. (2022) show crust production is composition-dependent and calculate Moho flux by subtracting integrated crust production from surface flux; that supports the balance equation, not transfer of their Earth inventory.

## Asthenosphere reference

Bind mantle potential temperature to the same HWR basal reference at nominal `zp=100 km`: `Tp=Tb−ΔTad(100 km)≈1638.8 K` at the nominal tuple. Use `dTad/dz=alpha*g*T/Cp` and its integrated form `T(z)=Tp exp(alpha*g*z/Cp)` for constant properties. The local gradient near the reference is about 0.41 K/km. `TADIAB=Tp`; `GRADIE` is a local compatibility parameter only, and `TAsthK` is derived at 100 km. `rhoAst` reuses mantle density at `Tp`; alpha also reuses the shared mantle value.

No universal `temLim` is chosen. The cited solidus literature shows composition, pressure, and water dependence; the source `temLim` also functions as an isostatic density cap rather than a true profile enforcement. A material solidus would require a separately specified physical model before runtime binding.

## HWR-to-LAB mapping

Select `zp` as **`TOTAL_THERMAL_LITHOSPHERE_THICKNESS`**: in HWR-2 it is the depth from the surface to the finite plate's lower fixed-temperature boundary, not mantle-only thickness. For geometric bookkeeping only, bind `h_mantle=zp−h_ocean_crust`, giving nominal 93.5 km and sensitivity 73.5–133.5 km for 6.5 km crust. Reject `zp<=h_crust`. Do not introduce another ocean-thickness authority.

This thickness map does not make the explicit layered steady profile equal HWR-2's age-dependent transient temperature profile. That distinction is central to the failed checks below.

## Continental geometry binding

Preserve the existing authored `continental_reference_lithosphere_thickness_m`: 200/135/80 km by class. Candidate mantle thickness is total minus cellwise crust thickness. Do not use HWR `zp` on continents. Surface flux remains authored and is not recalculated to fit a geotherm.

## Ocean geometry binding

Use the one HWR `zp` authority and authored ocean crust thickness, with fail-closed positive mantle residual. Exact age zero retains finite `q_ridge=0.3 W m⁻²`; it is never passed to HWR. The ridge's finite flux does not itself define a transient HWR initial profile.

## Isostatic binding

Use `rho_thermal=rho_ref exp[-alpha(T−T_ref)]` as the physically consistent finite-strain thermal form; the source's linear correction is only a first-order approximation and needs a matching reference-temperature implementation. Set crust reference temperatures to `TSurf` and mantle/asthenosphere density reference to `Tp`. Keep `delta_rho_chemical` separate; its current reference is zero because no compositional field is governed. Do not use source `±100 kg m⁻³` clipping as ARCANA physics; out-of-authority chemistry must fail closed. The density expression's numerical finiteness does not establish meaningful isostasy when temperatures are physically invalid.

## Curvature policy

Select **`CURVATURE_DISABLED_FOR_PRE_ORBDATA_REFERENCE_SOLUTION`**. A fitted curvature would mask the transient-versus-steady mismatch and can generate a Moho flux discontinuity. Require `q_above=q_below=q_s−A_C h_C` and continuous temperature. A future transient solver may reformulate curvature only if both layer balances and Moho flux remain conservative.

## Analytical column checks

Independent steady-layer calculation (no OrbData run), using nominal material values and representative authored geometries:

| Case | `q_s` W m⁻² | `h_C / H` km | `T_Moho` K | `q_Moho` W m⁻² | `T_base` K | Result |
|---|---:|---:|---:|---:|---:|---|
| Continental cold stable | .045 | 50 / 200 | 780 | .0050 | 939 | Too cold for shared asthenosphere reference |
| Continental normal | .060 | 35 / 135 | 924 | .0320 | 1863 | Above nominal adiabat |
| Continental hot extended | .085 | 25 / 80 | 1030 | .0650 | 2104 | Above nominal adiabat |
| Ocean youngest positive age | .47415 | 6.5 / 100 | 1678 | .47220 | 15030 | Steady profile diverges from HWR transient state |
| Ocean intermediate, 70 Ma | .06128 | 6.5 / 100 | 458 | .05933 | 2113 | Above basal reference |
| Ocean oldest, 160 Ma | .04765 | 6.5 / 100 | 418 | .04570 | 1686 | Near basal reference at nominal point only |
| Ridge | .300 | 6.5 / 100 | 1163 | .29805 | 9582 | Finite ridge flux does not define steady 100 km column |

The equations are `Tmoho=Ts+q hC/kC−AC hC²/(2kC)`; `qmoho=q−AC hC`; `Tbase=Tmoho+qmoho hM/kM−AM hM²/(2kM)`. All rows satisfy the prescribed surface flux and algebraic Moho flux continuity by construction, and have positive geometric layer thickness. The corner sensitivity sweep found no shared continental parameter corner placing all three class bases within 1600–1720 K while preserving nonnegative Moho flux. The youngest ocean steady base remains many thousands of kelvin even at low heat production/high mantle conductivity; `temLim` cannot be used to hide that. Density corrections at these temperatures are mathematically finite but physically meaningless. Therefore the analytical validation fails, including sensitivity and solidus plausibility.

## Material package status

The report records a reusable **candidate parameter set and its authority/provenance**, but no `R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json` is issued: the requested V1 is conditional on a physically valid numeric column, and the check fails. The previous material-parameter absence is addressed as authorial selections; the unresolved scientific blocker is now the coupling contract between HWR's transient producer state and OrbData's steady reconstructed profile, including the authored continental q/thickness classes.

## Config V1 readiness

**Not ready.** Do not construct heat-flow Config V1 from a geotherm known to violate the shared LAB boundary and temperature limits. The single remaining scientific blocker is `HWR_TRANSIENT_FLUX_TO_ORBDATA_STEADY_COLUMN_COMPATIBILITY`: the hybrid must consume a compatible age-dependent profile or another justified state mapping while preserving authored surface flux, thickness, and Moho energy conservation.

## Remaining implementation blockers

GDH1/qLim1 and thickness replacement still require ARCANA source bypass; no ShellSet changes or qualification were performed; canonical FEG support, UNKNOWN mask, and runtime qualification remain pending.

## Preserved gates

`PRE_ORBDATA_ready=false`; OrbData/SHELLS not run; ShellSet unmodified; runtime/mechanics qualification false; `dt_selected=false`; `T1_created=false`; forward evolution false; canonical T0 not promoted; staging untouched; no commit or push.

## Literature and authority sources

- Holdt, White & Richards (2025), [Revised Oceanic Plate Cooling Models](https://doi.org/10.1029/2024JB029890): HWR-2 formulation, age-dependent transient flux, and plate boundary meaning.
- Sammon et al. (2022), [Compositional Attributes of the Deep Continental Crust Inferred From Geochemical and Geophysical Data](https://doi.org/10.1029/2022JB024041): compositional dependence and energy balance; no Earth values transferred.
- Jaupart & Mareschal (2015), [Heat Flow and Thermal Structure of the Lithosphere](https://doi.org/10.1016/B978-0-444-53802-4.00126-3): crust conductivity and radiogenic heat production context.
- Christensen & Mooney (1995), [Seismic velocity structure and composition of the continental crust: A global view](https://doi.org/10.1029/95RG00259), and [oceanic crust: A global view](https://doi.org/10.1029/95JB03440): density context.
- Kumar et al. (2020), [LitMod2D 2.0](https://doi.org/10.1029/2019GC008777): representative oceanic crust parameters.
- Glazner et al. (2021), [Thermal Constraints on the Longevity, Depth, and Vertical Extent of Magmatic Systems](https://doi.org/10.1029/2020GC009459): representative rock heat capacity and conductivity.
- Phipps Morgan (2001), [Thermodynamics of pressure release melting](https://doi.org/10.1029/2000GC000049): adiabatic relation.
- Hasterok & Webb (2017), [On the radiogenic heat production of the continental lithosphere](https://doi.org/10.1093/gji/ggx024): mantle lithosphere production context.
- Till et al. (2010), [The effect of water on the mantle solidus](https://doi.org/10.1029/2010GC003234): no universal melting limit.

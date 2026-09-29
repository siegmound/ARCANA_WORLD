# R6 PRE_ORBDATA Thermal Reference-Column Contract

## Decision

**`R6_PRE_ORBDATA_THERMAL_REFERENCE_COLUMN_BLOCKED__ARCANA_MATERIAL_REFERENCE_COLUMN_AUTHORITY`**

The column equations, conservative Moho requirements, existing boundary heat-flow authorities, and shared HWR-2 parameters are explicit. Config V1 is not ready because ARCANA has not selected the material/reference-column package needed to calculate and check a numerical crust–mantle–LAB geotherm and isostatic density column. No physical values are guessed or copied from Earth examples.

## Physical column model

Use depth `z` positive downward. For a constant-property layer with conductivity `k`, volumetric heat production `A`, top flux `q_top`, and no transient/interface source:

```text
d/dz(k dT/dz) + A = 0
T(z) = T_top + q_top*z/k - A*z²/(2k)
q(z) = k*dT/dz = q_top - A*z
```

The minimum reference column is surface → crust → Moho → mantle lithosphere → LAB → asthenosphere reference. Temperature and conductive flux are continuous at material boundaries absent an authorized source/sink. Conductivity may jump, so the temperature gradient changes as `q/k`.

All previously closed decisions remain unchanged: `HYBRID_DOMAIN_AWARE_HEAT_FLOW`; authored continental class flux; HWR-2 structure and A0.6D parameter tuple; ocean age support; ridge `q=0.3 W m⁻²`; explicit ARCANA heat flow bypassing GDH1/qLim1; and the nonbinding `qLim0/dQL_dE` decision.

## Surface boundary

- `TSurf/T0 = 280 K`, A0.6D sensitivity 250–300 K. Bind OrbData `tSurf` only when it represents the same reference surface.
- Surface heat flux stays prescribed by its producer: continental 0.045/0.060/0.085 W m⁻²; positive-age ocean HWR-2; selected zero-age ridge 0.3 W m⁻².
- Solve inward from this flux. Never invert the profile to replace authored flux. An infeasible profile fails closed.

## Crust contract

Moho depth is the authored cellwise physical crust thickness, separate from thermal domain. Existing support includes normal ocean crust 6.5 km and continental physical crust in the 25–50 km domain; use the actual authored cell value. Do not infer composition from `COLD_STABLE`, `NORMAL`, or `HOT_EXTENDED`.

The minimum PRE_ORBDATA heat-production structure is **one uniform bulk-crust value per authorized crust material/domain**. Current T0 has no regional geochemical resolution, so no upper/lower layers or spatial composition are introduced. The needed `k_C`, `rhoBar_C`, `alpha_C`, bulk `A_C`, reference temperature, and solidus remain unselected.

## Moho contract

Require `T_C(h_C)=T_M(0)` and `q_M(0)=q_C(h_C)=q_s-A_C h_C`. Conductivity may change the gradient but not flux. No Moho source/sink is authorized.

## Mantle lithosphere contract

The A0.6D shared mantle values are `k=3.3 W m⁻¹ K⁻¹` (3.0–4.1), `rho=3300 kg m⁻³` (3200–3400), and `alpha=3.0×10⁻⁵ K⁻¹` (2.5–3.5×10⁻⁵). Bind the same effective mantle authority to HWR-2 and OrbData mantle consumer. HWR-2 also uses `Cp=1200 J kg⁻¹ K⁻¹` (1100–1250), `Tb=1680 K` (1523–1737), `T0=280 K` (250–300), and `zp=100 km` (80–140 km).

`A_M` is unresolved; zero is not an implicit default. HWR basal temperature and plate depth do not by themselves define OrbData's mantle-potential-temperature intercept or mechanical mantle thickness.

## LAB / asthenosphere reference

Define LAB as the modeled mantle-lithosphere base where the geotherm joins the governed asthenosphere adiabat. It is neither `ZBASTH` nor HWR `zp` by implication. If ARCANA later binds the HWR basal boundary as OrbData LAB, total thermal thickness is `zp` and mantle thickness is `zp-h_C`; reject nonpositive residual thickness rather than clamp it. That identity is not yet authorized.

The thermodynamic relation `dT_ad/dz = alpha*g*T/Cp` gives a local gradient of about `0.412 K/km` at A0.6D mantle point values and canonical `g=9.82 m/s²`. This is a derived slope, not a selected `TADIAB` value or approved constant-gradient convention. ShellSet's `TAsthK=TADIAB+GRADIE*100 km` needs an explicit intercept/depth mapping that agrees with the basal boundary across the full `zp` sensitivity range.

`temLim` is a Squeez density-integration cap, not a governed material solidus. Crust/mantle limits, `rhoAst`, `TADIAB`, `GRADIE`, and `ZBASTH` remain unresolved. The ShellSet Earth input example is excluded.

## Ocean column

For `t>0`, use A0.6D HWR-2 conductive surface flux. The nominal flux range over governed ages is 0.0476525–0.4741483 W m⁻²; full parameter sensitivity is 0.0322191–0.5815391 W m⁻². Never evaluate exact age zero through HWR-2.

HWR `zp` is the depth of the finite-plate basal isothermal boundary measured from its surface. It is a thermal model thickness, not inherently a mechanical thickness or mantle-only thickness. Only if ARCANA identifies that basal boundary with OrbData LAB may `h_M=zp-h_C` be used.

## Continental column

Retain authored heat flow and total reference lithosphere thickness:

| Thermal class | Surface flux | Total reference thickness |
|---|---:|---:|
| COLD_STABLE | 0.045 W m⁻² | 200 km |
| NORMAL | 0.060 W m⁻² | 135 km |
| HOT_EXTENDED | 0.085 W m⁻² | 80 km |

The mantle residual candidate is total thickness minus actual cell crust thickness and must be positive. With only broad stated extrema, this residual could span 30–175 km if extrema co-occur; actual cellwise combinations require the canonical field. Algebraic piecewise solutions exist for finite positive conductivities and finite heat production, but admissibility (monotonicity, basal join, temperature limits) cannot be established yet. Do not replace authored heat flow.

## Ridge column

On only the selected 108 zero-age ridge cells, use finite specialist boundary `q=0.3 W m⁻²`; do not call HWR at `t=0`. Keep authored zero-age state and explicit crust. Ridge mantle thickness and basal/LAB temperature need the same governed LAB mapping; ridge flux is closed but its full column is not.

## Radiogenic heat

Choose one uniform bulk-crust production parameter per authorized crust material/domain. Sammon et al. (2022) derive deep-crust composition and production using Earth geochemical/geophysical inputs and calculate Moho flux by subtracting integrated production from surface flux. This supports the energy balance form, but Earth's inventory is not an ARCANA parameter. No ARCANA value or uncertainty interval exists. Do not manufacture regional composition or a literature-derived range.

Use `q_Moho=q_s-A_C h_C`; for the full column `q_LAB=q_Moho-A_M h_M`, absent transients. Sensitivity must sweep future authored bounds for `A_C/A_M` and test flux positivity, temperature limits, and LAB match.

## Curvature correction

**Select treatment B: reformulate to preserve Moho flux continuity.** The audited legacy expression applies curvature with `k_M` when calculating mantle starting flux, while the crust-side correction depends on `k_C`; when they differ this creates an artificial Moho flux jump. No interface source exists to justify it.

For audited `cooling_curvature=c`, corrected mantle starting flux is `q_s-A_C h_C-c h_C k_C`. Seed mantle profile with the exact crust Moho temperature. Solve transient curvature jointly against the LAB boundary and layer balances; if no conservative solve is available, set curvature to zero for the reference solution and fail closed if the adiabat cannot be met. No implementation was made.

## Isostatic density

Bind thermal density as `rho_ref[1-alpha(T-T_ref)]` only after `rho_ref`, `alpha`, and reference temperature are authorized. Keep thermal contribution separate from chemical `delta_rho`. Do not infer chemistry from stress to hide an inconsistent column.

`rhoBar_M=3300 kg m⁻³` (3200–3400) and `rhoH2O=1000 kg m⁻³` (990–1030) are selected shared references. `rhoBar_C` and `rhoAst` are unselected. Source `delta_rho_limit=±100 kg m⁻³` is only an unqualified numerical guard; it cannot serve as chemical authority or silently clip anomalies.

## Parameter authority table

| Parameter | Value/range | Units | Authority and binding |
|---|---|---|---|
| `rhoBar_C` | Unselected | kg m⁻³ | Crust material/domain; OrbData |
| `rhoBar_M` | 3300 (3200–3400) | kg m⁻³ | A0.6D shared mantle; HWR and OrbData |
| `rhoAst` | Unselected | kg m⁻³ or profile | Asthenosphere reference; OrbData |
| `rhoH2O` | 1000 (990–1030) | kg m⁻³ | A0.6D water reference; OrbData |
| `alphaT_C` | Unselected | K⁻¹ | Crust material/domain; OrbData |
| `alphaT_M` | 3.0×10⁻⁵ (2.5–3.5×10⁻⁵) | K⁻¹ | A0.6D shared mantle; HWR and OrbData |
| `k_C` | Unselected | W m⁻¹ K⁻¹ | Crust material/domain; OrbData `conduc_C` |
| `k_M` | 3.3 (3.0–4.1) | W m⁻¹ K⁻¹ | A0.6D shared mantle; HWR and OrbData |
| `A_C` | Unselected | W m⁻³ | Bulk crust production; OrbData `radio_C` |
| `A_M` | Unselected; zero not implied | W m⁻³ | Mantle production; OrbData `radio_M` |
| `TSurf` | 280 (250–300) | K | A0.6D; OrbData `tSurf` where same surface |
| HWR `Tb` | 1680 (1523–1737) | K | Basal finite-plate boundary; not automatically `TADIAB` |
| `TADIAB` | Unselected | K | Potential-temperature intercept; OrbData |
| `TAsthK` | `TADIAB+GRADIE*100 km`; unresolved | K | Derived by audited OrbData source |
| `GRADIE` | Local estimate ~0.412 K/km; runtime convention unbound | K m⁻¹ | Thermodynamic relation; OrbData binding unresolved |
| `zp` | 100 (80–140) | km | A0.6D HWR thermal depth; OrbData mapping unresolved |
| Continental total thickness | 200/135/80 by class | km | Authored T0 field |
| Crust thickness | Cellwise; continental 25–50, normal ocean 6.5 | km | Authored physical Moho depth |
| `temLim_C/M` | Unselected | K | Composition/pressure-dependent solidus; OrbData |
| `ZBASTH` | Unselected | m | Separate mantle structural control; ShellSet |
| `gMean` | 9.82 | m s⁻² | Canonical global planet parameter |
| `delta_rho_limit` | Unselected; source ±100 not authority | kg m⁻³ | Specialist guard only after chemical bounds exist |

The JSON contains the full authority class, meaning, provenance, uncertainty, sensitivity requirement, and binding for every listed parameter.

## Profile consistency checks

Static/analytical only; no OrbData/SHELLS run.

- Surface condition passes by contract: prescribed domain `q_s` is retained.
- Temperature extrema are not numerically evaluable without `k_C`, `A_C`, `A_M`, and basal/adiabat mapping.
- Monotonicity requires `q_s-A_C h_C≥0` in crust and `q_Moho-A_M h_M≥0` in mantle (with curvature jointly solved); missing bounds prevent proof.
- Moho continuity is analytically specified; use exact shared temperature and `q_Moho=q_s-A_C h_C`, with curvature using `k_C`.
- LAB temperature cannot be evaluated without thickness meaning and adiabat intercept.
- Continental total classes 80–200 km exceed the broad crust domain 25–50 km; possible residual range is 30–175 km if extrema co-occur. Conditional ocean `zp-h_C=73.5–133.5 km` for 80–140 km `zp` and 6.5 km crust only if `zp` is LAB depth. Ridge thickness unresolved.
- `temLim` is unselected, so no temperature-limit pass is claimed.
- q extrema are covered: continental 0.045–0.085, ridge 0.3, ocean nominal 0.0476525–0.4741483 and sensitivity 0.0322191–0.5815391 W m⁻². Profile temperature extrema unavailable without full material vector.

## Config V1 readiness

**Not ready.** Do not create `R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_CANDIDATE_V1.json` from partial bindings. The smallest scientific blocker is one missing **ARCANA material/reference-column authority** binding bulk crust material and production, mantle production/solidus, asthenosphere reference, and HWR-to-LAB/adiabat/thickness meaning. These inputs jointly define one column energy balance and isostatic state; they are not independent blockers.

## Required source changes

1. Preserve explicit ARCANA producer `heatFl` through age handling and guard stages; GDH1/qLim1 overwrite remains legacy-only.
2. Remove independent GDH1/95-km ARCANA thickness path and consume one governed HWR/LAB mapping.
3. Preserve one Moho temperature and conservative flux; use `k_C` in curvature interface balance or an equivalent formulation.
4. Fail closed on profile/adiabat/solidus mismatch; never silently mutate governed flux or thickness.
5. Keep UNKNOWN distinct from numeric zero and retain provenance.

## Remaining blockers

**Scientific:** `ARCANA_MATERIAL_REFERENCE_COLUMN_AUTHORITY` (as above).

**Implementation:** correct source heat-flow/thickness path; implement conservative curvature after authority approval; qualify source-generalization and adapter through fair qualification; provide canonical FEG support with explicit UNKNOWN mask and complete nonzero coverage.

## Preserved gates

`PRE_ORBDATA_ready=false`; OrbData/SHELLS not executed; ShellSet unmodified; mechanics/runtime qualification false; `dt_selected=false`; `T1_created=false`; forward evolution false; canonical T0 not promoted; staging untouched; no commit or push.

## Sources

- Holdt, White & Richards (2025), [Revised Oceanic Plate Cooling Models](https://doi.org/10.1029/2024JB029890).
- Sammon et al. (2022), [Compositional Attributes of the Deep Continental Crust Inferred From Geochemical and Geophysical Data](https://doi.org/10.1029/2022JB024041).
- Phipps Morgan (2001), [Thermodynamics of pressure release melting of a veined plum pudding mantle](https://doi.org/10.1029/2000GC000049).
- Till et al. (2010), [The effect of water on the mantle solidus](https://doi.org/10.1029/2010GC003234).
- Local authority artifacts and source binding evidence listed in the JSON companion.

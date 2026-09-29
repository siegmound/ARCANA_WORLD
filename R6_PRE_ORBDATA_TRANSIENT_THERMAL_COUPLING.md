# R6 PRE_ORBDATA Transient Thermal Coupling

## Decision

**`R6_PRE_ORBDATA_TRANSIENT_THERMAL_COUPLING_CLOSED__CONFIG_V1_AND_IMPLEMENTATION_READY`**

The failed 15,030 K steady reconstruction identified an invalid representation, not bad HWR-2 or material constants. This closure uses HWR-2's transient ocean profile directly, derives instantaneous ocean LAB from its intersection with the governed mantle adiabat, projects the profile into conservative crust/mantle segments, and derives a boundary-matched transient rate for fixed-geometry continents. It preserves every governed surface flux and geometry. The mathematical/configuration contract is ready for implementation; runtime gates remain false.

## Legacy OrbData transient semantics

The qualified source excerpts are recorded in `R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.md`; source citations are to `MOD_Data.f90::Assign` and `OrbData5.f90`. Bird (2008), §4.6 describes the transient as a quadratic perturbation to the steady geotherm, zero at the plate top and base and maximal near mid-depth.

The extracted source constructs the steady reference as:

```text
T_C(z) = TSurf + (heatFl/k_C) z - A_C z²/(2 k_C)
T_M(x) = T_Moho + (qRed/k_M) x - A_M x²/(2 k_M)
qRed = heatFl - A_C h_C
```

The transient coefficient enters both layer quadratic terms. The extracted `Assign` expression reduces mantle Moho flux by `cooling_curvature*h_C*k_M`, while the crust-side derivative implies a correction using `k_C`. For unequal conductivities this produces a flux jump. The amplitude is selected to connect the mantle-base profile to `TAsthK` for current q/thickness inputs; it is zero when no correction is required. Surface heat flow enters the crust gradient and layer thickness enters the integration and endpoint conditions.

Two legacy mutation paths are separate from this useful transient representation:

1. If the steady Moho temperature exceeds `TAsthK`, `Assign` reduces `heatFl` by `-(TMoho-TAsthK) k_C/h_C`, then reapplies q limits.
2. If the transient profile develops an internal maximum above the asthenosphere, Bird's legacy rule reduces surface heat flow until the maximum equals asthenosphere temperature, then truncates lithosphere at that maximum. Bird reports this reduced ridge thickness as about 23 km for its Earth model; that value is not transferred.

The stock ocean path also uses GDH1 and a fixed 95 km scale; stock continental geometry uses S-wave travel-time estimates. Those source choices remain legacy-only. ARCANA uses their transient-profile idea, not their state mutation policy.

Bird explicitly characterizes the plate base as a typically isothermal boundary where the conductive geotherm bends toward the asthenosphere adiabat, and in §4.6 describes the transient quadratic and the q-reduction/thickness-truncation fallback. [Bird (2008)](https://doi.org/10.1029/2007JB005460)

## Steady-model failure interpretation

HWR-2's surface flux is from a transient cooling plate. Feeding that flux into a steady two-layer geotherm integrated through the full equilibrium depth creates the youngest-ocean 15,030 K artifact. It does not justify retuning governed k, rho, Cp, Tb, or zp. The transient profile must remain coupled to the flux that generated it.

## ARCANA transient column equations

Use `z` positive downward and `q=k dT/dz` as the positive-upward conductive heat-flow magnitude. In each layer:

```text
rho_i Cp_i dT_i/dt = d(q_i)/dz + A_i
dq_i/dz = rho_i Cp_i Tdot_i - A_i
q_i(x) = q_i(0) + (rho_i Cp_i Tdot_i - A_i)x
T_i(x) = T_i(0) + q_i(0)x/k_i
           + (rho_i Cp_i Tdot_i - A_i)x²/(2k_i)
```

### Continental derived transient rate

Continents have governed heat flow and total thickness, but no age-resolved HWR temperature parent. For the minimal reference correction, use one effective `Tdot` over the two layers and solve it from the LAB temperature condition. It is derived state, not a new canonical input.

```text
h_M = H_total - h_C
T_LAB = T_ad(H_total)
Tdot = (T_LAB - T_base_steady) / B
B = rho_C Cp_C [h_C²/(2k_C) + h_C h_M/k_M]
    + rho_M Cp_M h_M²/(2k_M)
```

This produces a unique finite correction when positive materials and layer thicknesses are supplied. Surface flux remains exact. Crust and mantle equations carry one shared temperature and heat flux through the Moho. If either layer flux turns negative or a profile has an internal maximum, the node fails closed.

### Ocean HWR-2 profile projection

For positive age, use HWR-2's analytical transient field:

```text
T_H(z,t) = T0 + ΔT z/zp
          + (2ΔT/π) Σ[n≥1] sin(nπz/zp)/n * exp(-κ n²π²t/zp²)
q_H(z,t) = k_H ΔT/zp * [1 + 2 Σ[n≥1] cos(nπz/zp)*exp(...)]
```

Use deterministic HWR truncation `N=256` and relative tolerance `1e-12` from A0.6D. Project to cubic Hermite segments using the parent profile endpoint temperatures and fluxes:

- Crust endpoints: `(0, TSurf, q_s/k_C)` and `(h_C, T_H(h_C), q_H(h_C)/k_C)`.
- Mantle endpoints: `(h_C, T_H(h_C), q_H(h_C)/k_M)` and `(h_LAB, T_ad(h_LAB), q_H(h_LAB)/k_M)`.

This preserves surface q, Moho temperature/flux, and LAB temperature exactly. Layer gradients may differ as required by conductivity. The projection residual defines a derived transient storage field through the heat equation; it does not add an independent source/sink.

## Surface boundary contract

Retain `TSurf/T0=280 K` nominal (existing 250–300 K sensitivity). Preserve authored continental q, positive-age HWR-2 q, and ridge `q=0.3 W m⁻²` exactly. ARCANA mode must never clip explicit q with `qLim1`, replace it with GDH1, or adjust it to fit the profile.

## Moho conservation contract

Require `T_C(h_C)=T_M(0)` and `q_C(h_C)=q_M(0)`. In the continental equation, mantle starts from the crust-derived interface T/q. In the ocean/ridge projection, both Hermite segments share HWR's Moho T and q; conductivity changes the gradient, not the flux.

Smallest source fix: compute mantle reduced flux from the crust-side Moho flux. In the legacy curvature convention, use `k_C` in the interface correction currently multiplied by `k_M`, or pass the shared interface flux as an explicit value. No Moho source/sink is authorized.

## LAB boundary contract

Derive the mantle adiabat from the existing A0.6G/A0.6D authorities:

```text
T_ad(z) = Tp exp(alpha_M g z/Cp_M)
Tp = Tb exp(-alpha_M g zp/Cp_M)
```

`Tp` is potential temperature at the reference pressure datum; `T_ad(z)` is actual temperature at depth `z`; the exponential increment is the adiabatic temperature increase. `TADIAB=Tp`; `GRADIE` is only the local derivative required by the legacy interface. Do not treat the 100 km source formula as a second independent temperature authority.

For ocean nodes, LAB is the shallowest positive depth where the HWR temperature meets/exceeds the adiabat; if the first intersection is at the plate base, use `zp`. Reject if `h_LAB<=h_C`. At LAB the temperature matches the adiabat; conductive q can enter the convecting reference and need not equal `k` times the small adiabatic gradient.

## Ocean HWR-2 projection

`zp` is the total finite thermal plate depth to HWR's lower isothermal boundary. It is not the instantaneous mantle-lithosphere thickness for every age. The selected LAB criterion yields these nominal results:

| Ocean age | HWR q | Derived LAB | Mantle thickness after 6.5 km crust |
|---:|---:|---:|---:|
| 1.1491667 Ma | 0.4741483 W m⁻² | 17.542 km | 11.042 km |
| 70 Ma | 0.0612828 W m⁻² | 100 km | 93.5 km |
| 160 Ma | 0.0476525 W m⁻² | 100 km | 93.5 km |

LAB depth is derived from the actual age-dependent state; `zp` is used only where the crossing is at its lower boundary. Nonpositive crust-subtracted thickness, absent crossing, nonfinite values, cubic overshoot, or nonmonotonic segments fail closed without parent mutation.

## Continental transient contract

Keep authored total lithosphere thickness and q exactly. Bind mantle thickness to total minus authored cell crust. Derive `Tdot` to make the profile reach the same adiabat at the fixed geometry.

| Class | q | Crust / total | Derived `Tdot` | Moho T | Moho q | LAB q | LAB T |
|---|---:|---:|---:|---:|---:|---:|---:|
| COLD_STABLE | .045 | 50 / 200 km | 3.6785×10⁻¹⁴ K/s | 831.5 K | .01015 | .02900 | 1721.3 K |
| NORMAL | .060 | 35 / 135 km | −1.7541×10⁻¹⁴ K/s | 912.0 K | .03028 | .02133 | 1694.0 K |
| HOT_EXTENDED | .085 | 25 / 80 km | −1.2992×10⁻¹³ K/s | 984.5 K | .05591 | .02651 | 1671.3 K |

All nominal rows are finite and monotone, retain the surface q, have positive layers, conserve flux and temperature at Moho, and meet the LAB adiabat. No q or geometry is adjusted.

## Ridge transient contract

Keep the authored age-zero state and `q=0.3 W m⁻²` on its 108 selected cells. Do not evaluate HWR at age zero. Invert the strictly decreasing HWR flux relation to obtain the derived positive equivalent thermal index `t_eff=2.87057 Ma`; this is not a change to world-history age. The HWR/adiabat first crossing gives `h_LAB=28.378 km` and mantle thickness `21.878 km` after crust subtraction. This yields a thin nonadiabatic lithosphere from current ARCANA boundary/model authorities. Bird's approximately 23 km is a comparison only, not a transferred value.

## Failure policy

Return `FAIL_CLOSED_WITH_DIAGNOSTIC` for nonfinite coefficients, negative thickness, Moho T/q discontinuity, LAB outside source geometry, nonmonotonic profile/internal maximum, profile outside the model domain, absent HWR inversion/crossing, or failed sensitivity member. Record node, parent hashes, algorithm/tolerances, and failed condition. Never lower q, truncate thickness, clamp temperature, or use chemical density anomaly to mask failure.

For numerical density integration only, set `temLim_C/M=1900 K` as a nonbinding numerical ceiling, not a physical solidus. The derived bounded profile envelope is below 1810 K; reaching the ceiling is fail-closed rather than clipped. Solidus interpretation remains distinct and material-dependent.

## Derived-state authority

Surface q remains governed parent or existing replayable physical state. Crust and continental total thickness remain authored T0 fields. HWR q/profile, derived ocean LAB, ridge equivalent thermal index, continental `Tdot`, and all curvature/Hermite coefficients are `DERIVED_REPLAYABLE_THERMAL_STATE`, never canonical primitives. Serialized OrbData values are `NUMERICAL_RUNTIME_INPUT_ONLY`.

## Static profile checks

The calculations used the A0.6G nominal materials, 256-mode HWR Fourier profile, and deterministic cubic Hermite projection. They are independent analytical/static work; OrbData/SHELLS was not run.

| Case | LAB | Moho q | LAB q | Moho T | LAB T | Minimum projected gradient | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Young ocean | 17.542 km | .334290 | .037186 | 1115.6 K | 1646.3 K | .01127 K/m | Pass |
| Ocean 70 Ma | 100 km | .060965 | .031246 | 400.5 K | 1680 K | .00947 K/m | Pass |
| Ocean 160 Ma | 100 km | .047622 | .044747 | 373.8 K | 1680 K | .01083 K/m | Pass |
| Ridge equivalent state | 28.378 km | .260829 | .020840 | 844.5 K | 1650.7 K | .00632 K/m | Pass |

All cases preserve surface q; all Moho interfaces conserve T and q; all have positive mantle residual, finite temperatures, monotone profiles and LAB/adiabat match. No 15,030 K artifact occurs. HWR maximum principle bounds temperature between its surface and basal temperatures. Continental `Tdot` denominator remains positive over material ranges; nominal columns pass. A sampled 256-corner material sensitivity sweep retained monotone q through Moho/LAB at 153/256 cold, 227/256 normal, and 239/256 hot combinations. Other corners violate monotonicity and are flagged invalid; no mutation is applied. For all sensitivity combinations, derived quantities stay finite; every HWR crossing and Hermite extremum must pass the same fail-closed checks before serialization.

## ShellSet patch contract

1. Preserve explicit ARCANA `heatFl`; separate validity mask from numeric zero.
2. Restrict GDH1 heat-flow replacement to stock mode.
3. Replace qLim1 mutation with ARCANA envelope assertion/fail-closed validation.
4. Implement HWR/Hermite ocean and ridge projection plus the analytic continental transient-rate solve.
5. Preserve authored crust and continental geometry; serialize derived ocean LAB geometry; remove GDH1/95 km geometry path and silent thickness truncation.
6. Pass shared Moho temperature and flux; use the conservative `k_C` interface term.
7. Fail closed on profile/limit failures. Preserve all legacy behavior outside complete ARCANA mode.

No source change is made in this closure.

## Config V1 readiness

**Ready to construct** `R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_CANDIDATE_V1.json` from the existing A0.6D/A0.6G authorities and this derived-state algorithm. Runtime readiness and qualification remain false. The scientific transient/steady incompatibility is closed by replacing the invalid steady reconstruction with the explicit transient representation.

## Remaining blockers

**Scientific:** none for this coupling contract.

**Implementation:** ARCANA-only profile solver and source bypasses; derived geometry/profile serialization; fair source qualification and stock regression; complete FEG support/UNKNOWN mask; full sensitivity ensemble validation before runtime claims. Keep `ZBASTH` in its distinct downstream structural role, not as a thermal-column authority.

## Preserved gates

`PRE_ORBDATA_ready=false`; OrbData/SHELLS not run; ShellSet unmodified; runtime and mechanics qualification false; `dt_selected=false`; `T1_created=false`; forward evolution false; canonical T0 not promoted; staging untouched; no commit or push.

## References

- Bird (2008), [Stresses that drive the plates from below](https://doi.org/10.1029/2007JB005460), §4.6.
- Holdt, White & Richards (2025), [Revised Oceanic Plate Cooling Models](https://doi.org/10.1029/2024JB029890).
- Local source excerpts: [R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.md](</D:/corsi/Arcana/ARCANA_WORLD/R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.md>).

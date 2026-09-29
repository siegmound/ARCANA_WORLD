# R6 T0 OrbData thermal binding closure

**Decision:** `R6_PRE_ORBDATA_THERMAL_BINDING_BLOCKED__ARCANA_REFERENCE_COLUMN_UNGOVERNED`

The existing evidence is enough to reconstruct what OrbData does, but not to establish a compatible ARCANA thermal profile. The smallest remaining scientific blocker is one missing authority: an ARCANA two-layer thermal reference-column contract that supplies the unresolved crust/mantle profile controls and defines how HWR-2 equilibrium thickness maps to per-node ShellSet lithosphere thickness. I did not create Config V1.

## Active thermal control flow

The audit uses the qualified source extraction in [R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.md](D:/corsi/Arcana/ARCANA_WORLD/R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.md), the read-only source copy under `%TEMP%\arcana_shellset_source_audit`, and the local proposed patch. The patch is not qualified, and no runtime was executed.

1. `OrbData5` reads nodal `dQdTdA` as `heatFl`. A zero value triggers heat-flow-grid fallback. Before `Assign`, it applies `qLimit=qLim0+dQL_dE*elev`, raises nonzero heat flow to that lower limit, then unconditionally caps heat flow at `qLim1`.
2. `Assign` interpolates seafloor age and crust thickness. In the local patch, `arcanaMode && arcanaOcean` enters the age-law branch: age zero substitutes `qLim1`; positive age substitutes GDH1. That overwrites explicit ARCANA heat flow.
3. `Assign` clamps crust thickness to `cLimit..hCMax`. Its current ARCANA ocean path still calculates total lithosphere thickness from GDH1 flux, `TAsthK`, `TSurf`, mantle conductivity, a hardcoded radiogenic helper, and `h_plate=95000 m`, then subtracts crust thickness and clamps to `hLMax`.
4. It builds a two-layer steady quadratic profile. In the crust, `TMoho=TSurf + heatFl*thickC/conduc_C - radio_C*thickC²/(2*conduc_C)`. The mantle starts with reduced flux `qRed=heatFl-thickC*radio_C`, then uses mantle conductivity and radiogenic production. If the computed Moho temperature exceeds `TAsthK`, `Assign` reduces heat flow and clamps it again.
5. A derived cooling-curvature term is adjusted so the mantle profile connects to the adiabat. If the chosen curvature would produce an internal temperature maximum, `Assign` reduces mantle thickness and recalculates curvature.
6. `Squeez` caps temperatures at `temLim` only during its isostatic density integration. It uses separate crust/mantle densities and expansivities, water density, asthenosphere reference density, gravity, and the geotherm to derive stress. `Assign` derives and limits chemical density anomaly, then checks pressure and adiabat mismatch.

This OrbData profile is not the HWR-2 transient temperature profile. It is a steady, piecewise quadratic fit using the passed heat flow and layer properties. A hybrid could be consistent, but the ARCANA material column and compatibility conditions have not been selected.

## Shared physical authorities

A0.6D's selected reference values are reused once: ocean effective mantle conductivity `k=conduc_M=3.3 W m⁻¹ K⁻¹`; mantle reference density `rho_m=rhoBar_M=3300 kg m⁻³`; mantle expansivity `alpha=alphaT_M=3.0×10⁻⁵ K⁻¹`; surface reference `T0=tSurf=280 K`; mantle heat capacity `Cp=1200 J kg⁻¹ K⁻¹` is used in HWR-2 diffusivity only. The HWR basal boundary is `Tb=1680 K`, and its fixed equilibrium plate thickness is `zp=100 km`.

These values do not fill the crust column. `conduc_C`, `radio_C`, `rhoBar_C`, and `alphaT_C` are distinct crust properties. `radio_M`, `rhoAst`, and both melting limits also lack ARCANA authority. HWR-2's `zp` is not automatically the per-node mechanical/thermal thickness `tLNode`.

## OrbData-only parameter binding

| Quantity | Declaration and active use | Classification | Binding |
|---|---|---|---|
| `alphaT_C` | `alphaT_C -> alphaT(1)`; temperature-dependent crust density in `Squeez`, then stress/mechanics | OrbData-only material configuration | Unresolved; no ARCANA crust material |
| `alphaT_M` | `alphaT_M -> alphaT(2)`; mantle thermal density | Shared authority | 3.0×10⁻⁵ K⁻¹ from A0.6D |
| `conduc_C` | `conduc_C -> conduc(1)`; surface gradient and crust geotherm curvature, affects Moho test and heat-flow correction | OrbData-only material configuration | Unresolved |
| `conduc_M` | `conduc_M -> conduc(2)`; reduced-flux mantle gradient and profile | Shared authority | 3.3 W m⁻¹ K⁻¹ from A0.6D; same reference as HWR-2 `k` under constant effective mantle assumption |
| `radio_C`, `radio_M` | `radio -> radio(1:2)`; profile curvature and crust-to-mantle reduced flux | OrbData-only material configuration | Unresolved; values depend on domain composition |
| `rhoBar_C` | `rhoBar_C -> rhoBar(1)`; crust reference density in stress/isostasy | OrbData-only material configuration | Unresolved |
| `rhoBar_M` | `rhoBar_M -> rhoBar(2)`; mantle reference density and HWR diffusivity | Shared authority | 3300 kg m⁻³ from A0.6D |
| `rhoAst` | Passed to `Squeez`; sets the deep reference density below its shallow transition | OrbData-only reference structure | Unresolved; not identical by definition to `rhoBar_M` |
| `rhoH2O` | Passed to `Squeez`; water-column reference stress | Shared aqueous authority | 1000 kg m⁻³ from A0.6D; salinity is not represented |
| `tSurf` | Surface boundary in both layer profiles | Shared authority | 280 K from A0.6D |
| `temLim_C/M` | `temLim(1:2)` caps temperatures inside `Squeez` density integration; it does not directly cap output `heatFl` or the profile polynomials | OrbData-only solidus controls | Unresolved; source Earth example values are excluded |
| `TADIAB`, `GRADIE` | `TAsthK=TADIAB+GRADIE×100 km`; TAsthK is Moho cap and mantle-base connection target | OrbData-only adiabat configuration | Unresolved as a governed pair and depth convention |
| `TAsthK` | Derived before node loop; compared to Moho and basal mantle temperatures | Derived OrbData state | Unresolved until `TADIAB/GRADIE` are bound |
| `ZBASTH` | ShellSet input; source example describes base of upper mantle/end of olivine-rich layer; not used in `Assign` profile equations | OrbData/ShellSet specialist control | Unresolved; 400 km Earth example is excluded |
| `qLim0`, `dQL_dE`, `qLim1` | Lower-line/upper heat-flow clamps before and after `Assign` corrections | Numerical guards | Stock source has 0, 0, and 0.3 W m⁻². Explicit ARCANA mode must not mutate `heatFl` through these clamps. |
| `cLimit`, `hCMax`, `hLMax`, `delta_rho_limit` | Crust/lithosphere and chemical-density limits | Numerical guards | Stock values exist, but compatibility with ARCANA domains must be checked before qualification |

The input values in `INPUT/iEarth5-049.in` are source examples, not ARCANA selections. They include crust/mantle conductivities, radioactive production, temperature limits, and surface temperature. They are excluded as authority.

`TAsthK` is explicitly computed as `TADIAB+GRADIE×100000 m`; it is not an independently read physical measurement. The adiabatic relation can estimate a gradient from material values (`dT/dz=alpha*g*T/Cp`), as discussed by [Phipps Morgan (2001)](https://doi.org/10.1029/2000GC000049), but it does not by itself select the reference temperature convention or `ZBASTH`. Likewise, [Till et al. (2010)](https://doi.org/10.1029/2010GC003234) shows solidus depends on composition and water, and [Sammon et al. (2022)](https://doi.org/10.1029/2022JB024041) documents compositional variation in crustal heat production. Neither supplies missing ARCANA domain composition.

## Hybrid profile consistency

The surface gradient is `heatFl/conduc_C`; it cannot be evaluated because ARCANA crustal conductivity is unselected. At the Moho the mantle gradient begins with `(heatFl-thickC*radio_C)/conduc_M`. It depends on the unselected crustal heat production. Thus the current data cannot establish Moho temperature, verify it is below `TAsthK`, or show `temLim` remains inactive.

Using the selected mantle conductivity only as a gradient scale, the nominal HWR-2 flux interval 0.0476525–0.4741483 W m⁻² corresponds to 14.44–143.68 K/km. That is **not** the crust surface gradient; substituting mantle conductivity into `conduc_C` would collapse two different materials. The result cannot be integrated through the 6.5 km ocean crust without the missing crust properties.

The geotherm is continuous at the Moho by construction, but its gradient may change there through material conductivity and heat production. No cross-cell continent/ocean interface condition is selected. Temperature-profile corrections can also change `heatFl` or thickness in current `Assign`. Therefore the global HWR/continental flux envelope is not enough to prove the OrbData profile is self-consistent.

The extracted curvature algebra exposes an additional source consistency condition: the crust-side flux at the Moho is `heatFl - thickC*radio_C - cooling_curvature*thickC*conduc_C`, while the code initializes mantle flux as `heatFl - thickC*radio_C - cooling_curvature*thickC*conduc_M`. They differ for nonzero curvature and unequal crust/mantle conductivity. No explicit interface heat source is authorized. The ARCANA path must use a flux-continuous interface expression or govern that term; the stock expression cannot be assumed physically continuous.

**Continent:** Ratified reference flux is 0.045/0.060/0.085 W m⁻² and reference total lithosphere thickness is 200/135/80 km for cold-stable/normal/hot-extended domains. The patch passes the total thickness on its ARCANA non-ocean branch, but later profile safeguards may reduce it. Geotherm compatibility is unproven without the reference-column material vector.

**Ocean:** HWR-2 supplies flux for 50,434 positive-age ocean cells over 1.1491667–160 Ma. The local patch still replaces that flux with GDH1 and still derives thickness from GDH1 plus 95 km. The HWR-2 equilibrium `zp=100 km` does not yet define an age-varying `tLNode`; a thermal-thickness mapping must be authorized.

**Ridge:** The explicit ridge boundary remains 0.3 W m⁻² on 108 cells; HWR-2 is never evaluated at age zero. The stock source happens to assign `qLim1=0.3` at age zero, but the numerical coincidence does not establish the ARCANA ridge profile. The ridge must receive the explicit boundary flux and a governed profile/thickness treatment.

## qLim and GDH1 preservation contract

With explicit ARCANA authority, preserve `heatFl` exactly. Bypass both GDH1 replacement and mutating `qLim1` clipping. `qLim0=0` and `dQL_dE=0` may remain only as a nonmutating assertion because the lower line is exactly zero; reject if validation fails. If the later geotherm consistency check would alter heat flow, fail closed. Only a separately governed ARCANA physical operation may change the value.

When ARCANA authority is absent, preserve the legacy GDH1/qLim behavior. Reject incomplete ARCANA input pairs; keep missingness in a separate validity mask, never as zero.

## Lithosphere thickness contract

Stock ocean thickness uses GDH1 heat flow, a 95 km plate reference, and a geometric-mean thickness, then subtracts crust and applies limits. Stock continental thickness comes from S-wave travel-time anomaly. The local patch replaces the continental value with requested ARCANA thickness, subject to later safeguards, but leaves the ocean stock branch active.

The ARCANA ocean path must bypass GDH1 and consume one governed projected thickness field. Before that implementation can be authorized, ARCANA must define how HWR-2's equilibrium `zp` maps to per-node mechanical/thermal lithosphere thickness. The values are physically related, but their equality is not established by the HWR-2 flux equation.

## Config V1 and implementation readiness

Config V1 is **not ready**. The single remaining scientific blocker is `ARCANA_ORBDATA_REFERENCE_COLUMN_CONTRACT_UNGOVERNED`: the coupled material/temperature column must govern `conduc_C`, `radio_C/M`, `rhoBar_C`, `rhoAst`, `temLim_C/M`, the `TADIAB/GRADIE` reference pair, `ZBASTH` if active in selected mechanics, and the mapping from HWR `zp` to age-dependent `tLNode`. These values cannot be selected independently without risking inconsistent or duplicated physical authority.

Once that scientific contract exists, implementation should separate into: (A) HWR/continental/ridge producer with masks and replay identity; (B) FEG projection that respects domain classes and reports error; (C) `src/OrbData5.f90` driver and `src/MOD_Data.f90::Assign` heat-flow preservation plus flux-continuous Moho correction; (D) `Assign` thickness preservation using the governed projected thickness. For explicit ARCANA inputs, before/after semantics are preserve-or-fail-closed. With ARCANA absent, retain stock behavior. No patch is implemented in this pass.

The requested output is **blocked**, so I did not create `R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_CANDIDATE_V1.json`. All preserved gates remain false: `PRE_ORBDATA_ready`, OrbData execution, ShellSet mechanics authorization, dt selection, T1 creation, and forward evolution.

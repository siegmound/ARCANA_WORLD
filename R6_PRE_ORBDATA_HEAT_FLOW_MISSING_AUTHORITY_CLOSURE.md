# R6 T0 heat-flow missing-authority closure

**Decision:** `R6_PRE_ORBDATA_HEAT_FLOW_MISSING_AUTHORITIES_CLOSED__CONFIG_V1_READY`

This closes A0.6C's two blockers for the heat-flow configuration: the existing ratified T0 age producer governs the entire ocean support, and this pass records an explicit ARCANA HWR-2 reference parameter set with uncertainty ranges. It does not qualify runtime, modify ShellSet, or promote candidate T0 to canonical. The full OrbData runtime configuration remains open for independent controls and hybrid consistency checks.

## Ocean support authority

The B-v2 realization is ratified for T0 materialization, with canonical promotion pending materialization validation. Its age source is [the T0 materializer](D:/corsi/Arcana/ARCANA_WORLD/src/arcana_worldsim/r6/t0_materialization/b_pangaea_v2.py:451): it selects the longest canonical branch among positive-normal ocean-ocean candidates, seeds both adjacent cells, then calculates spherical distance over the *entire connected ocean*. It requires finite distance for every ocean cell and assigns the monotone age transform on the complete ocean mask. It makes no constant spreading-rate claim.

The ratified `OCEANIC_AGE_STATE` contract governs a source-linked whole-ocean age field from 0 to 160 Ma with area-weighted median 70 Ma. Its divergent-boundary policy allows other divergence to remain rift or unknown. The age field contains 50,542 finite, nonnegative ocean values: 108 zero-age seed cells and 50,434 positive-age cells, spanning 1.1491667412–160 Ma.

The 1,072 cells previously marked unknown are in physical ocean domain 1 and have positive ages from this governed field. Their adjacency does not contradict the producer's specified whole-ocean age support. They are therefore classified `AUTHORIZED_POSITIVE_AGE_OCEAN`. No ages were changed and none were inferred to be ridge or rift cells.

| Outcome for the 1,072 cells | Count |
|---|---:|
| `AUTHORIZED_POSITIVE_AGE_OCEAN` | 1,072 |
| `RIDGE_OR_RIFT_SPECIAL_DOMAIN` | 0 |
| `UNKNOWN_INSUFFICIENT_AUTHORITY` | 0 |

The 634 unselected positive-normal ocean-ocean candidate segments remain process-unknown: kinematic signs are not geological process assignments. Their unique adjacent ocean mask has 1,075 cells, including 3 selected zero-age ridge cells and 1,072 positive-age ocean cells. The unknown segment classification does not erase neighboring age authority under the current ratified contract. Do not infer new ridge flux or local rift heating from those segments. If future physics requires a rift-specific thermal treatment, that must be an upstream T0 authorial boundary-process/thermal-domain revision.

## HWR-2 parameter authority

The primary-source HWR-2 surface-flux equation is `H(t)=k*(Tb-T0)/zp * [1+2*sum(i=1..N, exp(-kappa*i^2*pi^2*t/zp^2))]`, where `kappa=k/(rho_m*Cp)`. It is evaluated only for `t>0`. The equation and model discussion are in [Holdt et al. (2025)](https://doi.org/10.1029/2024JB029890).

This pass explicitly selects ARCANA reference values; the attached sensitivity intervals remain part of the configuration. For material parameters, published silicate-mantle models supply broad priors. The point values are not claimed as measurements of Arcana. Holdt's Earth-fit values (`k=3.8`, `Tb=1326 °C`, `zp=105 km`) are explicitly excluded as defaults. Independent petrologic temperature estimates summarized in Holdt inform the `Tb` sensitivity prior, not the selected fit.

| Parameter | ARCANA reference | Sensitivity range | Authority and use |
|---|---:|---:|---|
| `k` | 3.3 W m⁻¹ K⁻¹ | 3.0–4.1 | Effective silicate-mantle property; HWR-2 and OrbData ocean mantle `conduc(2)` share one authority. Crust `conduc(1)` stays distinct. |
| `rho_m` | 3300 kg m⁻³ | 3200–3400 | Mantle reference density; HWR-2 and OrbData `rhoBar(2)` share one authority. |
| `Cp` | 1200 J kg⁻¹ K⁻¹ | 1100–1250 | Mantle isobaric heat capacity; used to derive diffusivity, with no duplicate OrbData input. |
| `Tb` | 1680 K | 1523–1737 | ARCANA basal plate boundary; independent mantle-temperature literature supplies only the sensitivity prior. The selection is 1407 °C, distinct from the HWR-2 fit optimum of 1326 °C. |
| `T0` | 280 K | 250–300 | ARCANA surface reference selection; bind to `TSurf` only where the same reference surface is meant. |
| `zp` | 100 km | 80–140 km | ARCANA thermal-plate thickness; bind to the explicit OrbData ocean thickness path. The literature model spread is retained as sensitivity, not transferred as a fitted value. |
| `kappa` | 8.3333×10⁻⁷ m² s⁻¹ | 7.0588×10⁻⁷–1.1648×10⁻⁶ | Derived as `k/(rho_m Cp)`, not an independent constant. |

For the associated thermal-subsidence relation, this configuration also selects mantle expansivity `alpha=3.0×10⁻⁵ K⁻¹` (sensitivity 2.5–3.5×10⁻⁵) and water-column reference density `rho_w=1000 kg m⁻³` (990–1030). These are not extra parameters in the surface-flux Eq. 4. The deterministic Fourier truncation is `N=256`, with target relative flux tolerance `1e-12`; convergence must be recorded in replay metadata. The derived diffusivity sensitivity interval is 7.0588×10⁻⁷–1.1648×10⁻⁶ m² s⁻¹.

The material prior points are consistent with generic mantle model values such as [Schuberth et al. (2009)](https://doi.org/10.1029/2008GC002235) and material-model tables in [Solid Earth (2023)](https://se.copernicus.org/articles/14/1155/2023/). Their Earth/silicate context is kept explicit; it does not prove Arcana's composition.

## Shared thermal authority

One authority now supplies HWR-2 `k`, `rho_m`, `Cp`, `alpha`, `T0`, `Tb`, and `zp`; bindings are explicit in the JSON artifact. `Cp` and `kappa` are not duplicated in OrbData. `Tb` is a basal boundary condition, not automatically the same thing as `TADIAB`; `T0` is not a melting limit; `zp` is not automatically `ZBASTH`. The selected `k` maps to ocean mantle `conduc(2)` under the constant effective-property assumption, while ocean crust `conduc(1)` remains separate because the HWR-2 model has no explicit insulating crust layer.

## Positive-age and global heat-flow envelope

At the selected point values, HWR-2 decreases monotonically with positive age:

- Ocean nominal flux: **0.0476525 W m⁻² at 160 Ma** to **0.4741483 W m⁻² at 1.1491667 Ma**.
- Propagating the full parameter sensitivity intervals gives **0.0322191–0.5815391 W m⁻²** over the age range. These are sensitivity bounds, not additional selected points.
- Ridge: **0.3 W m⁻²** on 108 cells; age zero is never evaluated through HWR-2.
- Ratified continental references: **0.045–0.085 W m⁻²** (normal-domain value 0.060).
- Complete nominal global envelope: **0.045–0.4741483 W m⁻²**.
- Global envelope including parameter sensitivity: **0.0322191–0.5815391 W m⁻²**.

## `qLim1` and GDH1

The current `qLim1=0.3 W m⁻²` would clip the nominal youngest positive-age HWR-2 flux by at least 0.1741483 W m⁻². **Classification: `SOURCE_BYPASS_REQUIRED`.** The explicit ARCANA path must preserve governed `heatFl`; out-of-envelope inputs should be reported and fail closed, not silently mutated. No arbitrary larger cap is selected.

Independently, in `src/OrbData5.f90::Assign`, gate the age-based GDH1 heat-flow replacement and age-zero `qLim1` substitution to legacy/non-ARCANA mode. For a complete valid ARCANA ocean input, retain the supplied nonzero `heatFl`. Keep legacy GDH1 and continental behavior unchanged. The later geotherm correction/limit path must also preserve the explicit value or fail closed. Replace the ARCANA ocean branch's independent GDH1/95 km thickness with the same governed `zp` binding. No source change is made here.

## Candidate readiness and preserved gates

The ocean age-support and HWR numerical-authority blockers from A0.6C are closed for a heat-flow reference configuration. The full `R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_CANDIDATE_V1.json` is **not created**: `temLim`, `TADIAB`, `GRADIE`, and `ZBASTH` remain independent OrbData specialist controls, and the single-layer HWR-2 versus layered OrbData profile needs consistency qualification. The heat-flow parameters and support are ready for that config authoring step; this does not imply runtime readiness.

All gates remain false: `PRE_ORBDATA_ready`, OrbData/SHELLS execution, ShellSet modification/qualification, canonical T0 promotion, dt/T1, forward evolution, staging changes, commit, and push. No model run or test was performed.

# R6 PRE_ORBDATA Heat-Flow Ridge and Runtime Closure

## Decision

**`R6_PRE_ORBDATA_HEAT_FLOW_RIDGE_POLICY_ADJUDICATED__NUMERICAL_BINDING_READY`**

The finite domain and ridge-boundary convention are now explicit for the ratified-for-materialization B-v2 candidate. “Numerical binding ready” means the producer contract and formulas are defined for the next authorial parameter binding. It does not mean HWR-2 parameters or `qLim1` have numeric ARCANA selections, the runtime is qualified, or `PRE_ORBDATA_ready` is true.

The q-ridge recommendation is to ratify **0.3 W m⁻²** as `ARCANA_AUTHORED_SPECIALIST_BOUNDARY_PARAMETER_WITH_LITERATURE_PRIOR`, applied only to the selected age-source/ridge-boundary support. The value is not a WORLD_HISTORY field or Earth ground truth. Bird (2008) explicitly set a uniform 0.3 W m⁻² conductive boundary at OSR boundaries, describing it as the highest conductive heat flow typically observed. This supports a model boundary convention; it does not supply ARCANA observations or transfer Earth’s conductivity. [Bird (2008)](https://doi.org/10.1029/2007JB005460)

## T0 ocean age support audit

I inspected `oceanic_lithosphere_age_ma` in [R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz](/D:/corsi/Arcana/ARCANA_WORLD/R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz), cross-checked against the realization manifest, canonical branch registry, boundary kinematics census and the age materializer.

| Measure | Result |
|---|---:|
| Ocean cells (`physical_crust_domain_id == 1`) | 50,542 |
| Exact zero age | 108 |
| Positive age | 50,434 |
| Minimum positive age | 1.1491667412 Ma |
| Maximum age | 160 Ma |
| Area-weighted median (manifest) | 70 Ma |
| Unweighted cell median | 70.6665038007 Ma |
| Ocean NaN, infinite, or negative age | 0 |

Low-age cell counts are: 108 at zero; 0 in `(0,1)` Ma; 113 in `[1,2)` Ma; 291 in `[2,5)` Ma; 598 in `[5,10)` Ma; and 1,783 in `[10,20)` Ma. Unweighted cell quantiles are p01=4.9476 Ma, p05=18.2972 Ma and p10=28.3545 Ma. The complete zero-cell coordinate list is in the JSON artifact as row/column indices and cell-center latitude/longitude; every one has physical crust domain ID 1. They form two segments in the Indian Ocean region, spanning 17.5°N to 2.5°N and 16.5°S to 53.5°S, around 37.5°E to 69.5°E.

The manifest status is `RATIFIED_FOR_T0_MATERIALIZATION`, while canonical status remains `CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION`. These counts describe the current ratified candidate payload; it has not been promoted to canonical T0.

## Ridge-axis identification

The materializer selected branch `R6BR-DERIVED-50911691f2df2e592ca4` as the age source. Its 79 selected boundary segments all have positive relative normal velocity and both adjacent cells are oceanic. Their adjacent-cell support reconstructs exactly the 108 zero-age cells. Thus the zero-age cells do not identify a ridge by themselves: the selected spreading-source branch and kinematic support independently agree with them.

There are another 634 positive-normal, ocean-ocean candidate segments. The T0 manifest says boundary process classes are not assigned, and the kinematic census classifies every boundary process as `UNKNOWN_NOT_AUTHORIZED_BY_KINEMATICS_ALONE`. Their unique adjacent support is 1,075 cells: 3 overlap the selected zero-age ridge support, and 1,072 have positive age. Treat those 1,072 cells as `INVALID_OR_UNKNOWN` for heat-flow production until their process is authoritatively assigned as spreading, rift or another state. Do not turn every divergent kinematic candidate into a ridge.

## Three producer domains

| Domain | Current support and rule |
|---|---|
| `RIDGE_AXIS` | The 108 cells seeded by the selected 79-segment age-source branch. Assign the finite specialist boundary flux below; do not evaluate HWR-2 at age zero. |
| `POSITIVE_AGE_OCEAN` | 49,362 positive-age ocean cells not incident on an unclassified positive-normal ocean-ocean candidate boundary. Apply HWR-2 only for `t > 0`. |
| `INVALID_OR_UNKNOWN` | 1,072 positive-age cells incident on unclassified candidate divergence, plus any other UNKNOWN, mixed or unsupported domain. Preserve UNKNOWN and fail closed; never encode it as heat-flow zero. |

The full age field has 50,434 positive cells; the smaller positive-age producer domain excludes the 1,072 ambiguous boundary-adjacent cells. Non-ocean cells have NaN age and stay outside this ocean producer.

## Ridge boundary policy

Use `q_ridge = 0.3 W m⁻²` as an ARCANA-authored specialist boundary condition on the selected source support. Bird’s precedent addresses ridge-boundary assignment in a finite-element model where age-grid resolution and missing back-arc ages otherwise failed to provide reliable ridge-node heat flow. The precedent supports a finite model boundary value, but does not make 0.3 a universal physical law. [Bird (2008)](https://doi.org/10.1029/2007JB005460)

The selection is restricted to the selected branch and is recorded as a literature prior. The rest of the divergent boundary candidates stay UNKNOWN until a boundary-process authority classifies them. The full 108 selected support coordinates and parent-domain IDs are listed in the JSON report.

## Positive-age model domain and HWR-2 envelope

HWR-2 is evaluated over the finite positive-age interval `[1.1491667412337465, 160] Ma`; exact zero is assigned to the ridge boundary path. For positive `k`, `rho_m`, `C_p`, `z_p` and `T_b > T_0`,

```text
H(t; θ) = k (T_b - T_0) / z_p
          × [1 + 2 Σ(i=1..∞) exp(-κ i² π² t / z_p²)]
κ = k / (rho_m C_p)
```

and H decreases monotonically with age. Therefore the maximum on the valid positive support occurs at **1.1491667412 Ma**, at two cells centered at **(-53.5°, 36.5°)** and **(-53.5°, 39.5°)**. The minimum occurs at 160 Ma, at **(21.5°, -132.5°)**. Both are finite for any fixed finite admissible parameter tuple. Holdt et al. give the analytical law and show the `t → 0+` divergence; no zero-age value is calculated here. [Holdt et al. (2025)](https://doi.org/10.1029/2024JB029890)

No ARCANA HWR-2 values or bounded intervals for `k`, `rho_m`, `C_p`, `T_b-T_0` or `z_p` are selected. The valid age interval is finite, so the flux envelope is symbolically finite, but its numeric minimum and maximum cannot be calculated until ARCANA chooses the material/thermal tuple or a finite bounded ensemble. No Earth best-fit values are substituted.

## qLim1 governance

The authored continental range is 0.045–0.085 W m⁻², and the ridge boundary is 0.3 W m⁻². Once the HWR-2 parameters and projection error are bounded, the finite nonbinding requirement is

```text
qLim1 >= max(0.3, 0.085, sup_θ H(1.1491667412 Ma; θ)) + δ_guard
```

where `δ_guard` is a declared finite positive margin for serialization/projection and rounding error. This proves a finite nonbinding limit can be selected over the bounded model domain; it does not guess the number before its inputs are selected.

The current compiled `qLim1=0.3 W m⁻²` equals the ridge boundary value and has no safety margin. It leaves the continental references below the cap, but there is no selected positive-age HWR envelope proving all ocean values are at or below 0.3. OrbData applies `MIN(heatFl,qLim1)`, so any larger producer value is silently reduced. **Classification: `SOURCE_CHANGE_REQUIRED`.** Configure the finite bound from the governed producer envelope and make violations fail closed rather than silently changing an ARCANA field.

## qLim0 and dQL/dE governance

The current compiled values are `qLim0=0` and `dQL_dE=0`, so the lower line is `qLimit(E)=0` at every elevation. At the initial input clamp this is a `NON_BINDING_RUNTIME_GUARD`: continental references, ridge q and positive-age HWR flux are strictly positive. A positive Earth-calibrated elevation slope is not authorized.

The full `Assign` pass-through remains `UNRESOLVED`: if the Moho temperature exceeds `TAsthK`, OrbData first changes `heatFl` for geotherm consistency and then applies the limits again. The thermal parameter set is not selected, so that correction and its interaction with the floor cannot be ruled out. Preserve the governed flux or fail closed if the correction would alter it.

## Internal GDH1 compatibility and required ShellSet change

The local explicit-input patch still enters the age-based ocean branch for ARCANA ocean nodes. That branch replaces positive-age `heatFl` with GDH1 (`0.510/sqrt(ageMa)` through 55 Ma, then `0.048 + 0.096 exp(-0.0278 ageMa)`) and replaces age-zero `heatFl` with `qLim1`. The later clamp may change it again. Therefore an explicit ARCANA producer field is **not** currently authoritative at the OrbData handoff. This is an implementation blocker.

The smallest heat-flow change is to make the GDH1 heat-flow assignment stock-mode-only and preserve ARCANA’s explicit nonzero FEG `heatFl` through `Assign`. Keep stock behavior intact when the ARCANA input pair is absent. Separately, the current ARCANA ocean branch retains a GDH1/95-km thickness calculation; if the producer owns ocean thickness, bind that producer output or one shared thickness authority instead.

Because exact zero means “heat flow missing” to OrbData, every physical FEG node must carry a governed nonzero flux. Keep missingness/UNKNOWN in a separate mask; reject incomplete support before runtime so it cannot trigger qArray fallback.

## Producer contract and remaining choices

- `CONTINENT`: use the already-ratified 0.045/0.060/0.085 W m⁻² authored reference values on their governed land support.
- `RIDGE_AXIS`: use the 0.3 W m⁻² specialist boundary on the selected 108-cell age-source support.
- `POSITIVE_AGE_OCEAN`: use HWR-2 conductive flux on the 49,362 currently valid positive-age ocean cells.
- `INVALID_OR_UNKNOWN`: fail closed on the 1,072 ambiguous candidate-boundary cells and all other unsupported/mixed/unknown support.
- Joined global field: `DERIVED_REPLAYABLE_T0_STATE`.
- FEG serialization: `NUMERICAL_RUNTIME_INPUT_ONLY`.

Remaining numeric choices are ARCANA conductivity, density, heat capacity, expansivity, surface/basal temperature, plate thickness, numerical convergence tolerance, projection-error margin and then the resulting qLim1. No further broad literature research is required for the ridge value. Remaining implementation blockers are the GDH1 bypass, a nonbinding configured qLim1 with fail-closed validation, qualification of the source patch and complete nonzero FEG support.

## Preserved gates

- `PRE_ORBDATA_ready=false`.
- OrbData/SHELLS not run; ShellSet not modified or qualified.
- No `dt`, T1 or forward evolution created.
- Canonical T0 not promoted; staging area unchanged.
- No commit or push.

## Sources

- [Bird (2008), *Stresses that drive the plates from below*](https://doi.org/10.1029/2007JB005460): explicit OSR 0.3 W m⁻² conductive boundary precedent.
- [Holdt, White & Richards (2025), *Revised Oceanic Plate Cooling Models*](https://doi.org/10.1029/2024JB029890): HWR-2 equations and the positive-age limit.
- Local age-source logic: [b_pangaea_v2.py](/D:/corsi/Arcana/ARCANA_WORLD/src/arcana_worldsim/r6/t0_materialization/b_pangaea_v2.py).
- Local runtime patch under review: [R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch](/D:/corsi/Arcana/ARCANA_WORLD/patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch).
- Current source qualification and preservation gates: [R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json](/D:/corsi/Arcana/ARCANA_WORLD/R6_T0_ORBDATA_ARCANA_ADAPTER_AND_SOURCE_GENERALIZATION.json).

# R6 PRE_ORBDATA A0.6 — Heat-flow parameterization and runtime realization

**Decision:** `R6_PRE_ORBDATA_HEAT_FLOW_PARAMETERIZATION_PARTIAL__TARGETED_RESEARCH_REMAINS`

The closed architecture remains **HYBRID_DOMAIN_AWARE_HEAT_FLOW**. The ARCANA-side ocean producer path is selected by that authority. The exact ocean model/configuration and the downstream OrbData configuration are not selected, so this stage does not authorize field materialization or runtime execution. No config candidate was created because it would require unsupported parameter values and an unresolved young-ocean policy.

## Architecture and runtime realization

The governed continental reference remains the continental branch. Ocean heat flow must be produced from `oceanic_lithosphere_age_ma` and `physical_crust_domain_id` in ARCANA, then categorically joined into `DERIVED_REPLAYABLE_T0_STATE`. A FEG array is only `NUMERICAL_RUNTIME_INPUT_ONLY`; it is not a new canonical physical field.

The replay identity must include parent hashes, model/configuration and producer versions, young-ocean applicability, projection policy, lineage and output hashes. Unknown or unsupported values stay UNKNOWN and stop qualification; they must never be written as exact zero because ShellSet uses exact zero as its missing-heat-flow sentinel.

With explicit nonzero `heatFl`, qualified `Assign` skips the `needQ` branch. That bypasses its qArray sampling and age-law fill, including the `ageMa <= 0 -> qLim1` assignment. This does **not** make the whole interface a pass-through: OrbData5 applies a lower floor to nonzero values and an upper cap, `Assign` applies them again, and conditional geotherm-consistency corrections can modify heat flow before reclamping. Effects have not been measured by a new runtime execution.

## Ocean cooling model

The production model/version remains unselected. The leading literature candidate reviewed is HWR-2 from Holdt et al. (2025), a constant-property analytical finite plate model:

`H(t) = k (T - T0) / zp [1 + 2 Σ(i=1..N) exp(-κ i² π² t / zp²)]`, where `κ = k/(ρm Cp)`.

It represents conductive surface heat flow in W m⁻². The paper's HWR-2 reference fit lists `k=3.800 W m⁻¹ K⁻¹`, `α=3.20×10⁻⁵ K⁻¹`, `Cp=1171.52 J kg⁻¹ K⁻¹`, `T=1326 °C`, and plate thickness `zp=105 km`; its coupled depth fit uses ridge depth `zr=2.50 km`. These are **published Earth model parameters, candidate-only**, not ARCANA selections. The equation uses time in seconds, so an age input in Ma requires an explicit conversion.

Finite plate thickness produces mature/old-age flattening, unlike half-space cooling's indefinite cooling trend. HWR-2 assumes one-dimensional conduction and constant properties and does not represent total heat loss including hydrothermal advection. The study also presents variable-property HWR-3 as similarly supported; the evidence does not establish an ARCANA transfer rationale or settle this structural choice. The series is singular as age approaches zero; truncating its sum is numerical convergence handling, not a physical ridge model. [Holdt et al. (2025)](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2024JB029890)

Thus the selected architecture's finite-plate model family is retained, but the exact production model, ARCANA parameters/covariance, and valid ARCANA age interval remain targeted research. GDH1 is not selected merely because it appears in qualified ShellSet source or in the separate bathymetry lineage.

## Young ocean, ridge and age zero

Age zero, unsupported positive-young values and ridge/rift support receive `MODEL_DOMAIN_UNKNOWN` and fail closed until an applicable physical branch is governed. No finite value or numerical age cutoff is selected. A future valid positive-age model output would be `PHYSICAL_MODEL_OUTPUT`; no `PHYSICAL_REGULARIZATION` is selected. ShellSet's `qLim1` is a numerical ceiling and must not be substituted for ridge physics. No uniform hydrothermal correction is authorized; conductive flux and total advective-plus-conductive heat loss must remain distinct.

## qLim governance

The qualified source has compiled parameters `qLim0=0 W m⁻²`, `dQL_dE=0 (W m⁻²)/m`, and `qLim1=0.300 W m⁻²`. They are not runtime input-file bindings.

| Control | Qualified operation | Selected ARCANA path |
|---|---|---|
| `qLim0` | Lower floor intercept in `qLimit=qLim0+dQL_dE×elevation`; `MAX(heatFl,qLimit)` | Active guard. With the present zero intercept/slope it leaves positive input unchanged before correction, but this does not prove all later values are unaffected. |
| `dQL_dE` | Elevation slope of the lower floor | Active as part of the floor; current compiled zero slope is not an ARCANA elevation law. |
| `qLim1` | Upper cap applied before `Assign`, inside it, and after certain corrections; also the internal age-zero fill when `needQ` is true | Active as a global ceiling for explicit nonzero input. Only its internal age-zero fill is bypassed. |

No control is approved as a harmless pass-through. Before runtime qualification, either demonstrate with full-field before/after evidence that the controls and corrections do not alter valid governed flux, or seek separate source/configuration governance and FAIR requalification. Do not silently accept clipping.

## Heat-flow producer versus OrbData configuration

Ocean-model parameters belong to the ARCANA heat-flow producer. OrbData's `conduc` or `alphaT` must not silently inherit corresponding producer values; if they represent the same physical quantity, a single authority and explicit binding are required.

The qualified source extraction establishes these downstream inputs and units. `alphaT` (K⁻¹), `conduc` (W m⁻¹ K⁻¹), `radio` (W m⁻³), `rhoBar`, `rhoAst`, and `rhoH2O` (kg m⁻³), `TSurf` (K), `temLim` (K), and `TAsthK` (K) are consumed in the Assign/thermal-density path. Source `TADIAB` (K) and `GRADIE` (K m⁻¹) feed the `TAsthK` construction. `ZBASTH` (m) belongs to downstream ShellSet configuration, not the selected OrbData heat-flow path; defer it until mechanics are authorized. The Earth sample values in `INPUT/iEarth5-049.in` are not ARCANA authority. None of these ARCANA values, global/material scopes, or ranges is selected here. Material-family, radiogenic, density and geotherm constraints need targeted research and bounded sensitivity.

## FEG projection

The existing `project_cell_field_to_nodes` adapter provides deterministic source-cell lineage, unanimous categorical projection, UNKNOWN preservation, and no smoothing or resolution claim. Its generic continuous mode selects the lexicographically first incident cell. By itself it does not require heat-flow selection to agree with all incident `physical_crust_domain_id` values and, for continental cells, thermal-class support. A heat-flow-specific gate is required: accept only known homogeneous domain/class support, then project without cross-branch averaging and preserve incident-cell lineage. Mixed or unknown support stays UNKNOWN. This is numerical support only, not increased physical resolution. The 64,442-node projection also remains blocked until its canonical partition/mesh payload is available.

## Uncertainty and sensitivity

Keep the following separate: (1) continental authored-field provenance/uncertainty (no numerical interval exists); (2) ocean structural-model alternatives; (3) correlated ocean parameters; (4) young/rift applicability; (5) FEG support and projection error; and (6) OrbData material/geotherm uncertainty. Preserve authored-class metadata without inventing an interval. Use bounded/local sensitivity by parameter block and model-form ensembles where alternatives change a decision or output; add joint dimensions only for consequential interactions. No global Cartesian ensemble is required by current evidence.

Before runtime qualification, record model-form and parameter sensitivity, young-age/applicability behavior, each qLim and geotherm correction's before/after effect, boundary projection coverage/lineage, material configuration sensitivity, and any shared-quantity binding. These runs are not authorized in this stage.

## Unresolved and required next work

- Establish transfer of HWR-2, HWR-3, GDH1, or another named finite-plate model to the synthetic B-v2 age/domain field; choose exact model/version, flux meaning, parameter set and covariance.
- Govern valid positive-young ages and a physical ridge/accretion/hydrothermal policy, or keep affected support UNKNOWN.
- Adjudicate qLim floors/cap and geotherm corrections as explicit runtime configuration or prove they cannot alter the governed input; otherwise a separately reviewed ShellSet change and requalification are needed.
- Research and govern OrbData material-specific/global thermal and density parameters, radiogenic terms, uncertainty and sensitivity.
- Implement the field-aware FEG projection gate and wait for canonical partition/mesh payload before projecting 64,442 nodes.

No OrbData/SHELLS execution occurred; ShellSet and canonical values were not changed.

**Gates preserved:** `PRE_ORBDATA_ready=false`; `t0_orbdata_executed=false`; `shellset_mechanics_authorized=false`; `dt_selected=false`; `t1_created=false`; `forward_evolution_authorized=false`.

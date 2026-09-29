# R6 T0 heat-flow numerical binding

**Decision:** `R6_PRE_ORBDATA_HEAT_FLOW_NUMERICAL_BINDING_BLOCKED__UNSELECTED_HWR2_PARAMETERS_AND_UNKNOWN_BOUNDARY_SUPPORT`

The `HYBRID_DOMAIN_AWARE_HEAT_FLOW` architecture remains closed. This pass does not run OrbData/SHELLS, modify ShellSet, promote canonical T0, or alter staging. The numeric binding is blocked: there is no governed ARCANA HWR-2 parameter tuple or finite range from which to calculate an ocean flux envelope or justify a finite nonbinding `qLim1`. Also, 1,072 positive-age cells cannot yet be established as HWR cooling-domain cells because the realization's boundary-process classes are unassigned.

## Support completeness

The 1,072 cells are finite positive-age cells with `physical_crust_domain_id=1`; none is missing age or ocean-domain membership. Their unknown status arises from their adjacency to 634 unselected divergent ocean-ocean candidates. The T0 manifest confirms that boundary process classes were not assigned and that the age generator selected one spreading-source branch. It does not establish whether the other candidate segments are active spreading/rift boundaries. Thus proximity alone does not invalidate a governed age, but these candidates could invalidate the age producer's single-source cooling interpretation. The conservative current adjudication is:

| Outcome | Cells |
|---|---:|
| `AUTHORIZED_POSITIVE_AGE_OCEAN` | 0 |
| `RIDGE_OR_RIFT_SPECIAL_DOMAIN` | 0 |
| `UNKNOWN_INSUFFICIENT_AUTHORITY` | 1,072 |

The remaining 49,362 positive-age cells have previously audited support after excluding those unknowns, over 1.1491667412–160 Ma. This does not close complete ocean support. Unknowns must remain in a separate mask; zero carries OrbData missing/grid-fallback semantics. `PRE_ORBDATA_ready` therefore remains false.

## HWR-2 parameter binding

For `t>0`, the selected structure is:

`H(t)=k*(Tb-T0)/zp * [1 + 2*sum(i=1..infinity, exp(-kappa*i^2*pi^2*t/zp^2))]`, with `kappa=k/(rho_m*Cp)`.

No t=0 value is evaluated. The audited ARCANA configuration does not select `k`, `rho_m`, `Cp`, `Tb`, `T0`, or `zp`, and it has no governed finite intervals for them. The shared `alphaT_crust_mantle` family is also unselected; it affects thermal subsidence rather than the HWR surface-flux formula. HWR-2 series convergence settings are not selected either. The parameter-level audit, units, authority classes, uncertainty, and sensitivity requirements are in the JSON artifact.

Holdt et al.'s Earth HWR-2 fit (`k=3.8 W m⁻¹ K⁻¹`, `Tb=1326 °C`, `zp=105 km`) is explicitly excluded as an ARCANA default. Bird's `0.3 W m⁻²` OSR convention remains the already accepted ARCANA-authored ridge boundary with literature prior; it supplies no missing HWR-2 material constants.

## Heat-flow envelope

The authorized continental reference values span **0.045–0.085 W m⁻²** (normal domain is 0.060). The ridge boundary is **0.3 W m⁻²** on 108 selected-source support cells. The positive-age ocean minimum and maximum cannot be calculated without the HWR-2 parameters. For a fixed positive temperature contrast, the HWR-2 flux decreases with age, so its maximum would occur at 1.1491667412 Ma and its minimum at 160 Ma over the currently admissible positive-age interval. Their numerical values remain unknown. Consequently a complete global authorized minimum/maximum is not reportable.

## `qLim1` governance

The source currently has `qLim1=0.300 W m⁻²`; `Assign` can cap heat flow with `MIN(heatFl,qLim1)`. This equals the ridge value and has no margin. Since the HWR-2 maximum is unavailable, a finite nonbinding guard cannot be justified. **Classification: `SOURCE_BYPASS_REQUIRED`.** Once a governed envelope exists, ARCANA heat flow must pass unchanged; any envelope violation should fail closed rather than be silently clipped. No arbitrary large cap is selected.

## `qLim0` and `dQL_dE`

The audited values are `qLim0=0 W m⁻²` and `dQL_dE=0 W m⁻² m⁻¹`. The surface-closed candidate T0 package has total elevation from **−6819.275552157349 m to +3309.49365234375 m**. Across that entire range, `qLimit(E)=qLim0+dQL_dE*E=0 W m⁻²`. All currently authorized continental and ridge fluxes are strictly positive; HWR-2 flux is positive for `t>0` and `Tb>T0`. Thus the initial lower clamp is a `NON_BINDING_RUNTIME_GUARD` over the actual T0 elevation range. This does not qualify the later `Assign` pass: conditional geotherm correction must preserve the explicit ARCANA flux or fail closed.

## GDH1 override and source change

The local patch currently makes the ARCANA ocean branch enter the age-based branch in `src/OrbData5.f90::Assign`. It substitutes `qLim1` at age zero and GDH1 at positive ages. The smallest change is to make this replacement stock-mode-only: when `arcanaMode && arcanaOcean`, retain supplied, validated, nonzero explicit `heatFl`; when ARCANA mode is absent, preserve the legacy GDH1 behavior. Keep the continental path unchanged. Validate the complete ARCANA input pair before calling `Assign`, and reject partial/invalid inputs. Keep unknownness in an explicit mask rather than encoding it as zero.

The later limit/geotherm-correction path in `Assign` must also preserve the explicit ARCANA value or fail closed if consistency correction would alter it. The oceanic thickness branch presently uses GDH1 and hardcoded 95 km; it must instead consume the producer's thickness or one shared governed thickness authority. The exact source sites and context are recorded in the JSON report. No source edit is made in this pass.

## Shared and OrbData-only parameter authority

Conductivity, density/heat capacity, expansivity, surface and basal temperatures, and plate thickness require a single ARCANA authority wherever producer and OrbData semantics overlap. `kappa` is derived from the shared `k`, `rho_m`, and `Cp`; it is not a second independent constant. These authorities are currently unbound. `temLim`, `TADIAB`, `GRADIE`, and `ZBASTH` are OrbData specialist controls and remain unselected. Existing canonical gravity (9.82 m s⁻²) and radius (6,371,000 m) remain recorded as already selected, subject to the stated source/format binding.

## Configuration candidate and gates

`R6_PRE_ORBDATA_HEAT_FLOW_CONFIG_CANDIDATE_V1.json` was **not created** because it would require guessed HWR-2 values, a speculative global envelope, and unresolved boundary support. The exact remaining scientific and implementation blockers are enumerated in the JSON artifact.

All runtime and promotion gates remain false: `PRE_ORBDATA_ready`, OrbData/SHELLS execution, ShellSet modification/qualification, canonical T0 promotion, dt/T1, forward evolution, staging changes, commit, and push. No tests or model runs were performed.

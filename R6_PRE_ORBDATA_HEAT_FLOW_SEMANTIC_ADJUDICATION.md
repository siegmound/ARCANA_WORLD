# R6 PRE_ORBDATA heat-flow semantic adjudication

**Decision:** `R6_PRE_ORBDATA_HEAT_FLOW_SEMANTICS_PARTIALLY_ADJUDICATED__SOURCE_AMBIGUITY_REMAINS`

This report adjudicates code behavior from the FAIR extraction of Git-tracked source at qualified ShellSet branch `arcana-r6-runtime-capacity`, commit `62fd474f229b2676fd9d39c5def45137d22d2481`. The qualified executable reference is `4c0044fe4332184d63408960a2237d4edb7da891b71f74b82bd1d5a83b27e918`; governed patch SHA256 is `e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2`. Source citations below refer to the contextual excerpts in [the FAIR source extraction](R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.md) and its JSON companion.

The current ARCANA authority is `R6_T0_ORBDATA_ARCANA_SOURCE_GENERALIZATION_FAIR_QUALIFIED__PRE_ORBDATA_SCIENTIFIC_BLOCKERS_REMAIN`. Source-generalization FAIR qualification is closed. Remaining scientific blockers are governed heat-flow routing/qLim configuration and material/thermal OrbData configuration adjudication. The implementation blocker is materialization of the 64,442-node projection after the canonical partition payload is available. There is no superseding closure of these scientific blockers in the reconciled authority artifacts.

## Adjudicated execution order

1. `GetNet` reads nodal `qi` into `dQdTdA` and rejects negative heat flow; OrbData copies each node's value to `heatFl` before `Assign` (`src/MOD_Data.f90:1997-2003`; `src/OrbData5.f90:481-486`).
2. OrbData scans the full nodal array. If any value is exactly zero, it reads the heat-flow grid `qArray` once for the run. If all values are nonzero, it skips that grid (`src/OrbData5.f90:367-383`). This is a global loading condition, not a claim that every node uses the grid.
3. Before the per-node loop, nonzero inputs are raised to `qLim0 + dQL_dE * elevation` if below the lower limit, then capped at `qLim1`. Exact zeros skip that pre-loop floor operation (`src/OrbData5.f90:390-394`).
4. In `Assign`, exact `heatFl == 0.0D0` sets `needQ`. Only that node enters the branch that bilinearly interpolates `qArray` (`src/MOD_Data.f90:381-416`). Thus zero is the sentinel for derivation in this code path.
5. Still inside that missing-value branch, an ocean predicate can replace the interpolated grid value. In ARCANA mode it is `arcanaOcean`; outside ARCANA mode it uses `ageMa < 200`. For age `<= 0`, the assigned value is `qLim1`; otherwise the source applies its cited GDH1 piecewise age law (`src/MOD_Data.f90:418-437`).
6. After the missing-value branch, the lower and upper q limits are applied for either initial-zero or initial-nonzero heat flow (`src/MOD_Data.f90:437-445`).
7. If the steady geotherm test exceeds `TAsthK`, `Assign` changes heat flow by `deltaQ` and reapplies both limits (`src/MOD_Data.f90:625-638`). Nonzero nodal heat flow therefore bypasses `qArray` and the age law, but is not guaranteed to survive unchanged.
8. OrbData writes final `heatFl` back to `dQdTdA` and emits the output field (`src/OrbData5.f90:545-568`).

## Routing and scope findings

- **`qArray`:** loaded globally when at least one input node is zero; interpolated only for nodes whose local heat flow is zero (`src/OrbData5.f90:367-383`; `src/MOD_Data.f90:381-416`).
- **Age override:** it overwrites a `qArray`-derived value only inside the zero-sentinel branch. It does not override a nonzero explicit nodal value inside `Assign` (`src/MOD_Data.f90:381-437`).
- **ARCANA ocean/continent:** the governed patch derives `arcanaOcean` from the explicit ARCANA domain input and passes ARCANA mode/domain flags into `Assign` (see the `OrbData5.f90` input-pair, domain lookup, and `CALL Assign` hunks in `patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch`). In ARCANA mode, the age route uses `arcanaOcean`; a continental node with zero heat flow therefore does not take the age override and reaches the q-grid fallback plus limits. The patch does not define a new heat-flow law or provide heat flow/age values.
- **Age zero:** the implementation behavior is established, but physical/authorial meaning is not. The source sends `ageMa <= 0` to `qLim1`; it does not distinguish a valid zero-age ocean node from a sentinel (`src/MOD_Data.f90:420-437`).
- **Limits:** `qLim0` is documented as the zero-elevation floor, `dQL_dE` as its elevation slope, and `qLim1` as the cap. They are compiled parameters with documented units, but have direct effects on calculated nodal heat flow; `qLim1` also supplies the age-zero branch (`src/OrbData5.f90:153-168,273-279`; `src/MOD_Data.f90:443-445`). Treat them as mixed model controls, not as innocuous checks.
- **`delta_rho_limit`:** this is a separate symmetric limit on `chemical_delta_rho`, not a heat-flow-routing control (`src/OrbData5.f90:184-189`; `src/MOD_Data.f90:719-720`).

## Symbol classifications

The machine-readable companion contains the complete symbol-by-symbol record, evidence paths, units where documented, bindings, ARCANA coverage, and classifications. Principal findings:

| Symbol(s) | Classification | Source-supported role |
|---|---|---|
| `heatFl`, `dQdTdA` | `MIXED_OR_CONTEXT_DEPENDENT` | Input nodal heat flow that OrbData may derive or modify and write back. |
| `needQ`, `TAsthK` | `DERIVED_ORBDATA_STATE` | `needQ` is the exact-zero routing flag; `TAsthK` is calculated from the configured adiabat. |
| `qArray`, `ageMa` | `MIXED_OR_CONTEXT_DEPENDENT` | Conditional fallback data and conditional age-based route; ARCANA source authority for these inputs remains open. |
| `qLim0`, `dQL_dE`, `qLim1` | `MIXED_OR_CONTEXT_DEPENDENT` | Compiled limits with consequential heat-flow behavior; `qLim1` also supplies the age<=0 result. |
| `alphaT`, `conduc`, `TSurf`, `temLim`, `TADIAB`, `GRADIE`, `ZBASTH` | `SPECIALIST_MODEL_CONFIGURATION` | Thermal/material profile parameters; no ARCANA material-specific set is authorized. |
| `delta_rho_limit` | `NUMERICAL_GUARD_OR_LIMIT` | Density-anomaly cap, separate from heat-flow selection. |

The classifications do not promote legacy parameter-file examples into ARCANA values. Source-documented units and declaration/binding evidence are recorded per symbol in JSON.

## Research versus retained controls

**Physical source/literature or authorial research is needed** for the T0 heat-flow source/field; an ocean age/cooling law if selected (including age provenance and age-zero meaning); and material/profile-specific thermal properties such as `alphaT`, conductivity, heat production, and thermal-profile parameters. The current contracts say those R6 inputs are absent and values remain unset (`R6_SHELLSET_MINIMUM_THERMOMECHANICAL_STATE_CONTRACT.md:28,38-41,62-68`; `R6_SHELLSET_PRERUNTIME_INPUT_CLOSURE.md:65-77`).

**ShellSet control governance is needed** for `qLim0`, `dQL_dE`, and `qLim1`: explicitly decide whether to inherit the qualified implementation defaults, bound them, or replace them. No values are selected here. Changing their physical effect/range may need justification, but literature research is not automatically required simply to retain an existing code control. `delta_rho_limit` belongs to the separate density/material adjudication.

The extracted parameter input documents definitions and units for the legacy specialist parameters (`INPUT/iEarth5-049.in:11-12,23-27`); `ShellSetMain.f90` reads the parameter file and routes values through `ReadPm`/`Variable_Update` (`src/ShellSetMain.f90:577-612`). That proves the configuration path, not an ARCANA-authorized choice.

## Unresolved decisions and gates

The source does not decide which heat-flow input ARCANA should author, whether the GDH1 route is suitable for ARCANA, the intended meaning of age zero, whether continental q-grid fallback is authorized, or whether q limits are retained/bounded/replaced. Material-specific thermal configuration is also open. Accordingly this is a **partial adjudication**, not source closure or PRE_ORBDATA readiness.

| Gate | Preserved value |
|---|---:|
| `PRE_ORBDATA_ready` | `false` |
| `t0_orbdata_executed` | `false` |
| `shellset_mechanics_authorized` | `false` |
| `dt_selected` | `false` |
| `t1_created` | `false` |
| `forward_evolution_authorized` | `false` |

No OrbData/SHELLS execution, ShellSet modification, scientific value selection, or authorization change was made.

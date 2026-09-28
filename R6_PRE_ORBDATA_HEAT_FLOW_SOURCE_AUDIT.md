# R6 PRE_ORBDATA heat-flow source audit

**Decision:** `R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_AUDIT_PENDING_FAIR_SOURCE_EXTRACTION`

## Authority and current gate

The authoritative ARCANA JSON/Markdown and `R6_T0_ORBDATA_ARCANA_FAIR_RUNTIME_QUALIFICATION.json` agree on `R6_T0_ORBDATA_ARCANA_SOURCE_GENERALIZATION_FAIR_QUALIFIED__PRE_ORBDATA_SCIENTIFIC_BLOCKERS_REMAIN`. **OrbData source-generalization FAIR qualification is closed**; no qualification rerun is pending. `PRE_ORBDATA_ready=false` because the current unresolved scientific blockers are exactly:

- governed heat-flow routing and qLim configuration;
- material/thermal OrbData configuration adjudication.

The remaining implementation blocker is materializing the 64,442-node projection after the canonical partition payload is available.

Qualified FAIR ShellSet source identity: branch `arcana-r6-runtime-capacity`, commit `62fd474f229b2676fd9d39c5def45137d22d2481`, executable SHA-256 `4c0044fe4332184d63408960a2237d4edb7da891b71f74b82bd1d5a83b27e918`, governed patch SHA-256 `e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2`. Do not substitute current upstream ShellSet. Although source-generalization FAIR qualification is closed, the heat-flow semantics audit remains pending because this utility has not inspected the exact qualified source checkout on Ubuntu.

## What ARCANA evidence establishes

### A. WORLD_HISTORY physical state/input

- Surface heat flow is required as nodal physical state or an authorized synthetic producer/input with provenance. Candidate runtime manifest B v2 has no heat-flow artifact (`path=null`, `sha256=null`). The current ARCANA OrbData adapter emits age, crust, domain, and total lithosphere grids; it does not emit heat flow.
- `oceanic_lithosphere_age_ma` is physically authoritative only where `physical_crust_domain_id == 1`. The adapter's nearest-ocean extension outside that mask is numerical halo support and does not grant physical age authority.
- No heat-flow source or thermal primitive is bound by the inspected ARCANA artifacts. No values are selected in this audit.

### B. Specialist physical-model configuration

The minimum thermomechanical contract assigns `alphaT`, `conduc`, `TSurf`, `temLim`, `TAsthK`, and geotherm controls (`TADIAB`, `GRADIE`, `ZBASTH`) to specialist thermal-model configuration; their values remain unset. Qualified-source parameter binding and defaults still need extraction.

### C. Numerical guard/limit

The governed patch context shows `qLim1` assigned to `heatFl` when `ageMa <= 0` within the selected oceanic heat-flow branch. This establishes a code path, not the intended parameter value or its authority. ARCANA evidence is insufficient to classify the governance owner of `qLim0`, `dQL_dE`, `qLim1`, or `delta_rho_limit`; their exact roles/bindings remain unresolved. No values are chosen.

### D. Derived OrbData state and routing

- The patch initializes per-node `heatFl` from `dQdTdA(iNode)`, passes it to `Assign` as `INOUT`, then writes the result back to `dQdTdA(iNode)`.
- The patch's explicit ARCANA domain selects ocean routing independently of stock `ageMa < 200` classification. In ARCANA mode, ocean-domain nodes enter the ocean age/heat-flow branch; continental nodes use a separate explicit total-lithosphere path.
- In the selected ocean path, `ageMa <= 0` sets `heatFl=qLim1`.
- The thermomechanical contract says nonzero FEG heat flow is preserved. Patch-level pass-through alone does not prove that earlier `needQ`/`qArray` setup or later source precedence leaves every nonzero value unchanged.

### E. Exact qualified-source evidence still required

Inspect declarations, parameter reads/bindings and execution order in the exact qualified FAIR checkout for all requested symbols: `heatFl`, `dQdTdA`, `needQ`, `qArray`, `qLim0`, `dQL_dE`, `qLim1`, `ageMa`, `alphaT`, `conduc`, `TSurf`, `temLim`, `TAsthK`, `TADIAB`, `GRADIE`, `ZBASTH`, `delta_rho_limit`. Resolve the governance category for the limit symbols, `needQ`, qArray loading/interpolation, zero sentinel, all overrides and precedence, age-zero behavior, ocean/continental behavior, nonzero nodal preservation, and parameter-file defaults. Excerpts must be reviewed; a text match is not scientific adjudication.

### Evidence category separation

The machine-readable report keeps these evidence classes distinct: `WORLD_HISTORY_PHYSICAL_INPUT`, `SPECIALIST_MODEL_CONFIGURATION`, `NUMERICAL_GUARD_OR_LIMIT`, `DERIVED_ORBDATA_STATE`, and `UNRESOLVED_PENDING_SOURCE_ADJUDICATION`. Current ARCANA contracts support high-level input/configuration facts, but symbol-to-category assignments for the requested qualified ShellSet source terms are intentionally empty. `qLim*`, `dQL_dE`, `ageMa`, and other source names remain unresolved until contextual excerpts, binding sites, and call order are adjudicated. The utility emits source matches only and does not classify them automatically.

## Ubuntu extraction utility

The read-only utility [r6_pre_orbdata_heat_flow_source_audit.py](scripts/r6_pre_orbdata_heat_flow_source_audit.py) verifies exact branch and commit before it reads source/parameter text. It never reads the executable, edits ShellSet, or runs OrbData/SHELLS. On Ubuntu, from the ARCANA repository root, run:

```bash
python scripts/r6_pre_orbdata_heat_flow_source_audit.py \
  --shellset-root /home/jlpfritas/HPC-POMDP/tools/ShellSet-v1.1.0
```

It writes `R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.json` and `.md` in the current ARCANA directory, keeping this pending audit contract intact. A branch/commit mismatch exits fail-closed without scanning or writing reports. Source extraction alone does not close the scientific blocker.

## Preserved governance

`PRE_ORBDATA_ready=false`; `t0_orbdata_executed=false`; `shellset_mechanics_authorized=false`; `dt_selected=false`; `t1_created=false`; `forward_evolution_authorized=false`. Windows work is static/unit-only and makes no FAIR runtime claim.

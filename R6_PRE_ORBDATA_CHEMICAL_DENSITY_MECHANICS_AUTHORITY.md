# R6 PRE_ORBDATA — Chemical-Density Mechanics Authority

**Decision:** `R6_PRE_ORBDATA_CHEMICAL_DENSITY_MECHANICS_AUTHORITY_CLOSED__S1_CONSUMER_ARCHITECTURE_COMPLETE__S1A_IMPLEMENTATION_READY`

**Scope:** ARCANA T0 PRE_ORBDATA runtime representation and the meaning of ShellSet's legacy `chemical_delta_rho` compatibility field. This is an authorial authority decision; it is not a ShellSet implementation, runtime qualification, or PRE_ORBDATA readiness declaration.

## Authority decision

For the current R6 T0 PRE_ORBDATA minimum reference state, set:

```text
chemical_delta_rho_kg_m3 = 0.0
classification = NUMERICAL_RUNTIME_REFERENCE_COMPONENT
physical_authority = NOT_CANONICAL_CHEMICAL_GEOLOGY
```

This means no independently governed chemical or compositional density anomaly is materialized for this runtime state. It does **not** mean ARCANA geology has globally zero compositional density variation. The legacy field carries a compatibility value for the ShellSet runtime representation, not canonical chemical geology.

The 51-field runtime package remains `NUMERICAL_RUNTIME_SUPPORT_ONLY`; its data and schema are not changed. The selected S1 consumer architecture remains `SHARED_CANONICAL_RUNTIME_PACKAGE_DUAL_CONSUMER`: OrbData and Shells will independently read the same immutable package and bind its records to unchanged FEG node IDs.

## Residual mechanical state

Legacy OrbData computes an isostatic residual through `Squeez`, derives a trial density adjustment from `sigZZB / (g * total_lithosphere)`, clamps it to `delta_rho_limit`, and serializes the result as a chemical density anomaly. Shells reads that FEG field and uses it in its density and mechanics calculations. The residual arithmetic is deterministic, but ARCANA has not authorized interpreting it as compositional geology.

In complete ARCANA runtime mode, do not infer `chemical_delta_rho` from the residual and do not clamp such an inferred value. With `chemical_delta_rho=0`, retain quantities such as `sigZZB` and `tauZZ` as `DERIVED_REPLAYABLE_MECHANICAL_STATE`. A nonzero residual is an emergent mechanical consequence and must not be silently cancelled by invented composition.

`delta_rho_limit` is **not physical authority** in ARCANA mode and must not serve as a compensation rule. Legacy behavior remains outside this decision scope and must remain unchanged for stock/non-ARCANA execution.

## Thermal profile evaluation

The closed ARCANA thermal-column implementation enforces the governed 1900 K numerical ceiling. Continental columns reject a Moho or LAB endpoint reaching the ceiling and enforce their internal-temperature constraints; ocean and ridge columns check boundary temperatures, while the Hermite validator checks interior extrema against the segment endpoint bounds.

Complete ARCANA mode must evaluate its governed polynomial directly. It must not apply legacy `MIN(temLim,T)` clipping: if the profile violates its authorized validity envelope, fail closed. The ceiling remains a numerical guard, not a solidus interpretation or a new thermal model.

## S1 implementation consequences

### S1A — OrbData

- Read and validate the complete `ARCANA_R6_PRE_ORBDATA_RUNTIME_V1` package and bind records by node identity.
- Preserve governed heat flow, geometry, owner-specific material state, and transient polynomial profiles.
- Write exactly `0.0` to the legacy `chemical_delta_rho` compatibility output, classified as `NUMERICAL_RUNTIME_REFERENCE_COMPONENT` and not canonical geology.
- Retain `Squeez` residual outputs as derived mechanical state; do not convert them into chemical density or apply `delta_rho_limit` compensation.
- In explicit complete ARCANA mode, bypass GDH1, qLim mutation, and legacy steady-geotherm/cooling-curvature fitting.
- Evaluate governed polynomial temperatures directly and fail closed on validity-envelope violations.

### S1B — Shells

- Independently read and validate the same canonical runtime package, keyed by unchanged FEG `node_id`.
- Keep the ARCANA chemical density contribution at `0.0`.
- Construct mechanics state from the governed profile and owner-bound material state; allow derived stress/isostatic consequences to propagate.
- Bypass legacy profile reconstruction in ARCANA mode and preserve the stock path outside explicit ARCANA mode.

## Future refinement

A later ARCANA release may replace the runtime reference component only when a separately governed physical density/composition field exists, with its own provenance and historical resolution. Possible sources include crust/mantle composition, mineralogical state, phase assemblage, or another physically justified geological lineage. A future field must not be reconstructed retrospectively from ShellSet isostatic residuals.

## Preserved gates and remaining work

The authority gap identified by S1-PRE is closed. S1A is ready for implementation. S1B remains the subsequent consumer implementation stage. This does not authorize execution or imply that either stage has been implemented or runtime-qualified.

```text
PRE_ORBDATA_ready = false
OrbData_authorized = false
t0_orbdata_executed = false
SHELLS_ready = false
shellset_mechanics_authorized = false
mechanics_authorized = false
dt_selected = false
t1_created = false
forward_evolution_authorized = false
shellset_runtime_qualified = false
```

No ShellSet source was modified, and OrbData/SHELLS were not run. The next work is S1A implementation and static validation, followed by S1B implementation and qualified Ubuntu build/runtime qualification under their separate authorizations.

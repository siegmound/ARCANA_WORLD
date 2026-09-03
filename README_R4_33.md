# ARCANA WorldSim v0.6D1-R4.33
## Target Authority Binding Static Adjudication & Geonomics Runtime Parameter Compilation Preflight

**Status:** CANDIDATE OVERLAY — requires execution on the authoritative local root.

### Parent required

`v0.6D1-R4.32` must be SEALED with:
- 57 target authority binding records;
- 4 frozen source-identity authorities + 1 terminal pending authority gap;
- 39 selector catalog-extension authorities;
- 12 target-design observable-binding authorities;
- 1 primary-mapping authority;
- 3/3 Geonomics static parameter manifests valid;
- runtime compilation still 0;
- no Geonomics execution / numeric target execution / readjudication.

### R4.33 target lane

R4.33 performs **static authority adjudication only**.

Expected live dispositions:
- 4 exact source identities -> future numeric-execution **candidates**, not authorized executions;
- 1 source-identity authority gap remains deferred;
- 39 catalog-extension records remain rule-selection deferred;
- 12 observable-binding records remain exact-source-binding deferred;
- 1 primary mapping authority remains mapping-class/numeric-value frozen.

No target value is computed.

### R4.33 Geonomics lane

R4.32 deliberately retained:
- candidate/replay uncertainty dimensions;
- provenance-separated environment/producer layers;
- no target-derived tuning.

Therefore R4.33 compiles exactly **three hash-bound runtime parameter binding packages**
(J14/J18/J21), inventories their canonical NPZ inputs and preserves all five mapping classes,
but does **not** invent default selectors or collapse uncertainty/layer dimensions.

Consequently, a successful R4.33 is expected to report:
- runtime binding packages compiled = 3;
- native Geonomics `params` files materialized = 0;
- runtime selector authority required = 3;
- `gnx.make_model()` validation = not performed;
- Geonomics scientific execution = not authorized.

This is not a missing implementation. It is the fail-closed preflight result required by the
R4.32 uncertainty semantics.

### Next natural stage after a successful R4.33 seal

`BUILD_R434_GEONOMICS_RUNTIME_SELECTOR_AUTHORITY_FREEZE_AND_NATIVE_PARAMETER_MATERIALIZATION_PREFLIGHT`

R4.34 can freeze explicit runtime selectors/layer-combination authority and only then
materialize native Geonomics parameters and consider model-construction validation.
Scientific execution remains a separate later authorization.

### Run

```powershell
.\run_v0_6D1_R4_33.ps1
```

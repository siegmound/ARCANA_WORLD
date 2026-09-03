# ARCANA WorldSim v0.6D1-R4.35
## Geonomics Native Schema Mapping, Initial-State Adapter & Seed Authority Closure

**Status:** CANDIDATE OVERLAY — requires execution on the authoritative live root.

### Parent required

R4.34 SEALED:
- selector authority frozen 3/3;
- native parameter preflight 3/3;
- exactly 19 explicit native-schema authority gaps;
- native params 0;
- `read_parameters_file` not performed;
- `make_model` not performed;
- no Geonomics execution.

### R4.35 closes the 19 gaps without inventing science

#### Geometry
The canonical raster/grid is exposed to Geonomics as an **index coordinate system**:
- `dim = (n_cols, n_rows)` derived from the canonical source;
- `res = (1,1)`;
- `ulc = (0,0)`;
- `prj = None`.

This preserves cell topology only. It explicitly does **not** authorize km, km² or any
physical-distance interpretation.

#### Time
Each exact canonical age-axis element is mapped bijectively to an integer model-step index.
The sidecar retains the exact physical duration between adjacent ages.
No interpolation, extrapolation or equal-duration assumption is introduced.

#### Seed
R4.35 reuses `outputs/v0_6D1_R4_3/R4_3_SEED_LEDGER.json`.
The live ledger contains exactly 23 frozen jobs × 4 ordered replicate seeds = 92 seeds. R4.35-R2 preserves each four-seed vector in ledger order, requires all 92 seeds to be globally unique, and binds `params.model.seed.num` independently per replicate. No scalar seed is chosen and no new seed is generated.

#### Layer scaling
Identity values only. No automatic `[0,1]` normalization, clipping or target-fitted scaling.

#### J14/J18 population semantics
ARCANA `effective_population` / `population_proxy` is **not** converted to literal Geonomics
census individuals.

The adapter authority is:
- one nonliteral connectivity carrier per active deme;
- exact canonical population value retained as immutable sidecar weight;
- demographic population-count adjudication forbidden;
- authorized scientific scope: connectivity / range-support proxy only.

#### J14/J18 exact initial state
Future model construction must inject carriers at:
- J18: `x = grid_col`, `y = grid_row` exactly (continuous canonical grid-space coordinates)
- J14: preserve the R4.31 SEALED spatial-authority coordinate semantics; no stochastic relocation

using the exact active-deme ordering and Geonomics' coordinate-addition API.
Random K-weighted initialization is forbidden.

#### J14/J18 K layer
A binary canonical-support layer with `K_factor=1` may be used only as a model-construction
scaffold for the connectivity proxy. It is never an ARCANA carrying-capacity claim and does not
authorize demographic interpretation.

#### J21
Environment and producer-support arrays are bound as separate Geonomics defined-layer sets.
No numerical fusion is allowed and producer support is never synthesized into individual agents.

### What R4.35 still does not do

- no native Geonomics parameter file is written;
- no `gnx.make_model()`;
- no exact-state injection is executed;
- no Geonomics run;
- no target numeric execution;
- no readjudication;
- no canonical write.

### Next stage after successful seal

`BUILD_R436_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_CONSTRUCTION_AND_EXACT_STATE_INJECTION_PREFLIGHT`

R4.36 may finally materialize native Geonomics parameters, construct models without running
them, and validate exact state injection against the R4.35 authority sidecars.

### Run

```powershell
.\run_v0_6D1_R4_35.ps1
```

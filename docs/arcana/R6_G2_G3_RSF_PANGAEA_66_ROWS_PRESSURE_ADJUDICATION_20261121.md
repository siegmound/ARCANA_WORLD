# ARCANA R6 — FAIR 66 PANGAEA model fits; pressure-authority correction

Date: 2026-11-21. Original FAIR tested source: `8bbbab1c4fe19792a7f733e3c43d870de55f9e20`.
Scientific code correction: `48e460c10f1786b2f6caa8f5cd248507ab5dc8eb`.
Decision: `REAL_EARTH_RSF_TABLE2_66_FITTED_ROWS_ACQUIRED__PER_EXPERIMENT_NORMAL_PRESSURE_UNBOUND__NO_PHYSICAL_FAULT_SOLVE`.

## 1. Operator FAIR receipt

The operator supplied this terminal output (not independently rehashed here):

```text
source commit: 8bbbab1c...
13 passed in 0.07s
RSF_TEST_EXIT_CODE=0
DOWNLOAD_EXIT_CODE=0
PANGAEA 921284 SHA256:
b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d
status: SOURCE_INGESTED__EARTH_ANALOGUE_ONLY_NOT_T0
model_fit_rows: 66
RSF_INGEST_EXIT_CODE=0
mechanical_solve_authorized: false
physical_T1: null
```

FAIR source location:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_G3_PANGAEA921284_RAW_NEW_01/pangaea_921284.tab`.

This demonstrates source download, SHA logging, parser acceptance and **66 published inverse-model fitted rows**. They are not 66 independent instrument measurements or 66 ARCANA geological fault sites. The original bytes/rows were not transferred to the authoring environment, so this receipt does not independently verify row contents beyond the operator's successful parser run.

Dataset: https://doi.org/10.1594/PANGAEA.921284 .

## 2. Primary-literature discrepancy with universal 10 MPa scaling

The original research source (Ikari & Kopf 2017, `10.1126/sciadv.1701269`, https://pmc.ncbi.nlm.nih.gov/articles/PMC5706663/ ) describes modern powdered gouge tests at approximately **20°C**, nominal **10 MPa assumed effective normal stress**, with **prior Tohoku samples at 7 MPa**. These are *different test origins* and cannot all be taken as 10 MPa without confirming each dataset row's experiment identifier and specific loading record.

The PANGAEA Table 2 importer validates a 19-field fitted parameter table without a per-row effective normal pressure column. The previous module's universal `10MPa * delta_mu` therefore was not appropriately source-bound to each row. **The first FAIR `INGEST_NEW_01` report is retained immutable as historical evidence, but any reported conditional `delta_tau` in it is NOT physically qualified and must not be used to drive ARCANA G3.**

### Corrective implementation

Current development candidate:
- `lab_nominal_effective_normal_stress_pa` = 10 MPa (study-level metadata only).
- `lab_effective_normal_stress_pa` = `null`, `per_experiment_effective_normal_stress_qualified=false`.
- `delta_mu` and `steady_delta_mu` remain calculated from fitted `a,b_i,Dc_i`, with an explicitly assumed steady initial state.
- All `delta_tau_pa`, `steady_delta_tau_pa`, output normal pressure and absolute traction fields remain `null`, and the public API refuses a caller-supplied unbound pressure.
- `dataset_fit_inventory` records fitted row count, distinct study event/sample/experiment identifiers, one-/two-state rows and sign counts of reported `a-b`, without asserting independent replicates or an ARCANA lithology assignment.

The local authoring version of this scientific fix passed **13/13 unit tests** (Python 3.13.5); the exact GitHub commit awaits FAIR. It would be incorrect to claim the real per-experiment pressure is now established: no pressure-mapping provider has yet been ingested.

## 3. Qualification still missing

Separate source-backed test load mapping, material identification, gouge composition/hydration, **full crustal 280–1051.558K temperature coverage**, effective normal stress per fitted row, applicable relative slip speeds, reference absolute friction `mu_ref`, source fault side/interface geometry, fault traction transmission, G3 far-field/base forces and mantle, and compatible nonlinear solver. The authentic G3 source triple parent `34587` is not a new freely sliding state.

```text
PANGAEA921284_OPERATOR_ORIGINAL_FAIR=13/13_PASS
PANGAEA921284_REAL_FITTED_ROWS=66
PANGAEA921284_RAW_SHA256=b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d
PANGAEA921284_CORRECTED_SOURCE_FAIR=PENDING
CORRECTED_PER_EXPERIMENT_NORMAL_PRESSURE=null
ALL_DELTA_TAU_FROM_SOURCE_UNQUALIFIED=true
ARCANA_FAULT_SOURCE_AUTHORITY=false
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

## 4. FAIR next action

1. Checkout exact corrected development commit and run the RSF tests, then the full 134-test G2/G3 baseline + 13 RSF tests at the **same code SHA**.
2. Using exactly the SHA-pinned earlier downloaded raw `pangaea_921284.tab`, run the corrected importer with `--output .../INGEST_NEW_02`; never mutate `INGEST_NEW_01`.
3. Verify 66 rows, SHA equality, `dataset_fit_inventory`, all 66 `delta_tau` fields `null`, source grouping. Do not infer physical loads from the study-level 10 MPa.
4. Only then consider a fast-forward merge back to main; physical G2/G3 solver and T1 remain NO-GO.

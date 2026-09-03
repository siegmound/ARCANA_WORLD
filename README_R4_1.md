# ARCANA WorldSim v0.6D1-R4.1

## Multi-Engine Semantic Calibration + Controlled Microbenchmarks

R4.1 consumes the locally SEALED R4.0 infrastructure and performs the first real multi-engine scientific executions.

It **does not modify canonical state** and does **not** yet execute the seven historical World-1 windows. Its purpose is to prove that each engine can produce governed scientific evidence with semantics that ARCANA can compare safely.

## Run

Extract this overlay into the same project root used for R4.0, preserving the existing `.arcana_engines`, Conda environments, `set_r40_engine_env.local.ps1`, R4.0 configuration and R4.0 seal outputs.

Then run from PowerShell:

```powershell
.\run_v0_6D1_R4_1.ps1
```

No provisioning command is required if R4.0 remains SEALED and the six runtimes are unchanged.

## What the runner does

1. validates R4.1 source authority;
2. runs R4.1 regression tests;
3. captures fresh exact identities for all six R4.0 engines;
4. executes six real controlled scientific microbenchmarks through WSL/Conda;
5. validates benchmark metrics and semantic rules;
6. freezes the domain-specific authority matrix;
7. verifies that the seven R4.0 historical windows are unchanged;
8. emits a fail-closed R4.2 execution authorization gate;
9. seals R4.1 only if every required check passes.

## Main outputs

- `outputs/v0_6D1_R4_1/R4_1_RUNTIME_IDENTITY_EVIDENCE.json`
- `outputs/v0_6D1_R4_1/R4_1_HOST_MICROBENCHMARK_EVIDENCE.json`
- `outputs/v0_6D1_R4_1/R4_1_ENGINE_MICROBENCHMARK_REPORT.json`
- `outputs/v0_6D1_R4_1/R4_1_SEMANTIC_AUTHORITY_MATRIX.json`
- `outputs/v0_6D1_R4_1/R4_1_HISTORICAL_WINDOW_EXECUTION_GATE.json`
- `outputs/v0_6D1_R4_1/R4_1_INTEGRATED_AUDIT.json`
- `outputs/v0_6D1_R4_1_SEAL/R4_1_FINAL_SEAL_AUDIT.json`

## Expected success

The final line is:

`PASS_R41_INTEGRATED_AND_FINAL_SEAL_RUN`

and the final seal status is:

`PASS_R41_MULTI_ENGINE_SEMANTIC_CALIBRATION_CONTROLLED_MICROBENCHMARKS_AND_HISTORICAL_REVALIDATION_GATE_SEALED`

If one engine fails, R4.1 preserves all other engine evidence, reports the exact benchmark/return code/metrics, and exits blocked. Do not start R4.2 until R4.1 is SEALED.


### Adapter hardening notes
- RangeShiftR: use one-replicate `ReturnPopDataFrame` execution and derive instantaneous occupied cells from `totalAbundance > 0`; do not equate this with the engine's multi-replicate Occupancy product.
- CDMetaPOP: isolate the first pinned generic PopVars row into the benchmark workdir and apply only the documented `implement_disease=N` schema shim there.

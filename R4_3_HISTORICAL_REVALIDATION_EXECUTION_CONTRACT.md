# ARCANA WorldSim v0.6D1-R4.3 — Historical Revalidation Execution Contract

R4.3 is the first R4 stage allowed to execute the **exact 23 engine-window jobs frozen in R4.2**.

## Authority and invariants

- ARCANA WorldSim remains the sole canonical-state owner.
- The R4.2 seven-window / 23-job freeze is immutable in R4.3.
- No external engine can write ARCANA canonical state.
- No result can auto-promote to canon.
- No majority vote is permitted.
- R3 parameters and sealed physics/biology are unchanged.
- Deep biological coupling remains OFF.
- Raw engine evidence is preserved separately from normalized evidence.
- Failures, NaN values, noncomparability and negative results are preserved.
- R4.3 performs **execution + normalization + completeness audit only**. Scientific discordance adjudication belongs to R4.4.

## Historical execution semantics

The external engines have incompatible native clocks, population semantics and spatial semantics. Therefore R4.3 does not pretend that a multi-Myr ARCANA window can be replayed literally as the same number of engine years/generations.

Each frozen job is executed as a **normalized boundary-response revalidation experiment**:

1. read the frozen ARCANA baseline artifact(s);
2. materialize the start state and exogenous forcing without using the ARCANA end result to parameterize the engine;
3. map historical duration explicitly to a bounded engine-native representative runtime;
4. execute multiple deterministic-seed replicates;
5. preserve raw engine-native metrics;
6. normalize only scientifically declared quantities;
7. retain the ARCANA end state only as a later comparison target;
8. defer `CONCORDANT / CALIBRATION_OFFSET / STRUCTURAL_DISAGREEMENT / ...` classification to R4.4.

This is deliberately fail-closed: a crash is `ENGINE_EXECUTION_FAILURE`, an adapter problem is `ADAPTER_FAILURE`, and a semantic mismatch is `SEMANTIC_NONCOMPARABILITY`; none is silently converted into scientific disagreement.

## Execution phases

- **Phase A — pre-execution materialization:** exact R4.2 job freeze verification, per-job semantic/unit mapping, deterministic seed ledger and baseline descriptor audit. No historical engine execution.
- **Optional governed plumbing smoke:** six pre-declared jobs, exactly one per engine, may be executed before the full batch. The smoke is only an adapter/runtime check and is never used for result selection or scientific adjudication.
- **Phase B — full execution:** all exact 23 frozen jobs are executed. Existing smoke evidence may be overwritten by the full governed execution; the job list itself is unchanged.
- **Phase C — completeness:** every job must terminate with either `SCIENTIFIC_RESULT` or scientifically meaningful `SEMANTIC_NONCOMPARABILITY`. Engine/adaptor/missing-evidence failures block the seal.

A single `-JobId` execution is allowed only for targeted adapter diagnosis/repair and never produces an R4.3 completeness seal.

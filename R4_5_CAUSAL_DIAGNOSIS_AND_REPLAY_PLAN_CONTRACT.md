# ARCANA WorldSim — v0.6D1-R4.5
## Earliest-Affected-Authority Causal Diagnosis, Evidence-Robustness Gate & Minimal Replay Plan

**Parent:** `v0.6D1-R4.4 SEALED`

R4.5 is a diagnosis/planning stage. It does **not** modify R3 parameters and does **not** execute a canonical replay.

### Purpose
1. Resolve every R4.4 `STRUCTURAL_DISAGREEMENT` to the exact PRIMARY evidence row(s) that created it.
2. Test whether the disagreement survives external replicate uncertainty (q10–q90), not merely the median.
3. Trace the earliest replay boundary to the actual ARCANA authority files.
4. Register all calibration offsets without retuning.
5. Decompose evidence gaps by cause so later adapter work is targeted rather than result-selected.
6. Authorize, at most, a **diagnostic counterfactual** from the earliest affected authority when the structural signal is robust.

### Robustness rule (frozen pre-result)
A structural row is `ROBUST_PRIMARY_STRUCTURAL_DISAGREEMENT` only if:
- it is PRIMARY authority;
- mapping and ARCANA target are `DIRECT` or `NORMALIZABLE`;
- R4.4 classified it structural;
- at least 4 external replicates are summarized;
- q10 and q90 lie wholly on the same meaningful response side as the external median and that side is opposite the ARCANA target, outside the frozen neutral band.

A median-only sign flip is insufficient to authorize a replay experiment.

### Governance
- no majority vote;
- no automatic external promotion;
- no canonical write;
- Deep biological coupling remains OFF;
- the 67 insufficient and 2 semantically non-comparable R4.4 cells remain evidence, not failures;
- calibration offsets are recorded but cannot change parameters here;
- even a robust structural result authorizes only a targeted diagnostic counterfactual in the next stage, never an immediate canonical rewrite.

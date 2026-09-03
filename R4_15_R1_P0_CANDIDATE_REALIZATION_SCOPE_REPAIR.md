# R4.15-R1 — P0 Candidate Realization Scope Repair

## Trigger

The initial R4.15 run was fail-closed with 1/4 P0 cells recovered while all 59 P1 cells were audited. R4.14 had frozen those four P0 entries as **retained-runtime recovery candidates**, each with a specific `closure_action` such as `RETAINED_NEMO_RUNTIME_METRIC_RECOVERY_CANDIDATE`.

The initial R4.15 implementation nevertheless required **every PRIMARY engine present in the same window/domain cell** to have a successful retained extractor. That is broader than the R4.14 frozen candidate action and can block a cell even when the exact predeclared retained engine was recovered successfully.

## Repair

R4.15-R1 does not change the R4.14 census, authority matrix, R4.2 frozen job registry, engine results, targets, thresholds, or canonical state.

For each of the four frozen P0 cells it:

1. derives the authorized retained-recovery engine strictly from the pre-result R4.14 `closure_action`;
2. audits all PRIMARY engine records for context;
3. requires successful recovery only from the engine that R4.14 actually nominated for that P0 candidate;
4. verifies that R4.14 had already recorded at least one retained-runtime hit for that engine;
5. if the predeclared candidate cannot be cleanly recovered by the frozen extractor, it is **not fabricated** and no engine is rerun: that candidate is explicitly exhausted and moved to the P2 adapter-enhancement/symmetric-reexecution backlog;
6. requires all four P0 candidates to receive an explicit disposition before R4.15 can seal.

Thus the repaired accounting is:

`resolved P0 = recovered P0 + exhausted/reclassified-to-P2 P0 = 4`.

Only actually recovered metrics may enter the R4.16 domain-transform promotion gate. Exhausted candidates remain non-adjudicative and deferred to P2.

## Additional runner repair

The initial PowerShell wrapper printed its terminal PASS label even when the Python stage returned a non-zero fail-closed status. R4.15-R1 now checks `$LASTEXITCODE` after source authority, pytest, build, and final seal, and exits non-zero on any blocked gate.

## Invariants

- engine execution: forbidden;
- R4.2 frozen 23-job registry: unchanged;
- canonical state: unchanged;
- canonical replay: not authorized;
- canonical parameter change: not authorized;
- Deep biological coupling: OFF;
- external evidence may not define ARCANA targets;
- no metric or target promotion in R4.15-R1;
- no majority vote;
- initial blocked R4.15 evidence preserved under `outputs/v0_6D1_R4_15/repair_history/`.

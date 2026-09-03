# v0.6D1-R4.30

This overlay executes the work authorized by the R4.29 seal:

1. Attempts numeric materialization for exactly the five R4.29-authorized selector authorities. Source hashes are rechecked and the selector must bind uniquely to an exact canonical source. A transform with an unbound semantic dependency is deferred rather than guessed.
2. Freezes closure routes for the remaining 39 selector-authority gaps without adding selectors.
3. Executes the one authorized `PRIMARY_MAPPING_ELIGIBILITY_REVIEW_ONLY` semantic review without changing numeric values or mapping classes.
4. Executes the new engine-independent J14 3 Ma -> 200 ka spatial authority candidate and audits R3.27 macro invariants, age-matched canonical land support, provenance hashes, and the prohibition on future spatial anchors/external engines.

The J14 artifact is intentionally marked **candidate authority pending R4.31 validation seal**. R4.30 does not authorize or run Geonomics and does not readjudicate the 75-cell matrix.

Run on Windows PowerShell:

```powershell
.\run_v0_6D1_R4_30.ps1
```

Expected next stage after a clean seal:

`BUILD_R431_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_SELECTOR_AND_TARGET_DESIGN_AUTHORITY_CLOSURE_AND_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL`

## R4.30-R1 repair
R4.30-R1 repairs only the authorized-selector source-binding scope. The initial gate incorrectly required every parent candidate source packet to remain hash-valid even when a unique hash-valid exact-selector source still existed. The repair binds to the unique exact authorized source and records unrelated candidate-packet drift without using it as a veto. Zero exact bindings remain fail-closed; multiple exact bindings remain deferred. The first blocked R4.30 outputs are preserved by the PowerShell runner under `outputs/v0_6D1_R4_30/repair_history/R430_INITIAL_OVERBROAD_ALL_PARENT_SOURCE_PACKET_INTEGRITY_GATE_BLOCKED/`.


## R4.30-R2 repair
R4.30-R2 distinguishes **source integrity** from **source-binding authority**. If no exact selector binding can be reconstructed but at least one parent source packet remains hash-valid, the target is deferred because R4.29 never froze which packet supplied the aggregate-inventory selector. If all parent packets fail integrity, R4.30 remains BLOCKED. The current R4.30-R1 blocked evidence is preserved under `outputs/v0_6D1_R4_30/repair_history/R430_R1_SOURCE_BINDING_AUTHORITY_SCOPE_BLOCKED/`.

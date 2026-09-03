# v0.6D1-R4.6-R1 — Targeted R3.11 Causal Counterfactual & R4.3 CDMetaPOP Forcing-Parity Audit

## Repair reason
The first R4.6 candidate failed closed before executing the counterfactual because it incorrectly froze the R4.5-authorized PRIMARY row as RangeShiftR/J08. The sealed R4.5 diagnosis actually authorized:

- window `H0_POST_CHA1_RECOVERY` (65.5→55 Ma),
- domain `population_persistence`,
- earliest boundary `R3.11_POST_CHA1`,
- PRIMARY engine `CDMetaPOP`,
- frozen job `R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP`.

R4.6-R1 corrects only this scope/control error. The blocked R4.6 attempt produced no scientific counterfactual result and authorized no canonical write.

## Scientific task
R4.6-R1 performs two diagnostics only:

1. **R4.3 CDMetaPOP forcing-parity audit.** It checks the frozen J09 driver contract against the actual `benchmarks/r43/cdmetapop_r43.py` source. The R4.3 adapter parameterizes start-state patch `K/N0` and migration/gene-flow controls. For `population_persistence`, R4.6 explicitly tests whether nonzero/change-bearing end/dynamic forcing (`normalized_environment_change`, `normalized_habitat_fraction_end`) was actually consumed. Missing dynamic forcing is recorded as an adapter/input-semantic coverage gap, not as a scientific failure of CDMetaPOP.

2. **R3.11→R3.12 diagnostic counterfactual.** Starting from the exact SEALED R3.10 65.5 Ma checkpoint, execute ordinary R3.11/R3.12 machinery to 55 Ma while holding only `env.reference_population` at its 65.5 Ma value. All other environment fields and all scientific constants remain unchanged. No canonical checkpoint is written.

## Governance
- Canonical owner remains ARCANA WorldSim.
- Canonical replay remains unauthorized.
- Parameter changes remain unauthorized.
- Deep biological coupling remains OFF.
- No majority vote.
- A confirmed CDMetaPOP adapter forcing gap does **not** prove R3.11 correct or incorrect.
- The counterfactual is sensitivity evidence only.

## Symmetry guard
If the common R4.3 CDMetaPOP adapter semantics are repaired or downgraded, every frozen job using that adapter must be re-evaluated in a **new evidence namespace**:

- J03 `H0_DEEP_TIME_BACKGROUND_CDMETAPOP`
- J06 `H0_PRE_CHA1_CDMETAPOP`
- J09 `H0_POST_CHA1_RECOVERY_CDMETAPOP`
- J15 `SAPIENT_3MA_TO_200KA_CDMETAPOP`
- J20 `SAPIENT_200KA_TO_0_CDMETAPOP`

No result-selected J09-only patch is allowed.

## Expected next branch
If dynamic forcing coverage is missing, R4.7 must choose between:

- a scientifically justified CDMetaPOP forcing-parity adapter repair followed by symmetric re-execution of all five CDMetaPOP frozen jobs; or
- a comparability downgrade for affected domains where no lawful mapping exists.

Only after renewed evidence/adjudication may any canonical R3.11 recalibration be considered.

# ARCANA WorldSim v0.6D1-R3.22 candidate overlay

This overlay implements the **Generic Functional Phenotype Specification** above the SEALED R3.21 registry.

It is deliberately specification-only:

- no phenotype values are assigned;
- no biology is replayed;
- no human lineage is selected or ranked;
- Deep remains OFF;
- H0 and CHA-2 remain untouched.

## Run

Overlay on the current WorldSim root, then:

```powershell
.\run_v0_6D1_R3_22_checks.ps1
.\run_v0_6D1_R3_22_functional_phenotype_spec.ps1
```

The production runner requires:

`outputs\v0_6D1_R3_21_SEAL\R3_21_FINAL_SEAL_AUDIT.json`

and its manifest to pass closure. It fails closed if the R3.21 seal is not the expected 43/43 SEALED authority.

Expected result:

`PASS_R322_GENERIC_FUNCTIONAL_PHENOTYPE_SPECIFICATION_CANDIDATE`

Outputs:

`outputs\v0_6D1_R3_22\`

## Key design decisions

- state is component-level (295 current components), not one scalar per species;
- 31 primary functional traits across 8 primary domains;
- tool-use potential and environmental problem-solving are derived contextual capabilities;
- trait applicability is distinct from trait magnitude;
- not-applicable traits cannot become active by continuous drift alone;
- no new numerical heritability, covariance, cost or selection parameters are introduced;
- existing R3.19/R3.21 reduced ecological genetic state remains separate;
- future calibration must be comparative and non-anthropocentric.

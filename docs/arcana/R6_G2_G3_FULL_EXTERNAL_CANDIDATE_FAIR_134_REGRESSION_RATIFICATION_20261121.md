# R6 — G2/G3 complete external-channel engineering candidate: FAIR regression receipt

Date: 2026-11-21
Exact tested source commit: `f4524ec225110f99e970505e098c5cce61ff8fab`.
FAIR environment: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY`,
Python 3.12.14, environment `arcana-r6-linux`.
Evidence provenance: pasted FAIR operator terminal output; log file referenced below exists on operator workstation, but neither its bytes nor an independent full-suite run were available in this GitHub authoring environment.

## Observed source execution

```text
Checked out: f4524ec2 docs(r6): record FAIR 38/38 targeted receipt; full regression still pending
........................................................................ [ 53%]
..............................................................           [100%]
134 passed in 0.67s
FULL_REGRESSION_EXIT_CODE=0
LOG=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/G2G3_DEBUG/full_regression.log
```

The operator additionally reported **38/38 targeted PASS** at source `1f7af785d83f26c5e4853227b280e01dcceae9c6`, and the tested `f4524ec2` commit appended only documentation and ledger metadata to that code.

Source validation conclusion:

- `TARGETED_G2_G3_FAIR=PASS_OPERATOR_REPORTED_38_OF_38`
- `EXTENDED_G2_G3_REGRESSION_FAIR=PASS_OPERATOR_REPORTED_134_OF_134`
- `EXTENDED_G2_G3_EXIT_CODE=0`
- `G2_G3_COMPLETE_EXTERNAL_CHANNEL_ENGINEERING_SOFTWARE_GATE=PASS`
- `FULL_PHYSICAL_TRACTION_SOURCE_AUTHORITY=OPEN`
- `FULL_PHYSICAL_ROCK_AND_RHEOLOGY_SOURCE_AUTHORITY=OPEN`
- `PHYSICAL_THIN_SHEET_FAULT_SLIP_LAW=OPEN`
- `CORE_BASAL_NORMAL_CLOSURE=OPEN`
- `MECHANICAL_SOLVE_AUTHORIZED=false`
- `physical_T1=null`
- `D_024=ACTIVE`
- `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`

This test gate is applicable to **source-original full internal mechanics and optional full-channel candidate G3 external load accounting**. It does not demonstrate a physical whole-domain equilibrium or a completed actual-real-force scenario. The explicit candidate channel still demands supplied 81/289-node material/velocity, 8-core plus 120/504-exterior physical traction data and explicit non-duplicated core/exterior GPE, not filled by this test. The source topology and FE test regression are not independent physical measurement.

## Merge decision

The dev branch was 5 commits ahead, 0 behind the target `r6/multiphysics-integration-20261026` as compared before this receipt was written; a source-preserving fast-forward is allowed only if the target remains at exact `85a6ba7e4d5dfdde0de2eb0ca716d3670472fbef`. No forced history rewrites. This receipt is a post-run document-only commit; Python source at the new branch tip remains bitwise identical to the tested `f4524ec2` code.

Next substantive task: authorially selected lithology/water and pressure, qualified P/T/strain-rate creep/brittle law, genuine regional cut and *full basal* normal/tangential force provider, one-owner GPE and validated 2D thin-sheet slip/transmission mechanics. Keep all absent physical sources explicit `null` and don't turn test fixtures into ARCANA geological history.

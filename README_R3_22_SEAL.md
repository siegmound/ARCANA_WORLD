# ARCANA WorldSim v0.6D1-R3.22 — Final Seal Audit

Read-only final seal overlay for the already-materialized R3.22 specification outputs.

It does **not** materialize functional phenotype values, execute biology, enable Deep, rank lineages, or modify R3.21/H0/CHA-2.

Run from the WorldSim root after the R3.22 candidate has produced `outputs/v0_6D1_R3_22`:

```powershell
.\run_v0_6D1_R3_22_seal.ps1
```

The audit validates the actual R3.21 seal and its manifest, then independently closes:

- exact R3.21/R3.19 provenance;
- exact R3.22 output hash/size manifest;
- 10 domains, in canonical order;
- 31 primary component-level evolvable traits, in canonical order and domain assignment;
- 2 derived contextual capabilities with only valid trait/environment dependencies;
- no human/sapience/civilization/readiness target in primary trait IDs;
- no phenotype, heritability, covariance, cost, selection optimum, or applicability values materialized;
- 7 governed trade-off/constraint edges with no author-assigned numeric strengths;
- applicability states and governed innovation gate;
- five future state arrays as schema only;
- future G-covariance symmetry/PSD requirement;
- existing R3.19 reduced ecological state not repurposed;
- no invented cross-covariance with the existing three ecological traits;
- empirical calibration required before any materialization or replay;
- candidate audit 34/34 PASS.

On success it writes `outputs/v0_6D1_R3_22_SEAL/` and prints `PASS_R322_FINAL_SEAL_CHECKS`.

# ARCANA WorldSim v0.6D1-R4.53
## Non-Geonomics Scientific Execution Interface & Readout Authority Preflight

R4.52 SEALED the exact remaining plan:

- 20 jobs
- 5 engines
- 4 frozen seeds per job
- 80 planned scientific streams
- execution-plan SHA256:
  `f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6`

R4.53 performs no external-engine execution.

It freezes the scientific execution interface and authorized readouts for the
five remaining engines before any historical stream is allowed to run.

## Madingley

Authorized scientific-descriptive readouts:

- `MADINGLEY_COHORT_COUNT_TRAJECTORY`
- `MADINGLEY_STOCK_COUNT_TRAJECTORY`

These describe functional ecosystem state.

They do **not** define ARCANA species identity.

## RangeShifter

Authorized:

- `RANGESHIFTER_ABUNDANCE_TRAJECTORY`
- `RANGESHIFTER_OCCUPIED_CELL_TRAJECTORY`

Literal abundance equality with ARCANA population units is forbidden.
Occupancy requires the explicit eligible-habitat denominator already demanded
by the R4.1 semantics.

## CDMetaPOP

R4.1 proved that CDMetaPOP 3.08 executed and materialized outputs, but mere
`csv_output_files > 0` is not biological scientific evidence.

R4.53 therefore authorizes native biological summaries instead:

Primary native artifacts:

- `summary_popAllTime.csv`
- `summary_classAllTime.csv`

Authorized scientific-descriptive readouts:

- `CDMETAPOP_POPULATION_STATE_TRAJECTORY`
  - `Year`
  - `N_Initial`

- `CDMETAPOP_GENETIC_DIVERSITY_TRAJECTORY`
  - `Year`
  - `Alleles`
  - `He`
  - `Ho`

Pinned source commit remains integrity authority:

`3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118`

## NEMO

Authorized:

- `NEMO_ALLELE_FREQUENCY_TRAJECTORY`
- `NEMO_REALIZED_FREQUENCY_CHANGE_SUMMARY`

The raw qfreq/allele-frequency trajectory is primary evidence.
No result-selected summary statistic is permitted.

## SLiM

The raw tree sequence is the primary scientific artifact:

`SLIM_TREE_SEQUENCE_RAW`

Authorized derived readouts:

- `SLIM_TREE_SEQUENCE_STRUCTURAL_SUMMARY`
- `SLIM_ANCESTRY_GENE_FLOW_SUMMARY`

The ancestry/gene-flow extractor itself must be frozen before the historical
run.

## R4.1 relationship

The six R4.1 controlled microbenchmarks remain semantic/executable gates.

They are explicitly **not** reclassified as historical scientific evidence.

R4.53 verifies the original R4.1 semantic rules:

- no literal cross-engine N equality;
- explicit generation/timestep mapping;
- explicit spatial denominator;
- no assumption that genetic parameters have identical engine semantics;
- Madingley cohorts/stocks do not define ARCANA species;
- a single microbenchmark run is non-promotional.

## No numeric adjudication threshold

All 10 scientific metric definitions are descriptive.

R4.53 freezes:

- numeric acceptance thresholds = 0
- automatic scientific PASS/FAIL = 0
- majority vote = false
- result-selected metric = false
- result-selected threshold = false
- engine-defined ARCANA target = false
- canonical rewrite = false

## Why execution is still not authorized

Every one of the 20 jobs remains:

`r454_seed_and_readout_dry_run_required = true`

R4.54 must demonstrate, on disposable non-scientific dry-runs:

1. exact injection/readback of each frozen seed;
2. isolated output materialization;
3. extraction of only the authorized readouts;
4. schema validity and finite descriptive values.

Only after that may the 80 historical scientific streams be authorized.

Run:

```powershell
.\run_v0_6D1_R4_53.ps1
```

Next if SEALED:

`BUILD_R454_NON_GEONOMICS_EXACT_SEED_INJECTION_READOUT_EXTRACTION_DRY_RUN_AND_SCHEMA_VALIDATION`

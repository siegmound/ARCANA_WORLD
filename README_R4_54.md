# ARCANA WorldSim v0.6D1-R4.54
## Non-Geonomics Exact Seed Injection + Readout Extraction Dry-Run + Authorization

Parent authority:
- R4.53 integrated 39/39 PASS
- R4.53 seal 23/23 SEALED
- R4.52 20-job plan SHA256:
  `f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6`
- R4.53 readout registry SHA256:
  `f39bb36251a95f2d9e310113a9286608d72188374d7d9bc73fe90aa697e5d380`

R4.54 performs five **real runtime disposable dry-runs**, one per remaining
engine. These are deliberately not historical job executions and are not
scientific evidence.

Probe selection is deterministic:
- first frozen R4.52 job for the engine;
- first frozen seed of that job.

## Seed transport

- Madingley: `set.seed(seed)` before initialization/run.
- RangeShifter: native `RSsim(seed=seed)`.
- CDMetaPOP: both `random.seed(seed)` and `numpy.random.seed(seed)` in the same
  Python process before `runpy` executes the pinned 3.08 source.
- NEMO: isolated INI `random_seed`.
- SLiM: native CLI `slim -s seed`.

The CDMetaPOP shim does not modify the installed source tree. The pinned source
uses NumPy RNG throughout and Python `random` in the disease module, so both
process RNGs are frozen before imports/execution.

## Readout extraction

Each dry-run must emit exactly the two R4.53-authorized metrics for its engine,
with finite payloads and zero numeric acceptance thresholds.

NEMO is run with more frequent qfreq logging in the isolated dry-run INI so the
extractor validates a multi-generation frequency trajectory.

SLiM preserves the raw `.trees` file and validates:
- tree-sequence structural summary;
- between-population genealogical divergence as the frozen
  `SLIM_ANCESTRY_GENE_FLOW_SUMMARY` dry-run extractor.

CDMetaPOP reads the native:
- `summary_popAllTime.csv`
- `summary_classAllTime.csv`

and extracts population patch vectors plus `Alleles`, `He`, `Ho`.

## Authorization closure

To reduce unnecessary intermediate stages, R4.54 also closes execution
authorization if and only if all five real dry-runs pass.

On PASS:

- `exact_seed_injection_dry_run_validated = true`
- `readout_extraction_dry_run_validated = true`
- `scientific_execution_authorized = true`

Authorization applies only to:
- exact 20 R4.52 jobs;
- exact four frozen seeds/job;
- 80 scientific streams total;
- exact 10 R4.53 metric definitions.

R4.54 itself still has:

- historical scientific execution = false
- scientific evidence = false
- canonical state change = false
- Deep = OFF

Run:

```powershell
.\run_v0_6D1_R4_54.ps1
```

Next if SEALED:

`BUILD_R455_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_AND_EVIDENCE_CAPTURE`

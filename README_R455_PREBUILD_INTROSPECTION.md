# ARCANA — R4.55 Execution Source Introspection Helper

R4.54 and its R3.1 repair chain are now closed.

The next true stage is:

`v0.6D1-R4.55 — Non-Geonomics 80-Stream Scientific Execution & Evidence Capture`

However, R4.55 must not accidentally use the R4.54 disposable microbenchmark
configuration as a surrogate for the actual frozen historical jobs.

The current local repository contains the authoritative historical execution
machinery from R4.3/R4.7/R4.21/R4.22, including exact job contracts, adapter
profiles and prior repair history. Those sources are not all available in the
assistant runtime.

This helper therefore performs a **read-only local introspection** before the
R4.55 overlay is built.

It is deliberately:

- not R4.55;
- not scientific evidence;
- not an engine run;
- not a new seal.

## What it reads

It verifies:

- R4.54 integrated 32/32;
- R4.54 final seal 21/21;
- R4.54-R3 postrepair audit 12/12;
- R4.52 exact 20-job / 80-stream plan hash;
- R4.53 exact readout-registry hash;
- R4.2 exact 23-job matrix.

For every one of the 20 non-Geonomics jobs it reads:

`outputs/v0_6D1_R4_3/jobs/<JOB_ID>/JOB_CONTRACT.json`

and records:

- SHA256;
- top-level keys;
- seed/config/adapter/source/mapping/runtime/output-related contract fields.

It then inventories and hashes likely current execution sources under:

- `src/arcana_worldsim/scientific_engines/r43*.py`
- `r47*.py`
- `r4xx*.py` around R4.20–R4.22
- `benchmarks/r421/`
- `benchmarks/r422/`
- R4.3/R4.7/R4.21/R4.22 PowerShell bridges

For Python sources it extracts:

- relevant function signatures;
- bounded source excerpts;
- literal mappings such as `ADAPTER_PATHS` / `CANDIDATES`;
- CLI/`subprocess`/`runpy`/engine invocation lines.

## Why this is necessary

R4.3 governance requires historical jobs to preserve:

- raw engine evidence separately from normalized evidence;
- exact frozen job scope and seed ledger;
- explicit unit/semantic mapping;
- `ENGINE_EXECUTION_FAILURE` distinct from `ADAPTER_FAILURE`;
- no silent missing output;
- no canonical write.

R4.55 must reuse those actual historical mechanisms rather than reconstructing
a superficially runnable but scientifically different workload.

## Run

Extract into the project root, then:

```powershell
.\run_r455_execution_source_introspection.ps1
```

It writes:

`outputs/v0_6D1_R4_55_PREBUILD_INTROSPECTION/R4_55_EXECUTION_SOURCE_INTROSPECTION.json`

Then provide that JSON (or the console output plus the JSON file). The exact
R4.55 scientific execution overlay can then be generated from the local
authoritative invocation surfaces without guessing.

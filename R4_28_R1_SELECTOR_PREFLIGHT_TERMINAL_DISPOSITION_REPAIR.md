# v0.6D1-R4.28-R1 — Selector Preflight Terminal-Disposition Repair

## Finding
The initial R4.28 gate required all 44 hash-valid/static-valid canonical extractor sources to expose a non-empty exact selector inventory. The real root produced 38 ready records and 6 sources with no exact selector inventory. Treating those six as a process failure would pressure the pipeline to synthesize selector/column names, which is forbidden.

## Repair
R4.28-R1 distinguishes:
- `READY_EXACT_SCHEMA_INVENTORY_AND_PROTOCOL`
- `DEFERRED_NO_EXACT_SCHEMA_SELECTOR_INVENTORY`
- fail-closed `BLOCKED_*` integrity failures.

The stage may seal only when all 44 records are terminally disposed, no record is blocked, all selector auto-authorization remains zero, and target/J14 governance gates pass. A no-inventory source remains nonnumeric and nonadjudicative and is routed to R4.29 schema-authority or alternate canonical-source closure.

## Invariants
No numeric target execution. No selector synthesis. No fuzzy/synonym fallback. No engine execution. No readjudication. No canonical replay or parameter change. Deep biological coupling remains OFF.

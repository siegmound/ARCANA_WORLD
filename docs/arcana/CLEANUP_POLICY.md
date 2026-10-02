# Repository Cleanup Policy

## Allowed disposition

Use `KEEP_RUNTIME`, `KEEP_AUTHORITY`, `KEEP_REUSABLE`, `KEEP_REFERENCE`,
`DELETE_OBSOLETE`, `DELETE_SUPERSEDED`, `DELETE_TEMPORARY` or `REVIEW_UNKNOWN`.
Delete a file only after checking R6 source/runtime, tests, builders, current
manifest/authority references, hard-anchor/replay dependencies and unique
reusable mechanisms. `REVIEW_UNKNOWN` is protected.

Old material may be removed from the working tree when its historical role is
recorded in `LEGACY_ARCHIVE_MAP.md`; Git history is the archive. This does not
permit removing active test fixtures, source authority, provenance needed by
R6, hard anchors or non-reproducible evidence.

## Protected during PRE-B0

Keep `src/arcana_worldsim/r6/`, `tests/test_r6_*`, `scripts/r6_*`, current R6
contracts/manifests/authority, initial-world/T0 inputs, PRE_ORBDATA artifacts,
FEG/runtime package and builders/tests, S1B qualification provenance,
required vendored ShellSet source/patch/license, hard anchors and all unknowns.
Do not clean `outputs/`, `local_runs/` or `SIMULATION_RESULTS/` in this wave.

## Validation and audit trail

Use targeted reference searches and tests. Validate links in README and
`docs/arcana/`; run the complete R6-focused suite. Record starting and final
HEAD/worktree metrics, exact deletion families/counts, protected exceptions,
validation and residual unknowns in `C0_E_CLEANUP_LEDGER.md`. Do not commit or
push unless separately authorized.

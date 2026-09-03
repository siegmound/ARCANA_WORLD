# R3.8 diagnostic smoke audit

The diagnostic smoke exercises the restartable implementation without pretending to materialize the 150 Ma canonical checkpoint.

- 210→209 Ma: 8 biology cadences.
- R3.8 output matches the existing sealed R3.7I canonical smoke for total population, peak normalized VA, richness, component count and event counts.
- The 209 Ma full runtime state is serialized and reloaded.
- Serialization identity includes all four reduced genetic arrays.
- Both the in-memory 209→208 continuation and the reloaded 209→208 continuation are then executed.
- Full runtime-state comparison is exact within floating-point audit tolerance.

Machine-readable evidence: `outputs/v0_6D1_R3_8/R3_8_DIAGNOSTIC_SMOKE_AUDIT.json`.

This smoke does **not** authorize a canonical 150 Ma checkpoint. That requires the governed 210→150 + 150→149 local run.

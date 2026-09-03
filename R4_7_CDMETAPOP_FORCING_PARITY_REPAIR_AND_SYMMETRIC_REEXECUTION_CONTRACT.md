# ARCANA WorldSim v0.6D1-R4.7
## CDMetaPOP Dynamic-Forcing Parity Repair, Symmetric Five-Job Reexecution & Targeted Readjudication

R4.7 is authorized by the SEALED R4.6 finding that the R4.3 CDMetaPOP adapter was classified as NORMALIZABLE for `population_persistence` while only applying start-state support and migration, omitting the dynamic forcing that changed over the historical window.

R4.7 does **not** modify ARCANA canonical state, R3.11 parameters, the frozen R4.3 job list, the R4.4 seal, or the pinned CDMetaPOP source tree.

## Repair

A new adapter is created under `benchmarks/r47/`. The original R4.3 adapter and evidence remain untouched.

For H0 windows, dynamic `PatchVars.K` support is driven by the exogenous A1 `reference_population` ratio already present in the frozen R4.3 window descriptor. This is the specific causal forcing diagnosed by R4.6. The ARCANA comparison-target end population is forbidden from engine configuration.

For non-H0 CDMetaPOP windows, relative dynamic support is derived only from the already frozen R4.3 habitat and environment drivers.

The adapter uses CDMetaPOP's native `CDClimate` mechanism. It reuses the generic scenario's existing climate knots and applies a linearly interpolated relative K trajectory across those knots. `N0` remains a scalar start-state initialization and is never piped through climate knots, preventing later artificial re-injection of individuals.

## Symmetry

The common adapter repair is applied to all five frozen R4.3 CDMetaPOP jobs:

- J03 H0 deep-time background
- J06 H0 pre-CHA1
- J09 H0 post-CHA1 recovery
- J15 sapient 3 Ma -> 200 ka
- J20 sapient 200 ka -> 0

No result-selected J09-only repair is permitted.

## Readjudication

R4.7 normalizes the five new evidence bundles with the exact R4.3 within-engine normalization semantics and reuses the exact frozen R4.4 effect policy and metric candidates. Only evidence rows belonging to the five affected CDMetaPOP jobs are replaced in a new R4.7 matrix. The SEALED R4.4 matrix is preserved byte-for-byte.

R4.7 may SEALED whether the prior structural disagreement disappears or persists. A seal means the repair/reexecution/readjudication was governed and complete; it does not automatically authorize canonical replay or parameter change.

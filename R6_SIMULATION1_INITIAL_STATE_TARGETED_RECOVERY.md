# R6 Wave 3 — Simulation 1 Initial-State Targeted Recovery

**Status:** `BLOCKED_TARGETED_RECOVERY_REQUIRED`

**Audit baseline:** `main` / `origin/main` at `592b1651b405363373590092e133bd25569d99a5`

**Initial-world requirement:** `SIMULATION1_PANGAEA_EARTH_LIKE`

## Evidence-based boundary

Repository evidence supports **210.0 Ma as the current t0 candidate**: the A1 reference age coordinate starts at 210 Ma, and the R1–R3 rebaseline/replay configs use 210 Ma. The scoped audit did not find the original Simulation-1 bootstrap contract/config that binds those later artifacts to the original run. Therefore original Simulation-1 t0 is **210 Ma, strongly indicated but not yet authoritatively closed**, and R6 canonical t0 remains unbound. No alternative start time is selected.

`references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz` has SHA256 `9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f` and contains 11 frames at `[210, 180, 150, 140, 130, 120, 90, 66, 60, 30, 0]` Ma on a 90×180, 2° grid. It combines plate codes and land masks with climate, forage, population and carrying-capacity fields. It has no elevation/topography field and does not encode a verified plate-rotation/topology model. It is a **physical reference trajectory with an initial frame**, not an R6 canonical initializer; later frames are not reused.

R1 records `compatibility_radius_km=6371.0088`, which is a spatial compatibility parameter, not evidence for the physical radius of the simulated planet. A 210 Ma Deep reference and v0.5 calibration exist, but the complete canonical Deep/law/runtime/provenance closure is not established. CHA-1 and CHA-2 have scoped event contracts, not a complete R6 scheduler/runtime package. B6 D3 reports no successful paleohydrology snapshots; the P7S climate/hydrology authorities remain scoped and incomplete.

## Minimum targeted recovery

1. Recover the original Simulation-1 bootstrap contract/config or immutable run manifest and bind the exact start time, frame identities and initial-world semantics.
2. Recover the initial physical geography chain: native t0 elevation/topography, shoreline/sea datum and land/ocean semantics; identify the original ARCANA name/meaning of the Pangaea-like configuration. Do not infer terrestrial Pangaea or invent sub-grid detail.
3. Recover or explicitly classify all planetary assumptions (radius, gravity, rotation/day, axial/orbital, atmosphere, ocean/sea-level); do not promote R1 compatibility radius or substitute generic modern Earth constants.
4. Bind a valid climate/hydrology initializer or authorized generation chain from physical t0 inputs, with temporal/spatial support and uncertainty.
5. Close the physical/Deep law, parameter, runtime, event and provenance lineage; keep fundamental Deep physics distinct from later derived accessibility/resource fields.
6. Recover the original random/ensemble lineage or govern a new R6 policy, and bind each biological/human domain activation independently of global t0.

The JSON record classifies each item as data, semantic, authority, model or provenance recovery and defines acceptance evidence. Until these gaps close, the first R6 physical transition has no authorized start/end pair and Wave 4 must not execute.

## Disposition

No canonical initial-state package is created because that would falsely imply completeness. The A1 series is not replayed, no values are materialized, no provider is acquired, and no simulation or external engine is run. Current-state ledger, Scientific Authority Register, and protected execution indexes are unchanged.

**Decision:** `BLOCKED_SIMULATION1_INITIAL_STATE_AUTHORITY_AND_PHYSICAL_BOOTSTRAP_GAPS`

**Next action:** `R6_SIMULATION1_INITIAL_STATE_TARGETED_RECOVERY_PHYSICAL_GEOGRAPHY_AND_ORIGINAL_BOOTSTRAP_AUTHORITY`

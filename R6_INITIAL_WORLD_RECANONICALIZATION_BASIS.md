# R6 initial-world recanonicalization basis

This basis is the explicit route-B response to the missing formal Simulation1 provenance chain. It keeps three evidence classes separate; it does not reconstruct the old world bit-for-bit.

## 1. Recovered historical facts

- A directly inspectable ARCANA World Simulator v0.1 / World 1 / HYBRID-1 source package survives outside current Git history.
- Its README and source describe schematic Pangea at 210 Ma. Its config lists snapshots from 210 through 0 Ma, and its runner constructs a hard-coded HYBRID-1 scenario and exports a 210 Ma `plates.geojson` snapshot.
- This is Level A source evidence for the HYBRID-1 prototype itself. The preserved output is its direct-looking scenario snapshot. No inspected artifact formally equates that prototype with the original “Simulation1” identity.
- The v0.1 runner does not consume `FULL_A1_REFERENCE_210_0Ma.npz`; the A1 NPZ producer and original Simulation1 consumer remain unknown. A1's observed first age is 210 Ma on a 90x180, 2-degree grid, but its original role remains `REFERENCE_ONLY`.
- HYBRID-1 v0.1 records seed 917231. Its initial geometry is hard-coded; this does not establish a Simulation1 seed policy or authorize that seed for R6.
- HYBRID-1 v0.1 describes mountains as events without elevation. v0.3 later creates geological/elevation fields for a 0 Ma state. This does not establish the formal Simulation1 topography requirement.
- No fundamental Deep initial state/law was recovered from the early v0.1-v0.4 bootstrap sources. Later v0.5.5B/C Deep accessibility/resource fields are downstream and do not supply a Simulation1 initializer.
- The separately preserved old Git object-store backup has only two initial-import commits dated 2026-09-03; it contains no pre-import history.

Exact source/output paths, hashes, byte sizes, search scope, and the old Git commit IDs are recorded in `R6_WAVE3B_PREIMPORT_RECOVERY_ADJUDICATION.json`.

## 2. Authorial requirements

- R6 begins from an Earth-like early world with Pangaea/supercontinent-like initial geography.
- R6 preserves the broad initial-world concept associated with Simulation1, not necessarily its exact file or resulting trajectory.
- R6 evolves forward causally under canonical ARCANA physics and Deep, followed by later CHA-1/CHA-2 events and emergent R6 history.
- The old Simulation1 trajectory is not the R6 target.
- R5 is not an R6 runtime dependency.

## 3. New R6 scientific specification required

`R6_GLOBAL_T0 = 210 Ma` is now frozen as a **new R6 canonical design decision**. It is not a recovered original Simulation1 t0. This decision is supported by the authorial era requirement, the recovered early HYBRID-1 210 Ma schematic-Pangea source, A1's 210 Ma first timestamp, the later R1-R3 210 Ma starts, and the R6 world-history architecture.

The physical state at that time is not yet specified. The next governed contract must still define and justify:

- reproducible initial supercontinent geometry, plate semantics, grid/support, and source provenance;
- topography/elevation and sea-level datum;
- planetary constants (radius, gravity, rotation/day, tilt/orbit, atmosphere, ocean fraction);
- initial climate and hydrology methods;
- fundamental Deep initial state and laws;
- causal physical evolution method;
- seed/ensemble and runtime/dependency policy.

Do not promote A1 to numeric R6 initial-state authority or reuse its later trajectory. Do not treat the HYBRID-1 917231 seed or its schematic geometry as R6 authority without new adjudication. Do not claim recovered historical Simulation1 provenance.

**Next action:** `R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION_AND_SUPERCONTINENT_GENERATOR_CONTRACT`.

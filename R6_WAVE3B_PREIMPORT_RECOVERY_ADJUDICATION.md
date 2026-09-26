# R6 Wave 3B — Pre-import bootstrap recovery

**Decision:** `AUTHORIAL_RECANONICALIZATION_FREEZE_R6_GLOBAL_T0_210MA`

**Verdict:** `PASS_R6_WAVE3B_BOUNDED_RECOVERY__SIM1_PROVENANCE_UNRECOVERED__R6_T0_RECANONICALIZED`

**Selected route:** `R6_RECANONICALIZATION_REQUIRED`

## Recovery result

The bounded search found eight older ARCANA WorldSim copies (v0.1 through a v0.6.3 runpack) and one separate old Git object-store backup. The backup contains only two September 3, 2026 commits whose subjects are both “Initial ARCANA WorldSim repository import”; neither predates the import boundary.

A directly inspectable v0.1 World 1 / HYBRID-1 source package survives outside the current repository history. Its README says the initial schematic Pangea is at 210 Ma; `configs/hybrid1.yaml` gives ages 210, 180, 150, 120, 90, 60, 30, 0 Ma and seed 917231; `scenario_hybrid1.py` hard-codes the plate polygons and poses; and `run_hybrid1.py` invokes that scenario and exports the 210 Ma GeoJSON snapshot. These are Level A source artifacts for the HYBRID-1 prototype and its own direct output is preserved.

This is an important recovered precursor, but no inspected artifact identifies this source/output as the formal original “Simulation1” bootstrap. The v0.1 runner constructs its scenario in code and does not consume the A1 NPZ. It is not the producer of `FULL_A1_REFERENCE_210_0Ma.npz`. No exact Simulation1 contract, A1 producer, formal Simulation1 consumer, or execution manifest connecting the two identities was found. Therefore the exact Simulation1 pre-import provenance remains `IRRECOVERABLE_WITH_AVAILABLE_LOCAL_EVIDENCE`; the related HYBRID-1 prototype is recorded as Level A for itself and Level D as evidence of a Simulation1 relationship.

The v0.1 bootstrap represents Pangea schematically with hard-coded coordinates. The source does not establish a terrestrial reconstruction source, so this is not promoted to exact historical Pangaea semantics. v0.1 represents mountain building as events, not elevation; v0.3 introduces geological/elevation fields downstream and documents a present (0 Ma) geology product. This is evidence about that prototype lineage, not proof of the missing Simulation1 topography contract. No fundamental Deep initialization was found in v0.1-v0.4; later v0.5.5B/C Deep accessibility/resource fields are downstream and do not recover an initial Deep state. The 917231 value is recorded for HYBRID-1 only: its initial polygons are hard-coded, and no Simulation1 seed policy is established. The v0.1 great-circle default radius is a distance-calculation parameter, not a bound planetary constant.

## 210 Ma adjudication

Freeze `R6_GLOBAL_T0 = 210 Ma` as a **new R6 canonical design decision**, not as a recovered Simulation1 fact. The fixed authorial requirement asks for approximately the Simulation1 era; the early HYBRID-1 source explicitly starts with schematic Pangea at 210 Ma; A1 begins at 210 Ma; and later R1-R3 starts converge on 210 Ma under the existing world-history architecture. This convergence supports re-adopting the era while preserving the distinction between historical evidence and new R6 authority.

This does not freeze the physical initial state. `R6_PHYSICAL_T0`, exact supercontinent geometry, plate semantics, topography/sea level, planetary constants, initial climate/hydrology, Deep initialization, evolution method, and R6 seed/ensemble policy remain for a governed specification. A1 remains reference/design evidence only; neither it nor the later trajectory is promoted into R6 numeric state or history.

## Search and scope

Read-only search covered the current project parent, the eight named older ARCANA copies/runpack, and `_ARCANA_EXTERNAL_SOURCES`. Twelve compressed files surfaced. Both D3.3 result ZIPs were listed without extraction (40 and 43 entries); neither contains a Simulation1/bootstrap/initial-world/A1/210Ma/Pangaea/supercontinent filename. Remaining compressed files are provider/PRE5 payload archives, RNG fixtures, or tool dependencies, not plausible pre-import bootstrap sources. The old Git backup's refs and history were inspected directly; no old repository was switched or modified. No simulation, provider acquisition, external engine, climate, hydrology, biology, or numerical supercontinent design was run.

## Next action

`R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION_AND_SUPERCONTINENT_GENERATOR_CONTRACT`

That work must deliberately specify a reproducible R6 initial world under authorial constraints and currently validated methods. It must not claim bitwise recovery or reuse the old trajectory. R5 is not an R6 runtime dependency.

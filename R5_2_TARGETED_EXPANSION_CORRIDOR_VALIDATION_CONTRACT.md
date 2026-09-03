# ARCANA WorldSim v0.6D1-R5.2 — Targeted Expansion Corridor Validation

## Authority
Parent scientific state is **v0.6D1-R5.1 SEALED**. R5.2 consumes the twelve all-threshold cradle-opportunity families as ARCANA-defined origins and the SEALED J14 3 Ma→200 ka spatial replay as ARCANA-defined time-indexed occupancy targets.

RangeShiftR **3.0.1** is a governed external evidence engine. It does not select origins, targets, corridors, canonical states, or winners.

## R5.2-R1 source-initialisation repair
The first live R5.2 attempt completed all 80 planned RangeShiftR streams with exit code zero, but the evidence analyzer correctly blocked closure because no executable group's engine-year-0 occupancy reconstructed the frozen ARCANA source mask. The cause was isolated to the adapter initialisation setting: `SpDistFile="source.asc"` was supplied, while `Initialise(InitType=0, FreeType=1, InitDens=1)` selected RangeShiftR free initialisation of suitable habitat rather than initialisation from the loaded species-distribution map.

R5.2-R1 changes only this binding to `Initialise(InitType=1, SpType=0, InitDens=1)`. Origins, R5.1 families, J14 targets, dynamic habitat inputs, movement sensitivities, seeds, demography, dispersal and scientific readout rules are unchanged. The blocked 80-stream corpus is preserved as rejected repair history and must not be promoted or reinterpreted as corridor evidence. A new live execution is required.

Every new stream writes `initialization_mode=SPDIST_INITTYPE1_SPTYPE0`; analysis and `-Resume` both fail closed on pre-R1 evidence lacking this provenance. The mapping authority is the exact hash-bound, profile-filtered group `source.asc` (not the unfiltered R5.1 core); it must decode back to a subset of the corresponding R5.1/J14 origin. Before the full corpus, a one-engine-year RangeShiftR preflight must uniquely reconstruct that exact frozen source at engine year 0; otherwise R5.2-R1 stops before the expensive execution.

## Scientific question
Given the R5.1 robust origin families, do standardized RangeShiftR range-expansion challenges produce spatial occupancy that intersects the ARCANA J14 occupied-state sequence under two pre-frozen habitat interpretations?

This is a **descriptive connectivity test**, not a literal reconstruction of hominid travel speeds or observed historical migration routes.

## Time mapping
One RangeShiftR engine year is mapped to one ARCANA 20 kyr state transition. This is an indexed dynamic-landscape mapping only. It is explicitly **not** a claim that one RangeShiftR year represents 20,000 biological years.

## Space mapping
One ARCANA 90×180 grid cell is one normalized RangeShiftR cell at `Resolution=100` engine meters. The 100 m value is computational and preserves the R4.1 executable parameter ratio; it is not geodesic distance. Longitude is rolled separately for each family so the model's non-wrapped raster seam is moved away from the source core.

## Frozen sensitivity family
Habitat profiles:
1. `LAND_SUPPORT_UPPER_BOUND` — canonical land support only; a permissive topological upper bound.
2. `OCCUPIED_ENVELOPE_CORE_DIAGNOSTIC` — canonical land plus q05–q95 R5.1 occupied-environment ranges for temperature, aridity, total edible forage and wetland forage. This is a diagnostic occupied-envelope core, not a physiological tolerance claim.

Movement profiles:
- `D1_STANDARDIZED_1_CELL_CHARACTERISTIC`: transfer distance 100 engine units.
- `D2_STANDARDIZED_2_CELL_CHARACTERISTIC`: transfer distance 200 engine units.

Exact seeds per executable family×habitat group:
- `520201`
- `520202`

Each stream uses one RangeShiftR replicate, preserving the R4.1 single-replicate native population-output route rather than the historically problematic dedicated multi-replicate occupancy path.

## Reused governed R4.1 parameter path
- `Rmax=1.5`
- `EmigProb=0.1`
- `K=10`
- `DispersalKernel`
- native per-year population output (`x`, `y`, `NInd`)

No parameter is tuned to R5.2 results.

## Readout
For every exact stream, R5.2 records execution integrity and compares RangeShiftR occupied cells with the ARCANA J14 occupied cells at each mapped state. Derived readouts include target-intersection state fraction, final target intersection, target coverage and Jaccard overlap.

These numeric values **do not automatically cause scientific PASS/FAIL**. Stage PASS means the governed evidence corpus was executed and read correctly.

## Forbidden
- result-selected tuning;
- majority vote;
- one engine-selected corridor winner;
- RangeShiftR defining ARCANA geography or target states;
- automatic scientific truth from descriptive overlap values;
- canonical state rewrite;
- Deep biological coupling;
- literal interpretation of normalized engine time/space as historical migration rate/distance.

## Expected first-run scale
R5.1 supplies 12 robust families. With two habitat profiles, two movement profiles and two seeds, the maximum planned corpus is 24 groups / 96 single-replicate streams. A habitat-profile group whose frozen source has no applicable cell is retained as explicitly non-executable rather than repaired by modifying its source or habitat.

## Candidate closure
R5.2 remains a candidate after the live external-engine run. The evidence must be inspected before a final seal or before authorizing additional engines such as CDMetaPOP/NEMO/SLiM for later bottleneck/gene-flow/ancestry questions.

## R5.2 final evidence closure
R5.2 may be sealed once the governed RangeShiftR corpus is complete, source-bound, reproducible, and read without numeric truth adjudication. The final seal MUST preserve all 80 scientific streams and 40 fixed sensitivity records, verify the 100-file raw evidence corpus, recompute the source-binding preflight and evidence analysis, and preserve descriptive metric envelopes without selecting a corridor winner.

R5.2 closure does not require CDMetaPOP, NEMO, SLiM, Madingley, or a new Geonomics execution. Those engines answer downstream demographic, genetic, ancestry, or trophic questions rather than the R5.2 connectivity-evidence question. The next recommended scientific stage is corridor-conditioned demographic persistence and bottleneck validation; CDMetaPOP is the primary governed engine candidate for that distinct objective. No external engine may define ARCANA canonical geography or corridor truth.

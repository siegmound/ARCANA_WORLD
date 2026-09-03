# ARCANA WorldSim v0.6D1-R2.1
## Governed Speciation/Extinction Actuator & Internal Cadence Closure Contract

### Scope
R2.1 promotes the rebased 210→180 Ma Natural-Control runtime from a gate-diagnostic pilot to a runtime with production-capable taxonomic birth and ordinary-extinction actuators, while making biological integration independent of external macrostep chunking.

### Taxonomic birth authority
A daughter species may be created only when:
1. the extant species has at least two reproductive components;
2. every cross-component pair passes the D3.0C structural gate: biological time, intrinsic RI, trait distance and effective exchange;
3. the candidate lineage persists continuously for at least 1 Myr;
4. life-history-scaled branch and complement populations are viable;
5. founder effective-size proxy, standing additive variance, spatial support and non-collapse checks all pass.

There is no global speciation rate, radiation boost, lineage whitelist, author-selected winner, or Deep shortcut.

### Species identity vs root lineage
R2.1 separates immutable `root_species_id` from mutable `current_species_id`. Ecological metadata/trait scales remain inherited from the root lineage; taxonomic birth changes reproductive identity, not physical law or authorial niche parameters.

### Ordinary extinction authority
Ordinary extinction is a deterministic persistent-nonviability event. Low population alone is insufficient: the lineage must also exhibit ecological/range/density failure, satisfy minimum age, remain continuously stressed for 2 Myr, and continue declining relative to the stress episode start. Baselines are reset at taxonomic birth so a parent/daughter partition is never misread as extinction decline.

### Demographic fission
A demographic fragment is not a species. The persistent-vicariance actuator requires 2 Myr uninterrupted fragmentation and the D3 population/fraction floors. It is implemented and unit-tested but production-disabled in this two-keyframe R2.1 pilot pending R3 resolved barrier history.

### Internal cadence
The biological trajectory is advanced on a fixed 125 kyr cadence. Migration is subcycled at 62.5 kyr. External macrosteps are checkpoint/output grouping only and must be integer multiples of the internal cadence. Misaligned schedules fail closed.

### Library policy
Raster labeling, sparse graph components, and nearest-neighbour remap use SciPy. Custom code is restricted to ARCANA-specific state semantics and governance.

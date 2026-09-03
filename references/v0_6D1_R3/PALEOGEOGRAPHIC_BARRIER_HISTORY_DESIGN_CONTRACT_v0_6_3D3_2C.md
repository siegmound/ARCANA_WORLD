# v0.6.3D3.2C — Paleogeographic Barrier-History Resolution & Event Reconstruction

Status: **PASS_PALEOGEOGRAPHIC_BARRIER_HISTORY_RESOLUTION_EVENT_RECONSTRUCTION_CANDIDATE**

## Purpose

D3.2C replaces the temporally synchronous fractional-coast interpolation used between the sealed 60 Ma and 30 Ma physical frames with an endpoint-constrained event history. It changes only the timing of transition-cell accessibility. It does not alter the sealed endpoint macrogeometry, founder viability, speciation thresholds, genetic dynamics, or narrative locks.

## Physical authority

The only authoritative geographic states are the existing materialized A1/C2.2-rebased endpoints. Between 60 and 30 Ma:

- persistent land remains land;
- persistent ocean remains ocean;
- 499 cells transition land→ocean;
- 547 cells transition ocean→land;
- 1,046 transition cells receive derived event times;
- 86 plate/direction/time event clusters are exported for provenance.

Event clusters are **derived endpoint-constrained reconstructions**, not independent geological observations.

## Event ordering

Transition order is derived from distance to persistent same-plate land core. Emergence tends to occur core-near first; drowning tends to occur core-far first. Rank-balanced schedules are applied independently to emergence and drowning so the intermediate global land-area trajectory remains almost exactly consistent with endpoint interpolation.

Preferred candidate parameters:

- older endpoint: 60 Ma
- younger endpoint: 30 Ma
- event envelope: 5–95% of bracket
- transition width: 1 Myr
- integration timestep: 25 kyr
- critical-window verification: 12.5 kyr

## Biological coupling

The reconstructed land support enters the already-calibrated D3.2B effective-connectivity model. D3.2B remains authoritative for:

- founder-lineage viability;
- 0.075 life-history founder base;
- habitat barrier threshold 0.05;
- 2 Myr persistent-vicariance gate;
- ecological/genomic RI;
- resource-niche evolution;
- species-level ecological baselines.

D3.2C introduces no global speciation rate or radiation boost.

## Candidate outcome, +5 to +20 Myr post-CHA-1

- richness: 31 → 35
- demes: 116 → 117
- persistent-vicariance fissions: 1
- births: 4

Births:

- `RPT_012_D01` at +14.5 Myr
- `HSG_007_D01` at +15.5 Myr
- `LVF_009_D01` at +18.0 Myr
- `RPT_003_D01` at +19.0 Myr

Fission:

- `CAR_001_P001_F01` at +7.5 Myr, after 2 Myr continuous vicariance; demographic fragment only.

`RPT_004_D01`, present in D3.2B, is not born in D3.2C. Its isolated `RPT_004_P004` component remains reproductively isolated and genetically viable but has only 4 occupied cells at +20 Myr, below the 10-cell founder spatial-support requirement (21 cells at its D3.2B birth). It is therefore classified as provider-sensitive rather than robust.

## Resolution and sensitivity

Critical windows at 25 and 12.5 kyr reproduce all four birth checkpoints and the `CAR_001` fission checkpoint. Event-history sensitivity at 50 kyr across transition widths 0.5/1/2 Myr and event envelopes 2.5–97.5%, 5–95%, and 10–90% preserves final richness, deme count, birth identities, and fission identity.

Continuous trait/RI microstate values remain diagnostic and are not sealed to decimal precision.

## Scope locks

Deep adaptation, dragon selection, sapience, civilization, background species extinction, species fusion, author-selected winners, global radiation boost, and global speciation rate remain OFF.

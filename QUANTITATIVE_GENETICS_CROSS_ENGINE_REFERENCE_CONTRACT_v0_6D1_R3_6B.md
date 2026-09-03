# v0.6D1-R3.6B — Quantitative-Genetics Cross-Engine Reference Contract

## Status
`CANDIDATE — QTL ENSEMBLE AND REFERENCE SUITE IMPLEMENTED; EXTERNAL NEMO EXECUTION PENDING`

## Purpose
R3.6B creates an independent quantitative-genetics reference layer before any change to D3.3A `mu`, `b`, `q*=0.045`, moment mixing, or the numerical ceiling.

ARCANA WorldSim remains the sole canonical state/species/clock authority. NEMO is evidence only.

## Invariants
- no external engine may write canonical ARCANA state;
- no NEMO result may define ARCANA species identity or speciation;
- `q*=0.045` is fixed for this stage;
- thermal/aridity are benchmarked in normalized trait space with scale 1, making `q == V_A` numerically;
- every stochastic realization has explicit seed, replicate id and semantic SHA-256;
- ensemble comparison is distributional, not bit-identical;
- D3.0C, D3.2B/C, D3.3A and R3.3–R3.5 scientific authorities remain unchanged.

## Canonical controlled scenarios
1. `B0_EQUILIBRIUM_NO_FLOW`: no-admixture control.
2. `B1_TWO_DEME_ADMIXTURE`: persistent exchange between genetically differentiated demes.
3. `B2_FRAGMENTATION_RECONNECTION`: connected -> fragmented -> reconnected phases.
4. `B3_HIGH_ADMIXTURE_STRESS`: larger mean separation and stronger exchange to expose between-deme variance injection.

These are reference microbenchmarks, not reconstructed World-1 history.

## Promotion gate
R3.6B evidence cannot modify ARCANA. It may only feed R3.6C, which must compare:

`ARCANA current 125 kyr <-> ARCANA 5x25 kyr <-> NEMO 2.4.2 ensemble`

Only after R3.6C may a governed calibration candidate be proposed.

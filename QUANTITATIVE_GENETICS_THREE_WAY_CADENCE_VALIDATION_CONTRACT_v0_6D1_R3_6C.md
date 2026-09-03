# v0.6D1-R3.6C — Quantitative-Genetics Three-Way Cadence Validation Contract

## Scope
R3.6C compares, without changing canonical state or D3 parameters:

1. ARCANA current finite biology step: `1 × 125 kyr`;
2. ARCANA quantitative-genetic cadence probe: `5 × 25 kyr`;
3. NEMO 2.4.2 genetically explicit reference, with dispersal cadence normalized to per-generation probabilities.

## Hard locks
- `mu = 0.002 q/Myr` unchanged.
- `b = 0.9876543209876544 /Myr/q` unchanged.
- `q* = sqrt(mu/b) = 0.045` unchanged.
- no change to speciation, RI, fission, coalescence, paleogeography, barrier coupling, current-species gene-flow identity or canonical ceiling.
- external engines cannot write canonical ARCANA state and cannot automatically calibrate parameters.

## Cadence normalization
ARCANA R3 applies a finite exchange operator at biology cadence 125 kyr. NEMO applies dispersal each generation. Therefore an ARCANA finite-step exchange matrix MUST NOT be copied numerically into NEMO as a per-generation matrix.

For a row-stochastic finite-step transition `D_125`, an exact continuous-time embeddable mapping is:

`Q = log(D_125) / 125000`

and for generation time `g` years:

`D_gen = exp(Q g)`.

The implementation uses mature SciPy `logm`/`expm` and rejects non-embeddable finite-step matrices rather than silently projecting them.

For the ARCANA pairwise moment operator, which is not a Markov matrix, symmetric edge cadence normalization is diagnostic:

`g_25 = 1 - (1 - g_125)^(1/5)`.

Naively repeating `g_125` five times is retained only as a diagnostic counterexample and is never authorized as the 25-kyr mapping.

## Cross-engine comparison quantity
Absolute drift cannot be compared directly between WorldSim abundance units and a tractable finite NEMO individual population. Therefore primary inference uses matched-control excess quantities, especially:

`Delta VA_admixture = VA_flow - VA_no_flow`

with NEMO population-size sensitivity. NEMO remains an independent reference oracle, not an ARCANA population-unit reinterpretation.

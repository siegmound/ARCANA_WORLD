# v0.6D1-R3.7F — World-1 Stress-Window Adaptive Genetic Shadow Replay Contract

## Purpose
R3.7F extends the validated R3.7E short 210→205 Ma shadow replay to the governed 210→188 Ma stress window. The endpoint is selected *a priori* because the historical R3.5 q=0.08 run first entered homeostasis clipping at approximately 191.25 Ma. The new window therefore crosses that failure onset by about 3 Myr.

## Scientific question
Does the segregation-aware reduced genetic state remain below the existing q=0.08 additive-variance ceiling through a window where the legacy whole-trait admixture operator is independently known to clip, and is that conclusion invariant across the R3.7D high-N shadow K envelope?

## Hard locks
R3.7F does not change `mu=0.002/Myr`, `b=0.9876543209876544/Myr/q`, `q*=0.045`, q ceiling 0.08, migration/RI/speciation authority, fission/coalescence, paleogeography, climate, or trait-response dynamics. `K_LOW=37.614`, `K_CENTER=38.470`, and `K_HIGH=41.002` remain shadow sensitivity variants only. Recombination r=0.5 remains reference shadow architecture and is not promoted to a World-1 constant.

## Governed full window
- start: 210 Ma
- end: 188 Ma
- biology cadence: 125 kyr
- expected biology steps: 176

## Gate
The full replay is a stress PASS only if:
1. bit-exact canonical parity is preserved;
2. the legacy R3.5 branch actually reproduces at least one q=0.08 clipping step inside the governed window;
3. every segregation-aware shadow K variant has zero q-ceiling contacts;
4. all K variants agree qualitatively on ceiling state.

No arbitrary tolerance is imposed on S, ancestry/LD, or adaptive-coordinate spread. Those spreads are reported quantitatively and reviewed rather than calibrated away.

## Governance
A PASS authorizes only a production-binding readiness review. It does not itself authorize canonical writes, a scalar production K, a direct WorldSim-N to NEMO-N mapping, a mu/b/ceiling change, or a production runtime replacement.

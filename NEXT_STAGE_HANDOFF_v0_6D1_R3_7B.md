# Next-stage handoff after v0.6D1-R3.7B

## What R3.7B proves
The reduced neutral state `(VA_within, S)` is sufficient to reproduce the NEMO 2.4.2 B2 drift/connectivity lifecycle at the tested scale without fitting a new coefficient.

The evidence is strongest for the central claim:
- connected migration suppresses pairwise divergence;
- isolation lets finite-N drift grow `S`;
- reconnection contracts `S` again;
- the same D3.3A drift authority predicts both VA loss and expected S growth.

## What remains blocked
Directional selection.

B2 had no selection, so the static 64-QTL `K_eff` range is not enough to authorize production adaptive-coordinate evolution.

## Natural next stage
`v0.6D1-R3.7C — NEMO Directional-Selection Participation & Adaptive-Segregation Calibration`

The stage should construct an independent NEMO selection experiment with matched neutral controls and infer whether:
1. one scalar `K_eff` is stable across N, trait axis and selection strength;
2. `K_eff` needs trait-specific or state-dependent structure;
3. adaptive divergence and reconnection can be represented by the current latent-coordinate decomposition.

Only after R3.7C may a short selected World-1 shadow replay be considered for promotion toward runtime binding.

Do not modify `mu`, `b`, `q*`, ceiling, barriers, speciation authority, fission or coalescence while calibrating selection participation.

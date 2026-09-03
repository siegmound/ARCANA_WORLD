# v0.6D1-R3.4 — Admixture-Variance Headroom & Species-Bound Gene Flow Contract

## Purpose
R3.4 closes two long-horizon issues found after the R3.3 210→150 Ma replay:
1. `q=V_A/scale^2` used the old D3.3A ceiling 0.05 as an active attractor in ~13% of reservoirs.
2. the rebased runtime retained gene-flow geometry by immutable root lineage even after current-species divergence.

## Preserved authorities
No change to mutation supply or nonlinear homeostasis:
- `mu = 0.002 q/Myr`
- `b = 0.9876543209876544 / Myr / q`
- no-flow equilibrium `q* = 0.045`
- D3.3A moment-conserving gene-flow mixer and 45% aggregate exchange cap remain unchanged.

## Headroom calibration
A frozen 150 Ma R3.3 endpoint diagnostic was run with current-species-bound gene flow and ceilings 0.05, 0.06, 0.075, 0.08, 0.10.
- 0.05 remains strongly binding.
- 0.06 remains binding.
- 0.075 is almost non-binding but still has one reservoir at >=99% of the cap after 20 Myr.
- 0.08 and 0.10 produce the same natural max `q = 0.07435062666931849` after 20 Myr; 0.08 has zero reservoirs at >=99% of cap.

Therefore World 1 R3.4 uses candidate safety ceiling:

`q_ceiling = 0.08`

This changes only headroom. It does not move the no-flow equilibrium.

## Gene-flow identity
`root_species` is immutable provenance/metadata authority only.
`current_species` is reproductive identity authority.

Gene flow, contact matrices, RI/isolation pair-state updates and trait-distance pair metrics are current-species-bound. A parent and daughter species sharing a root lineage do not continue moment mixing after speciation.

## Promotion rule
R3.4 itself does not promote 150 Ma. The 210→150 Ma Natural-Control replay must be rerun from the R1 common state. Promotion requires:
- no `q > 0.08`;
- negligible contact with the 0.08 ceiling;
- stable demography/speciation/fission/coalescence;
- A1 population envelope preserved.

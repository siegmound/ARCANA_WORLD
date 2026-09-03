# v0.6D1-R3.1 — Audit of the first 210→150 Ma R3 long run

## Verdict

`REJECT_R3_210_150_AS_CONTINUATION_CHECKPOINT__REPAIR_REQUIRED`

The long run completed numerically, but it exposed a semantic regression in the rebased variance/gene-flow ordering. The endpoint must **not** be used as the 150 Ma parent for the next segment.

## Observed long-run endpoint

- 210→150 Ma completed in ~1101.95 s on the user's local workstation.
- total population: 1823.1595077 → 1940.1145193 WorldSim units.
- species: 120 → 137.
- demographic components: 133 → 476.
- events: 432 support-loss remaps, 343 deme fissions, 17 speciation births, 0 ordinary extinctions.

These event counts are evidence only because the variance/gene-flow bug occurs upstream of later trait divergence, RI, fission geometry and speciation timing.

## Blocking regression

The SEALED/preferred D3.3A order is:

1. compute gene-flow/contact geometry on the pre-selection state;
2. update trait means by selection;
3. mix trait first/second moments by gene flow with the D3 aggregate exchange cap;
4. apply the non-flow Riccati variance homeostasis as the final variance operator.

R3 instead executed:

`selection -> Riccati homeostasis -> gene-flow moment mixing`

and used a simplified rebased gene-flow mixer without the D3.3A aggregate `maximum_total_exchange_fraction_per_deme = 0.45` safeguard.

Consequences measured in the uploaded endpoint:

- normalized q median ≈ 0.04480;
- normalized q max ≈ 0.05348;
- 175 trait reservoirs exceed q=0.05 across 139 components;
- ≈13.3% of trait reservoirs are already at/above 99% of the nominal hard ceiling;
- the simplified final-state exchange geometry can exceed the inherited 45% aggregate exchange guard in tiny demes.

This is not an acceptable continuation state.

## Additional stress evidence (not yet a blocker by itself)

The rejected run also showed:

- 343 fissions over 60 Myr across 80/120 ancestral root lineages;
- large fission bursts (48 at 203.5 Ma, 45 at 192.5 Ma);
- 17 births, with 10/17 having minimum trait distance ≤1.10 and 5/17 ≤1.05;
- 15 endpoint components below 0.01 population units and 108 below 0.05.

After the variance repair, the full run must be repeated before deciding whether these patterns are robust natural history or cascade artifacts.

## R3.1 repair

R3.1 reuses the existing D3.3A `additive_variance.py` source byte-for-byte (SHA-256 `3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21`) and restores the D3 ordering and exchange cap. No new variance equation is introduced.

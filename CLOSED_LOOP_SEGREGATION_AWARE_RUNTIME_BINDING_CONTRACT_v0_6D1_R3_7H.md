# v0.6D1-R3.7H — Closed-Loop Segregation-Aware Runtime Binding Contract

## Purpose
R3.7G demonstrated over 210→150 Ma that the segregation-aware genetic state removes the historical whole-trait admixture VA clipping while preserving the parent world trajectory in shadow mode. R3.7H tests the remaining feedback that shadow mode intentionally suppressed: repaired within-deme VA is now returned to the runtime and is consumed by the next `select_traits` call.

R3.7H is a **production-binding candidate**, not yet production authority.

## Closed-loop state
For each independent K branch the canonical candidate VA is `VA_within`. The reduced state also carries:
- transient signed ancestry/LD covariance `C`;
- neutral segregation potential `S_neutral`;
- adaptive coordinate `h`;
- total segregation potential `S_total = S_neutral + (h_i-h_j)^2`.

Directional trait response is still decided by the unchanged R3.4 selection operator. R3.7H only maps the realized trait displacement into `h`, using the R3.7D K envelope.

## Gene flow binding
Mean migration and the 45% aggregate exchange cap remain R3.4/D3.3A authority. Persistent within-deme VA is updated by the R3.7 segregation-aware operator. The legacy whole-trait second-moment variance is evaluated only as a mean-transport closure oracle and is never fed back.

## Nonflow variance
Mutation supply, selection depletion, drift and nonlinear Riccati homeostasis remain the exact D3.3A operator with unchanged parameters:
- `mu = 0.002 / Myr`;
- `b = 0.9876543209876544 / Myr / q`;
- normalized ceiling `q = 0.08`.

Expected VA removed by the already-authorized D3.3A drift term is transferred to neutral segregation potential as in R3.7A/B.

## Coalescence repair
Legacy R3.3/R3.4 coalescence pooled whole-trait second moments. That would reintroduce the same structural admixture error during deme merging. R3.7H therefore preserves the exact R3.3 reconnection trigger, deterministic survivor identity, population/trait first-moment pooling, pair-state merge and bookkeeping resets, but replaces only the VA pooling semantics with the R3.7A segregation-aware barycentric pooling.

Fission, extinction and speciation triggers remain parent authority. Fission clones the reduced genetic state; extinction removes the same deme; speciation changes reproductive identity without resetting genetics.

## K-envelope semantics
Three independent closed-loop replays are mandatory:
- `K_LOW = 37.614` — uncertainty sentinel;
- `K_CENTER = 38.470` — nominal candidate branch, not a physical World-1 constant;
- `K_HIGH = 41.002` — uncertainty sentinel.

The full 210→150 validation reports divergence in population, event history, species/components, VA, S and h. No new arbitrary tolerance is fitted to those outputs. A run may pass the numerical closed-loop gate while production promotion remains review-required.

## Recombination parameter
`r=0.5` remains a reference architecture for the transient ancestry/LD diagnostic reservoir. It is not promoted to a World-1 constant. Persistent `VA_within` and `S` evolution do not consume `C`, so canonical candidate dynamics are not calibrated by this recombination value.

## Full gate
Each branch must:
1. execute exactly 480 biology steps over 210→150 Ma;
2. remain finite and internally state-consistent;
3. retain the existing q=0.08 hard ceiling with zero clipping contacts;
4. preserve mean-migration closure against R3.4 authority;
5. use segregation-aware coalescence whenever reconnection actually merges demes.

The aggregate gate additionally requires all three branches to remain valid and qualitatively coherent with respect to ceiling contact. Event-history and macrostate differences are reported for promotion review rather than hidden behind a fitted threshold.

## Governance
Until the full three-branch closed-loop evidence is executed and reviewed:
- `production_runtime_replacement_authorized = false`
- `scalar_K_eff_production_authorized = false`
- `mu_b_or_ceiling_change_authorized = false`

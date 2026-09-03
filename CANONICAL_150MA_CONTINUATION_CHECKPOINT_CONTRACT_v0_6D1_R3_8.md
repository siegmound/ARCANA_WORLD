# v0.6D1-R3.8 — Canonical 150 Ma Continuation Checkpoint Contract

## Purpose
Materialize the first restartable post-promotion World-1 H0 checkpoint at exactly 150 Ma. R3.7I remains the production authority; R3.8 adds serialization/restart mechanics and does not recalibrate biology.

## Canonical checkpoint contents
The checkpoint is a JSON+NPZ pair. It must contain every state variable capable of changing a future replay:

- component IDs, root/current species identity, guilds;
- full spatial population tensor, trait means, within-deme VA, generation time;
- species registry and descendant counters;
- current paleogeographic accessibility mask and demographic baselines;
- pairwise intrinsic-RI and isolation-clock state;
- extinction, founder, vicariance and reconnection persistence state;
- event/snapshot history required for cumulative diagnostics;
- full reduced genetic state:
  - `VA_within`;
  - ancestry/LD covariance;
  - neutral segregation-potential matrix `S_neutral`;
  - adaptive coordinate `h`;
- topology-remap and gene-flow closure diagnostics;
- exact R3.7I promotion-seal SHA-256.

No hidden pre-150 genomic information may be invented.

## Equivalence gates
A canonical checkpoint is authorized only if all gates pass:

1. R3.8 direct 210→150 exposed state matches the sealed R3.7H/R3.7I K_CENTER reference (hash bound by the R3.7I promotion seal).
2. Saving and reloading the 150 Ma checkpoint preserves the full R3.8 runtime state.
3. In-memory continuation 150→149 and reloaded-checkpoint continuation 150→149 are identical, including full reduced genetic matrices and lifecycle registries.
4. Exactly 480 biology steps occur before the checkpoint and exactly 8 after it in each continuation branch.

The R3.7H payload did not expose all hidden restart state (notably complete `S`, ancestry/LD, `h`, raw pair-state dictionaries and lifecycle timers). Therefore gate 1 checks the state R3.7H actually exposed; gates 2–3 establish exact identity for the newly explicit hidden state.

## Authority retained
R3.8 changes no scientific constant or law. The following remain exactly as sealed before R3.8:

- R3.7I segregation-aware production binding;
- `K_CENTER=38.470` only as an operational reduced-order coordinate reference;
- LOW/HIGH as release sentinels;
- D3.3A `mu`, `b`, drift and ceiling;
- migration, selection, RI/speciation, fission/extinction and paleogeography;
- H0 Deep biological coupling OFF.

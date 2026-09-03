# v0.6D1-R3.7A — Segregation-Potential Initialization, Evolution & Deme-Lifecycle Contract

## Purpose
Close the lifecycle semantics of the R3.7 reduced genetic state without yet binding it to the World-1 production replay.

State per trait:
- `VA_within[deme]`: persistent within-deme genic additive variance;
- `C_ancestry_LD[deme]`: signed transient ancestry/LD covariance;
- `S_neutral[i,j]`: neutral segregation-potential distance;
- `h[deme]`: trait-aligned adaptive genetic coordinate;
- `S_total[i,j] = S_neutral[i,j] + (h_i-h_j)^2`.

## 210 Ma initialization
Use minimum information only. Within each `current_species`, authoritative pairwise segregation potential starts at zero. Cross-species entries are zero placeholders and explicitly non-authoritative for reproductive mixing. No hidden pre-210 allele-frequency divergence is invented.

## Directional selection
R3.7A does not decide the phenotypic response. It consumes the response already produced by ARCANA selection authority. The minimum-distance aligned polygenic mapping is

`dh = dz / sqrt(2 K_eff)`.

`K_eff` is an effective participation number, not a literal locus count and not a production constant in R3.7A. Parent NEMO/QTL evidence places it in ~46.65–63.50 for the 64-QTL reference architecture; B2 calibration remains required before production binding.

## Drift
Reuse the exact D3.3A drift authority:

`R_i = exp[-dt/(2 Ne_i g_i)]`.

Expected within-deme VA loss is

`L_i = VA_i (1-R_i)`.

For two independently drifting demes, neutral segregation potential increases by

`Delta S_ij = L_i + L_j`.

No new drift rate is introduced.

## Mutation
D3.3A `mu` is a within-deme standing-variance supply, not a directional allele-frequency mutation matrix. Therefore R3.7A assigns zero deterministic mutation-driven displacement in `S`. Finite-population divergence is represented by the governed drift transfer.

## Migration/reconnection
Migration transforms the reduced Euclidean distance state using the same transition matrix that mixes trait means. The R3.7 Gram-matrix identity remains authoritative:

`B = -1/2 H S H`, `B' = P B P^T`, then reconstruct `S'` from `B'`.

## Fission
At the instant of fission the daughter is an exact genetic clone of the parent reduced state:
- parent–daughter `S=0`;
- identical distances to all pre-existing demes;
- identical `VA_within`, `C_ancestry_LD` and `h`.
Subsequent divergence is generated only by governed selection/drift/migration.

## Coalescence
Same-species coalescence uses population-weighted barycentric pooling. Persistent VA receives the exact R3.7 genic segregation contribution; the residual whole-trait mixture is kept in the signed ancestry/LD reservoir. External neutral distances use the squared-Euclidean barycenter identity.

## Speciation
Speciation changes reproductive identity only. It does not reset the numerical genetic state. Cross-species gene flow and coalescence remain prohibited by existing `current_species` authority.

## Remap and extinction
A pure paleogeographic support-loss remap preserves genetic state. Deme removal deletes the corresponding reduced-state row/column.

## Governance
This stage does **not** authorize:
- production runtime binding;
- a production `K_eff`;
- changes to `mu`, `b`, `q*` or the ceiling;
- changes to speciation, fission/coalescence, paleogeography, barriers or migration geometry;
- automatic calibration from NEMO.

The external B2 NEMO 2.4.2 chain is required before production selection/divergence mapping is promoted.

# v0.6D1-R3.7 — Segregation-Aware Admixture Variance State & Reduced-Order Genetic Mixing Repair

## Status
`PASS_SEGREGATION_AWARE_OPERATOR_REFERENCE_CLOSURE__PRODUCTION_STATE_EVOLUTION_PENDING`

R3.7 repairs the *representation* of admixture variance exposed by R3.6E. It does not change the World-1 production replay yet.

## Locked parent authorities
R3.7 does **not** change:
- D3.3A `mu = 0.002 / Myr`;
- D3.3A `b = 0.9876543209876544 / Myr / q`;
- `q* = 0.045`;
- the current hard VA ceiling;
- species-bound gene flow;
- the 45% aggregate exchange cap;
- speciation / RI / isolation / fission / coalescence authorities;
- paleogeography or climate.

## Problem proved by R3.6E
The legacy moment operator assigns the complete whole-trait mixture term

`Var_w(z_source means)`

to persistent within-deme additive variance. For the 64-QTL NEMO references this exceeds the exact genic segregation increment by about 114–127x.

## New reduced-order state
For each deme and trait:

1. `VA_within` — persistent within-deme genic additive variance.
2. `C_ancestry_LD` — signed transient cross-locus / ancestry covariance contribution.

For each deme pair and trait:

3. `S_ij` — segregation potential:

`S_ij = 2 * sum_l a_l^2 (p_il - p_jl)^2`

`S` has units of trait variance and is a squared-Euclidean distance matrix in latent allele-frequency/effect space.

## Exact genic mixing identity
If destination deme `i` is formed from source weights `w_j`, then:

`VA_within_i' = sum_j w_j VA_within_j + 0.5 * sum_j sum_k w_j w_k S_jk`

For two sources with weights `(1-m,m)`:

`Delta VA_genic = m(1-m) S_12`

This is the exact additive-diallelic QTL allele-frequency mixing result and contains no global suppression scalar.

## Mean transport authority
The transition weights are derived from the same D3.3A symmetric pair-exchange mass, harmonic abundance factor and 45% cap. Therefore:

`z' = P z`

has the same mean-gene-flow semantics as the parent operator. R3.7 remains current-species-bound.

## Transient ancestry / LD covariance
The whole-trait mean-mixture contribution is

`B_i = sum_j w_j z_j^2 - (sum_j w_j z_j)^2`.

The part not represented by genic segregation is retained separately:

`Delta C_i = B_i - Delta VA_genic_i`.

Before recombination:

`VA_within' + C_pre`

exactly reproduces the parent total mixture second moment. Thus R3.7 changes the biological partition, not the instantaneous mean or mixture accounting.

`C` is signed because linkage disequilibrium/cross-locus covariance may increase or decrease total additive-genetic variance.

## Recombination
The reference NEMO experiment uses free recombination (`r=0.5`). Existing ancestry covariance retains

`(1-r)^g`

after `g` generations.

For covariance injected uniformly through an interval, R3.7 uses the exact continuous-injection average retention

`[1-exp(-lambda g)]/(lambda g)`, where `lambda=-ln(1-r)`.

For 125 kyr and a 5-year generation at `r=0.5`, only ~5.77e-5 of uniformly injected transient covariance survives to the interval endpoint.

This `r=0.5` is a **reference-architecture parameter**, not a World-1 production constant.

## Evolution of S under migration
Because `S` is a squared-Euclidean latent genetic distance, migration can update it without reconstructing loci:

1. recover centered Gram matrix `B = -1/2 H S H`;
2. apply the same transition `B' = P B P^T`;
3. recover pairwise squared distances from `B'`.

This is exact for linear allele-frequency mixing.

## Reference closure
Using the real R3.6D QTL realizations:
- B1 thermal/aridity and C3 thermal/aridity close against direct QTL allele-frequency mixing;
- maximum relative error versus the R3.6E analytic polygenic reference: ~1.33e-10;
- the legacy operator is still 114.48–126.996x above the repaired genic increment;
- pre-recombination total-variance closure is at floating-point precision;
- population-weighted first-moment closure is at floating-point precision;
- transient ancestry retention at the 125-kyr endpoint is ~5.77e-5 under the free-recombination reference.

## What R3.7 does NOT authorize
R3.7 does not yet define how `S_ij` is initialized/evolved in the full 210→150 Ma state under:
- directional adaptation;
- mutation/drift;
- fission;
- coalescence;
- speciation;
- new deme creation/remapping.

Therefore the repaired operator is not yet bound into the production R3.5 replay.

## Next required stage
`v0.6D1-R3.7A — Segregation-Potential Initialization, Evolution & Deme-Lifecycle Calibration`

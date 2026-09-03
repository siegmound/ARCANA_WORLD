# v0.6D1-R3.7B — Neutral Reduced Genetic Lifecycle Contract

## Scope
R3.7B closes the neutral `VA_within + S` frequency-state lifecycle against the real NEMO 2.4.2 B2 connected→fragmented→reconnected chains. It introduces no new fitted biological rate and does not yet authorize directional-selection `K_eff` or production runtime replacement.

## State
For each deme `i` and trait `t`:
- `V_i`: within-deme genic additive variance;
- `S_ij`: pairwise segregation potential, a squared-Euclidean distance in latent additive allele-frequency/effect space.

## Exact generation-scale neutral recursion
Let `P` be the row-stochastic migration/parent-source transition for one generation.

### Migration
The exact within-deme genic mixture is

`V_i^M = sum_j P_ij V_j + 1/2 sum_jk P_ij P_ik S_jk`.

The pairwise latent distance is transformed exactly by the R3.7 Gram-matrix operator:

`S^M = T_P(S)`.

### Wright-Fisher drift
For diploid effective size `N_i`, one-generation genic retention is

`R_i = 1 - 1/(2 N_i)`.

The expected lost genic variance is

`L_i = V_i^M/(2 N_i)`.

Then

`V_i' = V_i^M - L_i`

and

`S_ij' = S_ij^M + L_i + L_j`.

The same variance removed by finite-N sampling is therefore transferred into expected between-deme squared displacement. No new drift coefficient exists.

## Recombination
Recombination does not change allele frequencies and therefore does not directly change the genic frequency-state pair `(V,S)`. It acts on the distinct `ancestry/LD covariance` reservoir introduced in R3.7.

## Relation to D3.3A
At WorldSim macro-interval scale, the already-sealed D3.3A drift authority remains

`R_i(dt) = exp[-dt/(2 N_e,i g_i)]`.

R3.7B does not replace that authority. The exact one-generation recursion is used for the NEMO B2 oracle because B2 is explicitly generation-scale.

## Governance
- new drift coefficient: NO
- new mutation coefficient: NO
- `mu`, `b`, `q*`, VA ceiling changes: NO
- automatic calibration from NEMO: NO
- canonical write: NO
- directional-selection `K_eff`: NOT AUTHORIZED BY THIS CONTRACT

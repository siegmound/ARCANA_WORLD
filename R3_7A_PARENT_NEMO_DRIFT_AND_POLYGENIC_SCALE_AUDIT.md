# R3.7A — Parent NEMO Drift & Polygenic-Scale Audit

The real R3.6D NEMO 2.4.2 evidence embedded in the parent package was reused before requesting new B2 runs.

## Drift control
B0 no-flow provides an independent finite-population drift check. R3.7A predicts pairwise segregation divergence by transferring the D3.3A expected loss of within-deme VA:

`Delta S_ij = VA_i(1-R_i) + VA_j(1-R_j)`, with `R=exp[-dt/(2Ne g)]`.

Across 8 parent reference rows:
- median observed/predicted ≈ 1.1044;
- mean ≈ 1.1085;
- maximum absolute fractional deviation ≈ 24.46%.

With only two finite-N replicates this supports reuse of the existing D3.3A drift authority; no new drift coefficient is justified.

## Effective polygenic participation
Using the actual B1/C3 64-QTL reference realizations, the minimum-distance directional mapping implies

`K_eff = (Delta z)^2 / (2 S)`.

Observed reference range:
- minimum ≈ 46.6464;
- median ≈ 59.6152;
- maximum ≈ 63.4982;
- literal QTL count = 64.

Therefore `K_eff` is an effective participation number, not automatically equal to the number of loci. R3.7A does not seal a World-1 production value.

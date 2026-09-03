# R3.7 Reduced-Order Genetic State Audit

## Representation audit
PASS — persistent genic variance, transient ancestry/LD covariance and pairwise segregation potential are separate state variables.

## No arbitrary suppression scalar
PASS — persistent admixture variance is determined by `S_ij`, not by multiplying the legacy whole-trait variance by a fitted global factor.

## Exact-QTL closure
PASS — on the R3.6D 64-QTL references, the repaired within-deme variance matches direct allele-frequency mixing to numerical precision.

## Mean-flow compatibility
PASS — mean transition is constructed from the unchanged D3.3A exchange-mass/harmonic-population/45%-cap semantics and current-species identity.

## Moment accounting
PASS — before recombination, `VA_within + C_ancestry_LD` reproduces the legacy instantaneous total mixture variance.

## Recombination semantics
PASS for the NEMO reference architecture — `r=0.5` is explicit and used only to validate the free-recombination benchmark. Production recombination architecture remains uncalibrated.

## Pairwise-state geometry
PASS — `S` is required to be squared-Euclidean and is updated by Gram transformation under migration. Non-Euclidean states fail closed.

## Production authority
NOT GRANTED — full-history initialization/evolution and deme lifecycle rules for `S` remain pending R3.7A.

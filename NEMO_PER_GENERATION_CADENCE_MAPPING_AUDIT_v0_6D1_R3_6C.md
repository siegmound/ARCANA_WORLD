# NEMO per-generation cadence mapping audit — R3.6C

R3.6B correctly established row-stochastic forward dispersal semantics, but its canonical synthetic values (for example `0.05`) were not yet cadence-equivalent to ARCANA because NEMO consumes dispersal per generation while ARCANA consumes effective exchange once per 125 kyr biology step.

R3.6C closes this ambiguity. For the B1 two-deme reference (`0.05` off-diagonal per 125 kyr), exact Markov cadence normalization at 5-year generations gives a per-generation off-diagonal probability of approximately `2.1072058728e-6`, not `0.05`.

The R3.6B B3 stress matrix is intentionally preserved but is rejected for exact per-generation mapping because its finite-step transition is not embeddable as an accepted continuous-time Markov generator. R3.6C creates a separate `C3_EMBEDDABLE_HIGH_ADMIXTURE_STRESS` reference from symmetric edge targets. C3 is benchmark-only and never replaces any ARCANA production exchange matrix.

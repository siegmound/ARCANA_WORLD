# NEMO admixture-only reference protocol — v0.6D1-R3.6D

## Experimental question

Does a genetically explicit finite-population model generate an admixture-driven increase in standing additive variance comparable to ARCANA's moment-mixing operator when both start from equivalent quantitative-trait moments and cadence-normalized exchange?

## Scenarios

- **B0** — equilibrium/no-flow sanity control.
- **B1** — two-deme admixture.
- **C3** — embeddable high-admixture stress reference introduced by R3.6C.

Historical R3.6B B3 remains unchanged and is not sent to exact per-generation NEMO conversion because it is non-embeddable.

## Matched-pair design

For each `(scenario, N, replicate, axis)`:

`FLOW` and `MATCHED_NO_FLOW` use the same:

- QTL realization;
- allele frequencies;
- effect sizes;
- population size;
- generation count;
- NEMO random seed.

Only migration differs.

Primary NEMO statistic:

`Delta V_A^NEMO = V_A(FLOW) - V_A(MATCHED_NO_FLOW)`.

This common-random-numbers design reduces stochastic noise from drift and recombination.

## ARCANA comparators

Like-for-like comparison uses the ARCANA **admixture-only** probes:

- `1 x 125 kyr` moment mixing;
- `5 x 25 kyr` cadence-normalized moment mixing.

The full R3.6C Riccati/homeostasis run is retained as context but is not the primary numerical comparator because R3.6D deliberately does not implement an invented NEMO equivalent of ARCANA `mu/b`.

## Population-size sensitivity

NEMO individual count is a numerical/reference scale, not a direct interpretation of WorldSim population units.

At least two N values are required before biological inference. The runpack reports the range of `Delta V_A` across N but does not invent a convergence threshold.

Recommended execution order:

1. pilot `N={500,2000}`, two replicates;
2. inspect runtime and drift sensitivity;
3. extend N and replicate count only if required by the evidence.

## Inference gate

R3.6D outputs `REVIEW_REQUIRED` evidence. It cannot authorize a parameter correction.

Possible later interpretations include cadence mismatch, moment-mixing excess, biologically plausible high admixture variance, or unresolved finite-N sensitivity. Those decisions belong to the next governed stage.

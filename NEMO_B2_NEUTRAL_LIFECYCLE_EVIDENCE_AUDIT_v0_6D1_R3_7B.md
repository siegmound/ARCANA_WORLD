# v0.6D1-R3.7B — NEMO B2 Neutral Lifecycle Evidence Audit

## Raw evidence
Source: `reference_results/v0_6D1_R3_7A_B2/v0_6D1_R3_7A_B2_RESULTS.zip`

SHA-256: `1f3484703c2482781222fb0de80cea5f2c7354b5eadc7e35f204c7885168d292`

The suite contains 8 complete chains:
- N = 500 and 2000;
- 2 replicates;
- 2 trait axes;
- 3 sequential phases per chain;
- 24 successful NEMO phase executions total.

Suite status: `NEMO_B2_EVIDENCE_COMPLETE_REVIEW_REQUIRED`.

## Comparison method
Each phase is predicted independently from that phase's *actual saved initial allele frequencies*. This removes accumulated stochastic error from earlier phases and asks a clean question:

> Given the exact starting frequency state, does the parameter-free reduced neutral `(VA,S)` recursion reproduce the next NEMO endpoint?

No coefficient is fitted to the B2 results.

## Results — 24 phase endpoints
For mean pairwise segregation potential:

- minimum observed/predicted: 0.71034
- median observed/predicted: 0.96704
- mean observed/predicted: 0.95209
- maximum observed/predicted: 1.29953

For mean within-deme VA:

- median absolute fractional error: 0.01361
- mean absolute fractional error: 0.01689
- maximum absolute fractional error: 0.04291

### By phase
`CONNECTED_BURNIN`
- median S ratio: 1.03874
- mean S ratio: 0.99965
- median absolute VA error: 1.285%

`FRAGMENTED`
- median S ratio: 0.96704
- mean S ratio: 0.97308
- median absolute VA error: 1.123%

`RECONNECTED`
- median S ratio: 0.87205
- mean S ratio: 0.88353
- median absolute VA error: 1.898%

### By population size
N=500:
- median S ratio: 0.96704
- median absolute VA error: 1.523%

N=2000:
- median S ratio: 0.96402
- median absolute VA error: 0.925%

## Lifecycle behavior in the real chains
Across the 8 chains, the observed mean-pair `S`:
- grows during fragmentation by median ~9.38x relative to the connected burn-in endpoint;
- after reconnection falls to median ~8.65% of the fragmented endpoint;
- ends at median ~73.5% of the burn-in endpoint, with finite-N stochastic spread.

The reduced neutral model reproduces this growth/collapse pattern without a new parameter.

## Interpretation
The evidence supports the R3.7A neutral lifecycle:
- drift moves expected genic variance from within-deme VA into between-deme S;
- connectivity/migration contracts S;
- reconnection reverses much of isolation-built divergence;
- N sensitivity follows the expected finite-N direction.

The post-reconnection median ratio below one is recorded, not calibrated away. With only two replicates per N/axis, it does not justify a new reconnection factor.

## Critical limitation
B2 explicitly had `selection_enabled = false` and `mutation_rate = 0`.
Therefore B2 **cannot** calibrate or authorize the directional-selection participation number `K_eff`.

Verdict: `PASS_NEUTRAL_S_LIFECYCLE_SUPPORTED_BY_NEMO_B2`.

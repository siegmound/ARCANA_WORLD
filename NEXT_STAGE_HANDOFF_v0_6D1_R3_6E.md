# Next-stage handoff after v0.6D1-R3.6E

## Closed
- R3.6D real NEMO execution: PASS (40/40 jobs, 40/40 parsed).
- Independent causal discrimination: PASS.
- Cadence-only explanation: rejected as primary cause.
- `b`-first recalibration: not authorized.
- ceiling raise: not authorized.

## Current diagnosis
The principal R3.5 VA inflation comes from `gene_flow_moment_mix` treating the whole-trait between-deme mixture term as persistent within-deme additive variance. NEMO and the exact QTL analytic reference show that most of this structure remains between demes / transient ancestry covariance and is not durable genic VA after recombination.

## Next recommended stage
`v0.6D1-R3.7 — Segregation-Aware Admixture Variance State & Reduced-Order Genetic Mixing Repair`

Required design goals:
1. preserve existing mean-gene-flow semantics and conservation;
2. split `VA_within` from transient admixture/ancestry covariance;
3. introduce no arbitrary global suppression scalar;
4. derive recombination decay from an explicit effective genetic architecture parameterization;
5. reproduce analytic QTL limits and NEMO envelopes on B0/B1/C3;
6. only then rerun short R3.5 windows and finally 210→150 Ma;
7. keep `mu`, `b`, speciation, fission, coalescence, paleogeography and ceiling unchanged until the new operator is validated.

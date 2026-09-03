# ARCANA WorldSim v0.6D1-R3.7 status

**Stage:** Segregation-Aware Admixture Variance State & Reduced-Order Genetic Mixing Repair

**Verdict:** `PASS_SEGREGATION_AWARE_OPERATOR_REFERENCE_CLOSURE__PRODUCTION_STATE_EVOLUTION_PENDING`

Closed in this stage:
- exact reduced-order segregation-potential definition;
- current-species-bound transition preserving D3.3A mean-flow semantics;
- exact QTL genic-variance mixing identity;
- explicit signed ancestry/LD covariance reservoir;
- recombination decay for the NEMO free-recombination reference;
- exact migration update of pairwise segregation potential;
- B1/C3 analytic-QTL reference closure.

Still pending:
- World-1 initialization of `S_ij`;
- selection/mutation/drift evolution of `S_ij`;
- fission/coalescence/speciation/remap lifecycle of the new state;
- short R3.5 runtime binding;
- 210→150 Ma rerun.

Governance:
- canonical write: NO
- production runtime binding: NO
- `mu`/`b` change: NO
- ceiling change: NO

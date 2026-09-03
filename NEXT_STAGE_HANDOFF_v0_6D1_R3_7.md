# Next-stage handoff after v0.6D1-R3.7

## Closed
R3.6E proved the current whole-trait admixture operator structurally over-promotes between-deme mean structure into persistent VA.

R3.7 implements and validates a replacement reduced-order representation:
- `VA_within[deme,trait]`;
- signed `C_ancestry_LD[deme,trait]`;
- `S[deme,deme,trait]` segregation potential.

The exact reference identity is:

`VA'_i = sum_j P_ij VA_j + 0.5 sum_jk P_ij P_ik S_jk`.

On B1/C3 from the real R3.6D QTL ensemble, R3.7 matches direct QTL allele-frequency mixing to ~1e-10 relative error, while the legacy operator is 114–127x too large.

## Governance
Do not bind R3.7 to the production 210→150 Ma runtime yet.
Do not change `mu`, `b`, q*, the ceiling, speciation, fission/coalescence, paleogeography or gene-flow geometry.

## Next stage
`v0.6D1-R3.7A — Segregation-Potential Initialization, Evolution & Deme-Lifecycle Calibration`

Required work:
1. define initial `S` at the 210 Ma common state without inventing hidden genomic detail;
2. derive how directional selection changes `S` as trait means diverge;
3. define drift/mutation effects on `S` consistently with existing D3.3A expectations;
4. define exact inheritance/pooling rules for fission and coalescence;
5. define separation semantics when a new current species is created;
6. validate those rules with additional NEMO microbenchmarks (isolation → divergence → reconnection, including B2);
7. only after those gates bind the operator into a short World-1 replay.

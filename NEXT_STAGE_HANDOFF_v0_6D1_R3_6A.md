# Next stage handoff after v0.6D1-R3.6A

Proceed to:

`v0.6D1-R3.6B — NEMO 2.4.2 Governed QTL-Ensemble Reference Benchmark`

## Objective

Construct independent genetically explicit NEMO reference experiments without modifying ARCANA scientific parameters.

## Required work

1. bind a NEMO 2.4.2-validated `.ini` template from the official examples/manual;
2. define a governed mapping from ARCANA population units to explicit NEMO individuals;
3. define an ensemble of QTL/genotype realizations matching selected ARCANA trait means and additive variances in expectation;
4. construct controlled no-flow, admixture, fragmentation and reconnection benchmarks;
5. construct at least one ARCANA-derived problematic exchange regime around the R3.5 ~191 Ma transition;
6. run multiple seeds/replicates and record uncertainty;
7. compare NEMO against both current ARCANA 125 kyr and restored `5 × 25 kyr` quantitative-genetic cadence;
8. do not change `mu`, `b`, ceiling or speciation rules until the three-way evidence is reviewed.

## Execution policy

Short validation and adapter tests may run in ChatGPT's environment. Longer NEMO ensembles should run locally/WSL2 or another pinned execution environment, with all engine/version/config hashes recorded in the evidence bundle.

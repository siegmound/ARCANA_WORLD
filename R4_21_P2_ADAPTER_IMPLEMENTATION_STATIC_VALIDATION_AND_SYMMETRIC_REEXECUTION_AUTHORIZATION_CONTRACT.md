# ARCANA WorldSim v0.6D1-R4.21
## P2 Adapter Implementation Static Validation & Symmetric Reexecution Authorization

R4.21 is an authorization gate. It does **not** execute external engines and does not change canonical state.

### Parent
Requires R4.20 SEALED with six P2 cells preflight-ready, 57 active target-protocol repairs, two context-only proxies, and six P3 backlog cells.

### Static implementation gate
For each P2 engine family, R4.21 requires:
- a new-namespace candidate adapter with valid Python syntax;
- exact preservation of the full frozen R4.2 job set for that shared engine adapter;
- parent adapter source provenance and hash integrity;
- exact seed reuse from each frozen R4.3 `JOB_CONTRACT.engine_input.replicates` during future execution;
- no target leakage, result-selected tuning, historical adapter overwrite, or canonical write.

Additional fail-closed requirements:
- **CDMetaPOP**: R4.7 dynamic-forcing repair profiles must exist for every frozen CDMetaPOP job; population extraction uses exact `summary_popAllTime.csv`; absolute response remains PROXY_ONLY and matched-neutral response remains non-adjudicative until a domain-equivalent ARCANA causal target exists.
- **Geonomics**: `run_default_model()` is forbidden. Each frozen Geonomics job requires an explicit, hash-bound canonical spatial binding profile and parameters file. Scalar ARCANA descriptors may not be synthesized into an invented spatial raster.
- **NEMO**: qfreq statistics retain their native semantics; heterozygosity is not additive variance, and frequency differentiation is not a gene-flow rate.
- **SLiM**: tree-sequence statistics retain sample/population/time semantics; diversity is not ancestry and FST is not a migration rate.

### Partial authorization
R4.21 may SEALED with some engine families authorized and others deferred. Authorization always applies to the **entire frozen R4.2 job set of that engine family**, never to a result-selected cell.

R4.21 itself performs zero engine runs. R4.22 is the earliest stage allowed to execute the frozen authorization registry.

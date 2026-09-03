# v0.6D1-R4.15 — Retained Runtime Metric Recovery & ARCANA Target-Semantic Materialization Audit

Parent: R4.14 SEALED. R4.15 is evidence-first and performs **no engine execution**.

Frozen scope:
- exactly 4 P0 retained-runtime recovery cells from R4.14;
- exactly 59 P1 ARCANA-target semantic cells from R4.14;
- R4.2 frozen 23-job registry remains immutable;
- no canonical state, replay, parameter change, Deep coupling, or majority vote.

P0 policy:
- inspect only retained runtime artifacts;
- recover raw/derived metrics for NEMO qfreq, SLiM tree sequences, and CDMetaPOP summary population evidence when those engines occur in the R4.14 P0 set;
- **no recovered metric is adjudicative in R4.15**. R4.16 must freeze a domain-specific transform before promotion.

P1 policy:
- search existing ARCANA canonical artifacts only;
- external-engine results may never define ARCANA targets;
- artifact hits are source candidates, not targets;
- R4.16 must specify value, units, temporal basis, spatial basis, transform, uncertainty, and provenance before any target becomes adjudicative.

Outputs:
- `R4_15_RETAINED_RUNTIME_METRIC_RECOVERY.json`
- `R4_15_ARCANA_TARGET_SOURCE_CANDIDATE_REGISTRY.json`
- `R4_15_R416_PROMOTION_GATE_PLAN.json`
- `R4_15_INTEGRATED_AUDIT.json`
- final seal under `outputs/v0_6D1_R4_15_SEAL/`.

## R4.15-R1 repair precedence

R4.14 froze four P0 entries as **candidate** retained-runtime recoveries and named the candidate engine in each cell's `closure_action`. R4.15-R1 supersedes the initial over-broad implementation that required successful retained extraction from every PRIMARY engine sharing that cell.

For P0 realization, the required engine is exactly the one named by the frozen R4.14 closure action. Other PRIMARY engines remain audited context and are not silently converted into required P0 extractors.

Every P0 candidate must resolve as exactly one of:

- `P0_RETAINED_RUNTIME_METRIC_RECOVERED`; or
- `P0_CANDIDATE_EXHAUSTED_RECLASSIFIED_TO_P2`.

The second state is a valid evidence-closure conclusion, not a scientific result. It authorizes no engine execution in R4.15-R1 and no adjudicative promotion. Only a later governed P2 stage may authorize symmetric adapter-enhanced reexecution.

R4.15-R1 seals only when all four candidates are explicitly resolved, all 59 P1 cells remain audited, and no metric/target/canonical promotion occurs.

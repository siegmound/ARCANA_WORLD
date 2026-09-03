# ARCANA WorldSim — v0.6D1-R5.9 Contract

## R5.8 → sealed R3.28 200 ka→0 High-Resolution Reconciliation and 0 ka Handoff

### Purpose
R5.9 does **not** run a new 200 ka→0 simulation. The repository already contains a SEALED R3.28 high-resolution replay for the exact two-lineage `HUMAN_200KA` cohort. R5.9 revalidates that sealed replay against the newer R5.7/R5.8 evidence chain and emits a clean 0 ka reconciliation handoff.

### Parent authorities
1. R5.8 scientific candidate, exact 200 ka handoff:
   - `RPT_010_D02`
   - `RPT_009_D02`
   - unique human species identity not materialized.
2. R3.28 SEALED high-resolution replay and HUMAN_0KA checkpoint.
3. The R3.27 trajectory hash inherited through the R5.8 parent binding, used only to independently reconstruct the exact R3.27→R3.28 initialization boundary.

### Runtime utility review
No new external engine execution is scientifically justified. R3.28 is already a governed sealed 200 ka→0 replay. R5.9 is a provenance/semantic reconciliation stage.

### Exact boundary checks allowed
R5.9 may require exact equality between the R3.27 200 ka parent values and the R3.28 time-zero initialization **only because this is the same ARCANA pipeline handoff**. This is not a heterogeneous-engine corroboration rule.

### R3.28 semantics preserved
- 280 time states from 200 ka to 0.
- 32 stratified R3.27 members (`0,3,...,93`).
- two candidate lineages in fixed order.
- R3.18 is phase-integral authority downscaled under the sealed R3.28 method; it is not reinterpreted as a direct recent time series.
- R3.20 CHA-2 14.95→11 ka is consumed directly at 50-year cadence (80 states).
- R3.28 `contact_index` and `admixture_opportunity_cumulative` remain diagnostics only. They are not true local ancestry and are not realized historical admixture.
- R5.6 true-local-ancestry challenge results end at the 200 ka boundary and are not injected retroactively into R3.28 as realized state.

### 0 ka rule
The sealed R3.28 result contains both lineages at 0 ka. R5.9 therefore must preserve a two-lineage 0 ka handoff with `unique_human_identity_materialized=false`.

### Downstream governance
Existing R3.29+ sealed legacy stages are **not automatically authorized** for the new R5 branch. R5.9 only makes R3.28 a reconciled authority. R3.29 must be reconciled explicitly next before downstream settlement/cultural history is accepted into the new branch.

### Prohibitions
- no R3.28 rerun;
- no new external engine execution;
- no result-selected tuning;
- no numeric historical truth claim;
- no realized-admixture claim from R3.28 diagnostics;
- no canonical rewrite;
- no derived refinement promotion;
- Deep biological coupling remains OFF;
- no automatic authorization of R3.29+.

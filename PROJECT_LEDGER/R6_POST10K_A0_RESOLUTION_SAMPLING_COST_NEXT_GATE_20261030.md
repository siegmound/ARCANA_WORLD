# R6 POST10K-A0 — read-only resolution, sampling and cost gate

The operator-reported synthetic R2 10k benchmark completed at Y10000 with 610001 causal records, 40 B0 paired checkpoints and nine historical query files. This action registers the next audit, not a new numerical run.

**First task:** determine exact numerical vs recorded time resolution, spatial 3x3 geometry and cell area, C028/C029 column node/depth spacing, thermal adaptive substeps, annual hydrology, event timestamp precision, and differences among 10001 reconstructible annual snapshots, 9 exported query snapshots, 40 recovery checkpoints and 10-year staged fsync. The reported regional baseline uses 1e6 square meters per cell, but verify the actual FAIR run contract/source. Undefined geography, subyear event time and missing biological domains remain UNKNOWN.

**Second task:** design read-only sampling of the existing immutable compact history: uniform yearly/decadal/century views, event-triggered exact-year windows, per-cell/material/Deep indexing, and batch replay from the committed journal. Preserve full provenance; no invented subannual or subcell resolution. A future finer physical model requires qualified providers, finer forcing and new numerical runs under distinct authorization.

**Third task:** real cost breakdown from 100 reported 100-year windows, resource samples and 40 commits; identify five remaining O(D) deposit passes, resident journal and decoded checkpoint chain, query cost and RSS overlap. Numeric advance+ingest 1244.446166s; full process 1484.032774s; post-run audit 124.862212s; peak RSS about 3.706GiB, run files 2469842406 B. First/last 100-year numerical window 3.181873/28.412477s. Do not double-count nested phases.

The detailed operational A0 handoff is available in the conversation as `ARCANA_R6_POST10K_A0_COST_AND_RESOLUTION_SAMPLING_GATE_20261030.md`. The FAIR operator should use it with `docs/arcana/R6_RUNTIME_R2_10K_FAIR_20261030.md`. No source edits, full legacy export, 10k rerun, 100k run, git commit/push or production/science authority. Gate output is `POST10K_A0=PASS_REPRODUCIBLE_RESOLUTION_AND_SAMPLING_AUDIT` or BLOCKED with evidence.

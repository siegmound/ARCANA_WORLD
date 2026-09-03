# v0.6D1-R4.10 — Matched-Control Precision & Alternate-Evidence Closure Contract

R4.10 is an audit/planning stage. It executes no historical engine job and does not reclassify the R4.9 result with a post-hoc statistical rule.

## Trigger

R4.9 SEALED with `EXPANDED_MATCHED_CONTROL_EFFECT_UNCERTAIN` and explicitly prohibited automatic further replicate escalation.

## New integrity finding audited in R4.10

The R4.3/R4.7/R4.8/R4.9 CDMetaPOP adapters selected CSV files using the broad predicate `"ind" in p.name.lower()`. The copied pinned example input contains files such as `yytype_hindex0.csv` and `wildtype_hindex1.csv`; `hindex` contains the substring `ind`. Therefore copied input files can enter the population-file candidate list.

The CDMetaPOP source itself provides `summary_popAllTime.csv` with `N_Initial`, which is a same-lifecycle-phase population tracker. R4.10 freezes this as the preferred extraction authority for the repair stage.

## Governance

- preserve all R4.3–R4.9 evidence and seals;
- do not delete negative/invalid evidence;
- old CDMetaPOP population-response metrics may not authorize canonical replay until repaired;
- do not add more replicates automatically;
- do not change R3.11 or any canonical parameter;
- no majority vote;
- Deep remains OFF.

## R4.11 plan

R4.11 must first re-extract existing CDMetaPOP runtime work using `summary_popAllTime.csv` / `N_Initial`. It applies the repair symmetrically to all five R4.7 CDMetaPOP jobs and rebuilds the J09 dynamic/neutral paired effect. Engine reruns are allowed only for arms whose required runtime summary artifacts are absent. Readjudication must reuse the frozen R4.4 policy.

# ARCANA R6 — Source contact feature admissibility FAIR: operator-reported diagnostic PASS

Date: 2026-11-20. Driver source commit: `a51c84ec1cca9775e825924566f3d7e2832cbbd7`. Operator-supplied final 1024 lines of FAIR terminal output, not entire stdout or raw evidence files.

The visible output reports `DRIVER_EXIT_CODE=0`, `PASS_SOURCE_EDGE_FEATURE_ADMISSIBILITY_INVENTORY__PHYSICAL_CONTACT_OPEN`, runtime 2.637046 s, and `REPORT.json` SHA256 `e7b8f9c47bcd9f46a35f9edb06ee52ba641747f006482a1efc766f25b5b1fc21`. MANIFEST schema `ARCANA_R6_CONTACT_FEATURE_ADMISSIBILITY_MANIFEST_V1` and `physical_T1=null`. **Neither raw FAIR REPORT.json nor MANIFEST.json has been independently fetched. The excerpt begins mid-JSON, and the pytest result is NOT visible; do not claim an exact number of passing tests.**

## Observed source-geometry findings

- 16×16 source domain at T0: **36/36** original source edges categorized `AMBIGUOUS`. This is consistent with coincident source-edge twins at T0; no unique admissible surface-contact separating gap was established.
- 16×16 records `source_feature_classification_transition_count=8`. The code increments this when **classification OR reason changes**. Therefore 8 is NOT necessarily eight changes in the classification label. Full details are not present in the pasted terminal excerpt.
- 16×16 at 100/500/1000 years: four old T0-linearized KKT active links still have positive oriented point-pair 3D gap minima `1.073929 / 5.415396 / 10.908885 m`, so old T0 reactions still cannot be promoted to updated-geometry Signorini contact.
- Signed closest-segment normal projections are negative on 6/7/5 source edges at 100/500/1000 years, with minima `-0.668775 / -3.037951 / -5.601532 m`. These are **diagnostics, not penetration of a demonstrated closed 3D solid surface**.
- All six visible prior SO(3) diagnostic checkpoint errors are small (max signed segment projection error `9.5092e-10 m` vs unchanged `1e-7 m` bound). This is the prior paired segment diagnostic, not proof of a full material contact solver.
- Visible 8×8 region at 500 and 1000 years retains 12 source segments. T0 and each checkpoint's **new admissibility classification counts** are not present in the excerpt; cannot infer number of eligible manufactured edge witnesses.

## Decision and additional FAIR evidence to inspect

`PASS_SOURCE_EDGE_FEATURE_ADMISSIBILITY_INVENTORY__PHYSICAL_CONTACT_OPEN` **from operator terminal**, subject to raw FAIR REPORT/MANIFEST SHA verification and capture of missing counts. No canonical seal, no physical T1 and no source-rock contact constitutive authority.

Before deciding the next experimental implementation, inspect and summarize the **actual generated** `G2_CONTACT_FEATURE_ADMISSIBILITY_NEW_01/REPORT.json`, *not* truncated stdout. For region 8 and 16, extract `T0_feature_admissibility_inventory.counts_by_classification`, every `checkpoints[year].feature_admissibility_inventory.counts_by_classification`, number of `source_eng_only_eligible_count`, classification-vs-reason transition details, `NOT_QUALIFIED` reasons, and any source-owned per-feature consistency audits; verify report SHA equals manifest.

## Following science-first decision

If all/most genuine edges remain ambiguous, **do not impose line-line closest-segment sign as a physical contact constraint** and do not launch updated-geometry KKT yet. Next designed research contract: reconstruct *authentic* plate-owned triangle/face neighborhoods of the original source boundaries and a reliable reference side/normal or volume separating-surface topology; adjudicate whether thickness/solid shell authority is sufficiently grounded; handle triple parent node 34587 and potential switching/edge-endpoint degeneracies; determine a mathematically objective contact g(q) and its derivative **on qualified features only**, with non-penetration semantics proven before manufactured KKT.

The experiment is an engineering geometry-admissibility inventory, not geological collision or true global 3D nonpenetration. `D-024=ACTIVE`, `physical_T1=null`, `HistoryStore` unchanged, no physical solver run.

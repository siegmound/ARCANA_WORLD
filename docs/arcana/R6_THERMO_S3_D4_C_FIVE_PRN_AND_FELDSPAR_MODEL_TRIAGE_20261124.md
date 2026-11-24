# R6 THERMO S3-D4-C — five original PRNs and feldspar model triage

Date: 2026-11-24. Decision: `S3_D4_C_FIVE_PRN_READBACK_PASS__HGP_4TR_CANDIDATE_IDENTIFIED__SCIENCE_UNKNOWN`.

## Operator evidence (not independent FAIR byte access)
Operator FAIR five-original-PRN read-only audit PASS (exit0), original S2 manifest 74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604, guarded command source fbb1e77c54e3545ea2e7e7b52226ed0576f1993e; all five PRNs identical SHA256 d942bfa0e73e0d0fcb4ca06fe2a074ea7883d4116ca632638f343e2a23f02c90, Fsp(C1)31.05wt%, XAb0.44901551 XAn0.54274457 XOr0.00823992, 1050K heuristic cutoff0.48100 not met 5/5. No new engines, S2 immutable. Source review: pinned solution_model.dat (blob 564742a569998a768c2d8e15d2b9599ee90438d1) contains Pl(I1,HP), Fsp(C1), and Fsp(HGP) 4TR (Holland/Green/Powell 2021 DOI 10.1111/jmg.12639); legacy I1/C1 cannot determine structural stability by Gibbs ranking. HGP candidate only: actual ab vs legacy abh, alpha(an) comment .550 vs executable .555; all four named endmembers present in hp62ver.dat (blob 34ab165fe8e5856294d7a967c63e07dfc04d701b), but compatibility/erratum/normalization and calibration not qualified.

All five paths PERPLEX_01..05/BL691_MEEMUM/bl691_MEEMUM.prn verified against the original sealed manifest according to the supplied operator transcript. Full byte equality pertains only to these PRNs, not every S2 file. The previous documented script checks source and manifest, phase-list parity and printed composition; the modified operator command used Ab <= cutoff and disabled PYTHONOPTIMIZE. The transcript is preserved in the new receipt. Reproducibility is not model validity. No further repeat of S2 is required for this specific flag.

## Pinned upstream source review
- [solution_model.dat](https://github.com/jadconnolly/Perple_X/blob/950d882bb6a9325a627109aa7154f7b526aa3087/test/bl691_MEEMUM/solution_model.dat), blob 564742a569998a768c2d8e15d2b9599ee90438d1: legacy Van Laar models lines ~8610–8760, HGP lines ~17654–17740. The upstream warning says I1/C1 cannot predict stable structure; the I1 parameterization is always more stable according to the warning, so selecting by lower G cannot establish symmetry. The threshold is binary guidance, not a universal ternary rule.
- [BL691 input](https://github.com/jadconnolly/Perple_X/blob/950d882bb6a9325a627109aa7154f7b526aa3087/test/bl691_MEEMUM/bl691_MEEMUM.dat), blob 3954964480612264838636fd394043aa0fef6324: selects Fsp(C1), not Pl(I1,HP) or Fsp(HGP).
- [hp62ver.dat](https://github.com/jadconnolly/Perple_X/blob/950d882bb6a9325a627109aa7154f7b526aa3087/test/bl691_MEEMUM/hp62ver.dat), blob 34ab165fe8e5856294d7a967c63e07dfc04d701b: database title TC-DS62; ab, abh, san, an entries around lines 1779–1815. Presence does not establish model/database compatibility.
- Holland, Green & Powell (2021), DOI https://doi.org/10.1111/jmg.12639 ; accepted-version abstract https://www.repository.cam.ac.uk/items/43d62b88-690c-4e23-9f3f-5eeefb41ce54 : seven models compared, 4TR best fitted considered data, partial tetrahedral ordering. Source abstract reviewed, full parameter-table/erratum audit pending.
- Author/developer note https://hpxeosandthermocalc.org/2022/01/27/a-new-x-eos-for-ternary-feldspars/ : binary structural transition not safely extrapolated to ternary; Gibbs ranking not necessarily correct symmetry; notes correction of ideal anorthite activity normalization (16^(1/4)). No inference yet on how Perple_X handles normalization.

| Model | Na endmember | W(Ab,An) constant | W(Ab,Or) constant | W(An,Or) constant |
|---|---|---:|---:|---:|
| Fsp(C1) | abh | 3100 | 25100 | 40000 |
| Pl(I1,HP) | abh | 15000 | 25100 | 40000 |
| Fsp(HGP) | ab | 14600 | 24100 | 48500 |

Actual HGP W terms include T/P dependence; legacy C1/I1 also have different DQF corrections. HGP source comments give alpha(an)=.550; implemented .555. Do not assume typo or fix without primary source. Native HGP model has M-site and T-site with effective T multiplicity 1, true 4; lAb(HGP) is a companion for Na-rich side of peristerite gap; its inclusion policy is not yet decided. The HGP model targets phase equilibria rather than explicit structural symmetry, so success would not alone adjudicate physical I1/C1 crystal structure. Augite, amphibole and MAGEMin G25 applicability remain open.

## Next scope
NEXT: source-only HGP 4TR implementation and calibration audit (paper parameter table, correction/normalization, database reference states and model-list compatibility including lAb(HGP)); resolve or retain explicit UNKNOWN, then design separate bounded Earth-only BL691 anchor sensitivity C1 vs I1 vs qualified HGP, not simultaneous I1/C1 Gibbs selection. No execution until separate authorization, numerical acceptance/resource contract and fresh evidence identity. D4-D 122/122 software PASS, all 50 S3 cells UNKNOWN/NOT_APPROVED, S3 engines0; D-024 ACTIVE, physical_T1=null, mechanics/history production false.

Compare separate model configurations at exact 4000bar/1050K, same bulk, other models, options and binary; any necessary database or model-list change becomes a separate sensitivity factor rather than a one-factor comparison. Preserve complete native outputs, component and mass closure, phase sets and compositions, warnings, observed wall/peak RSS/IO, and source/configuration/manifest pins. No experiment, threshold, source edit or run authorization here.

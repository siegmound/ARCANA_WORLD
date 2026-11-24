# ARCANA R6 — S3-D4 primary-source model and P/T-X review (V2)

Date: 24 November 2026. Decision: S3_D4_PINNED_PHASE_WARNINGS_AND_G25_UNCERTAINTY_SOURCE_AUDIT_PASS__50_CELLS_NOT_APPROVED. This is a literature and pinned-source review, not a thermodynamic runtime result.

## Exact original-source provenance
Perple_X upstream commit: 950d882bb6a9325a627109aa7154f7b526aa3087. Original BL691 problem definition Git blob: 3954964480612264838636fd394043aa0fef6324. Original selected solution_model.dat Git blob: 564742a569998a768c2d8e15d2b9599ee90438d1. Exact sources: https://github.com/jadconnolly/Perple_X/blob/950d882bb6a9325a627109aa7154f7b526aa3087/test/bl691_MEEMUM/solution_model.dat; https://groups.io/g/PerpleX/topic/64123068. Previous S3 software FAIR-qualified source SHA: 9a9c996b909d7752114165f7f036ebf2b00fb966.

## Scientific finding A — G25 model uncertainty and mixed phase-model provenance
HPx model-author reference https://hpxeosandthermocalc.org/the-hpx-eos/the-hpx-eos-families/hpx-eos-igneous-sets/ describes Green et al. 2025 G25 as corrected H18 igneous solution set for hydrous/anhydrous subalkaline systems, using dataset v6.36. The phases use distinct activity-composition models (e.g., liq_G25w, fl_G25, cpx_W24, opx_W24, fsp_H22, amp_G16).

The primary corrigendum https://academic.oup.com/petrology/article/66/1/egae079/7989477 gives a loosely illustrative boundary uncertainty of about ±1 kbar for pressure-sensitive phase boundaries or ±50°C for temperature-sensitive phase boundaries involving substantial phase fractions. Accessory-phase occurrence has much larger uncertainty. The S3-A candidate grid increments are exactly 1 kbar and 50°C. Therefore a change between adjacent computed cells is NOT proof of a geological boundary location with cell-size precision, and these illustrative physical uncertainty magnitudes are NOT to be used as the numerical solver's error acceptance thresholds.

The corrected model used constraints at other P/T-X conditions including lunar Ti-rich glass 10kbar/1435°C, basalt SC1 ~1atm at 1075/1110°C and Icelandic basalt analogues at 3kbar. These facts do not specifically validate original MAGEMin CUSTOM_IG sample at 10kbar/1100°C or each of 25 proposed points. Original source bulk is an upstream demonstrator (11 oxides, reported sum 99.75wt%, H2O 3wt%, FeO 6.65wt%, Fe2O3 1.64wt%), with fixed Fe2O3-to-native-FeO/O bookkeeping, not a field sample with proven subalkaline classification.

## Scientific finding B — BL691 selected solution models have original upstream cautions
The pinned BL691.dat selects cAmph(G), Augite(G), melt(G), Ep(HP11), Gt(W), Opx(W), Bi(W), Ilm(WPH), Sp(WPC) and Fsp(C1).

- Fsp(C1): the pinned solution_model.dat explicitly documents the I1/C1 feldspar structural-state selection and solvus caveats. The author Connolly separately warns about using these specific models without advance knowledge of the stable state (https://groups.io/g/PerpleX/topic/64123068). Historical S2 Fsp(C1) output is reproducible, but does not itself demonstrate a correct structural-state choice at other P/T conditions.
- Augite(G): pinned file says the model should not be used for Na-rich compositions. Original BL691 bulk Na2O=2.5416 molar input alone does not determine the resulting Augite phase Na composition; require phase-specific evaluation.
- cAmph(G): pinned file describes a simplified implementation with some Fe3+ and Ti pargasite exchanges omitted in part for computational feasibility. This is a documented approximation, not proof that all original results are incorrect; determine its relevance to phase chemistry.
- melt(G) is part of G16, not the G25 melt model. Green et al 2016 https://doi.org/10.1111/jmg.12211 calibrates a particular metabasic set for major experimental phase-in/out boundaries at pressures up to 13kbar, but does not prove all 25 BL691 P/T-X points valid.
- BL691 original problem P500–10000bar and T873–1323K is not a material calibration envelope. The Perple_X original chemical components include O2 and H2O, and are not identical to the FeO/Fe2O3 source basis in the MAGEMin demonstrator.

## Decision: retain 50 UNKNOWN cells; no source or scientific promotion
The non-executable companion JSON experiments/r6_thermo_provider_pilot_v1/s3_d4_primary_source_model_risk_v2.json records 8 sourced findings, ten original selected BL691 solution models, and 50 explicit P/T candidate cells with PT_X_scientific_domain=UNKNOWN and authority=NOT_APPROVED. The two S2 anchor cells are flagged only as historical upstream engine test points, not experimental validation. Previous triage V1 remains unchanged.

Next, S3-D4-C: composition- and phase-specific adjudication of G25 subalkaline/wet/redox applicability and BL691 Fsp I1/C1, Augite Na composition, cAmph redox/Ti, melt model experimental scope; if evidence is missing, leave UNKNOWN. S3-D4-D: preregister engineering numeric residual/closure, native printed rounding, same-P/T fresh-process stability, phase-boundary warnings and write-once source/evidence and cost budget separately from geological model uncertainty. A tiny source-bound Earth-only S3-D5 exploration requires separate explicit execution authorization; do not run 25+25 now.

D-024 strategic independence: progress on a physically supported regional T0→T1 geodynamic pipeline does not have to wait for unrelated thermo/biome/Deep provider qualifications. Current authority remains D-024 ACTIVE, physical_T1 null, mechanics false, world history production false. S2 SEALED unchanged, no S3 engine execution.

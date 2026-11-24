# ARCANA R6 — S3-D4 source-based scientific P/T-X triage and audited S2 timing baseline

**Date:** 2026-11-24. **Verdict:** `S3_D4_S2_TIMING_BASELINE_PASS__50_CANDIDATE_SCIENCE_CELLS_UNKNOWN__NO_S3_RUN_AUTHORIZED`.

All recorded S2 timings were measured on **FAIR** by the operator and SHA-checked against existing immutable S2 `MANIFEST.json` members. This GitHub entry records the operator's stdout and exact source meanings; the GitHub author has not independently accessed the FAIR raw byte contents. S3 science and runtime remain unapproved.

## Exact FAIR timing baseline from immutable S2 LAUNCH.json

| Source-native S2 process | N | Min wall s | Median wall s | Max wall s | Sum wall s | Native problems computed *per process* |
|---|---:|---:|---:|---:|---:|---|
| MAGEMin Julia | 5 | 6.281932055950165 | 6.380358584225178 | 6.3818054385483265 | 31.75680620968342 | **TWO**: KLB1 and CUSTOM_IG |
| Perple_X MEEMUM wrapper | 5 | 1.117596622556448 | 1.1679270006716251 | 1.1679777540266514 | 5.788513708859682 | **ONE**: BL691 |
| Total (ten serial launches) | 10 | — | — | — | **37.5453199185431** | historical S2 only |

The exact original S2 source is `632c4a570f876e3963b1dcd8a1f411a143fc8a59`; original REAL manifest SHA256 `74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604`. All ten existing `LAUNCH.json` were SHA-verified, exit0, timeout false; operator terminal marker `S3_D4_S2_RUNTIME_BASELINE_READONLY_PASS`, exit0. No extra engine work.

**Interpretation limits:** MAGEMin `6.38s` per process contains startup and **two** upstream equilibrium problems, while Perple_X `1.17s` includes a Python wrapper and original BL691 source/executable checks. These are not per-point S3 solve times. No extrapolation `25×` or run cap in seconds is defensible without at least source-native per-point/cold-start telemetry under **separate** future authorization. The S2 launch code sequentially awaited each process, with 600s timeout for each MAGEMin S2 process, 300s for each Perple_X S2 process; these historical safety ceilings are **not** proposed S3 budget/acceptance bounds. CPU load, peak RSS, disk I/O per S3 point, engine's multipoint behavior and phase-boundary complexity remain UNKNOWN; no S3 resource budget ratified.

## Science: model identity is NOT blanket P/T-X calibration

- **MAGEMin ig/tc_ds636** implements corrected **Green et al. (2025) G25** model with Holland & Powell dataset version **6.36**. HPx authors recommend G25 for **hydrous or anhydrous subalkaline systems**, not every geochemical class. The erroneous older H18 melt x-eos is explicitly superseded; a demonstration source bulk (11 oxides, 99.75 wt% as reported; Fe2O3 to native FeO/O conversion) has not been independently classified against **full** subalkaline composition/redox/water validity and phase-model experimental coverage at every P/T cell. Sources: https://hpxeosandthermocalc.org/the-hpx-eos/the-hpx-eos-families/hpx-eos-igneous-sets/ ; https://academic.oup.com/petrology/article/66/1/egae079/7989477 ; https://computationalthermodynamics.github.io/MAGEMin_C.jl/stable/database . Primary old H18 broad reported P/T scope must not be transferred indiscriminately to corrected G25/model-specific phases.
- **Perple_X BL691 hp62ver.dat** is based on **TC-DS620**, as used in Green et al. (2016), but the original BL691 source problem rectangle P500–10000bar, T873–1323K is a computational input range, not proof that experimental solution-phase calibrations, wet/redox or arbitrary assemblages are reliable across all 25 points. The Green et al. 2016 metabasic phase-model study states calibration across bulk compositions at pressures **≤13 kbar**, but that is not a full joint P/T-X calibration proof for original BL691 with this exact `solution_model.dat` model selection. Sources: https://www.perplex.ethz.ch/perplex_thermodynamic_data_file_body.html ; https://doi.org/10.1111/jmg.12211 ; https://www.perplex.ethz.ch/perplex_66_build_prompts.html .
- The two grids operate at different **temperatures** (MAGEMin 1000–1200°C = 1273.15–1473.15K; Perple_X 950–1150K = 676.85–876.85°C) and pressures (8–12 kbar versus 2–6 kbar); therefore **no same-point comparison is being conducted**. No provider winner/ranking. Distinct source bulk/redox data also remain scientifically incomparable.

## 25+25 candidate-cell status, explicitly fail-closed

The machine-readable companion `experiments/r6_thermo_provider_pilot_v1/s3_d4_science_budget_triage_v1.json` contains **50 explicit cells**, each with `scientific_ptx_applicability=UNKNOWN`, `authority=NOT_APPROVED`, `real_run_count=0`. For Perple_X all 25 satisfy the original file's *input rectangle only*, independently of scientific calibration. MAGEMin valid argument units/candidate axes are present, but no complete experimental G25 domain supports blanket cell validity.

- S3-A `MAGEMIN_CUSTOM_IG`: P[8,9,10,11,12] kbar × T[1000,1050,1100,1150,1200] °C; S2 computational anchor 10 kbar/1100°C.
- S3-B `PERPLEX_BL691_MEEMUM`: P[2000,3000,4000,5000,6000] bar × T[950,1000,1050,1100,1150] K; S2 computational anchor 4000bar/1050K.
- **0 scientific-cell approvals; 50 unknowns; 0 S3 engine runs.** An unknown is not proof of incorrectness, and a positive solver residual alone is not proof of calibration or geological truth.

## S3-D4 next preregistration plan (source-only, non-executable)

1. Source-classify original bulk as subalkaline/other, constrain pressure/temperature and experimental model calibrations, Fe redox and water thermodynamic formulation, and liquid/solid phase per provider; attach **paper/figure/table-backed** coverage per cell. Where any support remains UNKNOWN, do not claim science qualification. A narrowly defined *engineering exploratory Earth-only pilot* would require its own explicit decision and qualified scope, separate from scientifically validated data.
2. Freeze an **S3-specific** numeric metric contract *before any runtime*: setpoint serialization roundoff, native chemical closure/rounding, independent same-point run comparisons, finite Gibbs/density when supplied, phase-set differences between grid neighbors as observations, same-point new-phase disagreements as adjudications, nonconvergence and source-data gaps as FAIL/UNKNOWN; do not reuse S2 reference-fixed phase identities.
3. Derive resource limits by independently observing existing S2 manifest-member sizes and output sizes now; **peak RSS cannot be retroactively inferred from wall-clock times**. Any future pilot with `/usr/bin/time -v` or similar is a **new engine execution requiring separate authorization and write-once evidence**.
4. Define new S3 source/S2-provenance hash and write-once manifest with failure retention and per-cell identity; no actual S3 preflight/real engine call until the above gates and authorization.

**Governance remains** `D-024=ACTIVE`; `physical_T1=null`; `mechanical_solve_authorized=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

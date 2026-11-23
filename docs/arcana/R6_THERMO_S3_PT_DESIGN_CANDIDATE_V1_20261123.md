# ARCANA R6 — S3 P/T sensitivity: candidate design V1
2026-11-23. **DESIGN_ONLY / NOT RATIFIED / ZERO S3 ENGINE PROCESSES.** Machine-readable: `experiments/r6_thermo_provider_pilot_v1/s3_pt_design_candidate_v1.json`.

## Evidence
S2 Earth upstream 5 fresh Julia/MAGEMin + 5 fresh Perple_X processes and separate read-only native revalidation PASS. S2 tested executable source `632c4a570f876e3963b1dcd8a1f411a143fc8a59`; official S1 manifest `538c1b61f801c9902f8aa9b1b189b07ba38357eec339eb2b0211713f83299227`, S2 preflight `e96b52635d9755acd36ae9473c7a75c23eb8d1f0a2d80d384a6e09807a77f08b`, S2 REAL `74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604`. FAIR operator independently audited 68/68 manifest files and recomputed all S2 reported interprocess metrics at 0.0 observed differences. Never edit, rerun or overwrite any S1/S2 source-bound evidence. This proves *measured numerical repeatability*, not independent experimental accuracy.

## Scientific correction: original 25 shared points remain BLOCKED
The original science plan `docs/arcana/R6_THERMO_PROVIDER_SCIENTIFIC_STRESS_PLAN_20261122.md` proposed **one common 5×5 P/T** AFTER demonstrating matching composition, redox/H2O convention, thermodynamic dataset and phase model. S2 did NOT establish that crosswalk. MAGEMin custom uses `ig/tc_ds636` and its original 11-oxide input (sum 99.75 wt%) at 10 kbar/1100°C. Perple_X BL691 uses `hp62ver.dat`, `solution_model.dat`, a different molar bulk at 4000bar/1050K. **Do not attribute cross-provider differences to solver error or rank providers.** Proposed AMENDMENT for review is separate *provider-native* S3-A and S3-B screening; original common-source science stage remains deferred.

## Two candidate 5×5 experiments — NONE approved to run
| Track | Pressure grid | Temperature grid | Fixed input |
|---|---|---|---|
| S3-A MAGEMin | 8, 9, 10, 11, 12 **kbar** | 1000, 1050, 1100, 1150, 1200 **°C** | Original S2 `MAGEMIN_CUSTOM_IG`, `ig/tc_ds636` |
| S3-B Perple_X | 2000, 3000, 4000, 5000, 6000 **bar** | 950, 1000, 1050, 1100, 1150 **K** | Original S2 `PERPLEX_BL691_MEEMUM` |

Each matrix contains 25 *proposed* points; two matrices would be 50 distinct provider-native runs, not an original common 25-point comparison. Central anchors remain original S2 cases (10 kbar/1100 °C; 4000bar/1050K). **The numerical grids are proposed hypotheses, NOT documented database-calibration ranges.** Source-review before a grid is frozen may force changes.

Pinned upstream Perple_X original `test/bl691_MEEMUM/bl691_MEEMUM.dat` at `950d882bb6a9325a627109aa7154f7b526aa3087`, Git blob `3954964480612264838636fd394043aa0fef6324`, explicitly declares *problem definition* P from 500–10000bar, T from 873–1323K. The 25 candidate Perple_X points are strictly inside those declared bounds. These are NOT independently verified thermodynamic database validity or endmember-model calibration limits.

**Additional provenance gap:** the pinned `.dat` names `bl691_MEEMUM_perplex_option.dat` but the pinned upstream test directory lacks that file. The S2 wrapper copies only `bl691_MEEMUM.dat`, `bl691_MEEMUM_input.txt`, `hp62ver.dat`, `solution_model.dat`. Perple_X documentation specifies *default values if no option file is found*. This does not invalidate the measured S2 repeatability but does not establish the custom file or exact effective default options. For S3-B require pinned explicit effective-option policy, stdout confirmation, same source chemistry and no hidden working-directory files. Verify source and runtime before any experiment.

## S3 numerical / scientific test contract still to be frozen
1. Fixed source bulk per provider, solver/data/license pins and no silent oxidation/H2O/species conversion; track P in bar/kbar and T in kelvin/Celsius. Exact conversions: 1bar=100000Pa; 1kbar=100000000Pa; T[K]=T[°C]+273.15. Record original P/T and native returned setpoint with float-roundoff allowances distinct from scientific thresholds.
2. Per-point native solver status/iterations/residual, source-composition hash, stable phase names and fractions, measured density and Gibbs where the provider actually exposes them. Missing values are `NOT_AVAILABLE`, never approximated. Reconstruct oxide bulk chemistry when native phase compositions are available; Perple_X PRN molar reconstruction qualifies only at printed decimal-token precision.
3. **Phase sets may legitimately change across different P/T points**. Unlike S2, do not hardcode original 3/4 MAGEMin phases or original 6 Perple_X phases. Do not demand smooth phase modes across boundaries or compare G across distinct chemical standards. Same-P/T repeat disagreement, nonconvergence, invalid mass balance, unsupported species and domain violations trigger review or FAIL as predeclared.
4. Independently revisit index positions `(0,0),(0,4),(2,2),(4,0),(4,4)` in reverse order and fresh process, to assess same-point repeatability. Reverse scheduling alone **does not** test solver warm-start or path dependence; a separate documented warm-start API and experiment is required for that claim.
5. Before execution, freeze S3-specific error/tolerance policy, explicit model domain evidence, phase-agnostic parser, chemical closure, relevant independent physical/analytical anchor, negative tests and a measured S2-derived time/RAM/IO budget. No post-hoc threshold edits. Source-hashed new S3-only runner and preflight with NEW output ID, preserve failures, independent after-run audit. Old S2 runner and fixed-point parsers MUST NOT be repurposed unmodified.

## Current decision and blockers
`S3_PROVIDER_NATIVE_PT_DESIGN_CANDIDATE__NOT_READY_FOR_EXECUTION`.

Open gates: `MAGEMIN_IG_TCDS636_CALIBRATION_DOMAIN_AND_COMPOSITION`; `PERPLEX_BL691_HP62VER_VALIDITY_AND_EFFECTIVE_OPTIONS`; `S3_PHASE_AGNOSTIC_VALIDATOR_AND_NEGATIVE_TESTS`; `S3_PREDECLARED_TOLERANCES`; `S3_TIME_MEMORY_IO_BUDGET`; `S3_ISOLATED_SOURCE_BOUND_PREFLIGHT`; `SEPARATE_S3_REAL_AUTHORIZATION`. Cross-provider comparison stays `CROSS_PROVIDER_SCIENCE_INCOMPARABLE`. `D-024=ACTIVE`, `physical_T1=null`, `mechanical_solve_authorized=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

Checked references:
- MAGEMin database scope: https://computationalthermodynamics.github.io/MAGEMin_C.jl/stable/database
- MAGEMin native P/T input: https://computationalthermodynamics.github.io/MAGEMin_C.jl/stable/MAGEMin_C/examples
- Pinned Perple_X problem: https://github.com/jadconnolly/Perple_X/blob/950d882bb6a9325a627109aa7154f7b526aa3087/test/bl691_MEEMUM/bl691_MEEMUM.dat
- Perple_X default options: https://www.perplex.ethz.ch/perplex_options_body.html

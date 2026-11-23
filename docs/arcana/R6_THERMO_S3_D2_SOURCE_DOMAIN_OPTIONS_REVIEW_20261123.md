# ARCANA R6 THERMO S3 — D2 source-domain and Perple_X option review

**Date:** 2026-11-23. **Decision:** `S3_D2_SOURCE_MODEL_IDENTITY_AND_PROBLEM_BOUNDS_REVIEW_PASS__SCIENTIFIC_CALIBRATION_AND_EFFECTIVE_RUNTIME_OPTIONS_OPEN`.

This review compares the already source-pinned ARCANA S2 upstream Earth input and the S3 **non-executable** candidate. It **does not qualify S3 runs or the whole 5×5 calibration envelope**.

## Original provider identities (source-supported)

- MAGEMin source `632c4a570f876e3963b1dcd8a1f411a143fc8a59` original fixed custom input `ig` and `tc_ds636`; Julia MAGEMin_C v2.4.5. The developers describe `ig` as the corrected **Green et al. (2025)** igneous activity-composition model replacing the old Holland et al. (2018) set, with **TC data release 6.36** for G25. Source: https://hpxeosandthermocalc.org/the-hpx-eos/the-hpx-eos-families/hpx-eos-igneous-sets/ . The original custom demonstrator chemistry is an upstream *example*, not a measured or proven full P/T-X validity domain. MAGEMin documents explicit finite P/T/bulk validity; no full calibration envelope was established for the candidate grid. Source: https://computationalthermodynamics.github.io/MAGEMin_C.jl/stable/database .
- Perple_X source tag v7.3.3 commit `950d882bb6a9325a627109aa7154f7b526aa3087`, original BL691 `hp62ver.dat`, `solution_model.dat`; Perple_X data documentation identifies `hp62ver.dat` as the **TC-DS620** version of Holland & Powell (2011), as used by Green et al. (2016). Source: https://www.perplex.ethz.ch/perplex_thermodynamic_data_file_body.html . This is **not** TC-DS636 and not the same full chemical model as MAGEMin's `ig`; cross-provider scientific equivalence remains blocked.
- Pinned original `test/bl691_MEEMUM/bl691_MEEMUM.dat` blob `3954964480612264838636fd394043aa0fef6324` lists problem extents P=500–10000 **bar**, T=873–1323 **K**. Proposed S3-B 2000–6000 bar ×950–1150 K lies within these **declared problem limits only**; no independent proof of calibration at all 25 points.
- Perple_X source problem references `bl691_MEEMUM_perplex_option.dat` but pinned upstream `test/bl691_MEEMUM` directory does not contain it. The original S2 wrapper only copies `bl691_MEEMUM.dat`, `bl691_MEEMUM_input.txt`, `hp62ver.dat`, `solution_model.dat` into each **new workdir**; no custom options file supplied. The vendor states absent option files cause built-in defaults, and that effective values are emitted to console; `option_list_files=T` can emit a separate options report if explicitly enabled. Source: https://www.perplex.ethz.ch/perplex_options_body.html . Thus default-fallback is the documented expected behavior, but **the exact effective values for the previous S2 runs have not been read back from all official stdout logs and remain `NOT_ATTESTED`**. No rewrite of old evidence.
- A public validated example at another P/T or composition is not a blanket valid-envelope certificate for this exact S3 input. The published Green G25 model identity is source-supported; the proposed 25-point grid remains a hypothesis, not a proven calibration range.

## Consequences for the S3 study

1. Original common-composition cross-provider comparison (one common 25-point grid) requires independently sourced common bulk (identical oxide moles, O2/FeO/Fe2O3/H2O/redox stoichiometry), identical/explicitly mapped reference potentials, compatible solution model differences, phase identification, and P/T. **Unmet.** Separate candidate provider-native 25-point studies are only a staged engineering/sensitivity alternative, not fulfillment of original common-database comparison.
2. **D2-A:** MAGEMin candidate 8–12 kbar and 1000–1200°C cannot be ratified solely because all points are close to the original 10 kbar/1100°C. Need experimental/model validity evidence for this composition, not just successful solver convergence.
3. **D2-B:** Perple_X BL691 source rectangle and valid input syntax do not demonstrate predicted phases/kinetics/calibrated data. Avoid using old S2 fixed six-phase names as pointwise truth at new P/T.
4. **D2-B OPTIONS NEXT:** run a **read-only forensic audit** of the already stored ten S2 process folders, especially all five `PERPLEX_XX/BL691_MEEMUM/RUN_STDOUT.log` and `PERPLEX_XX/LAUNCH_STDOUT.log` under the SEALED `R6_THERMO_S2_REPEATABILITY_NEW01` root. SHA-verify the S2 REAL manifest `74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604` first. For each Perple_X process, verify that the referenced option file was **not** present in the actual input workdir, and record any console lines identifying option file/defaults. If the logs do not prove values, state `EFFECTIVE_OPTIONS_NOT_ATTESTED`, not PASS by inference. Leave all files untouched.
5. **D3 source-only can proceed in parallel:** pure `s3_design_contract.py` and mutation tests block unsafe changes to candidate grids, S2 provenance, P/T units, exact upstream chemistry and physical authority. These tests do not qualify S3 domain or scientific results. They do not run Julia or MEEMUM.

## Remaining gate checklist

```text
S3_D2_PROVIDER_MODEL_IDENTITY = SOURCE_CONFIRMED
S3_D2_PERPLEX_BL691_INPUT_RECTANGLE = SOURCE_CONFIRMED_NOT_CALIBRATION
S3_D2_MAGEMIN_G25_ALL_25_CALIBRATED = UNKNOWN
S3_D2_PERPLEX_HP62_ALL_25_CALIBRATED = UNKNOWN
S3_D2_PERPLEX_EFFECTIVE_OPTIONS_S2_ARCHIVE = NOT_ATTESTED
S3_SHARED_CHEMISTRY_CROSSWALK = NOT_QUALIFIED
S3_REAL_PROCESSES = 0
D-024 = ACTIVE
physical_T1 = null
mechanical_solve_authorized = false
WORLD_HISTORY_PRODUCTION_AUTHORIZED = false
```

Scientific authority remains unchanged. No S3 runner, S3 write-once preflight, engine runs, or original ARCANA mineral assignments authorized.

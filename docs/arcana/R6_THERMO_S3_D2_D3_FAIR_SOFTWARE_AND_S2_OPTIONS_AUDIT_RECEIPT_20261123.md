# ARCANA R6 — S3 D2/D3 FAIR source-only software and S2 Perple_X option fallback receipt
Date: 2026-11-23. This is user-operated FAIR terminal evidence and GitHub documentation review, not a direct GitHub copy/readback of FAIR raw bytes. **No S3 thermodynamic engine execution** or S3 official evidence manifest produced.

## Verified S3 D3 source and software test gate
- Existing, separate FAIR detached worktree: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_THERMO_S3_DESIGN_VERIFY`.
- Tested source commit: `591271f73c57d71b593ce1bbf216774ada5bc260` on `r6/thermo-s3-pt-design-20261123`; this is the **exact** code identity of the test results, **not** any subsequent docs-only commit.
- Source-only pytest command: `python -m pytest -q -ra --tb=short tests/test_r6_thermo_s3_design_v1.py` with `arcana-r6-linux`, `PYTHONPATH=$PWD/src:$PWD`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`.
- User-reported FAIR output: `36 passed in 0.08s`, `S3_D3_SOURCE_TESTS_PASS`, `S3_D3_TEST_EXIT=0`. This validates the proposed policy guard (chemistry/provenance, units, 5x5 axes, blockers, non-executable and governance) **only as software**; not 25+25 real equilibrium cases, phase-change parsing or calibration domain.
- No change to S2 tested code `632c4a570f876e3963b1dcd8a1f411a143fc8a59` or its archives.

## S2 original Perple_X effective option investigation — read-only
- Operator verified sealed `R6_THERMO_S2_REPEATABILITY_NEW01/MANIFEST.json` SHA256 `74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604` (`S2_ORIGINAL_MANIFEST_PASS`).
- For `PERPLEX_01` through `PERPLEX_05`, actual workdirs showed `CUSTOM_OPTIONS_PRESENT=False` and `DEFAULT_OPTIONS_FILE_PRESENT=False`, and each preserved `RUN_STDOUT.log` produced **67 relevant regex matches**. Each includes a Perple_X warning that `bl691_MEEMUM_perplex_option.dat` was not found and that **default option values will be used**. Thus default-fallback selection is positively evidenced for **all five S2 runs**, not just inferred from Perple_X documentation.
- In all five excerpts captured by the operator (first 30 regex-matching lines per file), the same effective visible entries are reported: `refinement_points=12` (resolved from `auto`); `solvus_tolerance_II=aut`; `initial_resolution=0.2000`; `refine_endmembers=F`; `solvus_tolerance=aut`; `function_tolerance_exp=0.8`; `option_list_files=F`; `do_not_reset_options=F`. Local `cAmph(G)` and `Augite(G)` options visible as `F`.
- `LAUNCH_STDOUT.log` generated zero matches per process; the relevant Perple_X options are in `RUN_STDOUT.log`. The read-only audit script had checked the SHA256 of each listed log against its original immutable S2 manifest, not just its filename.
- Limitation: because only the first 30 of 67 matching lines per process were printed, the user transcript **does not prove every option keyword/value and every local model option match across all five**. Decision: `S3_D2_S2_PERPLEX_DEFAULT_FALLBACK_EVIDENCED_5_OF_5__FULL_OPTIONS_VECTOR_COMPARISON_PENDING`. Do not replace this with `ALL_OPTIONS_HASH_EQUAL` without an additional read-only full-section comparison. Never rewrite S2 logs or retroactively claim custom options.
- `S3_D2_S2_OPTIONS_LOG_READONLY_AUDIT_PASS` is an upstream stored-log read; **no new thermodynamic process ran**.

## Next bounded actions
1. On FAIR, read-only verify exact sealed S2 MANIFEST + every referenced Perple_X stdout hash and compare the **entire** computational settings section and all local-option data across five runs (or compare full `RUN_STDOUT.log` bytes first). If full logs are equal byte-for-byte, report `S3_D2_PERPLEX_ALL_FIVE_STDOUT_BYTE_IDENTICAL`; else compare complete options sections and declare unequal/unknown fields explicitly, never silently normalize differences.
2. Proceed with **S3-specific phase-agnostic native output parser and comprehensive negative tests**, rather than reusing S2's fixed 3/4 MAGEMin and six Perple_X phase set assumptions. Source-only tests first. Distinguish P/T cross-point phase transitions from same-P/T process divergence.
3. Remain blocked on scientific P/T-X calibration validity for both provider-native 25-point candidates. No new S3 preflight/engine, no common-chemistry cross-provider ranking.

Governance: `D-024=ACTIVE`, `physical_T1=null`, `mechanical_solve_authorized=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. No original ARCANA T0 geology/Deep/resources/biomes affected.

# ARCANA R6 — S3-D3 read-only FAIR native reader qualification: 60 targeted software tests + historical S2 native readback

**Date:** 2026-11-24. **Decision:** `S3_D3_SOFTWARE_NATIVE_READBACK_PASS__HISTORICAL_S2_ANCHORS_ONLY`. This is user-operated FAIR output recorded by the ledger author; the GitHub-side review did **not** directly access or rehash FAIR raw files, and did **not** run Julia or Perple_X.

## Source and tested environment

- Tested EXACT GitHub source SHA: `9a9c996b909d7752114165f7f036ebf2b00fb966` (S3 parser source), detached FAIR worktree `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_THERMO_S3_DESIGN_VERIFY`; existing `arcana-r6-linux` with `PYTHONPATH="$PWD/src:$PWD"`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`.
- Targeted test command: `python -m pytest -q -ra --tb=short tests/test_r6_thermo_s3_design_v1.py tests/test_r6_thermo_s3_native_readback_v1.py`.
- Operator FAIR output: `60 passed in 0.12s`; `S3_D3_SOURCE_AND_NATIVE_READBACK_PASS`; `S3_D3_FINAL_EXIT=0`; exact `SOURCE_SHA=9a9c996b909d7752114165f7f036ebf2b00fb966`.
- These are 36 source/design-policy tests plus 24 new phase-agnostic parser tests; synthetic test cases are NOT a scientific treatment of actual P/T phase boundaries or measured experimental accuracy.

## Original S2 immutable source readback

- Operator read **existing, unchanged** `R6_THERMO_S2_REPEATABILITY_NEW01/MANIFEST.json` and enforced SHA256 `74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604`, then SHA256-checked two original S2 **member files** against the manifest's `files_sha256`: `MAGEMIN_01/NATIVE.toml`, and `PERPLEX_01/BL691_MEEMUM/bl691_MEEMUM.prn`.
- S3 source-only `read_magemin_case` parsed original S2 `MAGEMIN_CUSTOM_IG` at P=10 kbar, T=1100 °C. `MAGEMIN_S3_READER_PHASES=3`. Native reconstructed component maximum absolute delta `1.9984014443252818e-15`; source-to-native composition maximum absolute delta `5.551115123125783e-17`. These are *normalized component fraction closure residuals*, **not measured thermodynamic model error**.
- S3 source-only `read_perplex_prn` parsed original S2 Perple_X BL691 at P=4000bar, T=1050K. `PERPLEX_S3_READER_PHASES=6`; `PERPLEX_PRINTED_COMPONENTS=10`. Its bulk chemistry was checked against phase mol×oxide values using original report **decimal token rounding intervals**, not high-precision chemistry closure.
- Both native readers returned explicit `...S3_SCIENCE_UNQUALIFIED` statuses, confirming no physical/model promotion. Original S2 full 68-member independent read-only audit and five+five repeatability remain separate historical evidence.
- This D3 test qualifies schema-independent *phase-count/phase-name reading capability and S2-anchor native readback*, **not** physical validity of any other P/T point, proof of actual phase transitions, sufficient convergence near phase boundaries, cross-provider chemical equivalence, or release of the original world simulation.

## Existing D2 result retained

The separate user-operated S2 original five-Perple_X-log byte comparison closed D2 recorded-console option parity: every `RUN_STDOUT.log` SHA256 `5b53581fc32cdbc4bf9b4759f888ae7d402230c47818d409e4680477e46d54f7`; the full extracted settings blocks each SHA256 `423b99d38cc0425860f2aa0c6f9d8a362f7e777ed4ba23c164a593161411634b`; default fallback 5/5. No new thermodynamic run.

## Next gate: S3-D4 science-calibration and acceptance-contract **design only**

1. Independently source a documented calibration/applicability envelope in P, T, oxide composition, oxygen/redox/H2O and melt/mineral phase models for original exact MAGEMin `ig/tc_ds636` G25 chemistry. For Perple_X BL691 `hp62ver.dat`/solution models, distinguish original problem rectangle from dataset+phase model actual calibration and stability validity. Record source-specific supported, unsupported and UNKNOWN matrix cells. If unsupported/unknown, revise candidate grid or set no-run.
2. Distinguish a **provider-specific Earth-reference** phase diagram/sensitivity study from the original **shared 25-point common-chemistry** comparison; the latter remains blocked on same-source independent chemistry and database/model crosswalk.
3. Freeze numerical rules *before* engine runs: iterative convergence, component-wise bulk closure, phase wt. precision, source setpoint roundoff, same-point fresh-process 5 rechecks, Gibbs/density availability, phase-boundary flagging/repeat precision and nonconvergence handling. Old S2 closure tolerances are separate sanity checks, not universal S3 scientific uncertainties.
4. Read-only extract S2 exact observed launch-time/resource telemetry from hash-guarded original members and choose a bounded S3 compute/IO budget. Propose **new** source-only S3 preflight and write-once manifest schema only after scientific-domain adjudication and explicit separate authorization. Do not retarget frozen S1/S2 evidence or execute their runners.
5. Do not claim S3 model/scientific preflight approved by the D3 software PASS.

## Governance

`D-024=ACTIVE`; `physical_T1=null`; `mechanical_solve_authorized=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. ARCANA original rock/material selection and historic Deep/resource/biome generation remain unauthorized.

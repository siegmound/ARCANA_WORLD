ARCANA WorldSim v0.6D1-R4.32-R1 — diagnostic overlay

Purpose:
- preserve the failed live R4.32 run;
- inspect J14/J18/J21 Geonomics parameter-manifest static validation;
- identify missing mapping classes, missing referenced files, hash mismatches,
  path-resolution ambiguity, and explicit false static flags;
- do NOT run Geonomics, do NOT execute numeric targets, do NOT readjudicate,
  and do NOT modify canonical state.

Apply this overlay at the project root and run:
  .\run_v0_6D1_R4_32_R1_diagnostic.ps1

Generated report:
  outputs\v0_6D1_R4_32\R4_32_R1_GEONOMICS_STATIC_VALIDATION_DIAGNOSTIC.json

# ARCANA WorldSim — v0.6D1-R0 Status

## Verdict

`PASS_RECOVERY_AUDIT_WITH_PARTIAL_RAW_SURVIVAL_AND_EXECUTABLE_HISTORY_STILL_MISSING`

`FULL_210_TO_0_MA_HX = NOT_AUTHORIZED`

## Recovery summary

- known historical exact hashes locked: 5;
- exact historical packages found in current mounted runpacks: 0/5;
- original D2 package hash: not recovered from surviving records;
- local downstream support targets found: 3/3;
- D2.T core byte artifacts found: 0/3;
- major D2.2 RAW products documented: 12;
- standalone D2.2 RAW File-Library references recovered: at least 4/12;
- pre-CHA1 D1/D2 executable source: not found;
- exact D1 metadata surface: recovered downstream;
- real D2.2 -> D3.0A boundary: recovered downstream.

## What R0 proves

The project retains enough evidence to verify much of the original biological history and the CHA-1 bottleneck, but not enough executable/state authority to run the historical Deep-ON 210->66 Ma replay without reconstruction.

## Governance

- name-only file matches are not authority;
- historical packages with recorded hashes require SHA-256 exact match;
- RAW outputs are valid evidence/state only when their bytes are recovered;
- summaries are evidence, not simulation state;
- no fake D3 @ 210 Ma;
- no reconstruction of missing D1/D2 population grids from D3-era geometry;
- no original-H0 claim if a new runtime must be built.

## Tooling

`scan_v0_6D1_R0_windows.ps1` + `scripts/scan_arcana_historical_artifacts.py` recursively scan local archives and inspect ZIP member names without extraction. Exact package hashes are reported separately from name-only/raw hits.

## Verification

- complete inherited + R0 test suite: **37/37 PASS**;
- R0 formal recovery audit: **18/18 PASS**;
- current-session mounted scan: 0 exact historical packages, 3 support targets, no production HX authorization.

# R6-INT10K E0/E1 hash reconciliation (2026-10-29)

## Decision

`R6_INT10K_E0_WINDOWS_HASH_RECONCILIATION_PASS__E1_R1_LINUX_TESTS_PASS_REPORTED__E1_INPUT_RECHECK_PENDING`

This closes the Windows-side byte reconciliation only. It does not independently authenticate FAIR files, rerun the original E0 loader on FAIR, execute the E1 reference, or authorize a numerical run.

## Windows byte verification

The original input directory and transfer bundle named by the existing Windows operator attestation were available locally. Windows SHA256 was recomputed for each file and for the original tar.gz bundle. The tar contained exactly three root-level regular-file members; each decompressed member was byte-identical to its corresponding original Windows input.

| Windows original | Bytes | Independently computed SHA256 | Bundle member |
|---|---:|---|---|
| `RESULT.json` | 1,653,469 | `24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5` | byte-identical |
| `MANIFEST.json` | 969 | `a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21` | byte-identical |
| `RESULT.json.sha256` | 78 | `8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0` | byte-identical |
| Bundle `MATERIAL_RHEOLOGY_PROVIDER_20261025_03.tar.gz` | 113,004 | `fc5cda6e543f5f96673ba71e60c085566659672abff9728eb5ed74c2ab47c8b0` | — |

The manifest's result and sidecar paths, SHA256 values and byte lengths match the corresponding files. The sidecar text names `RESULT.json` and contains its full digest. This was verified locally; the matching FAIR bundle/member values are operator-reported from the FAIR evidence process and were not downloaded or independently rehashed on Windows.

## Digest discrepancy and historical evidence

The complete SHA256 of the Windows `MANIFEST.json` is 64 hexadecimal characters: `a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21`. The 52-character value supplied as the historical erroneous record is `a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc21` and is not a valid SHA256 digest.

Inspection of the current tracked E1 CLI and Windows attestations found that they already contain the complete 64-character digest; the 52-character string is absent from tracked files. Accordingly, no digest literal needed correction in this checkout. The historic discrepancy reported by the operator is preserved here rather than rewriting the original E0 attestation or FAIR evidence. The E1 verifier has been strengthened to reject malformed pins and to validate all three file identities plus manifest/sidecar closure before and after a reference call.

The complete `source_identity` object from the prior Windows loader operator report is recorded in [the corrective machine attestation](qualifications/R6_INT10K_E0_E1_HASH_RECONCILIATION_20261029.json). Its loader-derived fields remain provenance from that earlier operator-reported run; this reconciliation independently verifies the input bytes but does not rerun that loader. Existing E0 PASS decisions therefore remain historical and are not silently revised. The next FAIR gate must rerun the original pinned loader against the complete input triplet and record the full identity.

## E1-R1 and failed first test attempt

The operator reports E1-R1 commit `a7b7d4d58d3cc545781778a985529c269a81b9b9` passed 35 Linux tests, compilation, checkout immutability checks and hash checks for its log/JUnit. Evidence directory: `INT10K_E1_R1_TEST_3MXk3VwX`. These results and checksums are operator-reported; the FAIR files were not imported or rehashed on Windows.

The earlier first E1 Linux suite result remains an immutable operator-reported FAIL: 24 passed, 2 failed, exit 1, at `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT10K_E1_TEST_dMJckvUN`. Both failures were direct/checkpoint coverage cases `[3-1]` and `[10-5]`; the original E1 coverage defect was corrected separately. No failed evidence was overwritten or reclassified.

## Local validation and next gate

Windows focused tests cover the full E1 hash-pin format, malformed SHA256s (including 52-character input), all three member identities, manifest/sidecar consistency, and the existing direct/checkpoint coverage/regressions. Run the combined E1, regional and unified suite plus `py_compile` and `git diff --check` on the reviewed source before committing.

On FAIR, first revalidate the original loader and complete E0 triplet against the exact source commit. Then run the corrected commit's test suite and preserve it in a new evidence directory. Only after both pass may a distinct supervised three-year reference be considered. No E0 loader invocation or numerical evolution was performed during this reconciliation. The E1 runner remains limited to 3/10 years; do not run 10,000 years.

`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`.

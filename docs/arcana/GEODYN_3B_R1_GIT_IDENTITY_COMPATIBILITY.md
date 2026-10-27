# GEODYN-3B-R1 — Git identity compatibility repair

**Date:** 2026-10-27
**Baseline:** `e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa`
**Decision:** `GEODYN_3B_R1_GIT_IDENTITY_COMPATIBILITY_LOCAL_PASS__GEODYN_3C_FAIR_PENDING`

## Change

`RunIdentityClaim` now accepts exact lowercase hexadecimal Git object IDs of either 40 or 64 characters for `solver_source_commit`, `repository_commit`, and `adapter_commit`. The original strings are preserved byte-for-byte; the implementation does not pad, hash, truncate, or infer/authenticate the object algorithm from length. `configuration_sha256` and every `input_identities` value remain strictly 64-character lowercase SHA256 values. The schema and deterministic identity formula are unchanged.

When available, the caller may preserve the declared algorithm in the existing string-valued `declared_provenance` map using `solver_source_commit_algorithm`, `repository_commit_algorithm`, and `adapter_commit_algorithm`. These declarations remain unauthenticated caller claims. The test fixture carries the exact reported ASPECT commit `30eb77ee5da186137d436dbad35c6cb3cab64b69`, GEODYN-2A-R1 adapter commit `1fd5e8d8f21e28876da9ef89423755615efc6162`, and GEODYN-3B baseline commit `e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa`.

## Verification

Windows Python focused archive + ASPECT-reader suite: **69 passed, 2 skipped**. Both skips are the existing external-symlink tests because Windows denied symlink creation with WinError 1314; the Linux handoff requires all 71 collected tests to run with zero skips. `py_compile` and `git diff --check` passed. The tests cover SHA-1 and SHA-256 Git IDs, rejected lengths 39/41/63/65, uppercase/non-hex rejection, strict configuration/input SHA256 validation, real commit strings in the typed identity payload, retained algorithm declarations in the manifest, deterministic IDs/manifest under source relocation, and existing query/manifest/integrity/finalization and reader regressions.

The first test attempt failed because the existing provenance schema requires values to be strings and rejected a nested algorithm map. That test-fixture/schema compatibility issue was corrected by using three flat provenance fields; the schema was not broadened. The successful run followed that correction.

## GEODYN-3C handoff status

The qualification launcher now accepts the exact reviewed implementation SHA-1 through `GEODYN3C_EXPECTED_COMMIT`, verifies its parent is the GEODYN-3B baseline, and validates the real ASPECT, R1 adapter, and GEODYN-3B commit strings in their actual typed fields. It requires explicit `sha1` declarations in caller provenance and makes no 64-character Git-ID workaround. The expected Linux focused suite is 71 passed, zero failed, zero skipped.

This is only local code/test readiness. No FAIR files were read, no original source inventory or run-claim bundle was imported, no FAIR test ran, and no ASPECT process ran. The historical `configuration_sha256`, `input_identities`, inventory digests, attempt ID and time-unit source must still be recovered from preserved evidence. If any cannot be recovered exactly, GEODYN-3C is BLOCKED; do not create replacements. No compatibility migration is needed for existing archives because the schema and identity formula are unchanged, and there is no evidence here that an older sealed archive exists with altered values.

`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false` and `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false` remain unchanged.

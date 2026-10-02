# ARCANA WORLD — C0-F2 High-Confidence Data Cleanup

**Decision:** `PASS_C0_F2_HIGH_CONFIDENCE_DATA_CLEANUP_READY_FOR_REVIEW`

**Branch / base:** `r6/pre-b0-data-consolidation` / `0c15bf8de6a6002a49a64b85f3913a98024dffba`
**Scope:** only the two high-confidence families identified by C0-F1. No commit or push.

## Result

| Family | Removed | Bytes | Retained physical counterpart |
|---|---:|---:|---|
| `SIMULATION_RESULTS` catalogued copies | 863 | 372,078,719 | Every `OriginalRelativePath` in both retained manifests |
| `outputs/**/pytest_tmp` generated fixtures | 182 | 1,829,781 | No scientific counterpart required; tracked test producers recreate fixtures |
| **Total** | **1,045** | **373,908,500** | |

The 863 catalogued paths are exactly the `ConsolidatedPath` values of the 863
rows in `SIMULATION_RESULTS/MANIFEST.json` and `MANIFEST.csv`. Before deletion,
all 863 source/destination pairs existed and were byte-identical; every
`OriginalRelativePath` existed, `CopyVerified` was true, and no source path was
removed. After deletion, all 863 original paths still exist. Each manifest
continues to record the copied artifact's source, stage, filename, size, SHA256,
historical consolidated path, and copy-time verification. The
`ConsolidatedPath` is now a historical consolidation location; the extant
`OriginalRelativePath` is the retained payload location. The manifests and
semantic catalogue were not rewritten.

Of the 863 manifest SHA values, 223 match the present source bytes directly;
the other 640 match after canonicalizing CRLF/LF line endings (639 JSON and one
CSV). None is unmatched. This is consistent with the C0-F1 checkout line-ending
finding; it does not indicate source/copy disagreement. The source/copy byte
equality was checked before removal.

The 182 pytest files were all tracked files below `outputs/` with a
`pytest_tmp` path component. They total 1,829,781 bytes and are now absent.
C0-F1 identified their tracked `tmp_path` test producers and found no current
R6 consumer or hard-anchor role. Some R4 evidence records describe fixture
paths or fixture contents; those records remain. No `outputs/**/PREPATCH*`
source/test evidence was removed.

## Reference and identity audit

- Exact candidate-path search across current R6 root artifacts, `src/`,
  `scripts/`, `tests/`, `docs/arcana/`, `contracts/`, and `authority/` found no
  direct file-level consumer or required builder/test path.
- The generated `ARCANA_EXECUTION_REFERENCE_INDEX.json` contains 501 of the
  deleted consolidated paths. These are stale index citations, not active
  consumers. The index and its pinned historical identities were not changed
  in this wave. General historical references to the `SIMULATION_RESULTS`
  catalogue remain in documentation and qualification records.
- The retained manifests preserve run/stage identity and both source and
  historical consolidated paths. The original payload location is retained for
  every removed catalog copy. No new indirection scheme was introduced.
- The seven nested test files under `outputs/**/PREPATCH*/tests/` were audited
  and retained. Six differ from the same-named root test and preserve distinct
  prepatch source states; one matches its root counterpart byte-for-byte but
  remains part of the recorded prepatch snapshot. No physical nested test was
  removed. Consequently accidental pytest collection remains a deferred
  discovery/configuration issue rather than being hidden by deleting evidence.

| Retained nested path | SHA256 | Root test byte-identical? |
|---|---|---|
| `outputs/v0_6D1_R4_37_R2/PREPATCH/tests/test_r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run.py` | `455cbcdd774dfeca539826c16851ff34a680fbb5b1ca6fd829fa87aaee9b72cf` | No |
| `outputs/v0_6D1_R4_37_R3/PREPATCH/tests/test_r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run.py` | `4f87a0a5ecd92ccd31d333c83956f59b97139b2ac4138602da20db03b08dd56a` | No |
| `outputs/v0_6D1_R4_39_R2/PREPATCH_SOURCE/tests/test_r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py` | `b90eb652aa2d597af059deb633d45c82c39151e1a5813530ccc00f7eceaf0757` | No |
| `outputs/v0_6D1_R4_39_R3/PREPATCH_SOURCE/tests/test_r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py` | `e1dea8cbca23516e1d36a8a3e783b7f4f0d40561abf7949b00b00a94bdc0a1fd` | No |
| `outputs/v0_6D1_R4_39_R4/PREPATCH_SOURCE/tests/test_r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py` | `0c6063d958dfc64010c417d11e9e9dcee3ea19d003a880386a2292d709dfe852` | No |
| `outputs/v0_6D1_R4_39_R5/PREPATCH_SOURCE/tests/test_r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py` | `7152e5103123cb47b00464c05cc2ad66bfa9474ceb22c1cd7b71c273d2961141` | Yes |
| `outputs/v0_6D1_R4_42_R1/PREPATCH_SOURCE/tests/test_r442_geonomics_multi_transition_bounded_replay_production_queue_authorization.py` | `d0b00a3c20f64f7853ca5d3bf1c92e92909aa4b693cb8e9f6b2402455ca47397` | No |

## Validation

- R6-focused suite: **252 passed**.
- Normal full pytest invocation: collection stopped with **27 errors**; no test
  bodies ran. Post-cleanup `--collect-only` reported **1,613 tests collected,
  27 errors**, unchanged from the measured pre-cleanup collection result.
  The seven nested `outputs` test collection errors remain because their
  evidence files were retained. An older stated baseline of 26 errors differs
  from the measured pre-cleanup result of 27; this cleanup introduced no change.
- Both SIMULATION_RESULTS manifests parse and contain 863 rows. All rows retain
  extant originals, all copy-time `CopyVerified` values are true, and all
  recorded hashes match raw or line-ending-normalized retained content.
- Tracked worktree paths: **49,327 total**, **48,282 present**, **1,045 absent
  by this cleanup**. Present tracked logical bytes: **2,758,633,130**.
- Present `outputs/`: **2,009,545,027 bytes**; present
  `SIMULATION_RESULTS/`: **1,002,341 bytes**; present `local_runs/`:
  **113,105,603 bytes**.
- Exact current R6 file-level consumer scan: **zero**. Stale execution-index
  citations: **501**.
- `git diff --check`: recorded after this report is written.

## Deferred and protected

- Other exact-hash duplicate groups remain `MEDIUM_CONFIDENCE`: up to 33,433
  additional participant paths and 907,231,585 bytes of theoretical
  one-copy savings. No such path was removed.
- The two protected R5 authority CSVs remain untouched:
  `R5_17_B7_A3F2_P7C_CO2_SNAPSHOT_BINDING.csv` and
  `R5_17_B7_A3F2_P7T_TEMPORAL_SNAPSHOT_REGISTRY.csv`.
- R5.2/R5.3 attempts, blocked RangeShiftR evidence, unique engine outputs,
  current R6 authority/runtime payloads, references, hard anchors, and all
  nested prepatch tests remain untouched.
- `SIMULATION_RESULTS/README.md` and the manifests describe the original
  consolidation snapshot. This report records the later catalogue-only
  physical layout; the scientific/provenance records themselves were not
  rewritten.

## Worktree accounting

Only these 1,045 tracked payload paths were deleted. The F1 audit report remains
unmodified. This F2 report is the sole new file; there are no unexpected
untracked files. No files were staged, committed, pushed, cleaned, or regenerated.

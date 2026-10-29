# R6-INT10K E2-A1 — Full-history oracle implementation

**Decision:** `E2_A1_FULL_HISTORY_ORACLE_WINDOWS_PASS__STREAMING_AND_FAIR_PENDING`
**Source checkout:** `r6/multiphysics-integration-20261026`, baseline commit `662bed019bdd83832a8170bb1638cc1fc783295b`
**Classification:** `NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY`

## Scope

E2-A1 adds a separate, versioned `FULL_HISTORY_ORACLE_V1` capture and verification path. It leaves the E1 `ARCANA_R6_INT10K_SHORT_REFERENCE_V1` schema and all physical operators unchanged. The implementation calls the existing `run_regional_segment()` for a direct run, a prefix run ending at the actual split, and a continuation from that prefix's actual checkpoint. It preserves each complete returned object, including regional snapshots and year records/events/balances, unified step records, final states, accumulators and checkpoint envelopes. The prefix checkpoint is captured from the real prefix execution; it is not reconstructed from the final state.

The oracle stores three complete cases: `direct`, `split_prefix`, and `split_resumed`. Its deterministic run identity binds source identity, numerical configuration, tolerance, schema and implementation provenance. An independent UUID identifies the attempt. Canonical JSON SHA256 detects accidental alteration; it does not authenticate the producer. A separate manifest lists the oracle and run report with byte lengths and SHA256. The manifest is published last. A failed write can leave a new partial directory without a completion manifest; no prior output is overwritten.

The exact-history comparison requires identical structure, order, identifiers, events and checkpoint state. Finite numerical leaves use the existing E1 tolerance (`abs=1e-8`, `rel=2e-14`). Only `subsurface_unified_result.configuration.segment_external_step_count` is excluded from direct-versus-resumed equality because it describes each invocation's local segment length; its expected value and all elapsed/global step counts are validated separately. The split prefix is independently required to cover regional records 1..split, snapshots 0..split and unified steps 1..split. Checkpoint digests, source binding, checkpoint/frontier times and checkpoint records are verified.

`query_history()` indexes and returns only archived regional snapshots, regional year records and unified step records. It supports native exact-time or inclusive-range selection and filters by domain, cell/position, support and material identity. It reports `TIME_NOT_ARCHIVED` or `NO_MATCH` when applicable and always declares `interpolated: false`. It returns no synthetic state for a missing timestamp.

## Inputs and provenance

The E0 payload directory was read-only. Windows independently rechecked the three pinned member hashes with `verify_source_bundle()` before and after each capture:

| Input | SHA256 |
|---|---|
| `RESULT.json` | `24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5` |
| `MANIFEST.json` | `a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21` |
| `RESULT.json.sha256` | `8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0` |
| Windows E0 transfer tar | `fc5cda6e543f5f96673ba71e60c085566659672abff9728eb5ed74c2ab47c8b0` |

The original source archive identity retained by the E0 payload is `7dda60c8fa1f535d9e257eb2d04fdfde4643a92765eca8631bd766058240d8cb`. Both supports are C028/C029 with the recorded 73-node T0 state identities. The run report binds implementation commit `662bed...` and SHA256 for the CLI, oracle module and six runner/kernel/provider modules. The two new implementation files were untracked at capture time; their exact byte identities are recorded in each oracle. Thus the run is not represented as having executed a committed implementation revision.

The local environment was Python 3.12.10 / NumPy 2.5.1. The earlier FAIR E1 runtime was Python 3.12.10 / NumPy 2.3.5. Windows did not import the FAIR E1 reference files, so this work does not claim byte-for-byte or cross-runtime numerical equality against those operator-reported outputs. It demonstrates same-runtime direct/restart full-history parity and independently revalidated E0 input hashes.

## Local numerical captures

Final reviewed bundles are outside the Git repository at:

`F:\\corsiiiuu\\Magistrale\\Arcana\\ArcanaWorld\\ARCANA_WORLD_R6_UBUNTU_PORT\\INT10K_E2_A1_WINDOWS_662bed_02`

| Configuration | Full history per direct/resumed case | Actual split checkpoint | Oracle SHA256 | Manifest SHA256 | Total bundle bytes |
|---|---:|---:|---|---|---:|
| 3 years, 1+2 | 3 regional year records, 4 snapshots, 3 unified steps; 174 regional events | year 1; 1 record, 2 snapshots, 1 unified step; 316,486 checkpoint bytes | `a785f691270130fa87275ebd1fb718c0845470fb8ae2864ca58f8b53743dee7f` | `9485fa81ef6d88e63edb7d96a1a25661199bc3e712650316bd15864b8aed08c1` | 3,984,382 |
| 10 years, 5+5 | 10 regional year records, 11 snapshots, 10 unified steps; 580 regional events | year 5; 5 records, 6 snapshots, 5 unified steps; 895,876 checkpoint bytes | `000113cdf7e6f1f8bd4afb9bb5e03b50df94abe027c4dc31df5f719a2e58a156` | `a7f2bce9b4e725a9d0227ee76c5c6e88823a62a6d073afd94f713c0620099a0f` | 11,202,131 |

Each manifest-listed member was reopened on Windows and independently checked for exact byte length and SHA256. The oracle was parsed and passed `verify_oracle()`. Direct and resumed complete results matched within the existing E1 numeric tolerance, with exact identity/order comparisons. The 3-year water and solid residuals were zero; Deep residual was 0 J, geometry residual `6.437301635742188e-05 m3`, mechanical residual `-1.1641532182693481e-08 J`. At 10 years the maximum absolute yearly solid residual was `0.00048828125 kg`; water residuals were zero, Deep residual was 0 J, geometry residual `0.00018644332885742188 m3`, and mechanical residual `8.009374141693115e-08 J`. These are engineering-run diagnostics under unchanged existing model tolerances, not scientific qualification.

Measured local costs (capture only, excluding output write):

| Configuration | Direct wall / CPU | Prefix + resume wall / CPU | Capture wall / CPU | Python `tracemalloc` peak | RSS observations |
|---|---:|---:|---:|---:|---:|
| 3 years | 0.407 s / 0.406 s | 1.000 s / 0.969 s | 2.095 s / 1.375 s | 6,224,395 bytes | 36,405,248 before; 50,798,592 after |
| 10 years | 1.297 s / 1.250 s | 2.284 s / 2.250 s | 5.449 s / 3.500 s | 15,604,606 bytes | 36,843,520 before; 71,671,808 after |

RSS is Windows process working-set measurement at the capture phase boundaries; the reported maximum is only the maximum of those observations, not a sampled continuous peak. `tracemalloc` excludes some native allocations. The output contains three fully retained cases, so the 3.98 MB and 11.20 MB bundles intentionally duplicate direct and resumed histories. These measurements do not qualify streaming or predict longer-run costs.

## Verification

- Focused E2-A1 synthetic adversarial suite: 10 tests after final test addition; included in the combined run below.
- Combined E2-A1 + E1 short reference + regional + regional drainage + unified suites: **60 passed** on Windows Python 3.12.10 / NumPy 2.5.1.
- Actual 3-year 1+2 and 10-year 5+5 capture: natural process exit 0 for both; source bundle verified before and after; manifest members and oracle integrity independently rechecked.
- No FAIR, ShellSet, MPI, Solver, new long run or WORLD_HISTORY access/write.

## Remaining gaps and next gate

This milestone creates a complete *reference oracle*, not the E2 frontier/history streaming system. Histories are still assembled in memory and serialized together; queries validate and inspect the in-memory oracle; there is no append-only transaction/commit chain, recovery protocol, streaming writer, bounded frontier or independent indexed on-disk reader. The E1 FAIR reference bundle was not imported, so comparison to its serialized numerical bytes remains unavailable. Local NumPy differs from FAIR's reported E1 version. Linux qualification and exact committed-source retest are pending.

Next: commit the scoped implementation and report; run the combined Linux suite on that exact commit and independently inspect the new oracle bundle through its manifest/query APIs. Only then proceed to E2-B frontier/checkpoint design and streaming implementation. No 100-, 1,000- or 10,000-year run is authorized. `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`; `GEODYN_2B_ARCANA_FORWARD_AUTHORIZED=false`; `INT10K_LONG_RUN_AUTHORIZED=false`.

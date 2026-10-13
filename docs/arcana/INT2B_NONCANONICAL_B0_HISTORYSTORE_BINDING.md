# INT-2B — Minimal noncanonical B0 HistoryStore binding

Date: 2026-10-14
Checkout: `r6/si1-bandwidth-f2av`, HEAD `a2e3fd8608e7a736bc4aa06073be982b4a6cfd55`
Decision: `INT2B_BLOCKED_STORE_ATOMIC_PUBLICATION_UNAVAILABLE`

## Scope

This work validates the existing R4 and INT-1D noncanonical bundles, maps their observed rows into existing B0 typed records, and attempts the required isolated `HistoryStore` write/query path. It does not access or modify canonical `WORLD_HISTORY`, execute a provider-backed trajectory, or qualify physical authority or executable replay.

The bundle loader reused from INT-2A verified the pinned nine-file membership, member sizes and SHA256 values, run/result/sample cross-references, support identities, and provenance for both input bundles. The inputs remained unchanged. The pinned manifest identities are R4 `191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236` and INT-1D `0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571`.

## B0 mapping implemented

`scripts/r6_int2b_history_adapter.py` builds a `ProvenanceRecord` per experiment and a `DomainStateEnvelope` per verified observed sample. The output records comprise 8 R4 states (4 samples × 2 supports), 18 INT-1D states (9 × 2), and 2 provenance records. Each state carries its source experiment, manifest/run/sample digests, source commit and source-composite identity, provider digest references, boundary, exact support cell, resolution rung, stored engineering elapsed time, field values and units. Time keys preserve the exact parsed floating-point observation with `repr`; they are not rounded or converted to geological time keys.

R4 and INT-1D receive distinct deterministic `HistoryId` and `BranchId` values. The B0 classification is `SupportClass.DERIVED_SUPPORTED` with `AuthorityClass.NONE`; applicability explicitly says noncanonical engineering observation, physical/geographic authority not claimed, and canonical publication false. Uncertainty remains `UNKNOWN_NOT_REPORTED_BY_SOURCE`. The adapter rejects reconstructed rows and mismatched source/support identities. It reuses `HistoryStore.append_transaction()` and `HistoryQueryService.state_at()` if the filesystem capability precondition succeeds; it does not implement a second store or query path.

## Filesystem capability and blocked store test

The bounded probe ran in a new disposable directory on the intended F: NTFS volume. File creation and probe-byte readback worked. Creating a same-directory hard link with `os.link` failed with `PermissionError: [WinError 5] Accesso negato`; probe-created names were removed and the directory was empty afterward. The adapter repeated the actual probe in the new INT-2B output directory and recorded the same failure. It therefore did not instantiate `HistoryStore`, register records, or execute queries. No monkeypatch or relaxation of B0 atomic publication was used.

The focused INT-2B suite result was **6 passed, 1 skipped, 0 failed**. The skipped test is the actual B0 registration/readback/query integration test, skipped only after the hard-link capability probe failed. Related INT-2A/B0 regressions produced **16 passed, 9 failed**; all nine failures occurred while the existing `HistoryStore` tried to install its initial immutable manifest through `os.link`, before query assertions. These are Windows filesystem-environment failures, not evidence that the B0 store/query path passed or that the B0 implementation is defective. `py_compile` and `git diff --check` passed.

Windows reports the target volume as NTFS; same-volume format alone does not establish that the current managed process token can create hard links. WSL is installed but listing/running the configured distribution was denied (`Wsl/E_ACCESSDENIED`), so it was not an available local POSIX test environment. The repository procedure records a pre-existing Fair Conda environment `arcana-r6-linux`, where prior compiler-fixture work was run. That is a candidate environment for a later bounded B0 test after code publication and fetch; no B0 store/query test was run there in this gate, and prior compiler tests do not qualify B0 storage.

## Result bundle

New disposable result directory: `outputs/r6_functional_development/INT2B_B0_BINDING_20261014_01/`.

| File | Bytes | SHA256 |
|---|---:|---|
| `INT2B_B0_BINDING_RESULT.json` | 4,284 | `b11a6d1b057a1676f8da6afb6598a682a9f7255458a37055866f3e481d33006f` |
| `INT2B_OUTPUT_MANIFEST.json` | 553 | `b85216bafd82836f72a0720ef970c84137e5d98acc0092256ca8c562d9290440` |
| `INT2B_OUTPUT_MANIFEST.json.sha256` | 93 | `9b4c497b4bd8f7acd2060cdcd262d623201c23d79d33876f4c1c55a5480a83e1` |

The manifest binds the result JSON size/digest and both source manifest identities; the sidecar matches the manifest digest. The result records the planned 26 states and 2 provenance records, but reports `history_store.created=false`, `queries_executed=false`, and no store-byte or query-latency measurement. It is therefore not a B0 registration/query PASS.

The four existing candidate checkpoint payloads (two per bundle) successfully deserialize through the existing `state_from_payload()` into reduced states. They are not complete registered B0 checkpoint envelopes and do not bind a closed runner/configuration, forcing, and deterministic engine adapter. This proves payload deserialization only; executable replay remains unqualified.

## Validation and next step

Observed bundle-to-B0-record construction and reduced-state deserialization are verified offline. Store immutability, transactional publication, exact readback, query outcomes, store bytes, and latency remain untested because the required hard-link operation is denied on this Windows filesystem. Continue with the same isolated-store tests in an already qualified Linux environment after ordinary code publication/fetch, preserving these Windows results and output bundle. Do not change `HistoryStore` atomic-write semantics to bypass the environment restriction.

The scientific gates remain unchanged: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, and `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

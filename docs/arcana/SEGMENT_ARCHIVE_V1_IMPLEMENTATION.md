# Segment Archive V1 — implementation and bounded verification

## Decision and scope

`SEGMENT_ARCHIVE_V1_RUNNER_INTEGRATION_IMPLEMENTED__ENG10K_NOT_RUN`.

The incremental archive writer is connected to the reduced ENG10K candidate runner and tested through synthetic runner/writer fixtures. This is an export-format and observer-path result only. No ENG10K evolution, FAIR job, or canonical publication was run. Existing INT3 authorization and scientific gates are unchanged. Changes to the candidate execution code require a fresh source identity; no prior execution authorization is reused.

## Data flow and numerical immutability

`advance_with_bounded_samples()` in `src/arcana_worldsim/r6/int3_eng10k.py` accepts an optional `state_observer`. If supplied, it is called for the exact initial `ReducedState` and each state emitted after an actual integrator substep. The existing diagnostic-sample observer still runs, and the normal return values (final state and diagnostics) retain their existing path. With the default `None`, no archive callback is performed.

`SegmentArchiveWriter.observe()` serializes `state.payload()` and the exact `time_s`; it does not alter the state, feed data back to the integrator, interpolate, or choose representative records. Each record includes `time_s_hex` in addition to the JSON number so the exact binary64 time value can be checked. The grid identity fingerprints material coordinates and per-node material definitions. Every actual initial/substep state is written; scheduled diagnostic samples are a separate, potentially sparser product.

The INT3 runner binds eight unique trajectories into one archive: six direct runs (three configured resolution factors by two R4 supports) and two R4-checkpoint restart runs (the configured reference factor by two supports). The direct runs at the diagnostic factor continue to use `advance_with_bounded_samples()` and retain their existing diagnostic output. The other direct factors call the same kernel with the optional observer; restart runs use the same wrapper and still emit their existing diagnostic samples. Each archive trajectory records its support, kind, factor, exact initial/substep times and sequence. The archive is finalized only after all eight computations and existing direct/restart comparison logic complete. An error during a trajectory leaves its incomplete marker; omission of a trajectory prevents finalization.

An exported state has class `DIAGNOSTIC_OBSERVATION` and `checkpoint_capability=NOT_QUALIFIED_AS_RESTARTABLE`. Although the payload contains the reduced state fields, no restoration/replay contract is asserted. Representative-state selection and Luna indexes are derived products and are not written into the raw archive.

## Bundle and completion protocol

The versioned bundle contains:

- `STATES.jsonl`: one canonical UTF-8 JSON record per observed state, appended and flushed incrementally. Records carry segment/trajectory/support IDs, trajectory kind, resolution factor, global and trajectory sequence numbers, exact time, grid fingerprint, state-payload SHA256, full payload, and state/checkpoint classifications.
- `SEGMENT_MANIFEST.json`: published only after all declared trajectories complete and the state stream is flushed and `fsync`ed. It records trajectory endpoints/counts, stream bytes/hash, provenance claims, and write semantics.
- `SEGMENT_MANIFEST.json.sha256`: digest sidecar for the manifest bytes.
- `INCOMPLETE.json`: created first and retained on abort, observer/I/O error, missing trajectory completion, or other failed capture. The validator rejects any bundle with this marker.

The manifest is written to a new same-directory temporary file and renamed into place. This does not claim device-level durability or directory `fsync`; a crash or filesystem failure can leave a partial directory, which must remain non-authoritative. The writer requires an absent absolute destination, existing regular parent directories, rejects symlink/junction ancestors where detectable, rejects overlap with configured forbidden roots, and forbids a destination path containing `WORLD_HISTORY`. It never overwrites an existing destination.

The validator streams the JSONL file and checks record and trajectory membership, sequence, monotonic time, payload/grid digests, stream byte count/hash, manifest sidecar, and explicit completion. Hashes establish byte integrity relative to the emitted manifest; they do not independently authenticate the source, configuration, provider, input, or operator claims.

The outer INT3 `ARTIFACT_MANIFEST.json` also includes every archive member by relative path, byte count, and SHA256, plus the archive validator summary. Existing diagnostic artifacts remain present. The existing projected output estimate still applies to the preexisting run artifacts only; full archive size is explicitly `UNKNOWN_UNTIL_ACTUAL_INTEGRATOR_SUBSTEP_COUNTS`. In `MONITORED_BUDGETS`, the existing cumulative output monitor remains the active cap and the final bundle rejects a total above 512 MiB. In `OBSERVE_ONLY`, this integration adds no archive-size threshold; that mode records size without terminating for a size threshold. This does not remove administrative filesystem constraints or grant run authority.

## Provenance authority

The writer requires source, configuration, provider, and input identity fields. Values can be marked `SYNTHETIC_TEST_ONLY` or `CALLER_ASSERTED_UNVERIFIED`; production-shaped hashes are stored as caller claims and are explicitly labeled not independently authenticated. The writer is not the provider audit and cannot prove that a claimed source or input was used by the integrator. A production caller must verify these identities before capture and preserve the audit evidence alongside the archive.

No run/attempt authority or independently owned trajectory assignment is created by this component. Segment/trajectory/support labels and the resolution factor are caller-supplied metadata. They bind records internally but do not prove an external run identity.

## Bounded tests and measurements

Windows verification performed:

- Focused command over `test_r6_segment_archive.py`, `test_r6_segment_archive_kernel.py`, and `test_r6_int3_eng10k_segment_archive.py`: **9 passed, 1 skipped**. The skipped test compares the actual kernel observer path with its observer-free baseline; NumPy is not installed in this Python environment.
- The existing `tests/test_r6_int3_eng10k.py` suite was attempted but failed collection with `ModuleNotFoundError: numpy`. No package was installed.
- Runner/writer fixtures ran with numerical provider imports stubbed. They test all eight synthetic trajectory bindings, state order, direct/restart identity, outer-manifest membership, diagnostic artifact preservation, and rejection of a seven-of-eight archive. The stubs cannot call the kernel.
- `py_compile` for the archive module, both integration modules, runner, and tests: **PASS**.
- UTF-8/LF, no trailing whitespace, and `git diff --check`: **PASS**.

The standard-library writer tests check exact record round-trip, schema/identity binding, payload tamper rejection, failure/unfinished-trajectory behavior, and absent-destination/provenance rejection. The skipped kernel test compares observer-enabled final state and diagnostics against an observer-free baseline, and checks every actual kernel observation in the archive. That kernel immutability assertion remains pending on the supported NumPy runtime; no package was installed.

A separate writer-only measurement used 100 synthetic 73-node states (no kernel): 1,055,342 bytes in `STATES.jsonl` (10,553.42 bytes/record), 1,057,169 bytes total bundle, 0.4647 s wall time, and 40,542 bytes peak Python-traced allocation on this Windows environment. This is a small serialization fixture measurement, not ENG10K throughput, process RSS, or an estimate for a long segment. It excludes construction of the fixture states and operating-system/runtime allocations.

## Concatenated segment proposal

Keep each completed segment immutable and independently verifiable. A separate versioned series manifest should list ordered segment-manifest digests, time intervals, support and grid identities, source/configuration/provider identities, and the relationship at each boundary. Require exact continuity of the relevant source, configuration, forcing, support/grid and state schema for a continuous segment chain. Bind the next segment to the previous segment's verified endpoint payload fingerprint and exact time. If a trajectory restarts from a checkpoint, identify and validate that restart relation explicitly; do not infer it from equal endpoint values. If there is a gap, overlap, changed forcing/model, or changed grid, record a discontinuity or new series rather than silently concatenating. Do not deduplicate boundary records or synthesize interpolated states. Luna's representative-state index and replay requests remain separate derived artifacts that reference source segment manifest digests and record sequence/JSON pointers.

## Remaining gates

- Kernel-observer integration test on the supported NumPy runtime remains unexecuted on this Windows environment.
- Runner/writer integration tests have not yet run on the supported Linux runtime. They must be repeated there before treating the wiring as runtime-verified.
- No measured ENG10K export overhead, long-stream storage behavior, or memory/RSS behavior is available.
- No checkpoint is qualified as restartable by this archive format.
- Caller-supplied runtime identities are not authenticated by the writer.
- Filesystem crash durability and concurrent pathname replacement are not claimed.
- No scientific extrapolation of frozen ENG10K forcing to longer geological intervals is implied.

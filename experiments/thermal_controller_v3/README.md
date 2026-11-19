# Thermal controller V3 — indexed, byte-bounded sessions

Reuses HistoryStore, V2 ReadSession and the unchanged thermal solver. IndexedSession builds its index from committed HistoricalSnapshot metadata, not by loading every dynamic body. Prefixes are verified native snapshots stored as immutable canonical JSON bytes in deterministic LRU order. Default budget393216B (384KiB).

Budget accounting: incremental OrderedDict size + sys.getsizeof(keys) + sys.getsizeof(bytes buffers). Empty-container baseline, immutable static/index metadata, counters/diagnostic eviction list, temporary encoding/decoding and caller-owned returned states are outside this prefix budget. It is not a total-process RSS limit. Admission evicts before installing a candidate that would exceed the budget; oversized entries are skipped, with correct full verification fallback. Budget0 disables prefix storage. Index and prefix storage are per root/source/static/read-view session; refresh/force_verify/close invalidate caches. Metadata fingerprint guards and source guards are inherited and extended from V2. No new backend.

Read-only intermediate snapshot example, from ARCANA_WORLD_R6_GEOMETRY_R1_WORK:

```bash
E=../ARCANA_WORLD_EVIDENCE/R6/THERMAL_CONTROLLER_EXPLORE_V3_20261102_01/run02
PYTHONPATH=src:experiments/thermal_1d_history_v1:experiments/thermal_controller_history_v1:experiments/thermal_controller_v2 \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B \
experiments/thermal_controller_v3/demo.py query \
 --root "$E/C139_dense" --job "$E/C139_DENSE_JOB.json" \
 --job-sha 6ba4d03e9f13448418a9fa48c512c79641108ed275e78277e01e1f29292d7735 \
 --column R6G1D-R013-C139 --year 5.106382978723404 --budget-bytes 393216
```

C028 uses C028_dense/C028_DENSE_JOB.json, column R6G1D-R091-C028 and JOB SHA 384a56036f0da8ca71eae773a59c8c0f4d6cbcd9f7601063b4aeb58a5eed7a5d. CLI displays stored nodes0..8m. A separate CLI invocation starts application-cold. To reuse the cache, keep one `with IndexedSession(controller,budget_bytes=393216) as session:` open and call session.query(column,year,low,high) or session.restore(state_id) repeatedly.

Dense times are actual accepted steps0,12,...564 divided by564 times10years, represented by the stored model-time floats. Use DENSE_PUBLISHED_STATES.csv for exact archived instants; no nearest-time interpolation. In particular2.5years is stored in the five-snapshot archive but not in the48-snapshot archive. The time index is scoped to the pinned view. Session force_verify authenticates every published native state; refresh opens current view and clears derived cache.

DenseController adds explicit retention-plan/source identity while reusing the V2 publisher. Five- and48-snapshot identities differ intentionally; numerical states match after excluding the retention-only native-parent field. Direct/split of the SAME dense plan match completely in all48states/IDs. STATIC.json and causal ledger segments remain required for restart; caches are optional accelerators. Never append to sealed evidence. No physical coupling, solver change, production CAS/B0 or hostile-filesystem guarantee.

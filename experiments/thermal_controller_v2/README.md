# Thermal Controller EXPLORE V2

reader.py wraps the actual HistoryStore.read_view context manager. Cache is per session/root/view/static/source binding, with verified native-prefix copies and immutable R6 records. Refresh or force_verify clears cached data. File metadata changes trigger complete reload/identity verification; source-file metadata changes reject. Returning copies prevents mutation of the cached native state by callers. This local-file cache is not a hostile-filesystem authentication mechanism or a portable storage backend.

FastController preserves the previous C028 producer identities, adding only validated publication-head reuse. Its cache policy is separately bound by JOB.cache_policy_sha256 and this delivery's source snapshot. ColumnController adapts metadata to the actual column/support and uses a V2 producer binding; it does not change thermal.step. No backend or production CAS/B0 is implemented.

Read-only queries from ARCANA_WORLD_R6_GEOMETRY_R1_WORK:

```bash
E=../ARCANA_WORLD_EVIDENCE/R6/THERMAL_CONTROLLER_EXPLORE_V2_20261102_01/run01
PYTHONPATH=src:experiments/thermal_1d_history_v1:experiments/thermal_controller_history_v1 \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B \
experiments/thermal_controller_v2/campaign.py query \
 --root "$E/C139_direct" --job "$E/C139_JOB.json" \
 --job-sha 28df8dfef29e25f36a248740024cd329540e4e0a99bb00d2d6f7265705321913 \
 --kind column --year 10
```

C028: use root cached_publish, job C028_JOB.json, kind legacy, job SHA 9ae6f6cee90f04ba4f322881c2113c0b9580866fea00799be17a0052413065df. Query example returns stored nodes0..8m. API ReadSession.query(column,year,low,high) selects column/depth explicitly. Years0,2.5,5,7.5,10 only; no interpolation. Missing times and empty depth selections remain explicit statuses.

Use a new ReadSession when changing controller/context; cache never transfers between controllers or persists beyond session exit. A pinned view intentionally excludes later publications until refresh. Native restart requires STATIC.json plus causal ledger-segment prefix. The cache is optional: force_verify or a fresh session uses full verification. Do not append to sealed archives. No new simulations are run by query.

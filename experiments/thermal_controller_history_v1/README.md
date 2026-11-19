# Thermal controller/history R6 — experimental adapter

Reuses actual R6 DomainStateEnvelope, TimeSupport/SpatialSupport, HistoricalSnapshot, ProvenanceRecord, retention DomainExtractor/MinimalStateContract and HistoryStore. Numerical integration calls the unchanged thermal_1d_history_v1 thermal.step. No replacement history store, new CAS/B0 algorithm or engine registration.

Read-only delivered query, from ARCANA_WORLD_R6_GEOMETRY_R1_WORK:

```bash
E=../ARCANA_WORLD_EVIDENCE/R6/THERMAL_CONTROLLER_HISTORY_EXPLORE_20261102_01/run01
PYTHONPATH=src:experiments/thermal_1d_history_v1 \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B \
experiments/thermal_controller_history_v1/demo.py query \
  --root "$E/direct" --job "$E/JOB.json" \
  --job-sha adeaf6b2c27c85a2dd586580b3014a721ecda9150d8aaf237ad4cc25f34ecfdf \
  --year 10 --min-depth 0 --max-depth 8
```

The root/JOB identifies C028; API ThermalController.query(column,year,zmin,zmax) explicitly accepts a column. Available years0/2.5/5/7.5/10; no implicit temporal or depth interpolation. Query results contain authoritative hi/correction and rounded display temperature. Geometry/static schema and source hashes must match the supplied JOB. Keep STATIC.json AND all preceding dynamic records/ledger segments to restart. A single dynamic record is intentionally not self-contained.

Lifecycle: create(...).start() publishes T0; advance() executes accepted fixed steps to the next scheduled boundary and becomes READY; publish() validates complete native state and retention then uses existing HistoryStore.append_transaction; recover() restores latest committed typed state with its causal prefix. advance before publication, duplicate/skipped publications and inconsistent references reject. Parent-state identities and native-parent hashes are both checked. Static data once, each ledger row persisted once. Numerical/source/runtime/static identities stay bound.

Campaign mode requires a NEW exclusive output path. resume CLI is demonstrated only on the separate split archive during the bounded campaign; do not append to sealed evidence. Source snapshots and invocation receipts are in the evidence root. No production concurrency/crash/single-file standalone restart guarantee is inferred.

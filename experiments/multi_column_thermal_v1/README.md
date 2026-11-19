# Multi-column thermal scheduler EXPLORE

Two independent existing DenseControllers, shared integer accepted-step plan, existing HistoryStore as logical epoch registry, existing IndexedSession per-column readers. No solver/provider/backend change or physical coupling.

A shared epoch is available only after both column records are committed and verified and an epoch record is committed to the registry. Column commits and the registry commit are separate: there is NO cross-store atomicity. Individual-column queries may return a real published state with shared_epoch_published=false. Coordinated queries return EPOCH_INCOMPLETE/EPOCH_UNREGISTERED/EPOCH_NOT_IN_VIEW until the registry's pinned view contains the epoch; no partial group is represented as AVAILABLE.

Restart reconcile uses only committed matching states. At most one next epoch may be ahead of the registry. Existing matching publications are reused; missing column is advanced/published and then the epoch registered. Duplicate registration is idempotent ALREADY_AVAILABLE; duplicate column publication rejects. This is a controlled interruption demonstration, not SIGKILL/power-loss qualification.

Read-only actual shared epoch288 (from worktree):

```bash
E=../ARCANA_WORLD_EVIDENCE/R6/MULTI_COLUMN_THERMAL_SCHEDULER_20261102_01/run02/48/split
PYTHONPATH=src:experiments/thermal_1d_history_v1:experiments/thermal_controller_history_v1:experiments/thermal_controller_v2:experiments/thermal_controller_v3 \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B \
experiments/multi_column_thermal_v1/demo.py query \
 --root "$E" --plan-sha 3f0d664b21fea299926577867fb0893beb453ccaba4bb7417f44fd31c9b7d30f \
 --step 288 --cache-bytes 786432
```

The API also supports arbitrary stored depth intervals:

```python
scheduler = Scheduler(root, expected_plan_sha)
with CoordinatedReader(scheduler, budget_bytes=786432) as reader:
    shared = reader.query_epoch(288, low=0, high=8)
    one = reader.query_column('C028', 564, low=27900, high=28100)
```

Primary time key is integer accepted step; replies include seconds/years. Five epochs at0/141/282/423/564 or48epochs at0/12/.../564; no interpolation. Physical resolution545nodes per column, numerical564steps, archived5or48epochs are distinct. Static and causal ledger prefixes remain required to restore. Reader pins registry first and each column separately; referenced state IDs verify the logical combination. This does not imply a simultaneous atomic pin of all stores. Refresh explicitly closes and reopens views.

Aggregate prefix budget is partitioned into deterministic equal reservations (remainder assigned in sorted column order), no borrowing. Sum of per-column charged buffers and sum of peak upper bounds cannot exceed the aggregate limit. Same byte accounting as V3; static/index/controller metadata, active states, diagnostics, temporary decode and caller-owned results are outside the prefix budget. This is not an RSS cap.

Campaign/resume are opt-in and must not target sealed evidence. Source policy and PLAN SHA are required. Direct/split plans and outputs are identical in the tested runtime. Frozen first/final source snapshots, initial setup failure and actual receipts are preserved.

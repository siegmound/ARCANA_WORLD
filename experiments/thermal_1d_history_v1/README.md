# Thermal 1D history EXPLORE v1

Complete compensated temperature state and exclusive causal snapshot files. No production B0/CAS or crash recovery. Read the worktree report for scope. Physical temperature is hi minus correction; keep both arrays on restart.

## Query the delivered archive (read-only)

From ARCANA_WORLD_R6_GEOMETRY_R1_WORK:

```bash
E=../ARCANA_WORLD_EVIDENCE/R6/THERMAL_1D_HISTORY_EXPLORE_20261102_01/run02
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python -B \
experiments/thermal_1d_history_v1/run.py query \
  --root "$E/direct" --job "$E/JOB.json" \
  --job-sha 157d527abc24470d77847be05a01ac8b2f83aee1d7595d3cb7a74444e51d09c5 \
  --column R6G1D-R091-C028 --year 10 --depth-min 0 --depth-max 8
```

Returns stored nodes at0,2,4,6,8m. Available years0,2.5,5,7.5,10. Year1 returns TIME_NOT_ARCHIVED. A depth interval without a node returns NO_STORED_NODES_IN_INTERVAL. No interpolation/reconstruction is implemented. Displayed temperature is rounded binary64; authoritative hi/correction fields are both returned. The frozen source/runtime and externally supplied JOB SHA are checked. This is integrity/provenance checking, not signed authentication against an actor who replaces all trusted inputs.

## Implementation and reproduction

thermal.py contains complete accepted-step state and compensated Euler integration. history.py writes full JSON snapshots with embedded previous-snapshot SHA plus simple JSONL index. run.py offers campaign, resume and query. New campaigns require a new exclusive evidence root with authenticated BEFORE.json prepared from predecessor pins. Never point campaign at an existing archive. Source/runtime changes require an explicit new experimental version. JSON floats round-trip exactly in the tested runtime; longdouble is a temporary, never required as an opaque checkpoint type.

Snapshots carry physical and numerical state, geometry/materials, initial field, current/previous-step fluxes, plan and all accepted-step energy ledger rows. Time is step*fixed_dt, not re-planned on resume. Publication is file-write+fsync then index append+fsync; no atomic multi-file commit, directory durability, concurrency, power-loss or hostile-input hardening claim. Unindexed snapshot tails are rejected/preserved, not adopted or removed.

The temperature compensation and causal embedded parent are new isolated prototype behavior. Spatial accuracy is inherited only in the previously measured10year resolved-grid scope. No global geology or scientific production claim. Original source versions remain untouched.

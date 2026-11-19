# Geographic thermal history reader — EXPLORE

`geo.py` selects existing column histories by positive-area overlap with a geographic bbox `(south,north,west,east)`. West > east crosses the antimeridian. Coordinate bounds are degrees; area uses the original 6371000m sphere. Degenerate regions are rejected; boundary-only contact does not select a cell.

The PRE numerical owner cell is a runtime support association, not the FEG node coordinate or a horizontally uniform thermal field. Cell center/bounds/area are returned with `SpatialSupport`; subcell location and actual horizontal thermal area remain UNKNOWN/null. The catalogue contains only C028 and C139. Known grid area without either trajectory is NOT_SIMULATED. Other processes are UNKNOWN in this catalogue, not declared absent planet-wide.

Reuses Scheduler, CoordinatedReader, IndexedSession and the existing HistoryStore. No new backend, native state rewrite, retention change or evolution. The geographic catalogue is separately authenticated metadata; source/static/PLAN/native identity checks remain required. Epoch selection uses the accepted integer step, with actual seconds/years returned. A missing shared registry epoch in the pinned view is EPOCH_INCOMPLETE. An unplanned step is TIME_NOT_ARCHIVED. Out-of-support depth is UNKNOWN; empty in-support node selections are NO_STORED_NODES_IN_INTERVAL. No interpolation.

Prefix cache still has an aggregate786432B budget, excluding static/index/query results/temporary buffers and RSS. No additional cache or append-only head optimization is introduced: full prefix validation remains the cold bottleneck. Region filtering only restores selected columns. Provenance and complete geometry in the response add real warm-query overhead compared with the previous small scheduler query.

Run the delivered read-only example (original archives were copied; all archive bytes/IDs are identical):

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK/experiments/geo_temporal_thermal_v1/demo.py \
  query \
  --root \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEO_TEMPORAL_THERMAL_20261103_01/run03/48 \
  --plan-sha \
  3f0d664b21fea299926577867fb0893beb453ccaba4bb7417f44fd31c9b7d30f \
  --catalog \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEO_TEMPORAL_THERMAL_20261103_01/run03/CATALOG.json \
  --catalog-sha \
  755fb19aa92e5a56fe989d541553dcb01a9c0677f4ae9c763fdde05253786217 \
  --step \
  564 \
  --region \
  1 \
  2 \
  -152 \
  -151 \
  --depth \
  0 \
  8
```

The displayed temperature is rounded binary64; both hi and correction are returned. Physical geometry/materials/Dirichlet and native hash are unchanged. Source and runtime compatibility are still required for actual restart; this experiment tests restoration/query, not another evolution or crash recovery.

The campaign's first attempt rejects a one-ULP difference between archived C028 base Dirichlet and the PRE serialized base. Final adapter checks that difference within one ULP and exposes both numbers; it never changes the archived boundary. All physical inputs, source and static SHA bindings remain exact. run03 is the final complete campaign. run01/run02 remain separately preserved.

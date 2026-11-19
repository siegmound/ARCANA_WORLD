# HR1-MRES — six-tier measured synthetic infrastructure

2026-10-30–31. Gate dated 2026-10-30; completed 2026-10-31 Europe/Rome.
FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

`HR1_MRES_WORKLOAD=PASS_MEASURED_SIX_TIER_METADATA_ARRAY_AND_RESTART`

`HR1_MRES_PHYSICS_1000Y=BLOCKED_TRUE_GLOBAL_GRID_PHYSICS_OR_INPUTS_UNAVAILABLE`

All **54 infrastructure cases completed**, each with an independently launched
reader/probe. The common 64 B/cell profile actually advanced 1, 10, 100 and
1000 synthetic years on every requested raster, in increasing resolution within
each horizon. The 256/1024 B sensitivities actually advanced only 1/10Y on all
six rasters; the denser-event sensitivity advanced only 10Y/64B. There is no
measured 100/1000Y claim for these sensitivities, and no global physical trajectory.
No retry, physical recalculation, new 10k/100k, legacy export, commit or push.

## Exact scope, schema and geometry

Read in full: `~/HPC-POMDP/Arcana/R6_HR1_MRES_TASK.md`, the preceding
`R6_HR1_2K_TASK.md` and POST10K-A0 report. The multiresolution task supersedes
the older single-2K ladder. Referenced fuller conversational handoffs are not
invented. The user's explicit FAIR authoring and no-commit instructions supersede
the historical Windows-first/same-commit ledger procedure. Branch remains
`r6/runtime-copy-r1-fair`, HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787`.

The added workload imports existing B0 store/envelope primitives and advances a
live dense NumPy array; it does not import the regional/Unified/thermal/Deep
operators. It stores eight dimensionless `<f8` counter fields (64B), plus one
separately accounted mask byte per cell. Sensitivities use 32/128 fields with the
same precision and meaning. **All cells and fields change each year**. Exact
dyadic initialization/increments have an independent integer expected-value
assertion. Physical climate, chemistry, mineralogy, ecology, populations and
global Deep fields are ABSENT_UNAVAILABLE_NOT_ZERO.

All rasters use radius 6371000 m, 2:1 longitude/latitude bounds, south-to-north
rows, periodic longitude, no latitude wrap, and exact spherical row areas up to
binary64 rounding. The polar outer face has zero length. Positive-area/sphere
closure and seam/pole adjacency pass on all six grids. See
`GEOMETRY_COMPARISON.csv` for actual angular steps, equatorial scales and residuals.
These metrics do not qualify a polar physical flux operator or volume/energy law.
The geographic coordinate convention uses a spherical metric, not ellipsoidal
survey accuracy. No original nine-cell state was upsampled.

Common 128×128 tiles include actual partial edges. Every annual full array+mask,
including T0, is serialized, byte-shuffled, zlib1 compressed and written with raw
and compressed SHA256, JSONL index, causal descriptor chain and sparse events.
Time is one synthetic year=31557600s, annual steps, no physical substeps.
NULL event times remain NULL; context year is separate. Schema, masks, source,
configuration, years, field units and identities are bound in each case.

## Unified measured comparison

The authoritative **single comparison table is `COMPARISON.csv`**: all 54 cases,
all dimensions/profiles/horizons, raw CPU/RAM/storage/phase/query/restart values,
normalized per million cells and per cell-year. No extrapolated rows. The compact
view below is the actual common 64 B **1000Y** result for all six tiers. MB is
decimal; MiB=2²⁰B; archive includes T0, masks, events, B0, indexes and telemetry.

| Raster | Cells | Observed run s | CPU user/system s | Writer/probe RSS MiB | Archive MB / allocated MB | Child s / million cell-years | First/repeat full query s | Restore / next-step check s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 256×128 | 32,768 | 28.080 | 23.801 / 1.110 | 45.00 / 44.00 | 32.770 / 45.564 | 0.8458 | 0.0085 / 0.0053 | 0.0057 / 0.0045 |
| 512×256 | 131,072 | 36.347 | 34.593 / 0.721 | 51.41 / 53.18 | 105.865 / 114.348 | 0.2750 | 0.0248 / 0.0229 | 0.0198 / 0.0162 |
| 854×427 | 364,658 | 84.221 | 82.529 / 1.254 | 65.99 / 67.66 | 560.996 / 570.782 | 0.2300 | 0.0638 / 0.0610 | 0.0561 / 0.0472 |
| 1280×640 | 819,200 | 162.392 | 158.411 / 1.331 | 94.50 / 99.09 | 785.277 / 794.321 | 0.1979 | 0.1400 / 0.1309 | 0.1280 / 0.1037 |
| 1920×960 | 1,843,200 | 352.681 | 346.006 / 2.280 | 158.99 / 162.54 | 1807.093 / 1815.699 | 0.1911 | 0.3014 / 0.2959 | 0.2938 / 0.2401 |
| 2048×1024 | 2,097,152 | 391.744 | 386.312 / 2.230 | 175.43 / 178.75 | 1393.953 / 1406.566 | 0.1866 | 0.4608 / 0.3784 | 0.3740 / 0.2808 |


Case archives total 6.269452 GB logical,
6.341972 GB allocated,
30,402 files. This excludes the external supervisor,
derived report/figures and audit receipts, whose complete manifest is separate.
Campaign wall=1884.122s; sum of observed writer+probe services
=1882.392s. These totals include separately requested
query/recovery validation; they are not numerical-physics times. Individual argv,
stdout/stderr/exit/resource samples and ANNUAL.jsonl are retained.

`SCALABILITY.png/pdf` compares actual horizons, normalized costs, memory, storage,
queries/restart and payload sensitivity. `PHASE_COSTS.png/pdf` shows disjoint
1000Y phase costs. `MEASURED_FITS.json` provides horizon and cell-count affine
fits **with every observed residual**; fits are descriptive, not forecasts or
confidence intervals. One sample per distinct arm; no distributional speedup
claim. Larger grids can compress better than smaller ones because dyadic byte
structure and row/tile alignment vary. These compression ratios cannot forecast
natural-field entropy or physical solver scalability.

At 2K, actual 10Y payload sensitivities: 64 B: 4.555 s child service, 14.831 MB archive, 171.39 MiB RSS; 256 B: 28.132 s child service, 55.964 MB archive, 570.55 MiB RSS; 1024 B: 89.926 s child service, 219.073 MB archive, 2168.80 MiB RSS.
Actual event-density 10Y sensitivity: 2100→20980
events and 448,697→4,483,197
event JSON bytes (period 10000→1000). NULL counts, event density and all grid
measurements are retained rather than rounded to a nominal rate.

## Attribution, metadata and memory

For the actual 2K/1000Y case, measured disjoint writer phases are:

- `synthetic_array_update_s`: 21.726051 s.
- `serialization_shuffle_s`: 94.516580 s.
- `compression_s`: 183.295309 s.
- `raw_hash_s`: 71.363327 s.
- `compressed_hash_s`: 0.855488 s.
- `tile_index_metadata_s`: 1.355837 s.
- `write_stream_hash_s`: 2.155818 s.
- `journal_fsync_s`: 8.483691 s.
- `checkpoint_metadata_s`: 0.035440 s.
- `b0_atomic_publication_s`: 3.291622 s.

These are included in child service 391.279240s.
Other init/event/descriptor/unwrapped work is separately retained; no nested
checkpoint total is added again. B0 publication includes its own internal
serialization/hash/fsync; the journal-fsync phase covers external yearly streams.
This fixture performs no deposit scans or regional operator work: their cost is
NOT_MEASURED_NOT_APPLICABLE, not a claimed elimination of the old five O(D) passes.

`STORAGE_GROUPS.csv` accounts for compressed array+mask, tile index, events,
source/config/geometry, annual causal descriptors, B0 checkpoint/state metadata
and telemetry. `COMPARISON.csv` includes exact source bytes, raw 8 B per field per
cell/record, compressed bytes/tile, index bytes/tile, event bytes/event, B0 bytes/
pair, raw/allocated bytes/cell-year and compression ratios. Joint compression
does not uniquely allocate compressed bytes to fields. `STANDALONE_FIELD_CODEC.csv`
instead measures each field independently on actual middle/last Y10 tiles for
all grids/profiles; those standalone measurements are not additive joint sizes.

Memory is one live H×W×F state plus tile codec workspace, masks, small metadata
and annual telemetry, rather than a resident list of every historical array.
`ANNUAL_WINDOWS.csv` retains every actual 100Y window (and bounded shorter arms),
end RSS, phases, CPU and compressed growth. Fresh-reader peak is reported apart
from writer peak. Reading the history performs a full streaming prefix hash/event
check; it is O(history bytes), not constant-time. B0 metadata grows with checkpoint
count; selected array loads do not retain a chain of full prior physical states.
The measured array/query memory is not the R2 coupled solver's memory bound.

Each case was one child with 128 NumPy threads and no observed numerical process
children; own kernel VmHWM is authoritative over inherited maxrss. CPU user/system
and effective cores count actual utilization, not visible CPU/thread count.
Supervisor launch-to-observed-exit has <=0.25s polling slack; high-resolution child
subtotal is separately reported, especially for 1Y arms. Application-first query
does not mean physical disk-cold: OS cache is uncontrolled and prefix verification
precedes queries. Repeat full-grid query re-decodes all tiles; only the repeated
point query reuses a decoded tile. Source/runtime/source SHA are identical across
cases. No installations, invented resource caps or thread limits were added.

## Integrity, checkpoints, restart and test scope

Every yearly stream and descriptor is durably fsynced. B0 publishes a typed pair
at T0, every 10Y and the segment endpoint; 1000Y arms have101 pairs. Annual fsync
does not confer restart authority. Each pair binds source/config, checkpoint
parent, journal high-water and pending-prefix hash. The checkpoint refers to the
already stored **full annual array**, with no duplicated array write at commit.
This is a reference checkpoint for a simple array model, not a native physical
solver checkpoint or a measured coupled REC1 checkpoint substitute.

Each fresh process verifies all committed file hashes, descriptor/parent lineage,
events/NULLs and B0 high-water; then all fields/masks of the final full grid, six/
nine historical pole/seam/equator witnesses, full previous checkpoint arrays,
and one real increment against the persisted next year's complete tile state.
The expected formula is used only for assertions, never to supply query/restart
values in place of persisted bytes. Direct/split 3Y tests append and preserve exact
arrays/history. The four owned SIGKILL boundaries select the correct last pair
and pass restored-array continuation; killed stores are tar-preserved before
recovery. There is no hardware power-loss/failover qualification.

**61 focused tests passed in 8.07 s**: 23 new workload tests plus 38 existing B0
regressions. They cover all meshes, partial tiles/profiles, independent dyadic
table, clean split append, interruption visibility, corrupted data/index/events,
source/config rejection, exact queries and out-of-range access. Initial test
execution used pytest's already-existing temporary root as an exclusive run
directory; those 9 fixture failures are retained, corrected before qualification
and before the one-shot matrix. No benchmark case failed or was retried.

Crash recovery scope is explicit: the reader safely ignores unconfirmed tails and
restores the last visible pair. The exclusive fixture writer does **not** remove
or overwrite orphan year files; same-directory appending after such a crash can
refuse a colliding uncommitted year. Production tail-quarantine/linked continuation
dispatch remains unqualified. Clean committed split append and restored numerical
counter continuation are qualified; the fixture is not a production long-run
recovery controller. No original REC1 recovery scope is weakened or relabeled.

## Physics blocker and preserved identities

`PHYSICS_CAPABILITY_AUDIT.json` pins exact excerpts: `GlobalGrid1Degree` rejects
anything except 180×360; `create_synthetic_region` requires nine cells;
`SUPPORTS` contains only C028/C029 and Unified rejects other support sets.
A0 verifies the ungeoreferenced 3×3 basin and two 73-node columns. These qualified
paths provide no independently admitted global physical state/forcing/operator,
conservative global boundaries/coupling or mesh/time convergence for the six
rasters. This is a precise qualification gap, not a universal claim that no
external global software exists. The conditional physical suite was therefore
**not launched at any tier**. A future physics gate needs those operators, inputs,
pole/seam flux laws, stability/error evidence and full hidden-state restart.

All252 original10k and 49 A0 manifest members and their source identities were
rehash-checked before and after. Original10k MANIFEST SHA
`3d32aa9da0c3ff181fb048f352ec0435b967d55ef8c052f6028ca3ade8e06fb2`;
A0 MANIFEST SHA
`b54d5729151e5937a9f564f4404a217552cf1fc494e10d96ae58357f6e2aaca2`.
All 306 prior measured source/test pins and 27 pre-existing dirty-file fingerprints
were preserved before the authorized documentation handoff; five ledger files
are then changed only to record this gate. WORKTREE_BEFORE.tar preserves the old
dirty sources/docs. No R1/R2/REC1/L1 engine/source/test file was edited.

New workload SHA256 `d1a590b7195bcf033a01abc6077c6281c8fe225543e4b01199bc9440c2414fc2`;
new test SHA256 `2bad5858bae5aa3a3869574ca4fbfba24084b5145c1b823cc74016914bad3e30`.
Full source/runtime/campaign/analysis scripts and test receipts are manifest-bound
under `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/HR1_MRES_20261030_01`. FINAL_PRESERVATION binds old source/archive closure; MANIFEST.json
binds new evidence and FILE_MANIFEST.sha256 binds its bytes, without circularity.

FAIR context is session-58727, actual visible cgroups cpu.max/memory.max=max;
no available scheduler command/context or effective scheduler-only rule was
identified. This is not a CPU/RAM reservation or administrator attestation.
Quota remains UNKNOWN where unavailable; successful actual writes/fsync are
execution evidence. Scientific/production authority stays false.

Next: review measured service costs and the explicitly limited fixture recovery
interface. Any global physical 1000Y gate first needs qualified six-grid providers,
inputs, conservation/coupling and convergence. No automatic follow-on simulation.

## Direct artifact links

- [Unified comparison CSV](../../../ARCANA_WORLD_EVIDENCE/R6/HR1_MRES_20261030_01/COMPARISON.csv)
- [Scalability PDF](../../../ARCANA_WORLD_EVIDENCE/R6/HR1_MRES_20261030_01/SCALABILITY.pdf)
- [Disjoint cost PDF](../../../ARCANA_WORLD_EVIDENCE/R6/HR1_MRES_20261030_01/PHASE_COSTS.pdf)
- [Storage groups](../../../ARCANA_WORLD_EVIDENCE/R6/HR1_MRES_20261030_01/STORAGE_GROUPS.csv)
- [Full measured windows](../../../ARCANA_WORLD_EVIDENCE/R6/HR1_MRES_20261030_01/ANNUAL_WINDOWS.csv)
- [Standalone field codec costs](../../../ARCANA_WORLD_EVIDENCE/R6/HR1_MRES_20261030_01/STANDALONE_FIELD_CODEC.csv)
- [Independent final seal](../../../ARCANA_WORLD_EVIDENCE/R6/HR1_MRES_20261030_01/FINALIZATION.json)

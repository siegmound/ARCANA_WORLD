# ARCANA R6 — Sparse Source-Backed Geological Adapter (native T0, read only)

**Date:** 2026-11-22
**Engineering parent:** `0fe8605eaf60147429e51490d1963f7f2de3f434`, FAIR coarse geology **254/254 PASS**.
**Development:** `r6/geology-sparse-source-backed-native-t0-20261122`
**Decision:** `SPARSE_ORIGINAL_T0_SOURCE_JOIN_IMPLEMENTED__PHYSICAL_GEOLOGY_AND_HISTORY_UNAUTHORIZED`.

## Mission and non-goal

ARCANA WorldSim must support later local geological research along a replayable historical timeline with minimal global overhead. A 64,800-cell grid is the **index**, not a demand to compute every rock, mineral deposit or Deep mode. The verified B-v2 package and native plate partition provide source geometries for **requested cells only**. A density measurement can later screen candidate material families, but bulk density alone is non-identifying, and **authored thermophysical density reference ranges are not local natural-rock measurements**.

This intervention introduces `src/arcana_worldsim/r6/geological_source_t0_adapter.py`, a read-only, bounded native-source adapter to the already integrated `geological_coarse_state.py` and `hierarchical_refinement.py` services. It does not touch `HistoryStore`, canonical state, shellset files, FEG or PRE, does not perform time stepping and does not create geology.

## Exact authority inputs and why they matter

Four metadata files must match their original, unmodified Git blob SHA-1, and the two binary NPZ files must match original SHA-256:

| Source | Identifier | Semantics |
|---|---|---|
| `R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json` | Git blob `695cc991c0c8008c03ff9b57f289c73a1e2b71c2` | Source model T0 field names, field package SHA and derived physical domain classes |
| `R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json` | Git blob `2fffd9c49df777a0fb72f63acde31344731c1961` | Exact original 64,800 faces and 12 plate identity |
| `R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json` | Git blob `e041e7dc91f617cf7f755b46ab36e7417d486fd0` | **Authored specialist reference** bulk crust density, distinct from natural observed rock |
| `docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json` | Git blob `e06770577ebaf549aa113a4e72ec9f6095a29c2d` | 63,620 **thermal-role** eligible cells, not a natural mineral map |
| B-v2 `R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz` | SHA256 `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e` | Original 180×360 physical crust-domain and thickness/thermal class/age grids |
| Vector `R6_T0_VECTOR_PLATE_PARTITION.npz` | SHA256 `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab` | `face_row`, `face_col`, `face_plate_id` original 64,800 faces |

**Important scientific/source correction:** Native source plate IDs are `0,1,2,3,4,5,6,7,8,9,10,11`, **not** `1..12`. This was confirmed against the manifest's real 30 adjacency groups and 12-partition source, not inferred from names. One older exploratory `experiments/t0_authorial_composition_v1/provider.py` contains an `1..12` synthetic fixture/guard for hypothetical future placement. That separate path is NOT called, and must be source-corrected and revalidated before using it for any real original plate placement.

The original `B6N8N` compact support index contains **membership hash/counts but not a complete explicit 63,620-cell array**. Thus this adapter does **not** assert that a selected cell belongs to the full B6N8N thermal eligibility set; it reports `B6N8N_thermal_membership_verified=false`. The 1,180 cells outside that particular thermal provider remain legitimate T0 geographical cells and MUST NOT be discarded from geological research. They merely lack that specialized thermal-provider applicability.

## Exact values read for at most eight requested original cells

The adapter first confirms the authentic SHA of each NPZ and metadata source, then builds the 180×360 mapping from original face arrays with an exact one-to-one 64,800 face check and plate ID range `0..11`. It then extracts:

- Native `R6G1D-Rrrr-Cccc` ID and exact face/plate index, source `physical_crust_domain_id` `1..6`, original T0 `crustal_thickness_m`.
- When continental: source authored `continental_thermal_domain_id`, `continental_reference_surface_heat_flow_w_m2`, `continental_reference_lithosphere_thickness_m`; no assumption this is a true measured LAB, T0 natural composition or groundwater state.
- When oceanic: source `oceanic_lithosphere_age_ma` where finite, no continental heat-flow or lithosphere parameters silently applied.
- Mathematical spherical surface area from the original 1° grid geometry (not a physical crust volume/mass).
- The **model-only bulk reference density** according to oceanic or continental crust material role: continental nominal **2,800 kg/m³**, authored range **2,700..2,900**; oceanic nominal **2,890 kg/m³**, authored range **2,850..2,930**. These are **reference material model choices**, not source-constrained natural geological density observations in that cell.

`actual_local_bulk_density_kg_m3`, true rock family, mineral modal fields, ores/resources, Deep accessibility, true P/T/fluid activity and physical historical checkpoint remain explicitly **null**. Even if a B-v2 field is identified as "authored", it is still a model T0 geometric/source parameter and **does not prove the actual physical lithology of ARCANA**.

The adapter uses one source-reading pass over the original small 180×360 / 64,800 face arrays per request; this is modest I/O for source-integrity verification, not expensive global mineralogical precomputation. Only up to eight records enter the report.

## Connection to already validated R6 refinement

If the caller supplies an optional existing `ARCANA_R6_GEOLOGICAL_ON_DEMAND_REQUEST_V1` JSON:
- Only `at_ma=210` is allowed, **because this adapter has verified T0 inputs but no subsequent physical history**.
- Parent cell IDs must match **exactly** the native source-selected cells.
- The request is passed to `geological_coarse_state.make_refinement_plan` with an empty, noncanonical catalog. The output holds a source anchor and four or more geometry-only child cells, without copying density, rock mass, mineral fraction, ore likelihood or Deep accessibility.
- The original R6 hierarchical grid generates request-stable child IDs. The physical time-history reconstruction `refinement.py` is NOT invoked: no checkpoint/T1 exists for it.

The output writes a new immutable `REPORT.json` plus its SHA in `MANIFEST.json`, to a directory that MUST not already exist, with source NPZ digests, source metadata Git blobs and zero HistoryStore mutations.

## FAIR test gate (PENDING)

The module has **21 expected targeted cases** (11 test functions, a five-way and seven-way parameterization = 11+4+6). They validate source metadata hashes, zero-based original plate identity, synthetic in-memory native face reconstruction, reference density interpretation, ocean/continental conditionals, duplicate face/out-of-range/replaced binary failures, fail-closed unsupported data, requested-cell bounds, geometry-only on-demand integration, no T1/HistoryStore and immutable write-once SHA.

The synthetic NPZ fixtures in tests are explicitly **not** substituted for original physical authority. Their purpose is to test indexing and error handling. The real CLI gate must open two actual external SHA-matching binaries on FAIR.

Expected unchanged previous **254** selected test cases + **21** new = **275** if collection is stable.

Suggested FAIR source sanity before attempting extraction, from checkout root:

```bash
python - <<'PY'
import json
from pathlib import Path
from arcana_worldsim.r6.repository_context import resolve_external_payload_path
root=Path.cwd()
b=json.loads((root/"R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json").read_text())
v=json.loads((root/"R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text())
for label,path in [
 ("Bv2", root/b["field_package_path"]),
 ("plate", resolve_external_payload_path(root,v["payload"]["path"]))]:
 print(label, "EXISTS" if path.is_file() else "MISSING", path)
PY
```

If either external NPZ is missing at its default source-resolved path, **do not regenerate or fabricate source binaries**. Identify the original exact files in the existing FAIR evidence/source stores and pass `--field-package /absolute/existing/path` and/or `--plate-partition /absolute/existing/path`; SHA checking will reject any wrong file.

After targeted and extended tests pass, run:

```bash
python -m arcana_worldsim.r6.geological_source_t0_adapter \
  --repo-root . --cell R6G1D-R089-C359 \
  --query experiments/geological_coarse_v1/DEMO_GEOMETRY_ONLY_QUERY.json \
  --output "$BASE/R6_GEO_NATIVE_T0_SOURCE_DEMO_NEW_01"
```

Expected: `source_bound_cells=1`, `child_geometry_count=4`, `physical_T1=null`; reference density explicitly labeled, actual density and mineralogy null. This is a **one-cell source-readback and geometry-only query**, not geologic resource simulation.

**No FAIR test of this new module is claimed yet.** Main remains FAIR 254/254.

## Next phase (conditional on FAIR success)

Produce a small, native-source-backed spatial query demonstrating authentic T0 readout, while keeping B6N8N thermal membership unverified until that separate source audit. Any "possible mineral from density" research requires externally measured/simulated sampling parameters and independent calibrated reference intervals; the current source 2,800/2,890 reference values do not constitute such measurements.

After integration, proceed to sparse *historical* material-event provenance only once a physically qualified T0->T1 model provides checkpoints and mass/energy transport. Avoid all-world material mineralization.

```text
ORIGINAL_T0_GRID_CELLS=64800
ORIGINAL_T0_PLATE_ID_MIN=0
ORIGINAL_T0_PLATE_ID_MAX=11
R6_B6N8N_THERMOPHYSICAL_ELIGIBLE=63620
EARTH_GEOCHEM_REFERENCE_RECORDS=6
SPARSE_NATIVE_EXTRACT_MAX_CELLS=8
T0_NATURAL_ROCK_DENSITY_ASSIGNED=0
T0_NATURAL_MINERAL_RESOURCE_DENSITY_ASSIGNED=0
T0_DEEP_ACCESSIBILITY_ASSIGNED=0
HISTORICAL_CHECKPOINT_BINDING=false
MECHANICAL_SOLVE_AUTHORIZED=false
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
D_024=ACTIVE
physical_T1=null
```

# R6-LAND-1 — Fastscapelib experimental landscape benchmark

## Decision

`RETAIN_R6_SURFACE_ENGINE_WITH_SELECTED_FASTSCAPE_METHODS`

Retain R6 for explicit water balance, material identities, substrate and
mobile-sediment inventories, transport, deposition, export, and regional
history contracts. Fastscapelib 0.3.0 is a candidate optional operator for
bedrock channel incision with the Stream Power Law (SPL) and its flow routing.
This benchmark does not establish production coupling or geological authority.

## Existing capabilities and overlap

| Component | Implemented behavior | Overlap / boundary |
|---|---|---|
| `geological_surface_microdomain.py` | Verifies archived T0 columns C028/C029, derives their 1-degree cell areas and shared edge, and evolves a two-support synthetic surface/cover with linear hillslope-diffusion flux. | Subsurface columns and support identity are R6-derived; relief, cover and surface law are experimental. No channel routing/SPL. |
| `regional_geological_evolution.py` | Synthetic 3x3 topography; fixed or dynamic D8 routing; annual water/runoff routing; threshold bedrock detachment; mobile/suspended material transport, deposition/export, balances, checkpoints and queries. | Broadly overlaps routing and bedrock incision, but uses a different shear-stress detachment and explicit material ledger. Grid is synthetic. |
| `hydrology_surface_coupling.py` | Two-support water storage and precipitation, internal hydrologic substeps, Manning discharge, sediment capacity, material-ID-preserving transport, cover/substrate erosion, deposition/export, and water/sediment balances. | Not a generic landscape evolution solver. Fastscapelib Python SPL has no such water or sediment inventory/transport/deposition state. |
| `gflex_flexure_adapter.py` | Optional gFlex 1.3.0 F1D/F2D elastic equilibrium from explicit load stress, mesh, elastic parameters and boundaries; returns deflection/provenance and applies increments only to an explicitly synthetic 3x3 region. | Load-response mechanics, not erosion or sediment transport. No gFlex call occurred in this benchmark. |

Fastscapelib also offers raster linear diffusion, which overlaps the R6
surface microdomain's diffusion candidate. It was not used. This test isolates
the distinct SPL bedrock-incision method. Fastscapelib's Python eroders are
bedrock SPL and raster linear diffusion; its documentation places sediment
transport/deposition in the separate Fortran library, not this Python API.

## Candidate and API review

The selected package is **Fastscapelib Python 0.3.0**, the latest stable PyPI
release observed for this work, not the higher-level `fastscape` package and
not FastScapeLib-Fortran. The public API provides `RasterGrid`,
`SingleFlowRouter`, `FlowGraph.update_routes()`, `FlowGraph.accumulate()` and
`SPLEroder.erode(elevation, drainage_area, dt)`. Raster grids use 8-neighbor
connectivity. The tested eroder solves bedrock SPL implicitly; the documented
equation is

`dh/dt = -K A^m S^n`,

where `A` is upslope drainage area and `S` is local slope. Flow accumulation
of a unit per-area source returns drainage area. The lower raster row was
`FIXED_VALUE`, used by `FlowGraph` as base level; other edges were `CORE`.
Routes were recomputed from the updated surface at each step.

For `m=0.5`, `n=1`, area in m² and time in years, K has units yr⁻¹. This follows
from the equation and chosen units; the synthetic values were not calibrated.
The experiment uses no uplift or water state. The API reports incision depth
and slope-correction counts. The benchmark integrates lowering over node
areas as a **diagnostic volume only**. This is not tracked sediment mass,
export, or a conservation assertion.

PyPI lists Python >=3.10, NumPy and GPL-3.0 for Fastscapelib 0.3.0. The
separate `fastscape` model package is BSD-3-Clause; these packages and licenses
must not be conflated. Fastscapelib was installed only in an isolated temporary
Python 3.12.10 environment. No shared or project environment was changed.
Distribution should receive a GPL-3.0 compatibility review before bundling or
linking Fastscapelib.

Official references: [Fastscapelib PyPI 0.3.0 metadata](https://pypi.org/project/fastscapelib/),
[Python SPLEroder API](https://fastscapelib.readthedocs.io/en/latest/api_python/_api_generated/fastscapelib.SPLEroder.html),
[eroder scope and deposition limitation](https://fastscapelib.readthedocs.io/en/latest/guide_eroders.html),
[grid and boundary conventions](https://fastscapelib.readthedocs.io/en/latest/guide_grids.html),
[flow accumulation units](https://fastscapelib.readthedocs.io/en/latest/guide_flow.html),
and [official Python river-profile example](https://fastscapelib.readthedocs.io/en/latest/examples/river_profile_py.html).

## Actual synthetic numerical experiment

The run used Fastscapelib 0.3.0, Python 3.12.10, NumPy 2.5.4 on Windows.
The raster has 61 x 61 nodes at 1,000 m spacing (60 x 60 km node-to-node
span). Initial relief is a synthetic north-south 0.012 planar slope plus a
180 m Gaussian dome. The lower row is fixed at 0 m; other edges are core nodes.
One single-flow router and the SPL bedrock eroder were used. Routing and
unit-source drainage area were recomputed each step.

All cases used 20 steps of 500 years (10,000 model years), `m=0.5`, `n=1`; only
K changed:

| Case | K (yr⁻¹) | Diagnostic lowering volume (m³) | Maximum lowering (m) | Lowered nodes |
|---|---:|---:|---:|---:|
| Half K | 1.0e-5 | 20,377,265,969.32 | 32.379 | 3,599 |
| Baseline | 2.0e-5 | 40,549,500,486.13 | 65.594 | 3,599 |
| Double K | 4.0e-5 | 81,766,468,457.63 | 131.517 | 3,599 |

Maximum final drainage area ranged from 686 to 745 km² as routing changed.
The monotonic response demonstrates sensitivity to K, not calibration or
prediction. The reported volume integrates height lowering over grid node
areas; it does not identify a sediment destination. The lower row remained
fixed, elevations were finite, and returned incision depths were nonnegative.
No sediment mass conservation, deposition, or composition is claimed.

Repeat baseline was bitwise identical. A 10 + 10 step run restarted from saved
elevation had zero maximum difference from the continuous 20-step result.
This is an elevation-only restart for this stateless operator and exact
parameters, not a water/sediment checkpoint or R6 checkpoint qualification.

Final output bundle: `outputs/r6_land1_fastscapelib_20261026_02/`. Manifest
SHA256 `d94424355f50b42367060a0310a00ed0e05c2e55fccfe5a15434ed52692d198f`;
`RESULT.json` SHA256 `a9052346888c1fab06de97b1130c15056212048aaf8af6ae60ba98ebbfbf3213`;
sidecar SHA256 `3ef431a46c14e5bc42141986993bb026557060b7223f0bc1bade48a24016d515`.
Member sizes, hashes and sidecar content were rechecked locally. The manifest
does not self-hash. It records the tested source HEAD and exact source hashes.
No output bundle was staged for Git.

Measured benchmark time was 0.1332 s for three K cases, a repeated baseline,
a 10 + 10 restart and result sealing. Process peak working set was 43,520,000
bytes (process-lifetime peak, not run delta); Python `tracemalloc` peak was
1,949,192 bytes. This small local run is not a scaling study. Output was
401,605 bytes.

## Comparison and proposed integration contract

Fastscapelib SPL is not equivalent to R6's shear-stress detachment or its
transport-capacity/deposition laws. It does not consume R6 precipitation,
infiltration, storage, material IDs or substrate inventories; it lowers a
bedrock elevation field. R6 surface diffusion is also distinct from SPL.
There are no shared calibrated parameters or same-equation error metrics, so
no equivalence or accuracy superiority is claimed. The measured capability
gain is a tested 2-D raster SPL operator and flow graph beyond the existing
two-column surface microdomain. R6 remains necessary for hydrology and material
accounting.

Proposed future handoff, not implemented here:

1. Input a versioned surface state with stable node/cell IDs, coordinate frame,
   resolution, areas, time, topography in metres, base-level mask, source hash
   and explicit substrate/material identity. Do not treat R6's synthetic 3x3
   as a suitable physical basin or plate mesh without scale justification.
2. Return updated elevation, incision per node, routing identity and exact
   parameter/config/source identities. If R6 hydrology uses another support,
   require an explicit conservative mapping matrix; validate coverage, areas,
   and duplicate/omitted IDs.
3. Keep incision separate from material transfer until density/composition and
   destination laws exist. For gFlex, derive signed `Δm` from material
   inventories and map it to the flexural mesh, then compute `Δq=Δm*g/A`.
   Elevation change alone is not a load. Close transport, deposition and export
   ledgers before using mass changes as load.
4. Apply gFlex as the increment between successive total-deflection fields,
   exactly once. Track flexure separately from incision, deposition and uplift
   to prevent double-counting, then recompute drainage on updated topography.

No gFlex coupling ran here. Synthetic K values are not material properties,
the raster is not R6 geography, and no synthetic label is promoted to
lithology. Fastscapelib Python did not provide deposition in this selected
version/API; R6's sediment engine must remain the material-conservation owner
in any future coupling.

## Validation and authority

- Fastscapelib tests plus R6 regional, surface-microdomain and hydrology
  regressions: **29 passed** on Windows in the isolated environment.
- `py_compile` and `git diff --check`: PASS.
- Earlier same-task output `_01` and test temporary output are preserved;
  `_02` is the final result bundle with corrected synthetic row/column identity
  metadata.
- No Fair, ASPECT, long run, ShellSet/Solver, MPI, canonical data or
  WORLD_HISTORY operation occurred.

All scientific and canonical gates remain unchanged. Resource scope,
SI1/F2AV qualification, ARCANA material/forcing inputs, and physical vertical
response remain unresolved.

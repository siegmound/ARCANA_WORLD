# R6-SURF-2 — Fastscapelib SPL to R6 material and hydrology coupling

**Decision:** `SURF2_CONSERVATIVE_COUPLING_DEMONSTRATED`
**Scope:** `SYNTHETIC_ENGINEERING_ONLY`
**Source baseline before this work:** `672d4b9f8ff9d3eaf2b8673c48ad386f69b49c1a`

## Result

The optional Fastscapelib Python 0.3.0 bedrock-incision operator was run in a
two-year, 6×6 synthetic landscape. Its calculated lowering was mapped by exact
node control areas to a synthetic R6 3×3 region, converted to a synthetic bulk
rock mass, deducted from substrate, and placed in the existing R6 mobile
sediment ledger. R6 then ran its existing annual water routing, sediment
transport, deposition and outlet-export operators. The fine bedrock raster and
the R6 regional material/hydrology state were both checkpointed. The verified
continuous two-year and 1+1-year runs agree exactly for the regional state and
fine bedrock raster.

This demonstrates a conservative *synthetic code coupling*. It does not map
the experiment to C028/C029 or another ARCANA geographic support, and it does
not qualify the chosen coefficients or model as regional geology.

## Implemented handoff and operators

The mapping is explicitly synthetic: Fastscapelib's node-centered 6×6 raster
has 500 m spacing. Each of nine non-overlapping 2×2 node-control-area blocks
maps to one cell-centered synthetic R6 3×3 region cell. The four node areas in
each block sum to exactly 1,000,000 m²; all 36 nodes occur once. The mapping
does not assert that either grid is an ARCANA region or that the grid identities
are geographically interchangeable.

For each 1-year geomorphic step the executed bedrock operator is the implicit
Stream Power Law (SPL):

`∂h/∂t = −K A^m S^n`, with `m=0.5`,
=1`, synthetic `K=2e−4 yr⁻¹`,
Fastscapelib SingleFlowRouter drainage area `A`, and local slope `S`. The
bottom row is fixed base level; the other raster edges are core nodes. The
Python API's `SPLEroder` is bedrock channel incision, not a sediment
transport/deposition model. Its documentation also warns that the numerical
scheme is not implicit in drainage area, so large steps can affect transient
solutions. This pilot uses one-year steps only. [SPLEroder API](https://fastscapelib.readthedocs.io/en/latest/api_python/_api_generated/fastscapelib.SPLEroder.html),
[erosion methods and limitations](https://fastscapelib.readthedocs.io/en/latest/guide_eroders.html)

At each raster node, removed volume is calculated as
`max(h_before − h_after, 0) × node_control_area`. Volumes are summed within
their mapped region cell and converted using the declared synthetic bulk
density `2700 kg/m³`. The adapter rejects nonfinite/negative lowering or a
transfer exceeding available substrate. It removes that mass from the
synthetic substrate and adds the same material ID and mass to the R6 mobile
sediment compartment. R6's own substrate detachment is disabled for this case,
so SPL and the R6 bed-shear detachment law do not erode the same stock.

R6 then advances one annual hydrology step with prescribed synthetic
precipitation `0.15 m/year` per cell, dynamic topographic routing, and its
existing mobile/suspended/deposit/export rules. The R6 runoff is calculated
from its water balance; it is not substituted for Fastscapelib's accumulated
drainage area. Both operators advance over the same declared one-year external
step. No conversion from a geomorphic 500-year step to hourly hydrology is
assumed. The routing graph is recomputed at each annual R6 step after the
previous step's erosion/deposition has updated surface geometry.

A review of the first coupling output exposed a geometric consistency defect:
the second SPL handoff replaced regional surface elevation with bare bedrock,
leaving deposited mass in inventory but dropping its thickness from geometry.
The handoff now reconstructs surface elevation as mapped bedrock elevation
plus thickness of existing deposits. The regression checks every recorded
cell's geometric residual against 64 binary64 epsilons at its elevation scale.
The final run's maximum residual is `1.4210854715202004e−14 m`.

## Measured run

Final corrected bundle: `outputs/r6_surf2_fastscapelib_20261026_03/` (local,
untracked, not modified after sealing). `MANIFEST.json` SHA256:
`810eab2b9c12521231858f7c64a64e8087b711bd49ca2753b79f9de9c4da86d1`.
Its two members were independently rehashed: `RESULT.json` (537,209 bytes,
SHA256 `02f87bad8dc59f6e748990f34888847fb33be99783c205164c0446661d63abbd`)
and `RESULT.json.sha256` (78 bytes, SHA256
`17065abdd11c615fdd9878326a038375736318f8868cfc2fee53bfc4f4fe77e0`). The
sidecar digest content matches `RESULT.json`. Total bundle size including the
manifest is 537,621 bytes. The manifest has no self-hash; its digest above is
calculated externally.

Runtime was Python 3.12.10, NumPy 2.5.4 and Fastscapelib 0.3.0 in the isolated
LAND-1 environment. The run took `0.4321873 s`; the process-lifetime peak
working set was `46,497,792 bytes`, and Python `tracemalloc` peak was
`2,659,295 bytes` (Python allocations only). These are local pilot
measurements, not resource qualification. The result records baseline HEAD and
SHA256 identities for the runner, adapter, tests and reused R6 sources; these
hashes identify files but are not signed provenance.

| Step | SPL volume removed | Converted synthetic mass | Maximum node lowering |
| --- | ---: | ---: | ---: |
| Year 1 | 41,903.93296370232 m³ | 113,140,619.00199626 kg | 0.02118247424801467 m |
| Year 2 | 41,901.179107032505 m³ | 113,133,183.58898777 kg | 0.02117400464615571 m |

Total SPL removal was `83,805.11207073482 m³` or `226,273,802.59098403 kg`.
The volume-to-mass identity residual was `2.9802322387695312e−8 kg`, from
floating-point accumulation. R6 global solid-mass residuals were `[0.0, 0.0]
kg`, within the R6-derived roundoff limits; water residuals were `[0.0, 0.0]
m³`. All material compartments remained finite and nonnegative. Final regional
stocks were:

- substrate: `2,429,773,726,197.409 kg`
- mobile sediment: `77,929,266.68939902 kg`
- suspended sediment: `27,158,806.7450887 kg`
- deposited sediment: `25,376,035.777044408 kg`
- cumulative exported sediment: `95,809,693.37945187 kg`

The initial solid inventory was `2.43e12 kg`; final in-domain stocks plus
cumulative export close to that inventory. Water started at zero. Over two
years the synthetic regional precipitation input was `2.7e6 m³`; the output
balance includes evapotranspiration, infiltration, outlet export and final
storage, with zero residual. The `K=0` control transferred no SPL material and
left the solid stocks unchanged. In the SPL-enabled case, R6's C07 downstream
target changed from C06 to C08 for year 2, then back to C06 for year 3, as
recorded in the routing-event timeline. The experiment demonstrates dynamic
routing under the combined incision/deposition topography; it does not isolate
incision as the sole cause of the route changes. Fastscapelib's own basin map
did not change in this two-year run, while local raster slopes did change.

R6's bedrock-detachment law was disabled, but its sediment transport,
deposition, storage and export were active. The output load diagnostic was
calculated from regional solid-stock changes via the existing mass-to-pressure
helper. It was not passed to gFlex; no flexure, `Te`, Deep-energy change, thermal
or mechanical update was performed.

## Tests and review

Using the isolated Python 3.12.10 / NumPy 2.5.4 / Fastscapelib 0.3.0
environment, the focused coupling tests plus LAND-1, regional-geology,
geological-surface, hydrology-surface and unified-multiphysics regressions
passed: **40 passed, 0 failed, 0 skipped**. `py_compile` passed for the new
adapter, runner and test. The tests cover exact non-overlapping area mapping,
nonzero SPL-to-material transfer, R6 mass and water balances, nonnegative
stocks, slope changes, a dynamic-routing event, zero-erosion control, and
continuous versus 1+1 checkpoint continuation including tamper rejection.

The tested checkpoint SHA256 is
`d90f6a61e18c6109515763b1dcdd9f5a6f437c7fb80af799ed2f7dfe32679669`; its claim
is integrity-only, not authentication or production restart qualification.
The earlier same-task bundles `_01` and `_02` are preserved; `_03` is the
corrected final evidence bundle.

## Reuse, licensing and remaining conditions

`geological_surface_microdomain.py` remains a small support-aware surface and
cover-transport model; `hydrology_surface_coupling.py` supplies a more detailed
synthetic hydraulic/sediment-capacity operator; `regional_geological_evolution.py`
owns the regional annual water/material ledger and dynamic routing used here;
`unified_multiphysics_microdomain.py` coordinates thermal, Maxwell, Deep and
surface states where supported. The gFlex adapter can convert mass changes to
load and run flexure when supplied a valid grid and parameters. SURF-2 uses the
regional ledger and the gFlex mass-to-pressure helper only; it does not combine
the other surface/hydrology operators or execute gFlex. This avoids duplicating
their process laws in the new adapter.

The Fastscapelib Python API currently documents bedrock channel SPL and raster
hillslope diffusion, while sediment transport/deposition modules are described
for the separate Fortran library. Fastscapelib is GPL-3.0 according to its
PyPI project metadata. Keep it an optional development integration until the
project's distribution and licensing strategy is reviewed; it is not added as a
required dependency. [PyPI license and 0.3.0 package](https://pypi.org/project/fastscapelib/),
[Fastscapelib Fortran model scope](https://fastscape.org/fastscapelib-fortran/)

Before applying this to a regional ARCANA simulation, the project still needs:

1. A geographically verified coordinate/area remapping between an ARCANA
   support and the Fastscapelib grid, including spatial resolution and
   boundary-condition justification.
2. Real substrate density, material identity/provenance and available
   thickness, plus an explicit cover-shielding or cover-aware SPL rule.
3. Calibrated/justified erodibility and exponents, time-dependent forcing and
   timestep-sensitivity evidence.
4. A declared coupling contract with R6 hydrology (including how drainage
   area relates, or does not relate, to actual discharge), material transport,
   deposition and export.
5. A separate license/distribution decision before Fastscapelib becomes
   required or is redistributed with ARCANA.

All scientific and canonical gates remain unchanged, including
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

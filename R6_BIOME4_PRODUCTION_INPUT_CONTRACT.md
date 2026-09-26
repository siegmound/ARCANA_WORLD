# R6 BIOME4 production input contract

Decision: **BIOME4_CONTRACT_FROZEN__INPUT_PROVIDER_GAPS_REMAIN**

Verdict: **PASS_BIOME4_PRODUCTION_INTERFACE_FROZEN_WITH_EXPLICIT_INPUT_GAPS**

Next action: **TARGETED_BIOME4_INPUT_GAP_CLOSURE**

R5 remains the development/discovery and legacy reference world. R6 is a new clean simulation from initial conditions; reproducing the R5 final world is not the objective. P7S is not reopened. P7S climate binding remains proven within its prior 65-cell cohort, while BIOME4 climate binding is partial.

## Runtime identity

- Source: jedokaplan/BIOME4, pinned commit 4ad9dff37eed339fce88c0fa5802757f86a3ef44.
- Model identity: BIOME4 v4.2b2; numerical-core baseline 3c03014223a2dff3deb264e908e3fe44a3232541.
- biome4driver.f90 SHA256: 962dc05e5621f3fe3b31bbf2fe4fb82686e81613a98c766f24fd2683e0b7dece.
- biome4.f SHA256: 23b5194b7b2ca25439f9a97e4f55c147c78ee9198c5f953ca2fac8c4ce689968.
- Runtime executable SHA256: 2d55d3e381cb22ea0b6734cde88e1c97669ffcdc3c3eacb4332cd140dc53b9cd.
- Compiler/toolchain recorded by P7R: gfortran 13.3.0, WSL2 Ubuntu 24.04.1, netCDF-C 4.9.2, netCDF-Fortran 4.5.4.
- Recorded build: autoreconf -if && ./configure; make LDFLAGS= LIBS="$(nf-config --flibs)". CFLAGS -g -O2; FFLAGS -O2 -ftree-vectorize -march=native -fno-math-errno -fPIC -ffree-line-length-none -fopenmp -I/usr/include. The linker override is build-only; scientific source was not changed. The exact linker expansion was not retained; the executable SHA256 is the exact R6 runtime identity.
- Do not upgrade implicitly. No runtime execution occurred for this contract.

## Frozen climate interface

Every BIOME4 cell/checkpoint requires:

- tmp[12]: monthly climatological mean, °C; no annual-to-monthly reconstruction.
- pre[12]: monthly total, mm/month; finite and nonnegative. Reject invalid values rather than relying on the driver’s negative-value clipping.
- sun[12]: sunshine_percent_possible, percent in [0,100].
- If and only if a provider’s cloud cover is semantically bound as percent, an explicit adapter may compute sunshine_percent_possible = 100 - cloud_percent. No precipitation- or temperature-derived sunshine. Prefer native sun; do not use ambiguous internal cldp as the R6 semantic name.

Driver behavior was inspected: it accepts sun or cld; cld is converted to 100-cloud before the core, while sun is passed through. The driver’s native Tmin fallback is 0.006*tcm^2 + 1.316*tcm - 21.9; if used, label it MODEL_DERIVED. Policy: DIRECT_TMIN_IF_GOVERNED, otherwise BIOME4_NATIVE_DERIVED_TMIN.

Krapp’s governed 200/125 ka cache has annual temperature only, plus 12 monthly precipitation fields. Monthly temperature is therefore unknown at those anchors; do not synthesize a seasonal cycle. Krapp precipitation’s P7S-adjudicated source semantics are annualized rates in mm/year divided by 12 to mm/month under the recorded equal-month 360-day candidate calendar. Do not reopen that adjudication. Beyer has monthly temperature (°C) and monthly precipitation (mm/month) on a native time×month grid for 120–0 ka. Its cloudiness variable name is present in the root-variable inventory, but audited metadata did not bind dimensions, temporal semantics, or units: it is available, not yet bound.

## Other mandatory inputs

**CO₂:** P7C authority is ready with interpolation. Use exactly external_age_BP=(ARCANA_age_ka*1000)+200, then linear interpolation within adjacent NOAA ice-core records only—no extrapolation, fitting, smoothing, or spline. Units are ppm; authority is external global atmospheric forcing analog. The existing 12 anchor values and provenance are in the JSON contract; no refit/replacement occurred.

**Elevation:** the driver accepts elv in metres and defaults to sea level when absent. That fallback is prohibited for R6. No full-grid, all-anchor R6 elevation authority is bound. Legacy P7S elevation/shoreline evidence is only a 65-cell cohort and is not promoted into a global R6 static field.

**Soil:** consume P7S exactly: dz_cm=[5,10,15,30,40,100], six whc_mm_per_cm and ksat_mm_per_hr layers. Derive 0–30 cm WHC as the thickness integral over layers 1–3, 30–200 cm over layers 4–6; derive Ksat as thickness-weighted means over the same groups (30 and 170 cm denominators). The former [10]*6 geometry is diagnostic-only. Historical soil remains unknown; 0 ka has only the 65 P7S cohort profiles, not a full R6 grid.

## Grid and missing-state gate

Before any evaluation, compare climate and soil grids for exact dimensions, longitude and latitude coordinate values/order, cell centers, normalized dimension order, and per-cell land/missing masks. No implicit resampling, axis reversal, or driver repair. The previously adjudicated Beyer coordinate-attribute swap for the bounded cohort does not waive this full R6 check.

BIOME4_INPUT_ELIGIBLE requires all monthly climate values, sunshine semantics, scalar CO₂, valid elevation policy, direct or model-derived Tmin, all six WHC/Ksat layers and dz, and exact grid/mask compatibility. If any required value or authority is unknown, label the ecological result BIOME4_INPUT_UNKNOWN; do not write numeric defaults or run that cell/checkpoint.

### Governed-anchor availability matrix

| Age ka | Monthly temperature | Monthly precipitation | Sunshine/cloud | CO₂ | Elevation | Soil | Eligible |
|---:|---|---|---|---|---|---|---|
| 200 | Unknown (Krapp annual only) | Bound (Krapp normalized to mm/month) | Absent in governed Krapp cache | Bound, 246.322316986 ppm | Unknown | Unknown historical | No |
| 125 | Unknown (Krapp annual only) | Bound (Krapp normalized to mm/month) | Absent in governed Krapp cache | Bound, 276.558531714 ppm | Unknown | Unknown historical | No |
| 120 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound (cloudiness metadata incomplete) | Bound, 269.863602146 ppm | Unknown | Unknown historical | No |
| 20 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound | Bound, 190.692277889 ppm | Unknown | Unknown historical | No |
| 15 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound | Bound, 229.010309770 ppm | Unknown | Unknown historical | No |
| 14 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound | Bound, 238.573763937 ppm | Unknown | Unknown historical | No |
| 13 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound | Bound, 238.479607168 ppm | Unknown | Unknown historical | No |
| 12 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound | Bound, 250.365183946 ppm | Unknown | Unknown historical | No |
| 11 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound | Bound, 265.288171312 ppm | Unknown | Unknown historical | No |
| 10 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound | Bound, 263.552110694 ppm | Unknown | Unknown historical | No |
| 5 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound | Bound, 269.630899985 ppm | Unknown | Unknown historical | No |
| 0 | Bound (Beyer, °C) | Bound (Beyer, mm/month) | Available, not bound | Bound, 277.242989323 ppm | Unknown for full R6 grid | Partial: 65 legacy profiles only | No |

These statuses record source support, not newly materialized full-grid arrays. P7S’s 65-cell scope must not be generalized to the complete R6 grid.

## Output and execution contract

Retain biome_code, dominant_woody_pft, NPP_by_PFT[13] (annual, g m⁻²), and LAI_by_PFT[13] (maximum LAI; validate output units from metadata when implementing). Retain input/runtime/output SHA256, coordinate/mask hashes, valid/missing counts, driver log and exit evidence. BIOME4 runoff and soil moisture are DIAGNOSTIC_ONLY unless separately adjudicated; they do not become hydrological authority. Production diag=false.

Evaluate only checkpoints actually consumed by the R6 ecological pipeline; do not run all 12 anchors merely because they are governed anchors. Identical runtime, input hashes, namelist/CO₂, bounds, and coordinates should yield byte-identical outputs under the same runtime where feasible; verify empirically only when a future production run is authorized.

## Exact remaining gaps

1. Monthly temperature for 200/125 ka (the governed Krapp cache has annual temperature only).
2. Bind Beyer cloudiness dimensions, monthly temporal semantics, and units before any cloud-to-sunshine adapter.
3. Bind full-grid R6 elevation/topography at requested checkpoints; no sea-level fallback.
4. Bind complete soil state on the R6 grid; historical P7S unknowns remain unknown.
5. Validate exact full-grid climate/soil coordinate and mask compatibility.

Production contract: **frozen**. Production execution authorized: **false**. Provider acquisition and BIOME4 execution were not performed. ARCANA_WORLD_CURRENT_STATE.md, execution indexes, and P7S artifacts were not modified by this contract task.

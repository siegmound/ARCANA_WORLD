# ARCANA R6 — Zenodo 8304793 FAIR 39 curves / 555 point adjudication

**Date:** 2026-11-20. **Source code tested:** `65f72f63dd1db693cdf53e5225ed93a8fd557a68`.

**Decision:** `PASS_FAIR_RAW_SOURCE_INTEGRITY_AND_TWO_COLUMN_DATA_SHAPE__PAPER_SUPPORTS_STRESS_STRAIN__G2_CALIBRATION_BLOCKED`.

## 1. Grounded FAIR execution, exact scope

User's FAIR terminal shows seven tests passed in 0.06s and the source-bound
inspector emitted:

```text
status: PASS_SOURCE_ARCHIVE_INTEGRITY_AND_RAW_SHAPE__EXPERIMENTAL_COLUMN_SEMANTICS_UNQUALIFIED
files: 39
families: gleason_tullis 18, zhou 21
numeric_rows: 555
solver_runs: 0
physical_T1: null
```

The original Zenodo ZIP's published MD5 and its FAIR-recorded SHA-256
were verified at the preceding acquisition. The operator displayed
the first **six** curve records; each had 2 numeric columns.
We have NOT independently inspected the entire local FAIR JSON bytes
in the authoring environment. Hence do not claim all 39 records' actual
two-column count, absent anomalies or independent experiment identity
from those six preview records.

Sample A: `gleason_tullis_fig3a_1.dat`, 19 rows, X
[0.00025, 0.05627], Y [0.57436, 85.63143].

Sample B: `zhou_16_1050_1.dat`, 25 rows, X [0.00012,
0.08934], Y [0.88437, 451.38301]. Another `zhou_16_1050_2.dat`
continues X 0.08981–0.10181 with descending Y 451.39–407.33,
consistent with a strain-rate-stepped transient trace, not a single
monotone stress–strain equilibrium test. This is an interpretation, not
verified member-by-member protocol labeling.

## 2. Primary paper determines the physical observable

Source: Masuti, Muto & Rybacki (2023), *Transient Creep of Quartz and
Granulite at High Temperature Under Wet Conditions*, JGR Solid Earth,
DOI https://doi.org/10.1029/2023JB027762 .
Source archive: https://doi.org/10.5281/zenodo.8304793 .

The published paper's Figure 2 (quartz) and Figures 5–6 (granulite/
feldspar) show **Stress (MPa) versus Strain (%)** under imposed
constant or stepped strain-rate protocols. The raw file X range
0..~0.1, paired with ~0..450 Y, is numerically COMPATIBLE with
fractional strain X and stress MPa Y; however the specific source
figure numbering, original plotted normalization, rate schedule
and all per-member temperature/P metadata have not been individually
bound. Those raw-axis conversions remain **provisional**.

**The 555 digitized data points are NOT 555 independent empirical
(`stress_pa`, `strain_rate_s_inv`) measurements.** A strain–stress
trace is temporally correlated; multiple `.dat` fragments may come
from one rate-stepping experiment. Source experiment count and
train/holdout groups must be determined from paper sample/test IDs,
not from the filename count. Never pass these 555 rows directly into
`fit_g2_dislocation_laboratory()`, whose model is the stationary
log-linear Arrhenius *rate–stress* relationship, not a transient
history constitutive response.

The 2023 authors fit a **nonlinear Burgers rheology** with transient
Kelvin and steady Maxwell terms, strain-hardening/internal stress
and time/strain evolution. Their fitted transient parameters depend
on the steady-state reference/prior; the paper itself shows different
parameterizations under alternative steady-state assumptions.
Published nonlinear modeling code is referenced in the paper at
https://doi.org/10.5281/zenodo.8304760 .
No attempt to fit or reproduce it has occurred in ARCANA.

## 3. Temperature/pressure applicability to source T0

R6 T0 plate5:8 crust: **280–1051.558196831 K**
(approximately 6.85–778.41°C), with model lithostatic proxy up to
~0.754 GPa.

From Masuti (2023) section 2, GT95 quartzite: **900–1100°C**,
confining **1.5–1.7 GPa**, wet quartzite around 0.15 wt% H2O.
Zhou (2017) wet granulite: **900–1150°C** with ~0.17±0.05 wt%
H2O, constant/stepped rates ~3.3×10^-6 to 5×10^-5 s^-1.
The original Zhou (2017) abstract reports **300 MPa** confinement;
this must still be linked to per-curve IDs before physical use.

Therefore neither material's **temperature-supported experimental
domain overlaps the T0 crustal range**: even the lowest 1173.15 K
experiment is at least ~121.592 K above T0's maximum.
GT95 also has no overlap in pressure range with the reported
crustal pressure proxy. Zhou may overlap in pressure but not
temperature. Some T0 mantle temperatures overlap laboratory
temperatures, but quartzite/granulite cannot be assigned the mantle
mineralogical role on that basis.

This new dataset can support an **external laboratory numerical
reproduction**, not full regional G2 physical calibration.

## 4. Honest next scientific work

1. Map original GT95 Figure 3a, 3b, 6a, 6b, 6c and Zhou test IDs,
   stress/strain axes, imposed rates and P/T/water condition to
   each digitized `.dat`, preserving segments of the same experiment
   as a single train/holdout group.
2. If replaying transient rheology, obtain and inspect the
   Masuti (2023) model code, and reproduce published lab stress–strain
   traces with a nonlinear Burgers candidate, not a steady-state
   single-line fit. Compare held-out *whole experiments*, not
   adjacent points.
3. Separately locate empirical low-temperature brittle/friction and
   plasticity mechanisms valid at source 280–1051.558 K and
   relevant P/timescale, plus actual ARCANA authorial mineralogy/water.
4. G3 provider remains UNKNOWN; no Earth5-derived ARCANA basal
   force or fabricated force balance.

```text
G2_LAB_RAW_INSPECTION_FAIR=7/7_PASS
ZENODO_DIGITIZED_POINTS=555
G2_AXIS_PAPER_CLASSIFICATION=STRESS_MPA_VS_STRAIN_PERCENT
RAW_X_FRACTION_ENCODING=PROVISIONAL_NOT_RATIFIED
ALL_39_FILES_PER_CURVE_PROTOCOL_VERIFIED=false
DIRECT_STEADY_CREEP_REGRESSOR_ADMISSIBLE=false
ARCANA_G2_MATERIAL_FIT=null
ARCANA_G3_MANTLE_FORCE=null
D-024=ACTIVE
mechanical_solve_authorized=false
physical_T1=null
```

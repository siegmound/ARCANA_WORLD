# ARCANA R6 — Independent G2/G3 evidence discovery and mechanism adjudication

**Date:** 2026-11-20. **Scope:** T0 210 Ma, 5:8 (8×8) and 5:8:11
(16×16), noncanonical EXPLORE. **Source parent:** `18695cf43e18906065c6c5dd01559166e217bf98`.
**Decision:** `G2_MECHANISM_SPLIT_SOURCE_DISCOVERY_PASS__RAW_LAB_MEASUREMENTS_NOT_INGESTED__G3_EARTH_BENCHMARK_ONLY`.

The companion machine-readable source ledger is
`experiments/plate58_deforming_explore_v1/R6_G2_G3_EXTERNAL_EVIDENCE_REGISTER_20261120.json`.
It distinguishes original measurements, digitized curves, published fitted
coefficients, model-derived outputs, and raw archives **not downloaded**.
No G2/G3 physical parameters have been newly calibrated.

## 1. Why the existing full-column single-creep target is invalid

The source 5:8 crust spans **280–1051.558 K**, with lithostatic
pressure proxy approximately **0–0.754 GPa** and unknown real
mineralogical, water and effective-pressure state. This is not a
measured rock-specific constitutive curve. Literature mechanisms
must not be mixed:

| Mechanism | Sources found | Fit status |
|---|---|---|
| Existing-fracture friction / brittle sliding | Wang (2024) Bentheim sandstone saw-cut fault, controlled 5 MPa pore pressure; Byerlee (1978) physical review | Direct continuum Drucker–Prager inference **not** valid |
| Low-T dislocation glide / Peierls regime | Strozewski et al. (2021); Sly et al. (2023), quartz/feldspar nanoindentation at **23–500°C** | Hardness→yield is **model-dependent**; no direct triaxial power-law input |
| Hot dislocation creep | Masuti et al. (2023) digitized GT95 quartz/partially molten granulite; published wet-quartz law (2021) | Available for **research & source inspection**, not whole-column T0 |
| High-P in-situ quartz | Medina et al. (2026) 25–1199°C at **1.39–3.1 GPa**, strain rate **10^-6–10^-5 s^-1** | P range has **no intersection** with reported 5:8 crust proxy (≤0.754 GPa) |
| HPHT failure-mode database | Han et al. (2026), 1711 compiled points from 156 papers | Strength/failure class, **not** complete creep observations; raw curated database on request |

There is no qualified single `A,n,E,V,r` relationship spanning this
T0 upper-to-lower crust. The previously published GT95 laboratory
temperature window **1173.15–1373.15 K** is wholly above the
source crust's max **1051.558 K**. The existing
`g2_g3_empirical_calibration.fit_g2_dislocation_laboratory` is an
estimator for **triaxial differential-stress hot dislocation data**.
It must not be applied to nanoindentation, direct fault-friction or
yield-strength observations by relabeling the measured variable.

**Hydration nuance:** Ceccato et al. (2022) found comparable
low-temperature quartz indentation strength in the particular
studied natural wet/dry samples; this does **not** imply ARCANA
has zero pore pressure or that water has no role in high-temperature
creep. Different water mechanisms, time scales and stress states
must remain distinct.

## 2. Best real datasets to inspect

**A — Zenodo 8304793, primary ingestion priority.**
Masuti, Muto & Rybacki (2023) published a CC BY 4.0 archive of
*digitalized* creep results from GT95 (quartz) and Zhou et al. (2017)
(partially molten granulite):
https://zenodo.org/records/8304793

Visible public metadata: `data.zip`, **13.2 kB**,
`md5:fbb1734ffce3eb94e4ef974f5b2cb7be`.
This is not the same as new instrument-level raw measurements. The
archive members/columns have **not yet been inspected** and therefore
no individual data rows, measured fugacities, pressures, or strain
rates have been assumed from its contents. Its high-T mechanism
does not itself validate the cold T0 crust.

**B — low-temperature indentation data.**
Strozewski et al. (2021),
https://repository.library.washu.edu/data/86/ (DOI
`10.7936/av98-vn87`); Sly et al. (2023),
https://repository.library.washu.edu/data/93/ .
These support candidate *low-T plasticity calibration after* choosing
an appropriate nanoindentation-to-yield and Peierls constitutive
relation. Merely converting hardness to an ASPECT/SHELLS creep
stress is not justified.

**C — pore-controlled saw-cut rock friction.**
Wang (2024), https://data.mendeley.com/datasets/vkhs4y4sjv/1 ,
DOI `10.17632/vkhs4y4sjv.1`. Reported conditions: Bentheim sandstone,
35–75 MPa confinement, 5 MPa pore pressure, 1–10 μm/s load-point
velocity; the deposit contains MATLAB `.mat` logs and a README.
Fault loading speed is not automatically distributed rock strain
rate. This can help *candidate fault-interface friction* but
cannot assign ARCANA material or fit continuum Drucker–Prager.

**D — further but not ready for direct fits.**
Medina et al. (2026) Dryad X-ray and instrument archive:
https://datadryad.org/dataset/doi:10.5061/dryad.rbnzs7hqv .
Han, Huang & Santamarina (2026), DOI
`10.1007/s00603-026-06047-0` published on November 4:
curated 1711-point rock HPHT stiffness/strength/failure mode
database available on request from corresponding author, with
strain rate unreported in many cases. A complete log-linear
creep fit cannot be justified from those records without original
rate measurements.

## 3. G3: true reference model rather than invented ARCANA traction

Bird's historical Earth5/SHELLS digital archive is now accessible:
https://doi.org/10.5061/dryad.cnp5hqcjb .
Published on Dryad 2025-11-04; a ~415.64 MB archive contains
Earth5-049 input/output, the new Earth5_update workflow and
global data. The 2026 Earth5 paper (DOI `10.1029/2025JB032949`)
explicitly points to this archive. These are useful to independently
**replay and benchmark how global plate-force inversion, friction,
kinematic BC and inferred mantle torque interact**.

Earth5 Earth velocities, Earth rheology, GPE and mantle tractions are
**not authentic physical providers for ARCANA**; importing them
as plate 5/8/11 forces would create false geological evidence.
Inversion of plate motion into basal stress is also nonunique.
Therefore the real G3 basal drag `beta`, deep mantle flow, mechanical
LAB, basal normal support, and 32/64 real exterior-cut tractions
remain `null`.

**Recommended G3 route:** benchmark the *method* against the
Earth5 archive only if necessary, then build a source-consistent
ARCANA coupled mantle/lithosphere model or explicitly ratify
a bounded alternative mantle prior, including uncertainty and
force/torque/energy budget, before any physical G3 solve.

## 4. Immediate FAIR source acquisition (NO mechanical run)

In the existing `arcana-r6-linux` workstation, stage the small
publicly cited dataset in a **new, immutable external evidence**
directory. Do not write it into canonical runtime or a previously
sealed evidence folder:

```bash
set -euo pipefail
BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
OUT="$BASE/R6_G2_ZENODO_8304793_RAW_NEW_01"
mkdir "$OUT"        # fail if already exists; do not overwrite old evidence
curl --fail --location --retry 3 --silent --show-error \
  'https://zenodo.org/records/8304793/files/data.zip?download=1' \
  --output "$OUT/download.part"
printf 'fbb1734ffce3eb94e4ef974f5b2cb7be  %s\n' \
  "$OUT/download.part" | md5sum --check -
mv "$OUT/download.part" "$OUT/data.zip"
sha256sum "$OUT/data.zip" | tee "$OUT/SHA256.txt"
unzip -Z -1 "$OUT/data.zip" | tee "$OUT/ARCHIVE_MEMBERS.txt"
ls -lh "$OUT/data.zip"
```

If download or checksum fails, stop and leave an explicit failure;
do **not** relabel another archive as this source. Then review the
archive member schema, laboratory units, stress conventions and
experiment-group provenance. Do not use image digitization values
as original laboratory measurements. The file has **not** been
downloaded within this authoring environment, so no claim of
complete source acquisition or new fit is made.

The 415 MB Earth5 archive is deliberately deferred: download only
if a specific G3 parity question cannot be answered using the
existing ShellSet code and source docs.

## Decision and hard gates

```text
G2_LABORATORY_SOURCE_DISCOVERY=PASS
G2_RAW_MEASUREMENT_INGESTION=PENDING
G2_COMPOSITE_MECHANISM_CALIBRATION=NOT_AUTHORIZED
G2_MINERALOGY_AND_WATER_AUTHOR_RATIFICATION=PENDING
G3_EARTH5_COMPARATIVE_BENCHMARK_SOURCE=IDENTIFIED
G3_ARCANA_MANTLE_FORCE_PROVIDER=UNKNOWN
G3_BASAL_NORMAL_AND_LATERAL_FORCE=UNKNOWN
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
```

No code was changed in this source-research commit. No new FAIR
tests are required to validate research citations. This work
closes *source discovery*, not the world physical model.

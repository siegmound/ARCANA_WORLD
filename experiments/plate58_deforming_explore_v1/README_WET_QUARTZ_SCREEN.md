# ARCANA R6 — G2 follow-up: alternative wet-quartz PT screen, source-bound

**Context:** operator FAIR verified `rheology_envelope.py` at `bc25c5b9...`:
12/12 tests PASS, 9 PRE source nodes, **0/81** crust temperature samples in the Gleason–Tullis 900–1100°C laboratory window, and slope-only eCreep error **4.197428237611889%**. This does not validate a constitutive law. Do not rerun those tests.

## The scientific question

Can any sampled T0 crustal locations be compared against the **broader** wet-quartz literature without pretending the original GT1995 parameterization is calibrated at the T0 temperatures?

The new module compares:
- the reported **700–1200°C** range for wet-quartzite experiments aggregated by Tokle et al. (2019), DOI `10.1016/j.epsl.2018.10.017`;
- the **<560 MPa** low-pressure and **700–1600 MPa** high-pressure data-group split in the 2021 wet-quartz natural/experimental calibration, DOI `10.1029/2020JB021302`.

**These criteria come from different study datasets, and a joint window intersection is a SCREEN, not experimental validation.** The original 2021 calibration contains a water fugacity exponent; T0 PRE has no validated water/fugacity field. Do **not** calculate a 'new wet quartz stress', an LR record, a brittle cap, an integrated strength, or force a simulation based on these bounds.

The module joins the prior G2 output to source T0 PRE by original node ID and both SHA-verified manifests. It evaluates pressure analytically from source layer densities and g=9.82 m/s², preserves all 81 T samples, and reports the cross-study applicability categories. A sample matching a nominal T/P group remains `constitutive_law_validated=false`.

## FAIR run in the existing isolated, clean checkout

```bash
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

python -m pytest -q tests/test_r6_plate58_wet_quartz_screen.py

STAGE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_STAGE_NEW_01
PRIOR=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G2_PT_ENVELOPE_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_WET_QUARTZ_SCREEN_NEW_01
python -m experiments.plate58_deforming_explore_v1.wet_quartz_screen "$STAGE" "$PRIOR" "$OUTPUT"
```

Output: `PT_SCREEN.json` and `MANIFEST.json` in a new exclusive evidence directory. No write to existing FAIR evidence and no solver call.

## Decision after screen

A numerical pass **cannot** itself ratify the new rheology. If the putative field water state remains unknown, physical G2 is blocked. The next meaningful action is **a single authorial decision**: explicitly select a bounded *noncanonical* effective crust/mantle/fragile/water scenario and a G3 exterior/basal closure, or maintain T1 blocked. Do not continue creating micro-gates indefinitely; D-024.

# R6 G2/G3 — Laboratory rate-and-state fault analogue (not planetary physical closure)

**Date:** 2026-11-21. **Parent main R6:** `973a2e04c7afdb6d24367f0460669f73f21204da`.
**Status:** REAL LAB SOURCE IDENTIFIED, MODEL CODE IMPLEMENTED, REAL SOURCE INGESTION PENDING.
**Decision:** `LAB_RSF_FITTED_PARAMETER_ENGINE_IMPLEMENTED__REAL_PANGAEA_ROWS_AND_ARCANA_FAULT_BINDING_OPEN`.

## Why this is the next substantive physical step

The R6 original 81/289-node G2/G3 internal and full candidate G3 force-channel assembly passed FAIR 134/134. However, the source 2D P1 shell cannot itself generate independent fault slip traction; G2 lithology and mantle/cut/normal boundary sources remain unknown. This intervention implements a **real published physical fault friction model family** instead of adding another geometric KKT or numerical timestep comparison.

## Source and applicability

- Ikari, M. J. & Kopf, A. J. (2020), *Table 2: Model-extracted velocity-dependent friction parameters*, PANGAEA DOI `10.1594/PANGAEA.921284`: https://doi.pangaea.de/10.1594/PANGAEA.921284
- Parent collection `10.1594/PANGAEA.921293`: https://doi.pangaea.de/10.1594/PANGAEA.921293
- Ikari & Kopf (2017), *Seismic potential of weak, near-surface faults revealed at plate tectonic slip rates*: https://pmc.ncbi.nlm.nih.gov/articles/PMC5706663/
- Source context: Earth natural weak/clay-rich fault gouge in direct shear, **20°C**, **10 MPa effective normal stress**, **3.5% NaCl brine**. Table 2 gives inverse-model-derived fitting parameters, **not independent original sensor measurements**.
- The laboratory mineralogy/hydration/fault geometry do not specify ARCANA plate 5:8:11 original T0 fault materials. No lab result can be transferred to ARCANA T0 without a separately supported geological/material/pressure/kinematic binding.

## Physical equations, implemented only within source laboratory support

With `v0` the row's fitted reference step speed, `a`, `b_i`, `Dci`, and state variable `theta_i`, the chosen one/two-state Dieterich slowness model gives:

```text
delta_mu = a ln(v/v0) + sum_i b_i ln(theta_i*v0/Dci)
dtheta_i/dt = 1 - v*theta_i/Dci
theta_i(t+dt) = Dci/v + (theta_i(t)-Dci/v)*exp(-v*dt/Dci)
delta_mu_steady = (a-sum_i b_i)*ln(v/v0)
delta_tau = effective_normal_stress * delta_mu
```

`v0/v` and `Dci` are converted from µm/s and µm into SI. The code calculates **conditional immediate and steady changes** at the row's own fitted velocity step with an explicit assumed initial state `theta_i(v0)=Dci/v0`. This is NOT necessarily the actual experiment's initial state. The code does not invent `mu_ref`, absolute shear traction, fault-normal/slip orientation, pore pressure, or 3D contact. Velocity extrapolation and effective normal stress outside the study's declared 10 MPa condition are rejected.

The source parser verifies an exact 19-column catalog layout, DOI/author metadata, source SHA256, sample/experiment identity, `a-b` consistency within declared published rounding precision, one/two-state parameter pairing, nonfinite values and pressure/velocity support. It fails closed on changed or ambiguous source exports; no relabeling of synthetic rows.

## Software and tests

- `experiments/plate58_deforming_explore_v1/g2_g3_rsf_pangaea.py`: source importer, source fit-to-model velocity step prediction, exact-aging single/two-state law, lab differential stress, immutable report/manifest CLI.
- `tests/test_r6_g2_g3_rsf_pangaea.py`: 13 synthetic benchmark cases covering direct effect, two/one-state steady limit, analytical time-step semigroup, source identity/schema and validity rejection, and write-once report provenance.
- Local isolated authoring check: **13/13 PASS**, Python 3.13.5. These tests use manufactured table rows, not the downloaded real PANGAEA dataset.
- Full FAIR R6/G2/G3 regression and PANGAEA original data ingest: **PENDING**; no merge into main until independently checked.

## Next FAIR procedure

Use a clean isolated checkout and activate the existing `arcana-r6-linux` environment. Run the targeted test, then download the official table **into a new evidence directory** as PANGAEA documents its `Accept: text/tab-separated-values` download format:

```bash
set +e
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git fetch origin r6/g2g3-lab-fault-rate-state-20261121
git switch --detach 9c567c4424419c431a76cb6303d58451cc312b60
conda activate arcana-r6-linux
export PYTHONPATH=src:.
export PYTHONDONTWRITEBYTECODE=1
python -m pytest -q -ra --tb=short tests/test_r6_g2_g3_rsf_pangaea.py
echo "RSF_TEST_EXIT_CODE=$?"
```

Only if PASS, run empirical source ingestion:

```bash
set +e
BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
E="$BASE/R6_G2_G3_PANGAEA921284_RAW_NEW_01"
if mkdir "$E"; then
  curl --fail --location --retry 3 --silent --show-error \
    -H 'Accept: text/tab-separated-values' \
    'https://doi.org/10.1594/PANGAEA.921284' \
    -o "$E/pangaea_921284.tab"
  RC=$?
  if [ "$RC" -eq 0 ]; then
    sha256sum "$E/pangaea_921284.tab"
    python -m experiments.plate58_deforming_explore_v1.g2_g3_rsf_pangaea \
      --source "$E/pangaea_921284.tab" \
      --output "$E/INGEST_NEW_01"
    echo "RSF_INGEST_EXIT_CODE=$?"
  else
    echo "PANGAEA_DOWNLOAD_FAILED_EXIT_CODE=$RC"
  fi
else
  echo "EVIDENCE_FOLDER_EXISTS_OR_CANNOT_CREATE: $E"
fi
```

Do not alter existing evidence directories or replace publisher metadata with guessed headers. A failed data parse is a **real source compatibility issue**, not permission to fabricate a fit.

## Next scientific dependency

Source-only RSF values are **changes** in friction, not actual G3 loads. Physical source-side fault identification, `mu_ref` or equivalent absolute stress, real ARCANA gouge mineralogy/hydration, temperature/pressure/rate applicability, effective normal traction, independent fault trace DOFs including the authentic triple parent `34587`, basal mantle and outer-cut forces and full GPE owner remain unresolved. The existing continuous 8 shared interface DOFs **cannot represent physical slip jumps without new source-justified sidedness**.

```text
LAB_RSF_EARTH_MODEL_CODE=IMPLEMENTED
LAB_RSF_SOURCE_REAL_ROWS_INGESTED=NO
EARTH_LAB_FIT_REPRODUCED=NO
ARCANA_G2_ROCK_RATIFIED=false
ARCANA_FAULT_LAW_RATIFIED=false
G3_PHYSICAL_TRACTION_CLOSED=false
MECHANICAL_SOLVE_AUTHORIZED=false
physical_T1=null
D_024=ACTIVE
WORLD_HISTORY_PRODUCTION_AUTHORIZED=false
```

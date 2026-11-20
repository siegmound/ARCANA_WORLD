# ARCANA R6 — Zenodo 8304793 raw archive acquired on FAIR; introspection pending

Date: 2026-11-20. Operator source evidence at
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_ZENODO_8304793_RAW_NEW_01/data.zip`.

## Source integrity from FAIR terminal (operator reported)

- `curl` downloaded 13,201 bytes.
- Original Zenodo advertised MD5: `fbb1734ffce3eb94e4ef974f5b2cb7be`.
- Terminal: `download.part: OK`, matching that MD5.
- Independently reproducible SHA-256 from the operator's terminal:
  `1af973f4e96afe615d0f3eee94020b8a2186422392d3bcfa85699fd01f41327d`.
- Operator-reported ZIP member list: **39 .dat members** under `data/`,
  of which 18 match `gleason_tullis_fig3a/3b/6a/6b/6c_*.dat` and 21
  `zhou_16_{1050,1100,1125,1140,1150}_*.dat`.
- Preserved original raw archive; no canonical data modified.

This is a **real acquisition, with checksum verified by FAIR**, not merely a
dataset name in the register. Nevertheless the archive's actual numeric
line contents have **not yet been read by the authoring environment**.
Filenames alone cannot prove axes, units, pressure/temperature series or
how many distinct original experiments are represented. Zenodo labels this
collection digitized data from *figures*, not direct instrument logs:
https://zenodo.org/records/8304793 .

## New code: fail-closed, source-bound RAW .dat inspector

`experiments/plate58_deforming_explore_v1/zenodo_raw_dat_inspector.py`
reads the ZIP in memory, without extracting or altering members. It verifies
published MD5 and the FAIR-reported SHA-256, permits only `data/*.dat`,
rejects duplicates/path traversal/unexpected contents and requires
exact source-inventory family counts (18+21). For every file it reports
original member SHA-256, numeric-column cardinality, raw first lines,
unparsed/header lines, row count and unlabelled numeric min/max. It NEVER
infers stress, strain rate, temperature, pressure, fugacity, experiment
independence, rock mineralogy or material parameters from those raw numbers.

Unit tests used equivalent self-contained synthetic ZIPs (7/7 local PASS).
The pushed module and the actual source ZIP must now be verified on FAIR;
do not call this a FAIR pass yet.

### FAIR command (isolated checkout; not a mechanical solve)

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
git fetch origin r6/multiphysics-integration-20261026
git switch --detach FETCH_HEAD
git rev-parse HEAD
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH=src:.
export PYTHONDONTWRITEBYTECODE=1

python -m pytest -q tests/test_r6_g2_zenodo_raw_dat_inspector.py

BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
python -m experiments.plate58_deforming_explore_v1.zenodo_raw_dat_inspector \
  "$BASE/R6_G2_ZENODO_8304793_RAW_NEW_01/data.zip" \
  "$BASE/R6_G2_ZENODO_8304793_INSPECT_NEW_01"

python - <<'PY'
import json
from pathlib import Path
p = Path("/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_G2_ZENODO_8304793_INSPECT_NEW_01/RAW_DAT_INSPECTION.json")
x=json.loads(p.read_text())
print("Source",x["source_archive_sha256"])
print("Figure families",x["observed_figure_file_family_counts"])
print("Numeric rows",x["total_numeric_rows"])
for family in ("gleason_tullis", "zhou"):
    examples=[r for r in x["source_member_records"] if r["figure_family"]==family]
    for r in examples[:3]:
        print(r["name"],"rows",r["numeric_data_rows"],
              "columns",r["observed_numeric_column_counts"],
              "first",r["raw_first_nonempty_lines"][:3],
              "range",r["numeric_column_min_max_without_units"])
PY
```

The script rejects an existing inspection directory. If checksum, member
inventory or numeric schema fails, keep the failure as evidence and do not
patch or guess data. Only after reading this output and relevant figure
captions can we choose an eligible training/holdout structure or a valid
mechanism-specific calibrator.

## Scientific gate

The published material concerns **wet high-temperature transient creep** of
quartz aggregates and partially molten granulite, attributed to original
Gleason–Tullis (1995) and Zhou et al. (2017) sources. It is not a measured
source for cold 280–1051.558 K ARCANA crust. A plotted curve ordinate
may be time, strain, stress or another quantity; its meaning must be sourced,
not inferred from the file naming scheme. Do not pass arbitrary two-column
digitizations to `fit_g2_dislocation_laboratory` as real stress/rate pairs.

No G3 deep mantle or basal physical forcing is obtained by this dataset.

```text
G2_EXTERNAL_DIGITIZED_DATA_ACQUISITION=FAIR_SHA_CHECKED
G2_ARCHIVE_DATA_ROWS_AND_AXIS_UNITS=NOT_YET_INSPECTED
G2_PHYSICAL_CONSTITUTIVE_CALIBRATION=BLOCKED
G3_PHYSICAL_MANTLE_FORCE=UNKNOWN
D-024=ACTIVE
mechanical_solve_authorized=false
physical_T1=null
```

#!/usr/bin/env bash
# FAIR-only science gate; no canon, no physical WorldSim T1.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
if [ "$PWD" != "$ROOT" ]; then
  echo "FAIL: execute from source checkout root" >&2
  exit 2
fi
case "$(command -v python)" in
  */arcana-r6-linux/bin/python) ;;
  *) echo "FAIL: activate FAIR conda arcana-r6-linux" >&2; exit 2 ;;
esac

export PYTHONPATH="$ROOT/src:$ROOT"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

BASE="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
mkdir -p "$BASE"
TARGET_LOG="$BASE/R6_EXP_THERMAL_100Y_TARGET_34.log"
FULL_LOG="$BASE/R6_EXP_THERMAL_100Y_FULL_338.log"
OUT="$BASE/R6_EXP_THERMAL_100Y_NONCANONICAL_NEW_01"

for f in "$TARGET_LOG" "$FULL_LOG"; do
  if [ -e "$f" ]; then
    echo "FAIL: evidence log already exists (no overwrite): $f" >&2
    exit 3
  fi
done
if [ -e "$OUT" ]; then
  echo "FAIL: evidence directory already exists (no overwrite): $OUT" >&2
  exit 3
fi

echo "EXPERIMENTAL_SOURCE_HEAD=$(git rev-parse HEAD)"
echo "EXPERIMENTAL_AUTHORITY=EXPERIMENTAL_NONCANONICAL_ONLY"
echo "--- Targeted thermal-column tests (expected 34) ---"
python -m pytest -q -ra --tb=short \
  tests/test_r6_experimental_thermal_column_100y.py \
  2>&1 | tee "$TARGET_LOG"
grep -Eq '(^|[[:space:]])34 passed in ' "$TARGET_LOG" || {
  echo "FAIL: expected 34 targeted cases" >&2; exit 4;
}

echo "--- Selected R6 regression (expected 338) ---"
python -m pytest -q -ra --tb=short \
  tests/test_r6_g2_g3_full_external_candidate.py \
  tests/test_r6_g2_g3_source_core_exterior_stitch.py \
  tests/test_r6_g2_g3_core_exterior_source_runner.py \
  tests/test_r6_g2_g3_coupled_weak_form.py \
  tests/test_r6_g2_g3_source_coupled_runner.py \
  tests/test_r6_g2_viscoplastic_explore.py \
  tests/test_r6_g2_nodal_source_bridge.py \
  tests/test_r6_g2_g3_nonlinear_layered.py \
  tests/test_r6_g2_exact_thermal_validity.py \
  tests/test_r6_g2_g3_empirical_calibration.py \
  tests/test_r6_g3_force_budget.py \
  tests/test_r6_g3_gpe_force_accounting.py \
  tests/test_r6_g3_gpe_hydrostatic.py \
  tests/test_r6_g3_spherical_exterior.py \
  tests/test_r6_g2_g3_rsf_pangaea.py \
  tests/test_r6_g2_g3_rsf_linear_stability.py \
  tests/test_r6_g2_g3_t0_contact_material_applicability.py \
  tests/test_r6_t0_geochemical_reference_library.py \
  tests/test_r6_t0_authorial_bulk_composition.py \
  tests/test_r6_geological_coarse_on_demand.py \
  tests/test_r6_geological_sparse_native_source_adapter.py \
  tests/test_r6_geological_research_query_dt.py \
  tests/test_r6_experimental_thermal_column_100y.py \
  2>&1 | tee "$FULL_LOG"
grep -Eq '(^|[[:space:]])338 passed in ' "$FULL_LOG" || {
  echo "FAIL: expected 338 selected regression cases" >&2; exit 4;
}

echo "--- Source-anchored explicitly synthetic 100-year numeric run ---"
python -m arcana_worldsim.r6.experimental_thermal_column \
  --repo-root . \
  --config experiments/thermal_column_100y_v1/SYNTHETIC_OCEANIC_REFERENCE_COLUMN.json \
  --output "$OUT"

python - "$OUT/REPORT.json" "$OUT/MANIFEST.json" <<'PY'
import hashlib, json, sys
from pathlib import Path

report_path=Path(sys.argv[1])
manifest_path=Path(sys.argv[2])
r=json.loads(report_path.read_text())
m=json.loads(manifest_path.read_text())
assert m["report_sha256"]==hashlib.sha256(report_path.read_bytes()).hexdigest()
assert r["schema"]=="ARCANA_R6_EXPERIMENTAL_NONCANONICAL_100Y_COLUMN_REPORT_V1"
assert r["authority"]=="EXPERIMENTAL_NONCANONICAL_ONLY"
assert r["source_original_T0_cell"]=="R6G1D-R089-C359"
assert r["source_plate_id"]==8
assert r["source_model_crust_thickness_m"]==6500
assert r["source_field_sha256"]=="39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e"
assert r["source_plate_sha256"]=="a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
assert r["requested_duration_years"]==100
assert r["natural_ARCANA_T0_temperature_profile_qualified"] is False
assert r["natural_ARCANA_T1_temperature_profile_created"] is False
assert r["world_history_production_authorized"] is False
assert r["automatically_canonicalizable"] is False
assert r["history_store_mutations"]==0
assert r["physical_T1"] is None
assert r["actual_mineral_or_ore_or_Deep_assignments"]==0
assert r["all_energy_balances_pass"] is True
levels=r["convergence_levels"]
assert [(x["n_cells"],x["step_years"]) for x in levels] == [
    (50,1),(100,0.25),(200,0.0625)]
errors=[x["max_abs_error_against_synthetic_exact_k"] for x in levels]
assert errors[2]<errors[1]<errors[0] and errors[2]<0.001
assert all(x["diffusive_cfl"]<=0.5 and x["energy_balance_pass"]
    and abs(x["energy_balance_residual_j_m2"])<=x["energy_balance_tolerance_j_m2"]
    and x["physical_historical_T1"] is None
    for x in levels)
print("FAIR_THERMAL_NUMERIC_BENCHMARK=PASS")
print("FAIR_NUMERICAL_ERRORS_K=",errors)
print("FAIR_ENERGY_RESIDUALS_J_M2=",
      [x["energy_balance_residual_j_m2"] for x in levels])
print("EXPERIMENTAL_NONCANONICAL_ONLY=TRUE")
print("CANONICAL_PHYSICAL_T1=NULL")
PY
echo "FAIR_EXPERIMENT_100Y_TARGET_34=PASS"
echo "FAIR_EXPERIMENT_100Y_SELECTED_338=PASS"
echo "FAIR_EXPERIMENT_100Y_SYNTHETIC_NUMERIC_GATE=PASS"

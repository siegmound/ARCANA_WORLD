#!/usr/bin/env bash
# FAIR evidence gate for the separate synthetic 1000-year thermal-column study.
# This is numerical validation only; no ARCANA physical T1 / WorldHistory.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
if [ "$PWD" != "$ROOT" ]; then
  echo "FAIL: run from checkout root" >&2
  exit 2
fi
case "$(command -v python)" in
  */arcana-r6-linux/bin/python) ;;
  *) echo "FAIL: activate FAIR conda arcana-r6-linux" >&2; exit 2;;
esac
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "FAIL: source checkout has tracked modifications" >&2
  exit 2
fi

export PYTHONPATH="$ROOT/src:$ROOT"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1

BASE="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
mkdir -p "$BASE"
TARGET_LOG="$BASE/R6_EXP_THERMAL_1000Y_TARGET_30_NEW02.log"
FULL_LOG="$BASE/R6_EXP_THERMAL_1000Y_FULL_368_NEW02.log"
OUT="$BASE/R6_EXP_THERMAL_1000Y_NONCANONICAL_NEW_02"

for target in "$TARGET_LOG" "$FULL_LOG" "$OUT"; do
  if [ -e "$target" ]; then
    echo "FAIL: evidence path exists; do not overwrite: $target" >&2
    exit 3
  fi
done

echo "EXPERIMENTAL_1000Y_SOURCE_HEAD=$(git rev-parse HEAD)"
echo "EXPERIMENTAL_1000Y_AUTHORITY=EXPERIMENTAL_NONCANONICAL_ONLY"
echo "--- Targeted new 1000y tests; expected 30 ---"
python -m pytest -q -ra --tb=short \
  tests/test_r6_experimental_thermal_column_1000y.py \
  2>&1 | tee "$TARGET_LOG"
grep -Eq '(^|[[:space:]])30 passed in ' "$TARGET_LOG" || {
  echo "FAIL: expected 30 targeted tests" >&2; exit 4;
}

echo "--- Selected R6 regression including prior 338 + new 30 = 368 ---"
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
  tests/test_r6_experimental_thermal_column_1000y.py \
  2>&1 | tee "$FULL_LOG"
grep -Eq '(^|[[:space:]])368 passed in ' "$FULL_LOG" || {
  echo "FAIL: expected 368 selected R6 regression cases" >&2; exit 4;
}

echo "--- Real source-anchored but SYNTHETIC 1000y numeric experiment ---"
python -m arcana_worldsim.r6.experimental_thermal_column_1000y \
  --repo-root . \
  --config experiments/thermal_column_1000y_v1/SYNTHETIC_OCEANIC_REFERENCE_COLUMN.json \
  --output "$OUT"

python - "$OUT/REPORT.json" "$OUT/MANIFEST.json" <<'PY'
import hashlib, json, sys
from pathlib import Path
rpath,mpath=(Path(p) for p in sys.argv[1:])
r=json.loads(rpath.read_text())
m=json.loads(mpath.read_text())
assert m["report_sha256"]==hashlib.sha256(rpath.read_bytes()).hexdigest()
assert r["schema"]=="ARCANA_R6_EXPERIMENTAL_NONCANONICAL_1000Y_COLUMN_REPORT_V1"
assert r["authority"]=="EXPERIMENTAL_NONCANONICAL_ONLY"
assert r["source_original_T0_cell"]=="R6G1D-R089-C359"
assert r["source_plate_id"]==8
assert r["source_field_sha256"]=="39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e"
assert r["source_plate_sha256"]=="a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
assert r["requested_duration_years"]==1000
assert r["original_100y_config_git_blob"]=="ea1355175145894edf8a8e24268bf843b9368bdf"
assert r["governance_policy_git_blob"]=="75658d37b12ac3d2c3b3fed5b9e56203a6ae3cf1"
assert r["source_material_is_not_natural_T0_measurement"] is True
assert r["initial_temperature_is_synthetic"] is True
assert r["natural_T0_temperature_qualified"] is False
assert r["automatic_promotion_authorized"] is False
assert r["canonical_history_created"] is False
assert r["world_history_production_authorized"] is False
assert r["history_store_mutations"]==0
assert r["actual_rock_mineral_ore_or_Deep_assignments"]==0
assert r["physical_T1"] is None
assert m["physical_T1"] is None and m["no_history_store_writes"] is True
levels=r["insulated_1000y_convergence_levels"]
assert [(x["n_cells"],x["time_steps"]) for x in levels]==[
 (50,1000),(100,4000),(200,16000)]
for key in ("insulated_1000y_numerical_errors_k",
            "fixed_temperature_1000y_manufactured_errors_k"):
 e=r[key]
 assert len(e)==3 and 0<=e[2]<e[1]<e[0] and e[2]<0.001
assert all(x["energy_balance_pass"]
           and abs(x["energy_balance_residual_j_m2"])<1
           for x in levels)
assert len(r["one_factor_reference_sensitivities"])==8
assert all(x["physical_T1"] is None for x in r["one_factor_reference_sensitivities"])
assert len(r["fixed_temperature_1000y_manufactured_levels"])==3
assert all(x["energy_balance_pass"]
           for x in r["fixed_temperature_1000y_manufactured_levels"])
assert r["fixed_temperature_1000y_matched_initial_state"]["energy_balance_pass"]
assert r["fixed_temperature_1000y_matched_initial_state"][
    "max_abs_error_against_synthetic_exact_k"] is None
assert r["fixed_vs_insulated_max_abs_difference_at_five_sampled_centres_k"]>0
print("FAIR_1000Y_NUMERICAL_STUDY=PASS")
print("FAIR_1000Y_INSULATED_ERRORS_K=",r["insulated_1000y_numerical_errors_k"])
print("FAIR_1000Y_FIXED_BOUNDARY_ERRORS_K=",r["fixed_temperature_1000y_manufactured_errors_k"])
print("FAIR_1000Y_REFERENCE_SENSITIVITY_CASES=8")
print("FAIR_1000Y_PERMANENT_NONCANONICAL=TRUE")
print("CANONICAL_PHYSICAL_T1=NULL")
PY

echo "FAIR_1000Y_TARGET_30=PASS"
echo "FAIR_1000Y_SELECTED_368=PASS"
echo "FAIR_1000Y_EXPERIMENTAL_STUDY=PASS"

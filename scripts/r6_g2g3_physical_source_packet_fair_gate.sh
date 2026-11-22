#!/usr/bin/env bash
# R6 original T0 G2/G3 physical support extraction; input law gaps remain UNKNOWN.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
if [ "$PWD" != "$ROOT" ]; then
  echo "FAIL: run from source repository root" >&2; exit 2
fi
case "$(command -v python)" in
  */arcana-r6-linux/bin/python) ;;
  *) echo "FAIL: activate FAIR conda arcana-r6-linux" >&2; exit 2;;
esac
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "FAIL: dirty tracked code; read-only source gate" >&2; exit 2
fi
export PYTHONPATH="$ROOT/src:$ROOT"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

BASE="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
TARGET="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_TARGET_38_NEW01.log"
FULL="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_SELECTED_406_NEW01.log"
OUT8="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW01"
OUT16="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW01"
mkdir -p "$BASE"
for path in "$TARGET" "$FULL" "$OUT8" "$OUT16"; do
  if [ -e "$path" ]; then
    echo "FAIL: evidence already exists; cannot overwrite $path" >&2
    exit 3
  fi
done

# Prefer unique, read-only SHA-chain discovery. If distinct certified chains
# coexist, specify ALL four authoritative source directories explicitly.
ARGS=(--evidence-root "$BASE")
if [ -n "${R6_MULTI_DIR:-}${R6_INTERFACE_DIR:-}${R6_NODAL_DIR:-}${R6_FORCE_DIR:-}" ]; then
  for var in R6_MULTI_DIR R6_INTERFACE_DIR R6_NODAL_DIR R6_FORCE_DIR; do
    if [ -z "${!var:-}" ]; then
      echo "FAIL: all four R6_*_DIR paths must be provided" >&2; exit 3
    fi
  done
  ARGS=(--multiscale "$R6_MULTI_DIR" --interface "$R6_INTERFACE_DIR" \
        --nodal "$R6_NODAL_DIR" --force "$R6_FORCE_DIR")
fi

echo "PHYSICAL_SOURCE_PACKET_SHA=$(git rev-parse HEAD)"
echo "PHYSICAL_SOURCE_PACKET_AUTHORITY=SOURCE_MODEL_REFERENCE_NOT_PHYSICAL_RATIFICATION"
echo "--- 38 new source-packet targeted tests ---"
python -m pytest -q -ra --tb=short \
  tests/test_r6_g2_g3_physical_source_packet.py 2>&1 | tee "$TARGET"
grep -Eq '(^|[[:space:]])38 passed in ' "$TARGET" || {
  echo "FAIL: expected 38 new cases" >&2; exit 4;
}

echo "--- 406 selected R6 regression tests including 38 targeted ---"
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
  tests/test_r6_g2_g3_physical_source_packet.py \
  2>&1 | tee "$FULL"
grep -Eq '(^|[[:space:]])406 passed in ' "$FULL" || {
  echo "FAIL: expected 406 selected cases" >&2; exit 4;
}

echo "--- Read ORIGINAL FAIR FEG/PRE + four source manifest chain (8x8) ---"
python -m experiments.plate58_deforming_explore_v1.g2_g3_physical_source_packet \
  --repo-root . "${ARGS[@]}" --extent 8 --output "$OUT8"
echo "--- Read ORIGINAL FAIR FEG/PRE + four source manifest chain (16x16) ---"
python -m experiments.plate58_deforming_explore_v1.g2_g3_physical_source_packet \
  --repo-root . "${ARGS[@]}" --extent 16 --output "$OUT16"

python - "$OUT8" "$OUT16" <<'PY'
import hashlib, json, sys
from pathlib import Path
for d,extent in zip((Path(p) for p in sys.argv[1:]),(8,16)):
    i=json.loads((d/'SOURCE_INDEX.json').read_text())
    p=json.loads((d/'UNSELECTED_PHYSICAL_PROPOSAL.json').read_text())
    m=json.loads((d/'MANIFEST.json').read_text())
    expect=(81,128,8,120,32) if extent==8 else (289,512,8,504,64)
    assert tuple(i['counts'][k] for k in (
        'original_parent_nodes','source_original_full_basal_triangles',
        'source_core_basal_triangles','source_exterior_basal_triangles',
        'original_external_cut_edges'))==expect
    assert (34587 in i['original_parent_node_order'])==(extent==16)
    assert len(i['source_original_PRE_model_T0_thermal_profiles_by_parent_node'])==expect[0]
    assert all(len(v)==16 for v in i['source_original_PRE_model_T0_thermal_profiles_by_parent_node'].values())
    assert i['source_PRE_is_authored_thermal_material_model_not_natural_mineralogy']
    assert i['thermal_reference_is_not_100y_or_1000y_synthetic_pilot_output']
    assert p['source_index_sha256']==hashlib.sha256(json.dumps(
        i,sort_keys=True,separators=(',',':'),ensure_ascii=False,
        allow_nan=False).encode()).hexdigest()
    assert p['physical_T1'] is None and i['physical_T1'] is None
    assert p['physical_solve_authorized'] is False
    assert p['canonical_history_write_authorized'] is False
    assert len(p['remaining_physical_groups'])==8
    assert all(g['status']=='SOURCE_AUTHORITY_GAP'
               for g in p['remaining_physical_groups'].values())
    for slot in ('material_rock_phase_by_parent_node',
                 'water_effective_pressure_by_parent_node',
                 'constitutive_law_and_lab_validity_by_parent_node',
                 'outer_cut_physical_traction_N_per_m',
                 'full_basal_tangential_normal_load_Pa'):
        assert all(v is None for v in p[slot].values())
    assert m['physical_T1'] is None and m['HistoryStore_mutations']==0
    for file,digest in m['files'].items():
        assert hashlib.sha256((d/file).read_bytes()).hexdigest()==digest
    print(f'FAIR_ORIGINAL_T0_G2G3_{extent}X{extent}_SOURCE_INDEX=PASS')
    print(f'FAIR_ORIGINAL_T0_G2G3_{extent}X{extent}_PHYSICAL_INPUTS=UNKNOWN')
assert json.loads((Path(sys.argv[1])/'SOURCE_INDEX.json').read_text())[
    'source_hashes']==json.loads((Path(sys.argv[2])/'SOURCE_INDEX.json').read_text())[
    'source_hashes']
print('FAIR_G2G3_SOURCE_SHA_CHAIN=PASS')
print('MECHANICAL_SOLVE_AUTHORIZED=FALSE')
print('CANONICAL_PHYSICAL_T1=NULL')
PY

echo "FAIR_G2G3_SOURCE_PACKET_TARGET_38=PASS"
echo "FAIR_G2G3_SOURCE_PACKET_SELECTED_406=PASS"
echo "FAIR_G2G3_SOURCE_PACKET_REAL_T0_READBACK=PASS"

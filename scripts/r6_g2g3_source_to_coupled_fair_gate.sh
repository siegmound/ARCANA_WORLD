#!/usr/bin/env bash
# R6 source-authentic T0 -> NONCANONICAL coupled G2/G3 authoring handoff.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
if [ "$PWD" != "$ROOT" ]; then
  echo "FAIL: run this FAIR source gate from repository root" >&2; exit 2
fi
case "$(command -v python)" in
  */arcana-r6-linux/bin/python) ;;
  *) echo "FAIL: activate conda arcana-r6-linux" >&2; exit 2;;
esac
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "FAIL: tracked source changes present" >&2; exit 2
fi
export PYTHONPATH="$ROOT/src:$ROOT"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
BASE="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
PACKET8="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02"
PACKET16="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02"
TARGET="$BASE/R6_G2G3_SOURCE_COUPLED_TARGET_41_NEW01.log"
FULL="$BASE/R6_G2G3_SOURCE_COUPLED_SELECTED_451_NEW01.log"
OUTPUT="$BASE/R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01"
for item in "$TARGET" "$FULL" "$OUTPUT"; do
  if [ -e "$item" ]; then
    echo "FAIL: must preserve existing immutable evidence: $item" >&2; exit 3
  fi
done
for item in "$PACKET8" "$PACKET16"; do
  if [ ! -d "$item" ]; then
    echo "FAIL: original validated NEW02 packet missing: $item" >&2; exit 3
  fi
done
mkdir -p "$BASE"
echo "G2G3_SOURCE_COUPLED_CODE_HEAD=$(git rev-parse HEAD)"
echo "G2G3_SOURCE_COUPLED_GOVERNANCE=NONCANONICAL_UNSELECTED_NO_PHYSICAL_SOLVE"
echo "--- 41 NEW targeted junction / source-to-coupled authoring tests ---"
python -m pytest -q -ra --tb=short \
  tests/test_r6_g2_g3_junction_source_guard.py \
  tests/test_r6_g2_g3_source_to_coupled_handoff.py \
  tests/test_r6_g2_g3_source_runner_junction_integration.py \
  2>&1 | tee "$TARGET"
grep -Eq '(^|[[:space:]])41 passed in ' "$TARGET" || {
  echo "FAIL: expected exactly 41 new tests" >&2; exit 4;
}
echo "--- 451 selected R6 regression cases, including 41 NEW tests ---"
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
  tests/test_r6_g2_g3_junction_source_guard.py \
  tests/test_r6_g2_g3_source_to_coupled_handoff.py \
  tests/test_r6_g2_g3_source_runner_junction_integration.py \
  2>&1 | tee "$FULL"
grep -Eq '(^|[[:space:]])451 passed in ' "$FULL" || {
  echo "FAIL: expected exactly 451 selected tests" >&2; exit 4;
}
echo "--- Read original already FAIR-certified NEW02 source packet pair and emit scenario templates ---"
python -m experiments.plate58_deforming_explore_v1.g2_g3_source_to_coupled_handoff \
  --repo-root . --packet-8 "$PACKET8" --packet-16 "$PACKET16" \
  --output "$OUTPUT"
python - "$OUTPUT" <<'PY_AUDIT'
import hashlib, json, sys
from pathlib import Path
p=Path(sys.argv[1]); m=json.loads((p/'MANIFEST.json').read_text())
assert m['no_physical_solver_run'] is True
assert m['physical_T1'] is None
assert m['HistoryStore_modified'] is False
assert m['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False
for name, sha in m['files'].items():
    assert hashlib.sha256((p/name).read_bytes()).hexdigest()==sha
scenes={n:json.loads((p/f'SCENARIO_{n}X{n}_UNSELECTED.json').read_text())
        for n in (8,16)}
audit=json.loads((p/'AUDIT.json').read_text())
for n,num,ext,edge in ((8,81,120,32),(16,289,504,64)):
    s=scenes[n]
    assert s['authoring_template_unselected'] is True
    assert len(s['candidate_material_by_parent_node'])==num
    assert len(s['velocity_en_by_parent_node'])==num
    assert len(s['basal_tractions_by_triangle'])==ext
    assert len(s['line_tractions_by_edge'])==edge
    assert all(v is None for k in (
        'candidate_material_by_parent_node','velocity_en_by_parent_node',
        'basal_tractions_by_triangle','line_tractions_by_edge')
        for v in s[k].values())
    assert s['external_gpe'] is None
    assert s['core_basal_tractions_by_triangle'] is None
    assert s['physical_T1'] is None
    assert s['mechanical_solve_authorized'] is False
    assert s['D_024']=='ACTIVE'
assert scenes[8]['source_actual_3plus_plate_junctions']==[]
assert scenes[16]['source_actual_3plus_plate_junctions']==[
    {'parent_node_id':34587,'incident_plates':[5,8,11]}]
assert scenes[8]['source_parent_34587_in_footprint'] is True
assert audit['material_assignments']==audit['qualified_traction_inputs']==0
assert audit['mechanical_solver_runs']==0
assert audit['physical_T1'] is None
assert len(audit['unresolved_physical_groups'])==8
assert audit['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False
print('FAIR_G2G3_SOURCE_TO_COUPLED_SOURCE_PINNED_HANDOFF=PASS')
print('FAIR_G2G3_SOURCE_TO_COUPLED_ORIGINAL_JUNCTION=PASS')
print('FAIR_G2G3_SOURCE_TO_COUPLED_PHYSICAL_INPUTS=UNKNOWN')
print('FAIR_G2G3_SOURCE_TO_COUPLED_PHYSICAL_T1=NULL')
PY_AUDIT
echo "FAIR_G2G3_SOURCE_TO_COUPLED_TARGET_41=PASS"
echo "FAIR_G2G3_SOURCE_TO_COUPLED_SELECTED_451=PASS"
echo "FAIR_G2G3_SOURCE_TO_COUPLED_SOURCE_HANDOFF=PASS"

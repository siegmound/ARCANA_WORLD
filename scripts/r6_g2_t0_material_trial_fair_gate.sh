#!/usr/bin/env bash
# ARCANA R6 original T0 source-to-G2 authorial material/fluid LAB TRIAL only.
# NO rock identity or fault physics selected; zero physical T1/HistoryStore.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
[ "$PWD" = "$ROOT" ] || { echo 'FAIL: run from repository root' >&2; exit 2; }
case "$(command -v python)" in */arcana-r6-linux/bin/python) ;; *) echo 'FAIL: activate FAIR arcana-r6-linux' >&2; exit 2;; esac
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo 'FAIL: tracked files are dirty' >&2; exit 2; }
export PYTHONPATH="$ROOT/src:$ROOT"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
BASE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6
PACKET8="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02"
PACKET16="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02"
HANDOFF="$BASE/R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01"
PT="$BASE/R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
COLD="$BASE/R6_G2G3_T0_COLD_CRUST_REGIME_NEW01"
TARGET="$BASE/R6_G2_MATERIAL_TRIAL_TARGET_67_NEW01.log"
FULL="$BASE/R6_G2_MATERIAL_TRIAL_SELECTED_605_NEW01.log"
OUTPUT="$BASE/R6_G2_T0_MATERIAL_FLUID_TRIAL_NEW01"
for item in "$TARGET" "$FULL" "$OUTPUT"; do
  [ ! -e "$item" ] || { echo "FAIL: immutable evidence already exists: $item" >&2; exit 3; }
done
for item in "$PACKET8" "$PACKET16" "$HANDOFF" "$PT" "$COLD"; do
  [ -d "$item" ] || { echo "FAIL: missing previously FAIR-certified input directory $item" >&2; exit 3; }
done
mkdir -p "$BASE"
echo "G2_T0_MATERIAL_TRIAL_CODE_HEAD=$(git rev-parse HEAD)"
echo 'G2_T0_MATERIAL_TRIAL_AUTHORITY=EXPLICIT_NONCANONICAL_AUTHORIAL_ENGINEERING_TRIAL_NO_SOURCE_ROCK'
echo '--- 67 NEW original-source G2 material/fluid and constitutive-law trial tests ---'
python -m pytest -q -ra --tb=short tests/test_r6_g2_t0_material_trial.py 2>&1 | tee "$TARGET"
grep -Eq '(^|[[:space:]])67 passed in ' "$TARGET" || { echo 'FAIL: 67 targeted tests not completed' >&2; exit 4; }
echo '--- 605 selected R6 cases, including 67 new tests (not additive) ---'
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
  tests/test_r6_g2_g3_t0_lithostatic_pt_reference.py \
  tests/test_r6_g2_g3_t0_cold_crust_regime.py \
  tests/test_r6_g2_t0_material_trial.py \
  2>&1 | tee "$FULL"
grep -Eq '(^|[[:space:]])605 passed in ' "$FULL" || { echo 'FAIL: 605 selected R6 cases not completed' >&2; exit 4; }
echo '--- Re-read original FAIR 8x8/16x16, P-T, cold T context; emit UNSELECTED G2 material trial ---'
python -m experiments.plate58_deforming_explore_v1.g2_t0_material_trial \
  --repo-root . --packet-8 "$PACKET8" --packet-16 "$PACKET16" \
  --handoff "$HANDOFF" --pt-reference "$PT" --cold-context "$COLD" \
  --output "$OUTPUT"
python - "$OUTPUT" <<'PY_AUDIT'
import json,hashlib,sys
from pathlib import Path
p=Path(sys.argv[1]);m=json.loads((p/'MANIFEST.json').read_text())
assert m['schema']=='ARCANA_R6_G2_T0_MATERIAL_TRIAL_SOURCE_MANIFEST_V1'
assert m['physical_T1'] is None and m['no_solver_run'] is True
assert m['D_024']=='ACTIVE' and m['HistoryStore_modified'] is False
assert m['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False
assert set(m['files'])=={'MATERIAL_8X8_UNSELECTED.json','MATERIAL_16X16_UNSELECTED.json','AUDIT.json'}
for filename,digest in m['files'].items():
    assert hashlib.sha256((p/filename).read_bytes()).hexdigest()==digest
for n,count in ((8,81),(16,289)):
    a=json.loads((p/f'MATERIAL_{n}X{n}_UNSELECTED.json').read_text())
    ids=a['source_parent_ids'];assign=a['material_assignment_by_original_parent']
    assert len(ids)==len(set(ids))==count
    assert set(assign)==set(map(str,ids))
    assert all(v is None for v in assign.values())
    assert a['shared_parent_nodes_not_side_resolved_rock_materials'] is True
    assert a['hypothetical_material_classes']==[]
    assert a['hypothetical_fluid_state_classes']==[]
    assert a['hypothetical_lab_law_registry']==[]
    assert a['physical_G2_material_assignments']==0
    assert a['mechanical_solve_authorized'] is False and a['physical_T1'] is None
    assert a['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False
    assert len(a['source_cold_report_sha256'])==len(a['source_PT_report_sha256'])==64
    assert a['source_actual_local_triple_plate_junctions']==(
        [] if n==8 else [{'parent_node_id':34587,'incident_plates':[5,8,11]}])
    for row in a['nodewise_conditional_PT_reference'].values():
        assert row['actual_rock_phase'] is None
        assert row['actual_pore_pressure_pa'] is None
        assert row['source_moho_conditional_delta_overburden_pa']>0
    print(f'FAIR_G2_T0_MATERIAL_UNSELECTED_SOURCE_{n}X{n}=PASS')
a=json.loads((p/'AUDIT.json').read_text())
assert a['source_8x8_material_assignments']==a['source_16x16_material_assignments']==0
assert a['source_pore_pressure_assignments']==0
assert a['qualified_cold_T_P_rate_constitutive_laws']==0
assert a['physical_mineral_phases_selected']==0
assert a['physical_T1'] is None and a['mechanical_solve_authorized'] is False
assert a['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False
print('FAIR_G2_T0_MATERIAL_SOURCE_CHAIN_AND_COLD_PT_REPLAY=PASS')
print('FAIR_G2_T0_MATERIAL_TARGET_67=PASS')
print('FAIR_G2_T0_MATERIAL_SELECTED_605=PASS')
print('FAIR_G2_T0_MATERIAL_NO_ROCK_FLUID_FAULT_SOLVE_OR_T1=PASS')
PY_AUDIT

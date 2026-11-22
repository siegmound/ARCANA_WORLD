#!/usr/bin/env bash
# ARCANA R6: original T0 cold crust regime CONTEXT only, with no real rheology assigned.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
[ "$PWD" = "$ROOT" ] || { echo 'FAIL: run from repository root' >&2; exit 2; }
case "$(command -v python)" in */arcana-r6-linux/bin/python) ;; *) echo 'FAIL: activate FAIR arcana-r6-linux' >&2; exit 2;; esac
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo 'FAIL: tracked source is dirty' >&2; exit 2; }
export PYTHONPATH="$ROOT/src:$ROOT"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
BASE="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
P8="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02"
P16="$BASE/R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02"
HANDOFF="$BASE/R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01"
PT="$BASE/R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
TARGET="$BASE/R6_G2G3_COLD_CRUST_TARGET_51_NEW01.log"
FULL="$BASE/R6_G2G3_COLD_CRUST_SELECTED_538_NEW01.log"
OUT="$BASE/R6_G2G3_T0_COLD_CRUST_REGIME_NEW01"
for path in "$TARGET" "$FULL" "$OUT"; do
  [ ! -e "$path" ] || { echo "FAIL: do not overwrite evidence $path" >&2; exit 3; }
done
for path in "$P8" "$P16" "$HANDOFF" "$PT"; do
  [ -d "$path" ] || { echo "FAIL: missing original FAIR evidence $path" >&2; exit 3; }
done
mkdir -p "$BASE"
echo "COLD_CRUST_CODE_HEAD=$(git rev-parse HEAD)"
echo 'COLD_CRUST_AUTHORITY=EARTH_CONTEXTUAL_THERMAL_WINDOW__NOT_LAB_CONSTITUTIVE_VALIDITY'
echo '--- 51 NEW targeted cold-crust source-applicability tests ---'
python -m pytest -q -ra --tb=short tests/test_r6_g2_g3_t0_cold_crust_regime.py 2>&1 | tee "$TARGET"
grep -Eq '(^|[[:space:]])51 passed in ' "$TARGET" || { echo 'FAIL: expected 51 tests' >&2; exit 4; }
echo '--- 538 selected R6 regression cases including 51 new tests ---'
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
  2>&1 | tee "$FULL"
grep -Eq '(^|[[:space:]])538 passed in ' "$FULL" || { echo 'FAIL: expected 538 selected tests' >&2; exit 4; }
echo '--- Reopen authentic FAIR source/overburden and map EARTH context only ---'
python -m experiments.plate58_deforming_explore_v1.g2_g3_t0_cold_crust_regime \
    --repo-root . --packet-8 "$P8" --packet-16 "$P16" \
    --handoff "$HANDOFF" --pt-reference "$PT" --output "$OUT"
python - "$OUT" "$PT" <<'PY_AUDIT'
import hashlib,json,sys
from pathlib import Path
out,pt=map(Path,sys.argv[1:])
manifest=json.loads((out/'MANIFEST.json').read_text())
assert manifest['schema']=='ARCANA_R6_T0_COLD_CRUST_REGIME_MANIFEST_V1'
assert manifest['no_solver_run'] is True and manifest['physical_T1'] is None
assert manifest['HistoryStore_modified'] is False and manifest['D_024']=='ACTIVE'
assert manifest['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False
assert manifest['source_PT_manifest_sha256']==hashlib.sha256((pt/'MANIFEST.json').read_bytes()).hexdigest()
assert set(manifest['files'])=={'REGION_8X8_COLD_CRUST.json','REGION_16X16_COLD_CRUST.json','AUDIT.json'}
for name,sha in manifest['files'].items():
    assert hashlib.sha256((out/name).read_bytes()).hexdigest()==sha
reports={n:json.loads((out/f'REGION_{n}X{n}_COLD_CRUST.json').read_text()) for n in (8,16)}
audit=json.loads((out/'AUDIT.json').read_text())
for n,count in ((8,81),(16,289)):
    report=reports[n];nodes=report['original_T0_source_nodes']
    assert report['source_node_count']==len(nodes)==count
    assert set(nodes)==set(map(str,report['source_parent_ids']))
    assert report['earth_references']['contextual_BPT_interval_K']==[523.15,623.15]
    assert report['summary']['source_nodes_with_GT95_T_overlap']==0
    assert report['summary']['source_selected_rocks']==0
    assert report['summary']['source_constitutive_laws_selected']==0
    assert report['summary']['source_fault_normal_effective_pressure_assignments']==0
    assert report['mechanical_solve_authorized'] is False and report['physical_T1'] is None
    assert report['HistoryStore_modified'] is False and report['D_024']=='ACTIVE'
    assert report['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False
    for node in nodes.values():
        assert node['model_regime_assignment']=='UNDETERMINED'
        for key in ('source_node_lithology','source_pore_pressure_pa',
                    'source_effective_fault_normal_stress_pa','selected_brittle_law',
                    'selected_ductile_law','computed_real_brittle_ductile_transition_depth_m'):
            assert node[key] is None
        for row in node['earth_quartz_rich_BPT_temperature_only_intervals']:
            left,right=row['depth_interval_m']
            assert 0<=left<right<=node['original_crust_thickness_m']
            assert row['real_effective_fault_normal_stress_pa'] is None
            assert row['rock_phase_identity'] is None
            assert row['physical_brittle_ductile_transition'] is None
    print(f'FAIR_G2G3_T0_{n}X{n}_COLD_CRUST_TEMP_CONTEXT=PASS')
    print(f'FAIR_G2G3_T0_{n}X{n}_EARTH_CONTEXT_WINDOW_NODE_COUNT={report["summary"]["earth_BPT_temperature_window_nodes"]}')
assert audit['material_rock_selected'] is False
assert audit['mechanical_fault_or_traction_assigned'] is False
assert audit['water_pore_pressure_selected'] is False
assert audit['GT95_actual_crust_scope_rejected'] is True
assert audit['physical_T1'] is None and audit['mechanical_solve_authorized'] is False
print('FAIR_G2G3_T0_COLD_CRUST_SOURCE_SHA_RECONSTRUCTION=PASS')
print('FAIR_G2G3_T0_COLD_CRUST_TARGET_51=PASS')
print('FAIR_G2G3_T0_COLD_CRUST_SELECTED_538=PASS')
print('FAIR_G2G3_T0_COLD_CRUST_NO_LAW_SELECTION_OR_T1=PASS')
PY_AUDIT

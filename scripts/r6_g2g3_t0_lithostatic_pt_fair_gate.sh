#!/usr/bin/env bash
# R6 original T0 conditional overburden P/T model reference; not physical G2/G3/FAULT solve.
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
HANDOFF="$BASE/R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01"
TARGET="$BASE/R6_G2G3_PT_REFERENCE_TARGET_36_NEW01.log"
FULL="$BASE/R6_G2G3_PT_REFERENCE_SELECTED_487_NEW01.log"
OUTPUT="$BASE/R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
for item in "$TARGET" "$FULL" "$OUTPUT"; do
  if [ -e "$item" ]; then
    echo "FAIL: must preserve existing immutable evidence: $item" >&2; exit 3
  fi
done
for item in "$PACKET8" "$PACKET16" "$HANDOFF"; do
  if [ ! -d "$item" ]; then
    echo "FAIL: original validated NEW02 packet missing: $item" >&2; exit 3
  fi
done
mkdir -p "$BASE"
echo "G2G3_T0_PT_SOURCE_CODE_HEAD=$(git rev-parse HEAD)"
echo "G2G3_T0_PT_SOURCE_AUTHORITY=CONDITIONAL_SOURCE_MODEL_REFERENCE_NONCANONICAL"
echo "--- 36 NEW targeted original T0 lithostatic P/T physics tests ---"
python -m pytest -q -ra --tb=short \
  tests/test_r6_g2_g3_t0_lithostatic_pt_reference.py \
  2>&1 | tee "$TARGET"
grep -Eq '(^|[[:space:]])36 passed in ' "$TARGET" || {
  echo "FAIL: expected exactly 36 new tests" >&2; exit 4;
}
echo "--- 487 selected R6 regression cases, including 36 NEW tests ---"
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
  2>&1 | tee "$FULL"
grep -Eq '(^|[[:space:]])487 passed in ' "$FULL" || {
  echo "FAIL: expected exactly 487 selected tests" >&2; exit 4;
}
echo "--- SHA-reopen original NEW02 source pair + NEW01 unselected coupled handoff, evaluate conditional overburden P/T ---"
python -m experiments.plate58_deforming_explore_v1.g2_g3_t0_lithostatic_pt_reference \
  --repo-root . --packet-8 "$PACKET8" --packet-16 "$PACKET16" \
  --handoff "$HANDOFF" --output "$OUTPUT"
python - "$OUTPUT" <<'PY_PT_AUDIT'
import hashlib, json, math, sys
from pathlib import Path
folder=Path(sys.argv[1]); manifest=json.loads((folder/'MANIFEST.json').read_text())
assert manifest['no_solver_run'] is True
assert manifest['physical_T1'] is None
assert manifest['HistoryStore_modified'] is False
assert manifest['D_024']=='ACTIVE'
assert manifest['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False
assert set(manifest['files']) == {'REGION_8X8_SOURCE_PT.json','REGION_16X16_SOURCE_PT.json','AUDIT.json'}
for file,digest in manifest['files'].items():
    assert hashlib.sha256((folder/file).read_bytes()).hexdigest()==digest
reports={n:json.loads((folder/f'REGION_{n}X{n}_SOURCE_PT.json').read_text()) for n in (8,16)}
audit=json.loads((folder/'AUDIT.json').read_text())
for n,nn,basal,edges in ((8,81,128,32),(16,289,512,64)):
    r=reports[n]
    assert (r['source_node_count'],r['source_full_basal_facet_count'],r['source_external_cut_edge_count'])==(nn,basal,edges)
    assert len(r['original_T0_source_nodes'])==nn
    assert r['pressure_reference_is_delta_from_model_surface_not_absolute'] is True
    assert r['conditional_overburden_not_mechanical_vertical_traction'] is True
    assert r['hydrostatic_assumption_constant_layer_density_and_g'] is True
    assert r['physical_T1'] is None and r['mechanical_solve_authorized'] is False
    assert len(r['remaining_physical_groups'])==8
    assert r['summary']['GT95_arcana_rock_assignments']==0
    assert r['summary']['qualified_basal_traction_facets']==0
    for row in r['original_T0_source_nodes'].values():
        assert row['conditional_base_delta_overburden_pa']>=row['conditional_moho_delta_overburden_pa']>0
        assert len(row['source_depth_pt_samples'])==10
        assert row['absolute_surface_pressure_pa'] is None
        assert row['fault_normal_pressure_pa'] is None
        assert row['effective_pressure_pa'] is None
        assert row['pore_pressure_pa'] is None
        assert row['constitutive_law_assigned'] is False
    print(f'FAIR_G2G3_ORIGINAL_T0_{n}X{n}_CONDITIONAL_PT=PASS')
    print(f'FAIR_G2G3_ORIGINAL_T0_{n}X{n}_GT95_T_ONLY_COVERAGE='+str(r['summary']['terrestrial_GT95_temperature_only_crust_nodes']))
assert audit['physical_G2_material_law_or_rock_selected'] is False
assert audit['effective_normal_pressure_or_surface_load_selected'] is False
assert audit['G3_external_basal_GPE_loads_derived'] is False
assert audit['mechanical_solve_authorized'] is False
assert audit['region_extent_comparison_is_not_grid_convergence'] is True
assert audit['gravity_and_GT95_source']['gravity_m_s2']==9.82
print('FAIR_G2G3_SOURCE_PRE_GRAVITY_LAB_SHA_PINNED=PASS')
print('FAIR_G2G3_T0_LITHOSTATIC_PT_REFERENCE_TARGET_36=PASS')
print('FAIR_G2G3_T0_LITHOSTATIC_PT_REFERENCE_SELECTED_487=PASS')
print('FAIR_G2G3_CONDITIONAL_PT_NO_PHYSICAL_STRESS_OR_T1=PASS')
PY_PT_AUDIT

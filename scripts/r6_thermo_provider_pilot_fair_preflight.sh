#!/usr/bin/env bash
# Source-read-only / official-reference-only phase-provider qualification.
# NEVER claims external engines ran: numerical engine execution is a separate gate.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
[[ "$PWD" = "$ROOT" ]] || { echo 'FAIL: run from repository root' >&2; exit 2; }
case "$(command -v python)" in */arcana-r6-linux/bin/python) ;; *) echo 'FAIL: use FAIR arcana-r6-linux' >&2; exit 2;; esac
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || { echo 'FAIL: dirty tracked source' >&2; exit 2; }
python - <<'PY'
import sys
assert sys.version_info >= (3,11), 'Python >=3.11 required for stdlib tomllib'
PY
export PYTHONPATH="$ROOT/src:$ROOT" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
BASE="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
TARGET="$BASE/R6_THERMO_PROVIDER_PILOT_TARGET_35_NEW01.log"
SELECTED="$BASE/R6_THERMO_PROVIDER_PILOT_SELECTED_640_NEW01.log"
OUT="$BASE/R6_THERMO_PROVIDER_PILOT_PREFLIGHT_NEW01"
for p in "$TARGET" "$SELECTED" "$OUT"; do
  [[ ! -e "$p" ]] || { echo "FAIL: immutable evidence exists $p" >&2; exit 3; }
done
mkdir -p "$BASE"
echo "THERMO_PILOT_CODE_HEAD=$(git rev-parse HEAD)"
echo 'THERMO_PILOT_AUTHORITY=OFFICIAL_EARTH_FIXTURE_ONLY__NO_EXTERNAL_ENGINE_RUN_YET'
python -m pytest -q -ra --tb=short tests/test_r6_thermo_provider_pilot.py 2>&1 | tee "$TARGET"
grep -Eq '(^|[[:space:]])35 passed in ' "$TARGET" || { echo 'FAIL: expected 35 new tests' >&2; exit 4; }
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
  tests/test_r6_thermo_provider_pilot.py 2>&1 | tee "$SELECTED"
grep -Eq '(^|[[:space:]])640 passed in ' "$SELECTED" || { echo 'FAIL: expected 640 selected incl 35' >&2; exit 5; }
mkdir "$OUT"
python -m experiments.r6_thermo_provider_pilot_v1.pilot \
  --preflight-out "$OUT/PREFLIGHT.json"
python - "$ROOT" "$OUT" <<'PY'
import hashlib,json,sys
from pathlib import Path
root,out=map(Path,sys.argv[1:]);files={}
for name in ('PREFLIGHT.json',):
    raw=(out/name).read_bytes();files[name]=hashlib.sha256(raw).hexdigest()
report=json.loads((out/'PREFLIGHT.json').read_text())
assert report['status']=='SOURCE_REGISTER_PINNED__EXTERNAL_RUNTIME_NOT_YET_QUALIFIED'
assert report['official_engine_executions']==0
assert report['physical_T1'] is None and report['D_024']=='ACTIVE'
assert report['scientific_cross_provider_comparison_authorized'] is False
manifest={'schema':'ARCANA_R6_THERMO_PROVIDER_PREFLIGHT_MANIFEST_V1',
  'decision':'REGISTER_AND_CONTRACT_FAIR_SOFTWARE_CHECKS_ONLY',
  'code_head_git_sha':__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
  'files':files,'tested_cases':35,'selected_regression_including_target':640,
  'external_thermodynamic_executions':0,'cross_provider_comparison_authorized':False,
  'physical_T1':None,'mechanical_solve_authorized':False,
  'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,'D_024':'ACTIVE'}
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert hashlib.sha256((out/'PREFLIGHT.json').read_bytes()).hexdigest()==files['PREFLIGHT.json']
print('FAIR_THERMO_PROVIDER_PILOT_TARGET_35=PASS')
print('FAIR_THERMO_PROVIDER_PILOT_SELECTED_640=PASS')
print('FAIR_THERMO_PROVIDER_REGISTRY_PINNED=PASS')
print('FAIR_THERMO_EXTERNAL_MAGEMIN_EXECUTIONS=NOT_RUN')
print('FAIR_THERMO_EXTERNAL_PERPLEX_EXECUTIONS=NOT_RUN')
print('FAIR_THERMO_CROSS_PROVIDER_SCIENCE=NOT_AUTHORIZED')
print('FAIR_THERMO_PHYSICAL_T1=NULL')
PY

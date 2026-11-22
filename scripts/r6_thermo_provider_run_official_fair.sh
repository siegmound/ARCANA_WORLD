#!/usr/bin/env bash
# Actually invoke MAGEMin_C.jl and Perple_X official fixtures after local install.
# Requires exact pinned upstream packages/artifacts; never substitutes Earth geology.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
[[ "$PWD" = "$ROOT" ]] || { echo 'FAIL: invoke from repo root' >&2; exit 2; }
case "$(command -v python)" in */arcana-r6-linux/bin/python) ;; *) echo 'FAIL: arcana-r6-linux required' >&2; exit 2;; esac
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || { echo 'FAIL: dirty source' >&2; exit 2; }
for v in JULIA_BIN JULIA_PROJECT PERPLEX_SOURCE PERPLEX_MEEMUM PERPLEX_RELEASE_ARCHIVE; do
  [[ -n "${!v:-}" ]] || { echo "FAIL: set $v to installed pinned source or binary" >&2; exit 2; }
done
[[ -f "$JULIA_PROJECT/Manifest.toml" ]] || { echo 'FAIL: pinned Julia project Manifest missing' >&2; exit 2; }
BASE="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
PRE="$BASE/R6_THERMO_PROVIDER_PILOT_PREFLIGHT_NEW01"
OUT="$BASE/R6_THERMO_EXTERNAL_OFFICIAL_NEW01"
[[ -f "$PRE/MANIFEST.json" && ! -e "$OUT" ]] || { echo 'FAIL: preflight missing or external output exists' >&2; exit 3; }
export PYTHONPATH="$ROOT/src:$ROOT" PYTHONDONTWRITEBYTECODE=1
python - "$PRE/MANIFEST.json" <<'PY'
import json,sys,subprocess
x=json.load(open(sys.argv[1]))
assert x['schema']=='ARCANA_R6_THERMO_PROVIDER_PREFLIGHT_MANIFEST_V1'
assert x['code_head_git_sha']==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert x['external_thermodynamic_executions']==0
PY
mkdir "$OUT"
# Strongest local package-reproducibility record: operator-selected Manifest.
cp "$JULIA_PROJECT/Manifest.toml" "$OUT/MAGEMIN_JULIA_Manifest.toml"
"$JULIA_BIN" --project="$JULIA_PROJECT" \
  experiments/r6_thermo_provider_pilot_v1/run_magemin_official.jl \
  "$OUT/MAGEMIN_OFFICIAL.toml" 2>&1 | tee "$OUT/MAGEMIN_STDOUT.log"
python - "$OUT/MAGEMIN_OFFICIAL.toml" <<'PY'
import sys
from experiments.r6_thermo_provider_pilot_v1.pilot import load_magemin_toml
r=load_magemin_toml(sys.argv[1]);print('FAIR_MAGEMIN_TWO_UPSTREAM_EXAMPLES=PASS')
PY
python -m experiments.r6_thermo_provider_pilot_v1.run_perplex_official \
  --repo-root "$ROOT" --perplex-source "$PERPLEX_SOURCE" \
  --meemum "$PERPLEX_MEEMUM" --release-archive "$PERPLEX_RELEASE_ARCHIVE" \
  --output "$OUT/PERPLEX_BL691_MEEMUM"
python - "$OUT" "$ROOT" <<'PY'
import hashlib,json,sys,subprocess
from pathlib import Path
out,root=map(Path,sys.argv[1:])
manifest={'schema':'ARCANA_R6_THERMO_PROVIDER_OFFICIAL_EXECUTION_MANIFEST_V1',
  'source_R6_git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
  'files':{}, 'provider_fixtures':'TWO_MAGEMIN_ONE_PERPLEX',
  'cross_provider_scientific_comparison_authorized':False,
  'natural_ARCANA_material_assignments':0,
  'no_physical_solver':True,'D_024':'ACTIVE','physical_T1':None,
  'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}
for p in sorted(out.rglob('*')):
    if p.is_file() and p.name!='MANIFEST.json':
        manifest['files'][str(p.relative_to(out))]=hashlib.sha256(p.read_bytes()).hexdigest()
assert len(manifest['files'])>=8
(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
assert all(hashlib.sha256((out/k).read_bytes()).hexdigest()==v for k,v in manifest['files'].items())
print('FAIR_MAGEMIN_OFFICIAL_FIXTURES=PASS')
print('FAIR_PERPLEX_OFFICIAL_FAST_MEEMUM=PASS')
print('FAIR_PHASE_CROSS_SOLVER_COMPARISON=NOT_YET_QUALIFIED')
print('FAIR_T0_NATURAL_ROCK_SELECTION=ZERO')
print('FAIR_PHYSICAL_T1=NULL')
PY

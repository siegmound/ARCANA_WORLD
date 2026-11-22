#!/usr/bin/env bash
# NEW02 software-only preflight for corrected MAGEMin S1; no actual engines.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
[[ "$PWD" = "$ROOT" ]] || { echo 'FAIL: run from repo root' >&2; exit 2; }
case "$(command -v python)" in
 */arcana-r6-linux/bin/python) ;;
 *) echo 'FAIL: use arcana-r6-linux Python' >&2; exit 2;;
esac
[[ -z "$(git status --porcelain --untracked-files=no)" ]] ||
 { echo 'FAIL: tracked source dirty' >&2; exit 2; }
export PYTHONPATH="$ROOT/src:$ROOT" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
BASE="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
ORIGINAL="$BASE/R6_THERMO_PROVIDER_PILOT_PREFLIGHT_NEW01/MANIFEST.json"
OUT="$BASE/R6_THERMO_S1_SCOPEFIX_PREFLIGHT_NEW02"
[[ -f "$ORIGINAL" && ! -e "$OUT" ]] ||
 { echo 'FAIL: original preflight missing or write-once NEW02 exists' >&2; exit 3; }
python - "$ORIGINAL" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
assert x['schema']=='ARCANA_R6_THERMO_PROVIDER_PREFLIGHT_MANIFEST_V1'
assert x['code_head_git_sha']=='393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2'
assert x['tested_cases']==35 and x['selected_regression_including_target']==640
assert x['external_thermodynamic_executions']==0
assert x['physical_T1'] is None and x['D_024']=='ACTIVE'
PY
mkdir "$OUT"
python -m pytest -q -ra --tb=short \
 tests/test_r6_thermo_provider_pilot.py tests/test_r6_thermo_s1_v2.py \
 2>&1 | tee "$OUT/PYTEST.log"
python - "$ROOT" "$ORIGINAL" "$OUT" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
root,original,out=map(Path,sys.argv[1:])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[
 "experiments/r6_thermo_provider_pilot_v1/run_magemin_official.jl",
 "experiments/r6_thermo_provider_pilot_v1/validate_magemin_s1_v2.py",
 "experiments/r6_thermo_provider_pilot_v1/run_perplex_official.py",
 "experiments/r6_thermo_provider_pilot_v1/pilot.py",
 "experiments/r6_thermo_provider_pilot_v1/pilot.json",
 "scripts/r6_thermo_s1_corrected_preflight_fair.sh",
 "scripts/r6_thermo_s1_corrected_run_official_fair.sh",
 "tests/test_r6_thermo_s1_v2.py"]
manifest={
 "schema":"ARCANA_R6_THERMO_S1_SCOPEFIX_PREFLIGHT_V2",
 "decision":"CORRECTED_RUNNER_SOFTWARE_CHECKS_ONLY",
 "code_head_git_sha":subprocess.check_output(
   ["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
 "original_preflight_sha256":sha(original),
 "original_preflight_git_sha":"393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2",
 "files_sha256":{p:sha(root/p) for p in paths},
 "pytest_log_sha256":sha(out/"PYTEST.log"),
 "external_engine_executions":0,
 "cross_provider_scientific_comparison_authorized":False,
 "D_024":"ACTIVE", "physical_T1":None,
 "mechanical_solve_authorized":False,
 "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False}
with (out/"MANIFEST.json").open("x") as f:
 json.dump(manifest,f,indent=2,allow_nan=False); f.write("\n")
print("FAIR_THERMO_S1_CORRECTED_SOFTWARE_PREFLIGHT_PASS")
print("FAIR_THERMO_S1_EXTERNAL_EXECUTIONS_NOT_CLAIMED")
print("FAIR_THERMO_S1_SOURCE_SHA="+manifest["code_head_git_sha"])
print("FAIR_THERMO_S1_PREFLIGHT_MANIFEST_SHA256="+sha(out/"MANIFEST.json"))
PY

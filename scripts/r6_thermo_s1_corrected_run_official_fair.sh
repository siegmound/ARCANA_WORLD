#!/usr/bin/env bash
# Real S1 Earth-only official MAGEMin and Perple_X; versioned write-once NEW02.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
[[ "$PWD" = "$ROOT" ]] || { echo 'FAIL: call from repository root' >&2; exit 2; }
case "$(command -v python)" in
 */arcana-r6-linux/bin/python) ;;
 *) echo 'FAIL: arcana-r6-linux Python required' >&2; exit 2;;
esac
[[ -z "$(git status --porcelain --untracked-files=no)" ]] ||
 { echo 'FAIL: tracked source dirty' >&2; exit 2; }
for v in JULIA_BIN JULIA_PROJECT JULIA_DEPOT_PATH PERPLEX_SOURCE PERPLEX_MEEMUM PERPLEX_RELEASE_ARCHIVE; do
 [[ -n "$(printenv "$v")" ]] || { echo "FAIL: missing $v" >&2; exit 2; }
done
[[ -x "$JULIA_BIN" && -f "$JULIA_PROJECT/Manifest.toml" &&
   -f "$JULIA_PROJECT/Project.toml" &&
   -x "$PERPLEX_MEEMUM" && -f "$PERPLEX_RELEASE_ARCHIVE" ]] ||
 { echo 'FAIL: missing runtime binaries or manifests' >&2; exit 2; }
"$JULIA_BIN" --version | grep -Fx 'julia version 1.10.4' ||
 { echo 'FAIL: wrong Julia version' >&2; exit 2; }
export PYTHONPATH="$ROOT/src:$ROOT" PYTHONDONTWRITEBYTECODE=1
export JULIA_NUM_THREADS=1 JULIA_NUM_PRECOMPILE_TASKS=1 JULIA_PKG_PRECOMPILE_AUTO=0
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
BASE="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6"
PRE="$BASE/R6_THERMO_S1_SCOPEFIX_PREFLIGHT_NEW02"
OUT="$BASE/R6_THERMO_EXTERNAL_OFFICIAL_NEW02"
[[ -f "$PRE/MANIFEST.json" && ! -e "$OUT" ]] ||
 { echo 'FAIL: corrected preflight missing or NEW02 already exists' >&2; exit 3; }
# Do not claim original software-only evidence covers a newer source SHA.
python - "$ROOT" "$PRE" "$JULIA_PROJECT/Manifest.toml" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
root,pre,manifest=map(Path,sys.argv[1:])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
x=json.loads((pre/"MANIFEST.json").read_text())
assert x["schema"]=="ARCANA_R6_THERMO_S1_SCOPEFIX_PREFLIGHT_V2"
assert x["decision"]=="CORRECTED_RUNNER_SOFTWARE_CHECKS_ONLY"
assert x["external_engine_executions"]==0
head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
assert head==x["code_head_git_sha"]
assert sha(pre/"PYTEST.log")==x["pytest_log_sha256"]
for rel,digest in x["files_sha256"].items():
 assert sha(root/rel)==digest,"SOURCE_DRIFT: "+rel
original=pre.parent/"R6_THERMO_PROVIDER_PILOT_PREFLIGHT_NEW01/MANIFEST.json"
assert sha(original)==x["original_preflight_sha256"]
text=manifest.read_text()
assert "f4fd5ce3670b73693d046e65585e2b79d45c8e3a" in text, \
 "MAGEMIN_SOURCE_REVISION_MISSING_IN_MANIFEST"
assert "2.1.0+0" in text,"MAGEMIN_JLL_PIN_MISSING_IN_MANIFEST"
assert x["D_024"]=="ACTIVE" and x["physical_T1"] is None
print("S1_CORRECTED_SOURCE_AND_MANIFEST_PINS_PASS")
PY
mkdir "$OUT"
cp "$JULIA_PROJECT/Project.toml" "$OUT/MAGEMIN_Project.toml"
cp "$JULIA_PROJECT/Manifest.toml" "$OUT/MAGEMIN_Manifest.toml"
"$JULIA_BIN" --startup-file=no --project="$JULIA_PROJECT" \
 experiments/r6_thermo_provider_pilot_v1/run_magemin_official.jl \
 "$OUT/MAGEMIN_OFFICIAL.toml" 2>&1 | tee "$OUT/MAGEMIN_STDOUT.log"
python -m experiments.r6_thermo_provider_pilot_v1.validate_magemin_s1_v2 \
 --report "$OUT/MAGEMIN_OFFICIAL.toml" 2>&1 | tee "$OUT/MAGEMIN_VALIDATION.log"
python -m experiments.r6_thermo_provider_pilot_v1.run_perplex_official \
 --repo-root "$ROOT" --perplex-source "$PERPLEX_SOURCE" \
 --meemum "$PERPLEX_MEEMUM" --release-archive "$PERPLEX_RELEASE_ARCHIVE" \
 --output "$OUT/PERPLEX_BL691_MEEMUM" 2>&1 | tee "$OUT/PERPLEX_VALIDATION.log"
python - "$ROOT" "$PRE" "$OUT" "$JULIA_BIN" "$JULIA_PROJECT" "$PERPLEX_MEEMUM" "$PERPLEX_RELEASE_ARCHIVE" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
root,pre,out,julia,project,meemum,archive=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
per=json.loads((out/"PERPLEX_BL691_MEEMUM/REPORT.json").read_text())
assert per["status"]=="PERPLEX_ORIGINAL_MEEMUM_REFERENCE_NUMERICAL_PASS"
assert per["physical_T1"] is None and per["D_024"]=="ACTIVE"
manifest={
 "schema":"ARCANA_R6_THERMO_S1_CORRECTED_REAL_EXECUTION_V2",
 "decision":"BOTH_REAL_EARTH_S1_FIXTURES_NUMERIC_PASS__CROSS_PROVIDER_NOT_QUALIFIED",
 "source_R6_git_head":subprocess.check_output(
   ["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
 "preflight_manifest_sha256":sha(pre/"MANIFEST.json"),
 "julia_bin":str(julia),"julia_project":str(project),
 "julia_project_sha256":sha(project/"Project.toml"),
 "julia_manifest_sha256":sha(project/"Manifest.toml"),
 "perplex_meemum_sha256":sha(meemum),
 "perplex_release_archive_sha256":sha(archive),
 "magemin_readme_quantitative_reconciliation":"PENDING",
 "cross_provider_scientific_comparison_authorized":False,
 "natural_ARCANA_material_assignments":0,
 "D_024":"ACTIVE","physical_T1":None,
 "mechanical_solve_authorized":False,
 "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False,
 "files_sha256":{}}
for path in sorted(out.rglob("*")):
 if path.is_file() and path.name!="MANIFEST.json":
  manifest["files_sha256"][str(path.relative_to(out))]=sha(path)
assert len(manifest["files_sha256"])>=10
with (out/"MANIFEST.json").open("x") as f:
 json.dump(manifest,f,indent=2,allow_nan=False);f.write("\n")
for rel,digest in manifest["files_sha256"].items():
 assert sha(out/rel)==digest
print("FAIR_MAGEMIN_S1_CORRECTED_NUMERICAL_PASS")
print("FAIR_PERPLEX_S1_OFFICIAL_REFERENCE_PASS")
print("FAIR_CROSS_PROVIDER_SCIENCE=NOT_QUALIFIED")
print("FAIR_PHYSICAL_T1=NULL")
print("FAIR_THERMO_REAL_S1_MANIFEST_SHA256="+sha(out/"MANIFEST.json"))
PY

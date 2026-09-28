#!/usr/bin/env bash
set -euo pipefail

stage() { printf 'START %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1" >&2; exit 2; }

stage ARCANA_IDENTITY
repo_root="$(git rev-parse --show-toplevel)" || fail "cannot locate ARCANA repository"
cd "$repo_root"
expected_branch="r6/t0-authorial-realization-materialization"
minimum_ancestor="0dfccaa0722f025fee1590d94c78eb30ac54d828"
expected_field_package_sha="31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534"
expected_shellset_parent="09a06ecd061f00b80a52af86e31d609ff5545a8b"
historical_qualified_exe_sha="03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349"
expected_parent_exe_sha="4603c7d2854c2999c1e8e4607b7bbe470e43f300bf2e8ed1650528e49ceb56e9"
patch_path="$repo_root/patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch"
expected_patch_sha="e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2"
[[ "$(git branch --show-current)" == "$expected_branch" ]] || fail "wrong ARCANA branch"
git merge-base --is-ancestor "$minimum_ancestor" HEAD || fail "ARCANA HEAD is not descended from the adapter commit"
field_sha="$(sha256sum R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE_SURFACE_CLOSED.npz | awk '{print $1}')" || fail "cannot hash surface-closed field package"
[[ "$field_sha" == "$expected_field_package_sha" ]] || fail "surface-closed package SHA mismatch"

shellset_root="${ARCANA_SHELLSET_ROOT:-$HOME/HPC-POMDP/tools/ShellSet-v1.1.0}"
[[ -d "$shellset_root/.git" ]] || fail "ShellSet checkout not found: $shellset_root"
[[ "$(git -C "$shellset_root" rev-parse HEAD)" == "$expected_shellset_parent" ]] || fail "ShellSet parent HEAD mismatch"
[[ -z "$(git -C "$shellset_root" status --porcelain --untracked-files=no)" ]] || fail "tracked ShellSet files are not clean"
old_exe_sha="$(sha256sum "$shellset_root/ShellSet.exe" | awk '{print $1}')" || fail "cannot hash qualified ShellSet executable"
[[ "$old_exe_sha" == "$expected_parent_exe_sha" ]] || fail "current FAIR parent executable SHA mismatch"
patch_sha="$(sha256sum "$patch_path" | awk '{print $1}')" || fail "cannot hash source patch"
[[ "$patch_sha" == "$expected_patch_sha" ]] || fail "patch SHA mismatch"

stage NVIDIA_TOOLCHAIN
command -v nvfortran >/dev/null || fail "nvfortran is unavailable"
command -v mpifort >/dev/null || fail "mpifort is unavailable"
nvfortran --version 2>&1 | grep -q '25\.11' || fail "expected NVIDIA HPC SDK 25.11"
mpifort --showme:command 2>&1 | grep -q 'nvfortran' || fail "mpifort is not using nvfortran"

stage PATCH_APPLICATION
git -C "$shellset_root" apply --check "$patch_path" || fail "git apply --check rejected the source patch"
recovery_root="$(mktemp -d "${TMPDIR:-/tmp}/arcana-shellset-recovery.XXXXXX")" || fail "cannot create recovery directory"
parent_exe_backup="$recovery_root/ShellSet.exe.qualified-parent"
cp "$shellset_root/ShellSet.exe" "$parent_exe_backup" || fail "cannot preserve qualified parent executable"
patched_sources=(src/MOD_ShellSet.f90 src/OrbData5.f90 src/MOD_Data.f90 src/ShellSetMain.f90)
patch_started=true
qualification_pass=false
restore_on_failure() {
  local rc=$?
  if [[ "$qualification_pass" != true && "$patch_started" == true ]]; then
    echo "FAIL qualification; restoring patched tracked sources and qualified parent executable" >&2
    git -C "$shellset_root" checkout -- "${patched_sources[@]}" || echo "RECOVERY WARNING: source restore failed" >&2
    cp "$parent_exe_backup" "$shellset_root/ShellSet.exe" || echo "RECOVERY WARNING: executable backup remains at $parent_exe_backup" >&2
    echo "RECOVERY_BACKUP=$recovery_root"
  fi
  return "$rc"
}
trap restore_on_failure EXIT
git -C "$shellset_root" apply "$patch_path" || fail "failed to apply the source patch"
git -C "$shellset_root" diff --check || fail "patched ShellSet diff check failed"

stage NVIDIA_BUILD
build_log="$(mktemp "${TMPDIR:-/tmp}/arcana-shellset-build.XXXXXX.log")" || fail "cannot create build log"
set +e
(cd "$shellset_root" && make -B ShellSet) 2>&1 | tee "$build_log"
build_rc=${PIPESTATUS[0]}
set -e
[[ $build_rc -eq 0 ]] || { echo "FAIL NVIDIA build (exit $build_rc); log: $build_log" >&2; exit "$build_rc"; }
[[ -x "$shellset_root/ShellSet.exe" ]] || fail "built ShellSet.exe is missing"
new_exe_sha="$(sha256sum "$shellset_root/ShellSet.exe" | awk '{print $1}')" || fail "cannot hash rebuilt executable"
if ldd "$shellset_root/ShellSet.exe" | grep -q 'not found'; then fail "ShellSet has unresolved dynamic libraries"; fi

fixture_root="$(mktemp -d "${TMPDIR:-/tmp}/arcana-orbdata-fixture.XXXXXX")" || fail "cannot create fixture root"
objects=(lib/OrbScore2.o lib/MOD_Score.o lib/SHELLS_v5.0.o lib/MOD_Shells.o lib/OrbData5.o lib/MOD_Data.o lib/DMods.o lib/MOD_VarCheck.o lib/MOD_ShellSet.o lib/MOD_SharedVars.o)
for object in "${objects[@]}"; do [[ -f "$shellset_root/$object" ]] || fail "required qualified NVIDIA object missing: $object"; done

stage ASSIGN_FIXTURE
mpifort -Mbackslash -I"$shellset_root/lib" -o "$fixture_root/assign_source_generalization.exe" \
  "$repo_root/tests/fixtures/r6_t0_orbdata_arcana/assign_source_generalization.f90" \
  "${objects[@]/#/$shellset_root/}" -llapack -lblas || fail "cannot build Assign source-generalization fixture"
"$fixture_root/assign_source_generalization.exe" | tee "$fixture_root/assign_fixture.log"
grep -q 'ARCANA_SYNTHETIC_ASSIGN_FIXTURE=PASS' "$fixture_root/assign_fixture.log" || fail "Assign fixture did not report PASS"

stage INPUTSETUP_PAIR_FIXTURE
mpifort -Mbackslash -I"$shellset_root/lib" -o "$fixture_root/inputsetup_pair_driver.exe" \
  "$repo_root/tests/fixtures/r6_t0_orbdata_arcana/open_pair_driver.f90" \
  "${objects[@]/#/$shellset_root/}" -llapack -lblas || fail "cannot build InputSetup/OpenInput fixture"
make_input_case() {
  local root="$1" mode="$2"
mkdir -p "$root/INPUT" "$root/Error"
  cat > "$root/INPUT/InputFiles.in" <<'EOF'
fixture test inputs
parameters.in
grid.grd
skip-a
skip-b
skip-c
skip-d
etopo.grd
age.grd
crust.grd
delta_ts.grd
EOF
  for file in parameters.in grid.grd etopo.grd age.grd crust.grd delta_ts.grd; do : > "$root/INPUT/$file"; done
  if [[ "$mode" == full || "$mode" == only-domain ]]; then : > "$root/INPUT/ARCANA_DOMAIN.grd"; fi
  if [[ "$mode" == full || "$mode" == only-lithosphere ]]; then : > "$root/INPUT/ARCANA_TOTAL_LITHOSPHERE_M.grd"; fi
}
for mode in stock full only-domain only-lithosphere; do make_input_case "$fixture_root/input-$mode" "$mode"; done
(cd "$fixture_root/input-stock" && ../inputsetup_pair_driver.exe . stock) || fail "stock InputSetup/OpenInput fixture failed"
(cd "$fixture_root/input-full" && ../inputsetup_pair_driver.exe . full) || fail "full-pair InputSetup/OpenInput fixture failed"
for partial in only-domain only-lithosphere; do
  (cd "$fixture_root/input-$partial" && ../inputsetup_pair_driver.exe . partial) >"$fixture_root/$partial.log" 2>&1 || fail "partial-pair recording fixture failed: $partial"
  grep -q 'INPUTSETUP_PARTIAL_PAIR_FATAL_RECORDED=PASS' "$fixture_root/$partial.log" || fail "partial-pair fatal marker missing: $partial"
done
echo "PASS INPUTSETUP_PAIR_FIXTURE stock/full/partial-pair cases"

stage MPI_SMOKE
smoke_log="$fixture_root/mpi-smoke.log"
set +e
(cd "$shellset_root" && mpiexec -n 2 ./ShellSet.exe -info) >"$smoke_log" 2>&1
smoke_rc=$?
set -e
[[ $smoke_rc -eq 0 || $smoke_rc -eq 8 ]] || { cat "$smoke_log" >&2; echo "FAIL MPI compile/link smoke" >&2; exit "$smoke_rc"; }
grep -qi 'ShellSet' "$smoke_log" || { cat "$smoke_log" >&2; fail "MPI smoke did not reach ShellSet info"; }

stage LISTEX1_STOCK_REGRESSION
reference_models="$shellset_root/NVHPC_CAPACITY_ListEx1_n10_t5/Models.txt"
[[ -f "$reference_models" ]] || fail "qualified ListEx1 n10_t5 reference Models.txt is missing"
cmp -s "$shellset_root/INPUT/ListInput.in" "$shellset_root/NVHPC_CAPACITY_ListEx1_n10_t5/ListInput.in" || fail "active ListInput.in differs from qualified ListEx1 input"
run_name="NVHPC_ARCANA_PATCH_ListEx1_n10_t5_$(date -u +%Y%m%dT%H%M%SZ)"
[[ ! -e "$shellset_root/$run_name" ]] || fail "regression output directory already exists: $run_name"
export OPENBLAS_NUM_THREADS=5 OMP_NUM_THREADS=5 OMP_DYNAMIC=false OMP_PROC_BIND=true UCX_VFS_ENABLE=n
set +e
(cd "$shellset_root" && mpiexec -n 10 --map-by ppr:3:numa:PE=5 --bind-to core --report-bindings \
  ./ShellSet.exe -Iter 4 -InOpt List -Dir "$run_name" -GM 5,SSR,GV,SD,SA,FSR) 2>&1 | tee "$fixture_root/list_ex1.log"
list_rc=${PIPESTATUS[0]}
set -e
[[ $list_rc -eq 0 ]] || { echo "FAIL exact ListEx1 n10_t5 invocation (exit $list_rc); log: $fixture_root/list_ex1.log" >&2; exit "$list_rc"; }
patched_models="$shellset_root/$run_name/Models.txt"
[[ -f "$patched_models" ]] || fail "patched ListEx1 Models.txt missing"
"${ARCANA_PYTHON:-python3}" - "$reference_models" "$patched_models" <<'PY' || fail "exact ListEx1 Models.txt comparison failed"
from pathlib import Path
import sys

def records(path):
    rows = {}
    for line_number, line in enumerate(Path(path).read_text(errors="strict").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("Program invoked with:"):
            continue
        fields = line.split()
        if len(fields) < 3:
            raise SystemExit(f"Malformed Models row at {path}:{line_number}")
        model_id = fields[0]
        if model_id in rows:
            raise SystemExit(f"Duplicate global model ID {model_id!r} in {path}")
        rows[model_id] = fields[2:]
    return rows

reference, observed = map(records, sys.argv[1:])
expected_ids = set(reference)
observed_ids = set(observed)
if len(expected_ids) != 9 or observed_ids != expected_ids:
    raise SystemExit(f"Models global ID set mismatch: reference={sorted(expected_ids)}, observed={sorted(observed_ids)}")
for model_id in sorted(expected_ids):
    if reference[model_id] != observed[model_id]:
        raise SystemExit(f"ListEx1 exact field mismatch for global model ID {model_id}: {reference[model_id]!r} != {observed[model_id]!r}")
print("STOCK_LISTEX1_MODELS=9")
print("STOCK_LISTEX1_MAX_ABS=0")
print("STOCK_LISTEX1_MAX_REL=0")
print("PASS_STOCK_LISTEX1_BY_MODEL_ID")
PY

echo "SHELLSET_PATCH_QUALIFICATION=PASS_PENDING_MANUAL_COMMIT_AND_EVIDENCE_CAPTURE"
echo "PATCH_SHA256=$expected_patch_sha"
echo "HISTORICAL_QUALIFIED_EXE_SHA256=$historical_qualified_exe_sha"
echo "READJUDICATED_PARENT_EXE_SHA256=$expected_parent_exe_sha"
echo "SHELLSET_NEW_COMMIT=not created by this script"
echo "SHELLSET_EXE_SHA256=$new_exe_sha"
echo "FAIR_FIXTURE_ROOT=$fixture_root"
echo "BUILD_LOG=$build_log"
echo "Manual next commands after review:"
echo "  git -C '$shellset_root' add src/MOD_ShellSet.f90 src/OrbData5.f90 src/MOD_Data.f90 src/ShellSetMain.f90"
echo "  git -C '$shellset_root' commit -m 'arcana: add governed OrbData explicit inputs'"
echo "No push, ARCANA T0 OrbData, or SHELLS T0 mechanics was performed by this script."
qualification_pass=true

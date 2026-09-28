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
expected_old_exe_sha="03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349"
patch_path="$repo_root/patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch"
expected_patch_sha="74fa912d913a82314453ab00addc3e6bcfe1ede87f51866035412e4393f9ad94"
[[ "$(git branch --show-current)" == "$expected_branch" ]] || fail "wrong ARCANA branch"
git merge-base --is-ancestor "$minimum_ancestor" HEAD || fail "ARCANA HEAD is not descended from the adapter commit"
field_sha="$(sha256sum R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE_SURFACE_CLOSED.npz | awk '{print $1}')" || fail "cannot hash surface-closed field package"
[[ "$field_sha" == "$expected_field_package_sha" ]] || fail "surface-closed package SHA mismatch"

shellset_root="${ARCANA_SHELLSET_ROOT:-$HOME/HPC-POMDP/tools/ShellSet-v1.1.0}"
[[ -d "$shellset_root/.git" ]] || fail "ShellSet checkout not found: $shellset_root"
[[ "$(git -C "$shellset_root" rev-parse HEAD)" == "$expected_shellset_parent" ]] || fail "ShellSet parent HEAD mismatch"
[[ -z "$(git -C "$shellset_root" status --porcelain --untracked-files=no)" ]] || fail "tracked ShellSet files are not clean"
old_exe_sha="$(sha256sum "$shellset_root/ShellSet.exe" | awk '{print $1}')" || fail "cannot hash qualified ShellSet executable"
[[ "$old_exe_sha" == "$expected_old_exe_sha" ]] || fail "pre-patch executable SHA mismatch"
patch_sha="$(sha256sum "$patch_path" | awk '{print $1}')" || fail "cannot hash source patch"
[[ "$patch_sha" == "$expected_patch_sha" ]] || fail "patch SHA mismatch"

stage NVIDIA_TOOLCHAIN
command -v nvfortran >/dev/null || fail "nvfortran is unavailable"
command -v mpifort >/dev/null || fail "mpifort is unavailable"
nvfortran --version 2>&1 | grep -q '25\.11' || fail "expected NVIDIA HPC SDK 25.11"
mpifort --showme:command 2>&1 | grep -q 'nvfortran' || fail "mpifort is not using nvfortran"

stage PATCH_APPLICATION
git -C "$shellset_root" apply --check "$patch_path" || fail "git apply --check rejected the source patch"
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
[[ "$new_exe_sha" != "$expected_old_exe_sha" ]] || fail "executable SHA stayed at the qualified parent identity"
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
  mkdir -p "$root/INPUT"
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
  if (cd "$fixture_root/input-$partial" && ../inputsetup_pair_driver.exe . partial) >"$fixture_root/$partial.log" 2>&1; then
    fail "partial INPUT pair unexpectedly succeeded: $partial"
  fi
  grep -q 'Incomplete ARCANA OrbData source pair' "$fixture_root/$partial.log" || fail "partial-pair failure lacked diagnostic: $partial"
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
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys

def records(path):
    return [line.split() for line in Path(path).read_text(errors="strict").splitlines()
            if line.strip() and not line.lstrip().startswith("Program invoked with:")]

reference, observed = map(records, sys.argv[1:])
if len(reference) != len(observed):
    raise SystemExit(f"Models row count mismatch: {len(reference)} != {len(observed)}")
max_abs = Decimal(0)
max_rel = Decimal(0)
for row, (left, right) in enumerate(zip(reference, observed), 1):
    if len(left) != len(right):
        raise SystemExit(f"Models column count mismatch at row {row}")
    for column, (a, b) in enumerate(zip(left, right), 1):
        try:
            x, y = Decimal(a), Decimal(b)
        except InvalidOperation:
            if a != b:
                raise SystemExit(f"Models text mismatch at row {row}, column {column}: {a!r} != {b!r}")
            continue
        difference = abs(x-y)
        max_abs = max(max_abs, difference)
        if x != 0:
            max_rel = max(max_rel, difference/abs(x))
        elif difference != 0:
            max_rel = Decimal("Infinity")
        if difference != 0:
            raise SystemExit(f"ListEx1 numeric mismatch at reported precision row {row}, column {column}: {a} != {b}")
print(f"STOCK_LISTEX1_MAX_ABS={max_abs} MAX_REL={max_rel}")
PY

echo "SHELLSET_PATCH_QUALIFICATION=PASS_PENDING_MANUAL_COMMIT_AND_EVIDENCE_CAPTURE"
echo "PATCH_SHA256=$expected_patch_sha"
echo "SHELLSET_NEW_COMMIT=not created by this script"
echo "SHELLSET_EXE_SHA256=$new_exe_sha"
echo "FAIR_FIXTURE_ROOT=$fixture_root"
echo "BUILD_LOG=$build_log"
echo "Manual next commands after review:"
echo "  git -C '$shellset_root' add src/MOD_ShellSet.f90 src/OrbData5.f90 src/MOD_Data.f90"
echo "  git -C '$shellset_root' commit -m 'arcana: add governed OrbData explicit inputs'"
echo "No push, ARCANA T0 OrbData, or SHELLS T0 mechanics was performed by this script."

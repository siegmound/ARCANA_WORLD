#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
expected_branch="r6/t0-authorial-realization-materialization"
minimum_ancestor="0dfccaa0722f025fee1590d94c78eb30ac54d828"
expected_field_package_sha="31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534"
expected_shellset_parent="09a06ecd061f00b80a52af86e31d609ff5545a8b"
expected_old_exe_sha="03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349"
patch_path="$repo_root/patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch"
expected_patch_sha="4d4e5cfa07e8af0c52bc2fbcf2c77a080c2b68921174ad2e4cde078c5425843c"

[[ "$(git branch --show-current)" == "$expected_branch" ]] || { echo "wrong ARCANA branch" >&2; exit 2; }
git merge-base --is-ancestor "$minimum_ancestor" HEAD || { echo "ARCANA HEAD is not descended from the adapter commit" >&2; exit 2; }
[[ "$(sha256sum R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE_SURFACE_CLOSED.npz | awk '{print $1}')" == "$expected_field_package_sha" ]] || { echo "surface-closed package SHA mismatch" >&2; exit 2; }

shellset_root="${ARCANA_SHELLSET_ROOT:-$HOME/HPC-POMDP/tools/ShellSet-v1.1.0}"
[[ -d "$shellset_root/.git" ]] || { echo "ShellSet checkout not found: $shellset_root" >&2; exit 2; }
[[ "$(git -C "$shellset_root" rev-parse HEAD)" == "$expected_shellset_parent" ]] || { echo "ShellSet parent HEAD mismatch" >&2; exit 2; }
[[ -z "$(git -C "$shellset_root" status --porcelain --untracked-files=no)" ]] || { echo "tracked ShellSet files are not clean" >&2; exit 2; }
[[ "$(sha256sum "$shellset_root/ShellSet.exe" | awk '{print $1}')" == "$expected_old_exe_sha" ]] || { echo "pre-patch ShellSet executable SHA mismatch" >&2; exit 2; }
[[ "$(sha256sum "$patch_path" | awk '{print $1}')" == "$expected_patch_sha" ]] || { echo "patch SHA mismatch" >&2; exit 2; }

command -v nvfortran >/dev/null
command -v mpifort >/dev/null
nvfortran --version | grep -q '25\.11' || { echo "expected NVIDIA HPC SDK 25.11" >&2; exit 2; }
mpifort --showme:command | grep -q 'nvfortran' || { echo "mpifort is not using nvfortran" >&2; exit 2; }

git -C "$shellset_root" apply --check "$patch_path"
git -C "$shellset_root" apply "$patch_path"
git -C "$shellset_root" diff --check

build_log="$(mktemp "${TMPDIR:-/tmp}/arcana-shellset-build.XXXXXX.log")"
set +e
(cd "$shellset_root" && make -B ShellSet FC=nvfortran MPI=mpifort INCL= CMPLFLAGS="-Mbackslash -Ilib" MKLFLAGS="-lblas -llapack") 2>&1 | tee "$build_log"
build_rc=${PIPESTATUS[0]}
set -e
[[ $build_rc -eq 0 ]] || { echo "NVIDIA ShellSet build failed; log: $build_log" >&2; exit "$build_rc"; }
[[ -x "$shellset_root/ShellSet.exe" ]] || { echo "built ShellSet.exe is missing" >&2; exit 2; }
new_exe_sha="$(sha256sum "$shellset_root/ShellSet.exe" | awk '{print $1}')"
[[ "$new_exe_sha" != "$expected_old_exe_sha" ]] || { echo "executable identity did not change after source patch" >&2; exit 2; }
if ldd "$shellset_root/ShellSet.exe" | grep -q 'not found'; then echo "ShellSet has unresolved dynamic libraries" >&2; exit 2; fi

fixture_root="$(mktemp -d "${TMPDIR:-/tmp}/arcana-orbdata-fixture.XXXXXX")"
objects=(lib/OrbScore2.o lib/MOD_Score.o lib/SHELLS_v5.0.o lib/MOD_Shells.o lib/OrbData5.o lib/MOD_Data.o lib/DMods.o lib/MOD_VarCheck.o lib/MOD_ShellSet.o lib/MOD_SharedVars.o lib/mkl_service.o lib/lapack.o)
for object in "${objects[@]}"; do [[ -f "$shellset_root/$object" ]] || { echo "required object missing: $object" >&2; exit 2; }; done
mpifort -Mbackslash -I"$shellset_root/lib" -o "$fixture_root/assign_source_generalization.exe" \
  "$repo_root/tests/fixtures/r6_t0_orbdata_arcana/assign_source_generalization.f90" \
  "${objects[@]/#/$shellset_root/}" -lblas -llapack
"$fixture_root/assign_source_generalization.exe" | tee "$fixture_root/assign_fixture.log"
grep -q 'ARCANA_SYNTHETIC_ASSIGN_FIXTURE=PASS' "$fixture_root/assign_fixture.log"

mpifort -Mbackslash -I"$shellset_root/lib" -o "$fixture_root/open_pair_driver.exe" \
  "$repo_root/tests/fixtures/r6_t0_orbdata_arcana/open_pair_driver.f90" \
  "${objects[@]/#/$shellset_root/}" -lblas -llapack
make_input_set() {
  local root="$1" mode="$2"
  mkdir -p "$root/ThID_1_Data_input"
  for suffix in 1 2 3 7 11; do : > "$root/ThID_1_Data_input/fort_1.$suffix"; done
  if [[ "$mode" == stock ]]; then : > "$root/ThID_1_Data_input/fort_1.12"; fi
  if [[ "$mode" == full || "$mode" == only15 ]]; then : > "$root/ThID_1_Data_input/fort_1.15"; fi
  if [[ "$mode" == full || "$mode" == only16 ]]; then : > "$root/ThID_1_Data_input/fort_1.16"; fi
}
mkdir -p "$fixture_root/open-stock" "$fixture_root/open-full" "$fixture_root/open-only15" "$fixture_root/open-only16"
make_input_set "$fixture_root/open-stock" stock
make_input_set "$fixture_root/open-full" full
make_input_set "$fixture_root/open-only15" only15
make_input_set "$fixture_root/open-only16" only16
(cd "$fixture_root/open-stock" && ../open_pair_driver.exe "$fixture_root/open-stock") | grep -q 'ORBDATA_INPUT_PAIR_OPEN_CLOSE=PASS'
(cd "$fixture_root/open-full" && ../open_pair_driver.exe "$fixture_root/open-full") | grep -q 'ORBDATA_INPUT_PAIR_OPEN_CLOSE=PASS'
for partial in open-only15 open-only16; do
  if (cd "$fixture_root/$partial" && ../open_pair_driver.exe "$fixture_root/$partial") >"$fixture_root/$partial.log" 2>&1; then
    echo "partial ARCANA pair unexpectedly opened: $partial" >&2; exit 2
  fi
done
echo "ARCANA pair activation/partial-pair fixture PASS"

smoke_log="$fixture_root/mpi-smoke.log"
set +e
(cd "$shellset_root" && mpirun -np 2 ./ShellSet.exe -info) >"$smoke_log" 2>&1
smoke_rc=$?
set -e
[[ $smoke_rc -eq 0 || $smoke_rc -eq 8 ]] || { cat "$smoke_log" >&2; echo "MPI compile/link smoke failed" >&2; exit "$smoke_rc"; }
grep -qi 'ShellSet' "$smoke_log" || { cat "$smoke_log" >&2; echo "MPI smoke did not reach ShellSet info" >&2; exit 2; }

reference_models="$shellset_root/NVHPC_CAPACITY_ListEx1_n10_t5/Models.txt"
[[ -f "$reference_models" ]] || { echo "qualified ListEx1 n10_t5 reference Models.txt is missing" >&2; exit 2; }
cmp -s "$shellset_root/INPUT/ListInput.in" "$shellset_root/NVHPC_CAPACITY_ListEx1_n10_t5/ListInput.in" || { echo "active ListInput.in differs from qualified ListEx1 input" >&2; exit 2; }
run_name="NVHPC_ARCANA_PATCH_ListEx1_n10_t5_$(date -u +%Y%m%dT%H%M%SZ)"
[[ ! -e "$shellset_root/$run_name" ]] || { echo "output path already exists: $run_name" >&2; exit 2; }
(cd "$shellset_root" && mpirun -np 11 ./ShellSet.exe -Dir "$run_name" -InOpt List -Iter 5) | tee "$fixture_root/list_ex1.log"
patched_models="$shellset_root/$run_name/Models.txt"
[[ -f "$patched_models" ]] || { echo "patched ListEx1 Models.txt missing" >&2; exit 2; }
"${ARCANA_PYTHON:-python3}" - "$reference_models" "$patched_models" <<'PY'
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

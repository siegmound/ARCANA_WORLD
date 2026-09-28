#!/usr/bin/env bash
set -euo pipefail

# Validate a governed OrbData5 result on FAIR. This script never starts ShellSet
# mechanics, selects dt, or advances T0. It fails closed until an authorized
# PRE_ORBDATA input manifest and recorded OrbData output manifest exist.

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
expected_branch="r6/t0-authorial-realization-materialization"
expected_base="15dfca97b24c387af5b46c32f2b7db58154c2268"
expected_evidence_sha="ab29de4577c4c4b007d41a7ac5567d7b287c7fed5dee3107aeb69dc35df1a350"
expected_evidence_id="8265b998a8ddb8e3fdfd7371c9bfe076e6697fbbd7fcb922d77a37317ef59afe"
expected_shellset_commit="09a06ecd061f00b80a52af86e31d609ff5545a8b"
expected_shellset_sha="03e1a3f7ac0c4593a4a6eb641bb6d8acd0b752da5c5fd7b1ee74788fb705e349"
expected_upstream_commit="e4a6fbd5997b6c4978924649dff1abab0c96ca57"
expected_field_package_sha="31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534"
historical_parent_field_package_sha="39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e"
expected_total_surface_sha="b5cbbac4136b46f6352d2738552013995477b956ab31af9435b10b3d2ad4be70"
expected_ocean_thermal_sha="90ebdb63a981fde968a696a6844a51fb47be6a87e756f0651b947be10901d887"
expected_mesh_sha="6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"

[[ "$(git branch --show-current)" == "$expected_branch" ]] || { echo "wrong ARCANA branch" >&2; exit 2; }
git merge-base --is-ancestor "$expected_base" HEAD || { echo "ARCANA HEAD is not based on the governed R6 T0 base" >&2; exit 2; }

evidence_sha="$(git show "HEAD:R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json" | sha256sum | awk '{print $1}')"
[[ "$evidence_sha" == "$expected_evidence_sha" ]] || { echo "committed FAIR evidence SHA mismatch" >&2; exit 2; }

shellset_root="${ARCANA_SHELLSET_ROOT:-/home/jlpfritas/HPC-POMDP/tools/ShellSet-v1.1.0}"
[[ "$(git -C "$shellset_root" rev-parse HEAD)" == "$expected_shellset_commit" ]] || { echo "qualified ShellSet commit mismatch" >&2; exit 2; }
shellset_sha="$(sha256sum "$shellset_root/ShellSet.exe" | awk '{print $1}')"
[[ "$shellset_sha" == "$expected_shellset_sha" ]] || { echo "qualified ShellSet executable SHA mismatch" >&2; exit 2; }

python_bin="${ARCANA_PYTHON:-python3}"
"$python_bin" --version
PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}" "$python_bin" - <<'PY'
import arcana_worldsim.r6.shellset_mesh
import json
from pathlib import Path
closure = json.loads(Path("R6_T0_B_PANGAEA_LIKE_V2_OCEAN_SURFACE_CLOSURE.json").read_text(encoding="utf-8"))
if closure["materialized"]["field_package_sha256"] != "31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534":
    raise SystemExit("surface-closed field package identity mismatch")
if closure["parent"]["field_package_sha256"] != "39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e":
    raise SystemExit("historical parent field package lineage mismatch")
if closure["materialized"]["normalized_field_hashes"]["total_surface_elevation_m"] != "b5cbbac4136b46f6352d2738552013995477b956ab31af9435b10b3d2ad4be70":
    raise SystemExit("total surface elevation identity mismatch")
if closure["materialized"]["normalized_field_hashes"]["ocean_thermal_isostatic_elevation_m"] != "90ebdb63a981fde968a696a6844a51fb47be6a87e756f0651b947be10901d887":
    raise SystemExit("ocean thermal component identity mismatch")
print("Python environment/imports PASS")
PY

manifest="${ARCANA_T0_ORBDATA_RESULT_MANIFEST:-R6_T0_ORBDATA_FAIR_RESULT_MANIFEST.json}"
[[ -f "$manifest" ]] || { echo "blocked: no governed PRE_ORBDATA/OrbData result manifest at $manifest; do not execute OrbData or mechanics" >&2; exit 3; }

"$python_bin" - "$manifest" "$expected_evidence_id" "$expected_shellset_commit" "$expected_shellset_sha" "$expected_upstream_commit" "$expected_field_package_sha" "$expected_mesh_sha" <<'PY'
import hashlib, json, pathlib, sys
manifest_path = pathlib.Path(sys.argv[1])
expected = {
    "evidence_identity_sha256": sys.argv[2],
    "shellset_runtime_commit": sys.argv[3],
    "shellset_executable_sha256": sys.argv[4],
    "shellset_upstream_commit": sys.argv[5],
    "field_package_sha256": sys.argv[6],
    "mesh_sha256": sys.argv[7],
}
data = json.loads(manifest_path.read_text(encoding="utf-8"))
for key, value in expected.items():
    if data.get(key) != value:
        raise SystemExit(f"manifest {key} mismatch")
if data.get("pre_orbdata_ready") is not True or data.get("t0_input_transformations_authorized") is not True:
    raise SystemExit("PRE_ORBDATA/input-transformation gate is not authorized")
if any(data.get(key) is not False for key in ("shellset_mechanics_authorized", "forward_evolution", "dt_selected", "t1_created")):
    raise SystemExit("forbidden mechanics/evolution flag present")
for group in ("generated_inputs", "runtime_outputs"):
    entries = data.get(group)
    if not isinstance(entries, list) or not entries:
        raise SystemExit(f"manifest {group} must list files and SHA256 values")
    for entry in entries:
        path = pathlib.Path(entry["path"])
        if not path.is_absolute():
            path = manifest_path.parent / path
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise SystemExit(f"{group} hash mismatch: {path}")
        if group == "runtime_outputs" and entry.get("status") != "PASS":
            raise SystemExit(f"runtime output status is not PASS: {path}")
print("Governed OrbData result/input/output hashes PASS; mechanics/evolution remain false")
PY

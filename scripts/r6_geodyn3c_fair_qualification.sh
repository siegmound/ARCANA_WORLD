#!/usr/bin/env bash
# Read-only qualification of the existing GEODYN-2A-R1 ASPECT series.
# Usage:
#   bash scripts/r6_geodyn3c_fair_qualification.sh \
#     REPO SOURCE_ROOT PVD_RELATIVE_REF NUMERIC_AUDIT.json \
#     SOURCE_INVENTORY.json RUN_IDENTITY.json EVIDENCE_PARENT
set -Eeuo pipefail
IFS=$'\n\t'

EXPECTED_BRANCH='r6/multiphysics-integration-20261026'
EXPECTED_COMMIT=${GEODYN3C_EXPECTED_COMMIT:-}
EXPECTED_PARENT='e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa'
ASPECT_COMMIT='30eb77ee5da186137d436dbad35c6cb3cab64b69'
R1_ADAPTER_COMMIT='1fd5e8d8f21e28876da9ef89423755615efc6162'
EXPECTED_TIMES_COUNT=11
EXPECTED_POINTS=1152
EXPECTED_CELLS=512
EXPECTED_POINT_FIELDS=9
EXPECTED_TESTS=71

fail() { printf 'BLOCKED: %s\n' "$*" >&2; exit 2; }
[[ $# -eq 7 ]] || fail 'expected exactly seven arguments; see usage in script header'
[[ "$EXPECTED_COMMIT" =~ ^[0-9a-f]{40}$ ]] || fail 'set GEODYN3C_EXPECTED_COMMIT to the exact reviewed 40-hex Git SHA-1 commit'
REPO=$(realpath -e -- "$1") || fail 'repository path does not exist'
SOURCE_ROOT=$(realpath -e -- "$2") || fail 'source root does not exist'
PVD_REF=$3
AUDIT=$(realpath -e -- "$4") || fail 'NUMERIC_AUDIT.json is unavailable'
INVENTORY=$(realpath -e -- "$5") || fail 'independent source inventory JSON is unavailable'
CLAIMS=$(realpath -e -- "$6") || fail 'run identity claims JSON is unavailable'
EVIDENCE_PARENT=$(realpath -e -- "$7") || fail 'evidence parent must already exist'

[[ -d "$REPO/.git" ]] || fail 'REPO must be a normal Git worktree root'
[[ -d "$SOURCE_ROOT" ]] || fail 'source root must be a directory'
[[ -f "$AUDIT" && -f "$INVENTORY" && -f "$CLAIMS" ]] || fail 'audit, inventory and claim inputs must be files'
[[ -f "$SOURCE_ROOT/$PVD_REF" ]] || fail 'PVD relative reference is absent from source root'
case "$PVD_REF" in /*|../*|*/../*|..|*\\*) fail 'PVD reference must be a safe relative path';; esac

REPO=$(realpath -e -- "$REPO")
case "$EVIDENCE_PARENT/" in "$REPO/"*) fail 'evidence parent must be outside the Git checkout';; esac
[[ -d "$EVIDENCE_PARENT" && ! -L "$EVIDENCE_PARENT" ]] || fail 'evidence parent must pre-exist and must not be a symlink'

branch=$(git -C "$REPO" branch --show-current)
head=$(git -C "$REPO" rev-parse HEAD)
parent=$(git -C "$REPO" rev-parse 'HEAD^')
[[ "$branch" == "$EXPECTED_BRANCH" ]] || fail "wrong branch: $branch"
[[ "$head" == "$EXPECTED_COMMIT" ]] || fail "wrong HEAD: $head"
[[ "$parent" == "$EXPECTED_PARENT" ]] || fail "wrong parent: $parent"
git -C "$REPO" cat-file -e "$EXPECTED_COMMIT^{commit}" || fail 'expected commit object is unavailable'
git -C "$REPO" diff --quiet "$EXPECTED_COMMIT" -- || fail 'tracked worktree has modifications; use a clean/read-only checkout'
git -C "$REPO" diff --cached --quiet || fail 'index has staged changes; use a clean/read-only checkout'
tracked_status_before=$(git -C "$REPO" status --porcelain --untracked-files=no)

run_stamp=$(date -u +%Y%m%dT%H%M%SZ)
RUN_DIR="$EVIDENCE_PARENT/GEODYN3C_${run_stamp}"
mkdir -- "$RUN_DIR" || fail "evidence destination exists or cannot be created: $RUN_DIR"
trap 'rc=$?; post=$(git -C "$REPO" status --porcelain --untracked-files=no 2>&1); printf "%s\n" "$post" > "$RUN_DIR/tracked_status_after.txt"; if [[ "$post" != "$tracked_status_before" ]] || ! git -C "$REPO" diff --quiet "$EXPECTED_COMMIT" -- || ! git -C "$REPO" diff --cached --quiet; then printf "FAIL: tracked checkout/index changed during launcher\n" > "$RUN_DIR/checkout_immutability.txt"; rc=91; else printf "PASS: tracked checkout/index unchanged\n" > "$RUN_DIR/checkout_immutability.txt"; fi; printf "%s\n" "$rc" > "$RUN_DIR/launcher.exitcode"; exit "$rc"' EXIT
mkdir -- "$RUN_DIR/source-extract"
script_path=$(realpath -e -- "$0") || fail 'cannot resolve qualification launcher path'
cp -- "$script_path" "$RUN_DIR/qualification_launcher.sh"
sha256sum "$RUN_DIR/qualification_launcher.sh" > "$RUN_DIR/qualification_launcher.sha256"

printf '%s\n' "$EXPECTED_COMMIT" > "$RUN_DIR/source_commit.txt"
printf '%s\n' "$EXPECTED_PARENT" > "$RUN_DIR/source_parent.txt"
printf '%s\n' "$branch" > "$RUN_DIR/source_branch.txt"
git -C "$REPO" archive --format=tar "$EXPECTED_COMMIT" > "$RUN_DIR/source.tar"
sha256sum "$RUN_DIR/source.tar" > "$RUN_DIR/source.tar.sha256"
tar -xf "$RUN_DIR/source.tar" -C "$RUN_DIR/source-extract"

python --version > "$RUN_DIR/python_version.txt" 2>&1 || fail 'python is unavailable'
python -m pytest --version > "$RUN_DIR/pytest_version.txt" 2>&1 || fail 'pytest is unavailable; do not install packages in this task'
cp -- "$AUDIT" "$RUN_DIR/NUMERIC_AUDIT.json"
cp -- "$INVENTORY" "$RUN_DIR/SOURCE_INVENTORY.json"
cp -- "$CLAIMS" "$RUN_DIR/RUN_IDENTITY_CLAIMS.json"
sha256sum "$RUN_DIR/NUMERIC_AUDIT.json" "$RUN_DIR/SOURCE_INVENTORY.json" "$RUN_DIR/RUN_IDENTITY_CLAIMS.json" > "$RUN_DIR/input_sha256.txt"

set +e
(cd "$RUN_DIR/source-extract" && PYTHONPATH="$RUN_DIR/source-extract/src" \
  python -m pytest -q -rs --basetemp="$RUN_DIR/pytest-tmp" \
  tests/test_r6_experimental_trajectory_archive.py \
  tests/test_r6_aspect_snapshot_reader.py) 2>&1 | tee "$RUN_DIR/pytest.log"
pytest_rc=${PIPESTATUS[0]}
set -e
printf '%s\n' "$pytest_rc" > "$RUN_DIR/pytest.exitcode"
[[ $pytest_rc -eq 0 ]] || fail "Linux focused pytest failed (exit $pytest_rc)"
python - "$RUN_DIR/pytest.log" "$EXPECTED_TESTS" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
expected = int(sys.argv[2])
matches = re.findall(r"(?m)^=+\s*(.*?)\s+in\s+[0-9.]+s\s*=+$", text)
if not matches:
    raise SystemExit("pytest summary line not found")
summary = matches[-1]
passed = re.search(r"(\d+) passed", summary)
failed = re.search(r"(\d+) failed", summary)
skipped = re.search(r"(\d+) skipped", summary)
counts = (int(passed.group(1)) if passed else 0,
          int(failed.group(1)) if failed else 0,
          int(skipped.group(1)) if skipped else 0)
print(f"pytest summary: passed={counts[0]} failed={counts[1]} skipped={counts[2]}")
if counts != (expected, 0, 0):
    raise SystemExit(f"expected {expected} PASS, 0 FAIL, 0 SKIP; got {counts}")
PY

cat > "$RUN_DIR/run_geodyn3c.py" <<'PY'
from __future__ import annotations
import hashlib, json, math, shutil, sys
from collections import Counter
from pathlib import Path

source_tree, source_root_s, pvd_ref, audit_s, inventory_s, claims_s, evidence_s = sys.argv[1:]
sys.path.insert(0, str(Path(source_tree) / "src"))
from arcana_worldsim.r6.experimental_trajectory_archive import (
    ArchiveError, ExperimentalTrajectoryArchive, NativeTime, RunIdentityClaim,
    SourceDigest, index_existing_aspect_series,
)
from arcana_worldsim.r6.adapters.aspect_snapshot_reader import AspectSnapshotSeries

EXPECTED_COMMIT = "e3946add3fe63d2f5fc4c710d0e1d87e01f83ffa"
EXPECTED_PARENT = "0256458553f5ee856739cd0abff7561d90ad1198"
EXPECTED_ASPECT_COMMIT = "30eb77ee5da186137d436dbad35c6cb3cab64b69"
EXPECTED_R1_ADAPTER_COMMIT = "1fd5e8d8f21e28876da9ef89423755615efc6162"
EXPECTED_COMPLETION = 1.098612289
EXPECTED_LAST = 1.0142299266
EXPECTED_TIMES = 11
EXPECTED_POINTS = 1152
EXPECTED_CELLS = 512
EXPECTED_FIELDS = 9

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def find_snapshot_rows(node):
    """Extract only explicit auditor snapshot records; fail closed on unknown schema."""
    found = []
    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ("snapshots", "snapshot_audits", "snapshot_records") and isinstance(child, list):
                    for row in child:
                        if isinstance(row, dict) and any(k in row for k in ("time", "time_value", "timestep", "time_s")):
                            found.append(row)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(node)
    # The same rows can be reached through nested summary branches.
    unique = {}
    for row in found:
        marker = json.dumps(row, sort_keys=True, separators=(",", ":"))
        unique[marker] = row
    return list(unique.values())

def row_time(row):
    for key in ("time_value", "timestep", "time_s", "time"):
        if key in row:
            value = row[key]
            if isinstance(value, dict):
                value = value.get("value")
            if isinstance(value, (int, float)) and math.isfinite(float(value)):
                return float(value)
    raise ValueError("independent audit snapshot lacks a numeric native-time field")

def field_hashes(row):
    fields = row.get("fields")
    if fields is None:
        fields = row.get("field_arrays")
    hashes = {}
    def collect(value, hint=None):
        if isinstance(value, dict):
            digest = value.get("sha256_bytes")
            if isinstance(digest, str) and len(digest) == 64:
                name = (value.get("source_name") or value.get("name") or value.get("field_name")
                        or value.get("source_key") or value.get("field") or value.get("key") or hint)
                if isinstance(name, str):
                    name = name.removeprefix("point:").removeprefix("cell:")
                    if name in hashes: raise ValueError(f"duplicate audit field identity {name}")
                    hashes[name] = digest.lower()
            else:
                for key, child in value.items(): collect(child, key if isinstance(key, str) else hint)
        elif isinstance(value, list):
            for child in value: collect(child, hint)
    collect(fields)
    return hashes

def require(condition, message):
    if not condition: raise ValueError(message)

evidence = Path(evidence_s)
qualification = {"status": "FAIL", "stage": "INITIALIZING", "failures": []}
comparison_doc = {"status": "PENDING", "records": []}
query_doc = {"status": "PENDING", "records": []}
negative_doc = {"status": "PENDING", "checks": []}
try:
    source_root = Path(source_root_s).resolve(strict=True)
    audit_path = Path(audit_s)
    inventory_path = Path(inventory_s)
    claims_path = Path(claims_s)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    inventory_doc = json.loads(inventory_path.read_text(encoding="utf-8"))
    claims_doc = json.loads(claims_path.read_text(encoding="utf-8"))
    require(isinstance(inventory_doc, dict) and isinstance(inventory_doc.get("files"), list),
            "SOURCE_INVENTORY_SCHEMA: expected {files:[{relative_ref,byte_length,sha256}]} from prior evidence")
    require(isinstance(claims_doc, dict) and isinstance(claims_doc.get("run_identity"), dict),
            "RUN_CLAIMS_SCHEMA: expected {run_identity:{...RunIdentityClaim fields...}}")
    claim_values = claims_doc["run_identity"]
    claim = RunIdentityClaim(**claim_values)
    require(claim.solver_name == "ASPECT" and claim.solver_version == "3.2.0-pre",
            "run claim does not bind the reported ASPECT 3.2.0-pre runtime")
    # Exact commit strings are retained in typed fields. The archive validates
    # syntax only; this explicit algorithm map is still an operator claim, not
    # authentication. Do not derive identities by padding, hashing, or truncation.
    provenance = claim.declared_provenance
    require(claim.solver_source_commit == EXPECTED_ASPECT_COMMIT,
            "solver_source_commit must retain the exact reported ASPECT Git object ID")
    require(claim.repository_commit == EXPECTED_R1_ADAPTER_COMMIT,
            "repository_commit must retain the exact GEODYN-2A-R1 source Git object ID")
    require(claim.adapter_commit == EXPECTED_COMMIT,
            "adapter_commit must retain the exact GEODYN-3B implementation Git object ID")
    require({key: provenance.get(key) for key in (
        "solver_source_commit_algorithm", "repository_commit_algorithm", "adapter_commit_algorithm"
    )} == {"solver_source_commit_algorithm": "sha1", "repository_commit_algorithm": "sha1",
          "adapter_commit_algorithm": "sha1"},
        "run claims must declare the three known Git object ID algorithms explicitly")
    require(claim.solver_completed_time == EXPECTED_COMPLETION,
            "run claim solver completion time differs from the reported R1 value")
    require(claim.time_unit == "s", "native solver time unit must be seconds for this R1 comparison")
    qualification["stage"] = "SOURCE_PREHASH"

    pvd_path = (source_root / pvd_ref).resolve(strict=True)
    require(pvd_path.is_relative_to(source_root), "PVD reference escaped the source root")
    series = AspectSnapshotSeries(pvd_path, run_id="geodyn3c-preflight", time_unit=claim.time_unit,
        time_unit_source=claim.time_unit_source, mpi_rank_count=1,
        solver_completed_time=claim.solver_completed_time,
        experiment_provenance={"repository_commit": claim.repository_commit, "adapter_commit": claim.adapter_commit})
    source_rows = series.audit().snapshots
    refs = {pvd_ref}
    for row in source_rows:
        refs.update(row.file_sha256.keys())
    declared = {item["relative_ref"]: SourceDigest(**item) for item in inventory_doc["files"]}
    require(set(declared) == refs, "independent source inventory membership differs from PVD-referenced source files")
    before = {ref: {"byte_length": (source_root / ref).stat().st_size, "sha256": sha256(source_root / ref)} for ref in sorted(refs)}
    require(all(before[ref]["byte_length"] == declared[ref].byte_length and before[ref]["sha256"] == declared[ref].sha256 for ref in refs),
            "source bytes do not match the pre-existing independently preserved inventory")
    dump(evidence / "originals_pre_hashes.json", before)

    qualification["stage"] = "INDEX"
    index_root = evidence / "archive_index"
    build = index_existing_aspect_series(trusted_source_root=source_root, pvd_relative_ref=pvd_ref,
        run_identity=claim, expected_source_inventory=declared, output_index_root=index_root)
    require(build.status == "COMPLETE" and build.index_ref == "manifest.json", f"index build failed: {build}")
    archive = ExperimentalTrajectoryArchive.open(build.index_ref, trusted_index_root=index_root,
        trusted_source_roots={"source": source_root})
    integrity = archive.verify_integrity()
    dump(evidence / "INTEGRITY_REPORT.json", integrity.__dict__)
    require(integrity.status == "PASS", f"archive integrity status={integrity.status}: {integrity.message}")
    manifest = archive.manifest
    rows = manifest["snapshots"]
    times = [row["time"]["value"] for row in rows]
    require(len(rows) == EXPECTED_TIMES, f"expected {EXPECTED_TIMES} snapshots, got {len(rows)}")
    require(times[0] == 0.0 and times[-1] == EXPECTED_LAST and all(a < b for a,b in zip(times,times[1:])),
            f"native snapshot time sequence mismatch: {times}")
    require(manifest["time"]["solver_completed_time"] == EXPECTED_COMPLETION and times[-1] != EXPECTED_COMPLETION,
            "solver completion must remain distinct from last stored snapshot")
    meshes = manifest["mesh_catalog"]
    require(len(meshes) == 1 and all(row["mesh_id"] == meshes[0]["mesh_id"] for row in rows),
            "expected numerically stable single mesh")
    require(meshes[0]["point_count"] == EXPECTED_POINTS and meshes[0]["cell_count"] == EXPECTED_CELLS,
            "mesh dimensions differ from R1 qualification")
    require(meshes[0]["cell_type_counts"] == {"9": EXPECTED_CELLS},
            "VTK cell-type inventory is not exactly 512 VTK quadrilaterals (type 9)")
    fields = manifest["field_catalog"]
    require(len(fields) == EXPECTED_FIELDS and all(field["association"] == "point" for field in fields),
            "expected nine point-associated fields")
    require(manifest["classification"] == "SYNTHETIC_ENGINEERING_ONLY", "experimental classification mismatch")
    require(manifest["authority"] == "OPERATOR_REPORTED_UNAUTHENTICATED", "authority was improperly upgraded")
    require(manifest["capabilities"]["restart"] == "NOT_AVAILABLE" and manifest["capabilities"]["reconstruction"] == "NOT_CLAIMED",
            "snapshot observations were misclassified as restart/reconstruction data")
    observations = manifest["series_observations"]
    require(observations["mesh_stable"] and observations["schema_stable"],
            "reader did not observe stable R1 mesh/schema")
    require("point:T" in observations["zero_valued_invariant_fields"],
            "expected observed T=0 invariant is absent; do not infer its physical meaning")
    require(any(set(pair) == {"point:density", "point:density_comp"}
                for pair in observations["numerically_duplicate_fields"]),
            "reported density/density_comp numerical duplicate was not reproduced")

    qualification["stage"] = "QUERY_AND_AUDIT_COMPARISON"
    run_id = manifest["run"]["run_id"]
    all_rows = archive.query_snapshots(run_id).value
    require(len(all_rows) == EXPECTED_TIMES, "all-snapshot query count mismatch")
    exact = archive.get_snapshot_at(run_id, NativeTime(times[0], "s", claim.time_basis_id))
    require(exact.status == "FOUND" and exact.value["snapshot_id"] == rows[0]["snapshot_id"], "exact-time query mismatch")
    absent = archive.get_snapshot_at(run_id, NativeTime(EXPECTED_COMPLETION, "s", claim.time_basis_id))
    require(absent.status == "MISSING_SNAPSHOT", "solver-completion timestamp unexpectedly resolved to an archived snapshot")
    gap_midpoint = (times[-1] + EXPECTED_COMPLETION) / 2.0
    gap = archive.query_snapshots(run_id, start=NativeTime(gap_midpoint, "s", claim.time_basis_id),
                                  end=NativeTime(gap_midpoint, "s", claim.time_basis_id))
    require(gap.status == "MISSING_SNAPSHOT", "query in the unarchived tail returned a fabricated/interpolated snapshot")
    interval = archive.query_snapshots(run_id, start=NativeTime(times[0], "s", claim.time_basis_id),
                                       end=NativeTime(times[-1], "s", claim.time_basis_id))
    require(interval.status == "FOUND" and len(interval.value) == EXPECTED_TIMES, "inclusive interval query mismatch")
    field_list = archive.list_fields(rows[0]["snapshot_id"])
    require(field_list.status == "FOUND" and len(field_list.value) == EXPECTED_FIELDS, "field query mismatch")
    mesh_result = archive.get_mesh(rows[0]["mesh_id"])
    require(mesh_result.status == "FOUND" and mesh_result.value["mesh_id"] == rows[0]["mesh_id"], "mesh query mismatch")
    field = fields[0]
    field_result = archive.get_field(rows[0]["snapshot_id"], field["field_id"])
    snapshot_result = archive.get_snapshot(rows[0]["snapshot_id"])
    require(field_result.status == snapshot_result.status == "FOUND", "on-demand numerical read failed")
    query_doc.update({"status": "PASS", "records": [
        {"query": "exact_first_time", "status": exact.status, "snapshot_id": exact.value["snapshot_id"]},
        {"query": "exact_solver_completion_time", "status": absent.status},
        {"query": "empty_unarchived_tail_interval", "status": gap.status},
        {"query": "inclusive_full_interval", "status": interval.status, "count": len(interval.value)},
        {"query": "field_catalog", "status": field_list.status, "count": len(field_list.value)},
        {"query": "mesh", "status": mesh_result.status, "mesh_id": rows[0]["mesh_id"]},
        {"query": "on_demand_field", "status": field_result.status, "field_id": field["field_id"],
         "source_name": field["source_name"], "sha256_typed": rows[0]["typed_field_sha256"][field["field_id"]]},
        {"query": "on_demand_snapshot", "status": snapshot_result.status,
         "field_count": len(snapshot_result.value["fields"]), "mesh_id": rows[0]["mesh_id"]},
        {"query": "restart_capability", "status": manifest["capabilities"]["restart"]},
    ]})
    dump(evidence / "QUERY_RESULTS.json", query_doc)

    audit_rows = find_snapshot_rows(audit)
    require(len(audit_rows) == EXPECTED_TIMES,
            "NUMERIC_AUDIT_SCHEMA: could not identify exactly 11 snapshot records; inspect schema, do not bypass comparison")
    audit_by_time = {}
    for audit_row in audit_rows:
        t = row_time(audit_row)
        require(t not in audit_by_time, f"duplicate independent audit time {t}")
        audit_by_time[t] = field_hashes(audit_row)
    require(set(audit_by_time) == set(times), "archive and independent audit native times differ")
    compared_fields = 0
    comparison_doc.update({"status": "RUNNING", "method": "per-native-time, per-field SHA256 of typed numeric values",
                           "independent_audit_sha256": sha256(audit_path), "records": []})
    for row in rows:
        expected = audit_by_time[row["time"]["value"]]
        indexed_by_name = {definition["source_name"]: row["typed_field_sha256"][definition["field_id"]]
                           for definition in fields if definition["field_id"] in row["typed_field_sha256"]}
        on_demand = archive.get_snapshot(row["snapshot_id"])
        require(on_demand.status == "FOUND", f"on-demand snapshot read failed at {row['time']['value']}: {on_demand.status}")
        observed_by_name = {array.metadata.source_name: array.metadata.sha256_bytes
                            for array in on_demand.value["fields"].values()}
        require(len(expected) == EXPECTED_FIELDS, f"auditor field digest count is not {EXPECTED_FIELDS} at {row['time']['value']}")
        require(set(observed_by_name) == set(expected) == set(indexed_by_name),
                f"field names mismatch at native time {row['time']['value']}")
        field_results = [{"field": name, "index_sha256": indexed_by_name[name],
                          "queried_sha256": observed_by_name[name], "audit_sha256": expected[name],
                          "match": indexed_by_name[name] == observed_by_name[name] == expected[name]}
                         for name in sorted(expected)]
        comparison_doc["records"].append({"native_time_s": row["time"]["value"],
                                           "field_count": len(field_results), "fields": field_results})
        dump(evidence / "NUMERIC_COMPARISON.json", comparison_doc)
        require(indexed_by_name == observed_by_name == expected,
                f"typed field SHA256 mismatch at native time {row['time']['value']}")
        compared_fields += len(observed_by_name)
    require(compared_fields == 99, f"expected 99 typed field comparisons, got {compared_fields}")
    comparison_doc["status"] = "PASS"
    dump(evidence / "NUMERIC_COMPARISON.json", comparison_doc)

    qualification["stage"] = "NEGATIVE_AND_PORTABILITY_CHECKS"
    # Incomplete archive behavior is tested on a copy, never on the finalized index.
    incomplete_copy = evidence / "negative_incomplete"
    shutil.copytree(index_root, incomplete_copy)
    (incomplete_copy / "INCOMPLETE.json").write_text('{"archive_status":"INCOMPLETE"}\n', encoding="utf-8")
    incomplete = ExperimentalTrajectoryArchive.open("manifest.json", trusted_index_root=incomplete_copy)
    incomplete_status = incomplete.verify_integrity().status
    negative_doc["checks"].append({"check": "incomplete_manifest_copy", "status": incomplete_status})
    require(incomplete_status == "ARCHIVE_INCOMPLETE", "incomplete archive was accepted as complete")
    empty_payload_root = evidence / "empty_payload_root"
    empty_payload_root.mkdir()
    missing_payload = ExperimentalTrajectoryArchive.open("manifest.json", trusted_index_root=index_root,
        trusted_source_roots={"source": empty_payload_root})
    missing_status = missing_payload.verify_integrity().status
    negative_doc["checks"].append({"check": "payload_missing", "status": missing_status})
    require(missing_status == "MISSING_PAYLOAD", "missing source payload was not reported")

    moved = evidence / "relocated_archive_index"
    shutil.copytree(index_root, moved)
    metadata_only = ExperimentalTrajectoryArchive.open("manifest.json", trusted_index_root=moved)
    require(metadata_only.manifest["archive_id"] == manifest["archive_id"], "archive identity changed on relocation")
    relocated_missing_status = metadata_only.verify_integrity().status
    negative_doc["checks"].append({"check": "relocation_without_source_mapping", "status": relocated_missing_status,
                                   "archive_id_unchanged": True})
    require(relocated_missing_status == "MISSING_PAYLOAD", "relocated metadata should report unavailable external payloads")
    relocated_with_source = ExperimentalTrajectoryArchive.open("manifest.json", trusted_index_root=moved,
        trusted_source_roots={"source": source_root})
    require(relocated_with_source.manifest["archive_id"] == manifest["archive_id"] and relocated_with_source.verify_integrity().status == "PASS",
            "explicit source-root reconfiguration did not preserve identity and restore payload resolution")
    negative_doc["checks"].append({"check": "relocation_with_explicit_source_mapping", "status": "PASS",
                                   "archive_id_unchanged": True})

    corrupted_root = evidence / "corrupted_source_copy"
    for ref in refs:
        original, target = source_root / ref, corrupted_root / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
    vtu_ref = rows[0]["vtu_relative_ref"]
    with (corrupted_root / vtu_ref).open("ab") as stream: stream.write(b"\nGEODYN3C_TEST_CORRUPTION\n")
    corrupted = ExperimentalTrajectoryArchive.open("manifest.json", trusted_index_root=index_root,
        trusted_source_roots={"source": corrupted_root})
    corrupt_status = corrupted.verify_integrity().status
    negative_doc["checks"].append({"check": "altered_payload_copy", "status": corrupt_status})
    require(corrupt_status == "CORRUPT_PAYLOAD", "altered copied payload was not detected")

    # Indexer path/collision negatives use only copied PVD metadata and isolated destinations.
    negative_root = evidence / "negative_source"
    negative_root.mkdir()
    pvd_copy = negative_root / pvd_ref
    pvd_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_root / pvd_ref, pvd_copy)
    traversal = index_existing_aspect_series(trusted_source_root=negative_root, pvd_relative_ref="../" + pvd_ref,
        run_identity=claim, expected_source_inventory=declared, output_index_root=evidence / "negative_traversal")
    require(traversal.status == "FAILED" and (evidence / "negative_traversal" / "INCOMPLETE.json").is_file(),
            "path traversal was not rejected with incomplete evidence")
    negative_doc["checks"].append({"check": "path_traversal", "status": traversal.status})
    collision_dir = evidence / "negative_collision"
    collision_dir.mkdir()
    sentinel = collision_dir / "preserve.txt"
    sentinel.write_text("collision-test-preserve\n", encoding="utf-8")
    collision = index_existing_aspect_series(trusted_source_root=source_root, pvd_relative_ref=pvd_ref,
        run_identity=claim, expected_source_inventory=declared, output_index_root=collision_dir)
    require(collision.status == "FAILED" and sentinel.read_text(encoding="utf-8") == "collision-test-preserve\n",
            "destination collision overwrote existing content")
    negative_doc["checks"].append({"check": "destination_collision", "status": collision.status,
                                   "existing_sentinel_preserved": True})
    bad_manifest = evidence / "negative_manifest"
    shutil.copytree(index_root, bad_manifest)
    manifest_path = bad_manifest / "manifest.json"
    changed = json.loads(manifest_path.read_text(encoding="utf-8")); changed["classification"] = "OTHER"
    dump(manifest_path, changed)
    try:
        ExperimentalTrajectoryArchive.open("manifest.json", trusted_index_root=bad_manifest)
    except ArchiveError as exc:
        require(exc.status == "CORRUPT_MANIFEST", f"invalid manifest status was {exc.status}")
    else:
        raise ValueError("modified sealed manifest was accepted")
    negative_doc["checks"].append({"check": "invalid_sealed_manifest", "status": "CORRUPT_MANIFEST"})

    # External-symlink rejection is mandatory on FAIR; inability to create it blocks qualification.
    symlink_root = evidence / "negative_symlink_source"
    symlink_root.mkdir()
    symlink_pvd = symlink_root / pvd_ref
    symlink_pvd.parent.mkdir(parents=True, exist_ok=True)
    import xml.etree.ElementTree as ET
    shutil.copyfile(source_root / pvd_ref, symlink_pvd)
    collection = ET.parse(symlink_pvd).getroot().find("Collection")
    dataset = None if collection is None else collection.find("DataSet")
    require(dataset is not None, "source PVD lacks a first DataSet")
    source_locator = dataset.attrib["file"]
    symlink_target = symlink_pvd.parent / source_locator
    symlink_target.parent.mkdir(parents=True, exist_ok=True)
    external_target = evidence / "external_target.vtu"
    shutil.copyfile(source_root / rows[0]["vtu_relative_ref"], external_target)
    symlink_target.symlink_to(external_target)
    symlink_result = index_existing_aspect_series(trusted_source_root=symlink_root, pvd_relative_ref=pvd_ref,
        run_identity=claim, expected_source_inventory={}, output_index_root=evidence / "negative_symlink")
    require(symlink_result.status == "FAILED", "external symlink source was not rejected")
    negative_doc["checks"].append({"check": "external_symlink", "status": symlink_result.status,
                                   "message": symlink_result.message})
    negative_doc["status"] = "PASS"
    dump(evidence / "NEGATIVE_CHECKS.json", negative_doc)

    after = {ref: {"byte_length": (source_root / ref).stat().st_size, "sha256": sha256(source_root / ref)} for ref in sorted(refs)}
    dump(evidence / "originals_post_hashes.json", after)
    require(before == after, "original ASPECT source bytes changed during qualification")
    qualification.update({"status": "PASS", "stage": "COMPLETE", "commit": EXPECTED_COMMIT,
        "parent": EXPECTED_PARENT, "classification": manifest["classification"], "authority": manifest["authority"],
        "archive_id": manifest["archive_id"], "snapshot_count": len(rows), "times_native_seconds": times,
        "point_count": meshes[0]["point_count"], "cell_count": meshes[0]["cell_count"],
        "point_field_count": len(fields), "typed_field_sha256_comparisons": compared_fields,
        "manifest_sha256": sha256(index_root / "manifest.json"), "manifest_sidecar": (index_root / "manifest.sha256").read_text().strip(),
        "source_files_unchanged": True, "solver_executed": False, "restart": "NOT_AVAILABLE",
        "numeric_comparison": "NUMERIC_COMPARISON.json", "query_results": "QUERY_RESULTS.json",
        "negative_checks": "NEGATIVE_CHECKS.json", "integrity_report": "INTEGRITY_REPORT.json"})
    dump(evidence / "QUALIFICATION.json", qualification)
    print(json.dumps(qualification, sort_keys=True, indent=2))
except Exception as exc:
    qualification["failures"].append({"type": type(exc).__name__, "message": str(exc)})
    if comparison_doc["status"] == "RUNNING":
        comparison_doc["status"] = "FAIL"
        dump(evidence / "NUMERIC_COMPARISON.json", comparison_doc)
    if query_doc["status"] != "PENDING": dump(evidence / "QUERY_RESULTS.json", query_doc)
    if negative_doc["checks"]:
        negative_doc["status"] = "FAIL"
        dump(evidence / "NEGATIVE_CHECKS.json", negative_doc)
    dump(evidence / "QUALIFICATION.json", qualification)
    raise
PY

set +e
PYTHONPATH="$RUN_DIR/source-extract/src" python "$RUN_DIR/run_geodyn3c.py" \
  "$RUN_DIR/source-extract" "$SOURCE_ROOT" "$PVD_REF" \
  "$RUN_DIR/NUMERIC_AUDIT.json" "$RUN_DIR/SOURCE_INVENTORY.json" \
  "$RUN_DIR/RUN_IDENTITY_CLAIMS.json" "$RUN_DIR" 2>&1 | tee "$RUN_DIR/qualification.log"
qualification_rc=${PIPESTATUS[0]}
set -e
printf '%s\n' "$qualification_rc" > "$RUN_DIR/qualification.exitcode"
[[ $qualification_rc -eq 0 ]] || fail "archive/query qualification failed (exit $qualification_rc); preserve $RUN_DIR"

tracked_status_after=$(git -C "$REPO" status --porcelain --untracked-files=no)
[[ "$tracked_status_after" == "$tracked_status_before" ]] || fail 'tracked checkout state changed during read-only qualification'
git -C "$REPO" diff --quiet "$EXPECTED_COMMIT" -- || fail 'tracked checkout content changed during qualification'
git -C "$REPO" diff --cached --quiet || fail 'Git index changed during qualification'
printf 'PASS: GEODYN-3C existing-output qualification complete. Evidence: %s\n' "$RUN_DIR"

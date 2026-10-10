#!/usr/bin/env python3
"""Offline, read-only attestation of the SI1/BW1 DOF provenance chain.

The verifier uses only Python's standard library.  The existing BW1 module
implements the same transformations but imports NumPy/SciPy at module load;
those optional scientific packages are unavailable in the current Windows
interpreter, so this verifier independently checks the serialized artifacts
without installing or mutating an environment.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


TOOL_SCHEMA = "arcana_worldsim.r6.si1.f2b_d1a_attestation.v1"
NODE_COUNT = 64_442
TRIANGLE_COUNT = 128_880
DOF_COUNT = 128_884
RUNTIME_FIELDS = 51
BW1_ROOT_REL = Path("outputs/r6_si1_bandwidth_bw1")
F2AV_MANIFEST_SHA256 = "e59a1a31a450c7028b7a405cd6641454d9d67e082c7b62bd2132a0e452852854"
F2AV_RESULT_SHA256 = "02d7d8bd55dbe620f25772212be3db3f3a0c34ccf7e7c61b01af7994b5205fed"
F2AV_RUN_HEAD = "df670c8c4faaed641997f5c4bdb701e2ba0afc7d"
F2AV_EVIDENCE_GIT_COMMIT = "f318a217dfee2f99d51e834948bcf765d5d45c6b"
F2AV_MARKER = "BW1_F2AV_STOP_BEFORE_SOLVER"
F2A_MARKER = "BW1_F2A_STOP_BEFORE_SOLVER"
EXPECTED_BW1_MANIFEST_SHA256 = "63099f944c5379172f74831e08991c3dbe3315967de9bffbb639258448749732"
EXPECTED_BW1_REPORT_SHA256 = "944dfd039756d8b6cd9faf7ad1907fd034bac09cdbfd563f2385838b2eabc070"
EXPECTED_BW1_STAGING_CONTRACT_SHA256 = "3270c536eb7b54d3b8adf063e62dca695f4112d5d0ebcfeffc5f64d0e93b6ec2"
EXPECTED_PERMUTATION_SHA256 = "a0895fd99d3a356de276bd700af1564d951fcb9e4533e103e061aed15a8441e7"
EXPECTED_DERIVED_FEG_SHA256 = "18d78ec0c3382e0408f11f7b9826f5f22db7e6d921884c3375600fb2d447ffd1"
EXPECTED_DERIVED_RUNTIME_SHA256 = "a68c073011b2cb7782b760d5ff43b010610eaaddec731d5b39172c6b08294a31"
EXPECTED_ORIGINAL_FEG_SHA256 = "34b81c0df350d3b9a4c7df526c9171c89fe2d44d7e17b8662f5a92a9ee4c40b6"
EXPECTED_ORIGINAL_RUNTIME_SHA256 = "2dc83a759d4cdd4851ad57a37fc725841da24f0f2ca4312391283348703d3584"
EXPECTED_F2A_RECOVERY_ORIGINAL_MANIFEST_SHA256 = "605559ef61a652ae565d7240da33a089b5cda08cb1159052cb77fc2d58f4a1cd"
EXPECTED_F2A_RECOVERY_MANIFEST_SHA256 = "451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936"
EXPECTED_F2A_RUN_COMMIT = "e1694e18ddf1843c6709dd7e78f5de7bd6a281b4"

EXPECTED_STAGED_INPUTS = {
    "INPUT/ARCANA_PLATE_OUTLINES.dig": "6fdd149b2e5c8cc84992aa6a55b807867a27bc07bc0d78fdccf7b8bc4465525f",
    "INPUT/InputFiles.in": "d357d5a939a65fc9b8feee0cb0ca2fa0dba243a576249b5781323021ed751ab7",
    "INPUT/ListInput.in": "bb770c1ec132c4d6bee3ee2b12ce5d0dbbafd07147c435162acad2253606a49c",
    "INPUT/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat": EXPECTED_DERIVED_RUNTIME_SHA256,
    "INPUT/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg": EXPECTED_DERIVED_FEG_SHA256,
    "INPUT/SI1_ENGINEERING_REFERENCE.in": "c07834e17d9c6e21bad0d7cd81af20e8a670e0ae9ed481f999c881129ee4a89e",
    "INPUT/SI1_NO_VELOCITY.bcs": "e6fdc6c7d8050df65fb975e79147e981d164e527af948de64f8f7e825becb121",
    "INPUT/SI1_UNUSED_PLATE_PAIR.dig": "991316ececbe0042d8e2b6e6b06e819f9dd00f0bf65a3832fd4e3130cad88268",
}


class AttestationError(RuntimeError):
    """Fail-closed input or content validation failure."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _check_no_symlink_components(path: Path) -> None:
    absolute = Path(os.path.abspath(path))
    for component in (absolute, *absolute.parents):
        if component.is_symlink():
            raise AttestationError(f"symlink path component is not allowed: {component.name}")


def _overlaps(left: Path, right: Path) -> bool:
    """Return true if either path is equal to or nested under the other."""
    return left == right or left in right.parents or right in left.parents


def validate_output_location(repo_root: Path, evidence_root: Path, output_root: Path) -> Path:
    """Keep new attestation output in outputs/ and away from every input tree."""
    repo_root = Path(os.path.abspath(repo_root))
    evidence_root = Path(os.path.abspath(evidence_root))
    output_root = Path(os.path.abspath(output_root))
    bw1_root = repo_root / BW1_ROOT_REL
    outputs_root = repo_root / "outputs"
    protected_roots = (
        bw1_root,
        repo_root / "outputs/r6_si1_bandwidth_f2av_offline_recovery",
        repo_root / "external/ShellSet-v1.1.0",
        evidence_root,
    )
    if output_root.exists() or output_root.is_symlink():
        raise AttestationError("output directory must be new; refusing overwrite")
    _check_no_symlink_components(output_root.parent)
    if outputs_root not in output_root.parents:
        raise AttestationError("output must be a new descendant of the repository outputs/ directory")
    if any(_overlaps(output_root, protected) for protected in protected_roots):
        raise AttestationError("output path overlaps a protected BW1, recovery, ShellSet, or source-evidence path")
    if not output_root.parent.is_dir():
        raise AttestationError("output parent must already exist")
    return output_root


def _safe_member(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise AttestationError("manifest path is empty or not POSIX-relative")
    rel = PurePosixPath(relative)
    if rel.is_absolute() or any(part in ("", ".", "..") for part in rel.parts):
        raise AttestationError(f"unsafe manifest path: {relative}")
    lexical = root.joinpath(*rel.parts)
    _check_no_symlink_components(lexical)
    resolved_root = Path(os.path.abspath(root))
    resolved = Path(os.path.abspath(lexical))
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise AttestationError(f"manifest path escapes root or is not a regular file: {relative}")
    return resolved


def _tree_files_no_symlinks(root: Path) -> set[str]:
    root = Path(os.path.abspath(root))
    _check_no_symlink_components(root)
    if not root.is_dir():
        raise AttestationError("manifest root is not a directory")
    if root.is_symlink() or not root.is_dir():
        raise AttestationError("evidence root must be a regular directory, not a symlink")
    found: set[str] = set()
    for current, dirs, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in list(dirs):
            item = current_path / name
            if item.is_symlink():
                raise AttestationError(f"symlink directory in evidence tree: {item.relative_to(root)}")
        for name in files:
            item = current_path / name
            if item.is_symlink() or not item.is_file():
                raise AttestationError(f"non-regular object in evidence tree: {item.relative_to(root)}")
            found.add(item.relative_to(root).as_posix())
    return found


def verify_manifest(
    root: Path,
    manifest_name: str,
    *,
    expected_manifest_sha256: str | None,
    entries_key: str,
    size_key: str,
    sha_key: str,
    excluded_from_membership: set[str] | None = None,
    expected_paths: set[str] | None = None,
) -> dict[str, Any]:
    """Verify manifest seal, safe paths, file identities, and exact membership."""
    root = Path(os.path.abspath(root))
    manifest_path = _safe_member(root, manifest_name)
    manifest_sha = sha256_file(manifest_path)
    if expected_manifest_sha256 is not None and manifest_sha != expected_manifest_sha256:
        raise AttestationError(f"manifest SHA256 mismatch for {manifest_name}")
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AttestationError(f"manifest cannot be parsed: {manifest_name}") from exc
    entries = document.get(entries_key)
    if not isinstance(entries, list):
        raise AttestationError(f"manifest {manifest_name} has no {entries_key} array")
    seen: set[str] = set()
    verified: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise AttestationError(f"invalid entry in {manifest_name}")
        relative = entry.get("path")
        if not isinstance(relative, str) or relative in seen:
            raise AttestationError(f"duplicate or invalid manifest member in {manifest_name}")
        seen.add(relative)
        path = _safe_member(root, relative)
        digest = entry.get(sha_key)
        size = entry.get(size_key)
        if not _is_sha256(digest) or not isinstance(size, int) or isinstance(size, bool):
            raise AttestationError(f"invalid size/hash record for {relative}")
        actual_size = path.stat().st_size
        actual_sha = sha256_file(path)
        if actual_size != size or actual_sha != digest:
            raise AttestationError(f"manifest member identity mismatch: {relative}")
        verified.append({"path": relative, "size_bytes": size, "sha256": digest})
    if expected_paths is not None and seen != expected_paths:
        raise AttestationError(f"{manifest_name} member set differs from the required exact set")
    excluded = excluded_from_membership or set()
    actual = _tree_files_no_symlinks(root) - {manifest_name} - excluded
    if seen != actual:
        missing = sorted(seen - actual)
        extra = sorted(actual - seen)
        raise AttestationError(f"{manifest_name} membership mismatch; missing={missing[:3]} extra={extra[:3]}")
    return {
        "path": manifest_name,
        "sha256": manifest_sha,
        "member_count": len(verified),
        "members": sorted(verified, key=lambda item: item["path"]),
        "membership_verified": True,
    }


def _replace_token(line: bytes, token_index: int, replacement: str) -> bytes:
    spans = list(re.finditer(rb"\S+", line))
    if token_index < 0 or token_index >= len(spans):
        raise AttestationError("record does not contain the requested token")
    match = spans[token_index]
    return line[: match.start()] + replacement.encode("ascii") + line[match.end() :]


def validate_permutation(
    old_to_new: list[int], new_to_old: list[int], node_count: int, serialized_sha256: str
) -> dict[str, Any]:
    if len(old_to_new) != node_count or len(new_to_old) != node_count:
        raise AttestationError("permutation arrays do not have exactly node_count entries")
    expected = set(range(1, node_count + 1))
    if any(type(value) is not int for value in old_to_new + new_to_old):
        raise AttestationError("permutation entries must be JSON integers")
    if set(old_to_new) != expected or set(new_to_old) != expected:
        raise AttestationError("permutation arrays are not bijections over 1..node_count")
    for position, original_node in enumerate(new_to_old, start=1):
        if old_to_new[original_node - 1] != position:
            raise AttestationError("old_to_new[new_to_old[p]] inverse equation failed")
    for original_node, position in enumerate(old_to_new, start=1):
        if new_to_old[position - 1] != original_node:
            raise AttestationError("new_to_old[old_to_new[o]] inverse equation failed")
    serialized = b"".join(struct.pack("<q", value) for value in old_to_new + new_to_old)
    actual_digest = hashlib.sha256(serialized).hexdigest()
    if actual_digest != serialized_sha256:
        raise AttestationError("serialized little-endian int64 permutation digest mismatch")
    return {
        "node_count": node_count,
        "old_to_new_bijection": True,
        "new_to_old_bijection": True,
        "inverse_equations_checked": 2 * node_count,
        "serialized_maps_sha256_little_endian_int64": actual_digest,
    }


def _decode_ascii_lf(path: Path) -> list[bytes]:
    try:
        data = path.read_bytes()
        data.decode("ascii")
    except (OSError, UnicodeDecodeError) as exc:
        raise AttestationError(f"expected readable ASCII text: {path.name}") from exc
    if b"\r" in data:
        raise AttestationError(f"CR/CRLF is not admissible in canonical text input: {path.name}")
    if data and not data.endswith(b"\n"):
        raise AttestationError(f"text input lacks final LF: {path.name}")
    return data.splitlines(keepends=True)


def _parse_integer_token(token: bytes, label: str) -> int:
    try:
        text = token.decode("ascii")
        number = float(text)
    except (UnicodeDecodeError, ValueError) as exc:
        raise AttestationError(f"invalid numeric integer token for {label}") from exc
    if not math.isfinite(number) or not number.is_integer():
        raise AttestationError(f"non-integral or non-finite ID for {label}")
    return int(number)


def _feg_layout(path: Path, node_count: int, triangle_count: int) -> dict[str, Any]:
    lines = _decode_ascii_lf(path)
    if len(lines) != 2 + node_count + 1 + triangle_count + 1:
        raise AttestationError(f"FEG framing/line count mismatch: {path.name}")
    if not lines[0].rstrip(b"\n").startswith(b"ARCANA_R6_PRE_ORBDATA_RUNTIME_V1"):
        raise AttestationError(f"unexpected FEG title marker: {path.name}")
    header = lines[1].split()
    if len(header) < 5:
        raise AttestationError(f"malformed FEG count header: {path.name}")
    try:
        counts = [int(token) for token in header[:4]]
    except ValueError as exc:
        raise AttestationError(f"malformed FEG integer counts: {path.name}") from exc
    if counts != [node_count, node_count, 0, 100000] or header[4] != b"T":
        raise AttestationError(f"unexpected FEG node/fault/header counts: {path.name}")
    node_start = 2
    node_end = node_start + node_count
    if lines[node_end].split() != [str(triangle_count).encode("ascii")]:
        raise AttestationError(f"FEG triangle count record mismatch: {path.name}")
    tri_start = node_end + 1
    tri_end = tri_start + triangle_count
    if lines[tri_end].split() != [b"0"]:
        raise AttestationError(f"FEG fault count is not zero: {path.name}")
    nodes: dict[int, bytes] = {}
    for ordinal, line in enumerate(lines[node_start:node_end], start=1):
        fields = line.split()
        if len(fields) < 4:
            raise AttestationError(f"short FEG node record {ordinal}: {path.name}")
        node_id = _parse_integer_token(fields[0], f"{path.name} node ID")
        if not 1 <= node_id <= node_count or node_id in nodes:
            raise AttestationError(f"duplicate/out-of-range FEG node ID {node_id}: {path.name}")
        for coord in fields[1:3]:
            try:
                value = float(coord)
            except ValueError as exc:
                raise AttestationError(f"malformed FEG coordinate at node {node_id}") from exc
            if not math.isfinite(value):
                raise AttestationError(f"non-finite FEG coordinate at node {node_id}")
        nodes[node_id] = line
    if set(nodes) != set(range(1, node_count + 1)):
        raise AttestationError(f"FEG node ID set is incomplete: {path.name}")
    triangles: list[bytes] = []
    for ordinal, line in enumerate(lines[tri_start:tri_end], start=1):
        fields = line.split()
        if len(fields) < 4:
            raise AttestationError(f"short FEG triangle record {ordinal}: {path.name}")
        for token in fields[1:4]:
            node_id = _parse_integer_token(token, f"{path.name} triangle node reference")
            if not 1 <= node_id <= node_count:
                raise AttestationError(f"triangle {ordinal} references node outside 1..{node_count}")
        triangles.append(line)
    return {
        "lines": lines,
        "prefix": lines[:2],
        "nodes": nodes,
        "triangle_count_record": lines[node_end],
        "triangles": triangles,
        "fault_count_record": lines[tri_end],
    }


def verify_feg_pair(
    original_path: Path,
    derived_path: Path,
    old_to_new: list[int],
    new_to_old: list[int],
    node_count: int,
    triangle_count: int,
) -> dict[str, Any]:
    original = _feg_layout(original_path, node_count, triangle_count)
    derived = _feg_layout(derived_path, node_count, triangle_count)
    if original["prefix"] != derived["prefix"]:
        raise AttestationError("original/derived FEG headers differ")
    if (original["triangle_count_record"], original["fault_count_record"]) != (
        derived["triangle_count_record"], derived["fault_count_record"]
    ):
        raise AttestationError("FEG triangle/fault framing changed")
    for position, original_id in enumerate(new_to_old, start=1):
        source_line = original["nodes"][original_id]
        actual_line = derived["nodes"][position]
        expected_line = _replace_token(source_line, 0, str(position))
        if actual_line != expected_line:
            raise AttestationError(f"FEG nodal row/coordinate/field mismatch at derived node {position}")
        source_fields, actual_fields = source_line.split(), actual_line.split()
        if source_fields[1:3] != actual_fields[1:3]:
            raise AttestationError(f"FEG coordinate token mismatch at derived node {position}")
        if tuple(float(x) for x in source_fields[1:3]) != tuple(float(x) for x in actual_fields[1:3]):
            raise AttestationError(f"numeric FEG coordinate mismatch at derived node {position}")
    restored_triangles: list[bytes] = []
    for ordinal, (source_line, actual_line) in enumerate(
        zip(original["triangles"], derived["triangles"], strict=True), start=1
    ):
        source_ids = [_parse_integer_token(x, "source triangle node") for x in source_line.split()[1:4]]
        replacements = {idx + 1: str(old_to_new[node_id - 1]) for idx, node_id in enumerate(source_ids)}
        expected_line = source_line
        for idx, replacement in sorted(replacements.items(), reverse=True):
            expected_line = _replace_token(expected_line, idx, replacement)
        if actual_line != expected_line:
            raise AttestationError(f"FEG triangle connectivity/order/orientation mismatch at element {ordinal}")
        restored = actual_line
        derived_ids = [_parse_integer_token(x, "derived triangle node") for x in actual_line.split()[1:4]]
        for idx, new_id in sorted(enumerate(derived_ids, start=1), reverse=True):
            restored = _replace_token(restored, idx, str(new_to_old[new_id - 1]))
        restored_triangles.append(restored)
    restored_nodes: dict[int, bytes] = {}
    for position, original_id in enumerate(new_to_old, start=1):
        restored_nodes[original_id] = _replace_token(derived["nodes"][position], 0, str(original_id))
    if restored_nodes != original["nodes"] or restored_triangles != original["triangles"]:
        raise AttestationError("inverse FEG reconstruction differs from original records")
    return {
        "node_records_checked": node_count,
        "coordinate_token_pairs_checked": node_count * 2,
        "triangle_records_checked": triangle_count,
        "triangle_vertex_references_checked": triangle_count * 3,
        "fault_elements": 0,
        "triangle_order_and_local_orientation_preserved": True,
        "exact_text_inverse_reconstruction": True,
    }


def _parse_runtime(path: Path, node_count: int) -> tuple[bytes, dict[int, bytes], dict[str, int], int]:
    lines = _decode_ascii_lf(path)
    if len(lines) != node_count + 1:
        raise AttestationError(f"runtime line count mismatch: {path.name}")
    header = lines[0]
    header_fields = header.split()
    if len(header_fields) != 3 or header_fields[2] != str(node_count).encode("ascii"):
        raise AttestationError(f"runtime header/schema/node count mismatch: {path.name}")
    records: dict[int, bytes] = {}
    branch_counts: dict[str, int] = {}
    mixed_count = 0
    for ordinal, line in enumerate(lines[1:], start=1):
        fields = line.split()
        if len(fields) != RUNTIME_FIELDS:
            raise AttestationError(f"runtime record {ordinal} field count differs from {RUNTIME_FIELDS}")
        node_id = _parse_integer_token(fields[0], "runtime node ID")
        if not 1 <= node_id <= node_count or node_id in records:
            raise AttestationError(f"runtime node ID duplicate or out of range: {node_id}")
        numeric: list[float] = []
        for field in fields:
            try:
                value = float(field)
            except ValueError as exc:
                raise AttestationError(f"malformed runtime numeric field at record {ordinal}") from exc
            if not math.isfinite(value):
                raise AttestationError(f"non-finite runtime value at record {ordinal}")
            numeric.append(value)
        branch = str(int(numeric[8] + 0.5))
        branch_counts[branch] = branch_counts.get(branch, 0) + 1
        if int(numeric[5] + 0.5) == 1:
            mixed_count += 1
        records[node_id] = line
    if set(records) != set(range(1, node_count + 1)):
        raise AttestationError("runtime node ID set is incomplete")
    return header, records, branch_counts, mixed_count


def verify_runtime_pair(
    original_path: Path,
    derived_path: Path,
    new_to_old: list[int],
    node_count: int,
    *,
    expected_branch_counts: dict[str, int] | None = None,
    expected_mixed_count: int | None = None,
) -> dict[str, Any]:
    old_header, old_records, old_branches, old_mixed = _parse_runtime(original_path, node_count)
    new_header, new_records, new_branches, new_mixed = _parse_runtime(derived_path, node_count)
    if old_header != new_header:
        raise AttestationError("original and derived runtime package headers differ")
    for position, original_id in enumerate(new_to_old, start=1):
        source = old_records[original_id]
        derived = new_records[position]
        expected = _replace_token(source, 0, str(position))
        if derived != expected:
            raise AttestationError(f"runtime record {position} is not an exact field-preserving remap")
        if source.split()[1:] != derived.split()[1:]:
            raise AttestationError(f"runtime payload fields changed at derived node {position}")
    restored: dict[int, bytes] = {}
    for position, original_id in enumerate(new_to_old, start=1):
        restored[original_id] = _replace_token(new_records[position], 0, str(original_id))
    if restored != old_records:
        raise AttestationError("inverse runtime reconstruction differs from original rows")
    if old_branches != new_branches or old_mixed != new_mixed:
        raise AttestationError("runtime branch/support summaries changed under node remapping")
    expected_branches = expected_branch_counts or {"1": 14_258, "2": 108, "3": 50_076}
    required_mixed_count = 2_697 if expected_mixed_count is None else expected_mixed_count
    if new_branches != expected_branches or new_mixed != required_mixed_count:
        raise AttestationError("runtime branch/support counts disagree with D1 expected report values")
    return {
        "record_count": node_count,
        "fields_per_record_including_node_id": RUNTIME_FIELDS,
        "runtime_payload_fields_checked": node_count * (RUNTIME_FIELDS - 1),
        "branch_code_counts": dict(sorted(new_branches.items())),
        "mixed_physical_support_count": new_mixed,
        "exact_text_inverse_reconstruction": True,
    }


def dof_node_slot(q: int, new_to_old: list[int]) -> tuple[int, int, int]:
    if type(q) is not int or not 1 <= q <= 2 * len(new_to_old):
        raise AttestationError("raw DOF index outside 1..2*N")
    position = (q + 1) // 2
    component_slot = 1 if q % 2 else 2
    return position, component_slot, new_to_old[position - 1]


def _git_value(repo_root: Path, *args: str) -> str:
    env = os.environ.copy()
    env.pop("GIT_OBJECT_DIRECTORY", None)
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args], check=True, capture_output=True, text=True, env=env
    )
    return result.stdout.strip()


def _verify_f2av_run(evidence_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    result_path = evidence_root / "BW1_F2AV_RESULT.json"
    if sha256_file(result_path) != F2AV_RESULT_SHA256:
        raise AttestationError("original F2A-V result SHA256 mismatch")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("decision") != "BLOCKED_F2AV_QUALIFICATION":
        raise AttestationError("historical F2A-V verdict has changed")
    if result.get("failure") != "F2AVError: invalid saturation indicator":
        raise AttestationError("historical F2A-V recorded failure has changed")
    repository = result.get("repository", {})
    if repository.get("branch") != "r6/si1-bandwidth-f2av" or repository.get("head") != F2AV_RUN_HEAD:
        raise AttestationError("historical F2A-V execution identity mismatch")
    if result.get("compile_only") is not False or result.get("solver_executed") is not False or result.get("factorization_executed") is not False:
        raise AttestationError("historical F2A-V result does not prove the required pre-Solver scope")
    runtime = result.get("runtime", {})
    expected_command = ["mpiexec", "-n", "2", "./ShellSet.exe", "-Iter", "1", "-InOpt", "List", "-Dir", "RUN_OUTPUT"]
    if runtime.get("command") != expected_command or runtime.get("returncode") != 75:
        raise AttestationError("historical F2A-V command or intentional stop code mismatch")
    manifest_members = {item["path"]: item for item in manifest["members"]}
    log_rel = "logs/f2av_mpi_combined.log"
    if log_rel not in manifest_members or runtime.get("log_sha256") != manifest_members[log_rel]["sha256"]:
        raise AttestationError("F2A-V MPI log identity is not bound to the evidence manifest")
    log_path = _safe_member(evidence_root, log_rel)
    log = log_path.read_text(encoding="utf-8", errors="strict")
    for marker in ("ERROR STOP 75", F2AV_MARKER, F2A_MARKER):
        if log.count(marker) != 1:
            raise AttestationError(f"historical log marker count is not exactly one: {marker}")
    if log.count("BW1_F2A_STOP_BEFORE_SOLVER") != 1 or log.count(F2AV_MARKER) != 1:
        raise AttestationError("historical log lacks unique pre-Solver stops")
    provenance = result.get("provenance", {}).get("f2a_recovery", {})
    if provenance.get("original_manifest_sha256") != EXPECTED_F2A_RECOVERY_ORIGINAL_MANIFEST_SHA256:
        raise AttestationError("embedded F2A original manifest identity mismatch")
    if provenance.get("manifest_sha256") != EXPECTED_F2A_RECOVERY_MANIFEST_SHA256:
        raise AttestationError("embedded F2A recovery manifest identity mismatch")
    if provenance.get("original_run_source_commit") != EXPECTED_F2A_RUN_COMMIT:
        raise AttestationError("embedded historical F2A source commit mismatch")
    staged = result.get("staged_input_hashes_before")
    if not isinstance(staged, dict) or set(staged) != set(EXPECTED_STAGED_INPUTS):
        raise AttestationError("F2A-V run result staged-input set is not exactly the eight expected files")
    if staged != EXPECTED_STAGED_INPUTS:
        raise AttestationError("F2A-V staged-input hashes differ from the D1 identities")
    for staged_path, digest in staged.items():
        member = "run_f2av/" + staged_path
        if member not in manifest_members or manifest_members[member]["sha256"] != digest:
            raise AttestationError(f"staged-input hash is not bound by the original evidence manifest: {staged_path}")
    return {
        "result_sha256": F2AV_RESULT_SHA256,
        "historical_run_branch": repository["branch"],
        "historical_run_commit": repository["head"],
        "decision_preserved": result["decision"],
        "mpi_return_code": runtime["returncode"],
        "command": expected_command,
        "solver_executed": False,
        "factorization_executed": False,
        "unique_stop_markers_verified": True,
        "staged_input_count": len(staged),
        "f2a_source_provenance": {
            "original_manifest_sha256": provenance["original_manifest_sha256"],
            "recovery_manifest_sha256": provenance["manifest_sha256"],
            "original_run_commit": provenance["original_run_source_commit"],
            "note": "embedded provenance values are verified against the immutable F2A-V result; the referenced F2A bundle is not a member of the F2A-V evidence directory",
        },
    }


def _verify_staged_pair(evidence_root: Path, bw1_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    members = {item["path"]: item for item in manifest["members"]}
    pair = {
        "FEG": (
            "run_f2av/INPUT/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg",
            bw1_root / "derived/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg",
            EXPECTED_DERIVED_FEG_SHA256,
        ),
        "runtime": (
            "run_f2av/INPUT/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
            bw1_root / "derived/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
            EXPECTED_DERIVED_RUNTIME_SHA256,
        ),
    }
    checked = {}
    for label, (rel, derived, expected_sha) in pair.items():
        staged = _safe_member(evidence_root, rel)
        derived_hash = sha256_file(derived)
        if derived_hash != expected_sha or members.get(rel, {}).get("sha256") != expected_sha:
            raise AttestationError(f"{label} staged/derived manifest SHA mismatch")
        if staged.stat().st_size != derived.stat().st_size or staged.read_bytes() != derived.read_bytes():
            raise AttestationError(f"{label} staged file is not byte-identical to BW1 derived artifact")
        checked[label] = {"path": rel, "sha256": expected_sha, "byte_identical_to_bw1_derived": True}
    return checked


def _validate_original_authorities(repo_root: Path) -> dict[str, Any]:
    feg_path = repo_root / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
    feg_manifest_path = repo_root / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"
    runtime_path = repo_root / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
    runtime_manifest_path = repo_root / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json"
    for path in (feg_path, feg_manifest_path, runtime_path, runtime_manifest_path):
        _check_no_symlink_components(path)
        if not path.is_file():
            raise AttestationError(f"governed original authority is missing: {path.name}")
    fm = json.loads(feg_manifest_path.read_text(encoding="utf-8"))
    pm = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
    feg_sha = sha256_file(feg_path)
    runtime_sha = sha256_file(runtime_path)
    if feg_sha != EXPECTED_ORIGINAL_FEG_SHA256 or runtime_sha != EXPECTED_ORIGINAL_RUNTIME_SHA256:
        raise AttestationError("original FEG/runtime payload differs from the independently pinned BW1 input identities")
    head = _git_value(repo_root, "rev-parse", "HEAD")
    feg_manifest_blob = _git_blob(repo_root, head, feg_manifest_path.relative_to(repo_root).as_posix())
    runtime_manifest_blob = _git_blob(repo_root, head, runtime_manifest_path.relative_to(repo_root).as_posix())
    if feg_manifest_path.read_bytes() != feg_manifest_blob or runtime_manifest_path.read_bytes() != runtime_manifest_blob:
        raise AttestationError("original authority manifest differs from its Git HEAD blob")
    expected_feg = fm.get("production_feg", {}).get("raw_sha256")
    expected_runtime = pm.get("runtime_data_sha256")
    if feg_sha != expected_feg or not _is_sha256(expected_feg):
        raise AttestationError("original FEG differs from its governed manifest")
    if runtime_sha != expected_runtime or not _is_sha256(expected_runtime):
        raise AttestationError("original runtime package differs from its governed manifest")
    if pm.get("runtime_data_filename") != runtime_path.name:
        raise AttestationError("original runtime manifest names a different payload")
    return {
        "original_feg": {"path": feg_path.name, "sha256": feg_sha, "manifest_path": feg_manifest_path.name, "manifest_sha256": sha256_file(feg_manifest_path)},
        "original_runtime": {"path": runtime_path.name, "sha256": runtime_sha, "manifest_path": runtime_manifest_path.name, "manifest_sha256": sha256_file(runtime_manifest_path)},
    }


def validate_bw1_source_authority_links(authorities: dict[str, Any], source_input_hashes: Any) -> None:
    """Bind original payload and manifest identities to the pinned BW1 report."""
    expected = {
        "feg_sha256": authorities["original_feg"]["sha256"],
        "runtime_package_sha256": authorities["original_runtime"]["sha256"],
        "feg_manifest_sha256": authorities["original_feg"]["manifest_sha256"],
        "runtime_manifest_sha256": authorities["original_runtime"]["manifest_sha256"],
    }
    if not isinstance(source_input_hashes, dict) or source_input_hashes != expected:
        raise AttestationError("original authority hashes do not match the independently sealed BW1 report")


def _write_dof_csv(path: Path, new_to_old: list[int]) -> int:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["raw_dof_index", "reordered_node_id", "component_slot", "original_node_id"])
        for q in range(1, 2 * len(new_to_old) + 1):
            position, slot, original = dof_node_slot(q, new_to_old)
            writer.writerow([q, position, slot, original])
    return 2 * len(new_to_old)


def _write_census_mapping(source: Path, output: Path, new_to_old: list[int]) -> dict[str, Any]:
    expected_header = ["i", "j", "aij", "aji", "abs_delta", "abs_delta_saturated", "relative_delta", "row_scaled_discrepancy", "structure"]
    seen: set[tuple[int, int]] = set()
    rows = 0
    with source.open("r", encoding="utf-8-sig", newline="") as inp, output.open("w", encoding="utf-8", newline="") as out:
        reader = csv.reader(inp)
        if next(reader, None) != expected_header:
            raise AttestationError("original F2A-V census header mismatch")
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["source_row", "i_raw_dof", "i_reordered_node", "i_component_slot", "i_original_node", "j_raw_dof", "j_reordered_node", "j_component_slot", "j_original_node"])
        for source_row, row in enumerate(reader, start=2):
            if len(row) != len(expected_header):
                raise AttestationError(f"original census row {source_row} has wrong column count")
            try:
                i_raw, j_raw = int(row[0]), int(row[1])
            except ValueError as exc:
                raise AttestationError(f"original census row {source_row} has noninteger raw indices") from exc
            if not (1 <= i_raw < j_raw <= DOF_COUNT):
                raise AttestationError(f"original census row {source_row} raw indices are outside the proven DOF domain")
            pair = (i_raw, j_raw)
            if pair in seen:
                raise AttestationError(f"duplicate original census DOF pair {pair}")
            seen.add(pair)
            im = dof_node_slot(i_raw, new_to_old)
            jm = dof_node_slot(j_raw, new_to_old)
            writer.writerow([source_row, i_raw, *im, j_raw, *jm])
            rows += 1
    if rows != 10:
        raise AttestationError(f"original F2A-V census row count changed: expected 10, found {rows}")
    return {"source_rows": rows, "unique_pairs": len(seen), "source_sha256": sha256_file(source), "mapping_rows": rows, "original_census_modified": False}


def _artifact_manifest(output: Path) -> dict[str, Any]:
    artifacts = []
    for path in sorted((item for item in output.rglob("*") if item.is_file()), key=lambda item: item.relative_to(output).as_posix()):
        if path.name == "D1A_ARTIFACT_MANIFEST.json":
            continue
        artifacts.append({"path": path.relative_to(output).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    document = {"schema": "arcana_worldsim.r6.si1.f2b_d1a_manifest.v1", "membership": "all regular files except this manifest", "artifacts": artifacts}
    path = output / "D1A_ARTIFACT_MANIFEST.json"
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return {"path": path.name, "sha256": sha256_file(path), "artifact_count": len(artifacts), "artifacts": artifacts}


def attest(repo_root: Path, evidence_root: Path, output_root: Path) -> dict[str, Any]:
    # Keep paths lexical/absolute instead of calling Path.resolve(): on the
    # managed Windows runner, resolving a directory can be denied even when
    # ordinary file reads are permitted. Symlink components are still
    # rejected below before any input is opened.
    repo_root = Path(os.path.abspath(repo_root))
    evidence_root = Path(os.path.abspath(evidence_root))
    bw1_root = repo_root / BW1_ROOT_REL
    _check_no_symlink_components(evidence_root)
    _check_no_symlink_components(repo_root)
    if not repo_root.is_dir():
        raise AttestationError("repository root is not a directory")
    if not evidence_root.is_dir() or evidence_root == repo_root or evidence_root in repo_root.parents:
        raise AttestationError("F2A-V evidence root must be a distinct external directory")
    if output_root == repo_root or output_root in repo_root.parents:
        raise AttestationError("output cannot contain or replace the repository root")
    output_root = validate_output_location(repo_root, evidence_root, output_root)

    bw1_manifest = verify_manifest(
        bw1_root,
        "manifests/BW1_INPUT_MANIFEST.json",
        expected_manifest_sha256=EXPECTED_BW1_MANIFEST_SHA256,
        entries_key="files",
        size_key="size_bytes",
        sha_key="sha256",
        excluded_from_membership={
            "reports/BW1_REPORT.json",
            "reports/BW1_REPORT.md",
            "fair_staging/BW1_FAIR_PREFLIGHT_CONTRACT.md",
        },
        expected_paths={
            "derived/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg",
            "derived/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
            "fair_staging/INPUT/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg",
            "fair_staging/INPUT/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
            "permutation/BW1_NODE_PERMUTATION_V1.json",
        },
    )
    report_path = bw1_root / "reports/BW1_REPORT.json"
    staging_contract_path = bw1_root / "fair_staging/BW1_FAIR_PREFLIGHT_CONTRACT.md"
    if sha256_file(report_path) != EXPECTED_BW1_REPORT_SHA256:
        raise AttestationError("BW1 report SHA256 mismatch")
    if sha256_file(staging_contract_path) != EXPECTED_BW1_STAGING_CONTRACT_SHA256:
        raise AttestationError("BW1 staging contract SHA256 mismatch")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("decision") != "BLOCKED_BW1" or report.get("artifacts", {}).get("manifest_sha256") != EXPECTED_BW1_MANIFEST_SHA256:
        raise AttestationError("BW1 report decision or manifest link changed")

    authorities = _validate_original_authorities(repo_root)
    validate_bw1_source_authority_links(authorities, report.get("source", {}).get("input_hashes"))
    permutation_path = bw1_root / "permutation/BW1_NODE_PERMUTATION_V1.json"
    permutation_doc = json.loads(permutation_path.read_text(encoding="utf-8"))
    if permutation_doc.get("schema") != "R6_SI1_BW1_NODE_PERMUTATION_V1" or permutation_doc.get("node_count") != NODE_COUNT:
        raise AttestationError("unexpected permutation schema or node count")
    if permutation_doc.get("orientation") != "new_to_old maps each reordered 1-based position to original 1-based node ID; old_to_new is its inverse":
        raise AttestationError("permutation orientation metadata is not the expected 1-based contract")
    if permutation_doc.get("input_feg_sha256") != authorities["original_feg"]["sha256"] or permutation_doc.get("input_runtime_package_sha256") != authorities["original_runtime"]["sha256"]:
        raise AttestationError("permutation provenance does not name the verified original FEG/runtime")
    old_to_new = permutation_doc.get("old_to_new")
    new_to_old = permutation_doc.get("new_to_old")
    if not isinstance(old_to_new, list) or not isinstance(new_to_old, list):
        raise AttestationError("permutation map arrays are missing")
    permutation_check = validate_permutation(
        old_to_new, new_to_old, NODE_COUNT, permutation_doc.get("serialized_maps_sha256_little_endian_int64", "")
    )

    f2av_manifest = verify_manifest(
        evidence_root,
        "BW1_F2AV_ARTIFACT_MANIFEST.json",
        expected_manifest_sha256=F2AV_MANIFEST_SHA256,
        entries_key="artifacts",
        size_key="bytes",
        sha_key="sha256",
        expected_paths=None,
    )
    run_link = _verify_f2av_run(evidence_root, f2av_manifest)
    staged = _verify_staged_pair(evidence_root, bw1_root, f2av_manifest)

    derived_feg = bw1_root / "derived/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
    original_feg = repo_root / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
    feg_check = verify_feg_pair(original_feg, derived_feg, old_to_new, new_to_old, NODE_COUNT, TRIANGLE_COUNT)
    original_runtime = repo_root / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
    derived_runtime = bw1_root / "derived/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
    runtime_check = verify_runtime_pair(original_runtime, derived_runtime, new_to_old, NODE_COUNT)

    manifest_members = {item["path"]: item for item in f2av_manifest["members"]}
    census_rel = "run_f2av/BW1_F2AV_ASYMMETRY_CENSUS.csv"
    if census_rel not in manifest_members:
        raise AttestationError("raw F2A-V census is not included in the original evidence manifest")
    census_path = _safe_member(evidence_root, census_rel)
    current_head = _git_value(repo_root, "rev-parse", "HEAD")
    current_branch = _git_value(repo_root, "branch", "--show-current")
    historical_shellset_blob = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{F2AV_RUN_HEAD}:external/ShellSet-v1.1.0/src/MOD_Shells.f90"],
        check=True,
        capture_output=True,
        env={k: v for k, v in os.environ.items() if k not in {"GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"}},
    ).stdout
    shellset_source_path = repo_root / "external/ShellSet-v1.1.0/src/MOD_Shells.f90"
    if b"iry = 2 * nodeI" not in historical_shellset_blob or b"irx = iry - 1" not in historical_shellset_blob:
        raise AttestationError("historical ShellSet source does not establish odd/even component slot ordering")
    historical_f2av_blob = _git_blob(repo_root, F2AV_RUN_HEAD, "scripts/r6_si1_bandwidth_f2av_fair_diagnostics.py")
    required_f2av_source = (
        b'scan_anchor="DO f2a_j=1,nRank"',
        b"f2av_asym_i(f2av_asym_n)=f2a_i; f2av_asym_j(f2av_asym_n)=f2a_j",
    )
    if any(marker not in historical_f2av_blob for marker in required_f2av_source):
        raise AttestationError("historical F2A-V source does not bind census i/j to raw matrix row/column indices")
    f2av_source_path = repo_root / "scripts/r6_si1_bandwidth_f2av_fair_diagnostics.py"
    f2av_source_hash = sha256_file(f2av_source_path)
    if not shellset_source_path.is_file():
        raise AttestationError("current ShellSet source reference is missing")
    _check_no_symlink_components(shellset_source_path)

    staging_dir = Path(tempfile.mkdtemp(prefix=".d1a-attest-", dir=output_root.parent))
    try:
        dof_rows = _write_dof_csv(staging_dir / "RAW_DOF_NODE_COMPONENT_MAP.csv", new_to_old)
        census_check = _write_census_mapping(census_path, staging_dir / "F2AV_CENSUS_INDEX_MAP.csv", new_to_old)
        result: dict[str, Any] = {
            "schema": TOOL_SCHEMA,
            "decision": "DOF_MAPPING_PARTIAL",
            "scope": "offline exact-content attestation of node permutation, FEG/runtime reordering, F2A-V staged input linkage, and raw DOF to node/component-slot mapping",
            "repository": {"branch": current_branch, "head": current_head},
            "historical_execution": run_link,
            "input_identity": {
                "bw1_manifest": {"path": "outputs/r6_si1_bandwidth_bw1/manifests/BW1_INPUT_MANIFEST.json", "sha256": bw1_manifest["sha256"], "members_verified": bw1_manifest["member_count"]},
                "bw1_report": {"path": "outputs/r6_si1_bandwidth_bw1/reports/BW1_REPORT.json", "sha256": EXPECTED_BW1_REPORT_SHA256},
                "bw1_staging_contract": {"path": "outputs/r6_si1_bandwidth_bw1/fair_staging/BW1_FAIR_PREFLIGHT_CONTRACT.md", "sha256": EXPECTED_BW1_STAGING_CONTRACT_SHA256},
                "f2av_original_evidence_manifest": {"path": "BW1_F2AV_ARTIFACT_MANIFEST.json", "sha256": f2av_manifest["sha256"], "members_verified": f2av_manifest["member_count"]},
                "governed_original_authorities": authorities,
                "permutation": {"path": "outputs/r6_si1_bandwidth_bw1/permutation/BW1_NODE_PERMUTATION_V1.json", "sha256": EXPECTED_PERMUTATION_SHA256, **permutation_check},
                "derived_feg": {"path": "outputs/r6_si1_bandwidth_bw1/derived/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg", "sha256": EXPECTED_DERIVED_FEG_SHA256},
                "derived_runtime": {"path": "outputs/r6_si1_bandwidth_bw1/derived/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat", "sha256": EXPECTED_DERIVED_RUNTIME_SHA256},
                "historical_component_source": {"path": "external/ShellSet-v1.1.0/src/MOD_Shells.f90", "commit": F2AV_RUN_HEAD, "sha256_at_run_commit": hashlib.sha256(historical_shellset_blob).hexdigest(), "current_worktree_sha256": sha256_file(shellset_source_path)},
                "f2av_instrumentation_source": {"path": "scripts/r6_si1_bandwidth_f2av_fair_diagnostics.py", "current_worktree_sha256": f2av_source_hash, "historical_run_file_sha256": hashlib.sha256(historical_f2av_blob).hexdigest(), "census_indices_bound_to_matrix_i_j": True},
            },
            "validation": {
                "permutation": permutation_check,
                "feg_transform": feg_check,
                "runtime_transform": runtime_check,
                "f2av_staged_feg_runtime": staged,
                "f2av_census": census_check,
                "raw_dof_map_rows": dof_rows,
                "raw_dof_formula": "p=(q+1)//2; component_slot=1 if q odd else 2; original_node_id=new_to_old[p-1]; q is 1-based and bounded by 1..128884",
                "source_component_order": "ShellSet historical assembly source assigns component slot 1 to x=2*node-1 and slot 2 to y=2*node",
            },
            "interpretation": {
                "node_permutation_mapping": "PASS",
                "raw_dof_component_slot_mapping": "PASS_SOURCE_ORDER_ONLY",
                "overall_mapping_status": "DOF_MAPPING_PARTIAL",
                "component_geographic_basis_mapping": "DOF_MAPPING_UNVERIFIED",
                "census_geographic_or_plate_attribution": "PROHIBITED",
                "unknowns": ["geographic meaning/orientation of ShellSet component slots at each spherical node", "any plate/geographic interpretation of census pairs"],
            },
            "preserved": {
                "original_f2av_decision": "BLOCKED_F2AV_QUALIFICATION",
                "bw1_decision": "BLOCKED_BW1",
                "solver_executed_by_this_attestor": False,
                "factorization_executed": False,
                "gauge_applied": False,
                "canonical_or_world_history_modified": False,
                "source_inputs_modified": False,
            },
            "output_artifacts": ["RAW_DOF_NODE_COMPONENT_MAP.csv", "F2AV_CENSUS_INDEX_MAP.csv", "D1A_RESULT.json", "D1A_REPORT.md", "D1A_ARTIFACT_MANIFEST.json"],
        }
        (staging_dir / "D1A_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        report_text = _render_report(result)
        (staging_dir / "D1A_REPORT.md").write_text(report_text, encoding="utf-8", newline="\n")
        manifest_summary = _artifact_manifest(staging_dir)
        os.replace(staging_dir, output_root)
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise
    return {"result": result, "manifest": manifest_summary, "output_root_label": output_root.name}


def _git_blob(repo_root: Path, commit: str, relative: str) -> bytes:
    env = os.environ.copy()
    env.pop("GIT_OBJECT_DIRECTORY", None)
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    return subprocess.run(["git", "-C", str(repo_root), "show", f"{commit}:{relative}"], check=True, capture_output=True, env=env).stdout


def _render_report(result: dict[str, Any]) -> str:
    validation = result["validation"]
    identity = result["input_identity"]
    return "\n".join(
        [
            "# F2B-D1A Offline DOF Provenance Attestation",
            "",
            f"Decision: `{result['decision']}`",
            "",
            f"Attested source checkout: `{result['repository']['head']}` on `{result['repository']['branch']}`.",
            f"Historical F2A-V execution: `{result['historical_execution']['historical_run_commit']}`, original decision `{result['historical_execution']['decision_preserved']}`, MPI stop `{result['historical_execution']['mpi_return_code']}` before Solver.",
            "",
            "## Exact verification",
            "",
            f"- Manifest membership verified: BW1 {identity['bw1_manifest']['members_verified']} members; F2A-V original evidence {identity['f2av_original_evidence_manifest']['members_verified']} members.",
            f"- Permutation: {validation['permutation']['node_count']:,} nodes; both bijections and {validation['permutation']['inverse_equations_checked']:,} inverse relations checked.",
            f"- FEG: {validation['feg_transform']['node_records_checked']:,} node rows, {validation['feg_transform']['triangle_records_checked']:,} triangle rows and {validation['feg_transform']['triangle_vertex_references_checked']:,} vertex references; exact text inverse reconstruction PASS.",
            f"- Runtime: {validation['runtime_transform']['record_count']:,} records, {validation['runtime_transform']['runtime_payload_fields_checked']:,} payload fields checked; exact text inverse reconstruction PASS.",
            f"- Staged FEG/runtime byte identity to BW1 derived files: {all(v['byte_identical_to_bw1_derived'] for v in validation['f2av_staged_feg_runtime'].values())}.",
            f"- Raw DOF mapping table rows: {validation['raw_dof_map_rows']:,}; census pairs mapped: {validation['f2av_census']['source_rows']}.",
            "",
            "## Interpretation boundary",
            "",
            "Node/permutation mapping is attested. Odd/even raw DOF component-slot ordering is supported by the historical ShellSet assembly source. Geographic basis, plate attribution and physical interpretation remain `DOF_MAPPING_UNVERIFIED` / `PROHIBITED`; this result is partial and does not change the original F2A-V blocked verdict.",
            "",
            "No Fair, MPI, Solver, factorization, gauge, assembly, simulation, or canonical/WORLD_HISTORY write was performed by this attestor. The original evidence was read-only.",
            "",
            "Artifact identities are in `D1A_ARTIFACT_MANIFEST.json`.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(os.path.abspath(__file__)).parents[1])
    parser.add_argument("--f2av-evidence-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = attest(args.repo_root, args.f2av_evidence_root, args.output_root)
    except (AttestationError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"BLOCKED_D1A: {exc}\n")
    print(json.dumps({"decision": result["result"]["decision"], "output_root": result["output_root_label"], "manifest_sha256": result["manifest"]["sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

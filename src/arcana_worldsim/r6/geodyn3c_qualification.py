"""Narrow helpers used by the GEODYN-3C read-only qualification launcher."""

from __future__ import annotations

import hashlib
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


_GIT_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_VTK_TYPES = {
    "Float32": "f4", "Float64": "f8",
    "Int8": "i1", "UInt8": "u1", "Int16": "i2", "UInt16": "u2",
    "Int32": "i4", "UInt32": "u4", "Int64": "i8", "UInt64": "u8",
}
_TIME_KEYS = ("time_s", "time_value", "time", "timestep")
_ASPECT_COMMIT = "30eb77ee5da186137d436dbad35c6cb3cab64b69"
_R1_REPOSITORY_COMMIT = "1fd5e8d8f21e28876da9ef89423755615efc6162"
_R1_ADAPTER_COMMIT = "1fd5e8d8f21e28876da9ef89423755615efc6162"


class QualificationInputError(ValueError):
    """Malformed or inconsistent external qualification input."""


@dataclass(frozen=True)
class AuditPointField:
    name: str
    vtk_type: str
    components: int
    tuples: int
    sha256_bytes: str


@dataclass(frozen=True)
class AuditSnapshot:
    time_s: float
    mesh_sha256_numeric: str
    point_fields: tuple[AuditPointField, ...]


def validate_geodyn3c_run_claim(values: Mapping[str, Any]):
    """Validate preserved historical R1 claims without binding them to this launcher revision."""
    from .experimental_trajectory_archive import RunIdentityClaim

    if not isinstance(values, Mapping):
        raise QualificationInputError("RUN_CLAIMS_SCHEMA: run_identity must be an object")
    claim = RunIdentityClaim(**values)
    if claim.solver_name != "ASPECT" or claim.solver_version != "3.2.0-pre":
        raise QualificationInputError("run claim does not bind reported ASPECT 3.2.0-pre")
    if claim.solver_source_commit != _ASPECT_COMMIT:
        raise QualificationInputError("run claim does not preserve the exact ASPECT source commit")
    if claim.repository_commit != _R1_REPOSITORY_COMMIT:
        raise QualificationInputError("run claim does not preserve the GEODYN-2A-R1 repository commit")
    if claim.adapter_commit != _R1_ADAPTER_COMMIT:
        raise QualificationInputError("run claim does not preserve the GEODYN-2A-R1 adapter commit")
    required_algorithms = {
        "solver_source_commit_algorithm": "sha1",
        "repository_commit_algorithm": "sha1",
        "adapter_commit_algorithm": "sha1",
    }
    if any(claim.declared_provenance.get(key) != value for key, value in required_algorithms.items()):
        raise QualificationInputError("run claim lacks explicit unauthenticated SHA-1 algorithm declarations")
    if claim.solver_completed_time != 1.098612289 or claim.time_unit != "s":
        raise QualificationInputError("run claim time/completion does not match the preserved R1 record")
    return claim


def validate_source_inventory(document: Any):
    """Validate an externally preserved source inventory, rejecting empty/duplicate rows."""
    from .experimental_trajectory_archive import SourceDigest

    if not isinstance(document, Mapping) or not isinstance(document.get("files"), list):
        raise QualificationInputError("SOURCE_INVENTORY_SCHEMA: expected files list")
    rows = document["files"]
    if not rows:
        raise QualificationInputError("SOURCE_INVENTORY_SCHEMA: empty inventory is not evidence")
    result = {}
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"relative_ref", "byte_length", "sha256"}:
            raise QualificationInputError("SOURCE_INVENTORY_SCHEMA: each row requires exactly ref, byte_length, sha256")
        digest = SourceDigest(**row)
        if digest.relative_ref in result:
            raise QualificationInputError(f"SOURCE_INVENTORY_SCHEMA: duplicate ref {digest.relative_ref}")
        result[digest.relative_ref] = digest
    return result


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise QualificationInputError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def verify_git_candidate(
    repo: str | Path,
    *,
    branch_ref: str,
    expected_commit: str,
    expected_parent: str,
    remote: str = "origin",
) -> dict[str, str]:
    """Verify a remote ref and commit object without consulting/changing checkout HEAD."""
    root = Path(repo).resolve(strict=True)
    if not _GIT_SHA1.fullmatch(expected_commit) or not _GIT_SHA1.fullmatch(expected_parent):
        raise QualificationInputError("candidate commit and parent must be exact lowercase Git SHA-1 IDs")
    if not re.fullmatch(r"refs/heads/[A-Za-z0-9._/-]+", branch_ref) or ".." in branch_ref.split("/"):
        raise QualificationInputError("branch_ref must be a safe fully qualified heads ref")

    _git(root, "cat-file", "-e", f"{expected_commit}^{{commit}}")
    parent = _git(root, "rev-parse", f"{expected_commit}^")
    if parent != expected_parent:
        raise QualificationInputError(f"candidate parent mismatch: {parent}")

    remote_rows = _git(root, "ls-remote", "--exit-code", remote, branch_ref).splitlines()
    matches = [line.split("\t", 1) for line in remote_rows if "\t" in line]
    matches = [(sha, ref) for sha, ref in matches if ref == branch_ref]
    if len(matches) != 1:
        raise QualificationInputError(f"remote ref unavailable or ambiguous: {remote}/{branch_ref}")
    remote_commit = matches[0][0]
    if remote_commit != expected_commit:
        raise QualificationInputError(f"remote ref points to {remote_commit}, expected {expected_commit}")

    # These are observations only. A different branch or HEAD is permitted and preserved.
    return {
        "remote": remote,
        "remote_ref": branch_ref,
        "remote_commit": remote_commit,
        "qualified_commit": expected_commit,
        "qualified_parent": parent,
        "checkout_branch": _git(root, "branch", "--show-current"),
        "checkout_head": _git(root, "rev-parse", "HEAD"),
    }


def parse_geodyn2c_audit(document: Any) -> tuple[AuditSnapshot, ...]:
    """Parse the explicit GEODYN-2C snapshots[].point_fields[] schema only."""
    if not isinstance(document, Mapping) or not isinstance(document.get("snapshots"), list):
        raise QualificationInputError("NUMERIC_AUDIT_SCHEMA: expected top-level snapshots list")
    rows = document["snapshots"]
    if not rows:
        raise QualificationInputError("NUMERIC_AUDIT_SCHEMA: snapshots must not be empty")

    parsed: list[AuditSnapshot] = []
    previous_time = float("-inf")
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: snapshots[{index}] must be an object")
        time_keys = [key for key in _TIME_KEYS if key in row]
        if len(time_keys) != 1:
            raise QualificationInputError(
                f"NUMERIC_AUDIT_SCHEMA: snapshots[{index}] must have exactly one supported native time key"
            )
        time_value = row[time_keys[0]]
        if isinstance(time_value, Mapping):
            if "value" not in time_value or set(time_value) - {"value", "unit", "units"}:
                raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: invalid time object at snapshot {index}")
            time_value = time_value["value"]
        if isinstance(time_value, bool) or not isinstance(time_value, (int, float)):
            raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: nonnumeric time at snapshot {index}")
        time_s = float(time_value)
        if not math.isfinite(time_s) or time_s <= previous_time:
            raise QualificationInputError("NUMERIC_AUDIT_SCHEMA: snapshot times must be finite and strictly increasing")
        previous_time = time_s

        mesh_digest = row.get("mesh_sha256_numeric")
        if not isinstance(mesh_digest, str) or not _SHA256.fullmatch(mesh_digest):
            raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: invalid mesh_sha256_numeric at snapshot {index}")
        field_rows = row.get("point_fields")
        if not isinstance(field_rows, list) or not field_rows:
            raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: snapshots[{index}].point_fields must be a nonempty list")
        fields: list[AuditPointField] = []
        names: set[str] = set()
        for field_index, item in enumerate(field_rows):
            if not isinstance(item, Mapping):
                raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: point_fields[{field_index}] must be an object")
            expected_keys = {"name", "type", "components", "tuples", "sha256_bytes"}
            missing_keys = expected_keys - set(item)
            if missing_keys:
                raise QualificationInputError(
                    f"NUMERIC_AUDIT_SCHEMA: missing point_fields[{field_index}] keys {sorted(missing_keys)}"
                )
            if set(item) - expected_keys:
                raise QualificationInputError(
                    f"NUMERIC_AUDIT_SCHEMA: unsupported point_fields[{field_index}] record shape"
                )
            name, vtk_type = item.get("name"), item.get("type")
            components, tuples, digest = item.get("components"), item.get("tuples"), item.get("sha256_bytes")
            if not isinstance(name, str) or not name or name in names:
                raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: missing or duplicate field name at snapshot {index}")
            if vtk_type not in _VTK_TYPES:
                raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: unsupported numeric type {vtk_type!r}")
            if isinstance(components, bool) or not isinstance(components, int) or components < 1:
                raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: invalid components for {name}")
            if isinstance(tuples, bool) or not isinstance(tuples, int) or tuples < 0:
                raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: invalid tuples for {name}")
            if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
                raise QualificationInputError(f"NUMERIC_AUDIT_SCHEMA: invalid sha256_bytes for {name}")
            names.add(name)
            fields.append(AuditPointField(name, vtk_type, components, tuples, digest))
        parsed.append(AuditSnapshot(time_s, mesh_digest, tuple(fields)))
    return tuple(parsed)


def compare_numeric_audit(
    audit_snapshots: Sequence[AuditSnapshot],
    observed_snapshots: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare mesh and typed field hashes/metadata at exact native times."""
    by_time: dict[float, Mapping[str, Any]] = {}
    observed_times: list[float] = []
    for observed in observed_snapshots:
        time_s = observed.get("time_s")
        if not isinstance(time_s, (int, float)) or isinstance(time_s, bool):
            raise QualificationInputError("observed snapshot lacks numeric time_s")
        time_s = float(time_s)
        if time_s in by_time:
            raise QualificationInputError(f"duplicate observed time {time_s}")
        by_time[time_s] = observed
        observed_times.append(time_s)
    audit_times = [snapshot.time_s for snapshot in audit_snapshots]
    if observed_times != audit_times:
        raise QualificationInputError("audit and observed native snapshot times differ")

    field_comparisons = 0
    mesh_comparisons = 0
    records = []
    for audit in audit_snapshots:
        observed = by_time[audit.time_s]
        if observed.get("mesh_sha256_numeric") != audit.mesh_sha256_numeric:
            raise QualificationInputError(f"numeric mesh SHA256 mismatch at {audit.time_s}")
        observed_fields = observed.get("point_fields")
        if not isinstance(observed_fields, Sequence) or isinstance(observed_fields, (str, bytes)):
            raise QualificationInputError(f"observed point_fields invalid at {audit.time_s}")
        actual_by_name = {}
        for field in observed_fields:
            name = field.get("name")
            if not isinstance(name, str) or name in actual_by_name:
                raise QualificationInputError(f"duplicate/invalid observed field at {audit.time_s}")
            actual_by_name[name] = field
        if set(actual_by_name) != {field.name for field in audit.point_fields}:
            raise QualificationInputError(f"point-field names differ at {audit.time_s}")
        field_rows = []
        for expected in audit.point_fields:
            actual = actual_by_name[expected.name]
            checks = {
                "type": actual.get("type") == expected.vtk_type,
                "components": actual.get("components") == expected.components,
                "tuples": actual.get("tuples") == expected.tuples,
                "sha256_bytes": actual.get("sha256_bytes") == expected.sha256_bytes,
            }
            if not all(checks.values()):
                raise QualificationInputError(f"numeric field mismatch at {audit.time_s}: {expected.name} {checks}")
            field_comparisons += 1
            field_rows.append({"name": expected.name, "checks": checks, "sha256_bytes": expected.sha256_bytes})
        mesh_comparisons += 1
        records.append({"time_s": audit.time_s, "mesh_sha256_numeric": audit.mesh_sha256_numeric,
                        "point_fields": field_rows})
    return {"status": "PASS", "mesh_comparisons": mesh_comparisons,
            "field_comparisons": field_comparisons, "records": records}


def _mesh_dtype(vtk_type: str, byte_order: str):
    import numpy as np

    if vtk_type not in _VTK_TYPES or byte_order not in ("LittleEndian", "BigEndian"):
        raise QualificationInputError(f"unsupported mesh dtype/byte order: {vtk_type}/{byte_order}")
    base = _VTK_TYPES[vtk_type]
    endian = "|" if base.endswith("1") else ("<" if byte_order == "LittleEndian" else ">")
    return np.dtype(endian + base)


def mesh_sha256_numeric(coordinates, connectivity, offsets, types) -> str:
    """Hash four NumPy arrays in the independent auditor's documented order."""
    import numpy as np

    digest = hashlib.sha256()
    arrays = (coordinates, connectivity, offsets, types)
    for array in arrays:
        value = np.asarray(array)
        if value.dtype.kind not in "fiu" or value.dtype.hasobject:
            raise QualificationInputError("mesh hash accepts only typed numeric NumPy arrays")
        value = np.ascontiguousarray(value)
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def mesh_sha256_from_vtk(mesh, vtu_path: str | Path) -> str:
    """Recreate numeric mesh hash from adapter values and original VTK dtype metadata."""
    import numpy as np

    path = Path(vtu_path)
    root = ET.parse(path).getroot()
    if root.tag != "VTKFile" or root.attrib.get("type") != "UnstructuredGrid":
        raise QualificationInputError("unsupported VTK mesh source")
    pieces = root.findall(".//Piece")
    if len(pieces) != 1:
        raise QualificationInputError("numeric mesh audit requires exactly one VTK Piece")
    piece = pieces[0]
    points_arrays = piece.findall("./Points/DataArray")
    cells_arrays = piece.findall("./Cells/DataArray")
    if len(points_arrays) != 1:
        raise QualificationInputError("expected exactly one VTK point coordinate array")
    by_name = {item.attrib.get("Name"): item for item in cells_arrays}
    if len(cells_arrays) != 3 or set(by_name) != {"connectivity", "offsets", "types"}:
        raise QualificationInputError("VTK cell arrays must be connectivity, offsets, and types")
    byte_order = root.attrib.get("byte_order", "LittleEndian")
    coordinate_type = points_arrays[0].attrib.get("type")
    dtypes = [coordinate_type] + [by_name[name].attrib.get("type")
                                  for name in ("connectivity", "offsets", "types")]
    values = (mesh.coordinates, mesh.connectivity, mesh.offsets, mesh.cell_types)
    arrays = [np.asarray(data, dtype=_mesh_dtype(vtk_type, byte_order))
              for data, vtk_type in zip(values, dtypes, strict=True)]
    if (arrays[0].size != mesh.point_count * 3 or arrays[1].size != len(mesh.connectivity)
            or arrays[2].size != mesh.cell_count or arrays[3].size != mesh.cell_count):
        raise QualificationInputError("mesh array cardinality disagrees with parsed geometry")
    return mesh_sha256_numeric(*arrays)

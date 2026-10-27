"""Read-only index for experimental solver trajectories (GEODYN-3B MVP).

The index stores metadata and references to source files. It never copies VTU
payloads and never creates canonical ``DomainStateEnvelope`` records.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .identity import canonical_bytes, content_hash
from .adapters.aspect_snapshot_reader import (
    CLASSIFICATION, AspectSnapshotSeries, ReaderLimits, SnapshotFormatError,
)


SCHEMA = "ARCANA_GEODYN_EXPERIMENTAL_TRAJECTORY_V1"
AUTHORITY = "OPERATOR_REPORTED_UNAUTHENTICATED"
_HEX = re.compile(r"^[0-9a-f]{64}$")
_ID_TOKEN = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")


class ArchiveError(ValueError):
    """Fail-closed archive error with a stable machine-readable status."""

    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class SourceDigest:
    relative_ref: str
    byte_length: int
    sha256: str

    def __post_init__(self) -> None:
        _validate_relative_ref(self.relative_ref)
        if self.byte_length < 0 or not _HEX.fullmatch(self.sha256):
            raise ValueError("source digest requires nonnegative length and lowercase SHA256")


@dataclass(frozen=True)
class RunIdentityClaim:
    """Caller-supplied provenance claims; validation does not authenticate them."""

    attempt_id: str
    solver_name: str
    solver_version: str
    solver_source_commit: str
    repository_commit: str
    adapter_commit: str
    configuration_sha256: str
    input_identities: tuple[str, ...]
    time_basis_id: str
    time_unit: str
    time_unit_source: str
    solver_completed_time: float
    availability_checked_at_utc: str
    declared_provenance: Mapping[str, str]
    build_identity: str = "UNKNOWN"

    def __post_init__(self) -> None:
        for name in ("attempt_id", "solver_name", "solver_version", "time_basis_id", "time_unit"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be declared")
        if not _ID_TOKEN.fullmatch(self.attempt_id):
            raise ValueError("attempt_id must be a stable safe token")
        for name in ("solver_source_commit", "repository_commit", "adapter_commit", "configuration_sha256"):
            if not _HEX.fullmatch(getattr(self, name)):
                raise ValueError(f"{name} must be a lowercase SHA256/commit identity")
        if not self.input_identities or any(not _HEX.fullmatch(v) for v in self.input_identities):
            raise ValueError("input_identities must contain lowercase SHA256 identities")
        if not self.time_unit_source.strip() or not math.isfinite(self.solver_completed_time):
            raise ValueError("time unit source and finite solver completion time are required")
        try:
            stamp = datetime.fromisoformat(self.availability_checked_at_utc.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("availability_checked_at_utc must be an ISO-8601 timestamp") from exc
        if stamp.tzinfo is None:
            raise ValueError("availability_checked_at_utc must include a UTC offset")
        if stamp.utcoffset() != timedelta(0):
            raise ValueError("availability_checked_at_utc must be UTC")
        if any(not _ID_TOKEN.fullmatch(k) or not isinstance(v, str) or not v.strip()
               for k, v in self.declared_provenance.items()):
            raise ValueError("declared_provenance must contain safe keys and non-empty values")
        if any(re.match(r"^(?:[A-Za-z]:[\\/]|\\\\|/)", value)
               for value in self.declared_provenance.values()):
            raise ValueError("declared provenance values must not contain absolute machine paths")


@dataclass(frozen=True)
class IndexBuildResult:
    status: str
    archive_id: str | None
    index_ref: str | None
    message: str | None = None


@dataclass(frozen=True)
class ArchiveResult:
    status: str
    value: Any = None
    message: str | None = None
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class IntegrityReport:
    status: str
    checked_files: int
    missing_files: tuple[str, ...]
    corrupt_files: tuple[str, ...]
    message: str | None = None


@dataclass(frozen=True)
class NativeTime:
    value: float
    unit: str
    time_basis_id: str

    def __post_init__(self) -> None:
        if not math.isfinite(self.value) or not self.unit or not self.time_basis_id:
            raise ValueError("NativeTime requires finite value, unit and time basis")


def _id(prefix: str, payload: Any) -> str:
    return f"{prefix}_{content_hash(payload)}"


def _validate_relative_ref(reference: str) -> PurePosixPath:
    if not isinstance(reference, str) or not reference or "\\" in reference or "\x00" in reference:
        raise ArchiveError("UNSAFE_PATH", "references must be non-empty POSIX relative paths")
    if any(part in ("", ".", "..") for part in reference.split("/")):
        raise ArchiveError("UNSAFE_PATH", f"unsafe relative reference: {reference!r}")
    path = PurePosixPath(reference)
    if path.is_absolute():
        raise ArchiveError("UNSAFE_PATH", f"unsafe relative reference: {reference!r}")
    if re.match(r"^[A-Za-z]:", reference):
        raise ArchiveError("UNSAFE_PATH", "drive-qualified paths are not allowed")
    return path


def _is_reparse(path: Path) -> bool:
    info = path.lstat()
    attrs = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(info.st_mode) or bool(attrs & reparse_flag)


def _trusted_root(path: Path) -> Path:
    supplied = Path(path)
    try:
        if _is_reparse(supplied):
            raise ArchiveError("UNSAFE_PATH", "trusted root cannot itself be a symlink/reparse point")
        resolved = supplied.resolve(strict=True)
    except OSError as exc:
        raise ArchiveError("MISSING_PAYLOAD", f"trusted root unavailable: {supplied}") from exc
    if not resolved.is_dir():
        raise ArchiveError("UNSAFE_PATH", "trusted root must be a directory")
    return resolved


def _safe_directory(root: Path, reference: str) -> Path:
    rel = _validate_relative_ref(reference)
    current = root
    for part in rel.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            try:
                if _is_reparse(current):
                    raise ArchiveError("UNSAFE_PATH", f"symlink/reparse path component rejected: {reference}")
            except OSError as exc:
                raise ArchiveError("UNSAFE_PATH", f"cannot validate directory path: {reference}") from exc
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise ArchiveError("MISSING_PAYLOAD", f"directory missing or escapes trusted root: {reference}") from exc
    if not resolved.is_dir():
        raise ArchiveError("UNSAFE_PATH", "archive path is not a directory")
    return resolved


def _safe_join(root: Path, reference: str, *, must_exist: bool = True) -> Path:
    rel = _validate_relative_ref(reference)
    current = root
    for part in rel.parts:
        current = current / part
        try:
            if current.exists() or current.is_symlink():
                if _is_reparse(current):
                    raise ArchiveError("UNSAFE_PATH", f"symlink/reparse path component rejected: {reference}")
        except OSError as exc:
            raise ArchiveError("UNSAFE_PATH", f"cannot validate path component: {reference}") from exc
    try:
        resolved = current.resolve(strict=must_exist)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        status = "MISSING_PAYLOAD" if must_exist else "UNSAFE_PATH"
        raise ArchiveError(status, f"reference is missing or escapes trusted root: {reference}") from exc
    if must_exist and not resolved.is_file():
        raise ArchiveError("MISSING_PAYLOAD", f"referenced source is not a file: {reference}")
    return resolved


def _stream_digest(path: Path, max_bytes: int, relative_ref: str) -> SourceDigest:
    before = path.stat()
    size = before.st_size
    if size < 0 or size > max_bytes or not stat.S_ISREG(before.st_mode):
        raise ArchiveError("UNSUPPORTED_FORMAT", f"source file type/size outside reader limit: {path.name}")
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            total += len(block)
            digest.update(block)
        after_fd = os.fstat(stream.fileno())
    after = path.stat()
    if total != size or after.st_size != size or after_fd.st_size != size:
        raise ArchiveError("CORRUPT_PAYLOAD", f"source changed while hashing: {path.name}")
    return SourceDigest(relative_ref, size, digest.hexdigest())


def _read_xml(path: Path) -> ET.Element:
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ArchiveError("UNSUPPORTED_FORMAT", "DTD/entity declarations are not supported")
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ArchiveError("UNSUPPORTED_FORMAT", f"invalid XML in {path.name}") from exc


def _pvd_time_tokens(path: Path) -> tuple[str, ...]:
    root = _read_xml(path)
    collection = root.find("Collection")
    datasets = [] if collection is None else collection.findall("DataSet")
    tokens = tuple(item.attrib.get("timestep", "") for item in datasets)
    if not tokens:
        raise ArchiveError("UNSUPPORTED_FORMAT", "PVD contains no DataSet time tokens")
    return tokens


def _run_identity_payload(claim: RunIdentityClaim) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "solver": {"name": claim.solver_name, "version": claim.solver_version,
                   "source_commit": claim.solver_source_commit, "build_identity": claim.build_identity},
        "source": {"repository_commit": claim.repository_commit, "adapter_commit": claim.adapter_commit},
        "configuration_sha256": claim.configuration_sha256,
        "input_identities": list(claim.input_identities),
        "classification": CLASSIFICATION,
        "time_basis_id": claim.time_basis_id,
        "time_unit": claim.time_unit,
    }


def _archive_identity_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    payloads = [
        {k: record[k] for k in ("payload_id", "byte_length", "sha256", "role")}
        for record in manifest["payload_catalog"]
    ]
    normalized_snapshots = [
        {key: value for key, value in record.items()
         if key not in ("source_root_alias", "vtu_relative_ref")}
        for record in manifest["snapshots"]
    ]
    source_content = sorted((item["byte_length"], item["sha256"]) for item in manifest["source_files"])
    return {
        "schema": manifest["schema"], "run_id": manifest["run"]["run_id"],
        "attempt_id": manifest["run"]["attempt_id"],
        "snapshots": normalized_snapshots, "source_file_content": source_content,
        "meshes": manifest["mesh_catalog"],
        "fields": manifest["field_catalog"], "payloads": payloads,
        "series_observations": manifest["series_observations"],
        "completion": manifest["completion"], "time": manifest["time"],
    }


def _write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()


def index_existing_aspect_series(
    *, trusted_source_root: Path,
    pvd_relative_ref: str,
    run_identity: RunIdentityClaim,
    expected_source_inventory: Mapping[str, SourceDigest],
    output_index_root: Path,
    limits: ReaderLimits | None = None,
) -> IndexBuildResult:
    """Index an existing ASPECT series without copying source payloads.

    ``output_index_root`` must be a new directory whose parent already exists.
    On failure the directory and its incomplete marker are retained.
    """
    output = Path(output_index_root)
    if not output.parent.is_dir():
        return IndexBuildResult("FAILED", None, None, "output parent must already exist")
    try:
        output.mkdir(exist_ok=False)
    except FileExistsError:
        return IndexBuildResult("FAILED", None, None, "output index destination already exists")
    except OSError as exc:
        return IndexBuildResult("FAILED", None, None, f"could not create output index directory: {exc}")
    incomplete_path = output / "INCOMPLETE.json"
    partial: dict[str, Any] = {"schema": SCHEMA, "archive_status": "INCOMPLETE", "errors": []}
    try:
        _write_new(incomplete_path, canonical_bytes(partial))
        source_root = _trusted_root(Path(trusted_source_root))
        pvd_ref = pvd_relative_ref
        pvd_path = _safe_join(source_root, pvd_ref)
        if Path(pvd_ref).suffix.lower() != ".pvd":
            raise ArchiveError("UNSUPPORTED_FORMAT", "pvd_relative_ref must end with .pvd")
        series_root = pvd_path.parent
        try:
            series_root_rel = series_root.relative_to(source_root).as_posix()
        except ValueError as exc:
            raise ArchiveError("UNSAFE_PATH", "PVD parent escapes the trusted source root") from exc
        series = AspectSnapshotSeries(
            pvd_path, run_id="geodyn3run_" + content_hash(_run_identity_payload(run_identity)),
            time_unit=run_identity.time_unit, time_unit_source=run_identity.time_unit_source,
            mpi_rank_count=1, limits=limits, solver_completed_time=run_identity.solver_completed_time,
            experiment_provenance={"repository_commit": run_identity.repository_commit,
                                   "adapter_commit": run_identity.adapter_commit},
        )
        audit = series.audit()
        tokens = _pvd_time_tokens(pvd_path)
        if len(tokens) != len(audit.snapshots):
            raise ArchiveError("CORRUPT_MANIFEST", "PVD time token count changed during indexing")
        for token, row in zip(tokens, audit.snapshots):
            try:
                if not math.isfinite(float(token)) or float(token) != row.time_value:
                    raise ValueError
            except ValueError as exc:
                raise ArchiveError("INVALID_TIME_ORDER", "PVD source time token is invalid/inconsistent") from exc

        source_paths: dict[str, Path] = {pvd_ref: pvd_path}
        for row in audit.snapshots:
            source_paths[f"{series_root_rel}/{row.source_file}" if series_root_rel != "." else row.source_file] = _safe_join(
                source_root, f"{series_root_rel}/{row.source_file}" if series_root_rel != "." else row.source_file
            )
            for local_ref in row.file_sha256:
                full_ref = f"{series_root_rel}/{local_ref}" if series_root_rel != "." else local_ref
                source_paths[full_ref] = _safe_join(source_root, full_ref)
        actual: dict[str, SourceDigest] = {}
        for reference, path in sorted(source_paths.items()):
            measured = _stream_digest(path, (limits or ReaderLimits()).max_file_bytes, reference)
            actual[reference] = SourceDigest(reference, measured.byte_length, measured.sha256)
        expected: dict[str, SourceDigest] = {}
        for key, value in expected_source_inventory.items():
            _validate_relative_ref(key)
            expected[key] = value if isinstance(value, SourceDigest) else SourceDigest(**value)
            if expected[key].relative_ref != key:
                raise ArchiveError("CORRUPT_PAYLOAD", "inventory key and reference disagree")
        if set(actual) != set(expected):
            raise ArchiveError("CORRUPT_PAYLOAD", "source inventory membership differs from referenced files")
        for key in actual:
            if actual[key] != expected[key]:
                raise ArchiveError("CORRUPT_PAYLOAD", f"source file differs from expected inventory: {key}")
        if run_identity.solver_completed_time < audit.snapshots[-1].time_value:
            raise ArchiveError("INVALID_TIME_ORDER", "solver completion precedes last archived snapshot")

        fields: dict[str, dict[str, Any]] = {}
        meshes: dict[str, dict[str, Any]] = {}
        payloads: dict[tuple[str, int, str], dict[str, Any]] = {}
        snapshots: list[dict[str, Any]] = []
        pvd_token_by_ordinal = tokens
        for row in audit.snapshots:
            vtu_ref = f"{series_root_rel}/{row.source_file}" if series_root_rel != "." else row.source_file
            vtu_digest = actual[vtu_ref]
            source_xml = _read_xml(source_paths[vtu_ref])
            byte_order = source_xml.attrib.get("byte_order", "LittleEndian")
            if byte_order not in ("LittleEndian", "BigEndian"):
                raise ArchiveError("UNSUPPORTED_FORMAT", f"unsupported byte order: {byte_order}")
            mesh_id = _id("geodyn3mesh", {
                "reader_mesh_fingerprint": row.mesh_fingerprint,
                "coordinate_type": row.coordinate_vtk_type,
                "coordinate_sha256_typed": row.coordinate_sha256_bytes,
                "point_count": row.point_count, "cell_count": row.cell_count,
                "cell_type_counts": dict(row.cell_type_counts),
            })
            meshes.setdefault(mesh_id, {
                "mesh_id": mesh_id, "identity_algorithm": "aspect_reader_mesh_fingerprint_v1",
                "fingerprint": row.mesh_fingerprint, "point_count": row.point_count,
                "cell_count": row.cell_count, "cell_type_counts": dict(row.cell_type_counts),
                "coordinate_dtype": row.coordinate_vtk_type, "byte_order": byte_order,
                "coordinate_sha256_typed": row.coordinate_sha256_bytes,
                "bounds": [list(pair) for pair in row.coordinate_bounds],
                "association": "point_coordinates_and_cell_topology",
            })
            field_ids: list[str] = []
            typed_field_digests: dict[str, str] = {}
            for metadata in row.field_metadata:
                field_key = f"{metadata.association}:{metadata.name}"
                definition = {
                    "source_key": field_key, "source_name": metadata.source_name,
                    "association": metadata.association, "vtk_dtype": metadata.vtk_type,
                    "byte_order": byte_order, "components": metadata.components,
                    "tuple_count": metadata.tuples, "units": metadata.units or "UNKNOWN",
                    "semantic_provenance": "SOURCE_METADATA_ONLY",
                }
                field_id = _id("geodyn3field", definition)
                fields.setdefault(field_id, {"field_id": field_id, **definition})
                field_ids.append(field_id)
                typed_field_digests[field_id] = metadata.sha256_bytes
            payload_key = (vtu_digest.sha256, vtu_digest.byte_length, "VTU_SOURCE_FILE")
            payload_id = _id("geodyn3payload", {"sha256": vtu_digest.sha256,
                                                  "byte_length": vtu_digest.byte_length,
                                                  "role": "VTU_SOURCE_FILE"})
            payloads[payload_key] = {
                "payload_id": payload_id, "byte_length": vtu_digest.byte_length,
                "sha256": vtu_digest.sha256, "role": "VTU_SOURCE_FILE",
                "availability": {"state": "AVAILABLE_EXTERNAL", "checked_at_utc": run_identity.availability_checked_at_utc},
                "source_root_alias": "source", "relative_ref": vtu_ref,
            }
            time_value = row.time_value
            snapshot_id_payload = {
                "schema": SCHEMA, "run_id": "geodyn3run_" + content_hash(_run_identity_payload(run_identity)),
                "attempt_id": run_identity.attempt_id, "source_ordinal": row.ordinal,
                "original_time_token": pvd_token_by_ordinal[row.ordinal], "time_value": time_value,
                "time_unit": row.time_unit, "time_basis_id": run_identity.time_basis_id,
                "mesh_id": mesh_id, "field_ids": sorted(field_ids), "payload_id": payload_id,
            }
            snapshot_id = _id("geodyn3snapshot", snapshot_id_payload)
            snapshots.append({"snapshot_id": snapshot_id, "source_ordinal": row.ordinal,
                              "time": {"value": time_value, "source_token": pvd_token_by_ordinal[row.ordinal],
                                       "unit": row.time_unit, "time_basis_id": run_identity.time_basis_id},
                              "mesh_id": mesh_id, "field_ids": sorted(field_ids), "payload_id": payload_id,
                              "typed_field_sha256": typed_field_digests,
                              "source_root_alias": "source", "vtu_relative_ref": vtu_ref,
                              "source_file_sha256": vtu_digest.sha256,
                              "source_file_byte_length": vtu_digest.byte_length})
        run_payload = _run_identity_payload(run_identity)
        run_id = "geodyn3run_" + content_hash(run_payload)
        # Snapshot IDs were built from the same deterministic run ID above.
        payload_catalog = sorted(payloads.values(), key=lambda item: (item["sha256"], item["role"]))
        manifest: dict[str, Any] = {
            "schema": SCHEMA, "archive_status": "COMPLETE", "classification": CLASSIFICATION,
            "authority": AUTHORITY, "run": {"run_id": run_id, "attempt_id": run_identity.attempt_id,
                "identity_payload": run_payload,
                "solver": {"name": run_identity.solver_name, "version": run_identity.solver_version,
                           "source_commit": run_identity.solver_source_commit,
                           "build_identity": run_identity.build_identity},
                "source": {"repository_commit": run_identity.repository_commit,
                           "adapter_commit": run_identity.adapter_commit,
                           "provenance_claims": dict(run_identity.declared_provenance)}},
            "time": {"basis": "SOLVER_NATIVE", "basis_id": run_identity.time_basis_id,
                     "unit": run_identity.time_unit, "unit_source": run_identity.time_unit_source,
                     "solver_completed_time": run_identity.solver_completed_time,
                     "last_archived_snapshot_time": audit.snapshots[-1].time_value,
                     "coverage": "SNAPSHOT_SERIES", "unobserved_intervals": "NOT_INFERRED"},
            "completion": {"solver_status": "OPERATOR_REPORTED_NATURAL_COMPLETION",
                           "archive_status": "COMPLETE", "snapshot_count": len(snapshots)},
            "reader": {"implementation": "arcana_worldsim.r6.adapters.aspect_snapshot_reader",
                       "source_commit_claim": run_identity.adapter_commit},
            "source_roots": {"source": {"locator_kind": "CALLER_TRUSTED_ROOT"}},
            "source_pvd_ref": pvd_ref,
            "source_files": [
                {"relative_ref": d.relative_ref, "byte_length": d.byte_length, "sha256": d.sha256,
                 "availability": {"state": "AVAILABLE_EXTERNAL", "checked_at_utc": run_identity.availability_checked_at_utc}}
                for d in actual.values()
            ],
            "mesh_catalog": sorted(meshes.values(), key=lambda item: item["mesh_id"]),
            "field_catalog": sorted(fields.values(), key=lambda item: item["field_id"]),
            "snapshots": snapshots, "payload_catalog": payload_catalog,
            "series_observations": {
                "mesh_stable": audit.mesh_stable, "schema_stable": audit.schema_stable,
                "invariant_fields": list(audit.invariant_fields),
                "dynamic_fields": list(audit.dynamic_fields),
                "zero_valued_invariant_fields": list(audit.zero_valued_invariant_fields),
                "field_annotations": dict(audit.field_annotations),
                "numerically_duplicate_fields": [list(pair) for pair in audit.numerically_duplicate_fields],
                "time_gaps_native": list(audit.time_gaps),
                "final_snapshot_at_solver_completion": audit.final_snapshot_at_solver_completion,
                "comparison_authority": "MEASURED_BY_READER_NOT_PHYSICAL_SEMANTICS",
            },
            "capabilities": {"reconstruction": "NOT_CLAIMED", "restart": "NOT_AVAILABLE",
                             "interpolation": False, "remapping": False},
        }
        archive_id = _id("geodyn3archive", _archive_identity_payload(manifest))
        manifest["archive_id"] = archive_id
        manifest_bytes = canonical_bytes(manifest)
        seal = (hashlib.sha256(manifest_bytes).hexdigest() + "\n").encode("ascii")
        tmp_manifest = output / ".manifest.json.tmp"
        tmp_seal = output / ".manifest.sha256.tmp"
        _write_new(tmp_manifest, manifest_bytes)
        _write_new(tmp_seal, seal)
        os.replace(tmp_seal, output / "manifest.sha256")
        os.replace(tmp_manifest, output / "manifest.json")
        incomplete_path.unlink()
        return IndexBuildResult("COMPLETE", archive_id, "manifest.json")
    except (ArchiveError, SnapshotFormatError, OSError, ValueError, TypeError, KeyError) as exc:
        partial["errors"] = [{"status": getattr(exc, "status", "INDEX_BUILD_FAILED"),
                              "message": str(exc)}]
        try:
            incomplete_path.write_bytes(canonical_bytes(partial))
        except OSError:
            pass
        return IndexBuildResult("FAILED", None, "INCOMPLETE.json", str(exc))


class ExperimentalTrajectoryArchive:
    """Metadata index with explicit, on-demand reads from trusted source roots."""

    def __init__(self, root: Path, index_ref: str, manifest: dict[str, Any],
                 source_roots: Mapping[str, Path], incomplete: bool = False,
                 limits: ReaderLimits | None = None, manifest_seal: str | None = None,
                 trusted_index_root: Path | None = None):
        self.root = root
        self.trusted_index_root = trusted_index_root or root
        self.index_ref = index_ref
        self.manifest = manifest
        self.source_roots = {key: _trusted_root(Path(value)) for key, value in source_roots.items()}
        self.incomplete = incomplete
        self.limits = limits or ReaderLimits()
        self._manifest_seal = manifest_seal

    @classmethod
    def open(cls, index_ref: str, *, trusted_index_root: Path,
             trusted_source_roots: Mapping[str, Path] | None = None,
             limits: ReaderLimits | None = None) -> "ExperimentalTrajectoryArchive":
        root = _trusted_root(Path(trusted_index_root))
        rel = _validate_relative_ref(index_ref)
        if rel.name != "manifest.json":
            raise ArchiveError("UNSAFE_PATH", "index_ref must name manifest.json")
        parent_ref = rel.parent.as_posix()
        archive_dir = root if parent_ref == "." else _safe_directory(root, parent_ref)
        incomplete_path = archive_dir / "INCOMPLETE.json"
        incomplete = incomplete_path.exists() or incomplete_path.is_symlink()
        if incomplete:
            if _is_reparse(incomplete_path):
                raise ArchiveError("UNSAFE_PATH", "incomplete marker cannot be a symlink/reparse point")
        path = archive_dir / "manifest.json"
        if not path.exists() and incomplete:
            try:
                partial = json.loads(incomplete_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ArchiveError("CORRUPT_MANIFEST", "incomplete marker is unreadable") from exc
            if partial.get("archive_status") != "INCOMPLETE":
                raise ArchiveError("CORRUPT_MANIFEST", "invalid incomplete marker")
            return cls(archive_dir, index_ref, partial, {}, True, limits,
                       trusted_index_root=root)
        path = _safe_join(root, index_ref)
        try:
            manifest_bytes = path.read_bytes()
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArchiveError("CORRUPT_MANIFEST", "manifest cannot be read") from exc
        if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
            raise ArchiveError("UNSUPPORTED_FORMAT", "archive schema version is not supported")
        if incomplete:
            try:
                partial = json.loads((path.parent / "INCOMPLETE.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ArchiveError("CORRUPT_MANIFEST", "incomplete marker is unreadable") from exc
            if partial.get("archive_status") != "INCOMPLETE":
                raise ArchiveError("CORRUPT_MANIFEST", "invalid incomplete marker")
        elif not path.with_suffix(".sha256").is_file():
            raise ArchiveError("CORRUPT_MANIFEST", "manifest seal is missing")
        else:
            expected = path.with_suffix(".sha256").read_text(encoding="ascii").strip()
            if (not _HEX.fullmatch(expected) or hashlib.sha256(manifest_bytes).hexdigest() != expected
                    or canonical_bytes(manifest) != manifest_bytes):
                raise ArchiveError("CORRUPT_MANIFEST", "manifest seal mismatch")
            _validate_manifest(manifest)
        source_roots: dict[str, Path] = {}
        for alias, source_root in (trusted_source_roots or {}).items():
            try:
                source_roots[alias] = _trusted_root(Path(source_root))
            except ArchiveError as exc:
                if exc.status != "MISSING_PAYLOAD":
                    raise
        return cls(path.parent, index_ref, manifest, source_roots, incomplete, limits,
                   expected if not incomplete else None, root)

    def verify_integrity(self) -> IntegrityReport:
        if self.incomplete:
            return IntegrityReport("ARCHIVE_INCOMPLETE", 0, (), (), "archive was not finalized")
        try:
            index_root = self.trusted_index_root
            manifest_path = _safe_join(index_root, self.index_ref)
            manifest_bytes = manifest_path.read_bytes()
            seal_ref = Path(self.index_ref).with_suffix(".sha256").as_posix()
            seal_path = _safe_join(index_root, seal_ref)
            stored_seal = seal_path.read_text(encoding="ascii").strip()
            if (self._manifest_seal is None or stored_seal != self._manifest_seal
                    or hashlib.sha256(manifest_bytes).hexdigest() != self._manifest_seal
                    or canonical_bytes(self.manifest) != manifest_bytes):
                return IntegrityReport("CORRUPT_MANIFEST", 0, (), (), "sealed index changed after open")
            _validate_manifest(self.manifest)
        except (ArchiveError, OSError, ValueError, TypeError) as exc:
            return IntegrityReport("CORRUPT_MANIFEST", 0, (), (), str(exc))
        checked = 0
        missing: list[str] = []
        corrupt: list[str] = []
        for item in self.manifest["source_files"]:
            alias, ref = "source", item["relative_ref"]
            root = self.source_roots.get(alias)
            if root is None:
                missing.append(f"{alias}:{ref}")
                continue
            try:
                path = _safe_join(root, ref)
                actual = _stream_digest(path, self.limits.max_file_bytes, ref)
                checked += 1
                if actual.byte_length != item["byte_length"] or actual.sha256 != item["sha256"]:
                    corrupt.append(f"{alias}:{ref}")
            except ArchiveError as exc:
                if exc.status == "UNSAFE_PATH":
                    corrupt.append(f"{alias}:{ref}")
                else:
                    missing.append(f"{alias}:{ref}")
        status = "CORRUPT_PAYLOAD" if corrupt else "MISSING_PAYLOAD" if missing else "PASS"
        source_root = self.source_roots.get("source")
        if source_root is not None:
            try:
                pvd = _safe_join(source_root, self.manifest["source_pvd_ref"])
                tokens = _pvd_time_tokens(pvd)
                snapshots = self.manifest["snapshots"]
                if len(tokens) != len(snapshots):
                    return IntegrityReport("CORRUPT_MANIFEST", checked, (), (),
                                           "PVD snapshot count differs from index")
                for token, row in zip(tokens, snapshots):
                    if token != row["time"]["source_token"] or float(token) != row["time"]["value"]:
                        return IntegrityReport("CORRUPT_MANIFEST", checked, (), (),
                                               "PVD native time token differs from index")
            except (ArchiveError, ValueError, OSError) as exc:
                return IntegrityReport("CORRUPT_PAYLOAD", checked, (), (), str(exc))
        return IntegrityReport(status, checked, tuple(missing), tuple(corrupt))

    def get_run(self, run_id: str) -> ArchiveResult:
        if self.incomplete:
            return ArchiveResult("ARCHIVE_INCOMPLETE")
        if self.manifest["run"]["run_id"] != run_id:
            return ArchiveResult("MISSING_RUN")
        return ArchiveResult("FOUND", self.manifest["run"])

    def query_snapshots(self, run_id: str, *, start: NativeTime | None = None,
                        end: NativeTime | None = None) -> ArchiveResult:
        if self.incomplete:
            return ArchiveResult("ARCHIVE_INCOMPLETE")
        run = self.get_run(run_id)
        if run.status != "FOUND":
            return run
        expected_unit, basis = self.manifest["time"]["unit"], self.manifest["time"]["basis_id"]
        for bound in (start, end):
            if bound is not None and (bound.unit != expected_unit or bound.time_basis_id != basis):
                return ArchiveResult("INCOMPATIBLE_TIME_BASIS")
        low = -math.inf if start is None else start.value
        high = math.inf if end is None else end.value
        if low > high:
            return ArchiveResult("INVALID_TIME_ORDER")
        rows = [row for row in self.manifest["snapshots"]
                if low <= row["time"]["value"] <= high]
        rows.sort(key=lambda row: (row["time"]["value"], row["source_ordinal"]))
        return ArchiveResult("FOUND" if rows else "MISSING_SNAPSHOT", tuple(rows))

    def get_snapshot_at(self, run_id: str, time: NativeTime) -> ArchiveResult:
        result = self.query_snapshots(run_id, start=time, end=time)
        if result.status != "FOUND":
            return result
        rows = result.value
        if len(rows) > 1:
            return ArchiveResult("AMBIGUOUS", candidates=tuple(row["snapshot_id"] for row in rows))
        return ArchiveResult("FOUND", rows[0])

    def list_meshes(self) -> ArchiveResult:
        if self.incomplete:
            return ArchiveResult("ARCHIVE_INCOMPLETE")
        return ArchiveResult("FOUND", tuple(self.manifest["mesh_catalog"]))

    def get_mesh(self, mesh_id: str) -> ArchiveResult:
        if self.incomplete:
            return ArchiveResult("ARCHIVE_INCOMPLETE")
        mesh = next((item for item in self.manifest["mesh_catalog"] if item["mesh_id"] == mesh_id), None)
        return ArchiveResult("FOUND", mesh) if mesh is not None else ArchiveResult("MISSING_MESH")

    def list_fields(self, snapshot_id: str | None = None) -> ArchiveResult:
        if self.incomplete:
            return ArchiveResult("ARCHIVE_INCOMPLETE")
        if snapshot_id is None:
            return ArchiveResult("FOUND", tuple(self.manifest["field_catalog"]))
        snapshot = next((item for item in self.manifest["snapshots"] if item["snapshot_id"] == snapshot_id), None)
        if snapshot is None:
            return ArchiveResult("MISSING_SNAPSHOT")
        wanted = set(snapshot["field_ids"])
        return ArchiveResult("FOUND", tuple(field for field in self.manifest["field_catalog"]
                                               if field["field_id"] in wanted))

    def _series(self, root: Path) -> AspectSnapshotSeries:
        source = self.manifest["run"]["source"]
        return AspectSnapshotSeries(
            _safe_join(root, self.manifest["source_pvd_ref"]),
            run_id=self.manifest["run"]["run_id"],
            time_unit=self.manifest["time"]["unit"],
            time_unit_source=self.manifest["time"]["unit_source"], mpi_rank_count=1,
            limits=self.limits, solver_completed_time=self.manifest["time"]["solver_completed_time"],
            experiment_provenance={"repository_commit": source["repository_commit"],
                                   "adapter_commit": source["adapter_commit"]},
        )

    def get_snapshot(self, snapshot_id: str) -> ArchiveResult:
        """Read one snapshot numerically; the adapter materializes all its arrays."""
        if self.incomplete:
            return ArchiveResult("ARCHIVE_INCOMPLETE")
        row = next((item for item in self.manifest["snapshots"] if item["snapshot_id"] == snapshot_id), None)
        if row is None:
            return ArchiveResult("MISSING_SNAPSHOT")
        integrity = self.verify_integrity()
        if integrity.status != "PASS":
            message = integrity.message or ",".join(integrity.missing_files + integrity.corrupt_files)
            return ArchiveResult(integrity.status, message=message)
        root = self.source_roots.get(row["source_root_alias"])
        if root is None:
            return ArchiveResult("MISSING_PAYLOAD")
        try:
            snapshot = self._series(root).read_snapshot(row["source_ordinal"])
        except (ArchiveError, SnapshotFormatError, OSError, ValueError) as exc:
            return ArchiveResult("CORRUPT_PAYLOAD", message=str(exc))
        mesh_record = next((item for item in self.manifest["mesh_catalog"]
                            if item["mesh_id"] == row["mesh_id"]), None)
        if (snapshot.record.time_value != row["time"]["value"]
                or snapshot.record.mesh_fingerprint != (mesh_record or {}).get("fingerprint")):
            return ArchiveResult("CORRUPT_PAYLOAD", message="source snapshot time/mesh disagrees with index")
        for item_id in row["field_ids"]:
            definition = next(item for item in self.manifest["field_catalog"] if item["field_id"] == item_id)
            array = snapshot.fields.get(definition["source_key"])
            if array is None or array.metadata.sha256_bytes != row["typed_field_sha256"].get(item_id):
                return ArchiveResult("CORRUPT_PAYLOAD", message="typed field digest mismatch")
        source_digest = next((item for item in self.manifest["source_files"]
                              if item["relative_ref"] == row["vtu_relative_ref"]), None)
        if source_digest is None:
            return ArchiveResult("CORRUPT_MANIFEST", message="snapshot VTU reference is absent")
        try:
            measured = _stream_digest(_safe_join(root, row["vtu_relative_ref"]),
                                      self.limits.max_file_bytes, row["vtu_relative_ref"])
        except ArchiveError as exc:
            return ArchiveResult(exc.status, message=str(exc))
        if measured.sha256 != source_digest["sha256"] or measured.byte_length != source_digest["byte_length"]:
            return ArchiveResult("CORRUPT_PAYLOAD", message="VTU changed while reading snapshot")
        return ArchiveResult("FOUND", {"metadata": row, "mesh": snapshot.mesh, "fields": snapshot.fields})

    def get_field(self, snapshot_id: str, field_id: str) -> ArchiveResult:
        if self.incomplete:
            return ArchiveResult("ARCHIVE_INCOMPLETE")
        row = next((item for item in self.manifest["snapshots"] if item["snapshot_id"] == snapshot_id), None)
        if row is None:
            return ArchiveResult("MISSING_SNAPSHOT")
        field = next((item for item in self.manifest["field_catalog"] if item["field_id"] == field_id), None)
        if field is None or field_id not in row["field_ids"]:
            return ArchiveResult("MISSING_FIELD")
        snapshot_result = self.get_snapshot(snapshot_id)
        if snapshot_result.status != "FOUND":
            return snapshot_result
        array = snapshot_result.value["fields"].get(field["source_key"])
        if array is None:
            return ArchiveResult("MISSING_FIELD")
        if array.metadata.sha256_bytes != row["typed_field_sha256"].get(field_id):
            return ArchiveResult("CORRUPT_PAYLOAD", message="typed field digest mismatch")
        return ArchiveResult("FOUND", {"metadata": field, "values": array.values})


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    try:
        if manifest["schema"] != SCHEMA or manifest["archive_status"] != "COMPLETE":
            raise ValueError("unsupported schema or non-complete manifest")
        if manifest["classification"] != CLASSIFICATION or manifest["authority"] != AUTHORITY:
            raise ValueError("classification/authority mismatch")
        run = manifest["run"]
        if run["run_id"] != _id("geodyn3run", run["identity_payload"]):
            raise ValueError("run identity mismatch")
        if manifest["archive_id"] != _id("geodyn3archive", _archive_identity_payload(manifest)):
            raise ValueError("archive identity mismatch")
        if manifest["completion"]["snapshot_count"] != len(manifest["snapshots"]):
            raise ValueError("snapshot count mismatch")
        if not manifest["snapshots"]:
            raise ValueError("empty finalized archive")
        if len({item["snapshot_id"] for item in manifest["snapshots"]}) != len(manifest["snapshots"]):
            raise ValueError("duplicate snapshot ID")
        payload_ids: set[str] = set()
        for item in manifest["payload_catalog"]:
            if item["availability"]["state"] not in ("AVAILABLE_LOCAL", "AVAILABLE_EXTERNAL", "UNAVAILABLE", "EXPIRED", "UNKNOWN"):
                raise ValueError("invalid payload availability state")
            timestamp = datetime.fromisoformat(item["availability"]["checked_at_utc"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
                raise ValueError("payload availability check time must be UTC")
            payload = {"sha256": item["sha256"], "byte_length": item["byte_length"], "role": item["role"]}
            if item["payload_id"] != _id("geodyn3payload", payload):
                raise ValueError("payload ID mismatch")
            if item["payload_id"] in payload_ids:
                raise ValueError("duplicate payload identity record")
            payload_ids.add(item["payload_id"])
        mesh_ids: set[str] = set()
        for item in manifest["mesh_catalog"]:
            mesh_payload = {"reader_mesh_fingerprint": item["fingerprint"],
                            "coordinate_type": item["coordinate_dtype"],
                            "coordinate_sha256_typed": item["coordinate_sha256_typed"],
                            "point_count": item["point_count"], "cell_count": item["cell_count"],
                            "cell_type_counts": item["cell_type_counts"]}
            if item["mesh_id"] != _id("geodyn3mesh", mesh_payload):
                raise ValueError("mesh ID mismatch")
            if item["mesh_id"] in mesh_ids:
                raise ValueError("duplicate mesh identity record")
            mesh_ids.add(item["mesh_id"])
        field_ids: set[str] = set()
        allowed_dtypes = {"Float32", "Float64", "Int8", "UInt8", "Int16", "UInt16",
                          "Int32", "UInt32", "Int64", "UInt64"}
        for item in manifest["field_catalog"]:
            if item["association"] not in ("point", "cell") or item["vtk_dtype"] not in allowed_dtypes:
                raise ValueError("unsupported field association or numeric dtype")
            if (not isinstance(item["components"], int) or item["components"] < 1
                    or not isinstance(item["tuple_count"], int) or item["tuple_count"] < 0):
                raise ValueError("invalid field component/tuple count")
            if not isinstance(item["units"], str) or not item["units"]:
                raise ValueError("field units must be declared or UNKNOWN")
            field_payload = {key: value for key, value in item.items() if key != "field_id"}
            if item["field_id"] != _id("geodyn3field", field_payload):
                raise ValueError("field ID mismatch")
            if item["field_id"] in field_ids:
                raise ValueError("duplicate field identity record")
            field_ids.add(item["field_id"])
        sources: dict[str, dict[str, Any]] = {}
        for source in manifest["source_files"]:
            _validate_relative_ref(source["relative_ref"])
            if source["relative_ref"] in sources:
                raise ValueError("duplicate source file reference")
            if source["byte_length"] < 0 or not _HEX.fullmatch(source["sha256"]):
                raise ValueError("invalid source payload identity")
            if source["availability"]["state"] not in ("AVAILABLE_LOCAL", "AVAILABLE_EXTERNAL", "UNAVAILABLE", "EXPIRED", "UNKNOWN"):
                raise ValueError("invalid source availability state")
            timestamp = datetime.fromisoformat(source["availability"]["checked_at_utc"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
                raise ValueError("source availability check time must be UTC")
            sources[source["relative_ref"]] = source
        if manifest["source_pvd_ref"] not in sources:
            raise ValueError("PVD reference is absent from source inventory")
        seen_ordinals: set[int] = set()
        previous = -math.inf
        ordinals: list[int] = []
        for snap in manifest["snapshots"]:
            time_value = float(snap["time"]["value"])
            if not math.isfinite(time_value) or time_value < previous:
                raise ValueError("invalid source time order")
            previous = time_value
            if snap["source_ordinal"] in seen_ordinals:
                raise ValueError("duplicate source ordinal")
            seen_ordinals.add(snap["source_ordinal"])
            ordinals.append(snap["source_ordinal"])
            if snap["mesh_id"] not in mesh_ids or snap["payload_id"] not in payload_ids:
                raise ValueError("snapshot references missing mesh or payload")
            if not set(snap["field_ids"]).issubset(field_ids):
                raise ValueError("snapshot references missing field")
            reference = snap["vtu_relative_ref"]
            _validate_relative_ref(reference)
            if reference not in sources or sources[reference]["sha256"] != snap["source_file_sha256"] or sources[reference]["byte_length"] != snap["source_file_byte_length"]:
                raise ValueError("snapshot source reference and digest disagree")
            token_value = float(snap["time"]["source_token"])
            if token_value != time_value or snap["time"]["unit"] != manifest["time"]["unit"] or snap["time"]["time_basis_id"] != manifest["time"]["basis_id"]:
                raise ValueError("snapshot native time fields disagree")
            if set(snap["typed_field_sha256"]) != set(snap["field_ids"]):
                raise ValueError("snapshot field digests do not match field references")
            if any(not _HEX.fullmatch(value) for value in snap["typed_field_sha256"].values()):
                raise ValueError("invalid typed field digest")
            snapshot_payload = {
                "schema": SCHEMA, "run_id": run["run_id"], "attempt_id": run["attempt_id"],
                "source_ordinal": snap["source_ordinal"],
                "original_time_token": snap["time"]["source_token"], "time_value": time_value,
                "time_unit": snap["time"]["unit"], "time_basis_id": snap["time"]["time_basis_id"],
                "mesh_id": snap["mesh_id"], "field_ids": sorted(snap["field_ids"]),
                "payload_id": snap["payload_id"],
            }
            if snap["snapshot_id"] != _id("geodyn3snapshot", snapshot_payload):
                raise ValueError("snapshot ID mismatch")
        if ordinals != sorted(ordinals):
            raise ValueError("source ordinals are not in source order")
        completion_time = manifest["time"]["solver_completed_time"]
        if not math.isfinite(float(completion_time)) or completion_time < previous:
            raise ValueError("solver completion time is invalid or precedes archived data")
        _validate_relative_ref(manifest["source_pvd_ref"])
    except (KeyError, TypeError, ValueError, ArchiveError) as exc:
        raise ArchiveError("CORRUPT_MANIFEST", f"manifest schema/reference validation failed: {exc}") from exc

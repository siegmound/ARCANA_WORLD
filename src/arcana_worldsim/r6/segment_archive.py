"""Incremental, noncanonical archive for states emitted by the reduced integrator.

The writer observes immutable ``ReducedState`` values. It does not decide which
records are representative and deliberately does not claim that observations
are restartable checkpoints.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Iterator, Mapping, Sequence


ARCHIVE_SCHEMA = "ARCANA_R6_SEGMENT_ARCHIVE_V1"
STATE_STREAM = "STATES.jsonl"
MANIFEST_NAME = "SEGMENT_MANIFEST.json"
MANIFEST_SIDECAR = "SEGMENT_MANIFEST.json.sha256"
INCOMPLETE_NAME = "INCOMPLETE.json"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class SegmentArchiveError(ValueError):
    """The archive contract is incomplete or its bytes cannot be trusted."""


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SegmentArchiveError("ARCHIVE_VALUE_NOT_CANONICAL_JSON") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _valid_sha(value: Any, label: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise SegmentArchiveError(f"{label}_SHA256_INVALID")


def _validate_provenance(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {"identity_status", "source_commit", "source_composite_sha256",
                "configuration_sha256", "provider_identities", "input_identities"}
    if not isinstance(value, Mapping) or set(value) != required:
        raise SegmentArchiveError("PROVENANCE_FIELDS_INCOMPLETE_OR_UNEXPECTED")
    if value["identity_status"] not in ("SYNTHETIC_TEST_ONLY", "CALLER_ASSERTED_UNVERIFIED"):
        raise SegmentArchiveError("PROVENANCE_AUTHORITY_LABEL_UNSUPPORTED")
    commit = value["source_commit"]
    if value["identity_status"] == "SYNTHETIC_TEST_ONLY":
        if commit != "TEST_ONLY":
            raise SegmentArchiveError("TEST_ONLY_COMMIT_LABEL_REQUIRED")
    elif not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise SegmentArchiveError("SOURCE_COMMIT_ID_INVALID")
    _valid_sha(value["source_composite_sha256"], "SOURCE_COMPOSITE")
    _valid_sha(value["configuration_sha256"], "CONFIGURATION")
    for name in ("provider_identities", "input_identities"):
        members = value[name]
        if not isinstance(members, Mapping) or not members:
            raise SegmentArchiveError(f"{name.upper()}_MISSING")
        for key, digest in members.items():
            if not isinstance(key, str) or not key:
                raise SegmentArchiveError(f"{name.upper()}_KEY_INVALID")
            _valid_sha(digest, name.upper())
    # The writer only stores caller claims; it has no authority to verify them.
    return json.loads(_canonical_bytes(dict(value)))


def _grid_identity(state_payload: Mapping[str, Any]) -> str:
    grid = {"coordinate_system": "LAGRANGIAN_MATERIAL_COORDINATE",
            "material_coordinate": state_payload["material_coordinate"],
            "materials": state_payload["materials"]}
    return _sha256(_canonical_bytes(grid))


def _write_exclusive(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


class SegmentArchiveWriter:
    """Stream every integrator observation to a new, fail-closed bundle.

    A bundle is readable as complete only after ``finalize`` writes a verified
    manifest and sidecar and removes the initial incomplete marker. Successful
    writes flush each JSONL record but do not claim storage-device durability.
    """

    def __init__(self, root: str | Path, *, segment_id: str,
                 provenance: Mapping[str, Any], expected_trajectory_count: int,
                 forbidden_roots: Sequence[str | Path] = ()) -> None:
        self.root = Path(root)
        if not self.root.is_absolute():
            raise SegmentArchiveError("ARCHIVE_ROOT_MUST_BE_ABSOLUTE")
        if not _ID_RE.fullmatch(segment_id):
            raise SegmentArchiveError("SEGMENT_ID_INVALID")
        if any(part.casefold() == "world_history" for part in self.root.parts):
            raise SegmentArchiveError("CANONICAL_WORLD_HISTORY_DESTINATION_FORBIDDEN")
        if (isinstance(expected_trajectory_count, bool)
                or not isinstance(expected_trajectory_count, int)
                or expected_trajectory_count < 1):
            raise SegmentArchiveError("EXPECTED_TRAJECTORY_COUNT_INVALID")
        if self.root.exists() or self.root.is_symlink():
            raise SegmentArchiveError("ARCHIVE_DESTINATION_ALREADY_EXISTS")
        if not self.root.parent.exists() or not self.root.parent.is_dir():
            raise SegmentArchiveError("ARCHIVE_PARENT_MUST_EXIST")
        for parent in self.root.parents:
            if parent.exists() and (_is_link_or_junction(parent) or not parent.is_dir()):
                raise SegmentArchiveError("ARCHIVE_PARENT_NOT_REGULAR_DIRECTORY")
        for forbidden in forbidden_roots:
            blocked = Path(forbidden).absolute()
            if self.root == blocked or blocked in self.root.parents or self.root in blocked.parents:
                raise SegmentArchiveError("ARCHIVE_DESTINATION_OVERLAPS_FORBIDDEN_ROOT")
        self.provenance = _validate_provenance(provenance)
        self.segment_id = segment_id
        self.expected_trajectory_count = expected_trajectory_count
        self.root.mkdir(parents=False, exist_ok=False)
        self._incomplete_path = self.root / INCOMPLETE_NAME
        _write_exclusive(self._incomplete_path, _canonical_bytes({
            "schema": ARCHIVE_SCHEMA, "segment_id": segment_id,
            "status": "INCOMPLETE", "reason": "ARCHIVE_NOT_FINALIZED",
        }) + b"\n")
        self._stream_path = self.root / STATE_STREAM
        self._stream = self._stream_path.open("xb")
        self._stream_hash = hashlib.sha256()
        self._stream_bytes = 0
        self._state_count = 0
        self._trajectory_summaries: list[dict[str, Any]] = []
        self._active: dict[str, Any] | None = None
        self._closed = False
        self._failed = False

    @property
    def bytes_written(self) -> int:
        return self._stream_bytes

    @property
    def state_count(self) -> int:
        return self._state_count

    @contextmanager
    def trajectory(self, *, trajectory_id: str, support_id: str,
                   trajectory_kind: str, resolution_factor: float,
                   start_time_s: float, requested_duration_s: float,
                   time_unit: str = "s") -> Iterator["SegmentArchiveWriter"]:
        """Bind a unique trajectory and require explicit endpoint completion."""
        if self._closed or self._failed or self._active is not None:
            raise SegmentArchiveError("ARCHIVE_NOT_READY_FOR_TRAJECTORY")
        if (not isinstance(trajectory_id, str) or not _ID_RE.fullmatch(trajectory_id)
                or not isinstance(support_id, str) or not _ID_RE.fullmatch(support_id)
                or not isinstance(trajectory_kind, str) or not _ID_RE.fullmatch(trajectory_kind)):
            raise SegmentArchiveError("TRAJECTORY_OR_SUPPORT_ID_INVALID")
        if any(x["trajectory_id"] == trajectory_id for x in self._trajectory_summaries):
            raise SegmentArchiveError("TRAJECTORY_ID_DUPLICATE")
        if (isinstance(resolution_factor, bool) or not isinstance(resolution_factor, (int, float))
                or not math.isfinite(resolution_factor) or resolution_factor <= 0):
            raise SegmentArchiveError("RESOLUTION_FACTOR_INVALID")
        if (isinstance(start_time_s, bool) or not isinstance(start_time_s, (int, float))
                or isinstance(requested_duration_s, bool)
                or not isinstance(requested_duration_s, (int, float))
                or not math.isfinite(start_time_s) or not math.isfinite(requested_duration_s)
                or requested_duration_s <= 0
                or not math.isfinite(start_time_s + requested_duration_s)):
            raise SegmentArchiveError("TRAJECTORY_TIME_INVALID")
        if time_unit != "s":
            raise SegmentArchiveError("UNSUPPORTED_TIME_UNIT")
        self._active = {"trajectory_id": trajectory_id, "support_id": support_id,
                        "trajectory_kind": trajectory_kind,
                        "resolution_factor": resolution_factor,
                        "start_time_s": start_time_s,
                        "expected_end_time_s": start_time_s + requested_duration_s,
                        "requested_duration_s": requested_duration_s,
                        "first_sequence": self._state_count,
                        "state_count": 0, "last_time_s": None,
                        "last_state_sha256": None, "grid_identity_sha256": None,
                        "completion": "OPEN"}
        try:
            yield self
            if self._active is not None:
                self._failed = True
                self._mark_incomplete("TRAJECTORY_EXIT_WITHOUT_EXPLICIT_COMPLETION")
                raise SegmentArchiveError("TRAJECTORY_NOT_EXPLICITLY_COMPLETED")
        except BaseException as exc:
            self._failed = True
            self._mark_incomplete(f"TRAJECTORY_FAILED:{type(exc).__name__}")
            self._active = None
            raise

    def observe(self, state: Any) -> None:
        """Append one exact state object emitted by the integration observer."""
        if self._closed or self._failed or self._active is None:
            raise SegmentArchiveError("NO_ACTIVE_ARCHIVE_TRAJECTORY")
        try:
            payload = state.payload()
            time_s = state.time_s
            if isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s):
                raise SegmentArchiveError("STATE_TIME_INVALID")
            active = self._active
            previous = active["last_time_s"]
            if previous is None:
                if time_s != active["start_time_s"]:
                    raise SegmentArchiveError("INITIAL_STATE_TIME_MISMATCH")
                record_type = "INITIAL_INTEGRATOR_STATE"
            else:
                if time_s <= previous:
                    raise SegmentArchiveError("STATE_TIME_NOT_STRICTLY_INCREASING")
                record_type = "INTEGRATOR_SUBSTEP_STATE"
            state_bytes = _canonical_bytes(payload)
            state_digest = _sha256(state_bytes)
            grid_digest = _grid_identity(payload)
            if active["grid_identity_sha256"] is None:
                active["grid_identity_sha256"] = grid_digest
            elif active["grid_identity_sha256"] != grid_digest:
                raise SegmentArchiveError("MATERIAL_GRID_IDENTITY_CHANGED_WITHIN_TRAJECTORY")
            record = {"schema": "ARCANA_R6_SEGMENT_STATE_RECORD_V1",
                      "segment_id": self.segment_id,
                      "trajectory_id": active["trajectory_id"],
                      "trajectory_kind": active["trajectory_kind"],
                      "support_id": active["support_id"],
                      "resolution_factor": active["resolution_factor"],
                      "sequence": self._state_count,
                      "trajectory_sequence": active["state_count"],
                      "record_type": record_type,
                      "state_class": "DIAGNOSTIC_OBSERVATION",
                      "checkpoint_capability": "NOT_QUALIFIED_AS_RESTARTABLE",
                      "time_s": time_s,
                      "time_s_hex": float(time_s).hex(),
                      "time_unit": "s",
                      "grid_identity_sha256": grid_digest,
                      "state_payload_sha256": state_digest,
                      "state": payload}
            line = _canonical_bytes(record) + b"\n"
            written = self._stream.write(line)
            if written != len(line):
                raise OSError("SHORT_ARCHIVE_WRITE")
            self._stream.flush()
            self._stream_hash.update(line)
            self._stream_bytes += len(line)
            self._state_count += 1
            active["state_count"] += 1
            active["last_time_s"] = time_s
            active["last_state_sha256"] = state_digest
        except BaseException as exc:
            self._failed = True
            self._mark_incomplete(f"STATE_WRITE_FAILED:{type(exc).__name__}")
            raise

    def complete_trajectory(self, final_state: Any, *, integration_substeps: int) -> None:
        if self._active is None or self._failed:
            raise SegmentArchiveError("NO_ACTIVE_TRAJECTORY_TO_COMPLETE")
        active = self._active
        if (isinstance(integration_substeps, bool) or not isinstance(integration_substeps, int)
                or integration_substeps < 1 or active["state_count"] != integration_substeps + 1):
            raise SegmentArchiveError("INTEGRATOR_OBSERVATION_COUNT_MISMATCH")
        final_payload = final_state.payload()
        final_digest = _sha256(_canonical_bytes(final_payload))
        if final_state.time_s != active["last_time_s"] or final_digest != active["last_state_sha256"]:
            raise SegmentArchiveError("FINAL_STATE_DIFFERS_FROM_OBSERVED_ENDPOINT")
        roundoff_bound = max(1, integration_substeps + 1) * math.ulp(active["expected_end_time_s"])
        if abs(final_state.time_s - active["expected_end_time_s"]) > max(1e-9, roundoff_bound):
            raise SegmentArchiveError("FINAL_TIME_DIFFERS_FROM_REQUESTED_ENDPOINT")
        active["completion"] = "COMPLETE"
        active["integration_substeps"] = integration_substeps
        self._trajectory_summaries.append(dict(active))
        self._active = None

    def _mark_incomplete(self, reason: str) -> None:
        try:
            if self._incomplete_path.exists():
                value = {"schema": ARCHIVE_SCHEMA, "segment_id": self.segment_id,
                         "status": "INCOMPLETE", "reason": reason,
                         "states_written": self._state_count}
                self._incomplete_path.write_bytes(_canonical_bytes(value) + b"\n")
        except OSError:
            # The original marker remains and complete-manifest publication is
            # still forbidden; do not hide the triggering I/O exception.
            pass

    def finalize(self) -> dict[str, Any]:
        if self._closed or self._failed or self._active is not None:
            raise SegmentArchiveError("ARCHIVE_CANNOT_BE_FINALIZED")
        if len(self._trajectory_summaries) != self.expected_trajectory_count:
            raise SegmentArchiveError("EXPECTED_TRAJECTORY_SET_INCOMPLETE")
        self._stream.flush()
        os.fsync(self._stream.fileno())
        self._stream.close()
        self._closed = True
        manifest = {"schema": ARCHIVE_SCHEMA, "segment_id": self.segment_id,
                    "completion_status": "COMPLETE",
                    "completion_contract": "ALL_EXPECTED_TRAJECTORIES_COMPLETE; INCOMPLETE_MARKER_ABSENT",
                    "expected_trajectory_count": self.expected_trajectory_count,
                    "state_class": "DIAGNOSTIC_OBSERVATION",
                    "checkpoint_capability": "NOT_QUALIFIED_AS_RESTARTABLE",
                    "provenance": self.provenance,
                    "provenance_authority": "CALLER_ASSERTIONS_STORED_NOT_INDEPENDENTLY_AUTHENTICATED",
                    "state_stream": {"path": STATE_STREAM, "bytes": self._stream_bytes,
                                     "sha256": self._stream_hash.hexdigest(),
                                     "record_count": self._state_count},
                    "trajectories": self._trajectory_summaries,
                    "write_semantics": {"per_record_flush": True,
                        "fsync_at_finalize": True,
                        "atomic_manifest_rename_same_directory": True,
                        "device_durability_or_directory_fsync": "NOT_CLAIMED"},
                    "representative_selection": "SEPARATE_DERIVED_INDEX_NOT_INCLUDED"}
        raw = _canonical_bytes(manifest) + b"\n"
        tmp = self.root / (MANIFEST_NAME + ".tmp")
        final = self.root / MANIFEST_NAME
        if tmp.exists() or final.exists():
            self._failed = True
            self._mark_incomplete("MANIFEST_COLLISION")
            raise SegmentArchiveError("MANIFEST_PATH_COLLISION")
        _write_exclusive(tmp, raw)
        os.replace(tmp, final)
        sidecar = self.root / MANIFEST_SIDECAR
        _write_exclusive(sidecar, f"{_sha256(raw)}  {MANIFEST_NAME}\n".encode("ascii"))
        self._incomplete_path.unlink()
        return manifest

    def close_incomplete(self, reason: str = "CALLER_ABORTED") -> None:
        if self._closed:
            return
        self._failed = True
        self._mark_incomplete(reason)
        try:
            self._stream.flush()
            self._stream.close()
        finally:
            self._closed = True


def validate_segment_archive(root: str | Path) -> dict[str, Any]:
    """Stream-check a completed archive; reject partial or unqualified bundles."""
    path = Path(root)
    if (not path.is_dir() or _is_link_or_junction(path)
            or (path / INCOMPLETE_NAME).exists() or _is_link_or_junction(path / INCOMPLETE_NAME)):
        raise SegmentArchiveError("ARCHIVE_MISSING_OR_INCOMPLETE")
    manifest_path = path / MANIFEST_NAME
    sidecar_path = path / MANIFEST_SIDECAR
    stream_path = path / STATE_STREAM
    if not all(x.is_file() and not x.is_symlink() for x in (manifest_path, sidecar_path, stream_path)):
        raise SegmentArchiveError("ARCHIVE_REQUIRED_FILE_MISSING_OR_LINKED")
    manifest_raw = manifest_path.read_bytes()
    sidecar = sidecar_path.read_text(encoding="ascii").strip().split()
    if len(sidecar) != 2 or sidecar[1] != MANIFEST_NAME or sidecar[0] != _sha256(manifest_raw):
        raise SegmentArchiveError("MANIFEST_SIDECAR_MISMATCH")
    manifest = json.loads(manifest_raw)
    if (manifest.get("schema") != ARCHIVE_SCHEMA or manifest.get("completion_status") != "COMPLETE"
            or manifest.get("checkpoint_capability") != "NOT_QUALIFIED_AS_RESTARTABLE"):
        raise SegmentArchiveError("MANIFEST_COMPLETION_OR_CHECKPOINT_STATUS_INVALID")
    _validate_provenance(manifest.get("provenance", {}))
    file_hash = hashlib.sha256()
    byte_count = record_count = 0
    per_trajectory: dict[str, dict[str, Any]] = {}
    with stream_path.open("rb") as stream:
        for line in stream:
            if not line.endswith(b"\n"):
                raise SegmentArchiveError("STATE_STREAM_PARTIAL_LINE")
            file_hash.update(line)
            byte_count += len(line)
            record = json.loads(line)
            if (record.get("schema") != "ARCANA_R6_SEGMENT_STATE_RECORD_V1"
                    or record.get("state_class") != "DIAGNOSTIC_OBSERVATION"
                    or record.get("checkpoint_capability") != "NOT_QUALIFIED_AS_RESTARTABLE"):
                raise SegmentArchiveError("STATE_RECORD_SCHEMA_OR_CLASS_INVALID")
            state_payload = record.get("state")
            if _sha256(_canonical_bytes(state_payload)) != record.get("state_payload_sha256"):
                raise SegmentArchiveError("STATE_PAYLOAD_FINGERPRINT_MISMATCH")
            if _grid_identity(state_payload) != record.get("grid_identity_sha256"):
                raise SegmentArchiveError("STATE_GRID_IDENTITY_MISMATCH")
            tid = record.get("trajectory_id")
            time_s = record.get("time_s")
            identity = {key: record.get(key) for key in (
                "segment_id", "trajectory_kind", "support_id", "resolution_factor",
                "grid_identity_sha256")}
            row = per_trajectory.setdefault(tid, {"count": 0, "last_time_s": None,
                                                  "first_sequence": record.get("sequence"),
                                                  "identity": identity,
                                                  "start_time_s": time_s})
            if row["identity"] != identity:
                raise SegmentArchiveError("TRAJECTORY_IDENTITY_CHANGED_IN_STREAM")
            if record.get("sequence") != record_count or record.get("trajectory_sequence") != row["count"]:
                raise SegmentArchiveError("STATE_SEQUENCE_GAP_OR_DUPLICATE")
            if (not isinstance(time_s, (int, float)) or isinstance(time_s, bool)
                    or not math.isfinite(time_s) or float(time_s).hex() != record.get("time_s_hex")
                    or time_s != state_payload.get("time_s")):
                raise SegmentArchiveError("STATE_TIME_BINDING_INVALID")
            if row["last_time_s"] is not None and time_s <= row["last_time_s"]:
                raise SegmentArchiveError("STATE_TIME_NOT_STRICTLY_INCREASING")
            row["last_time_s"] = time_s
            row["count"] += 1
            record_count += 1
    declared = manifest.get("state_stream", {})
    if (declared.get("bytes") != byte_count or declared.get("record_count") != record_count
            or declared.get("sha256") != file_hash.hexdigest()):
        raise SegmentArchiveError("STATE_STREAM_MANIFEST_MISMATCH")
    trajectory_rows = manifest.get("trajectories", [])
    expected_count = manifest.get("expected_trajectory_count")
    if (len(trajectory_rows) != len(per_trajectory)
            or len(trajectory_rows) != len({x.get("trajectory_id") for x in trajectory_rows})
            or expected_count != len(trajectory_rows)):
        raise SegmentArchiveError("TRAJECTORY_MANIFEST_MEMBERSHIP_INVALID")
    for row in trajectory_rows:
        actual = per_trajectory.get(row.get("trajectory_id"))
        if (actual is None or actual["count"] != row.get("state_count")
                or actual["last_time_s"] != row.get("last_time_s")
                or row.get("completion") != "COMPLETE"
                or actual["count"] != row.get("integration_substeps", -1) + 1
                or actual["start_time_s"] != row.get("start_time_s")
                or actual["identity"] != {
                    "segment_id": manifest.get("segment_id"),
                    "trajectory_kind": row.get("trajectory_kind"),
                    "support_id": row.get("support_id"),
                    "resolution_factor": row.get("resolution_factor"),
                    "grid_identity_sha256": row.get("grid_identity_sha256"),
                }):
            raise SegmentArchiveError("TRAJECTORY_COMPLETION_MISMATCH")
    if set(per_trajectory) != {row["trajectory_id"] for row in trajectory_rows}:
        raise SegmentArchiveError("TRAJECTORY_STREAM_MEMBERSHIP_MISMATCH")
    return {"status": "SEGMENT_ARCHIVE_VALID", "segment_id": manifest["segment_id"],
            "trajectory_count": len(trajectory_rows), "state_count": record_count,
            "state_stream_bytes": byte_count, "state_stream_sha256": file_hash.hexdigest(),
            "manifest_sha256": _sha256(manifest_raw),
            "checkpoint_capability": "NOT_QUALIFIED_AS_RESTARTABLE"}

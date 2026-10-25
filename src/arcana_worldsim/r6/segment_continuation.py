"""Integrity-bound continuation contracts for reduced-kernel segments.

These records qualify a complete ReducedState as an engineering restart input;
they do not qualify the physics or authenticate caller-supplied provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .functional_development import ReducedState, state_from_payload
from .segment_archive import SegmentArchiveError, validate_segment_archive

CHECKPOINT_SCHEMA = "ARCANA_R6_REDUCED_STATE_CHECKPOINT_V1"
BINDING_SCHEMA = "ARCANA_R6_SEGMENT_BINDING_V1"
CONTINUATION_SCHEMA = "ARCANA_R6_SEGMENT_CONTINUATION_V1"
_SHA = re.compile(r"^[0-9a-f]{64}$")


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SegmentArchiveError("CONTINUATION_NONCANONICAL_VALUE") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(member) for key, member in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(member) for member in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(member) for key, member in value.items()}
    if isinstance(value, tuple):
        return [_thaw(member) for member in value]
    return value


def _require_sha(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise SegmentArchiveError(f"{name}_SHA256_INVALID")
    return value


def _require_identity_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SegmentArchiveError(f"{name}_IDENTITY_MISSING")
    return value


def _stream_endpoints(root: Path, trajectory_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = root / "SEGMENT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_bytes())
    matching = [row for row in manifest.get("trajectories", [])
                if row.get("trajectory_id") == trajectory_id]
    if len(matching) != 1:
        raise SegmentArchiveError("CONTINUATION_TRAJECTORY_NOT_UNIQUE")
    first = last = None
    stream = root / "STATES.jsonl"
    with stream.open("rb") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("trajectory_id") == trajectory_id:
                if first is None:
                    first = record
                last = record
    if first is None or last is None:
        raise SegmentArchiveError("CONTINUATION_TRAJECTORY_STATES_MISSING")
    return first, last


@dataclass(frozen=True, slots=True)
class SegmentBinding:
    """Caller-declared model identity bound to a validated archive trajectory."""

    schema: str
    segment_id: str
    segment_manifest_sha256: str
    trajectory_id: str
    support_id: str
    resolution_factor: float
    grid_identity_sha256: str
    start_time_s: float
    end_time_s: float
    start_state_sha256: str
    end_state_sha256: str
    model_identity_sha256: str
    model_configuration_sha256: str
    configuration_sha256: str
    source_commit: str
    source_composite_sha256: str
    forcing_identity_sha256: str
    provider_identities: Mapping[str, str]
    authority: str = "CALLER_ASSERTED_IDENTITIES_HASH_BOUND_NOT_SOURCE_AUTHENTICATED"

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_identities",
                           MappingProxyType(dict(self.provider_identities)))
        _validate_binding(self)

    def to_dict(self) -> dict[str, Any]:
        return {name: (dict(self.provider_identities) if name == "provider_identities"
                       else getattr(self, name)) for name in self.__dataclass_fields__}


def _validate_binding(binding: SegmentBinding) -> None:
    if binding.schema != BINDING_SCHEMA:
        raise SegmentArchiveError("CONTINUATION_BINDING_SCHEMA_INVALID")
    for name in ("segment_id", "trajectory_id", "support_id", "source_commit"):
        _require_identity_text(getattr(binding, name), name.upper())
    for name in ("segment_manifest_sha256", "grid_identity_sha256",
                 "start_state_sha256", "end_state_sha256", "model_identity_sha256",
                 "model_configuration_sha256", "configuration_sha256",
                 "source_composite_sha256", "forcing_identity_sha256"):
        _require_sha(getattr(binding, name), name.upper())
    if (isinstance(binding.resolution_factor, bool)
            or not isinstance(binding.resolution_factor, (int, float))
            or not math.isfinite(binding.resolution_factor)
            or binding.resolution_factor <= 0):
        raise SegmentArchiveError("CONTINUATION_RESOLUTION_INVALID")
    for value in (binding.start_time_s, binding.end_time_s):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise SegmentArchiveError("CONTINUATION_TIME_INVALID")
    if binding.end_time_s <= binding.start_time_s:
        raise SegmentArchiveError("CONTINUATION_TIME_ORDER_INVALID")
    providers = binding.provider_identities
    if not isinstance(providers, Mapping) or not providers:
        raise SegmentArchiveError("CONTINUATION_PROVIDERS_MISSING")
    for key, digest in providers.items():
        _require_identity_text(key, "PROVIDER_KEY")
        _require_sha(digest, "PROVIDER_IDENTITY")
    if binding.authority != "CALLER_ASSERTED_IDENTITIES_HASH_BOUND_NOT_SOURCE_AUTHENTICATED":
        raise SegmentArchiveError("CONTINUATION_AUTHORITY_LABEL_INVALID")


def bind_completed_segment(
    archive_root: str | Path, *, trajectory_id: str,
    model_identity_sha256: str, model_configuration_sha256: str,
    forcing_identity_sha256: str, numerical_configuration: Mapping[str, Any],
) -> SegmentBinding:
    """Bind one completed trajectory to its actual manifest and endpoint rows."""
    root = Path(archive_root)
    validated = validate_segment_archive(root)
    manifest_raw = (root / "SEGMENT_MANIFEST.json").read_bytes()
    manifest = json.loads(manifest_raw)
    first, last = _stream_endpoints(root, trajectory_id)
    summary = next(row for row in manifest["trajectories"]
                   if row["trajectory_id"] == trajectory_id)
    provenance = manifest["provenance"]
    for name, value in (
        ("MODEL_IDENTITY", model_identity_sha256),
        ("MODEL_CONFIGURATION", model_configuration_sha256),
        ("FORCING_IDENTITY", forcing_identity_sha256),
    ):
        _require_sha(value, name)
    if not isinstance(numerical_configuration, Mapping) or not numerical_configuration:
        raise SegmentArchiveError("NUMERICAL_CONFIGURATION_MISSING")
    if _digest(dict(numerical_configuration)) != model_configuration_sha256:
        raise SegmentArchiveError("MODEL_CONFIGURATION_DIGEST_MISMATCH")
    providers = provenance.get("provider_identities")
    if not isinstance(providers, Mapping) or not providers:
        raise SegmentArchiveError("CONTINUATION_PROVIDERS_MISSING")
    for key, value in providers.items():
        if not isinstance(key, str) or not key:
            raise SegmentArchiveError("CONTINUATION_PROVIDER_KEY_INVALID")
        _require_sha(value, "PROVIDER_IDENTITY")
    if (first["sequence"] != summary["first_sequence"]
            or last["state_payload_sha256"] != summary["last_state_sha256"]
            or first["time_s"] != summary["start_time_s"]
            or last["time_s"] != summary["last_time_s"]):
        raise SegmentArchiveError("CONTINUATION_ENDPOINT_MANIFEST_MISMATCH")
    return SegmentBinding(
        schema=BINDING_SCHEMA, segment_id=manifest["segment_id"],
        segment_manifest_sha256=validated["manifest_sha256"],
        trajectory_id=trajectory_id, support_id=summary["support_id"],
        resolution_factor=summary["resolution_factor"],
        grid_identity_sha256=summary["grid_identity_sha256"],
        start_time_s=first["time_s"], end_time_s=last["time_s"],
        start_state_sha256=first["state_payload_sha256"],
        end_state_sha256=last["state_payload_sha256"],
        model_identity_sha256=model_identity_sha256,
        model_configuration_sha256=model_configuration_sha256,
        configuration_sha256=provenance["configuration_sha256"],
        source_commit=provenance["source_commit"],
        source_composite_sha256=provenance["source_composite_sha256"],
        forcing_identity_sha256=forcing_identity_sha256,
        provider_identities=dict(providers),
        authority="CALLER_ASSERTED_IDENTITIES_HASH_BOUND_NOT_SOURCE_AUTHENTICATED",
    )


def _verify_binding_matches_archive(root: Path, binding: SegmentBinding) -> dict[str, Any]:
    _validate_binding(binding)
    validated = validate_segment_archive(root)
    raw = (root / "SEGMENT_MANIFEST.json").read_bytes()
    manifest = json.loads(raw)
    if (validated["manifest_sha256"] != binding.segment_manifest_sha256
            or manifest.get("segment_id") != binding.segment_id):
        raise SegmentArchiveError("CONTINUATION_BINDING_MANIFEST_MISMATCH")
    matches = [row for row in manifest.get("trajectories", [])
               if row.get("trajectory_id") == binding.trajectory_id]
    if len(matches) != 1:
        raise SegmentArchiveError("CONTINUATION_TRAJECTORY_NOT_UNIQUE")
    row = matches[0]
    provenance = manifest["provenance"]
    expected = {
        "support_id": binding.support_id,
        "resolution_factor": binding.resolution_factor,
        "grid_identity_sha256": binding.grid_identity_sha256,
        "start_time_s": binding.start_time_s,
        "last_time_s": binding.end_time_s,
        "last_state_sha256": binding.end_state_sha256,
    }
    if any(row.get(key) != value for key, value in expected.items()):
        raise SegmentArchiveError("CONTINUATION_BINDING_TRAJECTORY_MISMATCH")
    first, last = _stream_endpoints(root, binding.trajectory_id)
    if (first.get("state_payload_sha256") != binding.start_state_sha256
            or last.get("state_payload_sha256") != binding.end_state_sha256):
        raise SegmentArchiveError("CONTINUATION_BINDING_ENDPOINT_STATE_MISMATCH")
    if (provenance.get("configuration_sha256") != binding.configuration_sha256
            or provenance.get("source_commit") != binding.source_commit
            or provenance.get("source_composite_sha256") != binding.source_composite_sha256
            or dict(provenance.get("provider_identities", {})) != dict(binding.provider_identities)):
        raise SegmentArchiveError("CONTINUATION_BINDING_PROVENANCE_MISMATCH")
    return manifest


@dataclass(frozen=True, slots=True)
class QualifiedCheckpoint:
    """Complete state plus exact restart scope; engineering scope only."""

    checkpoint_id: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _freeze(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return _thaw(self.payload)


def create_qualified_checkpoint(
    archive_root: str | Path, binding: SegmentBinding, final_state: ReducedState,
) -> QualifiedCheckpoint:
    """Create a restart input only when the state is the archived final record."""
    root = Path(archive_root)
    _verify_binding_matches_archive(root, binding)
    state_payload = final_state.payload()
    restored = state_from_payload(state_payload)
    if _canonical(restored.payload()) != _canonical(state_payload):
        raise SegmentArchiveError("CHECKPOINT_RECONSTRUCTION_NOT_BITWISE")
    _, last = _stream_endpoints(root, binding.trajectory_id)
    if (binding.segment_manifest_sha256 !=
            hashlib.sha256((root / "SEGMENT_MANIFEST.json").read_bytes()).hexdigest()
            or last["state_payload_sha256"] != _digest(state_payload)
            or last["time_s"] != final_state.time_s
            or last["state"] != state_payload):
        raise SegmentArchiveError("CHECKPOINT_NOT_ARCHIVED_SEGMENT_ENDPOINT")
    body = {
        "schema": CHECKPOINT_SCHEMA,
        "qualification": "ENGINEERING_REDUCED_STATE_RESTART_INPUT_ONLY",
        "scientific_authority": "NOT_QUALIFIED",
        "segment_id": binding.segment_id,
        "segment_manifest_sha256": binding.segment_manifest_sha256,
        "trajectory_id": binding.trajectory_id,
        "support_id": binding.support_id,
        "grid_identity_sha256": binding.grid_identity_sha256,
        "resolution_factor": binding.resolution_factor,
        "time_s": final_state.time_s,
        "state_payload_sha256": _digest(state_payload),
        "state_payload": state_payload,
        "model_identity_sha256": binding.model_identity_sha256,
        "model_configuration_sha256": binding.model_configuration_sha256,
        "configuration_sha256": binding.configuration_sha256,
        "source_commit": binding.source_commit,
        "source_composite_sha256": binding.source_composite_sha256,
        "forcing_identity_sha256": binding.forcing_identity_sha256,
        "provider_identities": dict(binding.provider_identities),
    }
    return QualifiedCheckpoint(_digest(body), {**body, "checkpoint_id": _digest(body)})


def write_qualified_checkpoint(path: str | Path, checkpoint: QualifiedCheckpoint) -> str:
    """Create a new checkpoint file exclusively; no overwrite or durability claim."""
    _validate_checkpoint_object(checkpoint)
    target = Path(path)
    raw = _canonical(checkpoint.to_dict()) + b"\n"
    try:
        with target.open("xb") as handle:
            if handle.write(raw) != len(raw):
                raise OSError("SHORT_CHECKPOINT_WRITE")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise SegmentArchiveError("CHECKPOINT_DESTINATION_COLLISION") from exc
    return hashlib.sha256(raw).hexdigest()


def load_qualified_checkpoint(path: str | Path) -> tuple[QualifiedCheckpoint, ReducedState]:
    try:
        value = json.loads(Path(path).read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise SegmentArchiveError("CHECKPOINT_READ_OR_PARSE_FAILED") from exc
    if (not isinstance(value, dict) or value.get("schema") != CHECKPOINT_SCHEMA
            or value.get("qualification") != "ENGINEERING_REDUCED_STATE_RESTART_INPUT_ONLY"
            or value.get("scientific_authority") != "NOT_QUALIFIED"):
        raise SegmentArchiveError("CHECKPOINT_NOT_ENGINEERING_RESTART_INPUT")
    claimed_id = value.get("checkpoint_id")
    body = {key: member for key, member in value.items() if key != "checkpoint_id"}
    if not isinstance(claimed_id, str) or claimed_id != _digest(body):
        raise SegmentArchiveError("CHECKPOINT_IDENTITY_MISMATCH")
    state_payload = body.get("state_payload")
    if not isinstance(state_payload, Mapping) or _digest(state_payload) != body.get("state_payload_sha256"):
        raise SegmentArchiveError("CHECKPOINT_STATE_DIGEST_MISMATCH")
    try:
        state = state_from_payload(state_payload)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise SegmentArchiveError("CHECKPOINT_STATE_INVALID") from exc
    if (_canonical(state.payload()) != _canonical(state_payload)
            or state.time_s != body.get("time_s")):
        raise SegmentArchiveError("CHECKPOINT_STATE_RECONSTRUCTION_MISMATCH")
    for key in ("model_identity_sha256", "model_configuration_sha256",
                "configuration_sha256", "source_composite_sha256",
                "forcing_identity_sha256", "grid_identity_sha256",
                "segment_manifest_sha256", "state_payload_sha256"):
        _require_sha(body.get(key), key.upper())
    _require_identity_text(body.get("source_commit"), "CHECKPOINT_SOURCE_COMMIT")
    _require_identity_text(body.get("segment_id"), "CHECKPOINT_SEGMENT_ID")
    _require_identity_text(body.get("trajectory_id"), "CHECKPOINT_TRAJECTORY_ID")
    _require_identity_text(body.get("support_id"), "CHECKPOINT_SUPPORT_ID")
    resolution_factor = body.get("resolution_factor")
    if (isinstance(resolution_factor, bool) or not isinstance(resolution_factor, (int, float))
            or not math.isfinite(resolution_factor) or resolution_factor <= 0):
        raise SegmentArchiveError("CHECKPOINT_RESOLUTION_INVALID")
    providers = body.get("provider_identities")
    if not isinstance(providers, Mapping) or not providers:
        raise SegmentArchiveError("CHECKPOINT_PROVIDERS_MISSING")
    for key, digest in providers.items():
        _require_identity_text(key, "CHECKPOINT_PROVIDER_KEY")
        _require_sha(digest, "CHECKPOINT_PROVIDER")
    return QualifiedCheckpoint(claimed_id, body | {"checkpoint_id": claimed_id}), state


def build_continuation_manifest(
    bindings: Sequence[SegmentBinding], checkpoints: Sequence[QualifiedCheckpoint],
) -> dict[str, Any]:
    """Verify an ordered chain of exact, compatible segment boundaries."""
    if len(bindings) < 2 or len(checkpoints) != len(bindings) - 1:
        raise SegmentArchiveError("CONTINUATION_CHAIN_CARDINALITY_INVALID")
    identities = ("support_id", "grid_identity_sha256", "model_identity_sha256",
                  "model_configuration_sha256", "configuration_sha256", "source_commit",
                  "source_composite_sha256", "forcing_identity_sha256", "provider_identities",
                  "resolution_factor")
    for binding in bindings:
        _validate_binding(binding)
    if len({binding.segment_id for binding in bindings}) != len(bindings):
        raise SegmentArchiveError("CONTINUATION_SEGMENT_ID_DUPLICATE")
    for left, right in zip(bindings, bindings[1:]):
        if left.end_time_s >= right.end_time_s:
            raise SegmentArchiveError("CONTINUATION_SEGMENT_ORDER_INVALID")
        for name in identities:
            if getattr(left, name) != getattr(right, name):
                raise SegmentArchiveError(f"CONTINUATION_IDENTITY_MISMATCH:{name}")
    joins = []
    for index, (left, checkpoint, right) in enumerate(zip(bindings, checkpoints, bindings[1:])):
        row = checkpoint.to_dict()
        _checkpoint_body, checkpoint_state = _validate_checkpoint_object(checkpoint)
        if checkpoint_state.time_s != left.end_time_s:
            raise SegmentArchiveError("CONTINUATION_CHECKPOINT_STATE_TIME_INVALID")
        if (row.get("segment_manifest_sha256") != left.segment_manifest_sha256
                or row.get("segment_id") != left.segment_id
                or row.get("trajectory_id") != left.trajectory_id
                or row.get("support_id") != left.support_id
                or row.get("resolution_factor") != left.resolution_factor
                or row.get("grid_identity_sha256") != left.grid_identity_sha256
                or row.get("time_s") != left.end_time_s
                or row.get("state_payload_sha256") != left.end_state_sha256
                or right.start_time_s != left.end_time_s
                or right.start_state_sha256 != left.end_state_sha256
                or row.get("grid_identity_sha256") != right.grid_identity_sha256
                or row.get("state_payload_sha256") != right.start_state_sha256):
            raise SegmentArchiveError("CONTINUATION_BOUNDARY_STATE_OR_TIME_MISMATCH")
        for name in identities:
            checkpoint_name = name
            if row.get(checkpoint_name) != getattr(left, name):
                raise SegmentArchiveError(f"CONTINUATION_CHECKPOINT_IDENTITY_MISMATCH:{name}")
        joins.append({
            "after_segment_index": index, "checkpoint_id": checkpoint.checkpoint_id,
            "checkpoint_state_sha256": row["state_payload_sha256"],
            "time_s": row["time_s"], "from_manifest_sha256": left.segment_manifest_sha256,
            "to_manifest_sha256": right.segment_manifest_sha256,
        })
    body = {
        "schema": CONTINUATION_SCHEMA,
        "status": "CHAIN_VALIDATED_HASH_BOUND_NOT_EXECUTED",
        "qualification_scope": "ENGINEERING_REDUCED_STATE_BOUNDARY_CONTINUITY_ONLY",
        "segments": [{
            "segment_id": b.segment_id, "manifest_sha256": b.segment_manifest_sha256,
            "trajectory_id": b.trajectory_id, "support_id": b.support_id,
            "start_time_s": b.start_time_s, "end_time_s": b.end_time_s,
            "start_state_sha256": b.start_state_sha256, "end_state_sha256": b.end_state_sha256,
            "binding": b.to_dict(),
            "binding_sha256": _digest(b.to_dict()),
        } for b in bindings],
        "joins": joins,
        "shared_identity": {name: (dict(getattr(bindings[0], name))
                                    if isinstance(getattr(bindings[0], name), Mapping)
                                    else getattr(bindings[0], name)) for name in identities},
        "authority": "HASH_INTEGRITY_AND_CALLER_ASSERTED_BINDINGS_ONLY; NO_KERNEL_EXECUTION_OR_PHYSICAL_QUALIFICATION",
    }
    manifest = {**body, "continuation_sha256": _digest(body)}
    validate_continuation_manifest(manifest)
    return manifest


def _validate_checkpoint_object(checkpoint: QualifiedCheckpoint) -> tuple[dict[str, Any], ReducedState]:
    value = checkpoint.to_dict()
    if not isinstance(value, Mapping):
        raise SegmentArchiveError("CHECKPOINT_OBJECT_INVALID")
    claimed_id = value.get("checkpoint_id")
    body = {key: member for key, member in value.items() if key != "checkpoint_id"}
    if claimed_id != checkpoint.checkpoint_id or claimed_id != _digest(body):
        raise SegmentArchiveError("CHECKPOINT_IDENTITY_MISMATCH")
    if (body.get("schema") != CHECKPOINT_SCHEMA
            or body.get("qualification") != "ENGINEERING_REDUCED_STATE_RESTART_INPUT_ONLY"
            or body.get("scientific_authority") != "NOT_QUALIFIED"):
        raise SegmentArchiveError("CHECKPOINT_NOT_ENGINEERING_RESTART_INPUT")
    payload = body.get("state_payload")
    if not isinstance(payload, Mapping) or _digest(payload) != body.get("state_payload_sha256"):
        raise SegmentArchiveError("CHECKPOINT_STATE_DIGEST_MISMATCH")
    try:
        state = state_from_payload(payload)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise SegmentArchiveError("CHECKPOINT_STATE_INVALID") from exc
    if state.time_s != body.get("time_s") or _canonical(state.payload()) != _canonical(payload):
        raise SegmentArchiveError("CHECKPOINT_STATE_RECONSTRUCTION_MISMATCH")
    for name in ("model_identity_sha256", "model_configuration_sha256", "configuration_sha256",
                 "source_composite_sha256", "forcing_identity_sha256", "grid_identity_sha256",
                 "segment_manifest_sha256", "state_payload_sha256"):
        _require_sha(body.get(name), name.upper())
    for name in ("source_commit", "segment_id", "trajectory_id", "support_id"):
        _require_identity_text(body.get(name), name.upper())
    resolution = body.get("resolution_factor")
    if isinstance(resolution, bool) or not isinstance(resolution, (int, float)) or not math.isfinite(resolution) or resolution <= 0:
        raise SegmentArchiveError("CHECKPOINT_RESOLUTION_INVALID")
    providers = body.get("provider_identities")
    if not isinstance(providers, Mapping) or not providers:
        raise SegmentArchiveError("CHECKPOINT_PROVIDERS_MISSING")
    for key, digest in providers.items():
        _require_identity_text(key, "CHECKPOINT_PROVIDER_KEY")
        _require_sha(digest, "CHECKPOINT_PROVIDER")
    return dict(body), state


def validate_continuation_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Verify the self-digest and exact time/state joins of a stored chain manifest."""
    if not isinstance(manifest, Mapping):
        raise SegmentArchiveError("CONTINUATION_MANIFEST_INVALID")
    body = {key: value for key, value in manifest.items() if key != "continuation_sha256"}
    if (manifest.get("schema") != CONTINUATION_SCHEMA
            or manifest.get("status") != "CHAIN_VALIDATED_HASH_BOUND_NOT_EXECUTED"
            or manifest.get("continuation_sha256") != _digest(body)):
        raise SegmentArchiveError("CONTINUATION_MANIFEST_DIGEST_OR_STATUS_INVALID")
    segments = body.get("segments")
    joins = body.get("joins")
    if not isinstance(segments, list) or len(segments) < 2 or not isinstance(joins, list) or len(joins) != len(segments) - 1:
        raise SegmentArchiveError("CONTINUATION_MANIFEST_CARDINALITY_INVALID")

    def validate_segment_binding(segment: Mapping[str, Any]) -> None:
        binding = segment.get("binding")
        _require_sha(segment.get("binding_sha256"), "CONTINUATION_BINDING")
        if (not isinstance(binding, Mapping)
                or segment.get("binding_sha256") != _digest(binding)
                or binding.get("segment_id") != segment.get("segment_id")
                or binding.get("segment_manifest_sha256") != segment.get("manifest_sha256")
                or binding.get("trajectory_id") != segment.get("trajectory_id")
                or binding.get("support_id") != segment.get("support_id")
                or binding.get("start_time_s") != segment.get("start_time_s")
                or binding.get("end_time_s") != segment.get("end_time_s")
                or binding.get("start_state_sha256") != segment.get("start_state_sha256")
                or binding.get("end_state_sha256") != segment.get("end_state_sha256")):
            raise SegmentArchiveError("CONTINUATION_MANIFEST_BINDING_INVALID")
        try:
            SegmentBinding(**dict(binding))
        except (TypeError, ValueError) as exc:
            raise SegmentArchiveError("CONTINUATION_MANIFEST_BINDING_INVALID") from exc
        shared_identity = body.get("shared_identity")
        if (not isinstance(shared_identity, Mapping)
                or any(binding.get(name) != shared_identity.get(name)
                       for name in ("support_id", "grid_identity_sha256", "model_identity_sha256",
                                    "model_configuration_sha256", "configuration_sha256", "source_commit",
                                    "source_composite_sha256", "forcing_identity_sha256",
                                    "provider_identities", "resolution_factor"))):
            raise SegmentArchiveError("CONTINUATION_MANIFEST_SHARED_IDENTITY_MISMATCH")
        for name in ("segment_manifest_sha256", "grid_identity_sha256", "start_state_sha256",
                     "end_state_sha256", "model_identity_sha256", "model_configuration_sha256",
                     "configuration_sha256", "source_composite_sha256", "forcing_identity_sha256"):
            _require_sha(binding.get(name), f"CONTINUATION_BINDING_{name.upper()}")
        providers = binding.get("provider_identities")
        if not isinstance(providers, Mapping) or not providers:
            raise SegmentArchiveError("CONTINUATION_BINDING_PROVIDERS_MISSING")
        for provider_name, provider_digest in providers.items():
            _require_identity_text(provider_name, "CONTINUATION_PROVIDER_KEY")
            _require_sha(provider_digest, "CONTINUATION_PROVIDER")

    for segment in segments:
        if not isinstance(segment, Mapping):
            raise SegmentArchiveError("CONTINUATION_MANIFEST_SEGMENT_INVALID")
        validate_segment_binding(segment)
    for index, (left, join, right) in enumerate(zip(segments, joins, segments[1:])):
        if (not isinstance(left, Mapping) or not isinstance(right, Mapping)
                or not isinstance(join, Mapping)
                or join.get("after_segment_index") != index
                or left.get("end_time_s") != right.get("start_time_s")
                or left.get("end_state_sha256") != right.get("start_state_sha256")
                or join.get("time_s") != left.get("end_time_s")
                or join.get("checkpoint_state_sha256") != left.get("end_state_sha256")
                or join.get("from_manifest_sha256") != left.get("manifest_sha256")
                or join.get("to_manifest_sha256") != right.get("manifest_sha256")):
            raise SegmentArchiveError("CONTINUATION_MANIFEST_JOIN_INVALID")
        _require_sha(join.get("checkpoint_id"), "CONTINUATION_CHECKPOINT")
    return dict(manifest)


def write_continuation_manifest(path: str | Path, manifest: Mapping[str, Any]) -> str:
    validate_continuation_manifest(manifest)
    target = Path(path)
    raw = _canonical(manifest) + b"\n"
    try:
        with target.open("xb") as handle:
            if handle.write(raw) != len(raw):
                raise OSError("SHORT_CONTINUATION_MANIFEST_WRITE")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise SegmentArchiveError("CONTINUATION_MANIFEST_COLLISION") from exc
    return hashlib.sha256(raw).hexdigest()

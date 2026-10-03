"""Read-only adapter from the governed R6 T0 plate-rate realization.

This module binds the authored instantaneous T0 Euler-rate realization to a
WORLD_HISTORY ForcingRecord. It does not extrapolate rates over an interval,
rotate geometry, or advance a state.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping

import numpy as np

from .forcing import ForcingRecord
from .identity import BranchId, ForcingId, HistoryId, content_hash, verify_payload
from .provenance import ProvenanceRecord
from .repository_context import resolve_external_payload_path
from .state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
                    SupportClass, TimeSupport)

INITIAL_MANIFEST = "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json"
VECTOR_MANIFEST = "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"
KINEMATICS_PRIOR = "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json"
KINEMATICS_MANIFEST = "R6_T0_INITIAL_KINEMATICS_MANIFEST.json"
KINEMATICS_ARTIFACT = "R6_T0_CANONICAL_PLATE_KINEMATICS.json"
KINEMATICS_BINDING = "R6_INITIAL_PLATE_KINEMATICS_AND_RIFT_PARAMETER_AUTHORITY_BINDING.json"
KINEMATICS_EVIDENCE = "R6_PLATE_KINEMATICS_PARAMETER_EVIDENCE_MATRIX.json"
KINEMATICS_INTERFACE = "R6_PLATE_KINEMATICS_INTERFACE_CONTRACT.json"
BOUNDARY_CENSUS = "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json"
EVENT_GUARD = "R6_T0_FIRST_INTERVAL_EVENT_GUARD.json"
EVENT_CENSUS = "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json"
DT_LIMITS = "R6_FIRST_INTERVAL_DT_LIMIT_REGISTER.json"
STEPPING_CONTRACT = "R6_FIRST_INTERVAL_NUMERICAL_STEPPING_CONTRACT.json"
REPLAY_CONTRACT = "R6_FIRST_INTERVAL_SOLVER_REPLAY_CONTRACT.json"
PYGPLATES_REPORT = "R6_PYGPLATES_CANONICAL_MAPPING_REPORT.json"
PRE_ORBDATA_FEG = "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"
PRE_ORBDATA_RUNTIME = "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json"
B3_RESULT = "outputs/r6_world_history_b3_t0_ingest/B3_T0_INGEST_RESULT.json"
B3_STATES = "outputs/r6_world_history_b3_t0_ingest/B3_T0_STATE_INVENTORY.json"
B3_MANIFEST = "outputs/r6_world_history_b3_t0_ingest/B3_ARTIFACT_MANIFEST.json"
B4_BRANCH = "r6/b4-plate-kinematics-temporal-adapter"
GRID_ID = "R6_GLOBAL_GEOGRAPHY_1DEG_V1"
TIME_210 = TimeSupport("210Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT")

TRACKED_AUTHORITIES = (
    INITIAL_MANIFEST, VECTOR_MANIFEST, KINEMATICS_PRIOR, KINEMATICS_MANIFEST,
    KINEMATICS_ARTIFACT, KINEMATICS_BINDING, KINEMATICS_EVIDENCE,
    KINEMATICS_INTERFACE, BOUNDARY_CENSUS, EVENT_GUARD, EVENT_CENSUS,
    DT_LIMITS, STEPPING_CONTRACT, REPLAY_CONTRACT, PYGPLATES_REPORT,
    PRE_ORBDATA_FEG, PRE_ORBDATA_RUNTIME, B3_RESULT, B3_STATES, B3_MANIFEST,
)


class KinematicsAuthorityError(ValueError):
    """The source identity or declared kinematic support is invalid."""


class UnsupportedTemporalSupport(KinematicsAuthorityError):
    """The source does not govern the requested instant or interval."""


class UnknownPlateSupport(KinematicsAuthorityError):
    """A requested plate identity is absent from the governed source."""


class PlateGridMappingUnavailable(KinematicsAuthorityError):
    """No governed plate-to-grid-node mapping is available."""


class ReferenceFrameMismatch(KinematicsAuthorityError):
    """Requested and source reference frames differ."""


@dataclass(frozen=True, slots=True)
class GovernedPlateKinematics:
    repository_root: Path
    branch: str
    head: str
    history_id: str
    branch_id: str
    time_ma: float
    reference_frame: str
    authority_class: str
    canonical_identity_sha256: str
    artifact_sha256: str
    source_uncertainty: Mapping[str, Any]
    plates: tuple[Mapping[str, Any], ...]
    topology_plate_ids: tuple[int, ...]
    face_count: int
    boundary_count: int
    adjacent_pair_count: int
    source_refs: tuple[str, ...]
    payload_sources: tuple[Mapping[str, Any], ...]
    temporal_intervals: tuple[Mapping[str, Any], ...] = ()

    @property
    def plate_ids(self) -> tuple[int, ...]:
        return tuple(int(plate["plate_id"]) for plate in self.plates)


@dataclass(frozen=True, slots=True)
class B4Records:
    forcing: ForcingRecord
    source_provenance: ProvenanceRecord
    adapter_provenance: ProvenanceRecord
    index_state: DomainStateEnvelope
    driver_payload_identity_sha256: str


@dataclass(frozen=True, slots=True)
class SyntheticKinematicSegment:
    """Fixture-only segment descriptor; never read as R6 authority."""

    start_ma: float
    end_ma: float
    segment_id: str
    reference_frame: str
    plate_vectors_rad_per_year: Mapping[int, tuple[float, float, float]]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise KinematicsAuthorityError(f"cannot read authority JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise KinematicsAuthorityError(f"authority JSON must be an object: {path.name}")
    return value


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=False,
                            capture_output=True, text=True)
    if result.returncode:
        raise KinematicsAuthorityError(f"git identity query failed: {' '.join(args)}")
    return result.stdout.strip()


def _hash_file(path: Path) -> tuple[str, int, int]:
    digest = sha256()
    size = 0
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size, path.stat().st_mtime_ns


def _tracked_identity(root: Path, logical_path: str) -> dict[str, Any]:
    path = root / logical_path
    if not path.is_file():
        raise KinematicsAuthorityError(f"required tracked source missing: {logical_path}")
    expected = _git(root, "rev-parse", f"HEAD:{logical_path}")
    actual = _git(root, "hash-object", logical_path)
    if expected != actual:
        raise KinematicsAuthorityError(f"tracked authority differs from HEAD: {logical_path}")
    digest, size, mtime = _hash_file(path)
    return {"logical_path": logical_path, "role": "TRACKED_AUTHORITY_OR_EVIDENCE",
            "git_blob_sha1": expected, "sha256": digest, "byte_size": size,
            "mtime_ns_evidence_only": mtime}


def _verified_external(root: Path, stored_path: str, expected_sha: str,
                       expected_bytes: int, role: str,
                       logical_path: str) -> tuple[Path, dict[str, Any]]:
    path = resolve_external_payload_path(root, stored_path)
    if not path.is_file():
        raise KinematicsAuthorityError(f"governed payload unavailable: {role}")
    actual_sha, size, mtime = _hash_file(path)
    if actual_sha != expected_sha or size != expected_bytes:
        raise KinematicsAuthorityError(f"governed payload identity mismatch: {role}")
    verify_payload(f"sha256:{expected_sha}", path)
    logical = "external://" + logical_path.replace("\\", "/").lstrip("/")
    return path, {"logical_path": logical, "role": role, "sha256": actual_sha,
                  "byte_size": size, "mtime_ns_evidence_only": mtime,
                  "read_only_verified": True}


def _verify_b3_evidence(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    result = _read_json(root / B3_RESULT)
    state_inventory = _read_json(root / B3_STATES)
    manifest = _read_json(root / B3_MANIFEST)
    if result.get("decision") != "PASS_B3_GOVERNED_T0_READ_ONLY_INGEST":
        raise KinematicsAuthorityError("B3 evidence is not a passing T0 ingest")
    if "plate_kinematics" not in state_inventory.get("domains", []):
        raise KinematicsAuthorityError("B3 inventory has no plate_kinematics state")
    for row in manifest.get("artifacts", []):
        rel = str(row.get("relative_path", ""))
        if not rel or Path(rel).is_absolute():
            raise KinematicsAuthorityError("B3 manifest contains a non-portable path")
        artifact = ((root / B3_MANIFEST).parent / rel).resolve()
        if root.resolve() not in artifact.parents:
            raise KinematicsAuthorityError("B3 manifest artifact escapes repository root")
        if not artifact.is_file():
            raise KinematicsAuthorityError("B3 manifest artifact is missing")
        digest, size, _ = _hash_file(artifact)
        if digest != row.get("sha256") or size != row.get("byte_size"):
            raise KinematicsAuthorityError("B3 retained evidence hash mismatch")
    b3_manifest_hash, _, _ = _hash_file(root / B3_MANIFEST)
    return result, {"manifest_sha256": b3_manifest_hash,
                    "semantic_domains": state_inventory["domains"],
                    "source_commit": result.get("qualified_source_commit")}


def load_governed_source(repository_root: str | Path, *,
                         expected_branch: str = B4_BRANCH) -> tuple[GovernedPlateKinematics, dict[str, Any]]:
    """Read and verify only the current governed T0 kinematics/topology source set."""
    root = Path(repository_root).resolve()
    branch = _git(root, "branch", "--show-current")
    if branch != expected_branch:
        raise KinematicsAuthorityError(f"unexpected kinematics qualification branch: {branch}")
    head = _git(root, "rev-parse", "HEAD")
    docs = [_tracked_identity(root, name) for name in TRACKED_AUTHORITIES]
    initial = _read_json(root / INITIAL_MANIFEST)
    vector = _read_json(root / VECTOR_MANIFEST)
    kin_manifest = _read_json(root / KINEMATICS_MANIFEST)
    kin_path = root / KINEMATICS_ARTIFACT
    kin = _read_json(kin_path)
    prior = _read_json(root / KINEMATICS_PRIOR)
    binding = _read_json(root / KINEMATICS_BINDING)
    interface = _read_json(root / KINEMATICS_INTERFACE)
    census = _read_json(root / BOUNDARY_CENSUS)
    guard = _read_json(root / EVENT_GUARD)
    limits = _read_json(root / DT_LIMITS)
    stepping = _read_json(root / STEPPING_CONTRACT)
    pygplates = _read_json(root / PYGPLATES_REPORT)

    if initial.get("status") != "MATERIALIZED_AND_VALIDATED" or initial.get("time_ma") != 210.0:
        raise KinematicsAuthorityError("current initial-world T0 is not validated at 210 Ma")
    if initial.get("grid", {}).get("grid_id") != GRID_ID:
        raise KinematicsAuthorityError("unexpected T0 grid identity")
    if kin_manifest.get("status") != "CANONICAL_SYNTHETIC_MODEL_REALIZATION_MATERIALIZED__FIRST_INTERVAL_BLOCKED":
        raise KinematicsAuthorityError("kinematics manifest status changed; adjudication required")
    if kin_manifest.get("authority_class") != "STOCHASTIC_CANONICAL_MODEL_REALIZATION":
        raise KinematicsAuthorityError("unexpected T0 kinematics authority class")
    kin_body = dict(kin)
    declared_semantic_id = kin_body.pop("payload_identity_sha256", None)
    semantic_id = sha256((json.dumps(kin_body, sort_keys=True, ensure_ascii=False,
        indent=2, allow_nan=False) + "\n").encode("utf-8")).hexdigest()
    raw_sha, raw_size, raw_mtime = _hash_file(kin_path)
    if semantic_id != declared_semantic_id or semantic_id != kin_manifest.get("kinematics_sha256"):
        raise KinematicsAuthorityError("canonical kinematics semantic identity mismatch")
    verify_payload(f"sha256:{raw_sha}", kin_path)
    if kin.get("parent_canonical_t0_sha256") != initial["payload"]["sha256"]:
        raise KinematicsAuthorityError("kinematics does not bind current canonical T0")
    if kin.get("parent_vector_partition_sha256") != vector["payload"]["sha256"]:
        raise KinematicsAuthorityError("kinematics does not bind current vector partition")
    if (kin_manifest.get("time_ma") != initial["time_ma"]
            or vector.get("time_ma") != initial["time_ma"]):
        raise KinematicsAuthorityError("T0, topology and kinematics time anchors differ")
    reference_frame = str(kin_manifest.get("reference_frame", ""))
    if not reference_frame or kin.get("gauge", {}).get("name") != reference_frame:
        raise KinematicsAuthorityError("kinematics reference-frame declaration mismatch")

    parent_path, parent_file = _verified_external(root, initial["payload"]["relative_path"],
        initial["payload"]["sha256"], initial["payload"]["bytes"], "CANONICAL_T0_PHYSICAL_PAYLOAD",
        "r6/initial_world/" + Path(initial["payload"]["relative_path"]).name)
    vector_path, vector_file = _verified_external(root, vector["payload"]["path"],
        vector["payload"]["sha256"], vector["payload"]["bytes"], "T0_DERIVED_PLATE_PARTITION",
        "r6/tectonic_t0/R6_T0_VECTOR_PLATE_PARTITION.npz")
    with np.load(vector_path, allow_pickle=False) as archive:
        if "face_plate_id" not in archive or "face_vertex_latlon_deg" not in archive:
            raise KinematicsAuthorityError("vector payload lacks face plate/geometry support")
        face_plate_ids = tuple(int(value) for value in np.unique(archive["face_plate_id"]))
        face_count = int(archive["face_plate_id"].size)
    if face_count != vector["topology"]["face_count"]:
        raise KinematicsAuthorityError("vector payload face cardinality differs from manifest")
    if face_plate_ids != tuple(sorted(int(row["plate_id"]) for row in kin["plates"])):
        raise KinematicsAuthorityError("T0 kinematics plate IDs differ from canonical topology IDs")
    if len(face_plate_ids) != vector["topology"]["plate_count"]:
        raise KinematicsAuthorityError("T0 topology plate count differs from face plate IDs")
    plate_rows = tuple(sorted(kin["plates"], key=lambda row: int(row["plate_id"])))
    for row in plate_rows:
        vector3 = row.get("euler_vector_rad_per_year")
        if (not isinstance(vector3, list) or len(vector3) != 3
                or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in vector3)):
            raise KinematicsAuthorityError("plate Euler vector is malformed or non-finite")

    if (census.get("canonical_kinematics_sha256") != semantic_id
            or census.get("parent_vector_partition_sha256") != vector["payload"]["sha256"]):
        raise KinematicsAuthorityError("boundary kinematic census does not bind the current source pair")
    if guard.get("kinematics_manifest") != KINEMATICS_ARTIFACT:
        raise KinematicsAuthorityError("first-interval event guard source binding mismatch")
    if guard.get("positive_event_lead_time_lower_bound_ma") is not None:
        raise KinematicsAuthorityError("event guard now contains a lead-time bound; B4 review required")
    if prior.get("reference_frame", {}).get("name") != reference_frame:
        raise KinematicsAuthorityError("motion prior and canonical reference frames differ")
    if (binding.get("motion_segment_validity", {}).get("numerical_validity_limit") != "UNBOUND"
            or binding.get("motion_change_law", {}).get("status") != "BLOCKED"):
        raise KinematicsAuthorityError("motion validity/change authority changed; B4 review required")
    if interface.get("provider_status", {}).get("production_authorized") is not False:
        raise KinematicsAuthorityError("plate solver/tool status changed; B4 review required")
    if pygplates.get("production_authorized") is True:
        raise KinematicsAuthorityError("pyGPlates is now marked production-authorized; B4 review required")
    if stepping.get("authorization", {}).get("forward_evolution_executed") is not False:
        raise KinematicsAuthorityError("first-interval evolution state changed; B4 review required")
    b3_result, b3_info = _verify_b3_evidence(root)
    expected_parent = b3_result.get("qualified_source_commit")
    if expected_parent:
        ancestor = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor",
            expected_parent, head], check=False, capture_output=True, text=True)
        if ancestor.returncode != 0:
            raise KinematicsAuthorityError("B3 qualification source is not an ancestor of B4 HEAD")

    source_refs = tuple(sorted(
        f"artifact:{row['logical_path']}#sha256:{row['sha256']}" for row in docs
    ))
    payload_sources = (parent_file, vector_file,
        {"logical_path": KINEMATICS_ARTIFACT, "role": "GOVERNED_T0_KINEMATICS_RECORD",
         "sha256": raw_sha, "byte_size": raw_size, "mtime_ns_evidence_only": raw_mtime,
         "canonical_semantic_identity_sha256": semantic_id, "read_only_verified": True})
    source = GovernedPlateKinematics(
        repository_root=root, branch=branch, head=head,
        history_id=str(HistoryId(initial["history_id"])),
        branch_id=str(BranchId(initial["branch_id"])),
        time_ma=float(kin["time_ma"]), reference_frame=reference_frame,
        authority_class=str(kin["authority_class"]),
        canonical_identity_sha256=semantic_id, artifact_sha256=raw_sha,
        source_uncertainty=dict(kin.get("uncertainty", {})), plates=plate_rows,
        topology_plate_ids=face_plate_ids, face_count=face_count,
        boundary_count=int(vector["topology"]["positive_length_boundary_edge_count"]),
        adjacent_pair_count=int(vector["topology"]["positive_length_adjacency_pair_count"]),
        source_refs=source_refs, payload_sources=payload_sources, temporal_intervals=())
    inventory = {
        "branch": branch, "head": head, "tracked_authority_documents": docs,
        "payload_artifacts": list(payload_sources),
        "b3_qualification": b3_info,
        "kinematics": {"authority_class": source.authority_class,
            "semantic_identity_sha256": semantic_id, "artifact_sha256": raw_sha,
            "time_ma": source.time_ma, "reference_frame": reference_frame,
            "plate_ids": list(source.plate_ids), "uncertainty": dict(source.source_uncertainty),
            "temporal_interval_count": 0},
        "topology": {"authority_class": vector["authority_class"],
            "payload_sha256": vector["payload"]["sha256"], "face_count": face_count,
            "plate_ids_from_face_plate_id": list(face_plate_ids),
            "boundary_count": source.boundary_count,
            "adjacent_plate_pair_count": source.adjacent_pair_count,
            "boundary_semantics": "COARSE_SUPPORT_ON_FINE_GRID; boundary type/polarity not inferred"},
        "source_roles": {"canonical_plate_rates": "CANONICAL_SYNTHETIC_T0_MODEL_REALIZATION",
            "vector_partition": "MODEL_DERIVED_FROM_CANONICAL_T0",
            "pygplates": "CANDIDATE_PROCESSOR_NOT_SCIENTIFIC_AUTHORITY",
            "shellset_feg_runtime": "NUMERICAL_RUNTIME_SUPPORT_ONLY"},
    }
    inventory["_repository_root"] = str(root)
    inventory["_payload_paths_internal"] = {
        parent_file["logical_path"]: parent_path,
        vector_file["logical_path"]: vector_path,
    }
    return source, inventory


def _require_anchor_request(source: GovernedPlateKinematics, requested: TimeSupport,
                            requested_plate_ids: Iterable[int],
                            requested_reference_frame: str | None = None) -> tuple[int, ...]:
    if requested != TIME_210:
        raise UnsupportedTemporalSupport("the governed source supports only its exact 210 Ma instant anchor")
    if requested_reference_frame is not None and requested_reference_frame != source.reference_frame:
        raise ReferenceFrameMismatch("requested frame is not the governed synthetic T0 gauge")
    requested_ids = tuple(sorted(set(int(value) for value in requested_plate_ids)))
    unknown = sorted(set(requested_ids) - set(source.plate_ids))
    if unknown:
        raise UnknownPlateSupport(f"requested plate IDs are not governed: {unknown}")
    if not requested_ids:
        raise UnknownPlateSupport("empty plate support is not an evidenced motion field")
    return requested_ids


def require_plate_grid_mapping(mapping: Mapping[int, str] | None) -> Mapping[int, str]:
    """Reject absent node/cell to plate mapping; never substitute numerical owner."""
    if not mapping:
        raise PlateGridMappingUnavailable(
            "canonical node/grid-to-plate membership is not provided by the face partition")
    return mapping


def require_interval_coverage(source: GovernedPlateKinematics, start_ma: float,
                              end_ma: float) -> Mapping[str, Any]:
    """Return one source segment covering the interval, or fail closed."""
    if not math.isfinite(start_ma) or not math.isfinite(end_ma) or start_ma <= end_ma:
        raise UnsupportedTemporalSupport("interval must be finite and proceed older-to-younger")
    matches = [segment for segment in source.temporal_intervals
               if float(segment["start_ma"]) >= start_ma
               and float(segment["end_ma"]) <= end_ma]
    if len(matches) != 1:
        raise UnsupportedTemporalSupport(
            "no governed positive-duration plate-kinematics segment covers the requested interval")
    return matches[0]


def build_t0_records(source: GovernedPlateKinematics, *,
                     requested: TimeSupport = TIME_210,
                     requested_plate_ids: Iterable[int] | None = None,
                     requested_reference_frame: str | None = None) -> B4Records:
    """Create a deterministic instant-anchor forcing and query-link state."""
    ids = _require_anchor_request(source, requested,
        source.plate_ids if requested_plate_ids is None else requested_plate_ids,
        requested_reference_frame)
    vector_rows = [{"plate_id": int(row["plate_id"]),
                    "euler_vector_rad_per_year": [float(x) for x in row["euler_vector_rad_per_year"]]}
                   for row in source.plates if int(row["plate_id"]) in set(ids)]
    driver_payload = {"adapter_id": "R6_PLATE_KINEMATICS_T0_ANCHOR_ADAPTER_V1",
        "source_semantic_identity_sha256": source.canonical_identity_sha256,
        "source_artifact_sha256": source.artifact_sha256,
        "time_ma": source.time_ma, "reference_frame": source.reference_frame,
        "plate_ids": list(ids), "quantity": "PER_PLATE_EULER_ANGULAR_VELOCITY_VECTOR",
        "units": "rad/year", "vectors": vector_rows,
        "source_authority_class": source.authority_class,
        "source_uncertainty": dict(source.source_uncertainty),
        "temporal_validity": "EXACT_T0_INSTANT_ONLY; NO_POSITIVE_DURATION_INTERVAL_AUTHORIZED",
        "node_grid_mapping": "UNAVAILABLE; NO_PER_CELL_OR_NODE_ASSIGNMENT",
        "interpolation": "NONE", "geometry_transform_performed": False,
        "canonical_state_changed": False}
    driver_identity = content_hash(driver_payload)
    value = {"schema": "R6_PLATE_KINEMATICS_T0_ANCHOR_FORCING_V1",
        "driver_payload_identity_sha256": driver_identity, **driver_payload,
        "spatial_plate_support": {"selector": "WHOLE_GOVERNED_FACE_PLATE_ID_SET",
            "plate_ids": list(ids), "topology_face_count": source.face_count,
            "grid_or_mesh_node_membership": "NOT_PROVIDED"}}
    source_provenance = ProvenanceRecord.create(
        activity="R6_B4_BIND_GOVERNED_PLATE_KINEMATICS_T0_SOURCE",
        input_refs=(f"sha256:{source.artifact_sha256}",
                    f"payload://sha256/{source.canonical_identity_sha256}"),
        source_refs=source.source_refs,
        attributes={"source_authority_class": source.authority_class,
            "source_semantic_identity_sha256": source.canonical_identity_sha256,
            "time_ma": source.time_ma, "reference_frame": source.reference_frame,
            "read_only": True, "no_interval_extrapolation": True})
    forcing = ForcingRecord.create(
        history_id=source.history_id, branch_id=source.branch_id,
        forcing_kind="PLATE_KINEMATICS_T0_ANCHOR",
        domain="plate_kinematics", time_support=requested,
        spatial_support=SpatialSupport(None, (),
            f"{len(ids)} canonical face plate IDs; node/grid mapping unavailable", "GLOBAL"),
        support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY, value=value,
        provenance_ids=(str(source_provenance.record_id),), source_refs=source.source_refs)
    adapter_provenance = ProvenanceRecord.create(
        activity="R6_B4_PLATE_KINEMATICS_T0_ANCHOR_ADAPTER",
        input_refs=(str(forcing.forcing_id),), source_refs=source.source_refs,
        parent_provenance_ids=(str(source_provenance.record_id),),
        attributes={"adapter_id": "R6_PLATE_KINEMATICS_T0_ANCHOR_ADAPTER_V1",
            "driver_payload_identity_sha256": driver_identity,
            "temporal_support": requested.to_dict(), "canonical_state_changed": False,
            "forward_evolution": False})
    index_state = DomainStateEnvelope.create(
        history_id=source.history_id, branch_id=source.branch_id,
        domain="plate_kinematics_adapter_qualification", time_support=requested,
        spatial_support=SpatialSupport(None, (),
            f"{len(ids)} canonical face plate IDs; qualification reference only", "GLOBAL"),
        support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"record_role": "READ_ONLY_ADAPTER_QUALIFICATION_INDEX",
            "forcing_id": str(forcing.forcing_id), "driver_payload_identity_sha256": driver_identity,
            "source_kinematics_identity_sha256": source.canonical_identity_sha256,
            "canonical_state_changed": False, "not_a_T1_or_evolved_state": True},
        uncertainty={"source_class": source.authority_class,
            "source_uncertainty": dict(source.source_uncertainty),
            "positive_duration_validity": "UNKNOWN"},
        provenance_ids=(str(adapter_provenance.record_id),),
        model_derived=True)
    return B4Records(forcing, source_provenance, adapter_provenance,
                     index_state, driver_identity)


def validate_fixture_interval(start_ma: float, end_ma: float,
                              segments: Iterable[SyntheticKinematicSegment],
                              requested_plate_ids: Iterable[int],
                              requested_reference_frame: str) -> tuple[SyntheticKinematicSegment, ...]:
    """Validate fixture-only piecewise support without exposing it as R6 source."""
    if not math.isfinite(start_ma) or not math.isfinite(end_ma) or start_ma <= end_ma:
        raise UnsupportedTemporalSupport("fixture interval must proceed older-to-younger")
    ordered = tuple(sorted(segments, key=lambda item: -item.start_ma))
    if not ordered:
        raise UnsupportedTemporalSupport("fixture has no interval segment")
    plate_ids = set(int(value) for value in requested_plate_ids)
    covering = [segment for segment in ordered if segment.start_ma >= start_ma and segment.end_ma <= end_ma]
    if len(covering) != 1:
        raise UnsupportedTemporalSupport("request crosses a fixture regime boundary or lacks coverage")
    selected = covering[0]
    if requested_reference_frame != selected.reference_frame:
        raise ReferenceFrameMismatch("fixture request uses an incompatible reference frame")
    unknown = sorted(plate_ids - set(int(pid) for pid in selected.plate_vectors_rad_per_year))
    if unknown:
        raise UnknownPlateSupport(f"fixture plate IDs are UNKNOWN in selected regime: {unknown}")
    for plate_id in plate_ids:
        vector = selected.plate_vectors_rad_per_year[plate_id]
        if len(vector) != 3 or not all(math.isfinite(float(component)) for component in vector):
            raise KinematicsAuthorityError("fixture Euler vectors must contain three finite components")
    return (selected,)


def synthetic_fixture_forcing(segment: SyntheticKinematicSegment) -> ForcingRecord:
    """Build a deterministic FIXTURE_ONLY forcing for tests; never source from R6."""
    ids = tuple(sorted(int(value) for value in segment.plate_vectors_rad_per_year))
    value = {"fixture_only": True, "segment_id": segment.segment_id,
        "start_ma": segment.start_ma, "end_ma": segment.end_ma,
        "reference_frame": segment.reference_frame,
        "vectors_rad_per_year": [{"plate_id": pid,
            "vector": list(segment.plate_vectors_rad_per_year[pid])} for pid in ids]}
    return ForcingRecord.create(
        history_id=str(HistoryId.from_payload({"fixture": "b4", "history": 1})),
        branch_id=str(BranchId.from_payload({"fixture": "b4", "branch": 1})),
        forcing_kind="FIXTURE_ONLY_PLATE_KINEMATICS_INTERVAL",
        domain="plate_kinematics", time_support=TimeSupport(
            f"{segment.start_ma:g}Ma/{segment.end_ma:g}Ma",
            "FIXTURE_ONLY_OLDER_TO_YOUNGER", "INTERVAL"),
        spatial_support=SpatialSupport(None, (), f"fixture plate IDs {ids}", "GLOBAL"),
        support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY,
        value=value, source_refs=(f"fixture-only:{segment.segment_id}",))


def source_snapshot(inventory: Mapping[str, Any]) -> dict[str, tuple[str, int, int]]:
    """Return hashes for before/after source immutability comparison."""
    root = Path(str(inventory["_repository_root"]))
    result: dict[str, tuple[str, int, int]] = {}
    for row in inventory["tracked_authority_documents"]:
        result[str(row["logical_path"])] = _hash_file(root / str(row["logical_path"]))
    for row in inventory["payload_artifacts"]:
        logical = str(row["logical_path"])
        if logical.startswith("external://"):
            # Internal absolute paths stay out of serializable inventory rows.
            path = inventory["_payload_paths_internal"][logical]
        else:
            path = root / logical
        result[logical] = _hash_file(Path(path))
    return result

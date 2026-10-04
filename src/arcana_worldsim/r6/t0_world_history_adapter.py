"""Read-only adapter from governed R6 T0 references to WORLD_HISTORY records.

The adapter never invokes a producer or copies source payloads. Candidate and
numerical-runtime artifacts are audited but are not promoted to physical state.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

from .identity import BranchId, HistoryId, verify_payload
from .provenance import ProvenanceRecord
from .repository_context import external_root, resolve_external_payload_path
from .state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
                    SupportClass, TimeSupport)

INITIAL_MANIFEST = "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json"
VECTOR_MANIFEST = "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"
KINEMATICS_MANIFEST = "R6_T0_INITIAL_KINEMATICS_MANIFEST.json"
KINEMATICS_ARTIFACT = "R6_T0_CANONICAL_PLATE_KINEMATICS.json"
BPANGAEA_MANIFEST = "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json"
BPANGAEA_REPORT = "R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZATION_REPORT.json"
FEG_MANIFEST = "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"
RUNTIME_MANIFEST = "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json"
GRID_ID = "R6_GLOBAL_GEOGRAPHY_1DEG_V1"
T0_TIME = TimeSupport("210Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER", "INSTANT")

AUTHORITY_DOCUMENTS = (
    "R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json",
    INITIAL_MANIFEST,
    "R6_T0_AUTHORIAL_RATIFICATION_B_PANGAEA_LIKE_LATE_TRIASSIC.json",
    VECTOR_MANIFEST,
    "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json",
    KINEMATICS_MANIFEST,
    KINEMATICS_ARTIFACT,
    BPANGAEA_MANIFEST,
    BPANGAEA_REPORT,
    "R6_PRE_ORBDATA_HEAT_FLOW_ARCHITECTURE_CLOSURE.json",
    FEG_MANIFEST,
    RUNTIME_MANIFEST,
    "R6_PRE_ORBDATA_IMPLEMENTATION_REPORT.json",
    "R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json",
)


class T0AuthorityError(ValueError):
    """Current T0 authority is missing, inconsistent, or fails identity checks."""


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_file(path: Path) -> tuple[str, int, int]:
    digest = sha256()
    size = 0
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size, path.stat().st_mtime_ns


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(root), *args], check=True,
                               capture_output=True, text=True)
    return completed.stdout.strip()


def _tracked_identity(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        raise T0AuthorityError(f"required tracked authority document is missing: {relative}")
    expected_blob = _git(root, "rev-parse", f"HEAD:{relative}")
    actual_blob = _git(root, "hash-object", relative)
    if expected_blob != actual_blob:
        raise T0AuthorityError(f"tracked authority document differs from HEAD: {relative}")
    digest, size, mtime = _sha_file(path)
    return {"logical_path": relative, "role": "TRACKED_AUTHORITY_OR_EVIDENCE",
            "git_blob_sha1_expected": expected_blob, "git_blob_sha1_actual": actual_blob,
            "sha256_actual": digest, "byte_size": size, "mtime_ns_evidence_only": mtime}


def _external_identity(root: Path, stored_path: str, expected_sha: str,
                       expected_bytes: int | None, role: str) -> tuple[Path, dict[str, Any]]:
    path = resolve_external_payload_path(root, stored_path)
    ext = external_root(root).resolve()
    try:
        relative = path.resolve().relative_to(ext)
    except ValueError as exc:
        raise T0AuthorityError("external payload locator escapes configured external root") from exc
    if not path.is_file():
        raise T0AuthorityError(f"governed external payload is unavailable: external://{relative.as_posix()}")
    actual_sha, size, mtime = _sha_file(path)
    if actual_sha != expected_sha or (expected_bytes is not None and size != expected_bytes):
        raise T0AuthorityError(f"governed payload identity mismatch: external://{relative.as_posix()}")
    identity = verify_payload(f"payload://sha256/{expected_sha}", path)
    return path, {"logical_path": f"external://{relative.as_posix()}", "role": role,
                  "expected_sha256": expected_sha, "actual_sha256": actual_sha,
                  "verified_payload_identity": identity.to_dict(),
                  "expected_bytes": expected_bytes, "byte_size": size,
                  "mtime_ns_evidence_only": mtime, "read_only_verified": True}


def _tracked_payload(root: Path, relative: str, expected_sha: str, role: str) -> tuple[Path, dict[str, Any]]:
    path = root / relative
    if not path.is_file():
        raise T0AuthorityError(f"governed tracked payload is unavailable: {relative}")
    actual_sha, size, mtime = _sha_file(path)
    if actual_sha != expected_sha:
        raise T0AuthorityError(f"governed tracked payload identity mismatch: {relative}")
    identity = verify_payload(f"payload://sha256/{expected_sha}", path)
    return path, {"logical_path": relative, "role": role,
                  "expected_sha256": expected_sha, "actual_sha256": actual_sha,
                  "verified_payload_identity": identity.to_dict(),
                  "byte_size": size, "mtime_ns_evidence_only": mtime,
                  "read_only_verified": True}


def authority_inventory(root: str | Path, *,
                       expected_branch: str = "r6/b3-governed-t0-read-only-ingest"
                       ) -> dict[str, Any]:
    """Resolve and verify current T0 sources without opening a write-capable store."""
    root = Path(root).resolve()
    branch = _git(root, "branch", "--show-current")
    if branch != expected_branch:
        raise T0AuthorityError(f"unexpected branch for B3 qualification: {branch}")
    documents = [_tracked_identity(root, name) for name in AUTHORITY_DOCUMENTS]
    initial = _json(root / INITIAL_MANIFEST)
    vector = _json(root / VECTOR_MANIFEST)
    kin_manifest = _json(root / KINEMATICS_MANIFEST)
    kin = _json(root / KINEMATICS_ARTIFACT)
    b_manifest = _json(root / BPANGAEA_MANIFEST)
    b_report = _json(root / BPANGAEA_REPORT)
    feg = _json(root / FEG_MANIFEST)
    runtime = _json(root / RUNTIME_MANIFEST)

    if initial.get("status") != "MATERIALIZED_AND_VALIDATED" or initial.get("time_ma") != 210.0:
        raise T0AuthorityError("canonical initial-world manifest is not validated at T0")
    if initial.get("grid", {}).get("grid_id") != GRID_ID:
        raise T0AuthorityError("initial-world grid identity does not match governed R6 grid")
    initial_payload = initial["payload"]
    initial_path, initial_file = _external_identity(root, initial_payload["relative_path"],
        initial_payload["sha256"], initial_payload["bytes"], "CANONICAL_T0_PHYSICAL_PAYLOAD")

    if vector.get("authority_class") != "MODEL_DERIVED_FROM_CANONICAL_T0":
        raise T0AuthorityError("vector partition authority class differs from current manifest")
    vector_payload = vector["payload"]
    vector_path, vector_file = _external_identity(root, vector_payload["path"],
        vector_payload["sha256"], vector_payload["bytes"], "CANONICAL_T0_DERIVED_TOPOLOGY")
    if vector.get("canonical_parent_sha256") != initial_payload["sha256"]:
        raise T0AuthorityError("vector partition does not bind the current canonical T0 parent")

    kin_body = dict(kin)
    kin_identity = kin_body.pop("payload_identity_sha256", None)
    kin_canonical = sha256((json.dumps(kin_body, sort_keys=True, ensure_ascii=False,
        indent=2, allow_nan=False) + "\n").encode("utf-8")).hexdigest()
    if kin_identity != kin_canonical or kin_identity != kin_manifest.get("kinematics_sha256"):
        raise T0AuthorityError("canonical kinematics identity does not verify")
    if kin.get("parent_canonical_t0_sha256") != initial_payload["sha256"]:
        raise T0AuthorityError("kinematics does not bind current canonical T0 parent")
    if kin.get("parent_vector_partition_sha256") != vector_payload["sha256"]:
        raise T0AuthorityError("kinematics does not bind current vector partition")
    kin_raw_sha, kin_size, kin_mtime = _sha_file(root / KINEMATICS_ARTIFACT)
    kin_payload_identity = verify_payload(f"sha256:{kin_raw_sha}", root / KINEMATICS_ARTIFACT)
    kin_file = {"logical_path": KINEMATICS_ARTIFACT, "role": "CANONICAL_T0_KINEMATICS_RECORD",
        "expected_semantic_identity": kin_identity, "actual_semantic_identity": kin_canonical,
        "verified_payload_identity": kin_payload_identity.to_dict(),
        "actual_file_sha256": kin_raw_sha, "byte_size": kin_size,
        "mtime_ns_evidence_only": kin_mtime, "read_only_verified": True}

    # B-PANGAEA V2 is materialized, but its current manifest still says it is a
    # candidate. Preserve and report its identity without claiming canonical authority.
    if b_manifest.get("canonical_status") != "CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION":
        raise T0AuthorityError("B-PANGAEA V2 canonical status changed; review authority before B3")
    if b_report.get("canonical_status") != b_manifest.get("canonical_status"):
        raise T0AuthorityError("B-PANGAEA V2 manifest/report canonical statuses disagree")
    if b_manifest.get("field_package_sha256") != b_report.get("field_package_sha256"):
        raise T0AuthorityError("B-PANGAEA V2 field-package identities disagree")
    b_path, b_file = _tracked_payload(root, b_manifest["field_package_path"],
        b_manifest["field_package_sha256"], "AUTHORIAL_T0_CANDIDATE_NOT_PROMOTED")

    surface_ref = feg["source_authorities"]["surface_closed_package"]
    surface_path, surface_file = _tracked_payload(root, surface_ref["path"],
        surface_ref["sha256"], surface_ref["authority"])
    feg_path, feg_file = _tracked_payload(root, "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg",
        feg["production_feg"]["raw_sha256"], "NUMERICAL_DERIVED_FEG_RUNTIME_SUPPORT")
    runtime_ref = feg["source_authorities"]["runtime_package"]
    runtime_path, runtime_file = _tracked_payload(root, runtime_ref["path"],
        runtime_ref["sha256"], "NUMERICAL_RUNTIME_INPUT_ONLY")
    if runtime["runtime_data_sha256"] != runtime_ref["sha256"]:
        raise T0AuthorityError("runtime manifest does not bind the package bytes")
    if not all(value is False for value in feg.get("preserved_gates", {}).values()):
        raise T0AuthorityError("FEG source gate state differs; stop for authority review")
    for gate in ("PRE_ORBDATA_ready", "OrbData_authorized", "OrbData_executed",
                 "SHELLS_ready", "dt_selected", "forward_evolution_authorized", "t1_created"):
        if runtime.get("preserved_gates", {}).get(gate) is not False:
            raise T0AuthorityError(f"runtime package gate must remain false: {gate}")

    return {
        "branch": branch, "head": _git(root, "rev-parse", "HEAD"),
        "_repository_root": root,
        "tracked_authority_documents": documents,
        "payload_artifacts": [initial_file, vector_file, kin_file, b_file,
                               surface_file, feg_file, runtime_file],
        "source_paths_internal": {
            "canonical_initial_world": initial_path,
            "vector_partition": vector_path,
            "kinematics": root / KINEMATICS_ARTIFACT,
            "b_pangaea_candidate": b_path,
            "surface_closed_derived": surface_path,
            "feg_derived": feg_path,
            "runtime_derived": runtime_path,
        },
        "source_roles": {
            "canonical_initial_world": "CURRENT_T0_AUTHORITY",
            "vector_partition": "CURRENT_T0_DERIVED_TOPOLOGY_AUTHORITY",
            "kinematics": "CURRENT_CANONICAL_SYNTHETIC_T0_MODEL_REALIZATION",
            "b_pangaea_candidate": "AUTHORIAL_T0_CANDIDATE_NOT_CANONICAL; REVIEW_REQUIRED",
            "surface_closed_derived": "NUMERICAL_DERIVED_SUPPORT",
            "feg_derived": "NUMERICAL_RUNTIME_SUPPORT_ONLY",
            "runtime_derived": "NUMERICAL_RUNTIME_INPUT_ONLY",
        },
        "governance": {"runtime_authorized": False, "mechanics_authorized": False,
            "forward_evolution_authorized": False, "dt_selected": False,
            "t1_created": False, "canonical_state_changed": False},
    }


def build_records(root: str | Path, inventory: dict[str, Any]
                  ) -> tuple[tuple[DomainStateEnvelope, ...], ProvenanceRecord, dict[str, Any]]:
    """Build deterministic semantic records from validated manifests only."""
    root = Path(root).resolve()
    initial = _json(root / INITIAL_MANIFEST)
    vector = _json(root / VECTOR_MANIFEST)
    kin_manifest = _json(root / KINEMATICS_MANIFEST)
    kin_path = root / KINEMATICS_ARTIFACT
    kin_sha = _sha_file(kin_path)[0]
    history_id, branch_id = str(HistoryId(initial["history_id"])), str(BranchId(initial["branch_id"]))
    grid_shape = initial["grid"]["shape_lat_lon"]
    cell_deg = initial["grid"]["nominal_cell_size_deg"]
    resolution = (f"{int(cell_deg[0])} degree; {grid_shape[0]}x{grid_shape[1]}"
                  if cell_deg[0] == cell_deg[1] and float(cell_deg[0]).is_integer()
                  else f"{cell_deg[0]}x{cell_deg[1]} degree; {grid_shape[0]}x{grid_shape[1]}")
    grid = SpatialSupport(GRID_ID, (), resolution, "GRID")
    global_support = SpatialSupport(None, (), "12 canonical plate identities", "GLOBAL")
    parent_sha = initial["payload"]["sha256"]
    vector_sha = vector["payload"]["sha256"]
    parent_ref = f"sha256:{parent_sha}"
    vector_ref = f"payload://sha256/{vector_sha}"
    kin_ref = f"sha256:{kin_sha}"

    source_refs = tuple(sorted({
        f"artifact:{item['logical_path']}#sha256:{item['sha256_actual']}"
        for item in inventory["tracked_authority_documents"]
    } | {
        f"artifact:{item['logical_path']}#sha256:{item.get('actual_sha256', item.get('actual_file_sha256'))}"
        for item in inventory["payload_artifacts"]
    }))
    provenance = ProvenanceRecord.create(
        activity="R6_B3_GOVERNED_T0_READ_ONLY_WORLD_HISTORY_INGEST",
        input_refs=(parent_ref, vector_ref, kin_ref), source_refs=source_refs,
        attributes={"ingest_mode": "READ_ONLY_REFERENCE_ONLY",
            "source_authority": "ARCANA_CURRENT_GOVERNED_T0",
            "t0_time_ma": 210.0, "grid_id": GRID_ID,
            "payloads_copied_or_modified": False,
            "candidate_and_runtime_artifacts_promoted": False,
            "forward_evolution": False})
    provenance_id = str(provenance.record_id)
    support_fields = {
        "physical_geography": ("land_ocean_mask", "coastline_mask", "plate_id", "crust_class",
            "province_class", "land_surface_elevation_m"),
        "land_ocean": ("land_ocean_mask", "coastline_mask"),
        "province_state": ("plate_id", "crust_class", "boundary_class", "province_class"),
        "topography": ("land_surface_elevation_m", "elevation_support_mask",
            "synthetic_uncertainty_mask"),
    }
    states: list[DomainStateEnvelope] = []
    for domain, fields in support_fields.items():
        field_names = ({"land_ocean_mask": "land_ocean", "coastline_mask": "coastline",
            "plate_id": "plate_id", "crust_class": "crust_class",
            "province_class": "province_class", "land_surface_elevation_m": "land_surface_elevation"}
            if domain == "physical_geography" else {})
        refs = {field_names.get(name, name): f"payload://sha256/{parent_sha}#{name}" for name in fields}
        state_value = {"schema": "R6_INITIAL_DOMAIN_FIELD_REFERENCE_V1", "grid_id": GRID_ID,
            "time_ma": 210.0, "payload_sha256": parent_sha, "field_refs": refs}
        if domain == "physical_geography":
            state_value.update({"planet_specification_id": "R6_EARTH_SCALE_ANALOGUE_V1",
                                "generator_id": "ARCANA_R6_SUPERCONTINENT_GENERATOR_V1"})
        state = DomainStateEnvelope.create(history_id=history_id, branch_id=branch_id,
            domain=domain, time_support=T0_TIME, spatial_support=grid,
            support_class=SupportClass.DERIVED_SUPPORTED,
            authority_class=AuthorityClass.DERIVED_AUTHORITY,
            value=state_value,
            uncertainty={"classification": "AUTHORIAL_SYNTHETIC_INITIALIZATION",
                "no_empirical_210Ma_reconstruction_claim": True},
            provenance_ids=(provenance_id,), payload_ref=parent_ref)
        states.append(state)

    physical_parent = next(item for item in states if item.domain == "physical_geography")
    states.append(DomainStateEnvelope.create(history_id=history_id, branch_id=branch_id,
        domain="tectonic_plate_partition", time_support=T0_TIME, spatial_support=grid,
        support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"schema": "R6_T0_VECTOR_PARTITION_REFERENCE_V1", "payload_sha256": vector_sha,
            "plate_count": vector["topology"]["plate_count"],
            "parent_face_count": vector["topology"]["face_count"],
            "boundary_segment_count": vector["topology"]["positive_length_boundary_edge_count"],
            "adjacent_plate_pair_count": vector["topology"]["positive_length_adjacency_pair_count"],
            "support": vector["edge_semantics"]},
        uncertainty={"authority_class_source": vector["authority_class"]},
        provenance_ids=(provenance_id,), parent_state_ids=(str(physical_parent.state_id),),
        payload_ref=vector_ref))
    partition_state = states[-1]
    kin = _json(kin_path)
    states.append(DomainStateEnvelope.create(history_id=history_id, branch_id=branch_id,
        domain="plate_kinematics", time_support=T0_TIME, spatial_support=global_support,
        support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"schema": "R6_T0_KINEMATICS_REFERENCE_V1", "payload_sha256": kin_sha,
            "canonical_payload_identity_sha256": kin_manifest["kinematics_sha256"],
            "plate_count": kin_manifest["plate_count"], "time_ma": kin_manifest["time_ma"],
            "source_authority_class": kin["authority_class"],
            "topology_changed": kin["topology_changed"]},
        uncertainty={"classification": "SINGLE_STOCHASTIC_CANONICAL_MODEL_REALIZATION"},
        provenance_ids=(provenance_id,),
        parent_state_ids=(str(physical_parent.state_id), str(partition_state.state_id)),
        payload_ref=kin_ref))

    unknown_reasons = {
        "bathymetry": ("bathymetry_unknown_mask", "Numeric ocean depth is not authorized by the physical specification."),
        "tectonic_kinematics_grid": ("plate_motion_unknown_mask", "Grid-indexed motion is UNKNOWN; separately recorded plate-level kinematics are not cell values."),
        "boundary_classification": (None, "The initial province field distinguishes UNKNOWN and INTERIOR only; complete boundary classification remains unbound."),
        "deep": ("deep_unknown_mask", "No governed R6 Deep initializer/law package is bound."),
        "climate": ("climate_unknown_mask", "No T0 age-specific forcing or climate authority is bound."),
        "hydrology": ("hydrology_unknown_mask", "No hydrology initializer or compatible climate/water inputs are bound."),
        "weak_zone_state": (None, "Weak-zone state remains UNKNOWN in the current physical-domain authority map."),
        "junction_physical_semantics": (None, "Junction physical semantics remain unbound in current T0 authority."),
    }
    for domain, (mask_field, reason) in unknown_reasons.items():
        mask_ref = (None if mask_field is None else f"payload://sha256/{parent_sha}#{mask_field}")
        states.append(DomainStateEnvelope.create(history_id=history_id, branch_id=branch_id,
            domain=domain, time_support=T0_TIME, spatial_support=grid,
            support_class=SupportClass.UNKNOWN, authority_class=AuthorityClass.NONE, value=None,
            uncertainty={"status": "UNKNOWN", "reason": reason,
                "source_support_mask_reference": mask_ref,
                "mask_payload_is_not_a_numeric_state": True},
            provenance_ids=(provenance_id,)))

    if len({str(state.state_id) for state in states}) != len(states):
        raise T0AuthorityError("duplicate semantic state identity in B3 adapter output")
    info = {"history_id": history_id, "branch_id": branch_id,
        "time_support": T0_TIME.to_dict(), "grid_id": GRID_ID,
        "state_count": len(states), "domains": [state.domain for state in states],
        "state_authorities": {state.domain: {"support_class": state.support_class.value,
            "authority_class": state.authority_class.value,
            "payload_reference": state.payload_ref,
            "state_id": str(state.state_id)} for state in states},
        "payload_identities_are_separate_from_state_ids": True,
        "candidate_field_package_promoted": False}
    return tuple(states), provenance, info


def source_snapshot(inventory: dict[str, Any]) -> dict[str, tuple[str, int, int]]:
    """Hash the source set for before/after immutability; paths remain internal."""
    result = {}
    for key, path in inventory["source_paths_internal"].items():
        digest, size, mtime = _sha_file(path)
        result[key] = (digest, size, mtime)
    for item in inventory["tracked_authority_documents"]:
        digest, size, mtime = _sha_file(Path(inventory["_repository_root"]) / item["logical_path"])
        result[f"doc:{item['logical_path']}"] = (digest, size, mtime)
    return result

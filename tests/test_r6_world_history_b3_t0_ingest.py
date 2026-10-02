"""Small fixture-only tests for the B3 T0 record adapter."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from arcana_worldsim.r6.identity import BranchId, HistoryId
from arcana_worldsim.r6.state import SupportClass
from arcana_worldsim.r6.t0_world_history_adapter import (
    GRID_ID, KINEMATICS_ARTIFACT, KINEMATICS_MANIFEST, INITIAL_MANIFEST,
    VECTOR_MANIFEST, build_records,
)


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def test_b3_adapter_keeps_semantic_identity_separate_and_unknown_explicit(tmp_path: Path) -> None:
    root = tmp_path
    history = str(HistoryId.from_payload({"fixture": "b3-history"}))
    branch = str(BranchId.from_payload({"fixture": "b3-branch"}))
    parent_sha = "a" * 64
    vector_sha = "b" * 64
    kin_body = {"authority_class": "STOCHASTIC_CANONICAL_MODEL_REALIZATION",
                "time_ma": 210.0, "topology_changed": False,
                "parent_canonical_t0_sha256": parent_sha,
                "parent_vector_partition_sha256": vector_sha}
    kin_identity = sha256((json.dumps(kin_body, sort_keys=True, ensure_ascii=False,
        indent=2, allow_nan=False) + "\n").encode()).hexdigest()
    kin_artifact = {**kin_body, "payload_identity_sha256": kin_identity}
    _write(root / KINEMATICS_ARTIFACT, kin_artifact)
    _write(root / INITIAL_MANIFEST, {
        "history_id": history, "branch_id": branch, "time_ma": 210.0,
        "grid": {"grid_id": GRID_ID, "shape_lat_lon": [180, 360],
                 "nominal_cell_size_deg": [1.0, 1.0]},
        "canonical_initial_state_package_sha256": "c" * 64,
        "payload": {"sha256": parent_sha, "fields": []}})
    _write(root / VECTOR_MANIFEST, {
        "payload": {"sha256": vector_sha},
        "topology": {"plate_count": 12, "face_count": 64800,
            "positive_length_boundary_edge_count": 1983,
            "positive_length_adjacency_pair_count": 30},
        "edge_semantics": {"kind": "FIXTURE_ONLY"},
        "authority_class": "MODEL_DERIVED_FROM_CANONICAL_T0"})
    _write(root / KINEMATICS_MANIFEST, {"kinematics_sha256": kin_identity,
        "plate_count": 12, "time_ma": 210.0})
    source = {"logical_path": "fixture-authority.json", "sha256_actual": "d" * 64}
    payloads = [
        {"logical_path": "parent.npz", "actual_sha256": parent_sha},
        {"logical_path": "vector.npz", "actual_sha256": vector_sha},
        {"logical_path": KINEMATICS_ARTIFACT, "actual_file_sha256":
            sha256((root / KINEMATICS_ARTIFACT).read_bytes()).hexdigest()},
    ]
    inventory = {"tracked_authority_documents": [source], "payload_artifacts": payloads}

    states, provenance, info = build_records(root, inventory)
    repeated_states, repeated_provenance, _ = build_records(root, inventory)
    by_domain = {state.domain: state for state in states}
    assert info["grid_id"] == GRID_ID
    assert len(states) == 14
    assert len({str(state.state_id) for state in states}) == 14
    assert [str(state.state_id) for state in states] == [str(state.state_id) for state in repeated_states]
    assert provenance.record_id == repeated_provenance.record_id
    assert by_domain["physical_geography"].payload_ref == by_domain["topography"].payload_ref
    assert str(by_domain["physical_geography"].state_id) != parent_sha
    assert by_domain["bathymetry"].support_class is SupportClass.UNKNOWN
    assert by_domain["bathymetry"].value is None
    assert by_domain["bathymetry"].payload_ref is None
    assert by_domain["tectonic_kinematics_grid"].support_class is SupportClass.UNKNOWN
    assert by_domain["boundary_classification"].support_class is SupportClass.UNKNOWN
    assert "candidate_field_package_promoted" in info
    assert not info["candidate_field_package_promoted"]
    assert provenance.attributes["payloads_copied_or_modified"] is False

from __future__ import annotations

import json
import importlib.util
from pathlib import Path

from arcana_worldsim.r6.physical_boundary_accommodation import (
    adjudicate_boundary_accommodation, reconstruct_canonical_branches,
)

ROOT = Path(__file__).parents[1]


def _boundary_manifest():
    return json.loads((ROOT / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json").read_text(
        encoding="utf-8"))


def test_canonical_branch_graph_is_complete_stable_and_junction_bounded():
    manifest = _boundary_manifest()
    first = reconstruct_canonical_branches(manifest)
    second = reconstruct_canonical_branches(manifest)
    junction_vertices = {row["vertex_id"] for row in manifest["junctions"]}

    assert first == second
    assert len(first) == 30
    assert len({row.branch_id for row in first}) == 30
    assert len({row.section_id for row in first}) == 30
    assert len({row.plate_pair for row in first}) == 30
    assert sum(len(row.boundary_ids) for row in first) == 1983
    assert len({edge for row in first for edge in row.boundary_ids}) == 1983
    assert all(row.start_vertex_id in junction_vertices for row in first)
    assert all(row.end_vertex_id in junction_vertices for row in first)
    assert all(row.section_boundary_reason.endswith("CANONICAL_JUNCTIONS") for row in first)
    assert all(row.support == "COARSE_SUPPORT_ON_FINE_GRID" for row in first)


def test_report_separates_kinematic_demand_from_accommodation_and_events():
    report = adjudicate_boundary_accommodation(ROOT)
    assert report["decision"] == "R6_BOUNDARY_ACCOMMODATION_NOT_ESTABLISHED__RESEARCH_REQUIRED"
    assert report["canonical_topology"] == {
        "plate_count": 12, "parent_face_count": 64800,
        "boundary_segment_count": 1983, "adjacent_plate_pair_count": 30,
        "degree3_junction_count": 20, "graph_integrity": "PASS",
        "support": "COARSE_SUPPORT_ON_FINE_GRID"}
    assert report["canonical_boundary_graph"]["branch_count"] == 30
    assert report["canonical_boundary_graph"]["section_count"] == 30
    assert report["relative_motion"]["segments_with_resolved_normal_and_tangent"] == 1983
    assert report["relative_motion"]["segments_unresolved"] == 0
    assert report["accommodation_law"]["status"] == "NOT_ESTABLISHED"
    assert report["accommodation_law"]["positive_physical_accommodation_sections"] == 0
    assert report["accommodation_law"]["sections_with_authority_gap"] == 30
    assert report["junctions"]["outcome_counts"] == {
        "JUNCTION_COMPATIBLE": 0, "JUNCTION_UNDERDETERMINED": 0,
        "JUNCTION_INCOMPATIBLE": 0, "JUNCTION_AUTHORITY_GAP": 20}
    assert report["research_gate"]["external_scientific_research_required"] is True
    assert report["readiness"]["first_interval_contract_design_authorized"] is False
    assert all(value is False for value in report["invariants"].values())


def test_pure_plate_anchors_are_not_fabricated_and_patch_failure_is_reproduced():
    report = adjudicate_boundary_accommodation(ROOT)
    anchors = report["pure_plate_anchors"]
    assert anchors["validated_anchor_count"] == 0
    assert anchors["required_section_side_slots"] == 60
    assert anchors["unresolved_anchor_slots"] == 60

    patch = report["patch_operator"]
    assert patch["status"] == "OVERLAP_DERIVED_PATCH_BOUNDARY_DIRICHLET_INCOMPATIBLE"
    assert patch["replacement_established"] is False
    widths = {row["diagnostic_width_m"]: row for row in patch["old_operator_cause"]["diagnostic_width_cases"]}
    assert widths[250000]["junction_outcomes"]["CORNER_DIRICHLET_CONFLICT"] == 10
    assert widths[500000]["junction_outcomes"]["CORNER_DIRICHLET_CONFLICT"] == 10
    assert widths[100000]["patches_constructed"] == 0
    assert any("PORT_EXTRACTION_IMPLEMENTATION_FAILURE" in reason
               for reason in widths[100000]["failure_reasons"])


def test_generated_json_report_preserves_parent_t0_and_bootstrap_identity():
    report = json.loads((ROOT / "R6_PHYSICAL_BOUNDARY_ACCOMMODATION_REPORT.json").read_text(
        encoding="utf-8"))
    assert report["parent"]["commit"] == "f327a317bc8650df3abcfe5a5e9924eebafbe427"
    assert report["t0_invariants"]["world_history_state_id_unchanged"] is True
    assert report["t0_invariants"]["historical_bootstrap_identity"] == (
        "27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf")
    assert report["invariants"]["canonical_payload_changed"] is False
    assert report["invariants"]["t0_state_mutated"] is False


def test_pair_order_reversal_preserves_normal_demand_and_reverses_tangent_sign():
    script = ROOT / "scripts" / "r6_bind_shared_boundary_topology_contact.py"
    spec = importlib.util.spec_from_file_location("r6_topology_contact_frame", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    delta_v = [0.4, -0.2, 0.3]
    normal_ab = [0.0, 1.0, 0.0]
    tangent = [1.0, 0.0, 0.0]
    normal_ab_value, tangent_value = module.decompose_relative_velocity(
        delta_v, normal_ab, tangent)
    normal_ba_value, tangent_ba_value = module.decompose_relative_velocity(
        [-component for component in delta_v],
        [-component for component in normal_ab], tangent)

    assert normal_ba_value == normal_ab_value
    assert tangent_ba_value == -tangent_value

"""R6 T0 source handoff: uses synthetic test-only packets, not original FAIR."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from experiments.plate58_deforming_explore_v1 import g2_g3_source_to_coupled_handoff as h
from experiments.plate58_deforming_explore_v1 import g2_g3_physical_source_packet as packet
from test_r6_g2_g3_physical_source_packet import fixture


def packets(tmp_path):
    source_root = tmp_path / "src_repo"
    source_root.mkdir()
    result = {}
    for extent in (8, 16):
        d = tmp_path / ("fair_" + str(extent))
        f = fixture(extent, parent_34587_in_8=(extent == 8))
        index, proposal = packet.create_packet(**f)
        packet.write_once(source_root, d, index, proposal)
        result[extent] = d
    return source_root, result[8], result[16]


def test_pair_builds_two_exact_parent_scenarios_and_never_a_solve(tmp_path):
    root, p8, p16 = packets(tmp_path)
    a, b, audit = h.compile_pair(p8, p16)
    assert a["schema"] == h.CANDIDATE_SCHEMA
    assert a["authoring_template_unselected"] is True
    assert a["source_parent_34587_in_footprint"] is True
    assert a["source_actual_3plus_plate_junctions"] == []
    assert b["source_actual_3plus_plate_junctions"] == [
        {"parent_node_id": 34587, "incident_plates": [5, 8, 11]}]
    for item, n_nodes, n_cuts, n_ext in ((a, 81, 32, 120), (b, 289, 64, 504)):
        assert len(item["candidate_material_by_parent_node"]) == n_nodes
        assert len(item["velocity_en_by_parent_node"]) == n_nodes
        assert len(item["line_tractions_by_edge"]) == n_cuts
        assert len(item["basal_tractions_by_triangle"]) == n_ext
        assert set(item["source_manifest_sha256"]) == {
            "multiscale", "interface", "nodal", "force"}
        assert all(v is None for v in item["candidate_material_by_parent_node"].values())
        assert all(v is None for v in item["line_tractions_by_edge"].values())
        assert item["core_basal_tractions_by_triangle"] is None
        assert item["external_gpe"] is None
        assert item["physical_T1"] is None
        assert item["mechanical_solve_authorized"] is False
        json.dumps(item, allow_nan=False)
    assert audit["material_assignments"] == audit["qualified_traction_inputs"] == 0
    assert len(audit["unresolved_physical_groups"]) == 8
    assert audit["WORLD_HISTORY_PRODUCTION_AUTHORIZED"] is False
    assert audit["mechanical_solver_runs"] == 0
    assert audit["physical_T1"] is None
    assert h.compile_pair(p8, p16) == (a, b, audit)


def test_handoff_writes_once_external_receipt_with_real_hashes(tmp_path):
    root, p8, p16 = packets(tmp_path)
    a, b, audit = h.compile_pair(p8, p16)
    output = tmp_path / "immutable_external_evidence"
    manifest = h.write_once(root, output, {
        "SCENARIO_8X8_UNSELECTED.json": a,
        "SCENARIO_16X16_UNSELECTED.json": b,
        "AUDIT.json": audit,
    })
    assert manifest["physical_T1"] is None
    assert manifest["WORLD_HISTORY_PRODUCTION_AUTHORIZED"] is False
    assert manifest["no_physical_solver_run"] is True
    for name, sha in manifest["files"].items():
        assert h.sha256(output / name) == sha
    with pytest.raises(h.PhysicalHandoffError, match="ALREADY_EXISTS"):
        h.write_once(root, output, {
            "SCENARIO_8X8_UNSELECTED.json": a,
            "SCENARIO_16X16_UNSELECTED.json": b,
            "AUDIT.json": audit,
        })


def test_handoff_refuses_repository_path(tmp_path):
    root, p8, p16 = packets(tmp_path)
    a, b, audit = h.compile_pair(p8, p16)
    with pytest.raises(h.PhysicalHandoffError, match="OUTSIDE_REPOSITORY"):
        h.write_once(root, root / "unwanted", {
            "SCENARIO_8X8_UNSELECTED.json": a,
            "SCENARIO_16X16_UNSELECTED.json": b,
            "AUDIT.json": audit,
        })


@pytest.mark.parametrize("attack", [
    "manifest_hash", "manifest_authority", "source_index_bytes",
    "proposal_faked_water", "proposal_faked_cut_traction", "source_index_16_wrong_extent",
    "same_regional_original_PRE_sha", "mismatched_upstream_manifest",
])
def test_fails_closed_on_sha_or_authority_tampering(tmp_path, attack):
    root, p8, p16 = packets(tmp_path)
    path = p8
    if attack == "manifest_hash":
        name = path / "MANIFEST.json"
        row = json.loads(name.read_text())
        row["files"]["SOURCE_INDEX.json"] = "f"*64
        name.write_text(json.dumps(row))
    elif attack == "manifest_authority":
        name = path / "MANIFEST.json"
        row = json.loads(name.read_text())
        row["physical_solve_authorized"] = True
        name.write_text(json.dumps(row))
    elif attack == "source_index_bytes":
        with (path / "SOURCE_INDEX.json").open("a") as f:
            f.write(" \n")
    elif attack == "proposal_faked_water":
        name = path / "UNSELECTED_PHYSICAL_PROPOSAL.json"
        row = json.loads(name.read_text())
        key = next(iter(row["water_effective_pressure_by_parent_node"]))
        row["water_effective_pressure_by_parent_node"][key] = {"pore_pressure_pa": 0}
        name.write_text(json.dumps(row))
    elif attack == "proposal_faked_cut_traction":
        name = path / "UNSELECTED_PHYSICAL_PROPOSAL.json"
        row = json.loads(name.read_text())
        key = next(iter(row["outer_cut_physical_traction_N_per_m"]))
        row["outer_cut_physical_traction_N_per_m"][key] = [0, 0, 0]
        name.write_text(json.dumps(row))
    else:
        name = p16 / "SOURCE_INDEX.json"
        row = json.loads(name.read_text())
        if attack == "source_index_16_wrong_extent":
            row["extent_cells"] = 8
        elif attack == "same_regional_original_PRE_sha":
            row["source_hashes"]["original_PRE_sha256"] = (
                json.loads((p8 / "SOURCE_INDEX.json").read_text())
                ["source_hashes"]["original_PRE_sha256"])
        else:
            row["source_hashes"]["interface_manifest_sha256"] = "f"*64
        name.write_text(json.dumps(row))
    with pytest.raises((h.PhysicalHandoffError, packet.PhysicalSourcePacketError)):
        h.compile_pair(p8, p16)


@pytest.mark.parametrize("attack", [
    "material", "traction", "GPE", "authoring_flag", "source_sha",
    "missing_nodes", "fake_physical_T1", "fake_core_basals", "noncanonical",
])
def test_generated_handoff_rejects_unsourced_physics_mutation(tmp_path, attack):
    _, p8, p16 = packets(tmp_path)
    a, _, _ = h.compile_pair(p8, p16)
    idx, _, _ = h.load_packet(p8, 8)
    altered = copy.deepcopy(a)
    if attack == "material":
        k = next(iter(altered["candidate_material_by_parent_node"]))
        altered["candidate_material_by_parent_node"][k] = {"rock": "olivine"}
    elif attack == "traction":
        k = next(iter(altered["line_tractions_by_edge"]))
        altered["line_tractions_by_edge"][k] = [0,0,0]
    elif attack == "GPE":
        altered["external_gpe"] = {"pressure":0}
    elif attack == "authoring_flag":
        altered["authoring_template_unselected"] = False
    elif attack == "source_sha":
        altered["source_manifest_sha256"]["force"] = "f"*64
    elif attack == "missing_nodes":
        altered["velocity_en_by_parent_node"].pop(next(iter(altered["velocity_en_by_parent_node"])))
    elif attack == "fake_physical_T1":
        altered["physical_T1"] = {"year": 100}
    elif attack == "fake_core_basals":
        altered["core_basal_tractions_by_triangle"] = {"123": 0}
    elif attack == "noncanonical":
        altered["D_024"] = "RETIRED"
    with pytest.raises(h.PhysicalHandoffError):
        h.verify_candidate(idx, altered)

"""Original T0 source-packet -> G2/G3 coupled-engineering authoring handoff.

Reads the exact FAIR 8x8 / 16x16 source packet receipts, checks the SHA256
files and four-manifest cross-extent provenance, and prepares TWO deliberately
UNSELECTED input documents keyed to all original mechanical support IDs.

This is a real integration adapter to the existing G2/G3 full-parent input
schema, NOT a physics material calibration, force model, fault solve, T1
integration, WorldHistory record, or authorization. It never guesses zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from experiments.plate58_deforming_explore_v1.g2_g3_physical_source_packet import (
    SCHEMA as SOURCE_SCHEMA,
    verify_unselected,
    verify_cross_extent_provider_chain,
    content_sha,
)

SCHEMA = "ARCANA_R6_G2_G3_SOURCE_TO_COUPLED_AUTHORING_HANDOFF_V1"
CANDIDATE_SCHEMA = "ARCANA_R6_G2_G3_EXPLICIT_FULL_PARENT_ENGINEERING_INPUT_V1"
STATUS = "T0_SOURCE_AUTHENTIC_TO_COUPLED_INPUTS_MAPPED__PHYSICAL_PARAMETERS_UNKNOWN"
SCOPE = {8: (81, 128, 8, 120, 32), 16: (289, 512, 8, 504, 64)}
SOURCE_FILENAMES = ("SOURCE_INDEX.json", "UNSELECTED_PHYSICAL_PROPOSAL.json")
GROUP_NAMES = (
    "g2_material_and_phases", "g2_pressure_water", "g2_lab_law_and_coverage",
    "g3_outer_cut", "g3_full_basal", "g3_gpe", "interface_fault",
    "solver_compatibility",
)


class PhysicalHandoffError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise PhysicalHandoffError(code)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_packet(folder: Path, extent: int) -> tuple[dict, dict, dict]:
    """Check both output file hashes; this is *not* independent T0 re-ingest.

    Source-side FEG/PRE authentication was performed by the original source
    packet FAIR runner. Caller supplies that immutable evidence directory.
    """
    folder = Path(folder)
    manifest = json.loads((folder / "MANIFEST.json").read_text())
    require(manifest.get("schema") ==
            "ARCANA_R6_G2_G3_PHYSICAL_SUPPORT_PACKET_MANIFEST_V1"
            and set(manifest.get("files", {})) == set(SOURCE_FILENAMES)
            and manifest.get("status") ==
            "SOURCE_AUTHENTIC_SUPPORT__PHYSICAL_INPUTS_UNSELECTED_NO_SOLVE"
            and manifest.get("physical_T1") is None
            and manifest.get("physical_solve_authorized") is False
            and manifest.get("HistoryStore_mutations") == 0
            and manifest.get("D_024") == "ACTIVE",
            "G2G3_HANDOFF_UPSTREAM_MANIFEST_AUTHORITY_INVALID")
    for name, digest in manifest["files"].items():
        require(type(digest) is str and len(digest) == 64
                and sha256(folder / name) == digest,
                "G2G3_HANDOFF_SOURCE_PACKET_HASH_DRIFT:" + name)
    index = json.loads((folder / SOURCE_FILENAMES[0]).read_text())
    proposal = json.loads((folder / SOURCE_FILENAMES[1]).read_text())
    verify_unselected(index, proposal)
    require(index["schema"] == SOURCE_SCHEMA
            and index.get("extent_cells") == extent
            and manifest["source_original_FEG_sha256"] ==
            index["source_hashes"]["original_FEG_sha256"]
            and manifest["source_original_PRE_sha256"] ==
            index["source_hashes"]["original_PRE_sha256"]
            and proposal.get("source_index_sha256") == content_sha(index),
            "G2G3_HANDOFF_PACKET_INDEX_OR_SOURCE_MISMATCH")
    count = index["counts"]
    need = SCOPE[extent]
    require(tuple(count[k] for k in (
        "original_parent_nodes", "source_original_full_basal_triangles",
        "source_core_basal_triangles", "source_exterior_basal_triangles",
        "original_external_cut_edges")) == need,
        "G2G3_HANDOFF_SOURCE_COUNTS_INVALID")
    return index, proposal, {
        "evidence_manifest_sha256": sha256(folder / "MANIFEST.json"),
        "source_index_sha256": manifest["files"][SOURCE_FILENAMES[0]],
        "proposal_file_sha256": manifest["files"][SOURCE_FILENAMES[1]],
    }


def create_candidate(index: dict, proposal: dict, receipt: dict) -> dict:
    """Construct exact *existing* full-parent input field names, all null.

    The unselected flag explicitly prevents direct use by the coupled runner.
    A future source-qualified candidate compiler must produce a NEW, separately
    authorized record; deleting the flag alone never creates real physics.
    """
    extent = index["extent_cells"]
    require(extent in SCOPE and proposal["source_index_sha256"] == content_sha(index),
            "G2G3_HANDOFF_SOURCE_INDEX_INVALID")
    parents = index["original_parent_node_order"]
    core = index["source_original_core_triangle_ids"]
    outer = index["source_original_exterior_triangle_ids"]
    cut = [e["source_edge_id"] for e in index["source_external_cut_edges"]]
    facets = set(index["source_original_full_basal_triangle_nodes"])
    require(len(parents) == SCOPE[extent][0]
            and len(core) == SCOPE[extent][2]
            and len(outer) == SCOPE[extent][3]
            and len(cut) == SCOPE[extent][4]
            and len(facets) == SCOPE[extent][1]
            and {str(t) for t in core + outer} == facets
            and len(set(cut)) == len(cut),
            "G2G3_HANDOFF_EXACT_FULL_DOMAIN_SUPPORT_REQUIRED")
    exact = {
        "material_rock_phase_by_parent_node": {str(n) for n in parents},
        "water_effective_pressure_by_parent_node": {str(n) for n in parents},
        "constitutive_law_and_lab_validity_by_parent_node": {str(n) for n in parents},
        "outer_cut_physical_traction_N_per_m": set(cut),
        "full_basal_tangential_normal_load_Pa": facets,
    }
    for key, required in exact.items():
        rows = proposal.get(key)
        require(isinstance(rows, dict) and set(rows) == required
                and all(v is None for v in rows.values()),
                "G2G3_HANDOFF_UNSELECTED_PHYSICAL_SOURCE_TAMPERED:" + key)
    manifests = index["source_hashes"]
    source_manifest = {
        name: manifests[name + "_manifest_sha256"]
        for name in ("multiscale", "interface", "nodal", "force")
    }
    require(len(receipt["source_index_sha256"]) == 64,
            "G2G3_HANDOFF_SOURCE_RECEIPT_REQUIRED")
    # Legacy coupled runner accepts the *field layout* but this document is
    # deliberately invalid for assembly: authors have not selected law/data.
    return {
        "schema": CANDIDATE_SCHEMA,
        "authority": "ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
        "authoring_template_unselected": True,
        "source_packet_index_sha256": content_sha(index),
        "source_packet_report_file_sha256": receipt["source_index_sha256"],
        "source_packet_manifest_sha256": receipt["evidence_manifest_sha256"],
        "scope_extent_cells": extent,
        "source_manifest_sha256": source_manifest,
        "source_original_FEG_sha256": manifests["original_FEG_sha256"],
        "source_original_PRE_sha256": manifests["original_PRE_sha256"],
        "source_parent_34587_in_footprint":
            index["source_parent_34587_present_in_footprint"],
        "source_actual_3plus_plate_junctions":
            index["source_actual_3plus_plate_junctions"],
        "source_original_full_parent_node_order": parents,
        "source_original_core_triangle_ids": core,
        "source_original_exterior_triangle_ids": outer,
        "source_original_cut_edge_ids": cut,
        "physical_source_authority_ratified": False,
        "mechanical_solve_authorized": False,
        "core_external_force_provider_qualified": False,
        "fault_interface_physics_authorized": False,
        "candidate_material_by_parent_node": {str(n): None for n in parents},
        "velocity_en_by_parent_node": {str(n): None for n in parents},
        "line_tractions_by_edge": {key: None for key in cut},
        "basal_tractions_by_triangle": {str(n): None for n in outer},
        "core_basal_tractions_by_triangle": None,
        "core_gpe_increment_by_parent_node": None,
        "external_gpe": None,
        "additional_required_physics": {
            "actual_source_rock_phase_water_effective_pressure": None,
            "crust_mantle_creep_brittle_law_and_lab_PT_rate_coverage": None,
            "normal_basal_support_and_mechanical_LAB": None,
            "independent_mantle_flow_and_complete_source_tractions": None,
            "full_GPE_vertical_reference_and_unique_owner": None,
            "true_fault_sidedness_rate_friction_and_junction_law": None,
            "nonlinear_solver_rank_force_energy_restart_qualification": None,
        },
        "physical_T1": None,
        "HistoryStore_modified": False,
        "canonical_history_created": False,
        "D_024": "ACTIVE",
    }


def verify_candidate(index: dict, candidate: dict) -> None:
    """No submitted fields may quietly replace an unselected slot by 0."""
    require(candidate.get("schema") == CANDIDATE_SCHEMA
            and candidate.get("authoring_template_unselected") is True
            and candidate.get("scope_extent_cells") == index["extent_cells"]
            and candidate.get("source_packet_index_sha256") == content_sha(index)
            and candidate.get("physical_source_authority_ratified") is False
            and candidate.get("mechanical_solve_authorized") is False
            and candidate.get("core_external_force_provider_qualified") is False
            and candidate.get("fault_interface_physics_authorized") is False
            and candidate.get("physical_T1") is None
            and candidate.get("HistoryStore_modified") is False
            and candidate.get("canonical_history_created") is False
            and candidate.get("D_024") == "ACTIVE",
            "G2G3_HANDOFF_AUTHORITY_OR_SOURCE_DRIFT")
    expected = {
        "candidate_material_by_parent_node": set(map(str,index["original_parent_node_order"])),
        "velocity_en_by_parent_node": set(map(str,index["original_parent_node_order"])),
        "line_tractions_by_edge": {e["source_edge_id"] for e in index["source_external_cut_edges"]},
        "basal_tractions_by_triangle": set(map(str,index["source_original_exterior_triangle_ids"])),
    }
    for key, ids in expected.items():
        value = candidate.get(key)
        require(type(value) is dict and set(value) == ids
                and all(v is None for v in value.values()),
                "G2G3_HANDOFF_NO_SILENT_VALUE_OR_MISSING_KEY:" + key)
    for key in ("core_basal_tractions_by_triangle",
                "core_gpe_increment_by_parent_node", "external_gpe"):
        require(candidate.get(key, "__missing__") is None,
                "G2G3_HANDOFF_NO_UNQUALIFIED_FORCE:" + key)
    additional = candidate.get("additional_required_physics")
    require(type(additional) is dict and len(additional) == 7
            and all(v is None for v in additional.values()),
            "G2G3_HANDOFF_INDEPENDENT_PHYSICAL_GAPS_NOT_RESOLVED")
    hashes = index["source_hashes"]
    require(candidate.get("source_manifest_sha256") == {
        n: hashes[n + "_manifest_sha256"]
        for n in ("multiscale", "interface", "nodal", "force")}
        and candidate.get("source_original_FEG_sha256") == hashes["original_FEG_sha256"]
        and candidate.get("source_original_PRE_sha256") == hashes["original_PRE_sha256"],
        "G2G3_HANDOFF_ORIGINAL_PROVENANCE_CHANGED")


def compile_pair(folder8: Path, folder16: Path) -> tuple[dict, dict, dict]:
    index8, proposal8, receipt8 = load_packet(folder8, 8)
    index16, proposal16, receipt16 = load_packet(folder16, 16)
    verify_cross_extent_provider_chain(index8, index16)
    a = create_candidate(index8, proposal8, receipt8)
    b = create_candidate(index16, proposal16, receipt16)
    verify_candidate(index8, a)
    verify_candidate(index16, b)
    audit = {
        "schema": SCHEMA,
        "decision": STATUS,
        "physical_parameterization_status": "EIGHT_SOURCE_AUTHORITY_GAPS_REMAIN",
        "source_original_8x8_index_sha256": receipt8["source_index_sha256"],
        "source_original_16x16_index_sha256": receipt16["source_index_sha256"],
        "source_8x8_packet_manifest_sha256": receipt8["evidence_manifest_sha256"],
        "source_16x16_packet_manifest_sha256": receipt16["evidence_manifest_sha256"],
        "four_provider_manifest_chain_shared": True,
        "original_FE_G_and_PRE_region_specific": True,
        "reference_8x8": {
            "parent_nodes": len(index8["original_parent_node_order"]),
            "original_full_basal_triangles":
                len(index8["source_original_full_basal_triangle_nodes"]),
            "outer_cut_edges": len(index8["source_external_cut_edges"]),
        },
        "sensitivity_16x16": {
            "parent_nodes": len(index16["original_parent_node_order"]),
            "original_full_basal_triangles":
                len(index16["source_original_full_basal_triangle_nodes"]),
            "outer_cut_edges": len(index16["source_external_cut_edges"]),
        },
        "unresolved_physical_groups": list(GROUP_NAMES),
        "source_PRE_T0_authored_model_not_observed_lithology": True,
        "fault_sidedness_derived_from_parent_node_ids": False,
        "material_assignments": 0,
        "qualified_traction_inputs": 0,
        "mechanical_solver_runs": 0,
        "physical_T1": None,
        "HistoryStore_modified": False,
        "D_024": "ACTIVE",
        "WORLD_HISTORY_PRODUCTION_AUTHORIZED": False,
    }
    return a, b, audit


def write_once(repo_root: Path, output: Path, files: dict[str, dict]) -> dict:
    root, out = repo_root.resolve(), output.resolve()
    require(not out.is_relative_to(root),
            "G2G3_HANDOFF_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    require(not out.exists(), "G2G3_HANDOFF_EVIDENCE_ALREADY_EXISTS")
    require(set(files) == {"SCENARIO_8X8_UNSELECTED.json",
                           "SCENARIO_16X16_UNSELECTED.json", "AUDIT.json"},
            "G2G3_HANDOFF_OUTPUT_FILES_INVALID")
    for name, item in files.items():
        require(item.get("physical_T1") is None
                and item.get("D_024") == "ACTIVE",
                "G2G3_HANDOFF_OUTPUT_UNAUTHORIZED_PHYSICS")
        if name.startswith("SCENARIO_"):
            require(item.get("schema") == CANDIDATE_SCHEMA
                    and item.get("authoring_template_unselected") is True
                    and item.get("mechanical_solve_authorized") is False
                    and item.get("physical_source_authority_ratified") is False
                    and item.get("core_basal_tractions_by_triangle") is None
                    and item.get("core_gpe_increment_by_parent_node") is None
                    and item.get("external_gpe") is None
                    and all(type(item.get(k)) is dict
                            and item[k] and all(v is None for v in item[k].values())
                            for k in ("candidate_material_by_parent_node",
                                      "velocity_en_by_parent_node",
                                      "line_tractions_by_edge",
                                      "basal_tractions_by_triangle")),
                    "G2G3_HANDOFF_SCENARIO_NOT_UNSELECTED")
        else:
            require(item.get("schema") == SCHEMA
                    and item.get("decision") == STATUS
                    and item.get("mechanical_solver_runs") == 0
                    and item.get("WORLD_HISTORY_PRODUCTION_AUTHORIZED") is False,
                    "G2G3_HANDOFF_AUDIT_NOT_NO_SOLVE")
    text = {name: json.dumps(data, indent=2, allow_nan=False) + "\n"
            for name, data in files.items()}
    out.mkdir(parents=True, exist_ok=False)
    for name, body in text.items():
        (out / name).write_text(body, encoding="utf-8")
    manifest = {
        "schema": "ARCANA_R6_G2_G3_SOURCE_TO_COUPLED_HANDOFF_MANIFEST_V1",
        "decision": STATUS,
        "files": {name: hashlib.sha256(data.encode()).hexdigest()
                  for name, data in text.items()},
        "no_physical_solver_run": True,
        "physical_T1": None,
        "HistoryStore_modified": False,
        "D_024": "ACTIVE",
        "WORLD_HISTORY_PRODUCTION_AUTHORIZED": False,
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--packet-8", required=True, type=Path)
    ap.add_argument("--packet-16", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    p8, p16 = args.packet_8.resolve(), args.packet_16.resolve()
    require(p8 != p16, "G2G3_HANDOFF_SOURCE_REGIONS_IDENTICAL")
    sources = ((p8, "MANIFEST.json"), (p8, "SOURCE_INDEX.json"),
               (p8, "UNSELECTED_PHYSICAL_PROPOSAL.json"),
               (p16, "MANIFEST.json"), (p16, "SOURCE_INDEX.json"),
               (p16, "UNSELECTED_PHYSICAL_PROPOSAL.json"))
    before = tuple(sha256(folder / name) for folder, name in sources)
    a, b, audit = compile_pair(p8, p16)
    require(tuple(sha256(folder / name) for folder, name in sources) == before,
            "G2G3_HANDOFF_SOURCE_PACKET_CHANGED_DURING_COMPILE")
    write_once(args.repo_root, args.output, {
        "SCENARIO_8X8_UNSELECTED.json": a,
        "SCENARIO_16X16_UNSELECTED.json": b,
        "AUDIT.json": audit,
    })
    print(json.dumps({
        "status": STATUS,
        "source_8x8_nodes": audit["reference_8x8"]["parent_nodes"],
        "source_16x16_nodes": audit["sensitivity_16x16"]["parent_nodes"],
        "unresolved_physical_groups": len(audit["unresolved_physical_groups"]),
        "mechanical_solve_authorized": False,
        "physical_T1": None,
        "D_024": "ACTIVE",
    }))


if __name__ == "__main__":
    main()

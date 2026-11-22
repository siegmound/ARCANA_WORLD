"""R6 physical T0 regional input package: source-bound, *never* a T1 solver.

Materialize the full original 8x8/16x16 G2/G3 support, paired with an
UNSELECTED physical scenario keyed by genuine parent-node, triangle and
cut-edge IDs. Missing physics remains null, never an implicit zero.

Source/provider integrity is checked before any evidence is written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

SCHEMA = "ARCANA_R6_G2_G3_SOURCE_PHYSICAL_SUPPORT_PACKET_V1"
PROPOSAL_SCHEMA = "ARCANA_R6_G2_G3_UNSELECTED_PHYSICAL_PROPOSAL_V1"
MATRIX = "experiments/plate58_deforming_explore_v1/R6_G2_G3_INTEGRATED_PHYSICAL_PROVIDER_MATRIX_20261121.json"
MATRIX_GIT_BLOB = "b4f6bef26302de4ab780674b58fa4e59d4cac0d6"
STATUS = "SOURCE_AUTHENTIC_SUPPORT__PHYSICAL_INPUTS_UNSELECTED_NO_SOLVE"
THERMAL_KEYS = (
    "crust_thickness_m", "mantle_lithosphere_thickness_m",
    "crust_density_kg_m3", "mantle_density_kg_m3",
    "layer1_z0_m", "layer1_z1_m", "layer2_z0_m", "layer2_z1_m",
    "layer1_c0_k", "layer1_c1_k_m", "layer1_c2_k_m2", "layer1_c3_k_m3",
    "layer2_c0_k", "layer2_c1_k_m", "layer2_c2_k_m2", "layer2_c3_k_m3",
)
AUTHORITY = "SOURCE_MODEL_REFERENCE_WITH_UNSELECTED_PHYSICAL_PARAMETERS"


class PhysicalSourcePacketError(ValueError):
    """Fail closed on source identity, scope or forbidden authorization."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise PhysicalSourcePacketError(reason)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_sha(value: object) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=False, allow_nan=False).encode())


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def source_matrix(root: Path) -> dict:
    raw = (root / MATRIX).read_bytes()
    require(gitblob(raw) == MATRIX_GIT_BLOB, "PHYSICAL_PACKET_SOURCE_MATRIX_DRIFT")
    matrix = json.loads(raw)
    require(matrix["schema"] == "ARCANA_R6_G2_G3_INTEGRATED_PHYSICAL_PROVIDER_MATRIX_V1"
            and matrix["authority"]["mechanical_solve_authorized"] is False
            and matrix["authority"]["physical_T1"] is None
            and matrix["authority"]["HistoryStore_modified"] is False
            and matrix["authority"]["D_024"] == "ACTIVE"
            and len(matrix["groups"]) == 8
            and all(g["status"] == "SOURCE_AUTHORITY_GAP" for g in matrix["groups"]),
            "PHYSICAL_PACKET_MATRIX_AUTHORITY_CHANGED")
    return matrix


def exact_ids(items, label: str) -> list[int]:
    require(type(items) in (tuple, list), "PHYSICAL_PACKET_INVALID_IDS:" + label)
    require(all(type(x) is int and x > 0 for x in items)
            and len(items) == len(set(items)),
            "PHYSICAL_PACKET_DUPLICATE_OR_INVALID_IDS:" + label)
    return list(items)


def _map_with_int_ids(mapping, label: str):
    require(isinstance(mapping, dict), "PHYSICAL_PACKET_MAP_REQUIRED:" + label)
    out = {}
    for k, value in mapping.items():
        try:
            n = int(k)
        except (TypeError, ValueError) as exc:
            raise PhysicalSourcePacketError(
                "PHYSICAL_PACKET_BAD_MAP_KEY:" + label) from exc
        require(n > 0 and n not in out
                and str(n) == str(k), "PHYSICAL_PACKET_BAD_MAP_KEY:" + label)
        out[n] = value
    return out


def create_packet(*, extent: int, parent_ids: list[int],
                  core_triangles: dict, exterior_triangles: dict,
                  source_cut_edges: list[dict], pre_by_node: dict,
                  source_hashes: dict, matrix: dict) -> tuple[dict, dict]:
    """Pure compiler; the calling source adapter authenticates FEG/PRE first.

    Fixture-based tests exercise this function without pretending fixture IDs
    are source-authentic; successful FAIR source readback is separate.
    """
    require(type(extent) is int and extent in (8, 16),
            "PHYSICAL_PACKET_UNSUPPORTED_EXTENT")
    ids = exact_ids(parent_ids, "parent_nodes")
    scope = next((s for s in matrix["source_scopes"]
                  if s["extent_cells"] == extent), None)
    require(scope is not None and len(ids) == scope["original_parent_nodes"],
            "PHYSICAL_PACKET_PARENT_COUNT_INVALID")
    require((34587 in ids) == (extent == 16),
            "PHYSICAL_PACKET_ORIGINAL_TRIPLE_NODE_DRIFT")
    core = _map_with_int_ids(core_triangles, "core_triangles")
    exterior = _map_with_int_ids(exterior_triangles, "exterior_triangles")
    require(len(core) == scope["core_facets"]
            and len(exterior) == scope["exterior_facets"]
            and not (set(core) & set(exterior)),
            "PHYSICAL_PACKET_CORE_EXTERIOR_PARTITION_INVALID")
    faces = {**core, **exterior}
    used_nodes = set()
    for tid, vertices in faces.items():
        require(type(vertices) in (tuple, list) and len(vertices) == 3
                and all(type(n) is int and n in ids for n in vertices)
                and len(set(vertices)) == 3,
                "PHYSICAL_PACKET_SOURCE_TRIANGLE_INVALID:" + str(tid))
        used_nodes.update(vertices)
    require(len(faces) == scope["original_basal_facets_required"]
            and used_nodes == set(ids),
            "PHYSICAL_PACKET_FULL_BASAL_SUPPORT_INVALID")
    pre = _map_with_int_ids(pre_by_node, "source_pre")
    require(set(pre) == set(ids)
            and all(isinstance(pre[n], dict)
                    and int(pre[n]["node_id"]) == n
                    and "material_configuration_code" in pre[n]
                    for n in ids), "PHYSICAL_PACKET_PRE_SOURCE_NODE_COVERAGE_INVALID")
    model_thermal = {}
    for n in ids:
        row = pre[n]
        require(set(THERMAL_KEYS).issubset(row)
                and all(type(row[k]) in (int, float)
                        and math.isfinite(row[k]) for k in THERMAL_KEYS),
                "PHYSICAL_PACKET_PRE_THERMAL_SOURCE_INCOMPLETE")
        crust = float(row["crust_thickness_m"])
        mantle = float(row["mantle_lithosphere_thickness_m"])
        require(crust > 0 and mantle > 0
                and row["crust_density_kg_m3"] > 0
                and row["mantle_density_kg_m3"] > 0
                and row["layer1_c0_k"] > 0 and row["layer2_c0_k"] > 0
                and abs(row["layer1_z0_m"]) < 1e-6
                and abs(row["layer1_z1_m"] - crust) < 1e-5
                and abs(row["layer2_z0_m"] - crust) < 1e-5
                and abs(row["layer2_z1_m"] - crust - mantle) < 1e-5,
                "PHYSICAL_PACKET_PRE_THERMAL_LAYER_GEOMETRY_INVALID")
        model_thermal[str(n)] = {k: float(row[k]) for k in THERMAL_KEYS}
    require(type(source_cut_edges) is list
            and len(source_cut_edges) == scope["cut_edge_inputs_required"],
            "PHYSICAL_PACKET_CUT_EDGE_COUNT_INVALID")
    cut_ids = []
    for edge in source_cut_edges:
        require(isinstance(edge, dict) and type(edge.get("source_edge_id")) is str,
                "PHYSICAL_PACKET_CUT_EDGE_ID_MISSING")
        eids = edge.get("source_parent_node_ids")
        require(type(eids) is list and len(eids) == 2
                and len(set(eids)) == 2
                and all(type(n) is int and n in ids for n in eids),
                "PHYSICAL_PACKET_CUT_EDGE_SOURCE_NODE_INVALID")
        expected = ":".join(map(str, sorted(eids)))
        require(edge["source_edge_id"] == expected,
                "PHYSICAL_PACKET_CUT_EDGE_ID_TAMPERED")
        cut_ids.append(expected)
    require(len(set(cut_ids)) == len(cut_ids),
            "PHYSICAL_PACKET_DUPLICATE_CUT_EDGES")
    require(isinstance(source_hashes, dict)
            and set(source_hashes) == {
                "multiscale_manifest_sha256", "interface_manifest_sha256",
                "nodal_manifest_sha256", "force_manifest_sha256",
                "original_FEG_sha256", "original_PRE_sha256"}
            and all(type(s) is str and len(s) == 64
                    and all(c in "0123456789abcdef" for c in s)
                    for s in source_hashes.values()),
            "PHYSICAL_PACKET_SOURCE_HASHES_REQUIRED")
    counts = {
        "original_parent_nodes": len(ids),
        "source_original_full_basal_triangles": len(faces),
        "source_core_basal_triangles": len(core),
        "source_exterior_basal_triangles": len(exterior),
        "original_external_cut_edges": len(cut_ids),
        "source_pre_records": len(pre),
    }
    index = {
        "schema": SCHEMA, "status": STATUS, "authority": AUTHORITY,
        "epoch": "T0_210_Ma", "extent_cells": extent,
        "source_scope": "SOURCE_ORIGINAL_8x8_5_8" if extent == 8
                        else "SOURCE_ORIGINAL_16x16_5_8_11",
        "source_hashes": source_hashes,
        "physical_provider_matrix_git_blob": MATRIX_GIT_BLOB,
        "counts": counts, "original_parent_node_order": ids,
        "source_original_core_triangle_ids": sorted(core),
        "source_original_exterior_triangle_ids": sorted(exterior),
        "source_original_full_basal_triangle_nodes": {
            str(t): list(faces[t]) for t in sorted(faces)},
        "source_external_cut_edges": [
            {"source_edge_id": str(e["source_edge_id"]),
             "source_parent_node_ids": list(e["source_parent_node_ids"]),
             "side": e.get("side"),
             "adjacent_plate_id": e.get("adjacent_plate_id")}
            for e in source_cut_edges],
        "source_pre_record_sha256_by_parent_node": {
            str(n): content_sha(pre[n]) for n in ids},
        "source_material_configuration_code_by_parent_node": {
            str(n): pre[n]["material_configuration_code"] for n in ids},
        "source_original_PRE_model_T0_thermal_profiles_by_parent_node": model_thermal,
        "source_PRE_is_authored_thermal_material_model_not_natural_mineralogy": True,
        "thermal_reference_is_not_100y_or_1000y_synthetic_pilot_output": True,
        "source_feg_2d_sheet_not_sided_fault_solid": True,
        "physical_T1": None, "mechanical_solve_authorized": False,
        "history_store_mutations": 0, "D_024": "ACTIVE",
    }
    # A complete *source inventory* is not a complete *physical law*.
    groups = {g["id"]: {"status": "SOURCE_AUTHORITY_GAP",
                         "required": g["required"]} for g in matrix["groups"]}
    proposed = {
        "schema": PROPOSAL_SCHEMA, "authority": "UNSELECTED_NO_PHYSICAL_AUTHORITY",
        "source_index_sha256": content_sha(index),
        "scope_extent_cells": extent,
        "original_parent_node_order": ids,
        "material_rock_phase_by_parent_node": {str(n): None for n in ids},
        "water_effective_pressure_by_parent_node": {str(n): None for n in ids},
        "constitutive_law_and_lab_validity_by_parent_node": {
            str(n): None for n in ids},
        "outer_cut_physical_traction_N_per_m": {c: None for c in cut_ids},
        "full_basal_tangential_normal_load_Pa": {
            str(t): None for t in sorted(faces)},
        "GPE_full_domain_vertical_and_pressure_support": None,
        "sided_fault_transmission_and_triple_junction": None,
        "solver_version_rank_gauge_conservation_restart": None,
        "independent_mantle_reference_and_mechanical_LAB": None,
        "explicit_authorial_selection_record": None,
        "remaining_physical_groups": groups,
        "input_gaps_are_UNKNOWN_not_zero": True,
        "source_model_parameters_are_not_natural_properties": True,
        "physical_solve_authorized": False,
        "canonical_history_write_authorized": False,
        "history_store_mutations": 0,
        "physical_T1": None,
        "D_024": "ACTIVE",
    }
    return index, proposed


def verify_unselected(index: dict, proposal: dict) -> None:
    require(index["schema"] == SCHEMA and index["status"] == STATUS
            and index["authority"] == AUTHORITY
            and index["D_024"] == "ACTIVE"
            and index["history_store_mutations"] == 0
            and index["source_PRE_is_authored_thermal_material_model_not_natural_mineralogy"] is True
            and index["thermal_reference_is_not_100y_or_1000y_synthetic_pilot_output"] is True
            and proposal["input_gaps_are_UNKNOWN_not_zero"] is True
            and proposal["source_model_parameters_are_not_natural_properties"] is True
            and index["physical_T1"] is None
            and index["mechanical_solve_authorized"] is False
            and proposal["schema"] == PROPOSAL_SCHEMA
            and proposal["source_index_sha256"] == content_sha(index)
            and proposal["authority"] == "UNSELECTED_NO_PHYSICAL_AUTHORITY"
            and proposal["physical_solve_authorized"] is False
            and proposal["canonical_history_write_authorized"] is False
            and proposal["physical_T1"] is None
            and proposal["history_store_mutations"] == 0,
            "PHYSICAL_PACKET_AUTHORITY_OR_INDEX_MISMATCH")
    node_set = set(map(str, index["original_parent_node_order"]))
    facet_set = set(index["source_original_full_basal_triangle_nodes"])
    cut_set = {s["source_edge_id"] for s in index["source_external_cut_edges"]}
    for key, expected in (
        ("material_rock_phase_by_parent_node", node_set),
        ("water_effective_pressure_by_parent_node", node_set),
        ("constitutive_law_and_lab_validity_by_parent_node", node_set),
        ("outer_cut_physical_traction_N_per_m", cut_set),
        ("full_basal_tangential_normal_load_Pa", facet_set),
    ):
        mapping = proposal.get(key)
        require(isinstance(mapping, dict) and set(mapping) == expected
                and all(v is None for v in mapping.values()),
                "PHYSICAL_PACKET_UNSELECTED_SUPPORT_TAMPERED:" + key)
    for key in (
        "GPE_full_domain_vertical_and_pressure_support",
        "sided_fault_transmission_and_triple_junction",
        "solver_version_rank_gauge_conservation_restart",
        "independent_mantle_reference_and_mechanical_LAB",
        "explicit_authorial_selection_record",
    ):
        require(proposal.get(key, "MISSING") is None,
                "PHYSICAL_PACKET_NO_FAKE_PHYSICAL_SOURCE:" + key)
    require(set(proposal["remaining_physical_groups"]) == {
        "g2_material_and_phases", "g2_pressure_water",
        "g2_lab_law_and_coverage", "g3_outer_cut", "g3_full_basal",
        "g3_gpe", "interface_fault", "solver_compatibility"}
            and all(x["status"] == "SOURCE_AUTHORITY_GAP"
                    for x in proposal["remaining_physical_groups"].values()),
            "PHYSICAL_PACKET_UNQUALIFIED_GROUP_PROMOTION")


def compile_from_authentic_sources(root: Path, *, multiscale: Path,
                                   interface: Path, nodal: Path, force: Path,
                                   extent: int) -> tuple[dict, dict]:
    """Re-use pre-existing independent source SHA/FEG/PRE join validators."""
    from experiments.plate58_deforming_explore_v1.g2_g3_source_coupled_runner import (
        read_pinned,
    )
    from experiments.plate58_deforming_explore_v1.g2_g3_core_exterior_source_runner import (
        source_core_geometry,
    )
    from experiments.plate58_deforming_explore_v1.g3_force_budget import edge_key

    matrix = source_matrix(root)
    providers, manifest_sha = {}, {}
    for name, path in (("multiscale", multiscale), ("interface", interface),
                       ("nodal", nodal), ("force", force)):
        providers[name], manifest_sha[name] = read_pinned(name, path)
    a, b, c, d = (providers[x] for x in
                  ("multiscale", "interface", "nodal", "force"))
    require(b["source_multiscale_manifest_sha256"] == manifest_sha["multiscale"]
            and c["source_multiscale_manifest_sha256"] == manifest_sha["multiscale"]
            and c["source_interface_manifest_sha256"] == manifest_sha["interface"]
            and d["parent_multiscale_manifest_sha256"] == manifest_sha["multiscale"]
            and d["parent_interface_manifest_sha256"] == manifest_sha["interface"]
            and d["parent_G2_binding_manifest_sha256"] == manifest_sha["nodal"],
            "PHYSICAL_PACKET_PROVIDER_SOURCE_SHA_CHAIN_INVALID")
    region = next((s for s in a["topological_comparative_extents"]
                   if s["cell_extent_per_side"] == extent), None)
    iface = next((s for s in b["scales"]
                  if s["extent_cells_per_side"] == extent), None)
    ns = next((s for s in c["scales"]
               if s["extent_cells"] == extent), None)
    fs = next((s for s in d["scales"]
               if s["extent_cells"] == extent), None)
    require(all(x is not None for x in (region, iface, ns, fs)),
            "PHYSICAL_PACKET_SOURCE_SCOPE_NOT_FOUND")
    core = source_core_geometry(multiscale, interface, nodal, extent)
    parent_ids = core["source_original_full_parent_node_order"]
    require(parent_ids == list(map(int, region["parent_node_ids"])),
            "PHYSICAL_PACKET_PARENT_ORDER_DRIFT")
    exterior = {
        int(tid): list(map(int, row["parent_node_ids"]))
        for tid, row in ns["exterior_triangles"].items()}
    require(set(exterior) == set(map(int, iface["source_exterior_triangles"])),
            "PHYSICAL_PACKET_SOURCE_EXTERIOR_TRIANGLE_DRIFT")
    triangles = set(core["source_core_triangles"]) | set(exterior)
    require(triangles == set(map(int, region["parent_triangle_ids"])),
            "PHYSICAL_PACKET_ORIGINAL_FEG_TRIANGLE_SET_DRIFT")
    cuts = fs["source_external_cut_edges"]
    for row in cuts:
        require(row["source_edge_id"] == edge_key(row["source_parent_node_ids"]),
                "PHYSICAL_PACKET_ORIGINAL_CUT_SOURCE_ID_INVALID")
    hashes = {
        "multiscale_manifest_sha256": manifest_sha["multiscale"],
        "interface_manifest_sha256": manifest_sha["interface"],
        "nodal_manifest_sha256": manifest_sha["nodal"],
        "force_manifest_sha256": manifest_sha["force"],
        "original_FEG_sha256": core["source_FEG_sha256"],
        "original_PRE_sha256": core["source_PRE_sha256"],
    }
    index, proposal = create_packet(
        extent=extent, parent_ids=parent_ids,
        core_triangles=core["source_core_triangles"],
        exterior_triangles=exterior, source_cut_edges=cuts,
        pre_by_node=core["source_PRE"],
        source_hashes=hashes, matrix=matrix)
    verify_unselected(index, proposal)
    for name, path in (("multiscale", multiscale), ("interface", interface),
                       ("nodal", nodal), ("force", force)):
        from experiments.plate58_deforming_explore_v1.g2_g3_source_coupled_runner import sha
        require(sha(Path(path) / "MANIFEST.json") == manifest_sha[name],
                "PHYSICAL_PACKET_SOURCE_PROVIDER_CHANGED_DURING_COMPILE")
    return index, proposal


def write_once(root: Path, output: Path, index: dict, proposal: dict) -> None:
    root, output = Path(root).resolve(), Path(output).resolve()
    require(not output.is_relative_to(root),
            "PHYSICAL_PACKET_EVIDENCE_MUST_BE_OUTSIDE_REPOSITORY")
    require(not output.exists(), "PHYSICAL_PACKET_EVIDENCE_EXISTS")
    verify_unselected(index, proposal)
    data = {
        "SOURCE_INDEX.json": json.dumps(index, indent=2, allow_nan=False) + "\n",
        "UNSELECTED_PHYSICAL_PROPOSAL.json":
            json.dumps(proposal, indent=2, allow_nan=False) + "\n",
    }
    output.mkdir(parents=True, exist_ok=False)
    for filename, body in data.items():
        (output / filename).write_text(body, encoding="utf-8")
    (output / "MANIFEST.json").write_text(json.dumps({
        "schema": "ARCANA_R6_G2_G3_PHYSICAL_SUPPORT_PACKET_MANIFEST_V1",
        "status": STATUS,
        "source_original_FEG_sha256": index["source_hashes"]["original_FEG_sha256"],
        "source_original_PRE_sha256": index["source_hashes"]["original_PRE_sha256"],
        "files": {filename: sha_bytes(body.encode())
                  for filename, body in data.items()},
        "physical_T1": None, "physical_solve_authorized": False,
        "HistoryStore_mutations": 0, "D_024": "ACTIVE",
    }, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def select_unique_source_chain(options: dict) -> dict[str, Path]:
    """Select only a unique SHA provenance chain; identical aliases are fine.

    options[name] entries: (manifest_SHA, absolute provider_path, report_dict).
    All report dicts have already been integrity-checked by read_pinned.
    """
    required = ("multiscale", "interface", "nodal", "force")
    require(set(options) == set(required)
            and all(isinstance(options[n], list) for n in required),
            "PHYSICAL_PACKET_SOURCE_DISCOVERY_INPUT_INVALID")
    signatures = {}
    for ms, mp, mrow in options["multiscale"]:
        for ih, ip, ir in options["interface"]:
            if ir.get("source_multiscale_manifest_sha256") != ms:
                continue
            for nh, np, nr in options["nodal"]:
                if (nr.get("source_multiscale_manifest_sha256") != ms
                        or nr.get("source_interface_manifest_sha256") != ih):
                    continue
                for fh, fp, fr in options["force"]:
                    if (fr.get("parent_multiscale_manifest_sha256") == ms
                            and fr.get("parent_interface_manifest_sha256") == ih
                            and fr.get("parent_G2_binding_manifest_sha256") == nh):
                        identity = (ms, ih, nh, fh)
                        choice = {"multiscale": mp, "interface": ip,
                                  "nodal": np, "force": fp}
                        if identity not in signatures or tuple(
                            str(choice[k]) for k in required) < tuple(
                            str(signatures[identity][k]) for k in required):
                            signatures[identity] = choice
    require(len(signatures) == 1,
            "PHYSICAL_PACKET_SOURCE_CHAIN_MISSING_OR_AMBIGUOUS")
    return next(iter(signatures.values()))


def discover_fair_providers(evidence_root: Path) -> dict[str, Path]:
    """Find source-certified four-provider chain by manifest SHA, not mtime."""
    from experiments.plate58_deforming_explore_v1.g2_g3_source_coupled_runner import (
        EXPECTED, read_pinned,
    )
    evidence_root = Path(evidence_root)
    require(evidence_root.is_dir(), "PHYSICAL_PACKET_FAIR_EVIDENCE_ROOT_MISSING")
    options = {}
    for name in ("multiscale", "interface", "nodal", "force"):
        filename, _ = EXPECTED[name]
        candidates = []
        for file in sorted(evidence_root.rglob(filename)):
            try:
                report, sh = read_pinned(name, file.parent)
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
            if {int(row.get("cell_extent_per_side", row.get("extent_cells_per_side",
                      row.get("extent_cells", -1)))) for row in report.get(
                    "topological_comparative_extents" if name == "multiscale"
                    else "scales", [])} != {8, 16}:
                continue
            candidates.append((sh, file.parent, report))
        options[name] = candidates
    return select_unique_source_chain(options)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    for k in ("multiscale", "interface", "nodal", "force"):
        p.add_argument("--"+k, type=Path)
    p.add_argument("--evidence-root", type=Path,
                   help="Discover a unique SHA-chained FAIR four-provider set")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--extent", type=int, choices=(8, 16), default=8)
    x = p.parse_args()
    explicit = {k: getattr(x, k) for k in
                ("multiscale", "interface", "nodal", "force")}
    if x.evidence_root is not None:
        require(all(v is None for v in explicit.values()),
                "PHYSICAL_PACKET_DISCOVERY_EXPLICIT_PATH_CONFLICT")
        paths = discover_fair_providers(x.evidence_root)
    else:
        require(all(v is not None for v in explicit.values()),
                "PHYSICAL_PACKET_ALL_FOUR_EXPLICIT_PATHS_REQUIRED")
        paths = explicit
    index, proposal = compile_from_authentic_sources(
        x.repo_root, **paths, extent=x.extent)
    write_once(x.repo_root, x.output, index, proposal)
    print(json.dumps({"decision": STATUS, "extent": x.extent,
                      "source_counts": index["counts"],
                      "unresolved_physical_groups": 8,
                      "physical_T1": None, "D_024": "ACTIVE",
                      "world_history_production_authorized": False}))


if __name__ == "__main__":
    main()

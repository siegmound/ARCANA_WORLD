"""ARCANA R6 plate 5:8, source-indexed G2/G3 A exterior coupling.

The integration binds T0/PRE material-column identity and exact FEM interface
DOF identities, and implements a solver-independent exterior tangent/force
Schur transfer. It does NOT manufacture rheological coefficients, tractions,
external stiffness, basal closure, or a physical ShellSet solve.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.check import verify as verify_core
from experiments.plate58_deforming_explore_v1.check_envelope import verify as verify_halo
from experiments.plate58_deforming_explore_v1.envelope import (
    _copy_source_validation, edge_incidence,
)
from experiments.plate58_deforming_explore_v1.prepare import (
    PRE, ROOT, _json, require, sha,
)

SCHEMA = "ARCANA_R6_G2_G3_A_SOURCE_INTERFACE_BINDING_V1"
STATUS = "PASS_G2_G3_A_SOURCE_INTERFACE_BOUND__PHYSICAL_CLOSURE_OPEN"
APPROVAL = "experiments/plate58_deforming_explore_v1/G3_A_AUTHORIAL_ARCHITECTURE_RATIFICATION.json"
EXPECTED_APPROVAL = "OUTER_CONTINUUM_MECHANICAL_TRANSFER_A"


def block_dofs(parent_node_ids, components=2):
    """Velocity tangent DOFs in exact node order; no duplicate source nodes."""
    nodes = [int(i) for i in parent_node_ids]
    require(components == 2 and len(set(nodes)) == len(nodes) and
            all(i > 0 for i in nodes), "G3_A_DOFS_DUPLICATED_OR_INVALID")
    return [[2 * k, 2 * k + 1] for k in range(len(nodes))]


def exterior_interface(core_nodes, halo_nodes, core_triangles, halo_triangles,
                       halo_local_elements, halo_plates):
    """Identify ring, interior and shared boundary by original parent IDs."""
    c_nodes = tuple(map(int, core_nodes))
    h_nodes = tuple(map(int, halo_nodes))
    c_tris = tuple(map(int, core_triangles))
    h_tris = tuple(map(int, halo_triangles))
    require(len(c_nodes) == 9 and len(h_nodes) == 25 and
            len(c_tris) == 8 and len(h_tris) == 32 and
            len(set(c_nodes)) == 9 and len(set(h_nodes)) == 25 and
            set(c_nodes).issubset(h_nodes) and set(c_tris).issubset(h_tris)
            and len(halo_local_elements) == len(h_tris) == len(halo_plates)
            and set(halo_plates) == {5, 8},
            "G2_G3_SOURCE_INVENTORY_CHANGED")
    tri_nodes = {}
    for i, source_id in enumerate(h_tris):
        tri = halo_local_elements[i]
        local_ids = tuple(map(int, tri.node_ids))
        require(all(1 <= n <= len(h_nodes) for n in local_ids)
                and len(set(local_ids)) == 3,
                "G3_LOCAL_TRIANGLE_INVALID")
        tri_nodes[source_id] = tuple(h_nodes[n - 1] for n in local_ids)
    known_core = set(c_tris)
    ext_tris = [tid for tid in h_tris if tid not in known_core]
    require(len(ext_tris) == 24, "G3_EXTERIOR_TRIANGLES_WRONG_COUNT")
    core_from_faces = {n for tid in c_tris for n in tri_nodes[tid]}
    ext_from_faces = {n for tid in ext_tris for n in tri_nodes[tid]}
    require(core_from_faces == set(c_nodes) and
            ext_from_faces.issubset(h_nodes),
            "G3_TRIANGLE_TO_PARENT_NODE_BINDING_CHANGED")
    interface = sorted(core_from_faces & ext_from_faces)
    external_only = sorted(ext_from_faces - core_from_faces)
    core_only = sorted(core_from_faces - ext_from_faces)
    require(len(interface) == 8 and len(external_only) == 16
            and len(core_only) == 1 and
            len(ext_from_faces) == 24,
            "G3_INTERIOR_EXTERIOR_NODE_COUNTS_CHANGED")
    # The eight core perimeter edges must be shared by core and external mesh.
    incidence = Counter()
    for tid in c_tris:
        a, b, c = tri_nodes[tid]
        for x, y in ((a, b), (b, c), (c, a)):
            incidence[tuple(sorted((x, y)))] += 1
    core_perimeter = {edge for edge, n in incidence.items() if n == 1}
    require(len(core_perimeter) == 8 and
            {n for e in core_perimeter for n in e} == set(interface),
            "G3_CORE_PERIMETER_AND_INTERFACE_MISMATCH")
    ext_incidence = Counter()
    for tid in ext_tris:
        a, b, c = tri_nodes[tid]
        for x, y in ((a, b), (b, c), (c, a)):
            ext_incidence[tuple(sorted((x, y)))] += 1
    require(all(ext_incidence[edge] == 1 for edge in core_perimeter),
            "G3_OUTER_RING_DOES_NOT_SHARE_FULL_CORE_PERIMETER")
    all_25_dofs = block_dofs(h_nodes)
    physical_nodes = interface + external_only
    dofs = block_dofs(physical_nodes)
    assert len(all_25_dofs) == 25 and len(dofs) == 24
    return {
        "source_core_parent_node_ids": list(c_nodes),
        "source_core_parent_triangle_ids": list(c_tris),
        "source_halo_parent_node_ids": list(h_nodes),
        "source_halo_parent_triangle_ids": list(h_tris),
        "source_exterior_triangle_ids": ext_tris,
        "parent_interface_nodes": interface,
        "parent_external_only_nodes": external_only,
        "parent_core_only_nodes": core_only,
        "interface_parent_edges": [list(edge) for edge in sorted(core_perimeter)],
        "exterior_reduced_node_order": physical_nodes,
        "exterior_reduced_dof_order": [
            {"parent_node_id": n, "south_or_local_tangent_dof": d[0],
             "east_or_local_tangent_dof": d[1]}
            for n, d in zip(physical_nodes, dofs, strict=True)],
        "interface_dof_indices": list(range(16)),
        "external_only_dof_indices": list(range(16, 48)),
        "coordinate_frame": None,
        "source_mesh_nodes_not_duplicated": True,
        "unknown_exterior_constitutive_tangent": None,
        "unknown_exterior_loads": None,
    }


def condense_exterior_tangent(matrix, load, interface_indices, *,
                             max_condition=1e12, symmetric_test=False):
    """Exact linear algebra K_ii - K_ie K_ee^-1 K_ei; no physical input inference.

    Input is a REAL already assembled/constrained exterior solver tangent and
    load, with its gauge and far-boundary constraints physically specified.
    The function never assembles material tensors or boundary values.
    Returns interface response stiffness and effective load plus reconstruction
    operators; caller must still provide an actual physical boundary state.
    """
    k = np.asarray(matrix, dtype=np.float64)
    f = np.asarray(load, dtype=np.float64)
    boundary = np.asarray(interface_indices, dtype=np.int64)
    require(k.ndim == 2 and k.shape[0] == k.shape[1] and
            len(k) > 1 and f.shape == (len(k),) and
            boundary.ndim == 1 and 0 < len(boundary) < len(k)
            and len(set(boundary.tolist())) == len(boundary)
            and np.all((boundary >= 0) & (boundary < len(k)))
            and np.all(np.isfinite(k)) and np.all(np.isfinite(f))
            and math.isfinite(max_condition) and max_condition >= 1,
            "G3_EXTERIOR_TANGENT_INPUT_INVALID")
    inner = np.array([i for i in range(len(k)) if i not in set(boundary.tolist())],
                     dtype=np.int64)
    kii = k[np.ix_(inner, inner)]
    condition = float(np.linalg.cond(kii))
    require(math.isfinite(condition) and condition <= max_condition,
            "G3_EXTERIOR_UNANCHORED_OR_ILL_CONDITIONED")
    try:
        transfer = np.linalg.solve(kii, k[np.ix_(inner, boundary)])
        load_transfer = np.linalg.solve(kii, f[inner])
    except np.linalg.LinAlgError as e:
        raise ValueError("G3_EXTERIOR_SINGULAR_TANGENT") from e
    effective = k[np.ix_(boundary, boundary)] - k[np.ix_(boundary, inner)]@transfer
    force = f[boundary] - k[np.ix_(boundary, inner)]@load_transfer
    require(np.all(np.isfinite(effective)) and np.all(np.isfinite(force)),
            "G3_CONDENSED_OPERATOR_NOT_FINITE")
    if symmetric_test:
        require(np.allclose(k, k.T, atol=1e-10, rtol=1e-10) and
                np.allclose(effective, effective.T, atol=1e-10, rtol=1e-10),
                "G3_ENERGY_RECIPROCITY_TEST_FAILED")
    return {"interface_tangent": effective, "effective_load": force,
            "interior_affine_offset": load_transfer,
            "interior_response_operator": -transfer,
            "boundary_indices": boundary, "interior_indices": inner,
            "interior_block_condition": condition,
            "material_or_boundary_law_inferred": False}


def reconstruct_external_solution(condensed, boundary_displacement):
    u = np.asarray(boundary_displacement, dtype=np.float64)
    b = condensed["boundary_indices"]
    i = condensed["interior_indices"]
    require(u.shape == (len(b),) and np.all(np.isfinite(u)),
            "G3_INTERFACE_STATE_INVALID")
    all_u = np.zeros(len(b) + len(i))
    all_u[b] = u
    all_u[i] = (condensed["interior_affine_offset"] +
                condensed["interior_response_operator"] @ u)
    return all_u


def select_passive_pre(root, parent_ids, sha_expected):
    """Read authentic 25 PRE columns, preserve missing/unknown as null."""
    meta_path = root / (PRE + ".json")
    data_path = root / (PRE + ".dat")
    require(sha(meta_path) == sha_expected[PRE + ".json"] and
            sha(data_path) == sha_expected[PRE + ".dat"],
            "G2_SOURCE_PRE_SHA_DRIFT")
    meta = json.loads(meta_path.read_text())
    keys = list(meta["field_order"])
    wanted = set(map(int, parent_ids))
    require(len(keys) == 51 and len(wanted) == 25,
            "G2_PRE_INVENTORY_OR_SCHEMA_INVALID")
    selected = {}
    with data_path.open() as f:
        h = next(f).split()
        require(len(h) == 3 and int(h[2]) == int(meta["node_count"]) == 64442
                and h[0] == meta["header"]["magic"]
                and h[1] == meta["header"]["schema"],
                "G2_PRE_HEADER_INVALID")
        count = 0
        for count, line in enumerate(f, 1):
            if count not in wanted:
                continue
            values = line.split()
            require(len(values) == len(keys) and int(values[0]) == count,
                    "G2_PRE_NODE_INDEX_INVALID")
            record = {}
            for k, raw in zip(keys, values, strict=True):
                val = float(raw)
                record[k] = val if math.isfinite(val) else None
            require(record["node_id"] == count,
                    "G2_PRE_PARENT_ID_MISMATCH")
            selected[count] = record
        require(count == meta["node_count"] and set(selected) == wanted,
                "G2_PRE_SOURCE_NOT_COMPLETE")
    required = ("crust_thickness_m", "mantle_lithosphere_thickness_m",
                "surface_temperature_k", "moho_temperature_k",
                "lab_temperature_k", "crust_density_kg_m3",
                "mantle_density_kg_m3")
    for pid, col in selected.items():
        for k in required:
            v = col[k]
            require(v is not None and math.isfinite(v) and v > 0,
                    "G2_PRE_REQUIRED_PHYSICAL_INPUT_MISSING:"+str(pid)+":"+k)
    return {
        "source": PRE + ".dat",
        "source_sha256": sha(data_path),
        "source_meta_sha256": sha(meta_path),
        "scope": "SOURCE_T0_PRE_25_NODES_FOR_G2_COLUMN_BINDING_ONLY",
        "source_node_count": 25,
        "source_columns": [{"parent_id": pid, "source_PRE": selected[pid],
                            "material_law": None, "water_fugacity": None,
                            "pore_pressure": None, "friction": None,
                            "SHELLS_LR": None}
                           for pid in sorted(wanted)],
        "PRE_authority": "OWNER_BOUND_T0_FIELDS_NOT_LAYER_PHYSICAL_CONSTITUTIVE_LAW",
        "effective_constitutive_closure": None,
    }


def bind(stage_dir: Path, envelope_dir: Path, output_dir: Path, *, root=ROOT):
    require(not output_dir.exists(), "OUTPUT_ALREADY_EXISTS")
    verify_core(stage_dir)
    verify_halo(envelope_dir)
    stage = json.loads((stage_dir/"CASE.json").read_text())
    halo = json.loads((envelope_dir/"NEIGHBORHOOD.json").read_text())
    approval_path = root/APPROVAL
    ratified = json.loads(approval_path.read_text())
    require(ratified["guardrails"]["architecture_ratified"] is True
            and ratified["guardrails"]["mechanical_solve_authorized"] is False
            and ratified["selected"]["G3_external_continuation_architecture"] ==
                EXPECTED_APPROVAL,
            "G3_A_AUTHORIAL_ARCHITECTURE_NOT_RATIFIED_OR_SCOPE_CHANGED")
    require(halo["input_four_cell_sha256"] == sha(stage_dir/"CASE.json"),
            "G2_G3_STAGE_TO_HALO_SHA_MISMATCH")
    _copy_source_validation(stage, root=root)
    require(halo["source_mesh_identity_sha256"] and
            halo["source_euler_sha256"] == stage["source_sha256"]["R6_T0_CANONICAL_PLATE_KINEMATICS.json"],
            "G2_G3_PARENT_SOURCE_IDENTITY_CHANGED")
    feg = parse_feg((envelope_dir/"REGIONAL_16.feg").read_text(),
                    mode="SHELLS_READY")
    plate_ids = halo["triangle_plate_ids"]
    edges = edge_incidence(feg.elements, plate_ids)
    contacts = [edge for edge, members in edges.items()
                if len(members) == 2 and members[0][1] != members[1][1]]
    require(len(contacts) == halo["boundary_analysis"]["source_contact_count"] == 6,
            "G3_SOURCE_CONTACT_EDGE_COUNT_CHANGED")
    interface = exterior_interface(
        stage["node_ids_parent"], halo["parent_node_ids"],
        stage["parent_triangle_ids"], halo["parent_triangle_ids"],
        feg.elements, plate_ids,
    )
    pre = select_passive_pre(root, halo["parent_node_ids"], stage["source_sha256"])
    # No reader may promote PRE owner fields into a per-element creep law.
    transfer = {
        "schema": "ARCANA_R6_G3_A_EXTERIOR_TANGENT_TRANSFER_CONTRACT_V1",
        "architecture": EXPECTED_APPROVAL,
        "scope": "EXTERIOR_DIRICHLET_TO_NEUMANN_TANGENT_INTERFACE_ONLY",
        "source_interface_parent_nodes": interface["parent_interface_nodes"],
        "source_exterior_only_parent_nodes": interface["parent_external_only_nodes"],
        "source_core_only_parent_nodes": interface["parent_core_only_nodes"],
        "source_contact_boundary_ids": [row["source_boundary_id"]
                                        for row in halo["boundary_analysis"]["source_contact"]],
        "source_core_parent_triangle_ids": stage["parent_triangle_ids"],
        "source_exterior_parent_triangle_ids": interface["source_exterior_triangle_ids"],
        "mechanical_tangent_units": "REQUIRED_FROM_EXTERNAL_SHELLS_CONTINUUM__NOT_BOUND",
        "traction_or_force_units": "REQUIRED_FROM_EXTERNAL_SHELLS_CONTINUUM__NOT_BOUND",
        "coordinate_frame": stage["numerical_frame"],
        "G2_required_effective_rheology_provider": None,
        "G3_required_exterior_tangent_and_load_provider": None,
        "G3_required_distal_boundary_and_gauge": None,
        "G3_required_north_south_traction_state": None,
        "G3_required_basal_normal_and_tangential_support": None,
        "G3_required_GPE_Squeez_Fixed_no_double_count": None,
        "G3_required_external_domain_convergence": None,
        "actual_interface_tangent": None,
        "actual_effective_load": None,
        "external_solve_or_matrix_assembly_performed": False,
        "mechanical_solve_authorized": False,
        "physical_T1": None,
        "operator_contract": {
            "input_node_order": "INTERFACE_THEN_EXTERIOR_ONLY__TWO_TANGENTIAL_COMPONENTS_EACH",
            "tangent_block_algebra":
                "Keff=Kbb-Kbe*solve(Kee,Keb)",
            "load_block_algebra": "feff=fb-Kbe*solve(Kee,fe)",
            "far_boundary_condition": "REQUIRED_PHYSICAL_PROVIDER; NO_IMPLICIT_FREE_OR_ZERO",
            "K_tangent": None, "f_exterior": None,
        },
    }
    require(not stage["readiness"]["mechanical_solve_authorized"]
            and not halo["mechanical_solve_authorized"]
            and transfer["actual_interface_tangent"] is None
            and transfer["actual_effective_load"] is None,
            "UNAUTHORIZED_G2_G3_PHYSICAL_INPUT_OR_SOLVE")
    output_dir.mkdir(parents=True, exist_ok=False)
    out = {
        "GEOMETRY.json": {
            "schema": SCHEMA, "status": STATUS,
            "source_stage_CASE_sha256": sha(stage_dir/"CASE.json"),
            "source_halo_NEIGHBORHOOD_sha256": sha(envelope_dir/"NEIGHBORHOOD.json"),
            "authorial_G3_A_sha256": sha(approval_path),
            "source_mesh_identity_sha256": halo["source_mesh_identity_sha256"],
            "geometry": interface,
            "source_contact_count": len(contacts),
            "actual_solver_calls": 0, "physical_T1": None,
        },
        "G2_PRE_BINDING.json": pre,
        "G3_A_TRANSFER_CONTRACT.json": transfer,
    }
    for name, obj in out.items():
        (output_dir/name).write_bytes(_json(obj))
    manifest = {"schema": "ARCANA_R6_G2_G3_A_SOURCE_INTERFACE_MANIFEST_V1",
                "status": STATUS,
                "files": {name: sha(output_dir/name) for name in out},
                "source_stage_CASE_sha256": out["GEOMETRY.json"]["source_stage_CASE_sha256"],
                "source_halo_NEIGHBORHOOD_sha256": out["GEOMETRY.json"]["source_halo_NEIGHBORHOOD_sha256"],
                "no_solver_run": True, "no_T1": True, "no_canonical_promotion": True}
    (output_dir/"MANIFEST.json").write_bytes(_json(manifest))
    return {"status": STATUS,
            "halo_nodes": len(interface["source_halo_parent_node_ids"]),
            "halo_triangles": len(interface["source_halo_parent_triangle_ids"]),
            "core_triangles": len(interface["source_core_parent_triangle_ids"]),
            "exterior_triangles": len(interface["source_exterior_triangle_ids"]),
            "interface_nodes": len(interface["parent_interface_nodes"]),
            "external_only_nodes": len(interface["parent_external_only_nodes"]),
            "g2_PRE_columns_bound": pre["source_node_count"],
            "G3_A_architecture_ratified": True,
            "G2_effective_constitutive_closure": None,
            "G3_A_physical_tangent": None,
            "mechanical_solve_authorized": False, "solver_runs": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path)
    parser.add_argument("halo", type=Path)
    parser.add_argument("output", type=Path)
    options = parser.parse_args()
    print(json.dumps(bind(options.stage, options.halo, options.output),
                     indent=2, sort_keys=True))

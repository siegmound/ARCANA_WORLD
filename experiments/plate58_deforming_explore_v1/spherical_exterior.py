"""R6 G3 A: spherical-surface source FEM metric and explicit-material weak form.

On each original T0 triangle, embed its vertices in R3, project nodal East/
North velocity DOFs onto the oriented facet basis, and form a P1 piecewise-flat
surface membrane B. Exact global rigid rotations are strain-free on this
faceted surface. This is NOT the exact smooth-sphere covariant ShellSet solver,
and is not an ARCANA material law, traction closure or T1 authorization.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.prepare import (
    RADIUS_M, _json, sha,
)
from experiments.plate58_deforming_explore_v1.exterior_variational import (
    triangle_B, integrated_viscosity_tensor,
)
from experiments.plate58_deforming_explore_v1.continuation_A import (
    SCHEMA as CONTINUATION_SCHEMA, STATUS as CONTINUATION_STATUS,
)
from experiments.plate58_deforming_explore_v1.g3_multiscale_interface import (
    SCHEMA as INTERFACE_SCHEMA, STATUS as INTERFACE_STATUS,
)

STATUS = "PASS_G3_A_SOURCE_SPHERICAL_FACET_AUDIT__G2_G3_PHYSICS_UNRESOLVED"
SCHEMA = "ARCANA_R6_G3_A_SOURCE_SPHERICAL_FACET_METRIC_AUDIT_V1"


class SphericalExteriorInputError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise SphericalExteriorInputError(message)


def frames_and_cartesian(lat_lon_deg, radius_m=RADIUS_M):
    ll = np.asarray(lat_lon_deg, dtype=float)
    need(ll.ndim == 2 and ll.shape[1] == 2 and
         bool(np.all(np.isfinite(ll))) and
         bool(np.all(np.abs(ll[:, 0]) <= 90)) and
         math.isfinite(float(radius_m)) and float(radius_m) > 0,
         "G3_SPHERE_INVALID_LATLON_OR_RADIUS")
    lat, lon = np.deg2rad(ll).T
    ca, sa = np.cos(lat), np.sin(lat)
    cl, sl = np.cos(lon), np.sin(lon)
    radial = np.column_stack((ca*cl, ca*sl, sa))
    east = np.column_stack((-sl, cl, np.zeros(len(ll))))
    north = np.column_stack((-sa*cl, -sa*sl, ca))
    return radial * radius_m, radial, east, north


def spherical_triangle_area(unit_xyz, radius_m=RADIUS_M):
    v = np.asarray(unit_xyz, dtype=float)
    need(v.shape == (3, 3) and np.all(np.isfinite(v)) and
         np.allclose(np.linalg.norm(v, axis=1), 1., atol=1e-12, rtol=0),
         "G3_SPHERE_AREA_INPUT_INVALID")
    numerator = abs(float(np.dot(v[0], np.cross(v[1], v[2]))))
    denominator = float(1. + v[0]@v[1] + v[1]@v[2] + v[2]@v[0])
    area = 2. * math.atan2(numerator, denominator) * radius_m**2
    need(math.isfinite(area) and area > 0, "G3_SPHERE_TRIANGLE_AREA_ZERO")
    return area


def spherical_triangle_geometry(lat_lon_deg, radius_m=RADIUS_M):
    xyz, radial, east, north = frames_and_cartesian(lat_lon_deg, radius_m)
    need(xyz.shape == (3, 3), "G3_SPHERE_TRIANGLE_VERTEX_COUNT")
    chord_a, chord_b = xyz[1]-xyz[0], xyz[2]-xyz[0]
    cross = np.cross(chord_a, chord_b)
    norm = float(np.linalg.norm(cross))
    need(np.linalg.norm(chord_a) > 0 and np.linalg.norm(chord_b) > 0 and
         norm > 1e-13 * np.linalg.norm(chord_a)*np.linalg.norm(chord_b),
         "G3_SPHERE_DEGENERATE_FACET")
    face_normal = cross / norm
    if face_normal @ np.mean(radial, axis=0) < 0:
        face_normal = -face_normal
    e1 = chord_a/np.linalg.norm(chord_a)
    e2 = np.cross(face_normal, e1)
    xy = np.column_stack(((xyz-xyz[0])@e1, (xyz-xyz[0])@e2))
    B, facet_area = triangle_B(xy)
    spherical_area = spherical_triangle_area(radial, radius_m)
    relative_deficit = abs(facet_area/spherical_area-1.)
    need(relative_deficit < 0.02,
         "G3_SPHERE_TRIANGLE_CURVATURE_TOO_LARGE")
    T = np.zeros((6, 6))
    for i in range(3):
        T[2*i:2*i+2, 2*i:2*i+2] = np.array([
            [np.dot(e1, east[i]), np.dot(e1, north[i])],
            [np.dot(e2, east[i]), np.dot(e2, north[i])]])
    return {
        "strain_operator": B@T,
        "facet_area_m2": float(facet_area),
        "spherical_area_m2": float(spherical_area),
        "facet_sphere_relative_area_deficit": float(relative_deficit),
        "global_xyz_m": xyz, "nodal_east": east, "nodal_north": north,
        "facet_normal": face_normal,
        "piecewise_flat_not_covariant_shellset": True}


def spherical_element_tangent(lat_lon_deg, eta_h_pa_s_m,
                              lambda_h_pa_s_m, radius_m=RADIUS_M):
    geometry = spherical_triangle_geometry(lat_lon_deg, radius_m)
    D = integrated_viscosity_tensor(eta_h_pa_s_m, lambda_h_pa_s_m)
    B = geometry["strain_operator"]
    K = geometry["facet_area_m2"]*(B.T@D@B)
    K = 0.5*(K+K.T)
    need(np.all(np.isfinite(K)), "G3_SPHERE_K_INVALID")
    return K, geometry


def assemble_spherical_exterior(node_order, triangle_parent_nodes,
                                node_latlon, triangle_materials,
                                radius_m=RADIUS_M):
    """No material defaults and no force/BC creation. Exact parent IDs."""
    ids = list(map(int, node_order))
    need(len(ids) > 3 and len(set(ids)) == len(ids) and
         all(i > 0 for i in ids), "G3_SPHERE_DUPLICATE_NODE_OWNER")
    triangles = {int(t): tuple(map(int, v))
                 for t, v in triangle_parent_nodes.items()}
    materials = {int(t): v for t, v in triangle_materials.items()}
    need(bool(triangles) and set(triangles) == set(materials) and
         all(len(t) == 3 and len(set(t)) == 3 and
             set(t).issubset(ids) for t in triangles.values()),
         "G3_SPHERE_MATERIAL_OR_ELEMENT_COVERAGE")
    ll = {int(i): np.asarray(v, dtype=float) for i, v in node_latlon.items()}
    need(set(ll) == set(ids) and all(
        v.shape == (2,) and np.all(np.isfinite(v)) for v in ll.values()),
        "G3_SPHERE_LATLON_COVERAGE")
    positions = {n: i for i, n in enumerate(ids)}
    K = np.zeros((2*len(ids), 2*len(ids)))
    facet, sphere, distortion = 0., 0., 0.
    for tid, triangle in sorted(triangles.items()):
        material = materials[tid]
        need(isinstance(material, dict) and
             material.get("authority") ==
                "ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED" and
             isinstance(material.get("source_reference"), str) and
             len(material["source_reference"].strip()) >= 10,
             "G3_SPHERE_MATERIAL_UNAUTHORIZED")
        ke, geo = spherical_element_tangent(
            np.stack([ll[n] for n in triangle]),
            material.get("eta_h_pa_s_m"),
            material.get("lambda_h_pa_s_m"), radius_m)
        dofs = [2*positions[n]+i for n in triangle for i in (0, 1)]
        K[np.ix_(dofs, dofs)] += ke
        facet += geo["facet_area_m2"]
        sphere += geo["spherical_area_m2"]
        distortion = max(distortion, geo["facet_sphere_relative_area_deficit"])
    K = 0.5*(K+K.T)
    need(np.all(np.isfinite(K)), "G3_SPHERE_GLOBAL_TANGENT_INVALID")
    return {
        "tangent": K, "facet_area_m2": facet,
        "spherical_geodesic_area_m2": sphere,
        "maximum_element_area_deficit_fraction": distortion,
        "source_triangle_count": len(triangles),
        "source_node_order": ids, "dof_count": len(K),
        "material_authorial_ratification": False,
        "shellset_covariant_and_nonlinear_parity": False,
        "physical_load": None, "physical_basal_support": None,
        "mechanical_solve_authorized": False, "physical_T1": None}


def source_geometry_audit(region, scale, feg):
    """Use authentic FEG node coordinates; no materials or loads."""
    width = int(region["cell_extent_per_side"])
    ids = list(map(int, region["parent_node_ids"]))
    faces = list(map(int, region["parent_triangle_ids"]))
    ex = set(map(int, scale["source_exterior_triangles"]))
    order = list(map(int, scale["mechanical_node_order_interface_first"]))
    need(width in (8, 16) and len(ids) == (width+1)**2 and
         len(faces) == 2*width**2 and len(feg.nodes) == len(ids) and
         len(feg.elements) == len(faces) and len(ex) == 2*width**2-8
         and len(order) == len(ids)-1,
         "G3_SPHERE_SOURCE_AUDIT_INVENTORY_CHANGED")
    need(len(set(ids)) == len(ids) and len(set(order)) == len(order) and
         set(order).issubset(ids) and len(set(faces)) == len(faces)
         and ex.issubset(faces) and len(scale["source_interface_node_ids"]) == 8
         and order[:8] == scale["source_interface_node_ids"],
         "G3_SPHERE_SOURCE_AUDIT_INTERFACE_CHANGED")
    ll = {n: (float(feg.nodes[i].latitude_deg),
              float(feg.nodes[i].longitude_deg))
          for i, n in enumerate(ids)}
    ntri, facet, sphere, distortion = 0, 0., 0., 0.
    worst_triangle, max_rigid_strain = None, 0.
    for tid, element in zip(faces, feg.elements, strict=True):
        if tid not in ex:
            continue
        triangle = tuple(ids[int(i)-1] for i in element.node_ids)
        need(len(set(triangle)) == 3 and set(triangle).issubset(order),
             "G3_SPHERE_SOURCE_AUDIT_TRIANGLE_PARENT_DRIFT")
        geo = spherical_triangle_geometry([ll[n] for n in triangle])
        facet += geo["facet_area_m2"]
        sphere += geo["spherical_area_m2"]
        if geo["facet_sphere_relative_area_deficit"] > distortion:
            distortion = geo["facet_sphere_relative_area_deficit"]
            worst_triangle = tid
        ntri += 1
        xyz, east, north = (geo["global_xyz_m"], geo["nodal_east"],
                            geo["nodal_north"])
        # A test angular velocity, NOT the canonical Euler rate.
        for omega in np.eye(3)*1e-15:
            vel = np.cross(omega, xyz)
            en = np.stack((np.einsum("ij,ij->i", vel, east),
                           np.einsum("ij,ij->i", vel, north)),
                          axis=1).ravel()
            max_rigid_strain = max(
                max_rigid_strain,
                float(np.linalg.norm(geo["strain_operator"]@en)))
    need(ntri == len(ex) and facet > 0 and sphere > 0
         and max_rigid_strain < 1e-23,
         "G3_SPHERE_SOURCE_AUDIT_RIGID_OR_AREA_FAILED")
    return {
        "extent_cells": width, "exterior_triangles": ntri,
        "mechanical_dofs": 2*len(order),
        "facet_total_area_m2": facet,
        "spherical_geodesic_total_area_m2": sphere,
        "relative_total_area_deficit": abs(facet/sphere-1),
        "max_element_area_deficit": distortion,
        "worst_source_parent_triangle_id": worst_triangle,
        "max_unit_test_rigid_rotation_strain_s_inv": max_rigid_strain,
        "rigid_rotation_test_omega_rad_s": 1e-15,
        "source_3plus_plate_junction_count":
            len(scale["actual_3plus_plate_junctions"]),
        "actual_3plus_plate_junction_parent_node_ids": [
            j["parent_node_id"] for j in scale["actual_3plus_plate_junctions"]],
        "kernel": "PIECEWISE_FLAT_EMBEDDED_SPHERE_P1_NEWTONIAN",
        "covariant_ShellSet_parity": False,
        "G2_effective_viscosity": None,
        "physical_operator": None,
        "mechanical_solve_authorized": False}


def audit_fair_source(multiscale_dir: Path, mechanical_dir: Path, output: Path):
    """SHA-bound spherical metric audit for the existing FAIR 8x8 and 16x16.

    No physical viscosity input is accepted; no K/f are produced.
    """
    need(not output.exists(), "G3_SPHERE_OUTPUT_ALREADY_EXISTS")
    multi_manifest = json.loads((multiscale_dir/"MANIFEST.json").read_text())
    interface_manifest = json.loads((mechanical_dir/"MANIFEST.json").read_text())
    multi = json.loads((multiscale_dir/"CONTINUATION_A.json").read_text())
    inter = json.loads((mechanical_dir/"MULTISCALE_INTERFACE.json").read_text())
    need(multi_manifest["status"] == multi["status"] == CONTINUATION_STATUS and
         multi["schema"] == CONTINUATION_SCHEMA and
         interface_manifest["status"] == inter["status"] == INTERFACE_STATUS and
         inter["schema"] == INTERFACE_SCHEMA and
         multi_manifest["no_solver_run"] and multi_manifest["no_T1"] and
         multi_manifest["no_canonical_promotion"] and
         interface_manifest["no_solver_run"] and interface_manifest["no_T1"]
         and interface_manifest["no_canonical_promotion"],
         "G3_SPHERE_UPSTREAM_AUTHORITY_OR_SCHEMA_CHANGED")
    need(all(sha(multiscale_dir/name) == digest
             for name, digest in multi_manifest["files"].items())
         and all(sha(mechanical_dir/name) == digest
                 for name, digest in interface_manifest["files"].items())
         and inter["source_multiscale_manifest_sha256"] ==
                sha(multiscale_dir/"MANIFEST.json")
         and inter["source_mesh_sha256"] == multi["source_mesh_sha256"]
         and inter["physically_assembled_tangent_by_scale"] is None
         and not inter["mechanical_solve_authorized"],
         "G3_SPHERE_UPSTREAM_SOURCE_SHA_OR_SOLVE_INVALID")
    regions = {int(x["cell_extent_per_side"]): x
               for x in multi["topological_comparative_extents"]}
    scales = {int(x["extent_cells_per_side"]): x for x in inter["scales"]}
    need(set(regions) == set(scales) == {8, 16},
         "G3_SPHERE_UPSTREAM_EXTENTS_CHANGED")
    audits = []
    for width in (8, 16):
        p = multiscale_dir/f"OUTER_A_{width:02d}x{width:02d}.feg"
        need(sha(p) == regions[width]["output_FEG_sha256"],
             "G3_SPHERE_PARENT_FEG_HASH_CHANGED")
        feg = parse_feg(p.read_text(), mode="SHELLS_READY")
        need(not feg.faults, "G3_SPHERE_FABRICATED_SOURCE_FAULT")
        audit = source_geometry_audit(regions[width], scales[width], feg)
        need(audit["source_3plus_plate_junction_count"] ==
             len(scales[width]["actual_3plus_plate_junctions"]),
             "G3_SPHERE_JUNCTION_INVENTORY_CHANGED")
        audits.append(audit)
    result = {
        "schema": SCHEMA, "status": STATUS,
        "numerical_radius_m": RADIUS_M,
        "numerical_radius_source":
            "experiments.plate58_deforming_explore_v1.prepare.RADIUS_M",
        "source_multiscale_manifest_sha256":
            sha(multiscale_dir/"MANIFEST.json"),
        "source_interface_manifest_sha256":
            sha(mechanical_dir/"MANIFEST.json"),
        "scales": audits,
        "G2_physical_viscosity": None, "G3_exterior_K": None,
        "G3_external_force": None, "G3_basal_support": None,
        "spherical_covariant_ShellSet_parity": False,
        "solver_runs": 0, "mechanical_solve_authorized": False,
        "physical_T1": None}
    output.mkdir(parents=True, exist_ok=False)
    (output/"SPHERICAL_AUDIT.json").write_bytes(_json(result))
    (output/"MANIFEST.json").write_bytes(_json({
        "schema": "ARCANA_R6_G3_A_SPHERICAL_FACET_AUDIT_MANIFEST_V1",
        "status": STATUS,
        "files": {"SPHERICAL_AUDIT.json":
                  sha(output/"SPHERICAL_AUDIT.json")},
        "source_multiscale_manifest_sha256":
            result["source_multiscale_manifest_sha256"],
        "source_interface_manifest_sha256":
            result["source_interface_manifest_sha256"],
        "no_solver_run": True, "no_T1": True,
        "no_canonical_promotion": True}))
    return {
        "status": STATUS,
        "scales": [{
            "extent": a["extent_cells"],
            "triangles": a["exterior_triangles"],
            "max_area_deficit": a["max_element_area_deficit"],
            "total_relative_area_deficit": a["relative_total_area_deficit"],
            "max_rigid_rotation_strain_s_inv":
                a["max_unit_test_rigid_rotation_strain_s_inv"],
            "actual_3plus_plate_junction_parent_node_ids":
                a["actual_3plus_plate_junction_parent_node_ids"],
        } for a in audits],
        "mechanical_solve_authorized": False,
        "solver_runs": 0, "physical_T1": None}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("multiscale", type=Path)
    p.add_argument("mechanical_interface", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    print(json.dumps(audit_fair_source(
        args.multiscale, args.mechanical_interface, args.output), indent=2))

"""ARCANA R6 moving 3D regional contact-gap audit with optional parallel extents.

ENGINEERING ONLY: reconstruct split plate-material point trajectories from
*the previously verified fixed-T0 KKT test* by exact Euler SO(3) + residual
nodal displacement, without Euler double counting. Update source boundary-edge
normals from deformed geometries. Diagnose real signed 3D oriented gaps vs
fixed-source T0 integrated gaps. DOES NOT solve 3D geometry contact KKT,
real G2/G3, or canonical T1. 8x8/16x16 independent jobs may run in parallel.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import time

import numpy as np
from scipy.spatial.transform import Rotation

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT, RADIUS_M, source_inputs, sha256, usage,
)
from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import (
    contact_registry, assemble_split_source, euler_source_en,
)
from experiments.plate58_deforming_explore_v1.g2_regional_unilateral_contact_time import (
    normal_constraint_matrix, integrate,
)
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian

STATUS = "PASS_SOURCE_MOVING_3D_CONTACT_GEOMETRY_DIAGNOSTIC__CONTACT_PHYSICS_OPEN"
SCHEMA = "ARCANA_R6_SOURCE_MOVING_3D_CONTACT_GAP_AND_PARALLEL_V1"
YEARS = (100, 500, 1000)


def need(test, code):
    if not test:
        raise SparseP1Error(code)


def unit(x):
    values = np.asarray(x, dtype=np.float64)
    mag = float(np.linalg.norm(values))
    need(np.all(np.isfinite(values)) and math.isfinite(mag) and mag > 1e-20,
         "MOVING3D_UNIT_VECTOR_DEGENERATE")
    return values / mag


def rigid_motion_with_residual(
    xyz, east, north, plates, omegas, initial_Euler_EN,
    displacement_EN, velocity_EN, year, radius_m=RADIUS_M,
):
    """Use x(t)=R_p(t) normalize_R[x0 + E0 (u(t)-t*gEuler)].

    Explicit Euler component was already included in regional displacement.
    Source rotation rates are radians/model-year. The fixed-frame residual
    velocity is v(t)-gEuler. This is a diagnostic trajectory, NOT an
    objective finite-strain FEM constitutive update.
    """
    xyz = np.asarray(xyz, dtype=float)
    east = np.asarray(east, dtype=float)
    north = np.asarray(north, dtype=float)
    plates = np.asarray(plates, dtype=int)
    n = len(plates)
    base_g = np.asarray(initial_Euler_EN, dtype=float).reshape(n, 2)
    u = np.asarray(displacement_EN, dtype=float).reshape(n, 2)
    v = np.asarray(velocity_EN, dtype=float).reshape(n, 2)
    t = float(year)
    need(xyz.shape == east.shape == north.shape == (n, 3) and
         n > 0 and t >= 0 and math.isfinite(t) and
         math.isfinite(float(radius_m)) and radius_m > 0 and
         np.all(np.isfinite(xyz)) and np.all(np.isfinite(east)) and
         np.all(np.isfinite(north)) and np.all(np.isfinite(base_g)) and
         np.all(np.isfinite(u)) and np.all(np.isfinite(v)),
         "MOVING3D_MATERIAL_TRAJECTORY_INPUT_INVALID")
    residual = u - t * base_g
    d_residual = v - base_g
    offset = east * residual[:, 0, None] + north * residual[:, 1, None]
    d_offset = east * d_residual[:, 0, None] + north * d_residual[:, 1, None]
    raw = xyz + offset
    length = np.linalg.norm(raw, axis=1)
    need(np.all(length > 0.5 * radius_m),
         "MOVING3D_RADIAL_PROJECTION_INVALID")
    source_pos = radius_m * raw / length[:, None]
    raw_dot = np.einsum("ij,ij->i", raw, d_offset)
    source_rate = radius_m * (
        d_offset / length[:, None] -
        raw * (raw_dot / length**3)[:, None]
    )
    pos = np.empty_like(xyz)
    rate = np.empty_like(xyz)
    rotations = {}
    for p in sorted(np.unique(plates).tolist()):
        o = np.asarray(omegas[int(p)], dtype=float)
        need(o.shape == (3,) and np.all(np.isfinite(o)),
             "MOVING3D_SOURCE_EULER_RATE_INVALID")
        Q = Rotation.from_rotvec(o * t).as_matrix()
        idx = np.flatnonzero(plates == p)
        x = source_pos[idx] @ Q.T
        pos[idx] = x
        rate[idx] = source_rate[idx] @ Q.T + np.cross(o, x)
        rotations[int(p)] = Q
    need(np.all(np.isfinite(pos)) and np.all(np.isfinite(rate)),
         "MOVING3D_TRAJECTORY_NONFINITE")
    return pos, rate, rotations


def boundary_node_edges(rows, registry):
    """No invented contacts. Every pair-node link belongs to original IDs."""
    found = defaultdict(list)
    legitimate = set(registry["edges"].keys())
    for row in rows:
        edge = tuple(sorted(map(int, row["source_edge_node_ids"])))
        pair = tuple(sorted(map(int, row["plate_pair"])))
        label = row["source_boundary_id"]
        need(edge in legitimate and registry["edges"][edge] == pair and
             isinstance(label, str) and label.startswith("R6BND-T0-"),
             "MOVING3D_BOUNDARY_PROVENANCE_MISMATCH")
        for n in edge:
            found[(pair, int(n))].append((edge, label))
    expected = {(tuple(x["plate_pair"]), int(x["parent_node_id"]))
                for x in registry["contacts"]}
    need(set(found) == expected,
         "MOVING3D_PARENT_CONTACT_LINK_COVERAGE_MISMATCH")
    return {k: sorted(v) for k, v in found.items()}


def moving_contact_geometry(
    positions, velocities, rotations, source_east, source_north,
    index, links, incident, gap_T0, reactions,
):
    """Signed 3D normal gap from CURRENT twin boundary-edge geometry.

    Each edge tangent is the mean of the two moved plate-edge directions.
    Current contact-plane normal = radial x tangent, oriented with the
    transported source pair-normal. Source edge/plate owners are preserved.
    This is a POINT-PAIR oriented gap, not a signed face-face separation.
    """
    positions = np.asarray(positions, dtype=float)
    velocities = np.asarray(velocities, dtype=float)
    gap = np.asarray(gap_T0, dtype=float).ravel()
    lam = np.asarray(reactions, dtype=float).ravel()
    need(positions.shape == velocities.shape and
         positions.ndim == 2 and positions.shape[1] == 3 and
         len(links) == len(gap) == len(lam) > 0,
         "MOVING3D_CONTACT_SAMPLE_INVALID")
    rows = []
    for k, contact in enumerate(links):
        pair = tuple(map(int, contact["plate_pair"]))
        node = int(contact["parent_node_id"])
        p, q = pair
        i, j = index[(p, node)], index[(q, node)]
        xp, xq = positions[i], positions[j]
        vp, vq = velocities[i], velocities[j]
        radial = unit(xp + xq)
        normal0_EN = np.asarray(contact["normal_EN"], dtype=float)
        n0_p = (normal0_EN[0] * source_east[i] +
                normal0_EN[1] * source_north[i])
        n0_q = (normal0_EN[0] * source_east[j] +
                normal0_EN[1] * source_north[j])
        transported = unit(rotations[p] @ n0_p + rotations[q] @ n0_q)
        edge_normals = []
        provenance = []
        for (a, b), source_id in incident[(pair, node)]:
            a_p, b_p = index[(p, a)], index[(p, b)]
            a_q, b_q = index[(q, a)], index[(q, b)]
            edge_vec = .5 * (
                (positions[b_p] - positions[a_p]) +
                (positions[b_q] - positions[a_q])
            )
            need(np.linalg.norm(edge_vec) > 1e-5,
                 "MOVING3D_DEGENERATE_DEFORMED_SOURCE_EDGE")
            candidate = unit(np.cross(radial, edge_vec))
            if float(candidate @ transported) < 0:
                candidate = -candidate
            need(float(candidate @ transported) > 0.5,
                 "MOVING3D_CONTACT_NORMAL_ORIENTATION_AMBIGUOUS")
            edge_normals.append(candidate)
            provenance.append(source_id)
        current_normal = unit(np.sum(edge_normals, axis=0))
        direction = xq - xp
        signed_gap = float(direction @ current_normal)
        slip = float(np.linalg.norm(direction -
                                    signed_gap * current_normal))
        normal_rate = float((vq - vp) @ current_normal)
        source_difference = float(signed_gap - gap[k])
        # Equal/opposite artificial force at two different material
        # nodes generates a moment; record this and never claim 0 torque.
        reaction_torque = np.cross(direction, lam[k] * current_normal)
        rows.append({
            "parent_node_id": node,
            "plate_pair": list(pair),
            "source_boundary_ids": sorted(set(provenance)),
            "source_incident_edge_count": len(incident[(pair, node)]),
            "signed_geometric_point_pair_gap_m": signed_gap,
            "fixed_T0_integrated_gap_m": float(gap[k]),
            "signed_gap_difference_geometry_minus_T0_m": source_difference,
            "tangential_point_pair_slip_m": slip,
            "geometric_normal_relative_velocity_m_per_model_year": normal_rate,
            "normalized_source_KKT_reaction": float(lam[k]),
            "current_contact_normal_cartesian": current_normal.tolist(),
            "angle_normal_from_transported_T0_rad": math.acos(
                float(np.clip(current_normal @ transported, -1, 1))),
            "artificial_separated_material_point_force_couple_norm":
                float(np.linalg.norm(reaction_torque)),
            "no_force_unit_N_or_friction_claim": True,
        })
    gaps = np.asarray([r["signed_geometric_point_pair_gap_m"] for r in rows])
    differences = np.asarray(
        [r["signed_gap_difference_geometry_minus_T0_m"] for r in rows])
    active = np.asarray([r["normalized_source_KKT_reaction"] > 1e-9
                         for r in rows], dtype=bool)
    def summary(vals):
        return float(np.min(vals)), float(np.max(vals))
    min_gap, max_gap = summary(gaps)
    return {
        "source_contact_link_count": len(rows),
        "geometric_signed_gap_min_m": min_gap,
        "geometric_signed_gap_max_m": max_gap,
        "geometric_negative_signed_gap_link_count_1microm":
            int(np.count_nonzero(gaps < -1e-6)),
        "max_absolute_geometry_minus_T0_gap_m":
            float(np.max(np.abs(differences))),
        "active_KKT_link_count": int(np.count_nonzero(active)),
        "min_active_geometric_gap_m":
            None if not np.any(active) else float(np.min(gaps[active])),
        "max_active_absolute_geometry_minus_T0_gap_m":
            None if not np.any(active)
            else float(np.max(np.abs(differences[active]))),
        "maximum_current_normal_rotation_from_transport_rad":
            max(r["angle_normal_from_transported_T0_rad"] for r in rows),
        "total_artificial_separated_point_couple_norm":
            float(sum(r["artificial_separated_material_point_force_couple_norm"]
                      for r in rows)),
        "source_link_details": rows,
        "current_normals_updated_from_boundary_edges": True,
        "T0_KKT_geometry_closure_proved": False,
    }


def geometry_test_one_scale(width, multiscale, nodal, omegas):
    """Independent source-safe region computation. No worker writes files."""
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre, validate_column_for_potential,
    )
    began = time.perf_counter()
    width = int(width)
    need(width in (8, 16), "MOVING3D_REGION_EXTENT_INVALID")
    mdir, ndir = Path(multiscale), Path(nodal)
    model = json.loads((mdir / "CONTINUATION_A.json").read_text())
    nodal_doc = json.loads((ndir / "SOURCE_NODAL_ELEMENT_G2.json").read_text())
    regions = {int(x["cell_extent_per_side"]): x
               for x in model["topological_comparative_extents"]}
    nodal_scales = {int(x["extent_cells"]): x for x in nodal_doc["scales"]}
    need(set(regions) == set(nodal_scales) == {8, 16},
         "MOVING3D_SOURCE_REGION_SCOPE_CHANGED")
    r = regions[width]
    parent_ids = list(map(int, r["parent_node_ids"]))
    fpath = mdir / f"OUTER_A_{width:02d}x{width:02d}.feg"
    ppath = mdir / f"OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat"
    need(sha256(fpath) == r["output_FEG_sha256"] and
         sha256(ppath) == r["output_PRE_sha256"],
         "MOVING3D_SOURCE_FEG_PRE_SHA_INVALID")
    feg = parse_feg(fpath.read_text(), mode="SHELLS_READY")
    pre = parse_regional_pre(ppath, r["PRE_source_field_order"], parent_ids)
    need({str(k): v for k, v in pre.items()} ==
         {str(k): v for k, v in nodal_scales[width]["source_PRE_by_parent_node"].items()},
         "MOVING3D_SOURCE_PRE_NODAL_BINDING_CHANGED")
    for row in pre.values():
        validate_column_for_potential(row)
    ll = {parent_ids[i]: (float(n.latitude_deg), float(n.longitude_deg))
          for i, n in enumerate(feg.nodes)}
    faces = [tuple(parent_ids[int(n)-1] for n in e.node_ids)
             for e in feg.elements]
    plates = list(map(int, r["parent_triangle_plate_ids"]))
    registry = contact_registry(
        parent_ids, faces, plates, ll, r["source_contact_edges"]
    )
    need((width == 8 and set(plates) == {5, 8} and
          registry["triple_junction_parent_ids"] == []) or
         (width == 16 and set(plates) == {5, 8, 11} and
          34587 in registry["triple_junction_parent_ids"]),
         "MOVING3D_SOURCE_PLATE_TRIPLE_ID_MISMATCH")
    incident = boundary_node_edges(r["source_contact_edges"], registry)
    K, index, split_ll, plate_views, stats = assemble_split_source(
        parent_ids, faces, plates, ll, pre
    )
    g = euler_source_en(split_ll, plate_views, omegas)
    J = normal_constraint_matrix(registry["contacts"], index, K.shape[0])
    source_closing = int(np.count_nonzero(J @ g < -1e-12))
    need(source_closing == (0 if width == 8 else 4),
         "MOVING3D_SOURCE_EULER_CLOSING_INVENTORY_CHANGED")
    # Reconstruct the previous certified model from the same original
    # source and initial state; never use invented checkpoint vectors.
    trajectory = integrate(K, J, g, 1., 1000, checkpoints=YEARS)
    original_xyz, _, source_east, source_north = frames_and_cartesian(split_ll)
    checks = {}
    stamps = hashlib.sha256()
    for year in YEARS:
        state = trajectory["snapshots"][year]
        moved, velocity, R = rigid_motion_with_residual(
            original_xyz, source_east, source_north, plate_views,
            omegas, g, state["displacement"], state["velocity"], year,
        )
        geo = moving_contact_geometry(
            moved, velocity, R, source_east, source_north,
            index, registry["contacts"], incident,
            state["gap"], state["lambda"],
        )
        # Source-referenced, deterministic checkpoint fingerprint for
        # serial-vs-parallel equivalence.
        stamps.update(np.asarray(state["displacement"],
                                dtype="<f8").tobytes())
        stamps.update(np.asarray(state["gap"], dtype="<f8").tobytes())
        stamps.update(np.asarray(
            [row["signed_geometric_point_pair_gap_m"]
             for row in geo["source_link_details"]], dtype="<f8").tobytes())
        checks[str(year)] = geo
    return {
        "extent": width,
        "source_plates": sorted(set(plates)),
        "source_parent_nodes": len(parent_ids),
        "source_source_triangles": len(faces),
        "plate_local_views": stats["source_nodes"],
        "source_contact_edges": len(registry["edges"]),
        "source_contact_pair_node_links": len(registry["contacts"]),
        "source_triple_junction_ids": registry["triple_junction_parent_ids"],
        "source_initial_closing_links": source_closing,
        "prior_fixed_T0_KKT_max_force_residual":
            trajectory["max_force_residual"],
        "prior_fixed_T0_KKT_complementarity":
            trajectory["max_scaled_complementarity"],
        "prior_fixed_T0_min_gap_over_run_m": trajectory["min_gap_over_run"],
        "objective_geometry_reconstruction_at_years": checks,
        "computed_field_sha256": stamps.hexdigest(),
        "worker_wall_seconds": time.perf_counter() - began,
        "worker_process_memory": usage(),
    }


def certify_priors(multiscale, nodal, unilateral, root):
    """Strict preflight: every prior output SHA and original source is pinned."""
    mdir, ndir, prior = map(Path, (multiscale, nodal, unilateral))
    um = json.loads((prior / "MANIFEST.json").read_text())
    ur = json.loads((prior / "REPORT.json").read_text())
    mm = json.loads((mdir / "MANIFEST.json").read_text())
    nm = json.loads((ndir / "MANIFEST.json").read_text())
    ndoc = json.loads((ndir / "SOURCE_NODAL_ELEMENT_G2.json").read_text())
    need(um["schema"] == "ARCANA_R6_REGIONAL_UNILATERAL_MANIFEST_V1"
         and um["files"]["REPORT.json"] == sha256(prior / "REPORT.json")
         and ur["status"] ==
         "PASS_SOURCE_REGIONAL_UNILATERAL_COMPLEMENTARITY_TIME__MOVING_GEOMETRY_OPEN"
         and ur["physical_T1"] is None and ur["D_024"] == "ACTIVE",
         "MOVING3D_PRIOR_UNILATERAL_SHA_OR_STATUS_INVALID")
    need(mm["files"]["CONTINUATION_A.json"] ==
         sha256(mdir / "CONTINUATION_A.json") and
         nm["files"]["SOURCE_NODAL_ELEMENT_G2.json"] ==
         sha256(ndir / "SOURCE_NODAL_ELEMENT_G2.json") and
         ndoc["source_multiscale_manifest_sha256"] ==
         sha256(mdir / "MANIFEST.json"),
         "MOVING3D_INPUT_REGIONAL_SHA_MISMATCH")
    need(len(ur["scales"]) == 2 and
         {int(s["extent"]) for s in ur["scales"]} == {8, 16} and
         all(s["restart_500_plus_500_m"] == 0 for s in ur["scales"]),
         "MOVING3D_PREVIOUS_KKT_SCALE_OR_RESTART_INVALID")
    old = ur.get("source_sha256", {})
    need(all(sha256(Path(path)) == checksum
             for path, checksum in old.items()),
         "MOVING3D_PRIOR_UNILATERAL_SOURCE_PINS_CHANGED")
    files = [mdir / "MANIFEST.json", mdir / "CONTINUATION_A.json",
             ndir / "MANIFEST.json", ndir / "SOURCE_NODAL_ELEMENT_G2.json",
             prior / "REPORT.json", prior / "MANIFEST.json",
             root / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
             root / "R6_T0_CANONICAL_PLATE_KINEMATICS.json"]
    return {str(p): sha256(p) for p in files}


def compare_serial_parallel(parallel, serial):
    """Deterministic hashes exclude wall time; false PASS is forbidden."""
    by_extent = lambda value: {int(row["extent"]): row for row in value}
    a, b = by_extent(parallel), by_extent(serial)
    need(set(a) == set(b) == {8, 16},
         "MOVING3D_PARALLEL_SCALE_MISMATCH")
    for extent in (8, 16):
        need(a[extent]["computed_field_sha256"] ==
             b[extent]["computed_field_sha256"],
             "MOVING3D_PARALLEL_NUMERICAL_PARITY_FAILED")
    return {"status": "PASS_EXACT_NUMERICAL_SHA256_PARITY",
            "scales_compared": [8, 16]}


def execute(multiscale, nodal, prior, output, root=ROOT,
            workers=1, verify_serial_parity=False):
    root = Path(root)
    out = Path(output)
    need(not out.exists(), "MOVING3D_OUTPUT_EXISTS")
    workers = int(workers)
    need(workers in (1, 2), "MOVING3D_WORKERS_OUT_OF_RANGE")
    began = time.perf_counter()
    pinned = certify_priors(multiscale, nodal, prior, root)
    mesh, omega, pins, horizon, meta = source_inputs(root)
    need(horizon > 1000, "MOVING3D_SOURCE_EULER_HORIZON_INVALID")
    omegas = {int(k): np.asarray(v, dtype=float) for k, v in omega.items()}
    args = [(width, str(multiscale), str(nodal), omegas)
            for width in (8, 16)]
    calculation_start = time.perf_counter()
    if workers == 1:
        results = [geometry_test_one_scale(*x) for x in args]
    else:
        # Spawn avoids inherited BLAS/LU state; each worker only reads
        # original sealed files. Never parallelize dependent time steps.
        with ProcessPoolExecutor(
            max_workers=2, mp_context=mp.get_context("spawn")
        ) as pool:
            results = list(pool.map(geometry_test_one_scale, *zip(*args)))
    parallel_or_serial_wall_s = time.perf_counter() - calculation_start
    results.sort(key=lambda row: row["extent"])
    # Compare reconstructed T0-normal gap with the exact prior sealed
    # engineering run before evaluating geometric differences.
    previous = json.loads((Path(prior) / "REPORT.json").read_text())
    earlier = {int(x["extent"]): x for x in previous["scales"]}
    need(set(earlier) == {8, 16},
         "MOVING3D_PRIOR_REGION_INVENTORY_INVALID")
    for region in results:
        old = earlier[int(region["extent"])]
        need(region["source_contact_pair_node_links"] ==
             old["source_contact_pair_links"] and
             region["plate_local_views"] == old["source_plate_local_views"] and
             region["source_initial_closing_links"] ==
             old["Euler_initial_closing_link_count"],
             "MOVING3D_PRIOR_TO_RECONSTRUCTED_SCOPE_CHANGED")
        for year in (100, 1000):
            fields = region["objective_geometry_reconstruction_at_years"][
                str(year)]["source_link_details"]
            oldyear = old["horizons"][str(year)]
            gap_min = min(x["fixed_T0_integrated_gap_m"] for x in fields)
            gap_max = max(x["fixed_T0_integrated_gap_m"] for x in fields)
            activated = sum(x["normalized_source_KKT_reaction"] >
                            1e-9 for x in fields)
            need(abs(gap_min-oldyear["min_normal_contact_gap_m"]) <
                 1e-8 and
                 abs(gap_max-oldyear["max_normal_contact_gap_m"]) <
                 1e-8 and
                 activated == oldyear["active_contact_links"],
                 "MOVING3D_PRIOR_KKT_CHECKPOINT_RECONSTRUCTION_MISMATCH")
    serial_reference = None
    if verify_serial_parity and workers > 1:
        serial_start = time.perf_counter()
        reference = [geometry_test_one_scale(*x) for x in args]
        serial_wall = time.perf_counter() - serial_start
        parity = compare_serial_parallel(results, reference)
        serial_reference = {
            **parity,
            "measured_serial_wall_seconds": serial_wall,
            "measured_parallel_wall_seconds": parallel_or_serial_wall_s,
            "observed_speedup_serial_over_parallel":
                serial_wall / max(parallel_or_serial_wall_s, 1e-9),
        }
    need(all(sha256(Path(p)) == checksum for p, checksum in pinned.items()),
         "MOVING3D_PROVENANCE_CHANGED_DURING_RUN")
    all_links = []
    for region in results:
        for horizon in ("100", "500", "1000"):
            all_links.extend(region["objective_geometry_reconstruction_at_years"][
                horizon]["source_link_details"])
    any_negative = any(
        x["signed_geometric_point_pair_gap_m"] < -1e-6
        for x in all_links
    )
    report = {
        "schema": SCHEMA, "status": STATUS,
        "fair_source_head": "CHECK_OPERATOR_HEAD_FROM_GIT_REV_PARSE",
        "source_input_sha256": pinned,
        "source_world_mesh_sha256": mesh.normalized_sha256,
        "prior_unilateral_report_sha256": sha256(Path(prior) / "REPORT.json"),
        "regional_results": results,
        "worker_count": workers,
        "serial_parallel_exact_parity": serial_reference,
        "region_wall_seconds": parallel_or_serial_wall_s,
        "total_wall_seconds": time.perf_counter() - began,
        "operator_environment": {
            "cpu_visible_affinity_count": (
                len(os.sched_getaffinity(0))
                if hasattr(os, "sched_getaffinity") else os.cpu_count()
            ),
            "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
        },
        "peak_process_memory_parent": usage(),
        "worker_peak_memory_reported_per_region": True,
        "source_plate_Euler_motion_exact_SO3": True,
        "separated_Euler_from_material_residual": True,
        "current_edge_normals_updated": True,
        "3D_gap_is_signed_material_point_pair_projection": True,
        "true_face_face_minimum_clearance_measured": False,
        "3D_geometric_no_penetration_proved": False,
        "current_3D_contact_law_reaction_enforced": False,
        "negative_geometric_gaps_above_1um_detected": any_negative,
        "geometric_contact_closure_decision":
            "BLOCKED_NEGATIVE_GEOMETRIC_GAPS" if any_negative else
            "NOT_QUALIFIED_POINT_PAIR_DIAGNOSTIC_ONLY",
        "geological_material_calibrated": False,
        "natural_G3_forcing_provided": False,
        "physical_solver_runs": 0, "physical_T1": None,
        "D_024": "ACTIVE", "HistoryStore_modified": False,
    }
    out.mkdir(parents=True, exist_ok=False)
    p = out / "REPORT.json"
    p.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (out / "MANIFEST.json").write_text(json.dumps({
        "schema": "ARCANA_R6_SOURCE_MOVING_3D_CONTACT_DIAGNOSTIC_MANIFEST_V1",
        "status": STATUS,
        "files": {"REPORT.json": sha256(p)},
        "no_physical_solver_run": True, "no_T1": True,
        "no_canonical_promotion": True,
    }, indent=2) + "\n")
    return {
        "status": STATUS,
        "workers": workers,
        "serial_parallel_parity": serial_reference,
        "regional_summary": [{
            "extent": x["extent"],
            "source_contacts": x["source_contact_pair_node_links"],
            "source_triple_junction_ids": x["source_triple_junction_ids"],
            "checkpoints": {
                key: {k: v for k, v in check.items()
                      if k != "source_link_details"}
                for key, check in
                x["objective_geometry_reconstruction_at_years"].items()
            },
            "worker_wall_seconds": x["worker_wall_seconds"],
        } for x in results],
        "negative_geometric_gaps_detected": any_negative,
        "geometric_contact_closure_decision":
            report["geometric_contact_closure_decision"],
        "total_wall_seconds": report["total_wall_seconds"],
        "physical_solver_runs": 0, "physical_T1": None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multiscale", required=True, type=Path)
    ap.add_argument("--nodal", required=True, type=Path)
    ap.add_argument("--prior-unilateral", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--workers", type=int, choices=(1, 2), default=1)
    ap.add_argument("--verify-serial-parity", action="store_true")
    a = ap.parse_args()
    print(json.dumps(execute(a.multiscale, a.nodal, a.prior_unilateral,
                             a.output, a.root, a.workers,
                             a.verify_serial_parity), indent=2,
                     allow_nan=False))


if __name__ == "__main__":
    main()

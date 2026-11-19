"""ARCANA R6 full-planet T0 kinematic baseline, phase 1 (100 model years).

Noncanonical experiment: plate-local material views, passive PRE and measured
resources. No physical interface accommodation, no G2/G3, no T1 or HistoryStore.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import resource
import statistics
import subprocess
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "ARCANA_R6_GLOBAL_KINEMATIC_100Y_BASELINE_V1"
STATUS = "PASS_GLOBAL_T0_100Y_KINEMATIC_BASELINE__CONTACTS_UNRESOLVED"
NODES = 64_442
TRIANGLES = 128_880
PLATES = tuple(range(12))
CHECKPOINT_YEARS = (0, 50, 100)
DIAGNOSTIC_YEARS = (0, 1, 10, 50, 100)
IDENTITY_TOL = 1e-11
AREA_TOL_SR = 1e-11
RADIUS_M = 6_371_000.0


class BenchmarkError(ValueError):
    pass


def require(ok, explanation):
    if not ok:
        raise BenchmarkError(explanation)


def sha256(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, value: dict):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def rss_kib():
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except OSError:
        pass
    return None


def usage():
    x = resource.getrusage(resource.RUSAGE_SELF)
    return {"cpu_user_s": x.ru_utime, "cpu_sys_s": x.ru_stime,
            "peak_rss_kib": x.ru_maxrss, "instant_rss_kib": rss_kib()}


def unit_xyz(lat_lon):
    values = np.asarray(lat_lon, dtype=np.float64)
    require(values.ndim == 2 and values.shape[1] == 2, "LAT_LON_SHAPE_INVALID")
    lat, lon = np.deg2rad(values).T
    return np.column_stack((np.cos(lat) * np.cos(lon),
                            np.cos(lat) * np.sin(lon), np.sin(lat)))


def rotate_xyz(xyz, omega, years):
    """Vectorized quaternion formula, same geometry as finite_rotation.py."""
    xyz = np.asarray(xyz, dtype=np.float64)
    omega = np.asarray(omega, dtype=np.float64)
    t = float(years)
    require(xyz.ndim == 2 and xyz.shape[1] == 3 and
            omega.shape == (3,) and np.all(np.isfinite(xyz)) and
            np.all(np.isfinite(omega)) and math.isfinite(t) and t >= 0,
            "ROTATION_INPUT_INVALID")
    n = float(np.linalg.norm(omega))
    if n == 0.0 or t == 0.0:
        return xyz.copy()
    qv = omega * (math.sin(n*t/2.0)/n)
    qw = math.cos(n*t/2.0)
    cross = np.cross(qv, xyz)
    return xyz + 2.0*(qw*cross + np.cross(qv, cross))


def spherical_area_sr(xyz, triangles_zero_based):
    """Signed spherical area of SOURCE triangle topology for ONE plate view."""
    a, b, c = np.moveaxis(xyz[triangles_zero_based], 1, 0)
    dot = lambda x, y: np.einsum("ij,ij->i", x, y)
    det = dot(a, np.cross(b, c))
    return 2.0*np.arctan2(det, 1.0+dot(a, b)+dot(b, c)+dot(c, a))


def make_plate_views(face, plate, source_xyz, plate_ids):
    """Split triangles by plate without changing source node identities."""
    face = np.asarray(face, dtype=np.int64)
    plate = np.asarray(plate, dtype=np.int64)
    source_xyz = np.asarray(source_xyz, dtype=np.float64)
    require(face.ndim == 2 and face.shape[1] == 3 and
            plate.shape == (len(face),) and
            source_xyz.ndim == 2 and source_xyz.shape[1] == 3 and
            set(np.unique(plate).tolist()) == set(plate_ids),
            "PLATE_VIEW_SOURCE_TOPOLOGY_INVALID")
    views = {}
    for p in plate_ids:
        source_tri = face[plate == p] - 1
        ids = np.unique(source_tri)
        local_tri = np.searchsorted(ids, source_tri)
        require(np.array_equal(ids[local_tri], source_tri),
                "PLATE_LOCAL_FACE_LOOKUP_FAILED")
        coords = source_xyz[ids]
        area = spherical_area_sr(coords, local_tri)
        require(np.all(np.isfinite(area)) and np.all(area > 0),
                "SOURCE_TRIANGLE_SIGN_OR_AREA_INVALID")
        views[p] = {"ids": ids, "triangles": local_tri,
                    "source_xyz": coords, "area0": area}
    require(sum(len(v["triangles"]) for v in views.values()) == len(face),
            "TRIANGLE_OWNERSHIP_INCOMPLETE")
    return views


def build_views(mesh):
    face = np.asarray(mesh.triangles, dtype=np.int64)
    plate = np.asarray(mesh.triangle_plate_id, dtype=np.int64)
    require(face.shape == (TRIANGLES, 3) and plate.shape == (TRIANGLES,) and
            set(np.unique(plate).tolist()) == set(PLATES),
            "GLOBAL_TRIANGLE_OR_PLATE_INVENTORY_CHANGED")
    require(int(np.min(face)) == 1 and int(np.max(face)) <= NODES,
            "SOURCE_TRIANGLE_NODE_IDS_INVALID")
    source_xyz = unit_xyz(mesh.vertices_lat_lon)
    require(source_xyz.shape == (NODES, 3), "SOURCE_VERTEX_INVENTORY_CHANGED")
    return make_plate_views(face, plate, source_xyz, PLATES)


def shared_plate_nodes(views):
    """Source node identity shared by two plate material views; never infer owner."""
    pairs = {}
    keys = sorted(views)
    for p in keys:
        for q in keys:
            if q <= p:
                continue
            ids = np.intersect1d(views[p]["ids"], views[q]["ids"],
                                 assume_unique=True)
            if len(ids):
                pairs[(p, q)] = (np.searchsorted(views[p]["ids"], ids),
                                 np.searchsorted(views[q]["ids"], ids))
    require(bool(pairs), "NO_SHARED_PLATE_SOURCE_NODES")
    return pairs


def source_inputs(root):
    """Re-check canonical source pins, T0 first-segment policy and passive PRE."""
    from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
    from arcana_worldsim.r6.finite_rotation import rotate_vector_constant_euler

    files = ["R6_T0_CANONICAL_PLATE_KINEMATICS.json",
             "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json",
             "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json",
             "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json",
             "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json",
             "R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.json"]
    pins = {file: sha256(root/file) for file in files}
    euler = read_json(root/files[0])
    manifest = read_json(root/files[1])
    law = read_json(root/files[2])
    census = read_json(root/files[3])
    pre = read_json(root/files[4])
    closure = read_json(root/files[5])
    require(euler["time_ma"] == manifest["time_ma"] == 210 and
            manifest["canonical_parent_sha256"] == euler["parent_canonical_t0_sha256"] and
            manifest["payload"]["sha256"] == euler["parent_vector_partition_sha256"] and
            pre["projection_source_lineage"]["kinematics_sha256"] == euler["payload_identity_sha256"] and
            pre["projection_source_lineage"]["physical_geography_sha256"] == euler["parent_canonical_t0_sha256"] and
            pre["projection_source_lineage"]["vector_partition_sha256"] == euler["parent_vector_partition_sha256"],
            "T0_SOURCE_LINEAGE_INCONSISTENT")
    require("Hold the canonical t0 Euler state constant only through the first segment"
            in law["first_segment_policy"]["motion"], "FIRST_SEGMENT_POLICY_ABSENT")
    candidates = [float(row["earliest_modeled_initiation_elapsed_years"])
                  for row in census["candidates"]
                  if row["earliest_modeled_initiation_elapsed_years"] is not None]
    require(candidates and all(math.isfinite(t) and t > 0 for t in candidates),
            "INVALID_EVENT_CENSUS")
    horizon = min(candidates)
    require(100 < horizon, "100Y_EXCEEDS_SOURCE_EVENT_HORIZON")
    omegas = {int(p["plate_id"]): np.asarray(p["euler_vector_rad_per_year"], dtype=float)
              for p in euler["plates"]}
    require(len(euler["plates"]) == len(omegas) == len(PLATES) and
            set(omegas) == set(PLATES) and
            all(v.shape == (3,) and np.all(np.isfinite(v)) for v in omegas.values()),
            "SOURCE_EULER_INVENTORY_INVALID")
    pre_dat = root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
    pins[pre_dat.name] = sha256(pre_dat)
    require(pins[pre_dat.name] == pre["runtime_data_sha256"] and
            pre["node_count"] == NODES and len(pre["field_order"]) == 51,
            "PASSIVE_PRE_IDENTITY_OR_SCHEMA_MISMATCH")
    with pre_dat.open() as f:
        header = next(f).split()
        require(len(header) == 3 and int(header[2]) == NODES and
                header[0] == pre["header"]["magic"] and
                header[1] == pre["header"]["schema"],
                "PASSIVE_PRE_HEADER_CHANGED")
        count = 0
        for count, line in enumerate(f, 1):
            row = line.split()
            require(len(row) == 51 and int(row[0]) == count,
                    "PASSIVE_PRE_NODE_ORDER_OR_FIELD_COUNT_CHANGED")
        require(count == NODES, "PASSIVE_PRE_ROW_COUNT_MISMATCH")
    mesh = load_canonical_mesh(root)
    require(mesh.normalized_sha256 == closure["evidence"]["canonical_mesh_sha256"] and
            len(mesh.vertices_lat_lon) == NODES and
            len(mesh.triangles) == TRIANGLES, "GLOBAL_CANONICAL_MESH_SHA_MISMATCH")
    source = unit_xyz(mesh.vertices_lat_lon)
    for p in PLATES:
        i = p*413 % NODES
        expected = np.asarray(rotate_vector_constant_euler(source[i], omegas[p], 1.0))
        actual = rotate_xyz(source[[i]], omegas[p], 1.0)[0]
        require(float(np.max(np.abs(actual-expected))) <= 5e-15,
                "VECTORIZED_KERNEL_SOURCE_PRIMITIVE_PARITY_FAILED")
    return mesh, omegas, pins, horizon, pre


def compare_geometry(views, position, omegas, year, pairs):
    max_drift = max_norm = max_area = 0.0
    inverted = 0
    for p in PLATES:
        v = views[p]
        actual = position[p]
        direct = rotate_xyz(v["source_xyz"], omegas[p], year)
        max_drift = max(max_drift, float(np.max(np.abs(actual-direct))))
        max_norm = max(max_norm, float(np.max(np.abs(np.linalg.norm(actual, axis=1)-1.0))))
        a = spherical_area_sr(actual, v["triangles"])
        inverted += int(np.count_nonzero(a <= 0))
        max_area = max(max_area, float(np.max(np.abs(a-v["area0"]))))
    separations = []
    n = 0
    for (p, q), (pi, qi) in pairs.items():
        delta = np.linalg.norm(position[p][pi]-position[q][qi], axis=1)*RADIUS_M
        separations.append(delta)
        n += len(delta)
    gap = np.concatenate(separations)
    return {"model_year": year,
            "max_direct_vs_composed_xyz_unit": max_drift,
            "max_radial_norm_error": max_norm,
            "max_triangle_area_change_sr": max_area,
            "inverted_triangles": inverted,
            "shared_plate_pair_node_observations": n,
            "max_crossplate_source_node_separation_m": float(np.max(gap)),
            "p95_crossplate_source_node_separation_m": float(np.percentile(gap, 95)),
            "mean_crossplate_source_node_separation_m": float(np.mean(gap)),
            "separation_is_unresolved_contact_not_numerical_drift": True}


def save_checkpoint(folder, year, views, positions):
    path = folder/f"KINEMATIC_{year:03d}.npz"
    content = {"year": np.asarray([year], dtype=np.int64)}
    for p in PLATES:
        content[f"ids_{p}"] = views[p]["ids"]
        content[f"xyz_{p}"] = positions[p]
    with path.open("xb") as file:
        np.savez(file, **content)
    digest = sha256(path)
    with np.load(path, allow_pickle=False) as data:
        require(int(data["year"][0]) == year, "CHECKPOINT_TIME_MISMATCH")
        recovered = {}
        for p in PLATES:
            require(np.array_equal(data[f"ids_{p}"], views[p]["ids"]),
                    "CHECKPOINT_SOURCE_IDS_CHANGED")
            recovered[p] = data[f"xyz_{p}"].copy()
            require(np.array_equal(recovered[p], positions[p]),
                    "CHECKPOINT_READBACK_NOT_BIT_EXACT")
    return {"file": path.name, "sha256": digest,
            "byte_size": path.stat().st_size}, recovered


def run(output: Path, years=100, root=ROOT):
    require(years == 100, "PHASE1_ONLY_100Y_NOT_1000Y")
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    start = time.perf_counter()
    before = usage()
    load_start = time.perf_counter()
    mesh, omegas, pins, horizon, pre = source_inputs(root)
    views = build_views(mesh)
    pairs = shared_plate_nodes(views)
    positions = {p: views[p]["source_xyz"].copy() for p in PLATES}
    source_load_s = time.perf_counter()-load_start
    after_load = usage()
    output.mkdir(parents=True, exist_ok=False)
    checkpoints = []
    io_wall = 0.0
    tick = time.perf_counter()
    zero, recovered = save_checkpoint(output, 0, views, positions)
    require(all(np.array_equal(recovered[p], positions[p]) for p in PLATES),
            "ZERO_CHECKPOINT_FAILED")
    checkpoints.append(zero)
    io_wall += time.perf_counter()-tick
    milestones = {"0": compare_geometry(views, positions, omegas, 0, pairs)}
    step_wall = []
    step_cpu = []
    mid = None
    for year in range(1, years+1):
        start_step = time.perf_counter()
        start_cpu = time.process_time()
        for p in PLATES:
            positions[p] = rotate_xyz(positions[p], omegas[p], 1.0)
        step_cpu.append(time.process_time()-start_cpu)
        step_wall.append(time.perf_counter()-start_step)
        if year in DIAGNOSTIC_YEARS:
            milestones[str(year)] = compare_geometry(views, positions, omegas, year, pairs)
        if year in CHECKPOINT_YEARS:
            tick = time.perf_counter()
            chk, snapshot = save_checkpoint(output, year, views, positions)
            io_wall += time.perf_counter()-tick
            checkpoints.append(chk)
            if year == 50:
                mid = snapshot
    require(mid is not None and len(checkpoints) == 3, "MIDPOINT_CHECKPOINT_MISSING")
    for _ in range(50):
        for p in PLATES:
            mid[p] = rotate_xyz(mid[p], omegas[p], 1.0)
    resume_error = max(float(np.max(np.abs(mid[p]-positions[p]))) for p in PLATES)
    max_drift = max(row["max_direct_vs_composed_xyz_unit"] for row in milestones.values())
    max_norm = max(row["max_radial_norm_error"] for row in milestones.values())
    max_area = max(row["max_triangle_area_change_sr"] for row in milestones.values())
    require(max_drift <= IDENTITY_TOL and max_norm <= IDENTITY_TOL and
            max_area <= AREA_TOL_SR and resume_error <= IDENTITY_TOL and
            all(row["inverted_triangles"] == 0 for row in milestones.values()),
            "GLOBAL_100Y_NUMERICAL_ACCEPTANCE_FAILED")
    require(all(sha256(root/name) == digest for name, digest in pins.items()),
            "T0_TRACKED_OR_PASSIVE_SOURCE_CHANGED_DURING_BENCHMARK")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    report = {
        "code_source_commit": head,
        "schema": SCHEMA, "status": STATUS,
        "authority": "NONCANONICAL_GLOBAL_KINEMATIC_BASELINE_ONLY",
        "source_sha256": pins, "source_mesh_identity_sha256": mesh.normalized_sha256,
        "model_years": years, "start_age_ma": 210.0, "end_age_ma": 209.9999,
        "first_event_horizon_model_years": horizon,
        "grid": {"nodes": NODES, "triangles": TRIANGLES, "parent_faces": 64800,
                 "plates": len(PLATES),
                 "plate_local_material_point_views": sum(len(v["ids"]) for v in views.values()),
                 "shared_node_plate_pairs": len(pairs)},
        "passive_PRE": {"node_count": pre["node_count"],
                        "mode": "T0_SOURCE_ONLY_NO_THERMAL_EVOLUTION",
                        "data_sha256": pins["R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"]},
        "numerical_acceptance": {
            "max_xyz_drift_unit": max_drift,
            "max_radial_norm_error": max_norm,
            "max_triangle_area_change_sr": max_area,
            "restart_50_plus_50_xyz_error": resume_error,
            "numerical_tolerance_unit": IDENTITY_TOL,
            "triangle_area_tolerance_sr": AREA_TOL_SR,
            "all_milestones_accepted": True},
        "milestones": milestones, "checkpoints": checkpoints,
        "performance": {"source_load_wall_s": source_load_s,
                        "step_wall_sum_s": sum(step_wall),
                        "step_cpu_sum_s": sum(step_cpu),
                        "step_wall_p50_s": statistics.median(step_wall),
                        "step_wall_p95_s": float(np.percentile(step_wall, 95)),
                        "step_wall_max_s": max(step_wall),
                        "checkpoint_io_wall_s": io_wall,
                        "source_load_memory": after_load,
                        "final_before_report_memory": usage(),
                        "total_until_report_wall_s": time.perf_counter()-start,
                        "cpu_user_delta_s": usage()["cpu_user_s"]-before["cpu_user_s"],
                        "cpu_sys_delta_s": usage()["cpu_sys_s"]-before["cpu_sys_s"]},
        "unresolved_physics": {
            "G2": None, "G3_mechanical_continuation": None,
            "G3_basal_support": None, "global_deforming_solve": None,
            "T1": None, "HistoryStore": None},
        "solver_runs": 0, "physical_deforming_T1": None}
    write_json(output/"REPORT.json", report)
    members = {name: sha256(output/name)
               for name in sorted(p.name for p in output.iterdir() if p.is_file())}
    write_json(output/"MANIFEST.json", {
        "schema": "ARCANA_R6_GLOBAL_KINEMATIC_100Y_MANIFEST_V1",
        "status": STATUS, "files": members,
        "no_solver_run": True, "no_T1": True, "no_canonical_promotion": True,
        "source_sha256": pins})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path,
                        help="New exclusive external FAIR evidence directory")
    parser.add_argument("--years", type=int, default=100, choices=[100],
                        help="Phase 1 only")
    args = parser.parse_args()
    result = run(args.output, args.years)
    print(json.dumps({
        "status": result["status"], "model_years": result["model_years"],
        "grid": result["grid"],
        "numerical_acceptance": result["numerical_acceptance"],
        "performance": result["performance"],
        "solver_runs": 0, "physical_deforming_T1": None
    }, indent=2))

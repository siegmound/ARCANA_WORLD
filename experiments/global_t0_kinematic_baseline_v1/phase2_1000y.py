"""ARCANA R6 full-planet 1000-year T0 kinematic benchmark (Phase 2).

Strict continuation in methodology from the separately recorded 100Y FAIR
evidence. It does NOT continue a physical Earth/ARCANA world or author a T1.
All original source files and the Phase-1 evidence remain read-only.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import subprocess
import time

import numpy as np

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT, NODES, TRIANGLES, PLATES, STATUS as STATUS100, SCHEMA as SCHEMA100,
    IDENTITY_TOL, AREA_TOL_SR, require, source_inputs, build_views,
    shared_plate_nodes, rotate_xyz, compare_geometry, save_checkpoint, sha256,
    read_json, write_json, usage,
)

SCHEMA = "ARCANA_R6_GLOBAL_KINEMATIC_1000Y_BASELINE_V1"
STATUS = "PASS_GLOBAL_T0_1000Y_KINEMATIC_BASELINE__CONTACTS_UNRESOLVED"
PHASE1_COMMIT = "716a1ba770331cd759ee4703545893235b7696bc"
YEARS = 1000
CHECKPOINT_YEARS = (0, 1, 10, 100, 500, 1000)
DIAGNOSTIC_YEARS = (0, 1, 10, 100, 250, 500, 750, 1000)
PRIOR_MEMBERS = {
    "REPORT.json", "KINEMATIC_000.npz",
    "KINEMATIC_050.npz", "KINEMATIC_100.npz",
}


def validate_phase1_report(report, pins, mesh_hash, horizon):
    """Reject a phase-1 result that is not the qualified, same-source baseline."""
    require(report["status"] == STATUS100 and report["schema"] == SCHEMA100
            and report["code_source_commit"] == PHASE1_COMMIT
            and report["source_sha256"] == pins
            and report["source_mesh_identity_sha256"] == mesh_hash
            and report["model_years"] == 100
            and report["first_event_horizon_model_years"] == horizon
            and report["grid"]["nodes"] == NODES
            and report["grid"]["triangles"] == TRIANGLES
            and report["grid"]["plates"] == len(PLATES)
            and report["passive_PRE"]["mode"] == "T0_SOURCE_ONLY_NO_THERMAL_EVOLUTION"
            and report["passive_PRE"]["data_sha256"] ==
                pins["R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"]
            and report["solver_runs"] == 0
            and report["physical_deforming_T1"] is None,
            "PHASE1_REPORT_SOURCE_OR_AUTHORITY_MISMATCH")
    n = report["numerical_acceptance"]
    require(n["all_milestones_accepted"] is True and
            math.isfinite(float(n["max_xyz_drift_unit"])) and
            math.isfinite(float(n["max_radial_norm_error"])) and
            math.isfinite(float(n["max_triangle_area_change_sr"])) and
            math.isfinite(float(n["restart_50_plus_50_xyz_error"])) and
            0 <= n["max_xyz_drift_unit"] <= IDENTITY_TOL and
            0 <= n["max_radial_norm_error"] <= IDENTITY_TOL and
            0 <= n["max_triangle_area_change_sr"] <= AREA_TOL_SR and
            0 <= n["restart_50_plus_50_xyz_error"] <= IDENTITY_TOL and
            n["numerical_tolerance_unit"] == IDENTITY_TOL and
            n["triangle_area_tolerance_sr"] == AREA_TOL_SR and
            all(report["milestones"][str(y)]["inverted_triangles"] == 0
                for y in (0, 1, 10, 50, 100)),
            "PHASE1_NUMERICAL_ACCEPTANCE_MISSING")
    require(sorted(row["file"] for row in report["checkpoints"]) ==
            sorted(PRIOR_MEMBERS - {"REPORT.json"}),
            "PHASE1_CHECKPOINT_INVENTORY_CHANGED")


def load_prior_checkpoint(path, views, year):
    """No pickles or unverified owner IDs; read-only independent checkpoint."""
    require(path.name == f"KINEMATIC_{year:03d}.npz" and path.is_file(),
            "PHASE1_CHECKPOINT_MISSING")
    with np.load(path, allow_pickle=False) as data:
        require(int(data["year"][0]) == year and
                set(data.files) ==
                ({"year"} | {f"ids_{p}" for p in PLATES} |
                 {f"xyz_{p}" for p in PLATES}),
                "PHASE1_CHECKPOINT_SCHEMA_OR_YEAR_CHANGED")
        values = {}
        for p in PLATES:
            require(np.array_equal(data[f"ids_{p}"], views[p]["ids"]),
                    "PHASE1_CHECKPOINT_MATERIAL_IDS_CHANGED")
            x = data[f"xyz_{p}"]
            require(x.shape == views[p]["source_xyz"].shape and
                    np.all(np.isfinite(x)), "PHASE1_CHECKPOINT_XYZ_INVALID")
            values[p] = x.copy()
    return values


def verify_prior100(folder, pins, mesh_hash, horizon, views):
    """SHA-bind original 100Y FAIR receipt; never repair or mutate it."""
    require(folder.is_dir(), "PHASE1_EVIDENCE_DIRECTORY_MISSING")
    manifest_path = folder/"MANIFEST.json"
    manifest = read_json(manifest_path)
    require(manifest["schema"] == "ARCANA_R6_GLOBAL_KINEMATIC_100Y_MANIFEST_V1"
            and manifest["status"] == STATUS100
            and manifest["no_solver_run"] is True
            and manifest["no_T1"] is True
            and manifest["no_canonical_promotion"] is True
            and manifest["source_sha256"] == pins
            and set(manifest["files"]) == PRIOR_MEMBERS,
            "PHASE1_MANIFEST_INVALID")
    for name, expected in manifest["files"].items():
        require(sha256(folder/name) == expected, "PHASE1_MEMBER_HASH_MISMATCH:"+name)
    report = read_json(folder/"REPORT.json")
    validate_phase1_report(report, pins, mesh_hash, horizon)
    zero = load_prior_checkpoint(folder/"KINEMATIC_000.npz", views, 0)
    hundred = load_prior_checkpoint(folder/"KINEMATIC_100.npz", views, 100)
    return {
        "report": report,
        "prior_manifest_sha256": sha256(manifest_path),
        "prior_members": dict(manifest["files"]),
        "checkpoints": {0:zero, 100:hundred},
    }


def percentile(x, q):
    return float(np.percentile(np.asarray(x, dtype=float), q))


def replay(positions, omegas, count):
    for _ in range(count):
        for p in PLATES:
            positions[p] = rotate_xyz(positions[p], omegas[p], 1.0)
    return positions


def execute(output: Path, prior100: Path, root: Path=ROOT):
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    require(output.resolve() != prior100.resolve(), "OUTPUT_EQUALS_PRIOR_EVIDENCE")
    started = time.perf_counter()
    before = usage()
    tick = time.perf_counter()
    mesh, omegas, pins, horizon, pre = source_inputs(root)
    require(YEARS < horizon, "1000Y_OUTSIDE_FIRST_SEGMENT_EVENT_HORIZON")
    views = build_views(mesh)
    pairs = shared_plate_nodes(views)
    positions = {p:v["source_xyz"].copy() for p,v in views.items()}
    load_wall = time.perf_counter()-tick
    load_memory = usage()
    tick = time.perf_counter()
    prior = verify_prior100(prior100, pins, mesh.normalized_sha256, horizon, views)
    require(all(np.array_equal(positions[p], prior["checkpoints"][0][p])
                for p in PLATES), "PHASE1_AND_PHASE2_T0_NOT_BIT_EXACT")
    prior_verify_wall = time.perf_counter()-tick
    output.mkdir(parents=True, exist_ok=False)
    checkpoints = []
    checkpoint_io_wall = 0.0
    diagnostic_wall = 0.0
    durations = []
    cpu_durations = []
    window100 = []
    mid500 = None
    check100_exact = False
    tick = time.perf_counter()
    checkpoint0, readback = save_checkpoint(output, 0, views, positions)
    require(all(np.array_equal(readback[p], positions[p]) for p in PLATES),
            "PHASE2_CHECKPOINT_ZERO_READBACK_INVALID")
    checkpoints.append(checkpoint0)
    checkpoint_io_wall += time.perf_counter()-tick
    tick = time.perf_counter()
    milestones = {"0":compare_geometry(views,positions,omegas,0,pairs)}
    diagnostic_wall += time.perf_counter()-tick
    for year in range(1, YEARS+1):
        step_start = time.perf_counter()
        step_cpu_start = time.process_time()
        for p in PLATES:
            positions[p] = rotate_xyz(positions[p], omegas[p], 1.0)
        cpu_durations.append(time.process_time()-step_cpu_start)
        durations.append(time.perf_counter()-step_start)
        if year in DIAGNOSTIC_YEARS:
            tick = time.perf_counter()
            milestones[str(year)] = compare_geometry(
                views,positions,omegas,year,pairs)
            diagnostic_wall += time.perf_counter()-tick
        if year in CHECKPOINT_YEARS:
            tick = time.perf_counter()
            cp, snapshot = save_checkpoint(output,year,views,positions)
            checkpoint_io_wall += time.perf_counter()-tick
            checkpoints.append(cp)
            if year == 500:
                mid500 = snapshot
        if year == 100:
            check100_exact = all(np.array_equal(
                positions[p],prior["checkpoints"][100][p]) for p in PLATES)
            require(check100_exact, "100Y_PHASE1_PHASE2_STATE_NOT_BIT_EXACT")
        if year % 100 == 0:
            sl = slice(year-100,year)
            window100.append({
                "start_year":year-99,"end_year":year,
                "step_wall_sum_s":sum(durations[sl]),
                "step_cpu_sum_s":sum(cpu_durations[sl]),
                "step_wall_p95_s":percentile(durations[sl],95),
                "rss_kib":usage()["instant_rss_kib"],
            })
    require(check100_exact and mid500 is not None and len(checkpoints)==6,
            "PHASE2_CHECKPOINT_OR_PHASE1_JOIN_INCOMPLETE")
    replay_started=time.perf_counter()
    replay(mid500,omegas,500)
    replay_wall=time.perf_counter()-replay_started
    restart_error=max(float(np.max(np.abs(mid500[p]-positions[p]))) for p in PLATES)
    max_drift=max(m["max_direct_vs_composed_xyz_unit"] for m in milestones.values())
    max_norm=max(m["max_radial_norm_error"] for m in milestones.values())
    max_area=max(m["max_triangle_area_change_sr"] for m in milestones.values())
    require(max_drift <= IDENTITY_TOL and max_norm <= IDENTITY_TOL and
            max_area <= AREA_TOL_SR and restart_error <= IDENTITY_TOL and
            all(m["inverted_triangles"]==0 for m in milestones.values()),
            "PHASE2_1000Y_NUMERICAL_ACCEPTANCE_FAILED")
    require(all(sha256(root/name)==d for name,d in pins.items()),
            "GLOBAL_T0_SOURCE_CHANGED_DURING_PHASE2")
    require(sha256(prior100/"MANIFEST.json")==prior["prior_manifest_sha256"] and
            all(sha256(prior100/name)==digest
                for name,digest in prior["prior_members"].items()),
            "PHASE1_EVIDENCE_CHANGED_DURING_PHASE2")
    head=subprocess.run(
        ["git","-C",str(root),"rev-parse","HEAD"],
        capture_output=True,text=True,check=True).stdout.strip()
    report={
        "schema":SCHEMA,"status":STATUS,
        "source_commit":head,
        "scope":"NONCANONICAL_GLOBAL_KINEMATIC_AND_PASSIVE_T0_PRE_ONLY",
        "source_sha256":pins,
        "source_mesh_identity_sha256":mesh.normalized_sha256,
        "prior_phase1":{
            "code_source_commit":PHASE1_COMMIT,
            "manifest_sha256":prior["prior_manifest_sha256"],
            "report_sha256":prior["prior_members"]["REPORT.json"],
            "identity_at_100_years_bit_exact":check100_exact,
            "phase1_performance":prior["report"]["performance"],
        },
        "model_years":YEARS,
        "start_age_ma":210.0,"end_age_ma":209.999,
        "first_event_horizon_model_years":horizon,
        "grid":{
            "nodes":NODES,"triangles":TRIANGLES,"parent_faces":64800,
            "plates":len(PLATES),
            "plate_local_material_point_views":sum(len(v["ids"]) for v in views.values()),
            "shared_node_plate_pairs":len(pairs),
        },
        "passive_PRE":{
            "mode":"T0_SOURCE_ONLY_NO_THERMAL_EVOLUTION",
            "node_count":pre["node_count"],
            "sha256":pins["R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"],
        },
        "numerical_acceptance":{
            "max_xyz_drift_unit":max_drift,
            "max_radial_norm_error":max_norm,
            "max_triangle_area_change_sr":max_area,
            "restart_500_plus_500_xyz_error":restart_error,
            "prior_100y_prefix_bit_exact":check100_exact,
            "numerical_tolerance_unit":IDENTITY_TOL,
            "triangle_area_tolerance_sr":AREA_TOL_SR,
            "all_milestones_accepted":True,
        },
        "milestones":milestones,
        "checkpoints":checkpoints,
        "performance":{
            "source_load_wall_s":load_wall,
            "prior_100y_verification_wall_s":prior_verify_wall,
            "step_wall_sum_s":sum(durations),
            "step_cpu_sum_s":sum(cpu_durations),
            "step_wall_p50_s":statistics.median(durations),
            "step_wall_p95_s":percentile(durations,95),
            "step_wall_max_s":max(durations),
            "checkpoint_io_wall_s":checkpoint_io_wall,
            "geometry_diagnostics_wall_s":diagnostic_wall,
            "restart_replay_500y_wall_s":replay_wall,
            "source_load_memory":load_memory,
            "final_before_report_memory":usage(),
            "total_until_report_wall_s":time.perf_counter()-started,
            "cpu_user_delta_s":usage()["cpu_user_s"]-before["cpu_user_s"],
            "cpu_sys_delta_s":usage()["cpu_sys_s"]-before["cpu_sys_s"],
            "step_windows_100y":window100,
        },
        "kinematic_gap_is_unresolved_physical_interface_not_numeric_drift":True,
        "mechanics_and_G2_G3_applied":False,
        "thermal_PRE_evolved":False,
        "solver_runs":0,
        "physical_deforming_T1":None,
        "HistoryStore_writes":False,
    }
    write_json(output/"REPORT.json",report)
    members={path.name:sha256(path) for path in sorted(output.iterdir())
             if path.is_file()}
    write_json(output/"MANIFEST.json",{
        "schema":"ARCANA_R6_GLOBAL_KINEMATIC_1000Y_MANIFEST_V1",
        "status":STATUS,
        "files":members,
        "source_sha256":pins,
        "prior_manifest_sha256":prior["prior_manifest_sha256"],
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True,
    })
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output",type=Path,
                   help="Exclusive new FAIR output directory; must not already exist")
    p.add_argument("--prior100",required=True,type=Path,
                   help="Original successful Phase-1 FAIR output directory")
    p.add_argument("--years",type=int,choices=[1000],required=True,
                   help="Phase 2 only: explicitly 1000 years")
    a=p.parse_args()
    r=execute(a.output,a.prior100)
    print(json.dumps({
        "status":r["status"],
        "model_years":r["model_years"],
        "grid":r["grid"],
        "numerical_acceptance":r["numerical_acceptance"],
        "contact_at_year_1000":r["milestones"]["1000"],
        "performance":{k:v for k,v in r["performance"].items()
                       if k!="step_windows_100y"},
        "solver_runs":0,"physical_deforming_T1":None,
    },indent=2))


if __name__=="__main__":
    main()

"""ARCANA R6: G1(100/1000y) -> G2 passive-source integration audit.

Reads existing SHA-qualified global G1 checkpoints and the unchanged 51-field
T0 PRE G2 source. Checks mapping, whole-layer exact temperature bounds and
material-view metric preservation. It is NOT a mechanical or thermal evolution.
No G2 physical laws, G3 forces or history output are invented or evaluated.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    ROOT, NODES, PLATES, SCHEMA as G1_100_SCHEMA,
    STATUS as G1_100_STATUS, source_inputs, build_views, sha256,
)
from experiments.global_t0_kinematic_baseline_v1.phase2_1000y import (
    SCHEMA as G1_1000_SCHEMA, STATUS as G1_1000_STATUS,
    verify_prior100, load_prior_checkpoint,
)
from experiments.plate58_deforming_explore_v1.g2_exact_thermal_validity import (
    exact_layer_temperature_bounds_k, ThermalValidityError,
)

SCHEMA = "ARCANA_R6_G1_G2_PASSIVE_100_1000Y_AUDIT_V1"
PASS = "PASS_G1_G2_100_1000Y_PASSIVE_SOURCE_COUPLING__REAL_G2_PHYSICS_OPEN"
GAPS = "G1_G2_PASSIVE_MAPPING_PASS__G2_T0_SOURCE_COLUMN_GAPS_REPORTED"
REQUIRED = (
    "node_id", "crust_thickness_m", "mantle_lithosphere_thickness_m",
    "crust_density_kg_m3", "mantle_density_kg_m3", "lab_depth_m",
    "surface_temperature_k", "moho_temperature_k", "lab_temperature_k",
    "layer1_z0_m", "layer1_z1_m", "layer2_z0_m", "layer2_z1_m",
    "layer1_c0_k", "layer1_c1_k_m", "layer1_c2_k_m2",
    "layer1_c3_k_m3", "layer2_c0_k", "layer2_c1_k_m",
    "layer2_c2_k_m2", "layer2_c3_k_m3",
)


class CouplingError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise CouplingError(code)


def _record(file_line: np.ndarray, indices):
    return {k: float(file_line[i]) for k, i in indices.items()}


def assess_g2_column(pre: dict) -> dict:
    """A T0 source-geometry/thermal gate; NEVER judge real creep applicability."""
    try:
        c, m, rc, rm = (float(pre[k]) for k in (
            "crust_thickness_m", "mantle_lithosphere_thickness_m",
            "crust_density_kg_m3", "mantle_density_kg_m3"))
        z0, zc, zm, zb = (float(pre[k]) for k in
                         ("layer1_z0_m", "layer1_z1_m",
                          "layer2_z0_m", "layer2_z1_m"))
        lab = float(pre["lab_depth_m"])
    except (ValueError, KeyError, TypeError) as exc:
        raise CouplingError("G2_COLUMN_MISSING_OR_INVALID") from exc
    if not all(math.isfinite(v) for v in (c,m,rc,rm,z0,zc,zm,zb,lab)):
        return {"eligible":False,"reason":"NONFINITE_SOURCE_GEOMETRY"}
    if not (c>0 and m>0 and rc>0 and rm>0 and z0==0 and
            math.isclose(zc,c,abs_tol=1e-5,rel_tol=0) and
            math.isclose(zm,c,abs_tol=1e-5,rel_tol=0) and
            math.isclose(zb,c+m,abs_tol=1e-5,rel_tol=0) and
            math.isclose(lab,c+m,abs_tol=1e-5,rel_tol=0)):
        return {"eligible":False,"reason":"INVALID_SOURCE_LAYER_GEOMETRY"}
    try:
        t1=exact_layer_temperature_bounds_k(pre,1)
        t2=exact_layer_temperature_bounds_k(pre,2)
    except ThermalValidityError:
        return {"eligible":False,"reason":"INVALID_SOURCE_THERMAL_CUBIC"}
    def at(layer, depth):
        x=depth-float(pre[f"layer{layer}_z0_m"])
        return (((float(pre[f"layer{layer}_c3_k_m3"])*x+
                  float(pre[f"layer{layer}_c2_k_m2"]))*x+
                  float(pre[f"layer{layer}_c1_k_m"]))*x+
                  float(pre[f"layer{layer}_c0_k"]))
    try:
        pairs=((at(1,0.),float(pre["surface_temperature_k"])),
               (at(1,c),float(pre["moho_temperature_k"])),
               (at(2,c),float(pre["moho_temperature_k"])),
               (at(2,c+m),float(pre["lab_temperature_k"])))
    except (KeyError,TypeError,ValueError,OverflowError):
        return {"eligible":False,"reason":"INVALID_SOURCE_THERMAL_ANCHORS"}
    if not all(math.isfinite(a) and math.isfinite(b) and
               math.isclose(a,b,abs_tol=2e-5,rel_tol=0.)
               for a,b in pairs):
        return {"eligible":False,"reason":"THERMAL_PROFILE_ANCHOR_MISMATCH"}
    if max(t1[1],t2[1])>=1900.:
        return {"eligible":False,"reason":"GOVERNED_THERMAL_CEILING_VIOLATION"}
    return {"eligible":True,"crust_temperature_k":t1,
            "mantle_temperature_k":t2,
            "areal_column_mass_proxy_kg_m2":rc*c+rm*m,
            "thermal_LAB_is_not_mechanical_LAB":True}


def inspect_global_pre(path: Path, metadata: dict):
    """Read every genuine T0 node once; retain source field IDs and metadata."""
    order=metadata["field_order"]
    require(metadata["node_count"]==NODES and len(order)==51 and
            len(set(order))==51 and order[0]=="node_id" and
            set(REQUIRED).issubset(order), "G2_PRE_SCHEMA_MISMATCH")
    index={k:order.index(k) for k in REQUIRED}
    class_counts=collections.Counter()
    n=0
    minmax={"crust":[math.inf,-math.inf],
            "mantle":[math.inf,-math.inf],
            "areal_mass":[math.inf,-math.inf]}
    samples=[]
    with path.open(encoding="utf-8") as f:
        fields=f.readline().split()
        header=metadata["header"]
        require(fields==[header["magic"],header["schema"],str(NODES)],
                "G2_PRE_HEADER_MISMATCH")
        for line in f:
            n+=1
            arr=np.fromstring(line,sep=" ",dtype=np.float64)
            require(len(arr)==51 and n<=NODES and
                    bool(np.all(np.isfinite(arr))) and arr[0]==n,
                    "G2_PRE_ROW_OR_PARENT_ID_MISMATCH")
            p=_record(arr,index)
            status=assess_g2_column(p)
            if not status["eligible"]:
                class_counts[status["reason"]]+=1
                if len(samples)<10:
                    samples.append({"node_id":n,"reason":status["reason"]})
                continue
            class_counts["ELIGIBLE_SOURCE_COLUMN"]+=1
            for key,new in [("crust","crust_temperature_k"),
                            ("mantle","mantle_temperature_k")]:
                low,high=status[new]
                mm=minmax[key]
                mm[0]=min(mm[0],low)
                mm[1]=max(mm[1],high)
            val=status["areal_column_mass_proxy_kg_m2"]
            mm=minmax["areal_mass"]
            mm[0]=min(mm[0],val)
            mm[1]=max(mm[1],val)
    require(n==NODES,"G2_PRE_ROW_COUNT_MISMATCH")
    return {
        "node_count":n, "source_columns_eligible":class_counts["ELIGIBLE_SOURCE_COLUMN"],
        "invalid_or_unusable_reason_counts":{k:v for k,v in sorted(class_counts.items())
                                           if k!="ELIGIBLE_SOURCE_COLUMN"},
        "invalid_source_examples":samples,
        "source_temperature_bounds_K": {
            k:v if all(math.isfinite(x) for x in v) else None
            for k,v in minmax.items() if k!="areal_mass"},
        "source_areal_column_mass_proxy_kg_m2_range":
            minmax["areal_mass"] if all(math.isfinite(x) for x in minmax["areal_mass"]) else None,
        "material_density_thickness_transport_mode":"PASSIVE_BY_PARENT_NODE_ID__NO_EULERIAN_ADVECTION_OR_REMAP",
        "mineralogy_hydration_damage_stress_and_strain_rate_source":None,
        "physical_creep_law_validated":False,
    }


def triangle_metric_drift(source_xyz, moved_xyz, triangles):
    """Independent per-plate edge metric audit, NOT deformation across contacts."""
    source_xyz=np.asarray(source_xyz,dtype=float)
    moved_xyz=np.asarray(moved_xyz,dtype=float)
    faces=np.asarray(triangles,dtype=int)
    require(source_xyz.shape==moved_xyz.shape and source_xyz.ndim==2
            and source_xyz.shape[1]==3 and faces.ndim==2 and faces.shape[1]==3
            and bool(np.all(np.isfinite(moved_xyz)))
            and bool(np.all((faces>=0)&(faces<len(source_xyz)))),
            "G1_G2_METRIC_INPUT_INVALID")
    worst=0.
    for i,j in ((0,1),(1,2),(2,0)):
        initial=np.linalg.norm(source_xyz[faces[:,i]]-source_xyz[faces[:,j]],axis=1)
        evolved=np.linalg.norm(moved_xyz[faces[:,i]]-moved_xyz[faces[:,j]],axis=1)
        require(bool(np.all(initial>0)),"G1_G2_ZERO_SOURCE_EDGE")
        worst=max(worst,float(np.max(np.abs((evolved-initial)/initial))))
    return worst


def validate_1000_receipt(folder: Path, pins: dict, mesh_sha: str,
                          prior100_manifest_sha: str) -> tuple[dict,dict]:
    manifest=json.loads((folder/"MANIFEST.json").read_text())
    report=json.loads((folder/"REPORT.json").read_text())
    require(manifest["schema"]=="ARCANA_R6_GLOBAL_KINEMATIC_1000Y_MANIFEST_V1"
            and manifest["status"]==G1_1000_STATUS
            and manifest["no_solver_run"] is True
            and manifest["no_T1"] is True
            and manifest["no_canonical_promotion"] is True
            and manifest["source_sha256"]==pins
            and manifest["prior_manifest_sha256"]==prior100_manifest_sha,
            "G1_1000_MANIFEST_MISMATCH")
    expected={f"KINEMATIC_{i:03d}.npz" for i in (0,1,10,100,500,1000)}
    require(set(manifest["files"])==expected|{"REPORT.json"},
            "G1_1000_MEMBER_INVENTORY_MISMATCH")
    for name,sha in manifest["files"].items():
        require(sha256(folder/name)==sha,"G1_1000_MEMBER_SHA_MISMATCH:"+name)
    n=report["numerical_acceptance"]
    require(report["schema"]==G1_1000_SCHEMA and report["status"]==G1_1000_STATUS
            and report["model_years"]==1000
            and report["source_sha256"]==pins
            and report["source_mesh_identity_sha256"]==mesh_sha
            and report["prior_phase1"]["manifest_sha256"]==prior100_manifest_sha
            and report["prior_phase1"]["identity_at_100_years_bit_exact"] is True
            and report["solver_runs"]==0
            and report["physical_deforming_T1"] is None
            and report["thermal_PRE_evolved"] is False
            and report["mechanics_and_G2_G3_applied"] is False
            and n["all_milestones_accepted"] is True,
            "G1_1000_REPORT_SCOPE_OR_VALIDATION_MISMATCH")
    return manifest,report


def evaluate_checkpoints(views, checkpoint100, checkpoint1000,
                         prior100_checkpoint):
    results=[]
    for year, state in ((100,checkpoint100),(1000,checkpoint1000)):
        max_edge=0.
        max_norm=0.
        n_views=0
        for p in PLATES:
            ids=views[p]["ids"]
            moved=np.asarray(state[p])
            require(moved.shape==views[p]["source_xyz"].shape and
                    len(ids)==len(moved), "G1_G2_PARENT_ID_VIEW_MISMATCH")
            max_edge=max(max_edge,triangle_metric_drift(
                views[p]["source_xyz"],moved,views[p]["triangles"]))
            max_norm=max(max_norm,float(np.max(
                np.abs(np.linalg.norm(moved,axis=1)-1))))
            n_views+=len(ids)
        require(max_edge<=1e-10 and max_norm<=1e-10,
                "G1_G2_RIGID_METRIC_DRIFT_EXCEEDS_NUMERICAL_TOLERANCE")
        results.append({
            "year":year,
            "plate_material_views":n_views,
            "max_within_plate_relative_edge_length_change":max_edge,
            "max_unit_sphere_radial_error":max_norm,
            "PRE_node_binding_mode":"ORIGINAL_0_BASED_INDEX_PLUS_1__SAME_51_FIELD_T0_SOURCE",
            "G2_stress_or_creep_solution":None,
            "strain_across_5_8_11_contact_not_inferred":True,
        })
    require(all(np.array_equal(checkpoint100[p],prior100_checkpoint[p])
                for p in PLATES),"G1_100_PHASE1_PHASE2_NOT_BIT_IDENTICAL")
    return results


def run(prior100:Path,prior1000:Path,output:Path,root:Path=ROOT):
    require(not output.exists(),"G1_G2_OUTPUT_ALREADY_EXISTS")
    require(prior100.resolve()!=prior1000.resolve() and
            output.resolve() not in (prior100.resolve(),prior1000.resolve()),
            "G1_G2_EVIDENCE_PATH_ALIAS")
    mesh,omegas,pins,event_horizon,pre=source_inputs(root)
    require(event_horizon>1000,"G1_G2_EVENT_HORIZON_TOO_SHORT")
    views=build_views(mesh)
    old=verify_prior100(prior100,pins,mesh.normalized_sha256,event_horizon,views)
    pin100=sha256(prior100/"MANIFEST.json")
    m1000,r1000=validate_1000_receipt(prior1000,pins,mesh.normalized_sha256,pin100)
    pin1000=sha256(prior1000/"MANIFEST.json")
    hundred=load_prior_checkpoint(prior1000/"KINEMATIC_100.npz",views,100)
    thousand=load_prior_checkpoint(prior1000/"KINEMATIC_1000.npz",views,1000)
    checks=evaluate_checkpoints(views,hundred,thousand,old["checkpoints"][100])
    pre_path=root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
    source_pre_before=sha256(pre_path)
    require(source_pre_before==pins[pre_path.name],"G2_SOURCE_PIN_CHANGED")
    global_g2=inspect_global_pre(pre_path,pre)
    require(sha256(pre_path)==source_pre_before and
            sha256(prior100/"MANIFEST.json")==pin100 and
            sha256(prior1000/"MANIFEST.json")==pin1000 and
            all(sha256(prior1000/name)==value
                for name,value in m1000["files"].items()),
            "G1_G2_SOURCE_CHANGED_DURING_AUDIT")
    status=PASS if global_g2["source_columns_eligible"]==NODES else GAPS
    report={
        "schema":SCHEMA,"status":status,
        "scope":"ONE_WAY_G1_TO_G2_PASSIVE_T0_REPLAY_ONLY",
        "tested_years":[100,1000],
        "global_source_mesh_sha256":mesh.normalized_sha256,
        "source_PRE_SHA256":source_pre_before,
        "G1_100_manifest_SHA256":pin100,
        "G1_1000_manifest_SHA256":sha256(prior1000/"MANIFEST.json"),
        "G1_1000_numerical_acceptance":r1000["numerical_acceptance"],
        "G2_source_profile_audit":global_g2,
        "checks_by_year":checks,
        "full_1000_years_G2_material_time_evolution_performed":False,
        "G2_material_source_is_passive_unchanged_T0":True,
        "G2_constitutive_stress_feedback_to_G1":None,
        "real_G2_material_law":None,
        "G3_contact_forces_and_basal_support":None,
        "physical_G2_thermal_evolution":None,
        "G4_material_area_density_update":None,
        "material_mass_proxy_is_not_a_conserved_FEM_mass_result":True,
        "unresolved_contact_gaps_from_G1_are_not_numerical_instability":True,
        "mechanical_solve_authorized":False,"solver_runs":0,
        "physical_T1":None,"history_store_mutated":False,"D_024":"ACTIVE",
    }
    output.mkdir(parents=True,exist_ok=False)
    target=output/"REPORT.json"
    target.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    manifest={
        "schema":"ARCANA_R6_G1_G2_PASSIVE_100_1000Y_AUDIT_MANIFEST_V1",
        "status":status,
        "files":{"REPORT.json":sha256(target)},
        "source_PRE_SHA256":source_pre_before,
        "G1_100_manifest_SHA256":pin100,
        "G1_1000_manifest_SHA256":sha256(prior1000/"MANIFEST.json"),
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True}
    (output/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return {
        "status":status,"G2_columns_eligible":global_g2["source_columns_eligible"],
        "G2_source_gaps":global_g2["invalid_or_unusable_reason_counts"],
        "tests_by_year":checks,
        "solver_runs":0,"physical_T1":None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prior100",type=Path,required=True)
    p.add_argument("--prior1000",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(run(args.prior100,args.prior1000,args.output),indent=2))


if __name__=="__main__":
    main()

"""ARCANA R6 — source-bound G2/G3 candidate assembly runner (NO physical solve).

Reads verified FAIR multiscale FE, source interface, original PRE and G3
cut/basal inventory. An explicitly populated candidate input document is
REQUIRED. No default zero traction, mineralogy, hydration, pressure, or
contact law. Writes NONCANONICAL weak-form assembly, never T1/HistoryStore.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import hashlib

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.g2_g3_coupled_weak_form import (
    MODEL_FAMILY,integrate_coupled_candidate,CoupledAssemblyError,need,
)
from experiments.plate58_deforming_explore_v1.g3_force_budget import edge_key
from experiments.plate58_deforming_explore_v1.g2_g3_junction_source_guard import (
    certify_regional_junction, SourceJunctionError,
)

SCHEMA="ARCANA_R6_G2_G3_SOURCE_CONNECTED_EXPLICIT_CANDIDATE_RUNNER_V1"
INPUT_SCHEMA="ARCANA_R6_G2_G3_EXPLICIT_ENGINEERING_INPUT_V1"
SOURCE_TYPES={
    8:"SOURCE_ORIGINAL_8x8_5_8",
    16:"SOURCE_ORIGINAL_16x16_5_8_11",
}
EXPECTED={
    "multiscale":(
        "CONTINUATION_A.json",
        "PASS_G3_A_MULTISCALE_SOURCE_CONTINUATION__BC_AND_G2_UNRESOLVED"),
    "interface":(
        "MULTISCALE_INTERFACE.json",
        "PASS_G3_A_MULTISCALE_INTERFACE_AND_CONTACT_GRAPH__PHYSICS_UNRESOLVED"),
    "nodal":(
        "SOURCE_NODAL_ELEMENT_G2.json",
        "PASS_G2_SOURCE_NODAL_ELEMENT_BINDING__CONSTITUTIVE_AND_G3_FORCING_OPEN"),
    "force":(
        "FORCE_BUDGET_REQUIREMENTS.json",
        "PASS_G3_A_FORCE_SOURCE_INVENTORY__LOAD_PHYSICS_UNRESOLVED"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_pinned(name,folder):
    filename,status=EXPECTED[name]
    directory=Path(folder)
    manifest=json.loads((directory/"MANIFEST.json").read_text())
    result=json.loads((directory/filename).read_text())
    need(manifest["status"]==result["status"]==status
         and manifest["no_solver_run"] and manifest["no_T1"]
         and manifest["no_canonical_promotion"]
         and filename in manifest["files"]
         and all(sha(directory/f)==v for f,v in manifest["files"].items()),
         "G2_G3_COUPLED_UPSTREAM_AUTHENTIC_SHA_INVALID:"+name)
    return result,sha(directory/"MANIFEST.json")


def source_inputs(multiscale,interface,nodal,force,extent,scenario):
    need(extent in SOURCE_TYPES,"G2_G3_COUPLED_SCOPE_UNSUPPORTED")
    providers={}
    manifest_shas={}
    for name,path in (
        ("multiscale",multiscale),("interface",interface),
        ("nodal",nodal),("force",force)):
        providers[name],manifest_shas[name]=read_pinned(name,path)
    # Require provenance via the chained original source manifests, never
    # rely on matching only file names or user supplied asserted hashes.
    need(providers["interface"]["source_multiscale_manifest_sha256"]==
         manifest_shas["multiscale"]
         and providers["nodal"]["source_multiscale_manifest_sha256"]==
         manifest_shas["multiscale"]
         and providers["nodal"]["source_interface_manifest_sha256"]==
         manifest_shas["interface"]
         and providers["force"]["parent_multiscale_manifest_sha256"]==
         manifest_shas["multiscale"]
         and providers["force"]["parent_interface_manifest_sha256"]==
         manifest_shas["interface"]
         and providers["force"]["parent_G2_binding_manifest_sha256"]==
         manifest_shas["nodal"],
         "G2_G3_COUPLED_UPSTREAM_SOURCE_CHAIN_BROKEN")
    need(isinstance(scenario,dict) and
         scenario.get("schema")==INPUT_SCHEMA
         and scenario.get("authority")==
             "ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED"
         and scenario.get("physical_source_authority_ratified") is False
         and scenario.get("mechanical_solve_authorized") is False
         and scenario.get("scope_extent_cells")==extent,
         "G2_G3_COUPLED_EXPLICIT_INPUT_SCHEMA_OR_AUTHORITY_INVALID")
    need(scenario.get("source_manifest_sha256") == manifest_shas,
         "G2_G3_COUPLED_EXPLICIT_SCENARIO_SOURCE_SHA_MISMATCH")
    needs=("candidate_material_by_parent_node",
           "velocity_en_by_parent_node","line_tractions_by_edge",
           "basal_tractions_by_triangle","external_gpe")
    need(all(isinstance(scenario.get(key),dict)
             and bool(scenario[key]) for key in needs),
         "G2_G3_COUPLED_REAL_INPUT_PROVIDERS_ABSENT_NO_SILENT_DEFAULTS")
    regions={int(r["cell_extent_per_side"]):r for r in
             providers["multiscale"]["topological_comparative_extents"]}
    interfaces={int(r["extent_cells_per_side"]):r for r in
                providers["interface"]["scales"]}
    nodes={int(r["extent_cells"]):r for r in providers["nodal"]["scales"]}
    forces={int(r["extent_cells"]):r for r in providers["force"]["scales"]}
    need(set(regions)==set(interfaces)==set(nodes)==set(forces)=={8,16},
         "G2_G3_COUPLED_SOURCE_REGIONS_MISSING")
    reg,iface,nd,fr=(x[extent] for x in (
        regions,interfaces,nodes,forces))
    mdir=Path(multiscale)
    feg_path=mdir/f"OUTER_A_{extent:02d}x{extent:02d}.feg"
    pre_path=mdir/f"OUTER_A_{extent:02d}x{extent:02d}_PRE_T0_PASSIVE.dat"
    need(sha(feg_path)==reg["output_FEG_sha256"]
         and sha(pre_path)==reg["output_PRE_sha256"]
         and sha(pre_path)==nd["source_regional_PRE_sha256"],
         "G2_G3_COUPLED_ORIGINAL_FEG_PRE_PIN_DRIFT")
    feg=parse_feg(feg_path.read_text(),mode="SHELLS_READY")
    local_nodes=list(map(int,reg["parent_node_ids"]))
    need(len(feg.nodes)==len(local_nodes)
         and len(feg.elements)==len(reg["parent_triangle_ids"]),
         "G2_G3_COUPLED_FEG_SOURCE_MESH_CHANGED")
    coords={
        local_nodes[i]:[float(n.latitude_deg),float(n.longitude_deg)]
        for i,n in enumerate(feg.nodes)
    }
    # The global parent node 34587 can be present in the original 8x8
    # footprint WITHOUT a locally incident three-plate junction. Use the
    # source-authenticated interface provider to classify actual plate owners.
    try:
        junction=certify_regional_junction(local_nodes,iface,extent)
    except SourceJunctionError as exc:
        raise CoupledAssemblyError(
            "G2_G3_COUPLED_SOURCE_JUNCTION_TOPOLOGY_INVALID:"+str(exc)) from exc
    source_order=list(map(int,iface["mechanical_node_order_interface_first"]))
    valid_nd={int(n):v for n,v in
              nd["source_PRE_by_parent_node"].items()}
    bindings={int(k):v for k,v in nd["exterior_triangles"].items()}
    triangles={tid:tuple(map(int,x["parent_node_ids"]))
               for tid,x in bindings.items()}
    need(set(triangles)==set(map(int,iface["source_exterior_triangles"]))
         and {n for t in triangles.values() for n in t}==set(source_order)
         and set(source_order).issubset(valid_nd),
         "G2_G3_COUPLED_EXTERIOR_MECHANICAL_DOF_SOURCE_DRIFT")
    cuts=[]
    for c in fr["source_external_cut_edges"]:
        parents=list(map(int,c["source_parent_node_ids"]))
        need(c["source_edge_id"]==edge_key(parents),
             "G2_G3_COUPLED_ORIGINAL_CUT_ID_DRIFT")
        cuts.append({
            "source_parent_node_ids":parents,
            "side":c["side"],
            "adjacent_plate_id":int(c["adjacent_plate_id"]),
        })
    need(len(cuts)==4*extent and len(triangles)==2*extent*extent-8
         and len(source_order)==(extent+1)**2-1,
         "G2_G3_COUPLED_ORIGINAL_SOURCE_COUNTS_DRIFT")
    # Explicitly key every candidate channel to the checked source ID order.
    candidate={
        "scope":{
            "model_family":MODEL_FAMILY,
            "source_scope":SOURCE_TYPES[extent],
            "source_triple_parent_node_id":junction["local_triple_parent_id"],
            "source_parent_34587_present_in_footprint":
                junction["source_parent_34587_in_footprint"],
            "source_actual_3plus_plate_junctions":
                junction["source_actual_3plus_plate_junctions"],
            "junction_source_is_not_a_fault_slip_law":True,
            "physical_source_authority_ratified":False,
            "mechanical_solve_authorized":False,
            "interface_contact_authority":"UNQUALIFIED",
            "basal_normal_support_authority":"UNQUALIFIED",
            "constitutive_full_fault_law_authority":"UNQUALIFIED",
        },
        "node_order":source_order,
        "parent_triangle_nodes":triangles,
        "source_triangle_bindings":bindings,
        "node_lat_lon_deg":{n:coords[n] for n in source_order},
        "source_pre_by_parent_node":{n:valid_nd[n] for n in source_order},
        "candidate_material_by_parent_node":scenario[
            "candidate_material_by_parent_node"],
        "velocity_en_by_parent_node":scenario["velocity_en_by_parent_node"],
        "source_cut_edges":cuts,
        "line_tractions_by_edge":scenario["line_tractions_by_edge"],
        "basal_tractions_by_triangle":scenario["basal_tractions_by_triangle"],
        "gpe":scenario["external_gpe"],
    }
    return candidate,manifest_shas


def execute(*,multiscale,interface,nodal,force,scenario_path,
            extent,output):
    output=Path(output)
    need(not output.exists(),"G2_G3_COUPLED_OUTPUT_ALREADY_EXISTS")
    candidate_record=Path(scenario_path)
    scenario=json.loads(candidate_record.read_text())
    inputs,manifests=source_inputs(
        multiscale,interface,nodal,force,extent,scenario)
    result=integrate_coupled_candidate(**inputs)
    need(result["physical_mechanical_solve_authorized"] is False
         and result["physical_T1"] is None
         and result["physical_solver_runs"]==0
         and result["canonical_promotion"] is False,
         "G2_G3_COUPLED_UNAUTHORIZED_PHYSICAL_SOLUTION")
    result["verified_source_manifests_sha256"]=manifests
    result["supplied_candidate_sha256"]=sha(candidate_record)
    result["source_FEG_sha256"]=sha(
        Path(multiscale)/f"OUTER_A_{extent:02d}x{extent:02d}.feg")
    result["source_PRE_sha256"]=sha(
        Path(multiscale)/f"OUTER_A_{extent:02d}x{extent:02d}_PRE_T0_PASSIVE.dat")
    result["runner_schema"]=SCHEMA
    # Recheck input provenance before writing; never mutate prior evidence.
    for n,p in (
        ("multiscale",multiscale),("interface",interface),
        ("nodal",nodal),("force",force)):
        need(sha(Path(p)/"MANIFEST.json")==manifests[n],
             "G2_G3_COUPLED_SOURCE_MANIFEST_CHANGED_DURING_ASSEMBLY")
    need(sha(candidate_record)==result["supplied_candidate_sha256"],
         "G2_G3_COUPLED_EXPLICIT_INPUT_CHANGED_DURING_ASSEMBLY")
    output.mkdir(parents=True,exist_ok=False)
    rp=output/"REPORT.json"
    rp.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    (output/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_G2_G3_COUPLED_CANDIDATE_MANIFEST_V1",
        "status":result["status"],
        "files":{"REPORT.json":sha(rp)},
        "physical_T1":None,
        "no_canonical_promotion":True,
        "no_physical_solver_run":True,
    },indent=2)+"\n")
    return {
        "status":result["status"],
        "source_scope":result["source_scope"],
        "source_parent_triangle_count":result["source_parent_triangle_count"],
        "physical_T1":None,
        "D_024":"ACTIVE",
        "mechanical_solve_authorized":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",type=Path,required=True)
    p.add_argument("--interface",type=Path,required=True)
    p.add_argument("--nodal",type=Path,required=True)
    p.add_argument("--force",type=Path,required=True)
    p.add_argument("--scenario",type=Path,required=True)
    p.add_argument("--extent",type=int,choices=[8,16],required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(execute(
        multiscale=a.multiscale,interface=a.interface,nodal=a.nodal,
        force=a.force,scenario_path=a.scenario,extent=a.extent,
        output=a.output),indent=2))


if __name__=="__main__":
    main()

"""R6: source SHA-bound core+exterior G2/G3 full internal assembly runner.

A complete explicit NONCANONICAL candidate per all original parent nodes is
required (81/289). The ext provider supplies only 120/504 basal triangles,
so the result has a KNOWN PARTIAL external residual, NOT full equilibrium.
No synthetic defaults, no real physical solve, no physical T1 or HistoryStore.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.g2_g3_source_coupled_runner import (
    read_pinned,source_inputs,sha,INPUT_SCHEMA,
)
from experiments.plate58_deforming_explore_v1.g2_g3_coupled_weak_form import (
    integrate_coupled_candidate,
)
from experiments.plate58_deforming_explore_v1.g2_g3_source_core_exterior_stitch import (
    source_core_contribution,stitch_source_core_exterior,need,
)

from experiments.plate58_deforming_explore_v1.g2_g3_full_external_candidate import (
    assemble_full_candidate_external,
)

INPUT_FULL="ARCANA_R6_G2_G3_EXPLICIT_FULL_PARENT_ENGINEERING_INPUT_V1"
SCHEMA="ARCANA_R6_G2_G3_SOURCE_FULL_CORE_EXTERIOR_PARTIAL_FORCE_RUNNER_V1"


def validate_full_scenario(scenario,expected_ids,extent):
    """Cannot silently fill missing core-only material/velocity from exterior."""
    ids=list(map(int,expected_ids))
    need(len(ids)==(extent+1)**2 and len(set(ids))==len(ids)
         and all(i>0 for i in ids),
         "CORE_SOURCE_ORIGINAL_FULL_PARENT_SCOPE_INVALID")
    need(isinstance(scenario,dict)
         and scenario.get("schema")==INPUT_FULL
         and scenario.get("scope_extent_cells")==extent
         and scenario.get("authority")==
            "ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED"
         and scenario.get("physical_source_authority_ratified") is False
         and scenario.get("mechanical_solve_authorized") is False
         and scenario.get("core_external_force_provider_qualified") is False
         and scenario.get("fault_interface_physics_authorized") is False,
         "CORE_SOURCE_EXPLICIT_FULL_CANDIDATE_AUTHORITY_INVALID")
    # A core external candidate is either explicit in BOTH channels or absent.
    # A missing core load must never become an implicit zero.
    paired=("core_basal_tractions_by_triangle",
            "core_gpe_increment_by_parent_node")
    submitted=[isinstance(scenario.get(key),dict) and
               bool(scenario.get(key)) for key in paired]
    need(all(submitted) or not any(submitted),
         "CORE_SOURCE_CORE_G3_BASAL_AND_GPE_MUST_BE_PAIRED")
    if any(submitted):
        need(scenario.get("core_external_force_provider_qualified") is False,
             "CORE_SOURCE_CANDIDATE_CORE_LOAD_NOT_PHYSICALLY_QUALIFIED")
    for key in ("candidate_material_by_parent_node",
                "velocity_en_by_parent_node"):
        candidate=scenario.get(key)
        need(isinstance(candidate,dict)
             and set(map(int,candidate))==set(ids)
             and len(candidate)==len(ids),
             "CORE_SOURCE_FULL_PARENT_MATERIAL_OR_VELOCITY_MISSING:"+key)
    for key in ("line_tractions_by_edge",
                "basal_tractions_by_triangle","external_gpe"):
        need(isinstance(scenario.get(key),dict)
             and bool(scenario[key]),
             "CORE_SOURCE_G3_EXTERIOR_PROVIDER_MISSING:"+key)


def source_core_geometry(multiscale,interface,nodal,extent):
    """Derive exactly eight original FEG core faces with pinned node/triangle IDs."""
    a,_=read_pinned("multiscale",multiscale)
    b,_=read_pinned("interface",interface)
    c,_=read_pinned("nodal",nodal)
    region=next((r for r in a["topological_comparative_extents"]
                 if int(r["cell_extent_per_side"])==extent),None)
    interf=next((r for r in b["scales"]
                 if int(r["extent_cells_per_side"])==extent),None)
    pre=next((r for r in c["scales"]
              if int(r["extent_cells"])==extent),None)
    need(region is not None and interf is not None and pre is not None,
         "CORE_SOURCE_REGION_BINDING_MISSING")
    ids=list(map(int,region["parent_node_ids"]))
    tids=list(map(int,region["parent_triangle_ids"]))
    source_pre={int(k):v for k,v in pre["source_PRE_by_parent_node"].items()}
    need(len(ids)==(extent+1)**2 and set(ids)==set(source_pre)
         and len(tids)==2*extent**2,
         "CORE_SOURCE_FULL_FEG_PRE_COVERAGE_INVALID")
    p=Path(multiscale)/f"OUTER_A_{extent:02d}x{extent:02d}.feg"
    original_pre=Path(multiscale)/f"OUTER_A_{extent:02d}x{extent:02d}_PRE_T0_PASSIVE.dat"
    need(sha(p)==region["output_FEG_sha256"]
         and sha(original_pre)==region["output_PRE_sha256"]
         and sha(original_pre)==pre["source_regional_PRE_sha256"],
         "CORE_SOURCE_FEG_PRE_SOURCE_HASH_DRIFT")
    feg=parse_feg(p.read_text(),mode="SHELLS_READY")
    need(len(feg.nodes)==len(ids) and len(feg.elements)==len(tids),
         "CORE_SOURCE_ORIGINAL_FEG_TOPOLOGY_CHANGED")
    ext=set(map(int,interf["source_exterior_triangles"]))
    core_ids=sorted(set(tids)-ext)
    shared=list(map(int,interf["source_interface_node_ids"]))
    core_only=list(map(int,interf["source_core_only_node_ids"]))
    need(len(core_ids)==8 and len(shared)==8 and len(core_only)==1
         and len(set(core_ids))==8
         and core_only[0] not in shared
         and len(ext)==2*extent**2-8,
         "CORE_SOURCE_MISSING_OR_EXTRA_8_CORE_FACES")
    f_by_tid={
        tid:tuple(ids[int(i)-1] for i in elem.node_ids)
        for tid,elem in zip(tids,feg.elements,strict=True)
    }
    actual_core={tid:f_by_tid[tid] for tid in core_ids}
    need(set(n for nodes in actual_core.values() for n in nodes)==
         set(shared)|set(core_only),
         "CORE_SOURCE_CORE_FACES_AND_9_PARENT_NODES_MISMATCH")
    ll={
        ids[i]:(float(node.latitude_deg),float(node.longitude_deg))
        for i,node in enumerate(feg.nodes)
    }
    bindings={}
    for tid,nodes in actual_core.items():
        bindings[tid]={
            "parent_triangle_id":tid,
            "parent_node_ids":list(nodes),
            "material_configuration_codes":[
                source_pre[n]["material_configuration_code"] for n in nodes],
            "vertex_quadrature_weights":[1./3]*3,
            "material_law_by_node":None,
            "PRE_source_only_not_constitutive_projection":True,
        }
    return {
        "source_original_full_parent_node_order":ids,
        "source_core_interface_nodes":shared,
        "source_core_only_node_id":core_only[0],
        "source_original_core_triangle_ids":core_ids,
        "source_core_triangles":actual_core,
        "source_core_triangle_bindings":bindings,
        "source_PRE":source_pre,
        "source_lat_lon_deg":ll,
        "source_FEG_sha256":sha(p),
        "source_PRE_sha256":sha(original_pre),
    }


def build_candidate_inputs(multiscale,interface,nodal,force,scenario,extent):
    """SHA-bind existing exterior input contract, while core uses entire source."""
    core=source_core_geometry(multiscale,interface,nodal,extent)
    validate_full_scenario(
        scenario,core["source_original_full_parent_node_order"],extent)
    original_full_ids=core["source_original_full_parent_node_order"]
    source_interface,_=read_pinned("interface",interface)
    intf=next(x for x in source_interface["scales"]
              if int(x["extent_cells_per_side"])==extent)
    exterior_ids=list(map(int,intf["mechanical_node_order_interface_first"]))
    need(len(exterior_ids)==len(original_full_ids)-1
         and set(exterior_ids)==set(original_full_ids)-
         {core["source_core_only_node_id"]},
         "CORE_SOURCE_EXTERIOR_DOF_OWNERSHIP_CHANGED")
    # Old runner is verified for exterior input; hand only exact source exterior
    # node fields, leaving original interface/triangle/traction/GPE all as-is.
    ext_scenario={
        **scenario,
        "schema":INPUT_SCHEMA,
        "candidate_material_by_parent_node":{
            str(n):scenario["candidate_material_by_parent_node"][str(n)]
            for n in exterior_ids},
        "velocity_en_by_parent_node":{
            str(n):scenario["velocity_en_by_parent_node"][str(n)]
            for n in exterior_ids},
    }
    ext,manifest_sha=source_inputs(
        multiscale,interface,nodal,force,extent,ext_scenario)
    return core,ext,manifest_sha


def execute(*,multiscale,interface,nodal,force,scenario_path,extent,output):
    output=Path(output)
    need(not output.exists(),"CORE_SOURCE_OUTPUT_ALREADY_EXISTS")
    scenario_file=Path(scenario_path)
    scenario=json.loads(scenario_file.read_text())
    core,ext,manifest_shas=build_candidate_inputs(
        multiscale,interface,nodal,force,scenario,extent)
    ext_result=integrate_coupled_candidate(**ext)
    shared=core["source_core_interface_nodes"]
    only=core["source_core_only_node_id"]
    order=shared+[only]
    law=scenario["candidate_material_by_parent_node"]
    velocity=scenario["velocity_en_by_parent_node"]
    core_result=source_core_contribution(
        core_node_order=order,
        core_triangles=core["source_core_triangles"],
        source_core_triangle_bindings=core["source_core_triangle_bindings"],
        source_pre_by_parent_node={n:core["source_PRE"][n] for n in order},
        candidate_material_by_parent_node={n:law[str(n)] for n in order},
        node_lat_lon_deg={
            n:core["source_lat_lon_deg"][n] for n in order},
        velocity_en_by_parent_node={n:velocity[str(n)] for n in order},
    )
    stitched=stitch_source_core_exterior(
        core_result,ext_result,
        original_parent_node_order=core["source_original_full_parent_node_order"],
        original_core_interface_node_ids=shared,
        original_core_only_node_id=only,
        velocity_en_by_original_parent_node={
            n:velocity[str(n)] for n in
            core["source_original_full_parent_node_order"]},
    )
    need(stitched["full_domain_physical_residual_AVAILABLE"] is False
         and stitched["physical_T1"] is None
         and stitched["physical_solver_runs"]==0,
         "CORE_SOURCE_STITCHED_UNAUTHORIZED_PHYSICAL_PROMOTION")
    core_candidates=(
        isinstance(scenario.get("core_basal_tractions_by_triangle"),dict)
        and bool(scenario["core_basal_tractions_by_triangle"])
        and isinstance(scenario.get("core_gpe_increment_by_parent_node"),dict)
        and bool(scenario["core_gpe_increment_by_parent_node"])
    )
    if core_candidates:
        full_channels=assemble_full_candidate_external(
            stitched=stitched,exterior=ext_result,
            original_parent_node_order=core[
                "source_original_full_parent_node_order"],
            source_core_triangles=core["source_core_triangles"],
            source_exterior_triangles=ext["parent_triangle_nodes"],
            source_cut_edges=ext["source_cut_edges"],
            node_lat_lon_deg=core["source_lat_lon_deg"],
            line_tractions_by_edge=ext["line_tractions_by_edge"],
            exterior_basal_tractions_by_triangle=ext[
                "basal_tractions_by_triangle"],
            core_basal_tractions_by_triangle=scenario[
                "core_basal_tractions_by_triangle"],
            exterior_gpe=ext["gpe"],
            core_gpe_increment_by_parent_node=scenario[
                "core_gpe_increment_by_parent_node"],
            velocity_en_by_parent_node={
                n:velocity[str(n)] for n in core[
                    "source_original_full_parent_node_order"]},
        )
        stitched["candidate_complete_external_channels"]=full_channels
    stitched.update({
        "runner_schema":SCHEMA,
        "verified_provider_manifest_SHA256":manifest_shas,
        "input_explicit_full_source_scenario_SHA256":sha(scenario_file),
        "source_original_FEG_SHA256":core["source_FEG_sha256"],
        "source_original_PRE_SHA256":core["source_PRE_sha256"],
        "source_original_core_triangle_ids":core[
            "source_original_core_triangle_ids"],
        "CORE_EXTERNAL_GPE_NOT_SPECIFIED_OR_APPLIED":not core_candidates,
        "core_external_candidate_channels_submitted":bool(core_candidates),
        "source_explicit_g2_g3_not_yet_physical":True,
    })
    for n,p in (
        ("multiscale",multiscale),("interface",interface),
        ("nodal",nodal),("force",force)):
        need(sha(Path(p)/"MANIFEST.json")==manifest_shas[n],
             "CORE_SOURCE_PROVIDER_MANIFEST_CHANGED_DURING_RUN")
    need(sha(scenario_file)==
         stitched["input_explicit_full_source_scenario_SHA256"],
         "CORE_SOURCE_EXPLICIT_SCENARIO_CHANGED_DURING_RUN")
    output.mkdir(parents=True,exist_ok=False)
    rp=output/"REPORT.json"
    rp.write_text(json.dumps(stitched,indent=2,allow_nan=False)+"\n")
    (output/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_G2_G3_SOURCE_FULL_INTERNAL_CANDIDATE_MANIFEST_V1",
        "status":stitched["status"],
        "files":{"REPORT.json":sha(rp)},
        "no_physical_solver_run":True,
        "no_T1":True,
        "no_canonical_promotion":True,
    },indent=2)+"\n")
    return {
        "status":stitched["status"],
        "source_original_full_node_count":
            stitched["original_source_parent_node_count"],
        "source_original_full_triangles":
            stitched["source_original_full_domain_triangle_count"],
        "mechanical_source_shared_interface_en_dofs":16,
        "physical_T1":None,
        "D_024":"ACTIVE",
        "physical_solve_authorized":False,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ("multiscale","interface","nodal","force",
                 "scenario","output"):
        ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--extent",type=int,choices=(8,16),required=True)
    a=ap.parse_args()
    print(json.dumps(execute(
        multiscale=a.multiscale,interface=a.interface,
        nodal=a.nodal,force=a.force,scenario_path=a.scenario,
        extent=a.extent,output=a.output),indent=2))


if __name__=="__main__":
    main()

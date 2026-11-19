"""T0-authenticated nested continuation of ARCANA plate 5:8 G3 A.

Extends the original four-cell core and sixteen-cell halo to true source
parent meshes of 8x8 and 16x16 cells, preserving all source node/triangle,
plate and PRE identities. No new BC, rheology, stiffness or mechanical T1.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
from arcana_worldsim.r6.repository_context import resolve_external_payload_path
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh
from arcana_worldsim.r6.shellset_mesh.feg import parse_feg,write_feg
from experiments.plate58_deforming_explore_v1.prepare import (
    ROOT,FEG,PRE,_selection,_json,require,sha)
from experiments.plate58_deforming_explore_v1.check import verify as verify_core
from experiments.plate58_deforming_explore_v1.check_envelope import verify as verify_halo
from experiments.plate58_deforming_explore_v1.envelope import (
    _copy_source_validation,_source_boundary_index,edge_incidence)

STATUS="PASS_G3_A_MULTISCALE_SOURCE_CONTINUATION__BC_AND_G2_UNRESOLVED"
SCHEMA="ARCANA_R6_G3_A_MULTISCALE_SOURCE_CONTINUATION_V1"
COUPLING_STATUS="PASS_G2_G3_A_SOURCE_INTERFACE_BOUND__PHYSICAL_CLOSURE_OPEN"
CORE_CELLS=tuple((r,c) for r in (100,101) for c in (21,22))
EXTENTS=(8,16)

def extent_cells(side:int)->tuple[tuple[int,int],...]:
    require(isinstance(side,int) and side in (2,4,8,16),
            "G3_UNAPPROVED_DOMAIN_SCALE")
    r0,c0=101-side//2,22-side//2
    require(r0>=0 and c0>=0 and r0+side<=180 and c0+side<=360,
            "G3_DOMAIN_OUTSIDE_CANONICAL_GRID")
    return tuple((r,c) for r in range(r0,r0+side)
                       for c in range(c0,c0+side))

def summarize_region(side,parent_nodes,parent_elements,plates,mesh,
                     source_boundary_index):
    """Source contacts and exterior cuts only. NEVER assign Euler BC."""
    nodes=tuple(map(int,parent_nodes))
    require(len(nodes)==(side+1)**2 and len(set(nodes))==len(nodes),
            "G3_A_PARENT_NODE_COUNT_INVALID")
    require(len(parent_elements)==len(plates)==2*side**2,
            "G3_A_TRIANGLE_COUNT_INVALID")
    side_edges={x:[] for x in ("south","north","west","east")}
    incident=defaultdict(set)
    incidence=edge_incidence(parent_elements,plates)
    contacts=[]
    limits={"south":-90+(101-side//2),"north":-90+(101+side//2),
            "west":-180+(22-side//2),"east":-180+(22+side//2)}
    coords={n:tuple(map(float,mesh.vertices_lat_lon[n-1])) for n in nodes}
    for tri,p in zip(parent_elements,plates,strict=True):
        for n in tri.node_ids:
            incident[int(n)].add(int(p))
    for (a,b),owners in incidence.items():
        require(a in coords and b in coords,"G3_A_EDGE_PARENT_ID_MISSING")
        if len(owners)==2 and owners[0][1]!=owners[1][1]:
            require((a,b) in source_boundary_index,
                    "G3_A_CONTACT_SOURCE_ID_NOT_AUTHENTIC")
            contacts.append({"source_edge_node_ids":[a,b],
                             "source_boundary_id":source_boundary_index[(a,b)],
                             "plate_pair":sorted({x[1] for x in owners})})
        if len(owners)!=1:
            continue
        la,lo=coords[a];lb,ln=coords[b]
        tag=[]
        for name,axis,val in (("south",0,limits["south"]),
                              ("north",0,limits["north"]),
                              ("west",1,limits["west"]),
                              ("east",1,limits["east"])):
            x,y=(la,lb) if axis==0 else (lo,ln)
            if abs(x-val)<1e-8 and abs(y-val)<1e-8:
                tag.append(name)
        require(len(tag)==1,"G3_A_NONRECTANGULAR_OUTER_CUT")
        side_edges[tag[0]].append({
            "source_parent_node_ids":[a,b],
            "single_adjacent_plate_id":owners[0][1],
            "prescribed_velocity":None,"physical_traction":None,
            "mechanical_closure_provider":None})
    require(all(len(rows)==side for rows in side_edges.values()),
            "G3_A_RECTANGULAR_CUT_EDGE_COUNT_INVALID")
    require(any(rec["plate_pair"]==[5,8] for rec in contacts),
            "G3_A_PLATE58_CONTACT_DISAPPEARED")
    ambiguous={}
    for name,edges in side_edges.items():
        boundary={int(n) for row in edges for n in row["source_parent_node_ids"]}
        ambiguous[name]=[
            {"parent_node_id":n,"incident_plate_ids":sorted(incident[n]),
             "reason":"MULTIPLE_PLATE_EULER_PRIORS_CANNOT_BE_SINGLE_DIRICHLET_DOF"}
            for n in sorted(boundary) if len(incident[n])>1]
    return {
        "cell_extent_per_side":side,"parent_node_ids":list(nodes),
        "source_plates_present":sorted(set(map(int,plates))),
        "source_contact_edges":sorted(contacts,key=lambda c:c["source_boundary_id"]),
        "source_contact_count":len(contacts),
        "outer_cut_edges":side_edges,"ambiguous_outer_cut_nodes":ambiguous,
        "external_boundary_traction":None,
        "external_boundary_displacement":None,
        "G3_A_mantle_basal_normal_support":None,
        "G3_A_mantle_basal_tangential_law":None,
        "G3_A_source_thermal_fields_are_passive":True,
        "physical_extent_and_convergence_qualified":False}

def select_regional_pre(source_data:Path,wanted_ids,metadata:dict,output:Path):
    """Copy original T0 records intact; no owner changes or material modeling."""
    wanted=set(map(int,wanted_ids))
    require(len(wanted)==len(wanted_ids) and all(x>0 for x in wanted),
            "G3_A_PRE_NODE_OWNERSHIP_INVALID")
    rows=[]
    with source_data.open() as f:
        header=next(f).split()
        require(len(header)==3 and
                header[0]==metadata["header"]["magic"] and
                header[1]==metadata["header"]["schema"] and
                int(header[2])==metadata["node_count"]==64442,
                "G3_A_PRE_SOURCE_HEADER_INVALID")
        count=0
        for count,row in enumerate(f,1):
            if count not in wanted:
                continue
            columns=row.split()
            require(len(columns)==len(metadata["field_order"])==51
                    and int(columns[0])==count,
                    "G3_A_PRE_SOURCE_RECORD_INVALID")
            rows.append((count,row.rstrip("\n")))
        require(count==64442 and {n for n,_ in rows}==wanted,
                "G3_A_PRE_SOURCE_MISSING_RECORDS")
    rows.sort(key=lambda x:x[0])
    output.write_text(
        f"ARCANA_R6_G3_A_PASSIVE_PRE_V1 {metadata['header']['schema']} {len(rows)}\n"
        +"\n".join(row for _,row in rows)+"\n")
    return {"row_count":len(rows),"source_field_order":metadata["field_order"],
            "regional_file_sha256":sha(output),
            "no_material_constitutive_properties_inferred":True}

def build(stage_dir:Path,halo_dir:Path,coupling_dir:Path,
          output_dir:Path,root:Path=ROOT):
    require(not output_dir.exists(),"G3_A_OUTPUT_ALREADY_EXISTS")
    verify_core(stage_dir)
    verify_halo(halo_dir)
    stage=json.loads((stage_dir/"CASE.json").read_text())
    halo=json.loads((halo_dir/"NEIGHBORHOOD.json").read_text())
    manifest=json.loads((coupling_dir/"MANIFEST.json").read_text())
    require(manifest["status"]==COUPLING_STATUS and
            manifest["no_solver_run"] and manifest["no_T1"] and
            manifest["no_canonical_promotion"],
            "G3_A_COUPLING_NOT_SOURCE_VERIFIED")
    require(set(manifest["files"])==
            {"GEOMETRY.json","G2_PRE_BINDING.json","G3_A_TRANSFER_CONTRACT.json"},
            "G3_A_PRIOR_FILES_CHANGED")
    for name,digest in manifest["files"].items():
        require(sha(coupling_dir/name)==digest,
                "G3_A_COUPLING_MEMBER_HASH_MISMATCH:"+name)
    geometry=json.loads((coupling_dir/"GEOMETRY.json").read_text())
    transfer=json.loads((coupling_dir/"G3_A_TRANSFER_CONTRACT.json").read_text())
    require(geometry["source_stage_CASE_sha256"]==sha(stage_dir/"CASE.json")
            and geometry["source_halo_NEIGHBORHOOD_sha256"]==
                sha(halo_dir/"NEIGHBORHOOD.json")
            and geometry["geometry"]["source_halo_parent_node_ids"]==
                halo["parent_node_ids"]
            and transfer["actual_interface_tangent"] is None
            and transfer["actual_effective_load"] is None,
            "G3_A_PRIOR_COUPLING_INPUT_DRIFT")
    _copy_source_validation(stage,root=root)
    mesh=load_canonical_mesh(root)
    require(mesh.normalized_sha256==geometry["source_mesh_identity_sha256"],
            "G3_A_CANONICAL_PARENT_SHA_CHANGED")
    parent=parse_feg((root/FEG).read_text(),mode="SHELLS_READY")
    require(len(parent.nodes)==64442 and len(parent.elements)==128880
            and not parent.faults,"G3_A_SOURCE_FEG_INVENTORY_INVALID")
    manifest_partition=json.loads(
        (root/"R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text())
    part=resolve_external_payload_path(
        root,manifest_partition["payload"]["path"])
    require(sha(part)==manifest_partition["payload"]["sha256"],
            "G3_A_VECTOR_PARTITION_SHA_CHANGED")
    with np.load(part,allow_pickle=False) as data:
        index={(int(r),int(c)):i for i,(r,c) in enumerate(
            zip(data["face_row"],data["face_col"],strict=True))}
    require(len(index)==64800,"G3_A_FACE_INDEX_INCOMPLETE")
    meta=json.loads((root/(PRE+".json")).read_text())
    pre_file=root/(PRE+".dat")
    require(sha(pre_file)==meta["runtime_data_sha256"],
            "G3_A_PRE_SOURCE_SHA_CHANGED")
    boundary_ids=_source_boundary_index(mesh)
    former=set(map(int,halo["parent_triangle_ids"]))
    require(set(CORE_CELLS).issubset(set(map(tuple,halo["parent_cells"])))
            and len(former)==32,"G3_A_SOURCE_HALO_CONTEXT_INVALID")
    output_dir.mkdir(parents=True,exist_ok=False)
    results=[]
    for size in EXTENTS:
        cells=extent_cells(size)
        _,triangles,elements,nodes,plates=_selection(index,mesh,parent,cells)
        require(len(triangles)==2*size*size and
                len(nodes)==(size+1)**2 and former.issubset(triangles),
                "G3_A_NESTED_PARENT_TOPOLOGY_CHANGED")
        analysis=summarize_region(
            size,nodes,elements,plates,mesh,boundary_ids)
        loc={n:i for i,n in enumerate(nodes,1)}
        model=replace(parent,
            title=f"ARCANA_R6_G3_A_{size}x{size}_PASSIVE_GEOMETRY_NO_SOLVE",
            nodes=tuple(replace(parent.nodes[n-1],node_id=loc[n]) for n in nodes),
            elements=tuple(replace(el,element_id=i,
                node_ids=tuple(loc[n] for n in el.node_ids))
                for i,el in enumerate(elements,1)))
        raw=write_feg(model)
        require(parse_feg(raw,mode="SHELLS_READY")==model,
                "G3_A_NEW_FEG_ROUNDTRIP_INVALID")
        meshfile=f"OUTER_A_{size:02d}x{size:02d}.feg"
        pre_name=f"OUTER_A_{size:02d}x{size:02d}_PRE_T0_PASSIVE.dat"
        (output_dir/meshfile).write_text(raw)
        audit=select_regional_pre(pre_file,nodes,meta,output_dir/pre_name)
        analysis.update({
            "parent_cells":[list(c) for c in cells],
            "parent_triangle_ids":triangles,
            "parent_triangle_plate_ids":plates,
            "output_FEG_sha256":sha(output_dir/meshfile),
            "output_PRE_sha256":audit["regional_file_sha256"],
            "PRE_source_field_order":audit["source_field_order"],
            "PRE_records":audit["row_count"],"solver_calls":0})
        results.append(analysis)
    require(set(results[0]["parent_triangle_ids"]).issubset(
                set(results[1]["parent_triangle_ids"])),
            "G3_A_SCALE_NESTING_FAILED")
    out={
        "schema":SCHEMA,"status":STATUS,
        "authority":"RATIFIED_G3_A_ARCH_ONLY__GEOMETRY_NOT_PHYSICS",
        "source_mesh_sha256":mesh.normalized_sha256,
        "source_stage_sha256":sha(stage_dir/"CASE.json"),
        "source_halo_sha256":sha(halo_dir/"NEIGHBORHOOD.json"),
        "source_coupling_manifest_sha256":sha(coupling_dir/"MANIFEST.json"),
        "source_PRE_sha256":sha(pre_file),
        "source_vector_partition_sha256":sha(part),
        "topological_comparative_extents":results,
        "spatial_convergence_qualified":False,
        "G2_constitutive_provider":None,
        "G3_A_outer_boundary_laws":None,
        "G3_A_basal_normal_support":None,
        "G3_A_basal_tangential_law":None,
        "G3_A_physically_calibrated_tangent":None,
        "GPE_double_count_eliminated":None,
        "mechanical_solve_authorized":False,"solver_runs":0,"physical_T1":None}
    (output_dir/"CONTINUATION_A.json").write_bytes(_json(out))
    names=sorted(p.name for p in output_dir.iterdir() if p.is_file())
    (output_dir/"MANIFEST.json").write_bytes(_json({
        "schema":"ARCANA_R6_G3_A_NESTED_EXTENTS_MANIFEST_V1",
        "status":STATUS,
        "input_coupling_manifest_sha256":out["source_coupling_manifest_sha256"],
        "files":{name:sha(output_dir/name) for name in names},
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True}))
    return {"status":STATUS,
        "extensions":[{"width_cells":row["cell_extent_per_side"],
            "node_count":len(row["parent_node_ids"]),
            "triangle_count":len(row["parent_triangle_ids"]),
            "plate_ids":row["source_plates_present"],
            "contact_edges":row["source_contact_count"],
            "north_cut_ambiguous_nodes":len(row["ambiguous_outer_cut_nodes"]["north"]),
            "south_cut_ambiguous_nodes":len(row["ambiguous_outer_cut_nodes"]["south"])}
            for row in results],
        "mechanical_solve_authorized":False,
        "solver_runs":0,"physical_T1":None}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",type=Path)
    parser.add_argument("halo",type=Path)
    parser.add_argument("coupling",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.stage,args.halo,args.coupling,args.output),
                     indent=2))

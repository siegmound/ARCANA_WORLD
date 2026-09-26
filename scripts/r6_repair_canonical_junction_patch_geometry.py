"""Width-parametric t0 junction overlap patch audit; no world evolution."""
from __future__ import annotations

import argparse, heapq, json, math, os, subprocess, sys, time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/"src"))
from arcana_worldsim.r6.repository_context import (require_repository_context,
    resolve_external_payload_path, verify_protected_staged_blobs)
HEAD="592b1651b405363373590092e133bd25569d99a5"
PARENT_SHA="a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
INDEX={"ARCANA_EXECUTION_REFERENCE_INDEX.json":"551727fd6ea73dd39a4194bf3aa34dc2a2707836",
       "ARCANA_EXECUTION_REFERENCE_INDEX.md":"8a8052c5c2ec73f26c598df5aeb3ab50105da085"}
WIDTHS=(100_000,250_000,500_000,1_000_000)


def canonical_junction_geometry(junction_records, segment_records):
    """Derive local branch angles and next-junction graph distances at t0."""
    segments={s["boundary_id"]:s for s in segment_records}
    def vertex(v):
        _,r,c=v.split(":"); return int(r),int(c)%360
    def latlon(v):
        r,c=vertex(v); return -90.0+r,-180.0+c
    def xyz(lat,lon):
        p=math.radians(lat); l=math.radians(lon)
        return np.array((math.cos(p)*math.cos(l),math.cos(p)*math.sin(l),math.sin(p)))
    graph={}; targets={}
    for s in segment_records:
        pair=tuple(sorted(map(int,s["ordered_plate_pair"])))
        a,b=map(vertex,s["endpoint_vertex_ids"]); length=float(s["length_m"])
        g=graph.setdefault(pair,{})
        g.setdefault(a,[]).append((b,length,s["boundary_id"])); g.setdefault(b,[]).append((a,length,s["boundary_id"]))
    for j in junction_records:
        v=vertex(j["vertex_id"])
        for bid in j["incident_boundary_ids"]:
            pair=tuple(sorted(map(int,segments[bid]["ordered_plate_pair"])))
            targets.setdefault(pair,{}).setdefault(v,[]).append(j["junction_id"])
    def next_junction(pair,start):
        dist={start:0.0}; previous={}; queue=[(0.0,start)]
        while queue:
            d,v=heapq.heappop(queue)
            if d!=dist.get(v): continue
            if v!=start and v in targets.get(pair,{}):
                vertices=[v]; boundary_ids=[]; cur=v
                while cur!=start:
                    parent,bid=previous[cur]; vertices.append(parent); boundary_ids.append(bid); cur=parent
                vertices.reverse(); boundary_ids.reverse()
                return {"distance_m":d,"junction_ids":sorted(targets[pair][v]),"vertex":list(v),
                        "path_vertices":[list(p) for p in vertices],"path_boundary_ids":boundary_ids}
            for w,length,bid in graph.get(pair,{}).get(v,()):
                nd=d+length
                if nd<dist.get(w,math.inf): dist[w]=nd; previous[w]=(v,bid); heapq.heappush(queue,(nd,w))
        return {"distance_m":None,"junction_ids":[],"vertex":None,
                "status":"NO_OTHER_GOVERNED_JUNCTION_ON_COMPONENT"}
    out={}
    for j in junction_records:
        start=vertex(j["vertex_id"]); lat0,lon0=latlon(j["vertex_id"])
        center=xyz(lat0,lon0); latr=math.radians(lat0); lonr=math.radians(lon0)
        east=np.array((-math.sin(lonr),math.cos(lonr),0.0))
        north=np.array((-math.sin(latr)*math.cos(lonr),-math.sin(latr)*math.sin(lonr),math.cos(latr)))
        rays=[]; limits=[]
        for bid in sorted(j["incident_boundary_ids"]):
            s=segments[bid]; pair=tuple(sorted(map(int,s["ordered_plate_pair"])))
            a,b=map(vertex,s["endpoint_vertex_ids"]); other_id=s["endpoint_vertex_ids"][1] if a==start else s["endpoint_vertex_ids"][0]
            p=xyz(*latlon(other_id)); tangent=p-float(np.dot(p,center))*center; tangent/=np.linalg.norm(tangent)
            rays.append({"boundary_id":bid,"azimuth_rad":math.atan2(float(np.dot(tangent,east)),float(np.dot(tangent,north)))%(2*math.pi)})
            limits.append({"boundary_id":bid,"plate_pair":list(pair),**next_junction(pair,start)})
        az=sorted(r["azimuth_rad"] for r in rays)
        gaps=[(az[(i+1)%3]-az[i])%(2*math.pi) for i in range(3)]
        out[j["junction_id"]]={"branch_angles_rad":rays,"branch_angle_gaps_rad":gaps,
            "minimum_branch_angle_rad":min(gaps),"topological_limit_per_branch":limits}
    return out


def _xyz_from_grid_vertex(v):
    lat=math.radians(-90.0+int(v[0])); lon=math.radians(-180.0+int(v[1])%360)
    return np.array((math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat)))


def build_canonical_branch_sample_cache(junction, geom, segment_by_id, spatial_index, max_width_m):
    """Issue one maximum-width exact-distance query per canonical branch sample."""
    cache={}
    for limit in geom["topological_limit_per_branch"]:
        bid=limit["boundary_id"]; path=limit.get("path_vertices"); path_ids=limit.get("path_boundary_ids")
        if not path or not path_ids or limit.get("distance_m") is None:
            cache[bid]=None
            continue
        samples=[]; arc=0.0
        for a,b,edge_id in zip(path,path[1:],path_ids):
            edge_len=float(segment_by_id[edge_id]["length_m"])
            p0=_xyz_from_grid_vertex(a); p1=_xyz_from_grid_vertex(b)
            dot=float(np.clip(np.dot(p0,p1),-1.0,1.0)); angle=math.acos(dot)
            for fraction in (0.25,0.5,0.75):
                s=arc+edge_len*fraction
                if s>=float(limit["distance_m"]): continue
                q=p0 if angle<1e-14 else (math.sin((1-fraction)*angle)*p0+math.sin(fraction*angle)*p1)/math.sin(angle)
                q=q/np.linalg.norm(q); lat=math.degrees(math.asin(float(np.clip(q[2],-1,1))))
                lon=math.degrees(math.atan2(float(q[1]),float(q[0])))
                distances={}
                for candidate,distance in spatial_index.query(lat,lon,max_width_m/2):
                    distances[candidate.component_id]=min(float(distance),distances.get(candidate.component_id,math.inf))
                samples.append({"s_m":s,"component_distances_m":distances,"point_unit_xyz":q.tolist(),"edge_id":edge_id})
            arc+=edge_len
        cache[bid]=samples
    return cache


def scan_canonical_branch_persistence(junction, geom, records, segment_by_id, spatial_index,
                                      width_m, sample_cache=None):
    """Measure singleton membership along cached canonical branch samples."""
    ordered=tuple(sorted(records,key=lambda x:x["boundary_id"]))
    bit_by_component={str(r["component_id"]):1<<i for i,r in enumerate(ordered)}
    result=[]
    for limit in geom["topological_limit_per_branch"]:
        bid=limit["boundary_id"]; path=limit.get("path_vertices"); path_ids=limit.get("path_boundary_ids")
        if not path or not path_ids or limit.get("distance_m") is None:
            result.append({"branch_id":bid,"next_topological_limit_m":limit.get("distance_m"),
                           "status":"BRANCH_SCAN_NOT_CONVERGED","reason":"canonical path to next junction unavailable"})
            continue
        samples=[dict(s) for s in ((sample_cache or {}).get(bid) or [])]
        target_record=next((r for r in ordered if r["boundary_id"]==bid),None)
        target_bit=bit_by_component[str(target_record["component_id"])] if target_record else 0
        for sample in samples:
            sample["mask"]=sum(bit for component,bit in bit_by_component.items()
                                if sample["component_distances_m"].get(component,math.inf)<=width_m/2)
        run=None; run_end=None
        for i in range(len(samples)-1):
            if samples[i]["mask"]==target_bit and samples[i+1]["mask"]==target_bit:
                run=i; j=i+2
                while j<len(samples) and samples[j]["mask"]==target_bit: j+=1
                run_end=j-1; break
        if run is None:
            # Three fixed samples per canonical segment do not prove the
            # absence of a narrower singleton interval between samples.
            status="BRANCH_SCAN_NOT_CONVERGED"
            start_s=persist= None
        else:
            start_s=float(samples[run]["s_m"]); persist=float(samples[run_end]["s_m"]-samples[run]["s_m"])
            status="DOMAIN_SUFFICIENT" if persist>0 else "BRANCH_SCAN_NOT_CONVERGED"
        result.append({"branch_id":bid,"component_id":target_record["component_id"] if target_record else None,
                       "next_topological_limit_m":float(limit["distance_m"]),"initial_search_radius_m":float(width_m),
                       "final_executed_search_radius_m":float(limit["distance_m"]),
                       "radius_expansion_count":0,"exclusive_singleton_found":run is not None,
                       "S_exclusive_start_m":start_s,"S_exclusive_persistence_length_m":persist,
                       "persistence_sample_count":0 if run is None else run_end-run+1,
                       "samples":samples,"status":status,
                       "reason":None if run is not None else "fixed interior samples found no persistent singleton; unsampled sub-segment transitions cannot be excluded",
                       "reached_topological_limit":bool(samples),
                        "sampling":"three deterministic interior samples per canonical source segment; max-width distance cache; arc positions bounded strictly before next junction; non-detection is not treated as absence"})
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--widths",nargs="+",type=int,choices=WIDTHS,default=list(WIDTHS),
                        help="diagnostic widths to evaluate; omitted widths are explicitly marked not evaluated")
    args=parser.parse_args()
    branch=subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    context=require_repository_context(ROOT,required_ancestor=HEAD)
    branch=context.branch or f"DETACHED@{context.head[:12]}"
    head=context.head
    origin=context.refs.get("origin/main")
    verify_protected_staged_blobs(ROOT, INDEX)
    m=json.loads((ROOT/"R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text())
    bm=json.loads((ROOT/"R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json").read_text())
    import hashlib
    payload=resolve_external_payload_path(ROOT,m["payload"]["path"])
    h=hashlib.sha256(payload.read_bytes()).hexdigest()
    if h!=PARENT_SHA: raise RuntimeError("vector parent SHA mismatch")
    sys.path.insert(0,str(ROOT/"src"))
    from arcana_worldsim.r6.physical.reference_arrangement import CanonicalBoundarySpatialIndex
    from arcana_worldsim.r6.physical.boundary_geometry import BoundaryFeature, two_plate_corridor_weights, unit_xyz
    from arcana_worldsim.r6.physical.junction_patch import (
        analyze_membership_topology, build_junction_patch,
        evaluate_junction_membership, validate_junction_patch,
        deterministic_domain_radii, classify_trace_reach,
    )
    with np.load(payload,allow_pickle=False) as z:
        owner=np.empty((180,360),dtype=np.int16); owner[z["face_row"],z["face_col"]]=z["face_plate_id"]
    index=CanonicalBoundarySpatialIndex(bm["segments"])
    if len(index.records)!=1983: raise RuntimeError("canonical segment count mismatch")
    byid={r.boundary_id:r for r in index.records}
    jrecords=bm["junctions"]
    junction_geometry=canonical_junction_geometry(jrecords,bm["segments"])
    segment_by_id={s["boundary_id"]:s for s in bm["segments"]}
    branch_sample_cache={}
    for jj in sorted(jrecords,key=lambda r:r["junction_id"]):
        branch_sample_cache[jj["junction_id"]]=build_canonical_branch_sample_cache(
            jj,junction_geometry[jj["junction_id"]],segment_by_id,index,max(WIDTHS))
        print(json.dumps({"branch_sample_cache_junction":jj["junction_id"],
                          "samples":sum(len(v or []) for v in branch_sample_cache[jj["junction_id"]].values())}),flush=True)
    start=time.perf_counter(); cases=[]
    evaluated_widths=tuple(args.widths)
    checkpoint_path=ROOT/"R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT.json"
    resume_width=None; resume_rows=[]; resume_junction=None; resume_corner_levels=[]
    if checkpoint_path.exists():
        prior=json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if (prior.get("schema")=="R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT_V1"
                and prior.get("repository",{}).get("head")==head
                and prior.get("parent_payload_sha256")==h
                and prior.get("protected_staged_blobs")==INDEX
                and prior.get("forward_evolution") is False
                and prior.get("canonical_t0_changed") is False):
            cases=list(prior.get("completed_widths",[]))
            resume_width=prior.get("current_width_m")
            resume_rows=list(prior.get("completed_junction_rows",[]))
            resume_junction=prior.get("current_junction_id")
            resume_corner_levels=list(prior.get("completed_corner_refinement_levels",[]))
            print(json.dumps({"resume_checkpoint":True,"width_m":resume_width,
                              "completed_junctions":len(resume_rows),
                              "completed_widths":len(cases)}),flush=True)
    for width in evaluated_widths:
        if any(int(c["W_model_m"])==width for c in cases):
            continue
        rows=resume_rows if resume_width==width else []
        completed_ids={r["junction_id"] for r in rows}
        for j in sorted(jrecords,key=lambda r:r["junction_id"]):
            if j["junction_id"] in completed_ids:
                continue
            records=[]
            for bid in j["incident_boundary_ids"]:
                b=byid[bid]; segments=tuple(r.segment for r in index.by_component[b.component_id]
                    if r.segment.distance_m(float(j["vertex_id"].split(":")[1])-90.0,
                                            float(j["vertex_id"].split(":")[2])-180.0) <= 2.0*width)
                if not segments: segments=(b.segment,)
                records.append({"boundary_id":bid,"component_id":b.component_id,
                                "plate_pair":b.plate_pair,"segments":segments})
            records=sorted(records,key=lambda x:x["boundary_id"])
            def local_incident_corridor_query(lat,lon,radius):
                # Use the already midpoint-validated canonical spatial index
                # to retrieve only exact segments within the true half-width.
                # Component identity is filtered to this junction's three
                # incidents; no other global boundary can label a local bit.
                wanted={record["component_id"] for record in records}
                distances={}
                for candidate,distance in index.query(lat,lon,radius):
                    if candidate.component_id in wanted:
                        old=distances.get(candidate.component_id,math.inf)
                        distances[candidate.component_id]=min(old,distance)
                return distances
            row=int(j["vertex_id"].split(":")[1]); col=int(j["vertex_id"].split(":")[2])
            junction={"junction_id":j["junction_id"],"lat_deg":row-90.0,"lon_deg":col-180.0}
            attempts=[]
            patch=None
            geom=junction_geometry[j["junction_id"]]
            branch_scans=scan_canonical_branch_persistence(j,geom,records,
                segment_by_id,index,width,branch_sample_cache[j["junction_id"]])
            limits=[x.get("distance_m") for x in geom["topological_limit_per_branch"]]
            all_limits_bound=len(limits)==3 and all(v is not None and math.isfinite(float(v)) and float(v)>0 for v in limits)
            topological_cap=math.nextafter(min(map(float,limits)),0.0) if all_limits_bound else None
            scans_complete=all(b.get("status")!="BRANCH_SCAN_NOT_CONVERGED" for b in branch_scans)
            all_persistent_starts_found=all(b.get("exclusive_singleton_found") for b in branch_scans)
            # The canonical branch walk already tests samples up to each next
            # junction. If a branch scan is unresolved or finds no persistent
            # singleton, a larger square membership raster cannot change that
            # branch evidence; keep the local topology diagnostic bounded.
            radii=(deterministic_domain_radii(width,topological_cap,4)
                   if all_limits_bound and scans_complete and all_persistent_starts_found
                   else (float(width),))
            print(json.dumps({"junction_begin":j["junction_id"],"width_m":width,
                "domain_radii_m":list(radii),"branch_persistent_starts_m":[b.get("S_exclusive_start_m") for b in branch_scans],
                "branch_statuses":[b.get("status") for b in branch_scans]}),flush=True)
            final_radius=float(radii[0]); final_membership=None; finest=None; topologies=[]; domain_sufficient=False
            membership_distance_cache={}
            for level,radius in enumerate(radii):
                factor=max(1,int(math.ceil(radius/float(width))))
                finest_cells=32*factor
                final_radius=float(radius)
                print(json.dumps({"domain_attempt_begin":True,"junction_id":j["junction_id"],
                    "width_m":width,"level":level,"radius_m":radius,"finest_cells_per_half_axis":finest_cells}),flush=True)
                membership,axis,finest=evaluate_junction_membership(
                    junction,records,width,finest_cells,corridor_query=local_incident_corridor_query,
                    domain_radius_m=final_radius,distance_cache=membership_distance_cache)
                level_summaries=[]
                for cells_per_width in (8,16,32):
                    stride=finest_cells//cells_per_width
                    summary=finest if stride==1 else analyze_membership_topology(
                        membership[::stride,::stride],(finest_cells//stride,finest_cells//stride))
                    summary={k:v for k,v in summary.items() if k!="patch_component"}
                    signature={"patch_component_count":summary["patch_component_count"],
                               "port_component_counts":summary["port_component_counts"],
                               "exclusive_region_component_counts":summary["exclusive_region_component_counts"]}
                    level_summaries.append(signature)
                topologies=level_summaries
                stable=len(set(json.dumps(t,sort_keys=True) for t in topologies))==1
                branch_ready=all(b.get("exclusive_singleton_found") and
                    b.get("S_exclusive_start_m") is not None and b["S_exclusive_start_m"]<=radius
                    for b in branch_scans)
                boundary_touched=bool(finest["domain_boundary_touched_by_patch"])
                attempts.append({"level":level,"domain_radius_m":radius,
                    "cells_per_width_at_finest":finest_cells,
                    "status":"DOMAIN_SUFFICIENT" if stable and branch_ready and not boundary_touched else
                             "DOMAIN_EXPANSION_REQUIRED",
                    "topology_signatures_8_16_32":level_summaries,"topology_stable":stable,
                    "central_patch_touches_search_boundary":boundary_touched,
                    "all_three_branch_persistence_starts_inside_domain":branch_ready})
                domain_checkpoint={"artifact":"R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT",
                    "schema":"R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT_V1",
                    "state":"IN_PROGRESS","current_width_m":width,"current_junction_id":j["junction_id"],
                    "current_domain_level":level,"completed_domain_attempts":attempts,
                    "completed_corner_refinement_levels":(resume_corner_levels if resume_width==width and resume_junction==j["junction_id"] else []),
                    "completed_junction_rows":rows,"completed_widths":cases,
                    "repository":{"branch":branch,"head":head,"origin_main":origin},
                    "parent_payload_sha256":h,"protected_staged_blobs":INDEX,
                    "forward_evolution":False,"canonical_t0_changed":False}
                checkpoint_path.write_text(json.dumps(domain_checkpoint,sort_keys=True,indent=2,allow_nan=False)+"\n",
                    encoding="utf-8",newline="\n")
                print(json.dumps({"domain_attempt_complete":True,"junction_id":j["junction_id"],
                    "width_m":width,"level":level,"topology_stable":stable,
                    "central_patch_touches_search_boundary":boundary_touched,
                    "domain_sufficient_candidate":stable and branch_ready and not boundary_touched}),flush=True)
                final_membership=membership
                if stable and branch_ready and not boundary_touched:
                    domain_sufficient=True
                    break
            for branch_record in branch_scans:
                branch_record["final_executed_search_radius_m"]=final_radius
                branch_record["radius_expansion_count"]=max(0,len(attempts)-1)
                branch_record["reached_topological_limit"]=bool(
                    not branch_record.get("exclusive_singleton_found") and
                    branch_record.get("status")=="NO_EXCLUSIVE_CORRIDOR_BEFORE_TOPOLOGICAL_LIMIT")
            finest=analyze_membership_topology(final_membership,(final_membership.shape[0]//2,final_membership.shape[1]//2))
            finest.pop("patch_component",None)
            stable=len(set(json.dumps(t,sort_keys=True) for t in topologies))==1
            all_ports=(all(finest["exclusive_region_component_counts"][str(bit)]>0 for bit in (1,2,4))
                       and all(finest["port_component_counts"][str(bit)]==1 for bit in (1,2,4)))
            corner_levels=(resume_corner_levels if resume_width==width and resume_junction==j["junction_id"] else [])
            corner_status="NOT_REACHED_TOPOLOGY_OR_DOMAIN"
            can_test_corners=stable and all_ports and domain_sufficient
            if can_test_corners:
                factor=max(1,int(math.ceil(final_radius/float(width))))
                from arcana_worldsim.r6.physical.junction_patch import JunctionPatch
                for cells_per_width in (8,16,32,64):
                    actual_cells=cells_per_width*factor
                    if any(x.get("cells_per_width")==actual_cells for x in corner_levels):
                        continue
                    if corner_levels and not corner_levels[-1].get("corners"):
                        break
                    previous_maps=[{tuple(sorted((c["left_port_id"],c["right_port_id"]))):float(c["E_corner"])
                                    for c in level.get("corners",[])} for level in corner_levels]
                    if len(previous_maps)>=2 and all(previous_maps[-1].get(key,math.inf)>1e-4 and
                        abs(previous_maps[-1].get(key,math.inf)-previous_maps[-2].get(key,math.inf))<=
                        max(1e-8,0.01*previous_maps[-2].get(key,math.inf)) for key in previous_maps[-1]):
                        break
                    membership_override=None
                    if finest_cells % actual_cells == 0 and final_membership.shape[0]==2*finest_cells+1:
                        stride=finest_cells//actual_cells
                        membership_override=final_membership[::stride,::stride]
                    print(json.dumps({"corner_refinement_begin":True,"junction_id":j["junction_id"],
                        "width_m":width,"cells_per_width":actual_cells,"domain_radius_m":final_radius,
                        "reused_nested_membership_grid":membership_override is not None}),flush=True)
                    candidate=build_junction_patch(junction,records,width,
                        {"cells_per_width":actual_cells,"domain_radius_m":final_radius,
                         "corner_check_only":True,"contour_root_tolerance_m":1.0,
                         "corner_tolerance":1e-4,"max_tangent_metric_relative_distortion":0.01},owner,
                        corridor_query=local_incident_corridor_query,membership_grid=membership_override)
                    corner_levels.append({"cells_per_width":actual_cells,
                        "status":candidate.status,"reason":candidate.reason,
                        "corners":candidate.metrics.get("corner_compatibility",[])})
                    domain_checkpoint={"artifact":"R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT",
                        "schema":"R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT_V1",
                        "state":"IN_PROGRESS","current_width_m":width,"current_junction_id":j["junction_id"],
                        "current_domain_level":len(attempts)-1,"completed_domain_attempts":attempts,
                        "completed_corner_refinement_levels":corner_levels,
                        "completed_junction_rows":rows,"completed_widths":cases,
                        "repository":{"branch":branch,"head":head,"origin_main":origin},
                        "parent_payload_sha256":h,"protected_staged_blobs":INDEX,
                        "forward_evolution":False,"canonical_t0_changed":False}
                    checkpoint_path.write_text(json.dumps(domain_checkpoint,sort_keys=True,indent=2,allow_nan=False)+"\n",
                        encoding="utf-8",newline="\n")
                    print(json.dumps({"corner_refinement_complete":True,"junction_id":j["junction_id"],
                        "width_m":width,"cells_per_width":actual_cells,"corner_count":len(candidate.metrics.get("corner_compatibility",[])),
                        "status":candidate.status}),flush=True)
                    if not candidate.metrics.get("corner_compatibility"):
                        break
                    current={tuple(sorted((c["left_port_id"],c["right_port_id"]))):float(c["E_corner"])
                             for c in candidate.metrics["corner_compatibility"]}
                    if len(corner_levels)>=2:
                        prior={tuple(sorted((c["left_port_id"],c["right_port_id"]))):float(c["E_corner"])
                               for c in corner_levels[-2].get("corners",[])}
                        if any(current.get(key,math.inf)>1e-4 and prior.get(key,math.inf)>0 and
                               abs(current.get(key,math.inf)-prior.get(key,math.inf))<=
                               max(1e-8,0.01*prior.get(key,math.inf)) for key in current):
                            print(json.dumps({"corner_refinement_stopped":"NONZERO_CORNER_ERROR_PLATEAU",
                                "junction_id":j["junction_id"],"width_m":width}),flush=True)
                            break
                keyed=[]
                for level in corner_levels:
                    keyed.append({tuple(sorted((c["left_port_id"],c["right_port_id"]))):float(c["E_corner"])
                                  for c in level["corners"]})
                all_keys=set.intersection(*(set(k) for k in keyed)) if keyed and all(keyed) else set()
                latest_corners={tuple(sorted((c["left_port_id"],c["right_port_id"]))):c
                    for c in corner_levels[-1].get("corners",[])} if corner_levels else {}
                if len(all_keys)==3 and all(key in latest_corners and
                    float(latest_corners[key]["E_corner"])<=1e-4 and
                    (latest_corners[key].get("E_expected_pure_plate") is None or
                     float(latest_corners[key]["E_expected_pure_plate"])<=1e-4) and
                    latest_corners[key].get("same_spherical_point_used_for_both_port_evaluators") is True
                    for key in all_keys):
                    corner_status="CORNER_COMPATIBLE"
                    patch=build_junction_patch(junction,records,width,
                        {"cells_per_width":64*factor,"domain_radius_m":final_radius,
                         "trace_tolerance":1e-4,"trace_max_depth":12,
                         "contour_root_tolerance_m":1.0,"max_boundary_nodes":8192,
                         "corner_tolerance":1e-4,"max_tangent_metric_relative_distortion":0.01},owner,
                        corridor_query=local_incident_corridor_query)
                elif all_keys:
                    latest=[keyed[-1].get(key,math.inf) for key in sorted(all_keys)]
                    prior=[keyed[-2].get(key,math.inf) for key in sorted(all_keys)]
                    plateau=any(v>1e-4 and abs(v-p)<=max(1e-8,0.01*p) for v,p in zip(latest,prior))
                    declining=all(v<p for v,p in zip(latest,prior))
                    corner_status="CORNER_DIRICHLET_CONFLICT" if plateau else "CORNER_NUMERICALLY_UNRESOLVED"
                    why="persistent nonzero corner Dirichlet mismatch" if plateau else "corner mismatch has not converged by maximum refinement"
                    patch=JunctionPatch(junction["junction_id"],float(width),
                        tuple(sorted({int(p) for r in records for p in r["plate_pair"]})),
                        tuple(r["boundary_id"] for r in records),(),(),(),(),"INVALID",why,
                        {"corner_refinement_levels":corner_levels,"corner_status":corner_status,
                         "corner_error_decreased_at_final_level":declining},
                        {"algorithm":"R6_SPHERICAL_TWO_OF_THREE_CORRIDOR_MEMBERSHIP_TOPOLOGY_V3"})
                else:
                    corner_status="CORNER_NUMERICALLY_UNRESOLVED"
                    patch=JunctionPatch(junction["junction_id"],float(width),
                        tuple(sorted({int(p) for r in records for p in r["plate_pair"]})),
                        tuple(r["boundary_id"] for r in records),(),(),(),(),"INVALID",
                        "no three-port Dirichlet corner set extracted at tested refinements",
                        {"corner_refinement_levels":corner_levels,"corner_status":corner_status},
                        {"algorithm":"R6_SPHERICAL_TWO_OF_THREE_CORRIDOR_MEMBERSHIP_TOPOLOGY_V3"})
            else:
                from arcana_worldsim.r6.physical.junction_patch import JunctionPatch
                bits=tuple(r["boundary_id"] for r in sorted(records,key=lambda x:x["boundary_id"]))
                pids=tuple(sorted({int(p) for r in records for p in r["plate_pair"]}))[:3]
                why=("BRANCH_TOPOLOGICAL_LIMIT_UNBOUND" if not all_limits_bound else
                     "LOCAL_DOMAIN_LIMIT_REACHED" if finest["domain_boundary_touched_by_patch"] or not domain_sufficient else
                     "TOPOLOGY_NOT_CONVERGED" if not stable else
                     "SINGLETON_CORRIDOR_REGION_MISSING" if not all_ports else "MULTIPLE_PORT_COMPONENTS")
                patch=JunctionPatch(junction["junction_id"],float(width),pids,bits,(),(),(),(),
                    "INVALID",why,finest,{"algorithm":"R6_SPHERICAL_TWO_OF_THREE_CORRIDOR_MEMBERSHIP_TOPOLOGY_V3",
                    "membership_topology_only":True})
            trace=None
            if patch.status=="BOUND":
                center=unit_xyz(junction["lat_deg"],junction["lon_deg"])
                lat0,lon0=math.radians(junction["lat_deg"]),math.radians(junction["lon_deg"])
                east=np.array((-math.sin(lon0),math.cos(lon0),0)); north=np.array((-math.sin(lat0)*math.cos(lon0),-math.sin(lat0)*math.sin(lon0),math.cos(lat0)))
                features={r["boundary_id"]:BoundaryFeature(r["boundary_id"],*tuple(sorted(r["plate_pair"])),tuple(r["segments"])) for r in records}
                def corridor(port,x,y):
                    d=math.hypot(x,y); q=center if d==0 else math.cos(d/6371000)*center+math.sin(d/6371000)*(x*east+y*north)/d
                    lat=math.degrees(math.asin(float(np.clip(q[2],-1,1)))); lon=math.degrees(math.atan2(q[1],q[0]))
                    rr=min(179,max(0,int(math.floor(lat+90)))); cc=int(math.floor((lon+180)%360))%360
                    return dict(two_plate_corridor_weights(features[port],lat,lon,width,int(owner[rr,cc])))
                trace=validate_junction_patch(patch,corridor,1e-4,12)
            metrics=patch.metrics
            reason=patch.reason if patch.status!="BOUND" else (None if trace["pass"] else trace.get("reason"))
            topology_counts=metrics.get("membership_mask_counts_in_central_domain")
            port_components=metrics.get("port_component_counts")
            if stable and all_ports and domain_sufficient:
                topology_status="PASS_THREE_PORT_TOPOLOGY"
            elif topology_counts is None:
                topology_status="LOCAL_DOMAIN_LIMIT_REACHED" if "local extraction boundary" in str(reason) else "CENTRAL_MULTI_CORRIDOR_COMPONENT_MISSING"
            elif sum(metrics.get("exclusive_region_node_counts",{}).values())==0:
                topology_status="SINGLETON_CORRIDOR_REGION_MISSING"
            elif port_components and any(int(port_components.get(k,0))>1 for k in ("1","2","4")):
                topology_status="MULTIPLE_PORT_COMPONENTS"
            elif "PORT_EXTRACTION_IMPLEMENTATION_FAILURE" in str(reason):
                topology_status="PORT_EXTRACTION_IMPLEMENTATION_FAILURE"
            else:
                topology_status="TOPOLOGY_NOT_CONVERGED"
            topol_distances=[x["distance_m"] for x in geom["topological_limit_per_branch"] if x["distance_m"] is not None]
            nearest_topological_limit=min(topol_distances) if topol_distances else None
            min_angle=geom["minimum_branch_angle_rad"]
            trace_class,trace_detail=classify_trace_reach(patch.status,
                patch.reason if patch.status!="BOUND" else (None if trace and trace["pass"] else (trace or {}).get("reason")),
                (trace or {}).get("pass") if trace is not None else None)
            port_associations=[]
            for bit,record in zip((1,2,4),records):
                branch=next((x for x in branch_scans if x.get("branch_id")==record["boundary_id"]),{})
                port_associations.append({"singleton_mask":bit,"boundary_id":record["boundary_id"],
                    "canonical_corridor_id":record["component_id"],
                    "expected_adjacent_plate_pair":list(record["plate_pair"]),
                    "junction_id":j["junction_id"],
                    "branch_singleton_persistence_status":branch.get("status"),
                    "association_basis":"CANONICAL_INCIDENT_BOUNDARY_ID_AND_COMPONENT_ID; NOT NEAREST-BOUNDARY HEURISTIC"})
            rows.append({"junction_id":j["junction_id"],"status":patch.status,
                         "topology_status":topology_status,
                         "domain_status":"DOMAIN_SUFFICIENT" if domain_sufficient else
                            ("BRANCH_SCAN_NOT_CONVERGED" if any(b.get("status")=="BRANCH_SCAN_NOT_CONVERGED" for b in branch_scans) else
                             "NO_EXCLUSIVE_CORRIDOR_BEFORE_TOPOLOGICAL_LIMIT" if any(b.get("status")=="NO_EXCLUSIVE_CORRIDOR_BEFORE_TOPOLOGICAL_LIMIT" for b in branch_scans) else "DOMAIN_EXPANSION_REQUIRED"),
                         "branch_persistence_scans":branch_scans,
                         "corner_refinement_levels":corner_levels,"corner_status":corner_status,
                         "trace_status":trace_class,"trace_classification":trace_detail,
                         "port_associations":port_associations,
                         "port_association_valid":bool(all_ports and len({p["boundary_id"] for p in port_associations})==3
                             and len({p["canonical_corridor_id"] for p in port_associations})==3),
                         "reason":patch.reason if patch.status!="BOUND" else (None if trace["pass"] else trace.get("reason")),
                         "node_count":patch.metrics.get("node_count",0),"triangle_count":patch.metrics.get("triangle_count",0),
                         "port_count":patch.metrics.get("port_count",0),"max_trace_error":None if trace is None else trace["max_trace_error"],
                         "trace_pass":False if trace is None else trace["pass"],
                         "central_patch_connected":bool(topology_counts and sum(int(v) for k,v in topology_counts.items() if k in ("011","101","110","111"))>0),
                         "mask_region_statistics":topology_counts,
                         "exclusive_region_node_counts":metrics.get("exclusive_region_node_counts"),
                         "port_component_counts":port_components,
                         **geom,"minimum_branch_angle_rad":min_angle,
                         "angle_based_initial_search_radius_m":(width/2)/math.sin(min_angle/2),
                         "angle_scale_to_width_ratio":0.5/math.sin(min_angle/2),
                         "nearest_topological_limit_m":nearest_topological_limit,
                         "initial_domain_radius_m":width,
                         "final_domain_radius_m":final_radius,
                         "domain_expansion":"EXECUTED_BOUNDED_DYADIC" if len(attempts)>1 else "EXECUTED_INITIAL_RADIUS_ONLY",
                         "topological_limit_per_branch":geom["topological_limit_per_branch"],
                         "singleton_corridor_found":{str(bit):any(b.get("exclusive_singleton_found") for b in branch_scans if b["branch_id"]==records[i]["boundary_id"])
                            for i,bit in enumerate((1,2,4))},
                         "metrics":metrics,
                         "refinement_attempts":attempts})
            domain_checkpoint={"artifact":"R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT",
                "schema":"R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT_V1",
                "state":"IN_PROGRESS","current_width_m":width,
                "completed_junction_rows":rows,"completed_widths":cases,
                "repository":{"branch":branch,"head":head,"origin_main":origin},
                "parent_payload_sha256":h,"protected_staged_blobs":INDEX,
                "forward_evolution":False,"canonical_t0_changed":False}
            (ROOT/"R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT.json").write_text(
                json.dumps(domain_checkpoint,sort_keys=True,indent=2,allow_nan=False)+"\n",
                encoding="utf-8",newline="\n")
            print(json.dumps({"width_m":width,"junction_id":j["junction_id"],
                "domain_status":rows[-1]["domain_status"],"topology_status":topology_status,
                "corner_status":corner_status,"trace_status":trace_class}),flush=True)
        constructed=sum(x["status"]=="BOUND" for x in rows)
        simple=sum(x["central_patch_connected"] for x in rows)
        threeport=sum(x["topology_status"]=="PASS_THREE_PORT_TOPOLOGY" for x in rows)
        triangulated=sum(x["triangle_count"]>0 and x["status"]=="BOUND" for x in rows)
        tracepass=sum(x["trace_pass"] for x in rows)
        errors=[x["max_trace_error"] for x in rows if x["max_trace_error"] is not None]
        status="PASS_JUNCTION_GATE" if (constructed==simple==threeport==triangulated==tracepass==20) else "INVALID_AT_JUNCTION_GATE"
        cases.append({"W_model_m":width,"status":status,"patches_constructed":constructed,
                      "simple_connected":simple,"three_port":threeport,"triangulated":triangulated,
                      "trace_pass":tracepass,"trace_fail":sum(x.get("trace_status")=="TRACE_FAIL" for x in rows),
                      "trace_not_reached":sum(x.get("trace_status")=="TRACE_NOT_REACHED" for x in rows),
                      "domain_sufficient":sum(x.get("domain_status")=="DOMAIN_SUFFICIENT" for x in rows),
                      "stable_topology":threeport,
                      "port_association_valid":sum(bool(x.get("port_association_valid")) for x in rows),
                      "three_compatible_corners":sum(x.get("corner_status")=="CORNER_COMPATIBLE" for x in rows),
                      "local_static_velocity_pass":None,
                      "local_gate":"PASS" if status=="PASS_JUNCTION_GATE" else "FAIL",
                      "max_trace_error":max(errors) if errors else None,
                      "junctions":rows,"global_L0_L1_executed":False,"global_ownership":"NOT_RUN_JUNCTION_GATE_FAILED"})
        print(json.dumps({"completed_width_m":width,"junctions":len(rows),
                          "patches_constructed":constructed,"three_port":threeport,
                          "trace_pass":tracepass,"status":status}),flush=True)
        checkpoint={"artifact":"R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS",
            "schema":"R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS_V1",
            "matrix_complete":False,"completed_widths_m":[c["W_model_m"] for c in cases],
            "junction_count":len(jrecords),"width_count":len(WIDTHS),
            "port_identity_authority":"PATCH_TO_EXCLUSIVE_REGION_MESH_ADJACENCY",
            "normal_based_port_authority":"RETIRED",
            "mask_bit_order":"incident_boundary_ids sorted lexicographically; bit i corresponds to that record order",
            "domain_expansion_policy":"NOT_IMPLEMENTED; fixed local radius equals W_model_m",
            "per_branch_topological_limit":"NOT_BOUND",
            "width_cases":cases,"canonical_width_selected":False,
            "canonical_reference_map_materialized":False,"forward_evolution":False,
            "repository":{"branch":branch,"head":head,"origin_main":origin},
            "parent_payload_sha256":h,"protected_staged_blobs":INDEX}
        (ROOT/"R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS.json").write_text(
            json.dumps(checkpoint,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    for width in WIDTHS:
        if width not in evaluated_widths:
            cases.append({"W_model_m":width,"status":"NOT_EVALUATED_EXECUTION_BUDGET",
                          "patches_constructed":None,"simple_connected":None,"three_port":None,
                          "triangulated":None,"trace_pass":None,"max_trace_error":None,
                          "junctions":[],"global_L0_L1_executed":False,
                          "global_ownership":"NOT_RUN_WIDTH_NOT_EVALUATED"})
    cases.sort(key=lambda c:int(c["W_model_m"]))
    run_seconds=time.perf_counter()-start
    vcount=sum(c["status"]=="PASS_JUNCTION_GATE" for c in cases)
    structural_corner_conflicts=sum(j.get("corner_status")=="CORNER_DIRICHLET_CONFLICT"
        for c in cases for j in c.get("junctions",[]))
    failure_text=" ".join(str(j.get("reason") or "") for c in cases for j in c["junctions"])
    if vcount and len(evaluated_widths)==len(WIDTHS):
        decision="CANONICAL_JUNCTION_OVERLAP_PATCHES_BOUND__WIDTH_GATES_EVALUATED"; blocker=None
    elif vcount:
        decision="SELECTED_WIDTH_PATCHES_BOUND__WIDTH_MATRIX_INCOMPLETE"
        blocker="REMAINING_DIAGNOSTIC_WIDTH_CASES_NOT_EVALUATED"
    elif len(evaluated_widths)<len(WIDTHS):
        decision="PER_WIDTH_JUNCTION_GATE_INCOMPLETE__NO_COMPLETION_CLAIM"
        blocker="REMAINING_DIAGNOSTIC_WIDTH_CASES_NOT_EVALUATED"
    elif structural_corner_conflicts:
        decision="OVERLAP_DERIVED_PATCH_BOUNDARY_DIRICHLET_INCOMPATIBLE"
        blocker="JUNCTION_PATCH_REDEFINITION_FROM_CANONICAL_BRANCH_CROSS_SECTIONS_AND_PURE_PLATE_ANCHORS"
    else:
        decision="CANONICAL_PORT_TOPOLOGY_AUDITED__DOMAIN_EXPANSION_AND_TRACE_GATES_REMAIN"
        blocker="LOCAL_DOMAIN_OR_PORT_ASSOCIATION_OR_CORNER_CONVERGENCE_GATE"
    repo={"branch":branch,"head":head,"origin_main":origin}
    common={"repository":repo,"parent_payload_sha256":h,"canonical_parent_faces":64800,
            "canonical_boundary_segments":len(index.records),"canonical_junctions":len(jrecords),
            "algorithm":"R6_SPHERICAL_TWO_OF_THREE_CORRIDOR_MEMBERSHIP_TOPOLOGY_V3",
            "geometry_semantics":"SPHERICAL_DISTANCE_MEMBERSHIP; tangent chart only numerical extraction",
            "independent_junction_radius":False,"p1_primitive_retained":True,
            "trace_tolerance":1e-4,"evaluated_widths_m":list(evaluated_widths),
            "not_evaluated_widths_m":[w for w in WIDTHS if w not in evaluated_widths],
            "width_cases":cases,"elapsed_seconds":run_seconds,
            "canonical_width_selected":False,"canonical_map_materialized":False,
            "forward_evolution":False,"canonical_t0_changed":False,
            "execution_indexes_mutated":False,"protected_staged_blobs":INDEX,
            "remaining_blocker":blocker,
            "port_identity_authority":"PATCH_TO_EXCLUSIVE_REGION_MESH_ADJACENCY",
            "normal_based_port_authority":"RETIRED",
            "domain_expansion":"EXECUTED_BOUNDED_DYADIC_UNTIL_STABLE_OR_NEXT_JUNCTION_LIMIT",
            "branch_angles_and_topological_limits":"MEASURED_FROM_CANONICAL_BOUNDARY_GRAPH; NO SEARCH CROSSES NEXT JUNCTION",
            "canonical_branch_persistence":"THREE DETERMINISTIC INTERIOR SAMPLES PER SOURCE SEGMENT; NONDETECTION IS UNRESOLVED NOT ABSENCE",
            "corner_dirichlet_policy":"COMPARE BOTH PORT LIMITS AT IDENTICAL SPHERICAL POINT; NEVER AVERAGE CONFLICTING VALUES",
            "trace_policy":"ENTER TRACE REFINEMENT ONLY AFTER STABLE THREE-PORT TOPOLOGY, SUFFICIENT DOMAIN, VALID PORT ASSOCIATION AND THREE COMPATIBLE CORNERS"}
    out={
    "R6_JUNCTION_PATCH_OPERATOR_VALIDATION":{"schema":"R6_JUNCTION_PATCH_OPERATOR_VALIDATION_V6","decision":decision,"verdict":"BOUNDED_DOMAIN_AND_DIRICHLET_CORNER_AUDIT_EXECUTED__TRACE_FAIL_CLOSED" if not vcount else "BOUNDED_DOMAIN_AND_DIRICHLET_CORNER_AUDIT_EXECUTED__WIDTH_GATE_ADVANCED","patch_boundary_weights":"INHERITED_FROM_TWO_PLATE_CORRIDOR_OPERATOR_WHEN_PATCH_BINDS","corner_compatibility":"THREE_CORNERS_PER_PATCH; TWO PORT LIMITS COMPARED AT THE SAME SPHERICAL POINT; NO AVERAGING","adaptive_trace_subdivision":"IMPLEMENTED_DYADIC_QUARTER_MIDPOINT_THREE_QUARTER_RESIDUAL_CHECK; exact corridor weights at inserted nodes; bounded by trace_max_depth and max_boundary_nodes","triangulation":"ONLY_AFTER_THREE_CORNER_COMPATIBILITY_AND_TRACE_PASS",**common},
    "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION":{"schema":"R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION_V4","decision":decision,"canonical_boundary_index_count":1983,"canonical_patch_membership":"AT_LEAST_TWO_OF_THREE_INCIDENT_CORRIDORS",**common},
    "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION":{"schema":"R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION_V4","decision":"GLOBAL_OWNERSHIP_NOT_RUN_NO_EVALUATED_WIDTH_PASSED_JUNCTION_GATE","global_ownership":"NOT_RUN",**common},
    "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE":{"schema":"R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE_V4","decision":"GLOBAL_L0_L1_NOT_RUN_NO_EVALUATED_WIDTH_PASSED_JUNCTION_GATE","global_L0_L1":"NOT_RUN",**common},
    "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX":{"schema":"R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX_V6","decision":decision,"cases":cases,"valid_width_set_m":[c["W_model_m"] for c in cases if c["status"]=="PASS_JUNCTION_GATE"],"classification":"INCOMPLETE_NO_WIDTH_VALIDATED" if len(evaluated_widths)<len(WIDTHS) and not vcount else ("NO_TEST_WIDTH_VALID" if not vcount else "PARTIAL_JUNCTION_FEASIBILITY"),**common},
    "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS":{"schema":"R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS_V5","decision":decision,"cases":cases,"global_width_validity":"NOT_EVALUATED_UNLESS_LOCAL_20_OF_20_GATE_PASSES",**common},
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19":{"schema":"R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19","decision":decision,"verdict":"BOUNDED_DOMAIN_AND_CORNER_COMPATIBILITY_AUDITED__NO_FORWARD_EVOLUTION_AUTHORIZED","t0_ma":210.0,"first_dt_years":None,"reference_geometry_ready_for_canonical_width_selection":False,"remaining_blocker":blocker,"next_action":"R6_JUNCTION_PATCH_REDEFINITION_FROM_CANONICAL_BRANCH_CROSS_SECTIONS_AND_PURE_PLATE_ANCHORS" if any(x.get("corner_status")=="CORNER_DIRICHLET_CONFLICT" for c in cases for x in c.get("junctions",[])) else "COMPLETE_REMAINING_PER_WIDTH_JUNCTION_PATCH_EVALUATIONS" if len(evaluated_widths)<len(WIDTHS) else "R6_JUNCTION_PATCH_PORT_TOPOLOGY_DOMAIN_AND_TRACE_CONVERGENCE_REPAIR","canonical_width_selected":False,"canonical_reference_map_materialized":False,"forward_evolution":False,**common}}
    md={
    "R6_JUNCTION_PATCH_OPERATOR_VALIDATION":f"# Junction patch operator validation V5\n\nSelected widths `{list(evaluated_widths)}` were evaluated over 20 canonical junctions each. Omitted widths are explicitly `NOT_EVALUATED_EXECUTION_BUDGET`; no result is extrapolated. The patch is the spherical-membership contour of the central component covered by at least two incident corridors. P1 boundary traces use corridor-derived nodal weights and bounded adaptive subdivision. Result: `{decision}`. No global width cases proceeded unless a per-width junction gate passed.\n",
    "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION":f"# Spherical network arrangement operator validation V4\n\nCanonical parent and boundary index are preserved. Junction membership uses exact spherical segment distances; local tangent coordinates are numerical mesh coordinates only. Per-width results are recorded in the JSON.\n",
    "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION":f"# Global reference ownership validation V4\n\nGlobal ownership was not run. Evaluated widths `{list(evaluated_widths)}` failed their junction gate; omitted widths `{[w for w in WIDTHS if w not in evaluated_widths]}` are not evaluated. No global area or width-validity conclusion is made.\n",
    "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE":f"# Reference arrangement convergence V4\n\nGlobal L0/L1 was not run: no evaluated width passed its junction gate. Omitted widths remain unevaluated.\n",
    "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX":f"# Boundary-zone geometric feasibility matrix V5\n\nDecision: `{decision}`. Exact per-width and per-junction construction, port, triangulation and trace results are in the paired JSON. No canonical width is selected.\n",
    "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS":f"# Boundary-zone width case diagnostics V4\n\nEvaluated widths: `{list(evaluated_widths)}`. Not evaluated: `{[w for w in WIDTHS if w not in evaluated_widths]}`. No status is inferred for omitted widths; global L0/L1 is not run unless an evaluated width passes its all-20 local gate.\n",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19":f"# First physical interval readiness V19\n\nDecision: `{decision}`. Evaluated widths: `{list(evaluated_widths)}`; remaining widths are not evaluated. First dt remains unbound; no forward evolution, canonical width selection, or map materialization occurred. Bounded local-domain, canonical branch-persistence, port-association, Dirichlet-corner, trace, and triangulation outcomes are recorded per junction.\n"}
    from arcana_worldsim.r6.physical.junction_patch import classify_corner_refinement
    junction_by_id={j["junction_id"]:j for j in jrecords}
    corner_cases=[]; trace_cases=[]
    for case in cases:
        for row in case.get("junctions",[]):
            associations=row.get("port_associations",[])
            if len(associations)!=3 and row["junction_id"] in junction_by_id:
                associations=[]
                for bit,bid in enumerate(sorted(junction_by_id[row["junction_id"]]["incident_boundary_ids"]),start=0):
                    boundary=byid[bid]
                    associations.append({"singleton_mask":1<<bit,"boundary_id":bid,
                        "canonical_corridor_id":boundary.component_id,
                        "expected_adjacent_plate_pair":list(boundary.plate_pair),
                        "junction_id":row["junction_id"],
                        "association_basis":"CANONICAL_INCIDENT_BOUNDARY_ID_AND_COMPONENT_ID; NOT NEAREST-BOUNDARY HEURISTIC"})
                row["port_associations"]=associations
            pairs=[]
            for i in range(len(associations)):
                for k in range(i+1,len(associations)):
                    left,right=associations[i],associations[k]
                    shared=sorted(set(left["expected_adjacent_plate_pair"]) & set(right["expected_adjacent_plate_pair"]))
                    pairs.append((tuple(sorted((left["boundary_id"],right["boundary_id"]))),left,right,shared))
            levels=row.get("corner_refinement_levels",[])
            level_maps=[]
            for level in levels:
                level_maps.append({tuple(sorted((c["left_port_id"],c["right_port_id"]))):c
                                   for c in level.get("corners",[])})
            for port_ids,left,right,shared in pairs:
                observed=[m[port_ids] for m in level_maps if port_ids in m]
                errors=[float(c["E_corner"]) for c in observed]
                expected=[float(c["E_expected_pure_plate"]) if c.get("E_expected_pure_plate") is not None else None for c in observed]
                status=(classify_corner_refinement(errors,expected_errors=expected)
                        if errors and all(v is not None for v in expected) else
                        classify_corner_refinement(errors) if errors else
                        (row.get("corner_status") if row.get("corner_status") in
                         ("CORNER_DIRICHLET_CONFLICT","CORNER_NUMERICALLY_UNRESOLVED") else "CORNER_NUMERICALLY_UNRESOLVED"))
                corner_cases.append({"junction_id":row["junction_id"],"W_model_m":case["W_model_m"],
                    "corner_id":"|".join(port_ids),"port_ids":list(port_ids),
                    "expected_shared_plate_id":shared[0] if len(shared)==1 else None,
                    "expected_pure_plate_weights":([1.0 if p==shared[0] else 0.0 for p in sorted({v for a in associations for v in a["expected_adjacent_plate_pair"]})]
                        if len(shared)==1 else None),
                    "evaluated":bool(observed),"refinement_cells_per_width":[x.get("cells_per_width") for x in levels],
                    "E_corner_sequence":errors,"E_expected_pure_plate_sequence":expected,
                    "same_spherical_point_used_for_both_port_evaluators":all(c.get("same_spherical_point_used_for_both_port_evaluators") is True for c in observed),
                    "final_point_unit_xyz":observed[-1].get("point_unit_xyz") if observed else None,
                    "final_left_weights":observed[-1].get("left_weights") if observed else None,
                    "final_right_weights":observed[-1].get("right_weights") if observed else None,
                    "status":status,"non_evaluation_reason":None if observed else row.get("reason") or row.get("domain_status")})
            trace_cases.append({"junction_id":row["junction_id"],"W_model_m":case["W_model_m"],
                "trace_status":row.get("trace_status"),"trace_classification":row.get("trace_classification"),
                "trace_attempted":row.get("trace_status") in ("TRACE_PASS","TRACE_FAIL"),
                "trace_pass":row.get("trace_pass",False),"max_trace_error":row.get("max_trace_error"),
                "trace_refinement_metrics":row.get("metrics",{}).get("trace_refinement"),
                "reason":row.get("reason")})
    corner_summary={status:sum(c["status"]==status for c in corner_cases) for status in
                    ("CORNER_COMPATIBLE","CORNER_NUMERICALLY_UNRESOLVED","CORNER_DIRICHLET_CONFLICT")}
    out["R6_CANONICAL_JUNCTION_DIRICHLET_CORNER_COMPATIBILITY"]={
        "schema":"R6_CANONICAL_JUNCTION_DIRICHLET_CORNER_COMPATIBILITY_V1",
        "decision":"CORNER_AUDIT_EXECUTED_AFTER_STABLE_LOCAL_TOPOLOGY_WHERE_AVAILABLE",
        "corner_count":len(corner_cases),"expected_corner_count":len(cases)*20*3,
        "summary":corner_summary,"maximum_E_corner":max((v for c in corner_cases for v in c["E_corner_sequence"]),default=None),
        "cases":corner_cases,"never_average_conflicting_dirichlet_values":True,
        "parent_payload_sha256":h,"repository":repo,"forward_evolution":False,
        "canonical_width_selected":False,"protected_staged_blobs":INDEX}
    out["R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS"]={
        "schema":"R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS_V2",
        "decision":"TRACE_EVALUATED_ONLY_AFTER_THREE_COMPATIBLE_CORNERS",
        "cases":trace_cases,
        "summary":{k:sum(c["trace_status"]==k for c in trace_cases) for k in
                   ("TRACE_PASS","TRACE_FAIL","TRACE_NOT_REACHED")},
        "tolerance":1e-4,"adaptive_subdivision":"EXISTING_DETERMINISTIC_QUARTER_MIDPOINT_THREE_QUARTER_RESIDUAL; bounded depth and node count",
        "parent_payload_sha256":h,"repository":repo,"forward_evolution":False,"protected_staged_blobs":INDEX}
    md["R6_CANONICAL_JUNCTION_DIRICHLET_CORNER_COMPATIBILITY"]=(
        f"# Canonical junction Dirichlet corner compatibility\n\n"
        f"Corner records: {len(corner_cases)}; expected {len(cases)*20*3}. Counts: `{corner_summary}`. "
        "Each evaluated record compares the two port-implied vectors at the same spherical point and records the expected pure shared-plate limit. Conflicting values are never averaged. Non-evaluated corners remain explicitly unresolved.\n")
    md["R6_CANONICAL_JUNCTION_TRACE_CONVERGENCE_DIAGNOSTICS"]=(
        f"# Canonical junction trace convergence diagnostics\n\n"
        "Trace refinement runs only after stable topology, sufficient domain, valid port associations and all three compatible corners. Pre-trace blockers are recorded as `TRACE_NOT_REACHED`, not trace failures. Per-case subdivision/error metrics are in JSON.\n")
    for name,val in out.items():
        val["artifact"]=name
        (ROOT/f"{name}.json").write_text(json.dumps(val,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
        (ROOT/f"{name}.md").write_text(md[name]+"\n",encoding="utf-8",newline="\n")
    topology_artifact={"artifact":"R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS",
        "schema":"R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS_V2",
        "decision":decision,"junction_count":len(jrecords),"width_count":len(WIDTHS),
        "matrix_complete":len(evaluated_widths)==len(WIDTHS) and all(len(c.get("junctions",[]))==20 for c in cases),
        "port_identity_authority":"PATCH_TO_EXCLUSIVE_REGION_MESH_ADJACENCY",
        "normal_based_port_authority":"RETIRED",
        "mask_bit_order":"incident_boundary_ids sorted lexicographically; bit i corresponds to that record order",
        "domain_expansion_policy":"DETERMINISTIC_DYADIC_RADII; strictly below nearest next-junction distance; stops when topology and persistent branch ports are sufficient",
        "per_branch_topological_limit":"CANONICAL_BOUNDARY_GRAPH_SHORTEST_PATH_TO_NEXT_JUNCTION; no crossing permitted",
        "branch_sampling_policy":"THREE DETERMINISTIC INTERIOR SAMPLES PER SOURCE EDGE; sampled non-detection remains BRANCH_SCAN_NOT_CONVERGED",
        "dirichlet_corner_policy":"THREE PORT-PAIR CORNERS; same spherical point; expected pure shared-plate limit; no averaging",
        "trace_policy":"TRACE_NOT_REACHED UNLESS STABLE THREE-PORT PATCH HAS SUFFICIENT DOMAIN, VALID PORT ASSOCIATIONS AND ALL THREE CORNERS COMPATIBLE",
        "width_cases":cases,"canonical_width_selected":False,
        "canonical_reference_map_materialized":False,"forward_evolution":False,
        "repository":repo,"parent_payload_sha256":h,"protected_staged_blobs":INDEX}
    (ROOT/"R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS.json").write_text(
        json.dumps(topology_artifact,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
    diag_md=["# Canonical junction membership topology diagnostics V2", "",
        f"Decision: `{decision}`. Evaluated widths: `{list(evaluated_widths)}`.",
        "Port identity is derived from mesh adjacency between the central multi-corridor component and exclusive singleton masks; normal probes are retired.",
        "Bounded dyadic local domains are capped strictly before the next canonical junction. Branch persistence uses three deterministic interior samples per source edge; sample non-detection is `BRANCH_SCAN_NOT_CONVERGED`, not proof of absence. Corner gates precede trace refinement; conflicting Dirichlet data are never averaged.", ""]
    for case in cases:
        diag_md.append(f"## W = {case['W_model_m']} m")
        diag_md.append(f"Status: `{case['status']}`; topology pass {sum(x.get('topology_status')=='PASS_THREE_PORT_TOPOLOGY' for x in case.get('junctions',[]))}/20; trace pass {case.get('trace_pass')}/20; triangulation {case.get('triangulated')}/20.")
    (ROOT/"R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS.md").write_text("\n".join(diag_md)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"decision":decision,"per_width":[{k:c[k] for k in ("W_model_m","status","patches_constructed","three_port","triangulated","trace_pass","max_trace_error")} for c in cases],"elapsed_seconds":run_seconds},indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())

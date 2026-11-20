"""ARCANA R6 original-edge t0 normal consistency, moving 3D nearest-segment geometry and gap Jacobian.

Diagnostics only. Original source edge/plate ownership; no manufactured new
faults. Source 8x8 and 16x16. True 3D surface contact and moving-geometry
Signorini NOT implemented. NOT a physical T1. SERIAL intentionally after FAIR
0.735x two-worker speedup for these tiny regional tasks.
"""
from __future__ import annotations

from collections import Counter

import argparse
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.spatial.transform import Rotation

from experiments.global_t0_kinematic_baseline_v1.benchmark import ROOT, sha256, source_inputs, usage, RADIUS_M
from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import (
    contact_registry, assemble_split_source, euler_source_en,
)
from experiments.plate58_deforming_explore_v1.g2_regional_unilateral_contact_time import (
    normal_constraint_matrix, integrate,
)
from experiments.plate58_deforming_explore_v1.g2_moving_3d_contact_parallel import (
    boundary_node_edges, rigid_motion_with_residual,
    moving_contact_geometry, certify_priors, unit,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error

STATUS = "PASS_SOURCE_EDGE_FEATURE_ADMISSIBILITY_INVENTORY__PHYSICAL_CONTACT_OPEN"
SCHEMA = "ARCANA_R6_SOURCE_EDGE_FEATURE_ADMISSIBILITY_V1"
# Conservative geometry-only eligibility; these are NOT physical rock contact thresholds.
PARALLEL_RATIO_MIN = 1e-8
WITNESS_INTERIOR_MARGIN = 1e-3
REFERENCE_ALIGNMENT_MIN = 0.5
SO3_TOL_M = 1e-7
YEARS = (100, 500, 1000)


def need(ok, label):
    if not ok:
        raise SparseP1Error(label)


def closest_segments(a, b, c, d):
    """Closest points of TWO bounded 3D segments (RTCD clamp algorithm).

    Returns point pair, independent segment coordinates, and distance.
    Source segment order may be reversed; geometry remains invariant.
    """
    a,b,c,d = [np.asarray(x, dtype=float) for x in (a,b,c,d)]
    need(all(x.shape == (3,) and np.all(np.isfinite(x)) for x in (a,b,c,d)),
         "T0NORMAL_SEGMENT_INVALID_COORDINATES")
    e = b-a; f=d-c; r=a-c
    ee=float(e@e); ff=float(f@f)
    need(ee>1e-10 and ff>1e-10,
         "T0NORMAL_SEGMENT_DEGENERATE")
    ef=float(e@f); er=float(e@r); fr=float(f@r)
    # Avoid cancellation of nearly equal Gram products on near-parallel
    # source edges. The equivalent cross-product expressions are much
    # better conditioned under finite SO(3) rotations.
    cross_ef=np.cross(e,f)
    denominator=float(cross_ef@cross_ef)
    if denominator > 1e-14*ee*ff:
        numerator=float(np.cross(c-a,f)@cross_ef)
        s=float(np.clip(numerator/denominator,0.,1.))
    else:
        s=0.
    t=(ef*s+fr)/ff
    if t<0:
        t=0.;s=float(np.clip(-er/ee,0.,1.))
    elif t>1:
        t=1.;s=float(np.clip((ef-er)/ee,0.,1.))
    pa=a+e*s
    pb=c+f*t
    dist=float(np.linalg.norm(pb-pa))
    need(math.isfinite(dist) and 0<=s<=1 and 0<=t<=1,
         "T0NORMAL_SEGMENT_CLOSEST_POINT_FAILED")
    return pa,pb,s,float(t),dist


def geometric_contact_feature_rows(source_edges, registry, index,
                                   positions, link_geometry):
    """Source-defined paired boundary segments: closest-point diagnostic.

    Signed normal projection is NOT a globally valid nonpenetration
    condition, since the nearest features can be endpoints.
    """
    pos=np.asarray(positions,dtype=float)
    links={ (tuple(x["plate_pair"]),int(x["parent_node_id"])):x
            for x in link_geometry["source_link_details"]}
    rows=[]
    need(len(source_edges)==len(registry["edges"]),
         "T0NORMAL_SOURCE_EDGE_COUNT_DRIFT")
    for src in sorted(source_edges,key=lambda x:tuple(
            sorted(map(int,x["source_edge_node_ids"])) )):
        a,b=sorted(map(int,src["source_edge_node_ids"]))
        pair=tuple(sorted(map(int,src["plate_pair"])))
        need((a,b) in registry["edges"] and
             registry["edges"][(a,b)]==pair,
             "T0NORMAL_SOURCE_EDGE_OWNER_MISMATCH")
        p,q=pair
        pa,pb,s,t,dist=closest_segments(
            pos[index[(p,a)]],pos[index[(p,b)]],
            pos[index[(q,a)]],pos[index[(q,b)]],
        )
        n=unit(np.asarray(
            links[(pair,a)]["current_contact_normal_cartesian"])+
            np.asarray(links[(pair,b)]["current_contact_normal_cartesian"]))
        signed=float((pb-pa)@n)
        tangential=float(np.linalg.norm((pb-pa)-signed*n))
        rows.append({
            "source_boundary_id":src["source_boundary_id"],
            "source_edge_node_ids":[a,b],
            "plate_pair":list(pair),
            "segment_s_plate_p":s,
            "segment_t_plate_q":t,
            "unsigned_nearest_segment_distance_m":dist,
            "signed_nearest_segment_separation_m":signed,
            "tangent_nearest_segment_separation_m":tangential,
            "contact_normal_from_average_current_pair_node_normals":n.tolist(),
            "nearest_feature_is_not_a_physical_gap_law":True,
        })
    return rows



def t0_source_centroid_edge_normal_audit(faces, plates, latlon, source_edges):
    """Per EXACT source edge: original two triangle-centroid normal vs edge normal."""
    incidence={}
    for face,p in zip(faces,plates,strict=True):
        a,b,c=tuple(map(int,face))
        for edge in ((a,b),(b,c),(c,a)):
            k=tuple(sorted(edge))
            incidence.setdefault(k,[]).append((int(p),face))
    parent_xyz={}
    for n,ll in latlon.items():
        parent_xyz[int(n)]=frames_and_cartesian([ll])[0][0]
    samples=[]
    for source in source_edges:
        edge=tuple(sorted(map(int,source["source_edge_node_ids"])))
        p,q=tuple(sorted(map(int,source["plate_pair"])))
        rows=incidence.get(edge,[])
        need(len(rows)==2 and {x[0] for x in rows}=={p,q},
             "T0NORMAL_EDGE_TRIANGLE_OWNERSHIP_INVALID")
        a,b=edge
        xyz_a,xyz_b=parent_xyz[a],parent_xyz[b]
        radial=unit(xyz_a+xyz_b)
        edge_tangent=unit(xyz_b-xyz_a)
        edge_normal=unit(np.cross(radial,edge_tangent))
        centroids={plate:np.mean([parent_xyz[n] for n in face],axis=0)
                   for plate,face in rows}
        cent_delta=centroids[q]-centroids[p]
        projected=cent_delta-radial*(cent_delta@radial)
        centroid_normal=unit(projected)
        if edge_normal@centroid_normal<0:
            edge_normal=-edge_normal
        angle=float(math.acos(np.clip(
            edge_normal@centroid_normal,-1.,1.)))
        samples.append({
            "source_boundary_id":source["source_boundary_id"],
            "source_edge_node_ids":list(edge),
            "source_plate_pair":[p,q],
            "original_edge_length_m":float(np.linalg.norm(xyz_b-xyz_a)),
            "source_centroid_p_to_q_normal_cartesian":centroid_normal.tolist(),
            "original_edge_derived_normal_cartesian":edge_normal.tolist(),
            "angle_centroid_normal_vs_edge_normal_rad":angle,
        })
    need(len(samples)==len(source_edges)>0,
         "T0NORMAL_SOURCE_EDGE_CENTROID_AUDIT_INCOMPLETE")
    return {
        "original_source_contact_edge_count":len(samples),
        "maximum_centroid_vs_edge_normal_angle_rad":max(
            r["angle_centroid_normal_vs_edge_normal_rad"] for r in samples),
        "mean_centroid_vs_edge_normal_angle_rad":float(np.mean([
            r["angle_centroid_normal_vs_edge_normal_rad"] for r in samples])),
        "per_source_boundary_edge":samples,
    }


def displaced_on_sphere(x, delta, radius=RADIUS_M):
    y=np.asarray(x,dtype=float)+np.asarray(delta,dtype=float)
    return radius*y/np.linalg.norm(y)


def directional_gap_derivative(positions,velocities,rotations,east,north,
                               index,links,incident,contact_index,
                               direction,shift_view,step):
    """Independent finite-difference derivative, recomputing *all* normals."""
    target=links[contact_index]
    pair=target["plate_pair"]
    node=target["parent_node_id"]
    p,q=pair
    vid=index[(p if shift_view=="p" else q,node)]
    plus=np.array(positions,copy=True)
    minus=np.array(positions,copy=True)
    plus[vid]=displaced_on_sphere(plus[vid],step*direction)
    minus[vid]=displaced_on_sphere(minus[vid],-step*direction)
    values=[]
    for sample in (plus,minus):
        r=moving_contact_geometry(
            sample,velocities,rotations,east,north,index,links,
            incident,np.zeros(len(links)),np.zeros(len(links)))
        values.append(r["source_link_details"][contact_index][
            "signed_geometric_point_pair_gap_m"])
    return (values[0]-values[1])/(2.*step)


def normal_jacobian_audit(positions, velocities, rotations, east,north,
                          index, links, incident, baseline_geometry,
                          max_samples=6):
    # Include all source-closing KKT-active contacts first, then controls.
    rows=baseline_geometry["source_link_details"]
    active=[i for i,r in enumerate(rows)
            if r["normalized_source_KKT_reaction"]>1e-9]
    selected=active[:max_samples]
    for i in range(len(links)):
        if len(selected)>=max_samples:break
        if i not in selected:selected.append(i)
    audits=[]
    for k in selected:
        r=rows[k]
        n=unit(r["current_contact_normal_cartesian"])
        values={}
        for view in ("p","q"):
            derivatives={}
            for h in (1.0,0.5,0.25):
                derivatives[str(h)]=float(directional_gap_derivative(
                    positions,velocities,rotations,east,north,
                    index,links,incident,k,n,view,h))
            target=-1. if view=="p" else 1.
            values[view]={
                "h1_m_derivative":derivatives["1.0"],
                "h0_5_m_derivative":derivatives["0.5"],
                "h0_25_m_derivative":derivatives["0.25"],
                "estimated_curvature_effect_from_frozen_normal":
                    derivatives["0.25"]-target,
                "finite_difference_refinement_discrepancy":
                    abs(derivatives["0.5"]-derivatives["0.25"]),
            }
        audits.append({
          "plate_pair":r["plate_pair"],
          "parent_node_id":r["parent_node_id"],
          "old_normalized_T0_KKT_active":
              r["normalized_source_KKT_reaction"]>1e-9,
          "current_gap_m":r["signed_geometric_point_pair_gap_m"],
          "directional_gap_derivatives":values,
        })
    need(all(
        math.isfinite(v["h0_25_m_derivative"]) and
        v["finite_difference_refinement_discrepancy"]<3e-4 and
        abs(v["h0_25_m_derivative"]-
            (-1. if view=="p" else 1.))<.1
        for row in audits
        for view,v in row["directional_gap_derivatives"].items()
    ),"T0NORMAL_MOVING_GAP_JACOBIAN_FD_FAILED")
    return {
        "sampled_pair_node_links":len(audits),
        "old_KKT_active_links_sampled":len(active[:max_samples]),
        "max_FD_refinement_discrepancy":max(
            v["finite_difference_refinement_discrepancy"]
            for row in audits
            for v in row["directional_gap_derivatives"].values()),
        "max_absolute_gap_directional_derivative_error_vs_frozen_normal":max(
            abs(v["estimated_curvature_effect_from_frozen_normal"])
            for row in audits
            for v in row["directional_gap_derivatives"].values()),
        "derivative_details":audits,
    }


def objective_feature_invariance(positions,velocities,rotations,
                                  east,north,index,links,incident,source_edges,
                                  registry,geometry):
    Q=Rotation.from_rotvec([.4,-.7,.2]).as_matrix()
    moved=positions@Q.T
    moved_v=velocities@Q.T
    moved_e=east@Q.T
    moved_n=north@Q.T
    rotated_R={p:Q@R@Q.T for p,R in rotations.items()}
    r=moving_contact_geometry(
        moved,moved_v,rotated_R,moved_e,moved_n,index,links,
        incident,np.zeros(len(links)),np.zeros(len(links)))
    originals=geometry["source_link_details"]
    transformed=r["source_link_details"]
    node_gap_error=max(abs(a["signed_geometric_point_pair_gap_m"]-
                           b["signed_geometric_point_pair_gap_m"])
         for a,b in zip(originals,transformed,strict=True))
    f0=geometric_contact_feature_rows(source_edges,registry,index,
                                      positions,geometry)
    f1=geometric_contact_feature_rows(source_edges,registry,index,
                                      moved,r)
    segment_dist_error=max(abs(a["unsigned_nearest_segment_distance_m"]-
                               b["unsigned_nearest_segment_distance_m"])
         for a,b in zip(f0,f1,strict=True))
    signed_feature_error=max(abs(a["signed_nearest_segment_separation_m"]-
                                 b["signed_nearest_segment_separation_m"])
         for a,b in zip(f0,f1,strict=True))
    need(max(node_gap_error,segment_dist_error,signed_feature_error)<1e-7,
         "T0NORMAL_GEOMETRIC_FEATURE_SO3_OBJECTIVITY_FAILED")
    return {"max_node_pair_signed_gap_absolute_error_m":node_gap_error,
            "max_closest_segment_distance_absolute_error_m":segment_dist_error,
            "max_signed_segment_gap_absolute_error_m":signed_feature_error,
            "finite_SO3_rotation_rad":float(np.linalg.norm([.4,-.7,.2]))}



def _feature_unit(a):
    a=np.asarray(a,dtype=float)
    mag=float(np.linalg.norm(a))
    need(a.shape==(3,) and np.all(np.isfinite(a)) and
         math.isfinite(mag) and mag>1e-15,
         "FEATURE_INVALID_REFERENCE_NORMAL")
    return a/mag


def classify_edge_pair(a,b,c,d,reference_normal):
    """Source-owned finite edge witness; refuse ambiguous configurations.

    Only skew, strictly interior and well-oriented witnesses receive a
    mathematical signed gap. No rock/face/Signorini law follows from this.
    """
    a,b,c,d=(np.asarray(x,dtype=float) for x in (a,b,c,d))
    e,f=b-a,d-c
    ee,ff=float(e@e),float(f@f)
    need(ee>1e-10 and ff>1e-10,"FEATURE_DEGENERATE_SOURCE_EDGE")
    ref=_feature_unit(reference_normal)
    pa,pb,s,t,dist=closest_segments(a,b,c,d)
    cross=np.cross(e,f)
    ratio=float((cross@cross)/(ee*ff))
    need(math.isfinite(ratio),"FEATURE_NONFINITE_PARALLEL_RATIO")
    result={
        "classification":"AMBIGUOUS","reason":None,
        "physical_surface_contact_qualified":False,
        "engineered_edge_gap_eligible":False,
        "unsigned_closest_segment_distance_m":dist,
        "parallel_ratio":ratio,"s":float(s),"t":float(t),
        "signed_gap_m":None,"normal":None,"gradient":None,
    }
    if ratio<PARALLEL_RATIO_MIN:
        result["reason"]="PARALLEL_OR_NEAR_PARALLEL_NONUNIQUE_WITNESS"
        return result
    if min(s,1-s,t,1-t)<=WITNESS_INTERIOR_MARGIN:
        result["reason"]="BOUNDARY_ENDPOINT_OR_FEATURE_SWITCH"
        return result
    normal=cross/np.linalg.norm(cross)
    alignment=float(normal@ref)
    if abs(alignment)<REFERENCE_ALIGNMENT_MIN:
        result["reason"]="UNSUPPORTED_SOURCE_NORMAL_ORIENTATION"
        return result
    if alignment<0:
        normal=-normal
    signed=float((pb-pa)@normal)
    gradient=np.array([-(1-s)*normal,-s*normal,
                       (1-t)*normal,t*normal])
    result.update({
        "classification":"ENGINEERING_EDGE_EDGE_INTERIOR",
        "reason":"ENGINEERING_ONLY_NO_PHYSICAL_SURFACE_PROOF",
        "engineered_edge_gap_eligible":True,
        "signed_gap_m":signed,
        "normal":normal.tolist(),
        "gradient":gradient.tolist(),
        "reference_alignment_abs":abs(alignment),
    })
    return result


def verify_engineering_witness(vertices,reference_normal,step=1e-4):
    """Same signed gap, consistent two-sided FD, virtual work and SO(3)."""
    x=np.asarray(vertices,dtype=float)
    need(x.shape==(4,3),"FEATURE_WRONG_VERTICES_SHAPE")
    original=classify_edge_pair(*x,reference_normal)
    need(original["engineered_edge_gap_eligible"],
         "FEATURE_INELIGIBLE_FOR_JACOBIAN")
    analytical=np.asarray(original["gradient"])
    fd=np.empty((4,3),dtype=float)
    for k in range(4):
        for axis in range(3):
            u=np.zeros_like(x)
            u[k,axis]=step
            yp=classify_edge_pair(*(x+u),reference_normal)
            ym=classify_edge_pair(*(x-u),reference_normal)
            need(yp["engineered_edge_gap_eligible"] and
                 ym["engineered_edge_gap_eligible"],
                 "FEATURE_FINITE_DIFFERENCE_WITNESS_SWITCH")
            fd[k,axis]=(yp["signed_gap_m"]-ym["signed_gap_m"])/(2*step)
    error=float(np.max(np.abs(fd-analytical)))
    need(error<3e-4,"FEATURE_CONSISTENT_GAP_JACOBIAN_FAILED")
    lam=.25  # normalized manufactured multiplier, NOT SI rock force
    forces=lam*analytical
    force_balance=float(np.linalg.norm(np.sum(forces,axis=0)))
    torque_balance=float(np.linalg.norm(np.sum(np.cross(x,forces),axis=0)))
    need(force_balance<1e-8 and torque_balance<1e-6,
         "FEATURE_FORCE_TORQUE_OR_VIRTUAL_WORK_FAILED")
    displacement=np.array([[.3,-.2,.1],[-.1,.25,.05],
                           [.2,.05,-.15],[-.1,-.2,.2]])
    predicted=float(lam*np.sum(analytical*displacement))
    actual=float(lam*np.sum(fd*displacement))
    need(abs(predicted-actual)<3e-4,"FEATURE_VIRTUAL_WORK_FAILED")
    Q=Rotation.from_rotvec([.4,-.7,.2]).as_matrix()
    rotated=classify_edge_pair(*(x@Q.T),Q@_feature_unit(reference_normal))
    need(rotated["engineered_edge_gap_eligible"],
         "FEATURE_SO3_WITNESS_SWITCH")
    so3_gap=abs(original["signed_gap_m"]-rotated["signed_gap_m"])
    so3_unsigned=abs(original["unsigned_closest_segment_distance_m"]-
                     rotated["unsigned_closest_segment_distance_m"])
    so3_gradient=float(np.max(np.abs(
        np.asarray(rotated["gradient"])-analytical@Q.T)))
    need(max(so3_gap,so3_unsigned)<SO3_TOL_M and
         so3_gradient<1e-7,"FEATURE_SO3_OBJECTIVITY_FAILED")
    return {
        "max_absolute_jacobian_fd_error":error,
        "normalized_net_force":force_balance,
        "normalized_net_torque":torque_balance,
        "normalized_virtual_work_error":abs(predicted-actual),
        "SO3_signed_gap_error_m":so3_gap,
        "SO3_unsigned_distance_error_m":so3_unsigned,
        "SO3_gradient_error":so3_gradient,
        "physical_force_proved":False,
    }


def source_feature_inventory(source_edges,registry,index,positions,previous_rows,
                             step=.25):
    """Source-ID-complete inventory with explicit fail-closed abstentions."""
    previous={row["source_boundary_id"]:row for row in previous_rows}
    need(len(previous)==len(source_edges)==len(registry["edges"]),
         "FEATURE_PREVIOUS_EDGE_INVENTORY_MISMATCH")
    rows=[]
    for src in sorted(source_edges,key=lambda x:x["source_boundary_id"]):
        key=src["source_boundary_id"]
        a,b=sorted(map(int,src["source_edge_node_ids"]))
        p,q=sorted(map(int,src["plate_pair"]))
        need((a,b) in registry["edges"] and
             registry["edges"][(a,b)]==(p,q) and key in previous,
             "FEATURE_SOURCE_EDGE_OWNER_MISMATCH")
        vertices=np.asarray([
            positions[index[(p,a)]],positions[index[(p,b)]],
            positions[index[(q,a)]],positions[index[(q,b)]]
        ])
        ref=previous[key]["contact_normal_from_average_current_pair_node_normals"]
        feature=classify_edge_pair(*vertices,ref)
        if feature["engineered_edge_gap_eligible"]:
            try:
                feature["consistency_audit"]=verify_engineering_witness(
                    vertices,ref,step=step)
            except SparseP1Error as exc:
                # Do NOT preserve an invalid signed contact constraint.
                feature["classification"]="NOT_QUALIFIED"
                feature["reason"]="SOURCE_CONSISTENCY_"+str(exc)
                feature["engineered_edge_gap_eligible"]=False
                feature["signed_gap_m"]=None
                feature["gradient"]=None
                feature["normal"]=None
                feature["consistency_audit"]=None
        feature.update({
            "source_boundary_id":key,
            "source_edge_node_ids":[a,b],
            "source_plate_pair":[p,q],
        })
        rows.append(feature)
    need(len(rows)==len(source_edges) and
         len({row["source_boundary_id"] for row in rows})==len(rows),
         "FEATURE_SOURCE_EDGE_COVERAGE_INCOMPLETE")
    return {
        "source_original_feature_rows":rows,
        "counts_by_classification":dict(Counter(
            x["classification"] for x in rows)),
        "source_eng_only_eligible_count":sum(
            x["engineered_edge_gap_eligible"] for x in rows),
        "physical_surface_contact_count":0,
    }


def run_one(width,multiscale,nodal,omegas,prior_region,prior_normal_region):
    from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
    from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
        parse_regional_pre,validate_column_for_potential)
    width=int(width)
    mdir,ndir=Path(multiscale),Path(nodal)
    r=next(x for x in json.loads((mdir/"CONTINUATION_A.json").read_text())[
            "topological_comparative_extents"]
           if int(x["cell_extent_per_side"])==width)
    nod=next(x for x in json.loads((ndir/"SOURCE_NODAL_ELEMENT_G2.json").read_text())[
            "scales"] if int(x["extent_cells"])==width)
    ids=list(map(int,r["parent_node_ids"]))
    feg_path=mdir/f"OUTER_A_{width:02d}x{width:02d}.feg"
    pre_path=mdir/f"OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat"
    need(sha256(feg_path)==r["output_FEG_sha256"] and
         sha256(pre_path)==r["output_PRE_sha256"],
         "T0NORMAL_SOURCE_FEG_PRE_SHA_CHANGED")
    feg=parse_feg(feg_path.read_text(),mode="SHELLS_READY")
    pre=parse_regional_pre(pre_path,r["PRE_source_field_order"],ids)
    need({str(k):v for k,v in pre.items()}==
         {str(k):v for k,v in nod["source_PRE_by_parent_node"].items()},
         "T0NORMAL_NODAL_BINDING_CHANGED")
    for row in pre.values():validate_column_for_potential(row)
    ll={ids[i]:(float(n.latitude_deg),float(n.longitude_deg))
        for i,n in enumerate(feg.nodes)}
    faces=[tuple(ids[int(n)-1] for n in e.node_ids) for e in feg.elements]
    plates=list(map(int,r["parent_triangle_plate_ids"]))
    registry=contact_registry(ids,faces,plates,ll,r["source_contact_edges"])
    incident=boundary_node_edges(r["source_contact_edges"],registry)
    K,index,coords,plate_views,stats=assemble_split_source(
        ids,faces,plates,ll,pre)
    g=euler_source_en(coords,plate_views,omegas)
    J=normal_constraint_matrix(registry["contacts"],index,K.shape[0])
    source_xyz,radial,east,north=frames_and_cartesian(coords)
    nview=len(plate_views)
    zero=np.zeros(K.shape[0],dtype=float)
    t0_xyz,t0_velocity,t0_R=rigid_motion_with_residual(
        source_xyz,east,north,plate_views,omegas,g,
        zero,g,0.)
    # At T0 paired material copies must coincide to numerical precision.
    t0_geo=moving_contact_geometry(
        t0_xyz,t0_velocity,t0_R,east,north,index,
        registry["contacts"],incident,np.zeros(J.shape[0]),
        np.zeros(J.shape[0]))
    need(t0_geo["max_absolute_geometry_minus_T0_gap_m"]<1e-9,
         "T0NORMAL_COINCIDENT_SOURCE_CONTACT_POINTS_NOT_COINCIDENT")
    angle_values=[row["angle_normal_from_transported_T0_rad"]
                  for row in t0_geo["source_link_details"]]
    t0_features=geometric_contact_feature_rows(
        r["source_contact_edges"],registry,index,t0_xyz,t0_geo)
    t0_inventory=source_feature_inventory(
        r["source_contact_edges"],registry,index,t0_xyz,t0_features)
    t0_edge_centroid_audit=t0_source_centroid_edge_normal_audit(
        faces,plates,ll,r["source_contact_edges"])
    need(all(v["unsigned_nearest_segment_distance_m"]<1e-9
             for v in t0_features),
         "T0NORMAL_SOURCE_EDGES_NOT_COINCIDENT")
    source_angles={
        (tuple(row["plate_pair"]),int(row["parent_node_id"])):
        row["angle_normal_from_transported_T0_rad"]
        for row in t0_geo["source_link_details"]}
    trajectory=integrate(K,J,g,1.,1000,checkpoints=YEARS)
    need(abs(trajectory["max_scaled_complementarity"])<1e-8,
         "T0NORMAL_SOURCE_KKT_REPLAY_FAILED")
    out={}
    for year in YEARS:
        ss=trajectory["snapshots"][year]
        xyz,velocity,R=rigid_motion_with_residual(
            source_xyz,east,north,plate_views,omegas,g,
            ss["displacement"],ss["velocity"],year)
        geo=moving_contact_geometry(
            xyz,velocity,R,east,north,index,
            registry["contacts"],incident,ss["gap"],ss["lambda"])
        old=prior_region["objective_geometry_reconstruction_at_years"][str(year)]
        need(geo["source_contact_link_count"]==
             old["source_contact_link_count"] and
             abs(geo["geometric_signed_gap_min_m"]-
                 old["geometric_signed_gap_min_m"])<1e-7 and
             abs(geo["max_absolute_geometry_minus_T0_gap_m"]-
                 old["max_absolute_geometry_minus_T0_gap_m"])<1e-7,
             "T0NORMAL_PRIOR_40PASS_3D_GAP_REPLAY_MISMATCH")
        old_details=old["source_link_details"]
        need(all(a["parent_node_id"]==b["parent_node_id"] and
                 a["plate_pair"]==b["plate_pair"] and
                 abs(a["signed_geometric_point_pair_gap_m"]-
                     b["signed_geometric_point_pair_gap_m"])<1e-7
                 for a,b in zip(geo["source_link_details"],old_details,
                                 strict=True)),
             "T0NORMAL_PRIOR_3D_PAIRWISE_REPLAY_MISMATCH")
        features=geometric_contact_feature_rows(
            r["source_contact_edges"],registry,index,xyz,geo)
        old_normal=prior_normal_region["checkpoints"][str(year)]["source_edge_feature_details"]
        old_normal_by_id={x["source_boundary_id"]:x for x in old_normal}
        need(len(old_normal_by_id)==len(features),"FEATURE_PRIOR_NORMAL_EDGE_COUNT_DRIFT")
        for row in features:
            prev=old_normal_by_id[row["source_boundary_id"]]
            need(prev["plate_pair"]==row["plate_pair"] and
                 abs(prev["unsigned_nearest_segment_distance_m"]-
                     row["unsigned_nearest_segment_distance_m"])<1e-7 and
                 abs(prev["signed_nearest_segment_separation_m"]-
                     row["signed_nearest_segment_separation_m"])<1e-7,
                 "FEATURE_PRIOR_FAIR_EDGE_REPLAY_FAILED")
        feature_inventory=source_feature_inventory(
            r["source_contact_edges"],registry,index,xyz,features)
        jac=normal_jacobian_audit(
            xyz,velocity,R,east,north,index,registry["contacts"],
            incident,geo,max_samples=6)
        so3=objective_feature_invariance(
            xyz,velocity,R,east,north,index,registry["contacts"],
            incident,r["source_contact_edges"],registry,geo)
        # The old gap KKT and NEW geometric gap are separate models.
        # Never claim moving contact complementarity based on either alone.
        out[str(year)]={
          "point_pair_geometric_min_gap_m":
              geo["geometric_signed_gap_min_m"],
          "old_KKT_active_links":geo["active_KKT_link_count"],
          "min_3D_gap_on_old_KKT_active_links_m":
              geo["min_active_geometric_gap_m"],
          "max_absolute_3D_vs_T0_gap_m":
              geo["max_absolute_geometry_minus_T0_gap_m"],
          "source_feature_edge_count":len(features),
          "source_triple_junction_source_node":34587 if width==16 else None,
          "minimum_unsigned_segment_segment_distance_m":
              min(x["unsigned_nearest_segment_distance_m"] for x in features),
          "minimum_signed_nearest_segment_projection_m":
              min(x["signed_nearest_segment_separation_m"] for x in features),
          "maximum_segment_segment_distance_m":
              max(x["unsigned_nearest_segment_distance_m"] for x in features),
          "negative_signed_segment_projection_count_below_minus_1um":
              sum(x["signed_nearest_segment_separation_m"]<-1e-6
                  for x in features),
          "jacobian":jac,"objective_SO3":so3,
          "feature_admissibility_inventory":feature_inventory,
          "source_edge_feature_details":features,
          "source_pair_node_gap_details":geo["source_link_details"],
        }
    previous_by_id={
        0:{x["source_boundary_id"]:x for x in t0_inventory["source_original_feature_rows"]}
    }
    for yr in YEARS:
        previous_by_id[yr]={
            x["source_boundary_id"]:x
            for x in out[str(yr)]["feature_admissibility_inventory"][
                "source_original_feature_rows"]
        }
    transitions=[]
    for earlier,later in zip((0,)+YEARS[:-1],YEARS):
        for key in sorted(previous_by_id[earlier]):
            old=previous_by_id[earlier][key]
            new=previous_by_id[later][key]
            if (old["classification"],old["reason"])!=(
                new["classification"],new["reason"]):
                transitions.append({
                    "source_boundary_id":key,"from_year":earlier,
                    "to_year":later,"from":old["classification"],
                    "to":new["classification"],
                    "from_reason":old["reason"],"to_reason":new["reason"],
                })
    return {
      "extent":width,
      "T0_feature_admissibility_inventory":t0_inventory,
      "source_feature_classification_transitions":transitions,
      "source_plate_ids":sorted(set(plates)),
      "source_contact_edges":len(registry["edges"]),
      "source_contact_links":len(registry["contacts"]),
      "original_source_triple_node_ids":registry["triple_junction_parent_ids"],
      "T0_normal_definition_parity":{
        "source_centroid_normal_vs_edge_normal_max_angle_rad":
            max(angle_values),
        "source_centroid_normal_vs_edge_normal_mean_angle_rad":
            float(np.mean(angle_values)),
        "source_link_normal_angles": [{
            "source_parent_node_id":int(k[1]),"plate_pair":list(k[0]),
            "T0_angle_rad":v,
        } for k,v in sorted(source_angles.items())],
        "source_segments_coincident_at_T0":True,
        "source_centroid_vs_edge_per_boundary_audit":
            t0_edge_centroid_audit,
      },
      "checkpoints":out,
      "physical_contact_law_solved_in_updated_geometry":False,
    }


def execute(multiscale,nodal,unilateral,prior_moving,prior_normal_jacobian,out,root=ROOT):
    """Single worker: FAIR two-worker previous run slower (0.735x)."""
    mdir,ndir,un,old,normal_old,out,root=map(Path,(
        multiscale,nodal,unilateral,prior_moving,prior_normal_jacobian,out,root))
    need(not out.exists(),"FEATURE_OUTPUT_ALREADY_EXISTS")
    began=time.perf_counter()
    source_pins=certify_priors(mdir,ndir,un,root)
    m=json.loads((old/"MANIFEST.json").read_text())
    prior=json.loads((old/"REPORT.json").read_text())
    need(m["schema"]==
        "ARCANA_R6_SOURCE_MOVING_3D_CONTACT_DIAGNOSTIC_MANIFEST_V1"
        and m["files"]["REPORT.json"]==sha256(old/"REPORT.json")
        and prior["status"]==
        "PASS_SOURCE_MOVING_3D_CONTACT_GEOMETRY_DIAGNOSTIC__CONTACT_PHYSICS_OPEN"
        and prior["physical_T1"] is None
        and prior["D_024"]=="ACTIVE"
        and prior["prior_unilateral_report_sha256"]==
        sha256(un/"REPORT.json"),
        "T0NORMAL_PRIOR_MOVING_3D_FAIR_SHA_STATUS_INVALID")
    normal_manifest=json.loads((normal_old/"MANIFEST.json").read_text())
    normal_report=json.loads((normal_old/"REPORT.json").read_text())
    need(normal_manifest["schema"]==
         "ARCANA_R6_T0_NORMAL_NEAREST_SEGMENT_JACOBIAN_MANIFEST_V1"
         and normal_manifest["files"]["REPORT.json"]==
             sha256(normal_old/"REPORT.json")
         and normal_report["status"]==
             "PASS_SOURCE_T0_CONTACT_NORMAL_AND_MOVING_3D_EDGE_JACOBIAN_DIAGNOSTIC__GEOMETRIC_KKT_OPEN"
         and normal_report["physical_T1"] is None
         and normal_report["D_024"]=="ACTIVE"
         and sha256(old/"REPORT.json")==normal_report["source_sha256"][
             str(old/"REPORT.json")],
         "FEATURE_PRIOR_NORMAL_FAIR_SHA_STATUS_INVALID")
    for source_path,digest in normal_report["source_sha256"].items():
        need(Path(source_path).is_file() and
             sha256(Path(source_path))==digest,
             "FEATURE_PRIOR_SOURCE_PIN_CHANGED")
    source_pins[str(normal_old/"REPORT.json")]=sha256(normal_old/"REPORT.json")
    source_pins[str(normal_old/"MANIFEST.json")]=sha256(normal_old/"MANIFEST.json")
    source_pins[str(old/"REPORT.json")]=sha256(old/"REPORT.json")
    source_pins[str(old/"MANIFEST.json")]=sha256(old/"MANIFEST.json")
    mesh,omegas,pins,horizon,pre=source_inputs(root)
    need(horizon>1000,"T0NORMAL_G1_SOURCE_HORIZON_INVALID")
    scope={int(x["extent"]):x for x in prior["regional_results"]}
    need(set(scope)=={8,16},"T0NORMAL_PRIOR_SCOPE_INCORRECT")
    normal_scope={int(x["extent"]):x for x in normal_report["results"]}
    need(set(normal_scope)=={8,16},"FEATURE_PRIOR_NORMAL_SCOPE_INVALID")
    results=[run_one(width,mdir,ndir,omegas,scope[width],
                     normal_scope[width]) for width in (8,16)]
    need(results[0]["source_contact_links"]==13 and
         results[1]["source_contact_links"]==39 and
         results[1]["original_source_triple_node_ids"]==[34587],
         "T0NORMAL_SOURCE_CONTACT_COUNTS_CHANGED")
    need(all(sha256(Path(path))==h for path,h in source_pins.items()),
         "T0NORMAL_SOURCE_FILES_MUTATED_DURING_AUDIT")
    report={
        "schema":SCHEMA,"status":STATUS,
        "original_world_mesh_sha256":mesh.normalized_sha256,
        "source_sha256":source_pins,
        "results":results,
        "computation_workers":1,
        "why_serial":"PREVIOUS_FAIR_TWO_WORKERS_0.73485X_SLOWER_THAN_ONE",
        "total_wall_seconds":time.perf_counter()-began,
        "peak_process_memory":usage(),
        "t0_centroid_and_edge_normals_not_assumed_equal":True,
        "prior_normal_report_sha256":sha256(normal_old/"REPORT.json"),
        "source_witness_sign_not_physical_surface_gap":True,
        "source_ambiguous_edges_do_not_create_contact_constraints":True,
        "geometric_nearest_segments_reported_as_signed_diagnostic_only":True,
        "moving_contact_QP_enforced":False,
        "engineered_contact_solver_runs":0,
        "source_contact_signed_surface_gap_proved":False,
        "updated_3D_face_face_nonpenetration_validated":False,
        "real_G2_G3_or_G4_physics":False,
        "HistoryStore_modified":False,
        "physical_solver_runs":0,"physical_T1":None,"D_024":"ACTIVE",
    }
    out.mkdir(parents=True,exist_ok=False)
    r=out/"REPORT.json"
    r.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_CONTACT_FEATURE_ADMISSIBILITY_MANIFEST_V1",
        "status":STATUS,"files":{"REPORT.json":sha256(r)},
        "physical_T1":None,"no_canonical_promotion":True,
    },indent=2)+"\n")
    return {
        "status":STATUS,
        "regions":[{
           "extent":s["extent"],
           "T0_max_centroid_vs_edge_angle_rad":
              s["T0_normal_definition_parity"][
                  "source_centroid_normal_vs_edge_normal_max_angle_rad"],
           "T0_feature_classification_counts":
              s["T0_feature_admissibility_inventory"]["counts_by_classification"],
           "source_feature_classification_transition_count":
              len(s["source_feature_classification_transitions"]),
           "checkpoints":{
               k:{label:value for label,value in entry.items()
                  if label not in ("source_edge_feature_details",
                                   "source_pair_node_gap_details",
          "feature_admissibility_inventory")}
               for k,entry in s["checkpoints"].items()
           },
        } for s in results],
        "total_wall_seconds":report["total_wall_seconds"],
        "physical_solver_runs":0,"physical_T1":None,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",required=True,type=Path)
    p.add_argument("--nodal",required=True,type=Path)
    p.add_argument("--prior-unilateral",required=True,type=Path)
    p.add_argument("--prior-moving-3d",required=True,type=Path)
    p.add_argument("--prior-normal-jacobian",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    print(json.dumps(execute(a.multiscale,a.nodal,a.prior_unilateral,
                             a.prior_moving_3d,a.prior_normal_jacobian,
                             a.output,a.root),
                     indent=2,allow_nan=False))


if __name__=="__main__":
    main()

"""Controlled perimeter traces on the original regional sphere."""
from collections import defaultdict
import math

import numpy as np

from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian
from experiments.r6_thermo_provider_pilot_v1 import c08_mechanics as mechanics
from experiments.r6_thermo_provider_pilot_v1.run_c08_regional_closure import need

SCENARIO = "C10_R8_DIORITE2_KINEMATICALLY_CONTROLLED_FREE_SLIP_V1"
PREFERRED = "smooth_distributed"
RADIUS = 6_371_000.
RAD_NATIVE = .0174532925199433


def transport(v, a, b):
    """Levi-Civita transport along the shorter spherical segment."""
    dot = float(a@b)
    need(dot > -1+1e-12, "C10_ANTIPODAL_SEGMENT")
    return v-(v@b)*(a+b)/(1+dot)


def arc(a,b):
    return RADIUS*math.atan2(np.linalg.norm(np.cross(a,b)),a@b)


def angle_mag(south,east):
    return math.hypot(south,east), math.degrees(math.atan2(east,-south))%360


def decode_native(magnitude, azimuth):
    arg = (180.-azimuth)*RAD_NATIVE
    return np.array([magnitude*math.cos(arg),magnitude*math.sin(arg)])


def blend(s, kind):
    if kind=="linear_arc":
        return s
    if kind=="smooth_distributed":
        return s*s*(3-2*s)
    raise ValueError("C10_UNKNOWN_TRACE")


def side_path(edges, side, fixed):
    adj = defaultdict(list)
    for edge in edges:
        if edge["side"]==side:
            a,b = edge["source_parent_node_ids"]
            adj[a].append(b)
            adj[b].append(a)
    ends = [p for p,v in adj.items() if len(v)==1]
    need(len(adj)==9 and len(ends)==2 and all(len(v)<=2 for v in adj.values())
         and {fixed[p]["cut"] for p in ends}=={"west","east"}, "C10_CUT_GRAPH")
    path = [next(p for p in ends if fixed[p]["cut"]=="west")]
    while len(path)<len(adj):
        available = [q for q in adj[path[-1]] if q not in path]
        need(len(available)==1,"C10_CUT_TRACE_ORDER")
        path.append(available[0])
    need(path[-1] in ends, "C10_CUT_ENDPOINT")
    return path


def controlled_traces(package, previous):
    nodes = package["G4_mapping"]["nodes"]
    ll = [row["runtime_lat_lon_deg"] for row in nodes]
    _,rad,east,north = frames_and_cartesian(ll,RADIUS)
    parent = {r["parent_id"]:r["local_id"]-1 for r in nodes}
    basis = np.stack((-north,east),axis=1)
    modes = np.column_stack([np.einsum("nci,ni->nc",basis,np.cross(a,rad)).ravel() for a in np.eye(3)])
    fixed = {int(p):value for p,value in previous["distal_node_candidates"].items()}
    edges = previous["edges"]
    edge_index = {tuple(sorted(e["source_parent_node_ids"])):e for e in edges}
    cycle = [r["parent_node_id"] for r in package["BC_records_in_perimeter_order"]]
    need(len(cycle)==len(set(cycle))==len(edge_index)==32 and len(fixed)==18,
         "C10_PERIMETER_INVENTORY")
    for a,b in zip(cycle,cycle[1:]+cycle[:1],strict=True):
        need(tuple(sorted((a,b))) in edge_index,"C10_PERIMETER_EDGE")
    paths = {side:side_path(edges,side,fixed) for side in ("north","south")}
    candidates = {}
    rhs_design = {}
    for kind in ("linear_arc",PREFERRED):
        values = {p:row["south_east_m_s"][:] for p,row in fixed.items()}
        cuts = {}
        for side,path in paths.items():
            local = [parent[p] for p in path]
            abscissa = np.r_[0.,np.cumsum([arc(rad[i],rad[j]) for i,j in zip(local[:-1],local[1:])])]
            west = basis[local[0]].T@np.asarray(values[path[0]])
            east_velocity = basis[local[-1]].T@np.asarray(values[path[-1]])
            western = [west]
            eastern = [east_velocity]
            for i,j in zip(local[:-1],local[1:]):
                western.append(transport(western[-1],rad[i],rad[j]))
            for j,i in zip(local[:0:-1],local[-2::-1]):
                eastern.append(transport(eastern[-1],rad[j],rad[i]))
            eastern.reverse()
            endframe_rel = float(np.linalg.norm(east_velocity-western[-1]))
            for k,p in enumerate(path[1:-1],1):
                f = blend(abscissa[k]/abscissa[-1],kind)
                values[p] = (basis[local[k]]@((1-f)*western[k]+f*eastern[k])).tolist()
            cuts[side] = {"west_to_east_parent_nodes":path,"s_m":abscissa.tolist(),
                          "relative_endpoint_velocity_m_s":endframe_rel,
                          "relative_velocity_over_cut_s_inv":endframe_rel/abscissa[-1],
                          "endpoints_exact":all(values[p]==fixed[p]["south_east_m_s"] for p in (path[0],path[-1]))}
        need(set(values)==set(cycle),"C10_BOUNDARY_INCOMPLETE")
        rhs, matrix, records = [], [], []
        for order,p in enumerate(cycle,1):
            i=parent[p]
            south,eastward=values[p]
            mag,az=angle_mag(south,eastward)
            err=float(np.linalg.norm(decode_native(mag,az)-values[p]))
            need(err<2e-22,"C10_NATIVE_AZIMUTH")
            records.append({"BC_order":order,"parent_node_id":p,"runtime_node_id":i+1,
                            "runtime_lat_lon_deg":ll[i],
                            "source_distal_plate_id":fixed[p]["plate_id"] if p in fixed else None,
                            "source_distal_south_east_m_s":fixed[p]["south_east_m_s"] if p in fixed else None,
                            "generated_south_east_m_s":None if p in fixed else values[p],
                            "prescribed_south_east_m_s":values[p],"ReadBC_code":2,
                            "magnitude_m_s":mag,"azimuth_deg_from_north":az,"native_decode_error_m_s":err})
            for j,x in enumerate(values[p]):
                row=np.zeros(2*len(nodes))
                row[2*i+j]=1.
                matrix.append(row)
                rhs.append(x)
        metrics = []
        for a,b in zip(cycle,cycle[1:]+cycle[:1],strict=True):
            i,j=parent[a],parent[b]
            L=arc(rad[i],rad[j])
            delta=basis[j].T@values[b]-transport(basis[i].T@values[a],rad[i],rad[j])
            tangent=((rad[i]@rad[j])*rad[j]-rad[i])/np.linalg.norm(np.cross(rad[i],rad[j]))
            metrics.append({"parents":[a,b],"side":edge_index[tuple(sorted((a,b)))]["side"],
                            "length_m":L,"relative_speed_m_s":float(np.linalg.norm(delta)),
                            "gradient_norm_s_inv":float(np.linalg.norm(delta)/L),
                            "along_edge_extension_s_inv":float(delta@tangent/L)})
        max_pair=0.
        for i,a in enumerate(cycle):
            ia=parent[a]
            for b in cycle[i+1:]:
                ib=parent[b]
                diff=basis[ib].T@values[b]-transport(basis[ia].T@values[a],rad[ia],rad[ib])
                max_pair=max(max_pair,float(np.linalg.norm(diff)))
        candidates[kind] = {"cuts":cuts,"rows":records,"edge_metrics":metrics,
                            "max_edge_relative_speed_m_s":max(r["relative_speed_m_s"] for r in metrics),
                            "max_pair_relative_speed_m_s":max_pair,
                            "max_edge_gradient_s_inv":max(r["gradient_norm_s_inv"] for r in metrics)}
        rhs_design[kind]=mechanics.rank_details(matrix,rhs,modes)
    sensitivity=max(math.dist(a["prescribed_south_east_m_s"],b["prescribed_south_east_m_s"])
                    for a,b in zip(candidates["linear_arc"]["rows"],candidates[PREFERRED]["rows"],strict=True))
    return {"scenario":SCENARIO,"recommendation":PREFERRED,"frame":previous["frame"],
            "basis":"SOUTH_EAST in the original rotated S1B tangent frame, m/s",
            "candidates":candidates,"max_trace_difference_at_same_node_m_s":sensitivity,
            "interpolation":"Endpoint vectors parallel transported along source cut geodesic edges, blended by linear s or 3s^2-2s^3. Same vectors on common vertices.",
            "localized_case":{"status":"NOT_PROPOSED_UNRESOLVED_LOCALIZATION","minimum_edge_m":min(e["edge_length_m"] for e in edges),
                              "meaning":"C08 10 and 100 km scales do not span even one cut edge. No source-supported wider localization footprint is inferred."},
            "quadrature":{"native":"MOD_SharedVars fPoint/fGauss and MOD_Shells Fixed. Native edge contribution uses fGauss times eLong and side shape functions.",
                          "reaction":"Use conjugate nodal reactions dot imposed velocities. Compare with an independent edge integral of reconstructed traction dot velocity in the consistent tangent frame.",
                          "trace_scope":"C0 at nodes and corners. The analytical cut trace constructs targets. The later FE solve uses native interpolation between these targets."},
            "exterior_A_authority":"Separate mechanically closed validation route. Proposed trace is synthetic and single-valued."},rhs_design


def serialize_bc(rows):
    return SCENARIO+"\n"+"".join(
        f"{r['BC_order']} {r['runtime_node_id']} 2 {r['magnitude_m_s']:.17e} {r['azimuth_deg_from_north']:.17e}\n"
        for r in rows)

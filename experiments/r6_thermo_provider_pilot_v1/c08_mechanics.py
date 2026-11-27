"""Source cut, frame and kinematic constraint design without a mechanical solve."""
from collections import Counter, defaultdict
from itertools import combinations
import re

import numpy as np

from arcana_worldsim.r6.shellset_mesh.coordinates import RUNTIME_FRAME_ID, rotation_matrices
from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.prepare import RADIUS_M, SECONDS_YEAR
from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian
from experiments.r6_thermo_provider_pilot_v1 import run_c07_native_physical_configuration as c07


def rank_details(rows, rhs, modes):
    """Inspect only the algebraic velocity constraints and rigid rotation subspace."""
    matrix = np.asarray(rows)
    u, s, _ = np.linalg.svd(matrix, full_matrices=False)
    tol = max(matrix.shape) * np.finfo(float).eps * s[0]
    rank = int(np.sum(s > tol))
    residual = np.asarray(rhs) - u[:, :rank] @ (u[:, :rank].T @ rhs)
    rigid = matrix @ modes
    rigid_sv = np.linalg.svd(rigid, compute_uv=False)
    rigid_rank = int(np.linalg.matrix_rank(rigid))
    return {
        "variables": matrix.shape[1], "constraint_rows":matrix.shape[0],
        "rank":rank, "unconstrained_dof":matrix.shape[1]-rank,
        "rank_tolerance":float(tol), "constraint_singular_values":s.tolist(),
        "rigid_rotation_modes_constrained":rigid_rank,
        "remaining_rigid_rotation_modes":3-rigid_rank,
        "rotation_singular_values":rigid_sv.tolist(),
        "max_rhs_consistency_residual_m_s":float(np.max(np.abs(residual))),
        "matrix_row_nonzeros":[[[int(i), float(v)] for i,v in enumerate(row) if v] for row in matrix],
        "rhs_m_s":list(rhs), "stiffness_rank":None,
    }


def boundary(index, crosswalk, euler, feg_path, extent_payload, scope):
    mesh = parse_feg(feg_path.read_text(), mode="SHELLS_READY")
    parents = index["original_parent_node_order"]
    local = {p:i for i,p in enumerate(parents)}
    ll = np.asarray([(n.latitude_deg,n.longitude_deg) for n in mesh.nodes])
    rt_xyz, radial, east, north = frames_and_cartesian(ll, RADIUS_M)
    rotation, _ = rotation_matrices()
    canonical = rt_xyz @ rotation
    names = extent_payload["parent_triangle_ids"]
    owner = extent_payload["parent_triangle_plate_ids"]
    actual_edges = defaultdict(list)
    for feg_el, tri, plate in zip(mesh.elements, names, owner, strict=True):
        actual = [parents[x-1] for x in feg_el.node_ids]
        c07.need(actual == index["source_original_full_basal_triangle_nodes"][str(tri)],
                 "C08_TRIANGLE_PARENT_MAPPING")
        for a,b in combinations(actual,2):
            actual_edges[tuple(sorted((a,b)))].append((tri,plate))
    records = []
    for record in index["source_external_cut_edges"]:
        a,b = record["source_parent_node_ids"]
        t,plate = actual_edges[tuple(sorted((a,b)))][0]
        c07.need(actual_edges[tuple(sorted((a,b)))] == [(t,record["adjacent_plate_id"])],
                 "C08_EDGE_AUTHORITY")
        start,end = radial[[local[a],local[b]]]
        length = np.arctan2(np.linalg.norm(np.cross(start,end)), start@end)*RADIUS_M
        records.append({**record,"inner_parent_triangle_id":t,"edge_length_m":float(length),
                        "external_traction_N_per_m":None,"external_velocity_m_s":None})
    c07.need(len(records) == sum(len(faces)==1 for faces in actual_edges.values()) == 32
             and len({r["source_edge_id"] for r in records}) == 32 and not mesh.faults,
             "C08_CUT_INVENTORY")

    omegas = {p["plate_id"]:np.asarray(p["euler_vector_rad_per_year"]) for p in euler["plates"]}
    c07.need(set(omegas) == set(range(12)) and all(v.shape == (3,) and np.all(np.isfinite(v))
             for v in omegas.values()), "C08_EULER_INVENTORY")
    basis = np.stack((-north, east), axis=1)
    speeds = {p:np.einsum("nci,ni->nc", basis,
              np.cross(omega,canonical) @ rotation.T / SECONDS_YEAR) for p,omega in omegas.items()}
    # Unit-radius tangent rigid rotation modes. Scaling leaves the rank unchanged.
    rigid = np.column_stack([np.einsum("nci,ni->nc", basis, np.cross(a,radial)).ravel()
                             for a in np.eye(3)])
    nodal = {}
    rows, rhs = [], []
    for side, plate in (("west",8),("east",5)):
        cut = [r for r in records if r["side"]==side]
        nodes = sorted({p for r in cut for p in r["source_parent_node_ids"]})
        c07.need(len(nodes) == 9 and all(r["adjacent_plate_id"]==plate for r in cut),
                 "C08_DISTAL_PLATE_MISMATCH")
        for parent in nodes:
            i = local[parent]
            c07.need(crosswalk[str(parent)]["native_plate_ids"]==[plate] and
                     str(parent) not in nodal, "C08_SHARED_DISTAL_NODE")
            south,eastward = speeds[plate][i]
            nodal[str(parent)] = {
                "runtime_node_id":i+1, "cut":side,"plate_id":plate,
                "runtime_lat_lon_deg":ll[i].tolist(),
                "canonical_lat_lon_deg":[float(np.degrees(np.arcsin(canonical[i,2]/RADIUS_M))),
                    float(np.degrees(np.arctan2(canonical[i,1],canonical[i,0])))],
                "south_east_m_s":[float(south),float(eastward)], "ReadBC_iCond_candidate":2,
                "magnitude_m_s":float(np.hypot(south,eastward)),
                "azimuth_clockwise_from_north_deg":float(np.degrees(np.arctan2(eastward,-south))%360),
            }
            for j,v in enumerate(speeds[plate][i]):
                row = np.zeros(2*len(parents))
                row[2*i+j] = 1.
                rows.append(row)
                rhs.append(float(v))

    junctions = {}
    for side in ("north","south"):
        endpoints = defaultdict(set)
        for r in records:
            if r["side"] == side:
                for parent in r["source_parent_node_ids"]:
                    endpoints[parent].add(r["adjacent_plate_id"])
        junctions[side] = []
        for parent, plates in endpoints.items():
            if len(plates) > 1:
                i = local[parent]
                jump = speeds[5][i]-speeds[8][i]
                junctions[side].append({"parent":parent,"plate_order":sorted(plates),
                                        "jump_plate5_minus8_south_east_m_s":jump.tolist(),
                                        "jump_norm_m_s":float(np.linalg.norm(jump))})
    # Sidewise C0 discontinuity demonstration, deliberately inconsistent test case.
    dual_rows, dual_rhs = list(rows), list(rhs)
    for side in junctions.values():
        for record in side:
            i = local[record["parent"]]
            for plate in record["plate_order"]:
                for j,v in enumerate(speeds[plate][i]):
                    row = np.zeros(2*len(parents))
                    row[2*i+j] = 1.
                    dual_rows.append(row)
                    dual_rhs.append(float(v))

    contacts = []
    for item in extent_payload["source_contact_edges"]:
        if item["plate_pair"] != [5,8]:
            continue
        a,b = item["source_edge_node_ids"]
        pair = actual_edges[tuple(sorted((a,b)))]
        c07.need(len(pair)==2 and {plate for _,plate in pair}=={5,8}, "C08_CONTACT_OWNERSHIP")
        c = radial[local[a]]+radial[local[b]]
        c /= np.linalg.norm(c)
        conormal = np.cross(radial[local[a]],radial[local[b]])
        conormal /= np.linalg.norm(conormal)
        tri5 = next(tri for tri,plate in pair if plate==5)
        ids = index["source_original_full_basal_triangle_nodes"][str(tri5)]
        if conormal @ np.mean(radial[[local[i] for i in ids]],axis=0) < 0:
            conormal *= -1
        strike = np.cross(c,conormal)
        dv = np.cross(rotation @ (omegas[5]-omegas[8]), RADIUS_M*c)
        contacts.append({**item,"normal_points_into_plate":5,"conormal_runtime_xyz":conormal.tolist(),
                         "strike_runtime_xyz":strike.tolist(),"opening_m_year":float(dv@conormal),
                         "along_contact_m_year":float(dv@strike)})
    c07.need(len(contacts)==extent_payload["source_contact_count"],"C08_CONTACT_COUNT")

    # A named limiting hypothesis prescribes only the local cut-normal Euler
    # component. Great-circle edge conormals are length weighted at corners.
    normals, normal_rhs = [], []
    for parent, node in nodal.items():
        i = local[int(parent)]
        n = sum((np.cross(radial[local[a]],radial[local[b]])
                 for r in records if r["side"] == node["cut"] and
                 int(parent) in r["source_parent_node_ids"]
                 for a,b in [r["source_parent_node_ids"]]), np.zeros(3))
        en = basis[i] @ n
        en /= np.linalg.norm(en)
        if (en[1] > 0) != (node["cut"] == "east"):
            en *= -1
        row = np.zeros(2*len(parents))
        row[2*i:2*i+2] = en
        normals.append(row)
        normal_rhs.append(float(en @ node["south_east_m_s"]))
        node["distal_conormal_south_east"] = en.tolist()
        node["normal_only_value_m_s"] = normal_rhs[-1]
        node["normal_only_ReadBC_iCond_candidate"] = 1

    return (
        {"frame":RUNTIME_FRAME_ID, "rigid_rotation_active_transform":"RX_PLUS_0P5_DEG",
         "Euler_gauge":euler["gauge"]["name"], "distal_component_basis":"SOUTH_EAST_m_s",
         "radius_m":RADIUS_M, "node_order":parents, "edges":records,
         "edge_counts":dict(Counter(r["side"] for r in records)), "distal_node_candidates":nodal,
         "north_south_shared_plate_junctions":junctions,"contact_kinematic_priors":contacts,
         "native_route":"ReadBC code 2 full distal, or code 1 normal only conditional; native unknown north/south loads cannot be encoded as code 0 as a data substitution.",
         "G2_G3_route":"Exterior continuation A architecture has provenance; source traction or a physically closed continuation still needed.",
         "north_south_default":None,"distal_tangential_traction_for_normal_only":None,
         "sided_fault_DOFS":0,"fault_status":"Deferred source sided-contact geometry and law required if shared continuum rejected",
         **scope},
        {"column_order":"source parent order, [south,east]",
         "full_distal_S_and_E": rank_details(rows,rhs,rigid),
         "normal_only_distal_hypothesis":rank_details(normals,normal_rhs,rigid),
         "prohibited_dual_Euler_N_S_counterexample":rank_details(dual_rows,dual_rhs,rigid),
         "interpretation":"Distal full constraints remove all three homogeneous spherical rotations. No extra pin is indicated by this test. This is not stiffness rank or a well-posedness proof.",
         **scope},
    )


def basal_and_density(root, scope):
    src = root/"external/ShellSet-v1.1.0/src"
    interpretations = {
        "MOD_Data.f90":"Legacy OrbData Squeez and data synthesis use stock scalar densities. Keep OrbData synthesis outside the owner-bound PRE path.",
        "MOD_Score.f90":"OrbScore fault/earthquake diagnostics retain stock scalar densities. Exclude from initial native continuum run and qualify independently if enabled.",
        "MOD_SharedVars.f90":"Shared scalar declaration/storage.",
        "MOD_ShellSet.f90":"LR read/validation and variable sweeps; no scalar density override or sweep selected.",
        "MOD_Shells.f90":"Individual branch ownership below.",
        "MOD_VarCheck.f90":"Sweep checks compare scalar crust/mantle density. No automatic override of PRE.",
        "OrbData5.f90":"Stock OrbData call path, outside preserved PRE initialization.",
        "OrbScore2.f90":"Stock scorer call path, excluded from minimum solve.",
        "SHELLS_v5.0.f90":"SHELLS calls Assign, Pure and Result with legacy scalar arrays alongside native context.",
        "ShellSetMain.f90":"Stock orchestration and parameter forwarding. Requires explicitly disabled non-PRE stages for native minimum.",
    }
    matches = {}
    declarations = re.compile(r"(?i)^\s*(?:recursive\s+)?subroutine\s+(\w+)")
    for path in sorted(src.glob("*.f90")):
        routine = None
        locations = []
        for n,line in enumerate(path.read_text(errors="strict").splitlines(), 1):
            if match := declarations.match(line):
                routine = match[1]
            if re.match(r"(?i)^\s*end\s+subroutine", line):
                routine = None
            code = line.split("!",1)[0]
            if re.search(r"(?i)\brhobar(?:_[cm])?\b", code):
                locations.append({"line":n,"routine":routine,"source":code.strip()})
        if locations:
            c07.need(path.name in interpretations, "C08_UNREVIEWED_RHOBAR_FILE")
            matches[path.name] = {"sha256":c07.sha(path),"uses":locations,
                                  "disposition":interpretations[path.name]}
    return {
        "normal_support_Pa":None,"basal_drag_beta_Pa_s_per_m":None,"mechanical_LAB_m":None,"mantle_motion_m_s":None,
        "basal_traction_Pa":None,"zBAsth_m":None,"trHMax_Pa":None,"iConve":None,"pltRef":None,
        "native_controls": {
            "pltRef":"LR plate velocity reference sets iPVRef, not the regional no-net-rotation gauge by itself. Use explicit transformed BC values and reconcile mantle reference.",
            "zBAsth":"Bottom of the adopted basal shear calculation, independent of thermal LAB.",
            "trHMax":"Basal shear cap, participates in pulled/glue and traction logic. Zero suppresses that contribution only under a declared decoupled model.",
            "iConve":"Selects lower mantle velocity prescription. Code 0 denotes zero in Africa-fixed before transform; code 5 requires its own mantle predictor. Neither follows from T0 Euler."
        },
        "conditions_for_decoupled_limit":"Only if explicitly selected as a zero tangential exchange model, with separate normal support and native traction-term audit. It cannot supply missing GPE/normal/cut loading.",
        "coupled_limiting_models":"Zero tangential exchange or tau=beta(v_m-v_l) can be formulated with independent normal support. Coupled drag requires beta, v_m, frame and a mechanical interface.",
        "native_GPE":"Assign S1B integrates ArcanaRuntimeSqueez using source columns and native reference potential. Retain the native load once.",
        "coupled_GPE":"G3 exterior weak-form load separately configured with authorization and duplicate-force check; no additional native Squeez term in that representation.",
        "reactions":"Recover on enforced components from assembled residuals and use force/torque/work audits. They are diagnostics of a closed solve, not prescribed observations.",
        "absolute_pressure_requirement":None,"external_EOS_required_for_native_minimum":False,
        "rhoBar_static_uses":matches,
        "MOD_Shells_data_consumer_review":{
            "Diamnd":"2528/2571/2643 stock fallbacks. S1B uses weighted mean effective density with internal thermal correction.",
            "Assign":"3966/3982 active S1B runtime Squeez; 4086 is stock fallback. Static audit does not establish active configuration.",
            "Fixed":"4656 stock cut-reaction Squeez fallback; active ArcanaRuntimeSqueez at 4632. Code 0 uses the weak-margin normal anomaly, code -1 uses ridge reference. Neither stands in for missing loads.",
            "Mohr":"5901/5979/5980 stock fallbacks from Arcana weighted density. No elements with fault DOFs in this candidate.",
            "Pure":"Forwards scalar values to Viscos and fault/legacy branches.",
            "Result":"7533 stock fallback; 7524 active S1B weighted density.",
            "Squeez":"9392/9416/9446/9451/9490/9494 are the original stock integrator. R6 active callers use ArcanaRuntimeSqueez.",
            "Viscos":"10304/10356 forwarded scalars; Diamnd consumes S1B owner-weighted values in active mode. 10353 stock overburden. Native still uses a pore-pressure model scaled by Biot, which would require approval.",
        },
        "scalar_review_scope":"Static reference audit. Standalone native Shells mode, no OrbData/OrbScore synthesis/scoring, sweep, legacy fallback or sided fault, subject to later runtime verification.",
        **scope,
    }

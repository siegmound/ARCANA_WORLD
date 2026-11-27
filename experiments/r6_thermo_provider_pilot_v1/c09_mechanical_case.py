"""Prepare inspectable regional input fragments and compare the original global route."""
from collections import Counter
from dataclasses import replace
from itertools import combinations
import math

import numpy as np

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg, write_feg
from experiments.plate58_deforming_explore_v1 import prepare as plate
from experiments.r6_thermo_provider_pilot_v1 import run_c08_regional_closure as c08
from experiments.shellset_regional_explore_v1 import build_case


def regional_pre(pre_path, index, extent):
    """Remap only the first PRE field, retaining all 50 authored field tokens."""
    rows = {}
    body = []
    fields = extent["PRE_source_field_order"]
    for local,(line,parent) in enumerate(zip(pre_path.read_text().splitlines()[1:],
                                               index["original_parent_node_order"],strict=True),1):
        key,*vals = line.split()
        c08.need(int(key)==parent,"C09_PRE_OWNER")
        rows[str(parent)] = dict(zip(fields[1:],map(float,vals),strict=True))
        body.append(" ".join([str(local),*vals]))
    count = len(rows)
    header = f"{build_case.MARKER} {build_case.SCHEMA} {count}"
    return rows, "\n".join([header,*body])+"\n"


def regional_loader(source, rows):
    """Bind the existing regional reader's inventory to the authenticated subset."""
    branches = Counter(p["runtime_branch_code"] for p in rows.values())
    c08.need(branches=={1.: len(rows)},"C09_REGIONAL_BRANCHES")
    mixed = sum(p["mixed_support"]==1. for p in rows.values())
    template = build_case.specialize_loader(source,len(rows))
    c08.need(template.count("mixed_count /= 0")==1,"C09_LOADER_INVENTORY_GUARD")
    return template.replace("mixed_count /= 0",f"mixed_count /= {mixed}"), mixed


def time_plan(min_edge, vmax, max_opening_m_year, event_horizon):
    # Explicit provisional truncation-control budgets. No solve-derived
    # estimate of free interior motion is available at this stage.
    allowed_fraction = 1e-4
    width_m = min(plate.WIDTHS_KM)*1000.
    local_bound = allowed_fraction * width_m/max_opening_m_year
    distance_bound = allowed_fraction * min_edge/(2*vmax*plate.SECONDS_YEAR)
    trial = min(1., .5*min(local_bound,distance_bound,event_horizon))
    return {"candidate_trial_year":trial,"accepted_deformation_step_year":None,
            "same_start_halving_year":trial/2, "event_horizon_exclusive_year":event_horizon,
            "relative_geometry_change_proposal":allowed_fraction,
            "min_regional_edge_m":min_edge,"largest_distal_speed_m_s":vmax,
            "max_contact_opening_m_year":max_opening_m_year,
            "smallest_width_sensitivity_m":width_m,"opening_based_provisional_bound_year":local_bound,
            "distal_speed_provisional_bound_year":distance_bound,
            "limitation":"Recompute with actual solved velocities, gradients, thickness flux, event guards and triangle Jacobians. Anchors supply scales only, not a stability guarantee."}


def candidate_package(root, index, extent, pre_text, rows, feg_path, old, model_catalog):
    original = parse_feg(feg_path.read_text(),mode="SHELLS_READY")
    mesh = replace(original,title=build_case.MARKER+" C09 UNSELECTED PHYSICAL PROPOSAL")
    text = write_feg(mesh)
    c08.need(parse_feg(text,mode="SHELLS_READY")==mesh and
             len(mesh.nodes)==81 and len(mesh.elements)==128 and not mesh.faults,
             "C09_REGIONAL_FEG_ROUNDTRIP")
    src = root/build_case.LOADER
    loader, mixed = regional_loader(src.read_text(),rows)
    boundary = old["REGIONAL_BOUNDARY_CONDITION_CANDIDATES.json"]
    distal = boundary["distal_node_candidates"]
    cores = index["original_parent_node_order"]
    local = {parent:i for i,parent in enumerate(cores,1)}
    edges = boundary["edges"]
    cycle = build_case.perimeter(mesh.elements)
    border = {parent for edge in edges for parent in edge["source_parent_node_ids"]}
    c08.need(set(cycle)=={local[p] for p in border},"C09_BC_BORDER_PARENT")
    bc = []
    for node in cycle:
        parent = cores[node-1]
        d = distal.get(str(parent))
        if d:
            c08.need(d["runtime_node_id"]==node,"C09_BC_LOCAL_ID")
        bc.append({"runtime_node_id":node,"parent_node_id":parent,
                   "native_bc_candidate":None if d is None else {
                       "code":2,"magnitude_m_s":d["magnitude_m_s"],
                       "azimuth_deg_from_north":d["azimuth_clockwise_from_north_deg"]},
                   "external_traction_N_per_m":None})
    c08.need(sum(row["native_bc_candidate"] is not None for row in bc)==18,
             "C09_BC_DISTAL")
    baseline = old["AUTHORIAL_PHYSICAL_DECISION_SHEET.json"]["native_initialization"]
    ranks = old["CONSTRAINT_RANK_AND_GAUGE_ANALYSIS.json"]["full_distal_S_and_E"]
    c08.need(ranks["rank"]==36 and ranks["unconstrained_dof"]==126
             and ranks["remaining_rigid_rotation_modes"]==0,"C09_DISTAL_GAUGE")
    full_edges = {tuple(sorted(pair)) for element in mesh.elements for pair in combinations(element.node_ids,2)}
    xyz = plate._unit_vectors(np.asarray([(n.latitude_deg,n.longitude_deg) for n in mesh.nodes]))
    i,j = np.asarray(sorted(full_edges)).T-1
    edge_len = plate.RADIUS_M*np.arctan2(np.linalg.norm(np.cross(xyz[i],xyz[j]),axis=1),
                                        np.einsum("ij,ij->i",xyz[i],xyz[j]))
    clock = time_plan(float(np.min(edge_len)),max(d["magnitude_m_s"] for d in distal.values()),
                     max(d["opening_m_year"] for d in boundary["contact_kinematic_priors"]),
                     boundary["source_pins"]["exclusive_kinematic_upper_bound_model_year"])
    blocked = {
        "constitutive_approval_id":None,
        "pore_pressure_policy_selected":None,
        "outer_north_south_velocity_or_traction_field":None,
        "basal_normal_support_selected":None,
        "mechanical_basal_depth_and_mantle_reference_selected":None,
        "basal_exchange_selected":None,
        "native_LR_numerical_controls_selected":None,
        "native_executable_and_operator_qualification":None,
        "physical_solve_approval":None,
    }
    ids = extent["parent_triangle_ids"]
    mapping = {"nodes":[{"local_id":n.node_id,"parent_id":p,
                         "runtime_lat_lon_deg":[n.latitude_deg,n.longitude_deg]}
                        for n,p in zip(mesh.nodes,cores,strict=True)],
               "elements":[{"local_id":e.element_id,"parent_id":p,
                            "parent_node_ids":[cores[q-1] for q in e.node_ids]}
                           for e,p in zip(mesh.elements,ids,strict=True)]}
    if any(mapping["elements"][i]["parent_node_ids"]!=index["source_original_full_basal_triangle_nodes"][str(p)]
           for i,p in enumerate(ids)):
        raise ValueError("C09_G4_PARENT_ELEMENT_DRIFT")
    package = {
        "status":"NOT_EXECUTABLE","baseline":baseline,
        "suggested_constitutive_scenario":"C09_R_DIORITE2_EFFECTIVE_CONTINUUM",
        "native_parameter_values_unselected":model_catalog["native_diorite2"],
        "conditional_Biot_values":{"hydrostatic":1.,"dry_effective_pressure_equivalent_Biot":0.},
        "continuum_cohesion_Pa":0.,"SI":{"radius_m":plate.RADIUS_M,"oneKm_m":1000.},
        "physics_scope":"Uniform effective continental analogue in scenario design. Source PRE density, temperature and reference ranges stay owner bound.",
        "source_pins":boundary["source_pins"]|{"native_loader_sha256":c08.sha(src)},
        "geometry":{"nodes":len(mesh.nodes),"triangles":len(mesh.elements),"tangent_DOF":162,
                    "faults":0,"outer_edges":len(edges),"mixed_PRE_owner_records":mixed,
                    "multiple_plate_boundary_nodes":15},
        "runtime_mode":"Owner-bound PRE on S1B evaluator; header/manifest use isolated regional cardinality",
        "native_candidate_artifacts":["regional.feg","regional_PRE.dat","MOD_ArcanaRuntime.regional.f90"],
        "BC_records_in_perimeter_order":bc,"BC_observed_rank":ranks,"original_outer_edges":edges,
        "solver_configuration":{
            "target":"Standalone regional SHELLS v5 in ShellSet v1.1.0 source tree, S1B branch",
            "scalar_rhoBar_initializer_candidate_kg_m3":[2800.,3300.],
            "scalar_rhoBar_scope":"Only parser-compatible values for this homogeneous reference-density cardinality. Runtime must prove active weighted PRE ownership.",
            "fault_consumers_disabled_by_zero_feg_faults":True,
            "fFric_Byerly_physical_selection":None,"iConve":None,"trHMax_Pa":None,
            "pltRef":None,"zBAsth_m":None,"maxItr":None,"okToQt":None,
            "refStr_Pa":None,"okDelV_m_s":None,"visMax_Pa_s":None,
            "temLim_K_numeric":baseline["parameters"]["temLim"]["value"],
            "Earth_reference_runtime_controls_transferred":False},
        "frame":boundary["frame"],"GPE_owner":"Native Assign/ArcanaRuntimeSqueez only",
        "time":clock,"required_input_values":blocked,
        "resource_proposal":{
            "models":1,"MPI_ranks_for_review":2,"planned_wall_limit_s":120,
            "aggregate_memory_proposal_bytes":1073741824,
            "basis":"162 tangent unknowns; dense binary64 matrix payload 209952 bytes. Historical 9/8 engineering smoke 0.12s and 10240KiB is precedent only.",
            "limits_verified":False,"scope":"Contingent provisional operator-stage budget; measure actual packed matrix, ABI, process tree and workspace before solve."},
        "G4_mapping":mapping,
        "expected_outputs":{"velocity":"South/east m/s per local node, rotate back to canonical XYZ",
                            "EDot":"Seven points per element, xx yy tensor xy, s^-1",
                            "tauMat":"N/m, with tensor conventions and viscoplastic branch diagnostics",
                            "reactions":"N, force/torque and work; distinguish loads from held-DOF reactions"},
        "G4_before_T1":"Authenticate local IDs with solution_mapping.bind_solution. Update real spherical geometry and material volumes with conservative fluxes; separate reservoir/edge terms. Check orientation, positivity, mass by material, clock and restart. No global HistoryStore write before acceptance.",
        **c08.SCOPE,
    }
    return package, {"regional.feg":text,"regional_PRE.dat":pre_text,"MOD_ArcanaRuntime.regional.f90":loader}


def global_route(root):
    c06 = c08.c07.c06
    _,_,canonical,membership = c06.load_native(root)
    meta = c08.read(root/(build_case.PRE+".json"))
    pre_path = root/(build_case.PRE+".dat")
    c08.pinned(pre_path,meta["runtime_data_sha256"])
    clos = c08.read(root/"R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_CLOSURE.json")
    feg = c08.pinned(root/build_case.FEG,clos["evidence"]["raw_feg_sha256"])
    panel = parse_feg(feg.read_text(),mode="SHELLS_READY")
    c08.need(canonical.normalized_sha256==clos["evidence"]["canonical_mesh_sha256"]
             and len(panel.nodes)==len(canonical.vertices_lat_lon)==meta["node_count"]
             and len(panel.elements)==len(canonical.triangles)
             and all(e.node_ids==tuple(tri) for e,tri in zip(panel.elements,canonical.triangles,strict=True)),
             "C09_GLOBAL_TOPOLOGY_IDENTITY")
    uses = Counter()
    for e in panel.elements:
        uses.update(tuple(sorted(p)) for p in combinations(e.node_ids,2))
    c08.need(set(uses.values())=={2} and set(canonical.triangle_plate_id)==set(range(12))
             and len(panel.nodes)-len(uses)+len(panel.elements)==2,"C09_CLOSED_SPHERE")
    with pre_path.open() as handle:
        header = handle.readline().split()
        count = 0
        branches = Counter()
        domains = Counter()
        mixed = 0
        for count,line in enumerate(handle,1):
            row = line.split()
            c08.need(len(row)==51 and int(row[0])==count,"C09_GLOBAL_PRE_ORDER")
            domains[int(float(row[3]))] += 1
            branches[int(float(row[8]))] += 1
            mixed += float(row[5])==1.
    c08.need(count==int(header[-1])==len(panel.nodes) and
             set(domains)==set(range(1,7)) and len(membership)==64800,"C09_GLOBAL_INVENTORY")
    admitted = sum("ADMITTED_INITIALIZER_SUPPORT" in vals for vals in membership.values())
    ndof = 2*count
    return {"status":"DEFER_GLOBAL_PHYSICAL_CONFIGURATION",
            "node_count":count,"triangle_count":len(panel.elements),"undirected_edges":len(uses),
            "outer_cut_edges":0,"plate_count":12,"source_shared_boundary_edges":len(canonical.boundary_edge_nodes),
            "explicit_native_faults":len(panel.faults),"native_tangent_DOF":ndof,"known_PRE_profiles":count,
            "owner_domain_counts":dict(domains),"mixed_PRE_owner_records":mixed,"PRE_branch_counts":dict(branches),
            "D12_cells_total":len(membership),"D12_admitted_cells":admitted,
            "D12_unadmitted_cells":len(membership)-admitted,
            "D12_scope":"Native thermophysical/material admission masks on cells are distinct from numerical PRE on nodes. Excluded cells stay explicit.",
            "unclosed":"Constitutive regional authority over oceanic and continental classes, explicit sided-contact decisions, gauge, mantle/basal or other driving loads, solver/runtime resources.",
            "global_gauge_proposal":"Area-weighted L2 orthogonality to three rotations in the source canonical frame, with external torque compatibility and actual rank check; native representability not established.",
            "source_FEG_sha256":clos["evidence"]["raw_feg_sha256"],
            "source_PRE_sha256":meta["runtime_data_sha256"],
            "bandwidth_receipt":{"nKRows":2182,"kl":727,"ku":727,
                "conditional_matrix_bytes":8*2182*ndof,
                "conditional_named_arrays_bytes_plus_112_per_LRn_plus_1":2932975900,
                "pre_solver_seconds":282.0919778123498,"pre_solver_returncode":75,
                "solver_measured_wall_s":None,"peak_RSS":None,
                "estimated_factorization_work_order_n_times_kl_squared":ndof*727**2,
                "illustrative_kernel_seconds_if_1_to_10_Gwork_per_s":[ndof*727**2/1e10,ndof*727**2/1e9],
                "timing_estimate_limit":"One unit-coefficient n*kl^2 work proxy divided by assumed rate, excluding bandwidth pivot cost constants, nonlinear repeats, assembly, input and MPI. Actual time remains unknown.",
                "source_report_sha256":c08.sha(root/"docs/arcana/SI1_BW1_F2B_D3C_FAIR_RUNTIME_RESOURCE_RECONNAISSANCE.md"),
                "condition_and_rank":None,
                "evidence":"SI1_BW1_F2B_D3C_FAIR_RUNTIME_RESOURCE_RECONNAISSANCE; historical reordered F2A-V, not a measurement of this ordering/solve.",
                "F2AV":"BLOCKED_F2AV_QUALIFICATION","F2B_solver_authorized":False},
            **c08.SCOPE}

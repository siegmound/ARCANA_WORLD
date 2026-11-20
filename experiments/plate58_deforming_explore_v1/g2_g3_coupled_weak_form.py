"""ARCANA R6 G2/G3 coupled source-owned engineering weak-form assembly.

This module composes existing G2 two-layer viscoplastic (smooth-cap, NOT
fault return mapping), exact PRE vertex quadrature, G3 outer-cut + basal
load FE, and externally owned GPE on one original parent-node EN DOF order.
It NEVER creates a natural load/material law, runs Newton/KKT, or authorizes T1.

The user must explicitly supply every PRE column, per-node *candidate* law,
parent-owned triangle, tractions, GPE source and velocity; gaps remain null.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import numpy as np

from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
    vertex_quadrature_response, validate_column_for_potential,
)
from experiments.plate58_deforming_explore_v1.g2_viscoplastic_explore import (
    potential_gradient_tangent,
)
from experiments.plate58_deforming_explore_v1.g3_force_budget import (
    assemble_explicit_g3_loads,SYNTHETIC_GPE_OWNER,
)
from experiments.plate58_deforming_explore_v1.g3_gpe_force_accounting import (
    compose_candidate_nodal_loads,GPE_OWNER,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    spherical_triangle_geometry,
)
from experiments.plate58_deforming_explore_v1.prepare import RADIUS_M

SCHEMA="ARCANA_R6_G2_G3_COUPLED_EXPLICIT_WEAK_FORM_CANDIDATE_V1"
STATUS="PASS_COUPLED_ENGINEERING_ASSEMBLY__PHYSICAL_SOURCE_AUTHORITY_OPEN"
MODEL_FAMILY="REGIONAL_THIN_LITHOSPHERE_SPHERICAL_P1_FACET_VISCO_PLASTIC_EXPLORE"
SOURCE_TRIANGLE_AUTHORITY="PRE_SOURCE_ONLY_NOT_CONSTITUTIVE_PROJECTION"
CANDIDATE_AUTHORITY="ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED"


class CoupledAssemblyError(ValueError):
    pass


def need(ok,label):
    if not ok:
        raise CoupledAssemblyError(label)


def validate_scope(scope,node_order,triangles,cuts):
    """One noncanonical source regime, or an explicitly synthetic fixture."""
    need(isinstance(scope,Mapping) and
         scope.get("model_family")==MODEL_FAMILY and
         scope.get("physical_source_authority_ratified") is False and
         scope.get("mechanical_solve_authorized") is False,
         "G2_G3_COUPLED_SCOPE_OR_PHYSICAL_AUTHORITY_UNDECLARED")
    label=scope.get("source_scope")
    spec={
        "SOURCE_ORIGINAL_8x8_5_8":(80,120,32),
        "SOURCE_ORIGINAL_16x16_5_8_11":(288,504,64),
    }
    need(label in (*spec,"SYNTHETIC_UNIT_TEST_NOT_ARCANA"),
         "G2_G3_COUPLED_SCOPE_NOT_RECOGNIZED")
    if label in spec:
        need((len(node_order),len(triangles),len(cuts))==spec[label],
             "G2_G3_COUPLED_ORIGINAL_SOURCE_COUNTS_CHANGED")
        need(scope.get("source_triple_parent_node_id")==
             (34587 if label=="SOURCE_ORIGINAL_16x16_5_8_11" else None),
             "G2_G3_COUPLED_ORIGINAL_TRIPLE_NODE_SOURCE_DRIFT")
        # The G3 exterior Schur order excludes the original core-only node.
        # The authentic triple parent ID is not automatically a new G3 DOF.
    else:
        need(scope.get("fixture_only") is True,
             "G2_G3_COUPLED_SYNTHETIC_SOURCE_MUST_BE_MARKED")
    need(scope.get("interface_contact_authority")=="UNQUALIFIED"
         and scope.get("basal_normal_support_authority")=="UNQUALIFIED"
         and scope.get("constitutive_full_fault_law_authority")=="UNQUALIFIED",
         "G2_G3_COUPLED_UNAUTHORIZED_CONTACT_OR_NORMAL_SUPPORT")


def integrate_coupled_candidate(*,scope,node_order,parent_triangle_nodes,
                                source_triangle_bindings,node_lat_lon_deg,
                                source_pre_by_parent_node,
                                candidate_material_by_parent_node,
                                velocity_en_by_parent_node,
                                source_cut_edges,line_tractions_by_edge,
                                basal_tractions_by_triangle,gpe):
    """Return [R(u)=f_internal - f_external, K=dR/du] WITHOUT solving R=0.

    Mechanical dimensions: nodal velocity EN [m/s], internal/external nodal
    force [N], tangent [N s/m], potential [N m/s] and virtual power [W].
    All source IDs and channel owners are validated before evaluating G2/G3.
    """
    ids=list(map(int,node_order))
    need(len(ids)>=4 and len(set(ids))==len(ids) and all(x>0 for x in ids),
         "G2_G3_COUPLED_INVALID_PARENT_NODE_ORDER")
    faces={int(k):tuple(map(int,v))
           for k,v in parent_triangle_nodes.items()}
    bindings={int(k):v for k,v in source_triangle_bindings.items()}
    coords={int(k):np.asarray(v,dtype=float)
            for k,v in node_lat_lon_deg.items()}
    pre={int(k):v for k,v in source_pre_by_parent_node.items()}
    material={int(k):v for k,v in candidate_material_by_parent_node.items()}
    speed={int(k):np.asarray(v,dtype=float)
           for k,v in velocity_en_by_parent_node.items()}
    validate_scope(scope,ids,faces,source_cut_edges)
    need(bool(faces) and set(faces)==set(bindings)
         and all(len(t)==3 and len(set(t))==3
                 and set(t).issubset(ids) for t in faces.values()),
         "G2_G3_COUPLED_SOURCE_FACET_COVERAGE_INVALID")
    need(set(coords)==set(pre)==set(material)==set(speed)==set(ids)
         and all(v.shape==(2,) and np.all(np.isfinite(v))
                 for v in coords.values())
         and all(v.shape==(2,) and np.all(np.isfinite(v))
                 for v in speed.values()),
         "G2_G3_COUPLED_PRE_LAW_COORDINATES_OR_VELOCITY_COVERAGE")
    for pid in ids:
        need(isinstance(pre[pid],Mapping)
             and pre[pid].get("node_id")==pid
             and isinstance(material[pid],Mapping)
             and material[pid].get("authority")==CANDIDATE_AUTHORITY,
             "G2_G3_COUPLED_SOURCE_PRE_OR_MATERIAL_PROVENANCE_INVALID")
        validate_column_for_potential(pre[pid])
    for tid,nodes in faces.items():
        entry=bindings[tid]
        need(isinstance(entry,Mapping)
             and entry.get("parent_triangle_id")==tid
             and tuple(entry.get("parent_node_ids",()))==nodes
             and entry.get("PRE_source_only_not_constitutive_projection") is True
             and entry.get("material_law_by_node") is None
             and list(entry.get("vertex_quadrature_weights",()))==
             [1./3,1./3,1./3],
             "G2_G3_COUPLED_SOURCE_PRE_VERTEX_BINDING_DRIFT")
        if "material_configuration_codes" in entry:
            need(list(entry["material_configuration_codes"])==
                 [pre[n]["material_configuration_code"] for n in nodes],
                 "G2_G3_COUPLED_SOURCE_CONFIGURATION_CODE_DRIFT")

    # G3 exterior + basal source-keyed weak form. Every entry is explicit;
    # absent is an error, zero can only be an *explicit synthetic* value.
    force=assemble_explicit_g3_loads(
        ids,{n:coords[n].tolist() for n in ids},
        source_cut_edges,line_tractions_by_edge,faces,
        basal_tractions_by_triangle,
        gpe_ownership=SYNTHETIC_GPE_OWNER,
        velocity_en_by_node={n:speed[n].tolist() for n in ids})
    # GPE is an EXTERNAL candidate and must not have been added to SHELLS.
    accounting=compose_candidate_nodal_loads(
        force,gpe,node_lat_lon_deg={n:coords[n].tolist() for n in ids},
        numerical_radius_m=RADIUS_M,
        velocity_en_by_node={n:speed[n].tolist() for n in ids})
    need(accounting["source_node_order"]==ids
         and accounting["gpe_exclusive_owner"]==GPE_OWNER
         and accounting["internal_SHELLS_GPE_included"] is False,
         "G2_G3_COUPLED_GPE_OWNER_OR_SOURCE_DOF_DRIFT")

    pos={n:i for i,n in enumerate(ids)}
    internal=np.zeros(2*len(ids),dtype=float)
    tangent=np.zeros((2*len(ids),2*len(ids)),dtype=float)
    energy=0.
    area_total=0.
    for tid,nodes in sorted(faces.items()):
        geom=spherical_triangle_geometry(
            np.stack([coords[n] for n in nodes]))
        B=geom["strain_operator"]
        dofs=[2*pos[n]+j for n in nodes for j in (0,1)]
        nodal_v=np.stack([speed[n] for n in nodes]).ravel()
        strain=B@nodal_v
        state=vertex_quadrature_response(
            bindings[tid],pre,material,strain,
            evaluator=potential_gradient_tangent)
        area=float(geom["facet_area_m2"])
        eforce=area*(B.T@state["stress_resultant_N_per_m"])
        ek=area*(B.T@state["tangent_N_s_per_m"]@B)
        need(np.all(np.isfinite(eforce)) and np.all(np.isfinite(ek))
             and area>0,"G2_G3_COUPLED_NONFINITE_ELEMENT_RESPONSE")
        internal[dofs]+=eforce
        tangent[np.ix_(dofs,dofs)]+=ek
        energy+=area*state["potential_N_per_m_s"]
        area_total+=area
    tangent=.5*(tangent+tangent.T)
    ext=np.asarray(accounting["candidate_total_nodal_force_N"],dtype=float)
    need(ext.shape==internal.shape and np.all(np.isfinite(ext)) and
         np.all(np.isfinite(internal)) and np.all(np.isfinite(tangent))
         and math.isfinite(energy) and energy>=0,
         "G2_G3_COUPLED_GLOBAL_FORCE_TANGENT_INVALID")
    velocity=np.stack([speed[n] for n in ids]).ravel()
    residual=internal-ext
    vwork_internal=float(internal@velocity)
    vwork_ext=float(ext@velocity)
    prior_power=accounting["virtual_power_W_by_channel"]
    need(prior_power is not None
         and math.isclose(vwork_ext,prior_power["total"],
                          rel_tol=1e-12,abs_tol=1e-6)
         and math.isclose(float(residual@velocity),
                          vwork_internal-vwork_ext,
                          rel_tol=1e-12,abs_tol=1e-6),
         "G2_G3_COUPLED_VIRTUAL_WORK_IDENTITY_FAILED")
    need(np.allclose(tangent,tangent.T,rtol=1e-12,atol=0),
         "G2_G3_COUPLED_TANGENT_NOT_SYMMETRIC")
    return {
        "schema":SCHEMA,"status":STATUS,
        "source_scope":scope["source_scope"],
        "source_node_order":ids,
        "source_parent_triangle_count":len(faces),
        "external_cut_count":len(source_cut_edges),
        "source_basal_triangle_count":len(faces),
        "surface_facet_area_sum_m2":area_total,
        "candidate_internal_force_N":internal.tolist(),
        "candidate_external_plus_GPE_force_N":ext.tolist(),
        "candidate_weak_form_residual_N":residual.tolist(),
        "candidate_tangent_N_s_per_m":tangent.tolist(),
        "candidate_dissipation_potential_N_m_per_s":energy,
        "candidate_virtual_power_W":{
            "internal":vwork_internal,
            "external_plus_GPE":vwork_ext,
            "residual":float(residual@velocity),
            "outer_cut":prior_power["outer_cut"],
            "basal_tangential":prior_power["basal_tangential"],
            "gpe_external":prior_power["gpe_external"],
        },
        "candidate_global_external_resultant_xyz_N":
            accounting["resultant_xyz_N_by_channel"],
        "candidate_global_external_torque_xyz_N_m":
            accounting["torque_xyz_N_m_by_channel"],
        "G2_smooth_cap_not_return_mapped_fault":True,
        "PRE_vertex_sampling_not_physical_element_mixing":True,
        "G3_gpe_external_one_owner_only":True,
        "source_solid_contact_gap_available":False,
        "source_fault_traction_law_available":False,
        "full_3D_interface_geometry_available":False,
        "basal_normal_support_qualified":False,
        "physical_rank_and_gauge_qualified":False,
        "force_and_torque_equilibrium_qualified":False,
        "source_material_physical_calibration_qualified":False,
        "material_field_source_ratified":False,
        "physical_mechanical_solve_authorized":False,
        "nonlinear_solver_iterations":0,
        "physical_solver_runs":0,
        "physical_T1":None,
        "D_024":"ACTIVE",
        "HistoryStore_modified":False,
        "canonical_promotion":False,
    }

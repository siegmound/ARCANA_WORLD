"""R6 source-original G2 core plus G3 exterior: single-parent EN weak-form stitch.

The 8 original source core triangles and one core-only node are omitted from
G3 exterior (120/504 triangles). They MUST be assembled exactly once on the
same 8 source interface-node EN pairs, never doubled as fault DOFs.

This is a source-indexed ENGINEERING internal-force/tangent composition only.
An original core basal/GPE/external load provider, complete physical G2
material and a source-qualified fault/interface law remain absent. No R=0 solve.
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
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    spherical_triangle_geometry,
)
from experiments.plate58_deforming_explore_v1.g2_g3_coupled_weak_form import (
    SCHEMA as EXTERIOR_SCHEMA, MODEL_FAMILY,
)

SCHEMA="ARCANA_R6_G2_G3_SOURCE_CORE_EXTERIOR_STITCHED_INTERNAL_WEAK_FORM_V1"
STATUS="PASS_SOURCE_INDEXED_G2_CORE_G3_EXTERIOR_ENGINEERING_STITCH__CORE_LOADS_OPEN"
ENGINEERING="ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED"


class StitchedCandidateError(ValueError):
    pass


def need(value,label):
    if not value:
        raise StitchedCandidateError(label)


def _parent_ids(ids,minimum):
    try:
        result=[int(i) for i in ids]
        need(len(result)>=minimum and len(set(result))==len(result)
             and all(i>0 for i in result),
             "CORE_STITCH_PARENT_ID_DUPLICATE_OR_INVALID")
        return result
    except (TypeError,ValueError) as e:
        raise StitchedCandidateError(
            "CORE_STITCH_PARENT_ID_DUPLICATE_OR_INVALID") from e


def _vector(obj,key,n):
    try:
        v=np.asarray(obj[key],dtype=float)
    except (KeyError,TypeError,ValueError) as ex:
        raise StitchedCandidateError("CORE_STITCH_VECTOR_MISSING:"+key) from ex
    need(v.shape==(2*n,) and bool(np.all(np.isfinite(v))),
         "CORE_STITCH_VECTOR_SHAPE_NONFINITE:"+key)
    return v


def _matrix(obj,key,n):
    try:
        k=np.asarray(obj[key],dtype=float)
    except (KeyError,TypeError,ValueError) as ex:
        raise StitchedCandidateError("CORE_STITCH_MATRIX_MISSING:"+key) from ex
    need(k.shape==(2*n,2*n) and bool(np.all(np.isfinite(k)))
         and bool(np.allclose(k,k.T,rtol=1e-12,atol=1e-8)),
         "CORE_STITCH_TANGENT_SHAPE_SYMMETRY_INVALID:"+key)
    return k


def source_core_contribution(core_node_order,core_triangles,
                             source_core_triangle_bindings,
                             source_pre_by_parent_node,
                             candidate_material_by_parent_node,
                             node_lat_lon_deg,velocity_en_by_parent_node):
    """Assemble only the 8 source original core triangles, no external loads.

    All 9 original core source nodes (8 shared interface+1 core-only) have
    explicit G2 candidate laws and PRE. No synthetic default material.
    """
    ids=_parent_ids(core_node_order,9)
    need(len(ids)==9,"CORE_STITCH_SOURCE_CORE_9_NODES_REQUIRED")
    triangles={int(k):tuple(map(int,v))
               for k,v in core_triangles.items()}
    bindings={int(k):v for k,v in source_core_triangle_bindings.items()}
    need(len(triangles)==8 and set(triangles)==set(bindings)
         and all(len(t)==3 and len(set(t))==3
                 and set(t).issubset(ids) for t in triangles.values())
         and set(n for t in triangles.values() for n in t)==set(ids),
         "CORE_STITCH_SOURCE_8_TRIANGLES_INVALID")
    pre={int(k):v for k,v in source_pre_by_parent_node.items()}
    law={int(k):v for k,v in candidate_material_by_parent_node.items()}
    loc={int(k):np.asarray(v,dtype=float)
         for k,v in node_lat_lon_deg.items()}
    vel={int(k):np.asarray(v,dtype=float)
         for k,v in velocity_en_by_parent_node.items()}
    need(set(pre)==set(law)==set(loc)==set(vel)==set(ids)
         and all(x.shape==(2,) and np.all(np.isfinite(x))
                 for x in list(loc.values())+list(vel.values())),
         "CORE_STITCH_SOURCE_9_NODE_FIELDS_INCOMPLETE")
    for pid in ids:
        need(isinstance(pre[pid],Mapping)
             and pre[pid].get("node_id")==pid
             and isinstance(law[pid],Mapping)
             and law[pid].get("authority")==ENGINEERING,
             "CORE_STITCH_G2_SOURCE_PRE_OR_MATERIAL_AUTHORITY_INVALID")
        validate_column_for_potential(pre[pid])
    positions={pid:i for i,pid in enumerate(ids)}
    fint=np.zeros(2*len(ids))
    kt=np.zeros((2*len(ids),2*len(ids)))
    potential=0.
    area_sum=0.
    for tid,nodes in sorted(triangles.items()):
        binding=bindings[tid]
        need(binding.get("parent_triangle_id")==tid
             and tuple(binding.get("parent_node_ids",()))==nodes
             and binding.get("PRE_source_only_not_constitutive_projection") is True
             and binding.get("material_law_by_node") is None
             and list(binding.get("vertex_quadrature_weights",()))==
                 [1./3]*3,
             "CORE_STITCH_ORIGINAL_TRIANGLE_PRE_BINDING_INVALID")
        if "material_configuration_codes" in binding:
            need(list(binding["material_configuration_codes"])==
                 [pre[n]["material_configuration_code"] for n in nodes],
                 "CORE_STITCH_SOURCE_MATERIAL_CONFIGURATION_CHANGED")
        geo=spherical_triangle_geometry(
            np.stack([loc[n] for n in nodes]))
        B=geo["strain_operator"]
        x=np.stack([vel[n] for n in nodes]).ravel()
        state=vertex_quadrature_response(
            binding,pre,law,B@x,evaluator=potential_gradient_tangent)
        area=float(geo["facet_area_m2"])
        i=[2*positions[n]+c for n in nodes for c in (0,1)]
        fint[i]+=area*B.T@np.asarray(state["stress_resultant_N_per_m"])
        kt[np.ix_(i,i)]+=area*B.T@np.asarray(state["tangent_N_s_per_m"])@B
        potential+=area*state["potential_N_per_m_s"]
        area_sum+=area
    kt=.5*(kt+kt.T)
    u=np.stack([vel[n] for n in ids]).ravel()
    need(np.all(np.isfinite(fint)) and np.all(np.isfinite(kt))
         and math.isfinite(potential) and potential>=0 and area_sum>0,
         "CORE_STITCH_G2_INTERNAL_RESPONSE_NONFINITE")
    return {
        "schema":"ARCANA_R6_SOURCE_CORE_8_TRIANGLE_G2_INTERNAL_CANDIDATE_V1",
        "source_node_order":ids,
        "source_parent_triangle_ids":sorted(triangles),
        "source_triangle_count":8,
        "candidate_internal_force_N":fint.tolist(),
        "candidate_tangent_N_s_per_m":kt.tolist(),
        "candidate_dissipation_potential_N_m_per_s":potential,
        "candidate_internal_virtual_power_W":float(fint@u),
        "source_area_m2":area_sum,
        "core_external_forces_and_GPE_provider_qualified":False,
        "physical_source_material_authorized":False,
        "mechanical_solve_authorized":False,
        "physical_T1":None,
    }


def stitch_source_core_exterior(core,exterior,*,original_parent_node_order,
                                original_core_interface_node_ids,
                                original_core_only_node_id,
                                velocity_en_by_original_parent_node,
                                fixture_only=False):
    """Stitch core+exterior source internal forces, tangent, potential.

    Output known ext loads as PARTIAL contributions, never a global
    physical force balance. The core external load is UNKNOWN, not zero.
    """
    ids=_parent_ids(original_parent_node_order,11 if fixture_only else 81)
    ext_ids=_parent_ids(exterior["source_node_order"],8)
    core_ids=_parent_ids(core["source_node_order"],9)
    shared=_parent_ids(original_core_interface_node_ids,8)
    need(len(shared)==8 and len(core_ids)==9
         and len(set(ids))==len(ids),
         "CORE_STITCH_INTERFACE_SOURCE_NODE_COUNT_INVALID")
    need(exterior.get("schema")==EXTERIOR_SCHEMA
         and exterior.get("physical_solver_runs")==0
         and exterior.get("physical_T1") is None
         and exterior.get("source_solid_contact_gap_available") is False,
         "CORE_STITCH_EXTERIOR_CANDIDATE_INVALID")
    need(core.get("source_triangle_count")==8
         and core.get("mechanical_solve_authorized") is False
         and core.get("physical_T1") is None,
         "CORE_STITCH_CORE_CANDIDATE_INVALID")
    need(tuple(ext_ids[:8])==tuple(shared)
         and set(core_ids).intersection(ext_ids)==set(shared)
         and set(core_ids)-set(shared)=={int(original_core_only_node_id)}
         and set(ext_ids).union(core_ids)==set(ids),
         "CORE_STITCH_SHARED_ORIGINAL_SOURCE_DOF_MISMATCH")
    if not fixture_only:
        scope=exterior.get("source_scope")
        expectations={
            "SOURCE_ORIGINAL_8x8_5_8":(81,80,120),
            "SOURCE_ORIGINAL_16x16_5_8_11":(289,288,504),
        }
        need(scope in expectations and
             (len(ids),len(ext_ids),exterior["source_parent_triangle_count"])==
             expectations[scope],
             "CORE_STITCH_REAL_SOURCE_SCOPE_OR_TRIANGLE_MISMATCH")
    else:
        need(exterior.get("source_scope")=="SYNTHETIC_UNIT_TEST_NOT_ARCANA",
             "CORE_STITCH_SYNTHETIC_FIXTURE_MUST_BE_EXPLICIT")
    speeds={int(k):np.asarray(v,dtype=float)
            for k,v in velocity_en_by_original_parent_node.items()}
    need(set(speeds)==set(ids)
         and all(v.shape==(2,) and np.all(np.isfinite(v))
                 for v in speeds.values()),
         "CORE_STITCH_ORIGINAL_VELOCITY_DOF_INCOMPLETE")
    f_ext_int=_vector(exterior,"candidate_internal_force_N",len(ext_ids))
    f_core_int=_vector(core,"candidate_internal_force_N",len(core_ids))
    f_known=_vector(
        exterior,"candidate_external_plus_GPE_force_N",len(ext_ids))
    R_ext=_vector(exterior,"candidate_weak_form_residual_N",len(ext_ids))
    need(bool(np.allclose(R_ext,f_ext_int-f_known,atol=1e-6,rtol=1e-12)),
         "CORE_STITCH_EXTERIOR_RESIDUAL_HAS_HIDDEN_CHANNEL")
    K_ext=_matrix(exterior,"candidate_tangent_N_s_per_m",len(ext_ids))
    K_core=_matrix(core,"candidate_tangent_N_s_per_m",len(core_ids))
    order={n:i for i,n in enumerate(ids)}
    ng=len(ids)
    f_int=np.zeros(2*ng)
    f_partial=np.zeros(2*ng)
    K=np.zeros((2*ng,2*ng))
    def inject(src,nodes,F,T):
        global_dofs=[2*order[n]+j for n in nodes for j in (0,1)]
        f_int[global_dofs]+=F
        K[np.ix_(global_dofs,global_dofs)]+=T
        return global_dofs
    i_ext=inject("exterior",ext_ids,f_ext_int,K_ext)
    i_core=inject("core",core_ids,f_core_int,K_core)
    f_partial[i_ext]+=f_known
    u=np.stack([speeds[n] for n in ids]).ravel()
    need(math.isclose(
        float(f_core_int@u[i_core]),
        float(core["candidate_internal_virtual_power_W"]),
        rel_tol=1e-12,abs_tol=1e-6),
        "CORE_STITCH_G2_CORE_INTERNAL_VIRTUAL_POWER_MISMATCH")
    need(math.isclose(
        float(f_ext_int@u[i_ext]),
        float(exterior["candidate_virtual_power_W"]["internal"]),
        rel_tol=1e-12,abs_tol=1e-6),
        "CORE_STITCH_G3_EXTERIOR_INTERNAL_VIRTUAL_POWER_MISMATCH")
    need(math.isclose(
        float(f_known@u[i_ext]),
        float(exterior["candidate_virtual_power_W"]["external_plus_GPE"]),
        rel_tol=1e-12,abs_tol=1e-6),
        "CORE_STITCH_G3_KNOWN_EXTERNAL_VIRTUAL_POWER_MISMATCH")
    need(bool(np.allclose(K,K.T,rtol=1e-12,atol=1e-8))
         and np.all(np.isfinite(f_int))
         and np.all(np.isfinite(K)),
         "CORE_STITCH_GLOBAL_INTERNAL_TANGENT_INVALID")
    power_internal=float(f_int@u)
    power_known=float(f_partial@u)
    candidate_partial=f_int-f_partial
    core_potential=float(core["candidate_dissipation_potential_N_m_per_s"])
    ext_potential=float(exterior["candidate_dissipation_potential_N_m_per_s"])
    need(math.isfinite(core_potential) and core_potential>=0
         and math.isfinite(ext_potential) and ext_potential>=0,
         "CORE_STITCH_SOURCE_ENERGY_INVALID")
    return {
        "schema":SCHEMA,
        "status":STATUS,
        "original_parent_node_order":ids,
        "original_source_parent_node_count":ng,
        "source_interface_node_ids":shared,
        "source_core_only_node_id":int(original_core_only_node_id),
        "source_G2_core_triangle_count":8,
        "source_G3_exterior_triangle_count":
            exterior["source_parent_triangle_count"],
        "source_original_full_domain_triangle_count":
            8+exterior["source_parent_triangle_count"],
        "source_original_shared_interface_en_dof_count":16,
        "G2_core_candidate_internal_force_N":f_core_int.tolist(),
        "candidate_whole_domain_internal_force_N":f_int.tolist(),
        "candidate_whole_domain_internal_tangent_N_s_per_m":K.tolist(),
        "candidate_whole_domain_dissipation_potential_N_m_per_s":
            core_potential+ext_potential,
        "known_exterior_external_and_GPE_force_N":f_partial.tolist(),
        "known_PARTIAL_residual_N_NOT_EQUILIBRIUM":candidate_partial.tolist(),
        "candidate_virtual_power_W":{
            "whole_internal":power_internal,
            "known_exterior_external":power_known,
            "PARTIAL_residual":float(candidate_partial@u),
            "G2_core_internal":float(f_core_int@u[i_core]),
            "G3_exterior_internal":float(f_ext_int@u[i_ext]),
        },
        "core_external_and_basal_GPE_physics_qualified":False,
        "full_domain_physical_residual_AVAILABLE":False,
        "full_domain_mechanical_equilibrium_qualified":False,
        "no_duplicate_source_interface_en_dofs":True,
        "no_double_count_of_core_triangles":True,
        "physical_fault_slip_solution_qualified":False,
        "physical_solver_runs":0,
        "physical_T1":None,
        "D_024":"ACTIVE",
        "HistoryStore_modified":False,
        "canonical_promotion":False,
    }

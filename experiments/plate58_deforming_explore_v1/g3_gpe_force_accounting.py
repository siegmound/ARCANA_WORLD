"""G3 A: one-owner *candidate* weak-form force composition, never a physical solve.

Adds source-keyed GPE, explicit outer-cut and basal-tangential P1 nodal loads
on the same original-parent East/North degrees of freedom. No boundary
values, rheology, isostatic support or solver state are inferred here.
"""
from __future__ import annotations

import math
import numpy as np

GPE_OWNER = "EXPERIMENTAL_EXTERNAL_GPE_ONLY__ORIGINAL_SHELLS_GPE_NOT_COMBINED"
NO_INTERNAL_GPE = "NOT_MODELED_IN_SYNTHETIC_KERNEL"
STATUS = "CANDIDATE_G3_A_ONE_OWNER_NODAL_FORCE_ACCOUNTING__PHYSICAL_CLOSURE_OPEN"


class G3AccountingError(ValueError):
    pass


def need(condition, code):
    if not condition:
        raise G3AccountingError(code)


def _nodal_force(row, key, count):
    try:
        arr = np.asarray(row[key], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise G3AccountingError("G3_ACCOUNTING_FORCE_CHANNEL_MISSING") from exc
    need(arr.shape == (count, 2) or arr.shape == (2*count,),
         "G3_ACCOUNTING_DOF_SHAPE_INVALID")
    arr = arr.reshape(count, 2)
    need(bool(np.all(np.isfinite(arr))), "G3_ACCOUNTING_NONFINITE_FORCE")
    return arr


def _frames(node_order, node_lat_lon_deg, radius_m):
    need(isinstance(node_lat_lon_deg, dict), "G3_ACCOUNTING_SOURCE_COORDINATES_MISSING")
    loc = {int(k): v for k, v in node_lat_lon_deg.items()}
    need(set(loc) == set(node_order), "G3_ACCOUNTING_SOURCE_COORDINATES_MISMATCH")
    try:
        ll = np.asarray([loc[n] for n in node_order], dtype=float)
        r = float(radius_m)
    except (TypeError, ValueError) as exc:
        raise G3AccountingError("G3_ACCOUNTING_INVALID_COORDINATES") from exc
    need(ll.shape == (len(node_order), 2) and bool(np.all(np.isfinite(ll)))
         and bool(np.all(np.abs(ll[:, 0]) <= 90.0))
         and math.isfinite(r) and r > 0,
         "G3_ACCOUNTING_INVALID_COORDINATES")
    lat, lon = np.deg2rad(ll).T
    ca, sa = np.cos(lat), np.sin(lat)
    cl, sl = np.cos(lon), np.sin(lon)
    xyz = r*np.column_stack((ca*cl, ca*sl, sa))
    east = np.column_stack((-sl, cl, np.zeros(len(ll))))
    north = np.column_stack((-sa*cl, -sa*sl, ca))
    return xyz, east, north


def compose_candidate_nodal_loads(force_budget, gpe, *,
                                  node_lat_lon_deg, numerical_radius_m,
                                  velocity_en_by_node=None):
    """Account once for GPE in N, torque in N*m and virtual power in W.

    force_budget is from assemble_explicit_g3_loads (external and basal,
    already explicit even if synthetic); gpe must carry the source order
    of the separate g3_gpe_hydrostatic computation and exact external owner.
    Synthetic zero loads are not promoted to physical free boundaries.
    """
    need(isinstance(force_budget, dict) and isinstance(gpe, dict),
         "G3_ACCOUNTING_PAYLOAD_REQUIRED")
    need(force_budget.get("gpe_accounting") == NO_INTERNAL_GPE and
         gpe.get("GPE_force_owner") == GPE_OWNER,
         "G3_ACCOUNTING_GPE_DOUBLE_COUNT_OR_OWNER_UNKNOWN")
    need(force_budget.get("physical_traction_laws_source_qualified") is False
         and force_budget.get("mechanical_solve_authorized") is False
         and force_budget.get("physical_T1") is None
         and gpe.get("mechanical_solve_authorized") is False
         and gpe.get("physical_T1") is None,
         "G3_ACCOUNTING_UNAUTHORIZED_PHYSICAL_PROMOTION")
    try:
        order = list(map(int, force_budget["source_node_order"]))
        gpe_order = list(map(int, gpe["source_interface_node_order"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise G3AccountingError("G3_ACCOUNTING_NODE_ORDER_MISSING") from exc
    need(len(order) >= 3 and all(n > 0 for n in order)
         and len(set(order)) == len(order),
         "G3_ACCOUNTING_DUPLICATED_SOURCE_DOF")
    need(order == gpe_order, "G3_ACCOUNTING_SOURCE_DOF_ORDER_MISMATCH")
    n = len(order)
    f_line = _nodal_force(force_budget,"candidate_external_line_force_N",n)
    f_basal = _nodal_force(force_budget,"candidate_basal_tangential_force_N",n)
    f_base = _nodal_force(force_budget,"candidate_total_nodal_force_N",n)
    f_gpe = _nodal_force(gpe,"candidate_GPE_force_vector_N",n)
    # The force provider must not already contain an implicit GPE channel.
    need(bool(np.allclose(f_base, f_line + f_basal, rtol=1e-12, atol=0.)),
         "G3_ACCOUNTING_FORCE_BUDGET_HAS_HIDDEN_CHANNEL")
    f_total = f_line + f_basal + f_gpe
    xyz, east, north = _frames(order, node_lat_lon_deg, numerical_radius_m)
    def diagnostics(f):
        fxyz = east*f[:, 0, None] + north*f[:, 1, None]
        return np.sum(fxyz, axis=0), np.sum(np.cross(xyz, fxyz), axis=0)
    components = {"outer_cut": f_line, "basal_tangential": f_basal,
                  "gpe_external": f_gpe, "total": f_total}
    forces, torques = {}, {}
    for k, v in components.items():
        forces[k], torques[k] = diagnostics(v)
    need(bool(np.allclose(forces["total"], sum((forces[k] for k in
         ("outer_cut", "basal_tangential", "gpe_external")), np.zeros(3)),
         atol=1e-3, rtol=1e-12)), "G3_ACCOUNTING_FORCE_PARTITION_FAILED")
    power = None
    if velocity_en_by_node is not None:
        need(isinstance(velocity_en_by_node,dict),
             "G3_ACCOUNTING_VELOCITY_SOURCE_INVALID")
        vel = {int(k):v for k,v in velocity_en_by_node.items()}
        need(set(vel) == set(order), "G3_ACCOUNTING_VELOCITY_NODE_COVERAGE")
        try:
            u=np.asarray([vel[n] for n in order],dtype=float)
        except (TypeError, ValueError) as exc:
            raise G3AccountingError("G3_ACCOUNTING_INVALID_VELOCITY") from exc
        need(u.shape == (n,2) and bool(np.all(np.isfinite(u))),
             "G3_ACCOUNTING_INVALID_VELOCITY")
        power={k:float(np.sum(f*u)) for k,f in components.items()}
        need(math.isclose(power["total"], sum(power[k] for k in
             ("outer_cut","basal_tangential","gpe_external")),
             abs_tol=1e-8,rel_tol=1e-12),
             "G3_ACCOUNTING_VIRTUAL_POWER_PARTITION_FAILED")
    return {
        "status": STATUS,
        "source_node_order": order,
        "candidate_external_cut_N":f_line.ravel().tolist(),
        "candidate_basal_tangential_N":f_basal.ravel().tolist(),
        "candidate_external_GPE_N":f_gpe.ravel().tolist(),
        "candidate_total_nodal_force_N":f_total.ravel().tolist(),
        "resultant_xyz_N_by_channel":{k:v.tolist() for k,v in forces.items()},
        "torque_xyz_N_m_by_channel":{k:v.tolist() for k,v in torques.items()},
        "virtual_power_W_by_channel":power,
        "gpe_exclusive_owner":GPE_OWNER,
        "internal_SHELLS_GPE_included":False,
        "basal_normal_support_qualified":False,
        "G2_material_source_qualified":False,
        "G3_physical_boundary_source_qualified":False,
        "force_torque_balance_physical_qualified":False,
        "physical_model_complete":False,
        "mechanical_solve_authorized":False,
        "solver_runs":0,
        "physical_T1":None}

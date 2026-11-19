"""R6 G2/G3 A engineering-only nonlinear depth-integrated membrane.

Uses an explicit *candidate* pair of dislocation-creep laws with distinct
exponents for crust and mantle, authentic-shaped PRE temperature and density
columns, and an incompressible 3D invariant with ezz=-(exx+eyy).

Implements a convex strain-rate potential, its exact gradient and consistent
Newton tangent; assembles them on the existing G3 A spherical-facet P1 B.
No Byerlee/friction or fault failure, real water state, GPE, basal support,
external BC, ShellSet parity, or canonical mechanical evolution is inferred.
"""
from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np

from experiments.plate58_deforming_explore_v1.full_column import (
    R_GAS, bounds, overburden_pa, scalar, temperature_k,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    spherical_triangle_geometry,
)


class ConstitutiveCandidateError(ValueError):
    pass


def require(condition, label):
    if not condition:
        raise ConstitutiveCandidateError(label)


# In-plane strain vector [exx, eyy, gamma_xy=2exy] with
# the incompressible 3D out-of-plane rate ezz=-(exx+eyy).
# epsilon_II^2 = 0.5*epsilon:epsilon = e.T @ Q @ e.
Q_3D_PLANE_STRESS_KINEMATIC = np.array([
    [1.0, 0.5, 0.0], [0.5, 1.0, 0.0], [0.0, 0.0, 0.25],
])


def invariant_rate(strain):
    e = np.asarray(strain, dtype=np.float64)
    require(e.shape == (3,) and np.all(np.isfinite(e)),
            "G2_NONLINEAR_STRAIN_VECTOR_INVALID")
    return float(np.sqrt(e @ Q_3D_PLANE_STRESS_KINEMATIC @ e))


def _layer_nodes(pre, layer, spec):
    integration = spec.get("integration")
    require(isinstance(integration, Mapping), "G2_QUADRATURE_UNSPECIFIED")
    order = integration.get("gauss_points_per_layer")
    require(isinstance(order, int) and 4 <= order <= 64,
            "G2_QUADRATURE_ORDER_UNSUPPORTED")
    a = scalar(pre[f"layer{layer}_z0_m"], "PRE_Z0", nonnegative=True)
    b = scalar(pre[f"layer{layer}_z1_m"], "PRE_Z1", positive=True)
    require(b > a, "G2_PRE_LAYER_DEPTH_INVALID")
    nodes, weights = np.polynomial.legendre.leggauss(order)
    depths = (b+a)/2 + (b-a)*nodes/2
    weights_m = weights*(b-a)/2
    gravity = scalar(spec.get("gravity_m_s2"), "GRAVITY", positive=True)
    temp = temperature_k(pre, layer, depths)
    pressure = overburden_pa(pre, gravity, depths)
    return depths, weights_m, temp, pressure


def _layer_law(spec, name, temperature, pressure, strain_reg):
    require(spec.get("authority") == "ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
            "G2_AUTHORIAL_AUTHORITY_NOT_GRANTED")
    require(isinstance(spec.get("source_identifier"), str)
            and len(spec["source_identifier"].strip()) >= 10,
            "G2_PROVENANCE_MISSING")
    require(isinstance(spec.get("layers"), Mapping)
            and isinstance(spec["layers"].get(name), Mapping),
            "G2_MISSING_CREEP_LAYER")
    # This is a ductile-only operator. A fake brittle law cannot silently pass.
    layer = spec["layers"][name]
    require(layer.get("brittle_mechanical_closure") is None,
            "G2_BRITTLE_CLOSURE_NOT_VALIDATED")
    law = layer.get("ductile")
    require(isinstance(law, Mapping), "G2_CREEP_LAW_MISSING")
    require(law.get("stress_convention") == "ASPECT_2ETA_EPS_INVARIANT_SCALE"
            and isinstance(law.get("source_reference"), str)
            and len(law["source_reference"].strip()) >= 10,
            "G2_CREEP_REFERENCE_OR_INVARIANT_MISSING")
    A = scalar(law.get("A_pa_minus_n_s_inv"), "A", positive=True)
    n = scalar(law.get("n"), "N", positive=True)
    require(n >= 1, "G2_NONCONVEX_POWER_LAW_OUTSIDE_MODEL")
    E = scalar(law.get("E_j_mol"), "E", nonnegative=True)
    V = scalar(law.get("V_m3_mol"), "V", nonnegative=True)
    wr = scalar(law.get("fugacity_exponent"), "WATER_EXPONENT", nonnegative=True)
    if wr > 0:
        water = scalar(law.get("water_fugacity_pa"), "WATER_FUGACITY", positive=True)
        reference = scalar(law.get("reference_fugacity_pa"), "REFERENCE_FUGACITY", positive=True)
        log_a = math.log(A) + wr*math.log(water/reference)
    else:
        require(law.get("water_fugacity_pa") is None
                and law.get("reference_fugacity_pa") is None,
                "G2_UNEXPLAINED_WATER_PARAMETER")
        log_a = math.log(A)
    tmin, tmax = bounds(law, "valid_temperature_k")
    pmin, pmax = bounds(law, "valid_pressure_pa")
    rmin, rmax = bounds(law, "valid_strain_rate_s_inv")
    require(tmin <= np.min(temperature) and np.max(temperature) <= tmax
            and pmin <= np.min(pressure) and np.max(pressure) <= pmax
            and rmin <= strain_reg <= rmax,
            "G2_LAB_VALIDITY_DOMAIN_NOT_COVERED")
    e = 1.0/n
    log_c = (-log_a+(E+pressure*V)/(R_GAS*temperature))/n
    require(np.all(np.isfinite(log_c)) and np.all(log_c < 700)
            and np.all(log_c > -700), "G2_CREEP_STRESS_SCALE_UNREPRESENTABLE")
    return e, np.exp(log_c)


def column_potential_gradient_tangent(pre, spec, strain):
    """Return Phi(e), dPhi/de, d²Phi/de² integrated over crust+mantle.

    Phi is non-negative, convex for n>=1, has units N/(m*s).
    dPhi/de is membrane stress resultant N/m, d²Phi/de² is N*s/m.
    Per-layer exponents n need NOT match; no ShellSet LR file is created.
    """
    e = np.asarray(strain, dtype=np.float64)
    rate = invariant_rate(e)
    require(spec.get("authority") == "ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
            "G2_AUTHORIAL_AUTHORITY_NOT_GRANTED")
    regularization = scalar(spec.get("regularization_strain_rate_s_inv"),
                            "RATE_FLOOR", positive=True)
    reg = math.hypot(rate, regularization)
    require(math.isfinite(reg), "G2_REGULARIZED_RATE_INVALID")
    q = Q_3D_PLANE_STRESS_KINEMATIC
    qe = q@e
    potential = 0.0
    stress = np.zeros(3)
    tangent = np.zeros((3, 3))
    layers = []
    exponents = []
    for which, name in ((1, "crust"), (2, "mantle")):
        _, weights, temp, pressure = _layer_nodes(pre, which, spec)
        ec, coeff = _layer_law(spec, name, temp, pressure, reg)
        exponents.append(ec)
        # At zero strain the regularized potential is exactly zero, stress=0,
        # tangent finite, no implicit strain rate or water assumption.
        fac = float(np.dot(weights, 2.0*coeff))
        reg_power = reg**(ec-1)
        # (reg^(ec+1) - floor^(ec+1)) avoids an arbitrary energy offset.
        relative = (rate/regularization)**2
        delta = regularization**(ec+1)*math.expm1(
            0.5*(ec+1)*math.log1p(relative))
        potential += fac*delta/(ec+1)
        stress += fac*reg_power*qe
        tangent += fac*reg_power*(q + (ec-1)*np.outer(qe, qe)/(reg*reg))
        layers.append({"layer": name,
                       "depth_integrated_creep_scale": fac,
                       "eCreep_in_engineering_operator": ec,
                       "temperature_k_range": [float(temp.min()), float(temp.max())],
                       "pressure_pa_range": [float(pressure.min()), float(pressure.max())]})
    require(np.all(np.isfinite(tangent)) and np.all(np.isfinite(stress))
            and math.isfinite(potential) and potential >= 0,
            "G2_NONLINEAR_ENERGY_OR_TANGENT_INVALID")
    tangent = 0.5*(tangent+tangent.T)
    require(np.min(np.linalg.eigvalsh(tangent)) > 0,
            "G2_NONLINEAR_TANGENT_NOT_POSITIVE_DEFINITE")
    return {"potential_N_per_m_s": potential,
            "stress_resultant_N_per_m": stress,
            "tangent_N_s_per_m": tangent,
            "invariant_strain_rate_s_inv": rate,
            "regularized_strain_rate_s_inv": reg,
            "exponents_by_layer": exponents,
            "different_creep_exponents_supported": True,
            "layer_diagnostics": layers,
            "brittle_failure_implemented": False,
            "water_fugacity_from_PRE": False,
            "ShellSet_nonlinear_tensor_parity": False,
            "physical_G3_forcing": None,
            "mechanical_solve_authorized": False,
            "physical_T1": None}


def spherical_candidate_element(latlon, candidate_velocity_ms, pre, spec):
    """Element internal virtual-force and consistent tangent; no exterior f."""
    g = spherical_triangle_geometry(latlon)
    B = g["strain_operator"]
    vel = np.asarray(candidate_velocity_ms, dtype=np.float64)
    require(vel.shape == (6,) and np.all(np.isfinite(vel)),
            "G3_NONLINEAR_ELEMENT_VELOCITY_INVALID")
    state = column_potential_gradient_tangent(pre, spec, B@vel)
    area = g["facet_area_m2"]
    residual = area*(B.T@state["stress_resultant_N_per_m"])
    tangent = area*(B.T@state["tangent_N_s_per_m"]@B)
    tangent = 0.5*(tangent+tangent.T)
    require(np.all(np.isfinite(residual)) and np.all(np.isfinite(tangent)),
            "G3_NONLINEAR_ELEMENT_RESPONSE_INVALID")
    return {"internal_force_N": residual, "consistent_tangent_N_s_per_m": tangent,
            "dissipation_potential_N_m_per_s": area*state["potential_N_per_m_s"],
            "area_m2": area,"strain_rate_s_inv": state["invariant_strain_rate_s_inv"],
            "layer_exponents": state["exponents_by_layer"],
            "ShellSet_parity": False,
            "brittle_failure_implemented": False,
            "G3_external_force": None,"G3_basal_force": None,
            "mechanical_solve_authorized": False,"physical_T1": None}


def assemble_candidate_exterior(node_order, parent_triangle_nodes,
                                node_lat_lon, velocity_by_node,
                                PRE_column_by_triangle, candidate_by_triangle):
    """Global source-ID keyed internal force and consistent Newton tangent.

    All triangle PRE states and constitutive scenarios are caller-supplied. The
    function refuses missing provenance but does NOT claim any PRE->triangle
    interpolation or real geological calibration has been qualified. No
    boundary force, basal load, Euler constraint, or physical solve is made.
    """
    nodes = list(map(int, node_order))
    faces = {int(t): tuple(map(int, v)) for t, v in parent_triangle_nodes.items()}
    pre = {int(t): state for t, state in PRE_column_by_triangle.items()}
    material = {int(t): state for t, state in candidate_by_triangle.items()}
    loc = {int(n): np.asarray(x, dtype=float) for n, x in node_lat_lon.items()}
    vel = {int(n): np.asarray(x, dtype=float) for n, x in velocity_by_node.items()}
    require(len(nodes) >= 4 and len(set(nodes)) == len(nodes)
            and all(n > 0 for n in nodes), "G3_NONLINEAR_NODE_ID_DUPLICATION")
    require(bool(faces) and set(faces) == set(pre) == set(material)
            and all(len(t) == 3 and len(set(t)) == 3
                    and set(t).issubset(nodes) for t in faces.values()),
            "G3_NONLINEAR_TRIANGLE_INPUT_COVERAGE_INVALID")
    require(set(loc) == set(vel) == set(nodes)
            and all(x.shape == (2,) and np.all(np.isfinite(x))
                    for x in loc.values())
            and all(x.shape == (2,) and np.all(np.isfinite(x))
                    for x in vel.values()),
            "G3_NONLINEAR_NODE_FIELDS_INCOMPLETE")
    for tid in faces:
        require(isinstance(pre[tid], Mapping) and
                pre[tid].get("PRE_projection_provenance") ==
                    "EXPLICIT_TEST_COLUMN_NOT_VALIDATED_FOR_REAL_T0" and
                isinstance(material[tid], Mapping),
                "G3_NONLINEAR_PRE_INTERPOLATION_UNQUALIFIED")
    pos = {n: i for i, n in enumerate(nodes)}
    residual = np.zeros(2*len(nodes))
    tangent = np.zeros((2*len(nodes), 2*len(nodes)))
    energy = 0.0
    count = 0
    for tid, triangle in sorted(faces.items()):
        ll = np.stack([loc[n] for n in triangle])
        vv = np.stack([vel[n] for n in triangle]).ravel()
        state = spherical_candidate_element(ll, vv, pre[tid], material[tid])
        indices = [2*pos[n]+j for n in triangle for j in (0, 1)]
        residual[indices] += state["internal_force_N"]
        tangent[np.ix_(indices,indices)] += state["consistent_tangent_N_s_per_m"]
        energy += state["dissipation_potential_N_m_per_s"]
        count += 1
    tangent = 0.5*(tangent+tangent.T)
    require(np.all(np.isfinite(residual)) and np.all(np.isfinite(tangent))
            and math.isfinite(energy) and energy >= 0,
            "G3_NONLINEAR_GLOBAL_ASSEMBLY_NONFINITE")
    return {
        "global_internal_force_N": residual,
        "global_consistent_tangent_N_s_per_m": tangent,
        "global_dissipation_potential_N_m_per_s": energy,
        "source_node_order": nodes,
        "source_parent_triangle_count": count,
        "PRE_projection_validated_for_real_T0": False,
        "G2_full_brittle_ductile_closed": False,
        "ShellSet_tensor_or_dual_eCreep_parity": False,
        "global_external_and_basal_force_N": None,
        "mechanical_solve_authorized": False,
        "physical_T1": None,
    }

"""Exploratory G3 A exterior membrane weak-form operator, never a physical T1.

Source mesh and parent-plate identity are independently bound by the previous
G3 A interface evidence. Finite-element kernel here uses a *planar* tangent
approximation and explicit per-triangle depth-integrated Newtonian viscosity;
it is NOT the nonlinear ShellSet constitutive tensor or G2 material closure.
"""
from __future__ import annotations

import math
import numpy as np

RADIUS_M = 6_371_000.0


class MechanicalInputError(ValueError):
    pass


def require(ok, msg):
    if not ok:
        raise MechanicalInputError(msg)


def tangent_log_map(lat_lon_deg, center_lat_lon_deg, radius_m=RADIUS_M):
    """Azimuthal equidistant log map in the EAST/NORTH tangent plane, meters."""
    ll = np.asarray(lat_lon_deg, dtype=float)
    center = np.asarray(center_lat_lon_deg, dtype=float)
    require(ll.ndim == 2 and ll.shape[1] == 2 and center.shape == (2,)
            and np.all(np.isfinite(ll)) and np.all(np.isfinite(center))
            and np.all(np.abs(ll[:, 0]) <= 90)
            and abs(center[0]) <= 90 and radius_m > 0,
            "G3_A_TANGENT_MAP_INPUT_INVALID")
    lat,lon = np.deg2rad(ll).T
    phi,lam = np.deg2rad(center)
    xyz = np.column_stack((np.cos(lat)*np.cos(lon),
                           np.cos(lat)*np.sin(lon),np.sin(lat)))
    z = np.array([np.cos(phi)*np.cos(lam),
                  np.cos(phi)*np.sin(lam),np.sin(phi)])
    east = np.array([-np.sin(lam), np.cos(lam), 0.0])
    north = np.array([-np.sin(phi)*np.cos(lam),
                      -np.sin(phi)*np.sin(lam), np.cos(phi)])
    ux,uy = xyz@east, xyz@north
    sin_theta = np.hypot(ux,uy)
    theta = np.arctan2(sin_theta, xyz@z)
    require(np.all(theta < math.pi/2), "G3_A_TANGENT_MAP_HEMISPHERE_VIOLATION")
    fac = np.ones_like(theta)
    np.divide(theta, sin_theta, out=fac, where=sin_theta > 1e-14)
    return radius_m * np.column_stack((ux*fac, uy*fac))


def triangle_B(coords_m):
    """P1 constant strain-rate B, with engineering shear gamma = ux,y+uy,x.

    Returns B shape (3,6), physical planar triangle area in m^2. This is a
    local metric approximation, not exact covariant spherical ShellSet strain.
    """
    xy = np.asarray(coords_m, dtype=float)
    require(xy.shape == (3,2) and np.all(np.isfinite(xy)),
            "G3_A_TRIANGLE_GEOMETRY_INVALID")
    x,y = xy.T
    twice_area = float(np.linalg.det(np.array([
        [x[1]-x[0],y[1]-y[0]],
        [x[2]-x[0],y[2]-y[0]],
    ])))
    # Accept consistent clockwise/anticlockwise FEG orientation, never zero.
    scale = max(float(np.linalg.norm(xy[1]-xy[0]) *
                       np.linalg.norm(xy[2]-xy[0])),1.0)
    require(abs(twice_area) > 1e-14 * scale,
            "G3_A_SINGULAR_OR_UNRESOLVED_TRIANGLE")
    gx = np.array([y[1]-y[2],y[2]-y[0],y[0]-y[1]])/twice_area
    gy = np.array([x[2]-x[1],x[0]-x[2],x[1]-x[0]])/twice_area
    b = np.zeros((3,6))
    b[0,0::2] = gx
    b[1,1::2] = gy
    b[2,0::2] = gy
    b[2,1::2] = gx
    return b,abs(twice_area)*0.5


def integrated_viscosity_tensor(eta_h_pa_s_m, lambda_h_pa_s_m):
    """2D Newtonian membrane D, (Pa s m); sigma resultant = D * strain-rate.

    Lamé-like integrated bulk coefficient lambda_h requires a real material
    model; no incompressible/viscoelastic/nonlinear ShellSet equivalence implied.
    """
    eta,lam=eta_h_pa_s_m,lambda_h_pa_s_m
    require(all(isinstance(v,(int,float,np.floating)) and math.isfinite(v)
                for v in (eta,lam)) and eta>0 and lam>=0,
            "G3_A_MATERIAL_TANGENT_MISSING_OR_INVALID")
    return np.array([[lam+2*eta,lam,0.0],
                     [lam,lam+2*eta,0.0],
                     [0.0,0.0,eta]],dtype=float)


def triangle_viscous_tangent(coords_m, eta_h_pa_s_m, lambda_h_pa_s_m):
    b,area=triangle_B(coords_m)
    d=integrated_viscosity_tensor(eta_h_pa_s_m,lambda_h_pa_s_m)
    k=area*(b.T@d@b)
    require(np.all(np.isfinite(k)), "G3_A_ELEMENT_STIFFNESS_NONFINITE")
    return k,b,area


def assemble_explicit_exterior(node_order, parent_triangle_nodes,
                               tangent_xy_m, element_materials):
    """Assemble physically dimensioned K ONLY from complete explicit inputs.

    The caller supplies every exterior triangle with parent source ID and an
    engineering material provider with eta_h/lambda_h. No defaults, physical
    force vector, boundary state or T1 returned. Intended for controlled
    verification before any physically calibrated G2/G3 ShellSet integration.
    """
    nodes = list(map(int,node_order))
    require(len(nodes)>3 and len(nodes)==len(set(nodes)) and all(i>0 for i in nodes),
            "G3_A_SOURCE_DOF_OWNERSHIP_INVALID")
    triangles={int(t):tuple(map(int,v)) for t,v in parent_triangle_nodes.items()}
    mats={int(t):v for t,v in element_materials.items()}
    require(triangles and set(triangles)==set(mats)
            and all(len(ids)==3 and len(set(ids))==3 and
                    set(ids).issubset(nodes) for ids in triangles.values()),
            "G3_A_SOURCE_TRIANGLE_OR_MATERIAL_COVERAGE_INCOMPLETE")
    coordinates={int(n):np.asarray(x,dtype=float) for n,x in tangent_xy_m.items()}
    require(set(coordinates)==set(nodes)
            and all(x.shape==(2,) and np.all(np.isfinite(x))
                    for x in coordinates.values()),
            "G3_A_SOURCE_NODE_METRIC_INCOMPLETE")
    pos={node:index for index,node in enumerate(nodes)}
    k=np.zeros((2*len(nodes),2*len(nodes)),dtype=float)
    total_area=0.0
    for tid,verts in sorted(triangles.items()):
        material=mats[tid]
        require(isinstance(material,dict)
                and isinstance(material.get("source_reference"),str)
                and len(material["source_reference"].strip())>=10
                and material.get("authority")=="ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
                "G3_A_MATERIAL_PROVENANCE_OR_AUTHORITY_MISSING")
        coords=np.stack([coordinates[i] for i in verts])
        local,b,area=triangle_viscous_tangent(
            coords,material.get("eta_h_pa_s_m"),
            material.get("lambda_h_pa_s_m"))
        dofs=[2*pos[p]+j for p in verts for j in (0,1)]
        k[np.ix_(dofs,dofs)]+=local
        total_area+=area
    require(np.allclose(k,k.T,rtol=2e-13,atol=0)
            and np.all(np.isfinite(k)),
            "G3_A_EXTERIOR_TANGENT_NONRECIPROCAL_OR_NONFINITE")
    return {"tangent":k,"area_m2":total_area,
            "dof_count":len(k),"original_parent_triangle_count":len(triangles),
            "source_node_order":nodes,
            "linear_newtonian_membrane_only":True,
            "shellset_tensor_equivalence":False,
            "spherical_covariant_strain_validated":False,
            "G3_A_real_boundary_tractions":None,
            "G3_A_real_basal_coupling":None,
            "G3_A_physical_force_vector":None,
            "material_authorial_ratification":False,
            "mechanical_solve_authorized":False,
            "physical_T1":None}


def affine_patch_energy(coords, eta_h, lam_h, affine):
    """Manufactured patch identity for an explicit homogeneous triangle.

    v(x,y) = affine[:,0]+affine[:,1:]@[x,y] (m/s).
    """
    xy=np.asarray(coords,dtype=float)
    affine=np.asarray(affine,dtype=float)
    require(affine.shape==(2,3) and np.all(np.isfinite(affine)),
            "G3_A_AFFINE_TEST_INPUT_INVALID")
    v=np.column_stack((np.ones(3),xy))@affine.T
    k,b,area=triangle_viscous_tangent(xy,eta_h,lam_h)
    e=b@v.ravel()
    exact=0.5*area*(e@integrated_viscosity_tensor(eta_h,lam_h)@e)
    energy=0.5*(v.ravel()@k@v.ravel())
    return {"finite_element_energy_N_m_s_inv":float(energy),
            "analytic_linear_field_energy_N_m_s_inv":float(exact),
            "relative_error":float(abs(energy-exact)/max(abs(exact),1e-100))}

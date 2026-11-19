"""Source-linked Earth-analogue GPE hypothesis for ARCANA R6 G3 A.

Uses authentic-shaped PRE densities/thicknesses and FEG elevation, with a
separately stated gravity and common compensation level. Both the elevation's
geological authority and the choice of compensation depth remain UNRATIFIED.
Not equivalent to SHELLS Squeez/Fixed or a complete basal-normal equilibrium.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.prepare import _json, sha, ROOT
from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian
from experiments.plate58_deforming_explore_v1.exterior_variational import triangle_B

STATUS = "CANDIDATE_G3_A_GPE_FROM_AUTHENTIC_T0_COLUMNS__VERTICAL_CLOSURE_UNRESOLVED"
SCENARIO = "EARTH_ANALOGUE_HYDROSTATIC_SOURCE_TEST_NOT_AUTHOR_RATIFIED"
OWNER = "EXPERIMENTAL_EXTERNAL_GPE_ONLY__ORIGINAL_SHELLS_GPE_NOT_COMBINED"


def need(value, tag):
    if not value:
        raise ValueError(tag)


def positive(value, name):
    try:
        x = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError("GPE_INVALID_" + name) from e
    need(math.isfinite(x) and x > 0.0, "GPE_INVALID_" + name)
    return x


def column_hydrostatics(pre, elevation_m, *, gravity_m_s2, reference_elevation_m):
    """Hydrostatic column moment and basal pressure, z measured upward.

    Rocks: crust [h-c,h], mantle lithosphere [h-c-m,h-c].
    Asthenosphere between reference level zref and lithosphere base.
    At h<0 seawater fills [h,0]. No unknown dynamic pressure is inferred.

    GPE moment U = integral rho*g*(z-zref) dz, units J/m2=N/m;
    normal load W = integral rho*g dz, units Pa.
    """
    h = float(elevation_m)
    zr = float(reference_elevation_m)
    need(math.isfinite(h) and math.isfinite(zr), "GPE_ELEVATION_NONFINITE")
    g = positive(gravity_m_s2, "GRAVITY")
    c = positive(pre["crust_thickness_m"], "CRUST_THICKNESS")
    m = positive(pre["mantle_lithosphere_thickness_m"], "MANTLE_THICKNESS")
    rho_c = positive(pre["crust_density_kg_m3"], "CRUST_DENSITY")
    rho_m = positive(pre["mantle_density_kg_m3"], "MANTLE_DENSITY")
    rho_a = positive(pre["rho_asthenosphere_kg_m3"], "ASTHENOSPHERE_DENSITY")
    rho_w = positive(pre["rho_water_kg_m3"], "WATER_DENSITY")
    moho, base = h-c, h-c-m
    need(zr < base, "GPE_REFERENCE_LEVEL_INTERSECTS_LITHOSPHERE")
    water = max(-h, 0.0)
    asth = base-zr
    U = (g/2.0)*(rho_c*((h-zr)**2-(moho-zr)**2)
         + rho_m*((moho-zr)**2-(base-zr)**2)
         + rho_a*(base-zr)**2
         + (rho_w*((-zr)**2-(h-zr)**2) if h < 0 else 0.0))
    W = g*(rho_c*c+rho_m*m+rho_a*asth+rho_w*water)
    need(math.isfinite(U) and math.isfinite(W) and U>0 and W>0,
         "GPE_COLUMN_NONPHYSICAL_OR_NONFINITE")
    return {
        "gpe_J_m2":U,"hydrostatic_normal_pressure_Pa":W,
        "source_elevation_m":h,"surface_water_depth_m":water,
        "moho_elevation_m":moho,"lithosphere_base_elevation_m":base,
        "reference_elevation_m":zr,
        "reference_layer_asthenosphere_thickness_m":asth,
        "physical_isostasy_qualified":False}


def triangle_gpe_gradient_load(lat_lon_deg, three_gpe_J_m2):
    """Piecewise-flat P1 -grad(U) force, local East/North node DOFs.

    This channel is forbidden alongside any duplicate SHELLS Squeez/Fixed
    internal GPE source. Facet gradients are an EXPLORE approximation.
    """
    ll = np.asarray(lat_lon_deg, dtype=float)
    U = np.asarray(three_gpe_J_m2, dtype=float)
    need(ll.shape==(3,2) and U.shape==(3,)
         and np.all(np.isfinite(ll)) and np.all(np.isfinite(U)),
         "GPE_ELEMENT_INPUT_INVALID")
    xyz, radial, east, north = frames_and_cartesian(ll)
    c1,c2 = xyz[1]-xyz[0],xyz[2]-xyz[0]
    norm = np.linalg.norm(np.cross(c1,c2))
    need(norm > 1e-12*np.linalg.norm(c1)*np.linalg.norm(c2),
         "GPE_TRIANGLE_DEGENERATE")
    e1 = c1/np.linalg.norm(c1)
    face = np.cross(c1,c2)/norm
    if np.dot(face,np.mean(radial,axis=0)) < 0:
        face = -face
    e2 = np.cross(face,e1)
    xy = np.column_stack(((xyz-xyz[0])@e1,(xyz-xyz[0])@e2))
    B,area = triangle_B(xy)
    # Only differences are observable. This also prevents roundoff spurious
    # forces from ~1e15 J/m2 constants with much smaller lateral gradients.
    U_relative = U-U[0]
    grad = float(B[0,0::2]@U_relative)*e1 + float(B[1,1::2]@U_relative)*e2
    loads_xyz = np.tile((-area/3.0)*grad,(3,1))
    loads_en = np.column_stack((
        np.einsum("ij,ij->i",loads_xyz,east),
        np.einsum("ij,ij->i",loads_xyz,north)))
    need(np.all(np.isfinite(loads_en)),"GPE_ELEMENT_FORCE_NONFINITE")
    return loads_en,area,grad


def assemble_candidate_gpe(node_order, exterior_triangles, node_lat_lon,
                           node_gpe_J_m2):
    nodes = list(map(int,node_order))
    tris = {int(t):tuple(map(int,v)) for t,v in exterior_triangles.items()}
    need(len(nodes)>=4 and len(set(nodes))==len(nodes) and bool(tris),
         "GPE_SOURCE_INTERFACE_DOF_INVALID")
    loc = {int(k):v for k,v in node_lat_lon.items()}
    vals = {int(k):float(v) for k,v in node_gpe_J_m2.items()}
    need(set(loc)==set(vals)==set(nodes) and
         all(len(t)==3 and len(set(t))==3 and set(t).issubset(nodes)
             for t in tris.values()),"GPE_SOURCE_TRIANGLE_NODE_MISSING")
    pos = {n:i for i,n in enumerate(nodes)}
    f = np.zeros((len(nodes),2))
    total_area = 0.0
    for _,verts in sorted(tris.items()):
        fi,area,_ = triangle_gpe_gradient_load(
            [loc[n] for n in verts],[vals[n] for n in verts])
        for j,n in enumerate(verts):
            f[pos[n]]+=fi[j]
        total_area+=area
    return {
        "candidate_gpe_nodal_force_N":f.ravel(),
        "facet_exterior_area_m2":total_area,
        "node_count":len(nodes),"triangle_count":len(tris),
        "GPE_force_owner":OWNER,
        "SHELLS_Squeez_Fixed_compatibility_qualified":False,
        "vertical_normal_support_qualified":False,
        "mechanical_solve_authorized":False,"physical_T1":None}


def build(multiscale:Path, interface:Path, nodal:Path,
          scenario:Path, output:Path):
    """SHA-bound source+physical-form calculation, never a physical solve."""
    need(not output.exists(),"GPE_OUTPUT_ALREADY_EXISTS")
    policy = json.loads(scenario.read_text())
    need(policy.get("schema") ==
             "ARCANA_R6_G2_G3_HYDROSTATIC_REFERENCE_HYPOTHESIS_V1" and
         policy.get("authority")==SCENARIO and
         policy.get("GPE_force_owner")==OWNER and
         policy.get("FEG_elevation_source_physically_qualified") is False and
         policy.get("physical_solve_authorized") is False,
         "GPE_UNAUTHORIZED_HYPOTHESIS")
    zr = float(policy["reference_elevation_m"])
    g = positive(policy["gravity_m_s2"],"GRAVITY")
    # The source FEG metadata explicitly classifies elevation as derived
    # numerical support, not automatically approved physical paleotopography.
    source_feg_meta_path = ROOT/"R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"
    source_feg_meta = json.loads(source_feg_meta_path.read_text())
    elevation_authority = source_feg_meta["nodal_fields"]["elevation_m"]
    need(elevation_authority["authority"] == "NUMERICAL_DERIVED_SUPPORT"
         and elevation_authority["source_field"]=="total_surface_elevation_m"
         and source_feg_meta["source_authorities"]["surface_closed_package"]["authority"]==
             "GOVERNED_T0_FIELD_NUMERICAL_DERIVED_SUPPORT",
         "GPE_SOURCE_ELEVATION_AUTHORITY_CHANGED")
    gravity_authority=policy.get("gravity_authority_kind")
    if gravity_authority=="CANONICAL_R6_PLANET":
        gravity_reference_path=ROOT/"R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_AUTHORITY.json"
        reference=json.loads(gravity_reference_path.read_text())
        gravity_matches=[item for item in
            reference["existing_authority_audit"]["canonical_planet"]
            if item["quantity"]=="gravity" and
            item["authority"]=="canonical R6"]
        need(len(gravity_matches)==1 and
             math.isclose(g,float(gravity_matches[0]["value"]),
                          rel_tol=0,abs_tol=1e-12),
             "GPE_CANONICAL_GRAVITY_SOURCE_MISMATCH")
    else:
        need(gravity_authority is None,
             "GPE_GRAVITY_AUTHORITY_UNKNOWN")
    sources = []
    for folder,name,status in (
        (multiscale,"CONTINUATION_A.json",
         "PASS_G3_A_MULTISCALE_SOURCE_CONTINUATION__BC_AND_G2_UNRESOLVED"),
        (interface,"MULTISCALE_INTERFACE.json",
         "PASS_G3_A_MULTISCALE_INTERFACE_AND_CONTACT_GRAPH__PHYSICS_UNRESOLVED"),
        (nodal,"SOURCE_NODAL_ELEMENT_G2.json",
         "PASS_G2_SOURCE_NODAL_ELEMENT_BINDING__CONSTITUTIVE_AND_G3_FORCING_OPEN")):
        manifest = json.loads((folder/"MANIFEST.json").read_text())
        record = json.loads((folder/name).read_text())
        need(manifest["status"]==record["status"]==status and
             manifest["no_solver_run"] and manifest["no_T1"] and
             manifest["no_canonical_promotion"] and
             all(sha(folder/k)==v for k,v in manifest["files"].items()),
             "GPE_UPSTREAM_SOURCE_AUTHORITY_FAILED")
        sources.append(record)
    multi,inter,nod = sources
    need(inter["source_multiscale_manifest_sha256"]==
             sha(multiscale/"MANIFEST.json") and
         nod["source_multiscale_manifest_sha256"]==
             sha(multiscale/"MANIFEST.json") and
         nod["source_interface_manifest_sha256"]==
             sha(interface/"MANIFEST.json") and
         nod["source_node_34587_PRE_record"]["node_id"]==34587,
         "GPE_UPSTREAM_SOURCE_LINK_CHANGED")
    regions = {x["cell_extent_per_side"]:x
               for x in multi["topological_comparative_extents"]}
    scales = {x["extent_cells_per_side"]:x for x in inter["scales"]}
    records = {x["extent_cells"]:x for x in nod["scales"]}
    need(set(regions)==set(scales)==set(records)=={8,16},
         "GPE_UPSTREAM_DOMAIN_CHANGED")
    result = []
    for width in (8,16):
        region,scale,record = regions[width],scales[width],records[width]
        feg_file = multiscale/f"OUTER_A_{width:02d}x{width:02d}.feg"
        need(sha(feg_file)==region["output_FEG_sha256"],
             "GPE_SOURCE_FEG_HASH_CHANGED")
        feg = parse_feg(feg_file.read_text(),mode="SHELLS_READY")
        node_ids = region["parent_node_ids"]
        need(len(node_ids)==len(feg.nodes)==record["source_node_count"],
             "GPE_NODE_COUNT_CHANGED")
        pre = {int(k):v for k,v in record["source_PRE_by_parent_node"].items()}
        need(set(node_ids)==set(pre),"GPE_SOURCE_PRE_COLUMNS_MISSING")
        latlon = {pid:(feg.nodes[i].latitude_deg,feg.nodes[i].longitude_deg)
                  for i,pid in enumerate(node_ids)}
        pressure,gpe,height = {},{},{}
        for i,pid in enumerate(node_ids):
            elevation = feg.nodes[i].elevation_m
            row = column_hydrostatics(
                pre[pid],elevation,gravity_m_s2=g,reference_elevation_m=zr)
            pressure[pid]=row["hydrostatic_normal_pressure_Pa"]
            gpe[pid]=row["gpe_J_m2"]
            height[pid]=elevation
        order = scale["mechanical_node_order_interface_first"]
        exterior = {int(t):v["parent_node_ids"]
                    for t,v in record["exterior_triangles"].items()}
        response = assemble_candidate_gpe(
            order,exterior,
            {n:latlon[n] for n in order},
            {n:gpe[n] for n in order})
        pres = np.asarray(list(pressure.values()),dtype=float)
        result.append({
            "extent":width,"node_count":len(node_ids),
            "exterior_triangles":response["triangle_count"],
            "source_elevation_min_max_m":
                [float(min(height.values())),float(max(height.values()))],
            "candidate_normal_pressure_min_max_Pa":
                [float(np.min(pres)),float(np.max(pres))],
            "relative_normal_pressure_spread":
                float((pres.max()-pres.min())/pres.mean()),
            "candidate_GPE_min_max_J_m2":
                [float(min(gpe.values())),float(max(gpe.values()))],
            "candidate_GPE_force_norm_N":
                float(np.linalg.norm(response["candidate_gpe_nodal_force_N"])),
            "candidate_GPE_force_vector_N":
                response["candidate_gpe_nodal_force_N"].tolist(),
            "source_interface_node_order":order,
            "source_3plate_junction_parent_ids":
                [j["parent_node_id"]
                 for j in scale["actual_3plus_plate_junctions"]],
            "reference_normal_pressure_pa":
                policy.get("reference_normal_pressure_pa"),
            "isostatic_normal_balance_verified":False,
            "FEG_elevation_source_physically_qualified":False,
            "physical_force_vector":None})
    need([x["source_3plate_junction_parent_ids"] for x in result]
         ==[[],[34587]],"GPE_TRIPLE_JUNCTION_SOURCE_DRIFT")
    report = {
        "schema":"ARCANA_R6_G3_A_SOURCE_GPE_HYDROSTATIC_HYPOTHESIS_V1",
        "status":STATUS,"scenario_sha256":sha(scenario),
        "source_multiscale_manifest_sha256":sha(multiscale/"MANIFEST.json"),
        "source_interface_manifest_sha256":sha(interface/"MANIFEST.json"),
        "source_g2_binding_manifest_sha256":sha(nodal/"MANIFEST.json"),
        "numerical_radius_m":6371000.0,
        "gravity_m_s2":g,
        "gravity_authority_kind":gravity_authority or "EARTH_ANALOGUE_ONLY",
        "FEG_elevation_source_authority":elevation_authority["authority"],
        "FEG_elevation_source_field":elevation_authority["source_field"],
        "FEG_elevation_metadata_sha256":sha(source_feg_meta_path),
        "assumption":SCENARIO,"scales":result,
        "G2_physical_constitutive_law":None,
        "G3_physical_load_or_normal_support":None,
        "GPE_internal_shellset_parity":False,
        "mechanical_solve_authorized":False,"solver_runs":0,"physical_T1":None}
    output.mkdir(parents=True,exist_ok=False)
    target = output/"GPE_SOURCE_HYPOTHESIS.json"
    target.write_bytes(_json(report))
    (output/"MANIFEST.json").write_bytes(_json({
        "schema":"ARCANA_R6_G3_GPE_SOURCE_HYPOTHESIS_MANIFEST_V1",
        "status":STATUS,"files":{target.name:sha(target)},
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True}))
    return {"status":STATUS,
            "scales":[{"extent":r["extent"],"nodes":r["node_count"],
                       "candidate_GPE_force_norm_N":
                           r["candidate_GPE_force_norm_N"],
                       "source_elevation_min_max_m":
                           r["source_elevation_min_max_m"],
                       "relative_normal_pressure_spread":
                           r["relative_normal_pressure_spread"]}
                      for r in result],
            "mechanical_solve_authorized":False,"solver_runs":0,
            "physical_T1":None}


if __name__=="__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("multiscale","mechanical_interface",
                 "nodal_PRE_binding","scenario_json","output"):
        ap.add_argument(name,type=Path)
    a=ap.parse_args()
    print(json.dumps(build(a.multiscale,a.mechanical_interface,
                           a.nodal_PRE_binding,a.scenario_json,a.output),
                     indent=2))

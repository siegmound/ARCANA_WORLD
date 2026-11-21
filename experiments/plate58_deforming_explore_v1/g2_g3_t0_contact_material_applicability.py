"""R6 scientific T0 contact-side thermal applicability for published lab RSF.

Reopens original FAIR FEG/PRE and SHA-linked nodal records; retains both
original owner faces and original shared parent IDs. Quantifies the exact
crustal 293.15 K isotherm along source nodal thermal polynomials but does
NOT infer actual fault depth, gouge mineralogy, hydration, pore pressure,
normal stress, physical slip-sidedness, or any ARCANA seismicity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.shellset_mesh.feg import parse_feg
from experiments.plate58_deforming_explore_v1.g2_g3_source_coupled_runner import (
    read_pinned, sha,
)
from experiments.plate58_deforming_explore_v1.g2_nodal_source_bridge import (
    parse_regional_pre, validate_column_for_potential,
)
from experiments.plate58_deforming_explore_v1.g2_exact_thermal_validity import (
    exact_layer_temperature_bounds_k,
)
from experiments.plate58_deforming_explore_v1.g2_source_owned_face_topology import (
    source_face_incidence,
)

STATUS = "SOURCE_T0_FAULT_CONTACT_THERMAL_APPLICABILITY_AUDITED__GEOLOGY_AND_SLIP_OPEN"
SCHEMA = "ARCANA_R6_G2_G3_T0_ORIGINAL_CONTACT_THERMAL_MATERIAL_APPLICABILITY_V1"
RSF_SOURCE_SHA = "b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d"
LAB_T_K = 293.15  # published Ikari & Kopf laboratory 20 Celsius; no T-range implied.
SCALES = {8:(81,128,12,(5,8)),16:(289,512,36,(5,8,11))}


class ApplicabilityInputError(ValueError):
    pass


def need(condition, code):
    if not condition:
        raise ApplicabilityInputError(code)


def isotherm_depths_m(pre:dict, *, target_k:float=LAB_T_K) -> list[float] | None:
    """All exact cubic crust roots in original depth coordinate, not fault depth.

    None denotes a whole-layer isotherm with infinitely many possible depths;
    [] denotes no crossing. Scale z to [0,1] to condition the cubic.
    """
    need(math.isfinite(float(target_k)) and float(target_k)>0,
         "T0_CONTACT_TARGET_TEMPERATURE_INVALID")
    z0=float(pre["layer1_z0_m"])
    z1=float(pre["layer1_z1_m"])
    H=z1-z0
    need(math.isfinite(H) and H>0,
         "T0_CONTACT_CRUST_SOURCE_DEPTH_INVALID")
    c=[float(pre[f"layer1_c{i}_{suffix}"]) for i,suffix in
       enumerate(("k","k_m","k_m2","k_m3"))]
    need(all(math.isfinite(v) for v in c),
         "T0_CONTACT_THERMAL_COEFFICIENT_NOT_FINITE")
    coeff=[c[3]*H**3,c[2]*H**2,c[1]*H,c[0]-target_k]
    scale=max(1.,*(abs(x) for x in coeff))
    while len(coeff)>1 and abs(coeff[0])<=1e-14*scale:
        coeff.pop(0)
    if len(coeff)==1:
        return None if abs(coeff[0])<=1e-10*scale else []
    raw=np.roots(coeff)
    depths=[]
    for r in raw:
        if abs(float(r.imag))>1e-9*max(1.,abs(float(r.real))):
            continue
        t=float(r.real)
        if -1e-9<=t<=1.+1e-9:
            t=min(1.,max(0.,t))
            value=c[0]+H*t*(c[1]+H*t*(c[2]+H*t*c[3]))
            need(abs(value-target_k)<1e-5,
                 "T0_CONTACT_POLYNOMIAL_ROOT_RECONSTRUCTION_INVALID")
            z=z0+H*t
            if not any(abs(z-a)<1e-6 for a in depths):
                depths.append(z)
    return sorted(depths)


def survey_contact_face_source(region:dict, pre:dict, faces:list,
                               plates:list, *, width:int) -> dict:
    """Authentic source boundary edge faces + thermal feasibility ONLY."""
    need(width in SCALES,"T0_CONTACT_UNSUPPORTED_REGION_EXTENT")
    nodes=list(map(int,region["parent_node_ids"]))
    expected_nodes,expected_tri,expected_edges,expected_plates=SCALES[width]
    need(len(nodes)==len(set(nodes))==expected_nodes
         and set(nodes)==set(pre)
         and len(faces)==len(plates)==expected_tri
         and set(map(int,plates))==set(expected_plates),
         "T0_CONTACT_ORIGINAL_NODE_TRIANGLE_PLATE_SCOPE_CHANGED")
    source=region["source_contact_edges"]
    need(len(source)==expected_edges and
         region["source_contact_count"]==expected_edges,
         "T0_CONTACT_SOURCE_EDGE_INVENTORY_CHANGED")
    bound=source_face_incidence(faces,plates,source)
    need(len(bound)==expected_edges,
         "T0_CONTACT_TWO_ORIGINAL_FACES_PER_EDGE_REQUIRED")
    records=[]
    all_crossed_depths=[]
    side_full=0
    both_full=0
    isotherm_ambiguous=0
    boundary_ids=set()
    for face_row in bound:
        bid=face_row["source_boundary_id"]
        need(bid not in boundary_ids, "T0_CONTACT_DUPLICATE_BOUNDARY_ID")
        boundary_ids.add(bid)
        edge=list(map(int,face_row["source_edge_node_ids"]))
        pair=list(map(int,face_row["plate_pair"]))
        sides=[]
        for plate,face_key in zip(pair,(
            "plate_p_original_triangle_node_ids",
            "plate_q_original_triangle_node_ids"),strict=True):
            face=list(map(int,face_row[face_key]))
            need(set(edge).issubset(face) and len(face)==3
                 and len(set(face))==3,"T0_CONTACT_SOURCE_FACE_EDGE_CHANGED")
            rows=[]
            for pid in face:
                p=pre[pid]
                validate_column_for_potential(p)
                tmin,tmax=map(float,exact_layer_temperature_bounds_k(p,1))
                z=isotherm_depths_m(p)
                found=(z is None or bool(z))
                if z is None:
                    isotherm_ambiguous+=1
                else:
                    all_crossed_depths.extend(z)
                rows.append({
                    "original_parent_node_id":pid,
                    "source_crust_thickness_m":float(p["crust_thickness_m"]),
                    "source_crust_density_kg_m3":float(p["crust_density_kg_m3"]),
                    "source_surface_temperature_k":float(p["layer1_c0_k"]),
                    "exact_whole_crust_temperature_range_k":[tmin,tmax],
                    "published_lab_293_15_k_within_exact_crust_range":
                        tmin-1e-8<=LAB_T_K<=tmax+1e-8,
                    "isotherm_depths_m_DIAGNOSTIC_NOT_FAULT_DEPTH":z,
                    "isotherm_nonunique_entire_layer":z is None,
                    "isotherm_reached_at_some_crust_depth":found,
                    "source_crust_material_code_NOT_LITHOLOGY":p["crust_material_code"],
                    "source_material_configuration_code_NOT_MINERALOGY":
                        p["material_configuration_code"],
                })
            qualifies=all(r["isotherm_reached_at_some_crust_depth"] for r in rows)
            side_full+=int(qualifies)
            sides.append({
                "plate_id":plate,
                "original_owner_face_parent_node_ids":face,
                "source_face_vertex_records":rows,
                "all_three_source_vertex_columns_have_some_293_15K_crust_depth":
                    qualifies,
                "actual_gouge_mineralogy":None,
                "gouge_hydration_state":None,
                "pore_pressure_pa":None,
                "fault_effective_normal_stress_pa":None,
                "fault_depth_m":None,
                "fault_side_independent_mechanical_dofs":None,
            })
        both=all(s["all_three_source_vertex_columns_have_some_293_15K_crust_depth"]
                 for s in sides)
        both_full+=int(both)
        need(set(sides[0]["original_owner_face_parent_node_ids"])&
             set(sides[1]["original_owner_face_parent_node_ids"])==set(edge),
             "T0_CONTACT_SOURCE_FACES_NOT_EDGE_SHARED")
        records.append({
            "source_boundary_id":bid,
            "source_boundary_parent_edge_ids":edge,
            "source_plate_pair":pair,
            "source_original_faces":[sides[0],sides[1]],
            "both_sides_have_nodewise_crustal_293_15K_isotherm":both,
            "identical_shared_parent_node_PRE_is_not_fault_side_material_identity":True,
            "original_shared_nodes_not_split":True,
            "lab_rate_state_fitted_rows_assigned_to_contact":0,
            "actual_fault_shear_traction_pa":None,
            "physical_contact_force_derived":False,
        })
    node_plate_owners={}
    for face,plate in zip(faces,plates,strict=True):
        for pid in face:
            node_plate_owners.setdefault(pid,set()).add(int(plate))
    triple=(34587 in node_plate_owners and
            len(node_plate_owners[34587])>=3)
    need(triple==(width==16),"T0_CONTACT_TRIPLE_PARENT_3PLATE_INCIDENCE_DRIFT")
    return {
        "extent_cells":width,"source_original_nodes":len(nodes),
        "source_original_facets":len(faces),
        "source_exact_contact_edges":len(records),
        "source_owner_face_sides":sum(len(x["source_original_faces"]) for x in records),
        "source_plate_pairs":sorted({tuple(r["source_plate_pair"]) for r in records}),
        "triple_parent_node_34587_is_3plate_junction":triple,
        "contact_sides_with_nodewise_isotherm":side_full,
        "contacts_with_both_side_nodewise_isotherm":both_full,
        "all_mathematically_crossed_isotherm_depths_min_max_m":
            [min(all_crossed_depths),max(all_crossed_depths)] if all_crossed_depths else None,
        "nonunique_constant_profile_vertex_occurrences":isotherm_ambiguous,
        "source_contacts":records,
        "isotherm_reachability_is_necessary_not_sufficient_for_rsf_law":True,
        "source_PRE_role_codes_cannot_identify_gouge_or_hydration":True,
        "fault_side_source_original_feg_not_a_slip_interface":True,
        "arcana_friction_materials_assigned":0,
        "mechanical_solve_authorized":False,"physical_T1":None,
    }


def _validate_lab_stability_report(folder:Path):
    manifest=json.loads((folder/"MANIFEST.json").read_text())
    report=json.loads((folder/"REPORT.json").read_text())
    need(manifest.get("schema")==
         "ARCANA_R6_G2_G3_NORMALIZED_RSF_STABILITY_MANIFEST_V1"
         and manifest.get("files",{}).get("REPORT.json")==sha(folder/"REPORT.json")
         and manifest.get("source_sha256")==RSF_SOURCE_SHA
         and manifest.get("no_solver_run") is True
         and manifest.get("no_T1") is True
         and manifest.get("no_canonical_promotion") is True
         and report.get("schema")==
         "ARCANA_R6_G2_G3_PANGAEA921284_NORMALIZED_RSF_STABILITY_V1"
         and report.get("source_sha256")==RSF_SOURCE_SHA
         and report.get("mechanical_solve_authorized") is False
         and report.get("physical_T1") is None
         and report.get("inventory",{}).get("fitted_model_rows")==66
         and len(report.get("rows",[]))==66,
         "T0_CONTACT_RSF_PUBLISHED_SOURCE_REPORT_INVALID")
    counts=report["inventory"]["source_row_qualification_counts"]
    need(sum(int(v) for v in counts.values())==66
         and report["inventory"]["pressure_values_assigned"]==0
         and report["inventory"]["arcana_faults_assigned"]==0,
         "T0_CONTACT_RSF_SOURCE_AUTHORITY_PROMOTED")
    return report,sha(folder/"REPORT.json"),sha(folder/"MANIFEST.json")


def build(multiscale:Path,nodal:Path,rsf_stability:Path,out:Path):
    """Source-verified 8+16 contact-side geology feasibility, no mechanical solve."""
    need(not out.exists(),"T0_CONTACT_OUTPUT_EXISTS_NO_OVERWRITE")
    mult,ms=read_pinned("multiscale",multiscale)
    nd,ns=read_pinned("nodal",nodal)
    need(nd["source_multiscale_manifest_sha256"]==ms,
         "T0_CONTACT_NODAL_PARENT_SOURCE_CHAIN_MISMATCH")
    lab,lab_sha,lab_manifest_sha=_validate_lab_stability_report(rsf_stability)
    regions={int(x["cell_extent_per_side"]):x
             for x in mult["topological_comparative_extents"]}
    nodal_regions={int(x["extent_cells"]):x for x in nd["scales"]}
    need(set(regions)==set(nodal_regions)==set(SCALES),
         "T0_CONTACT_REGION_SCALES_CHANGED")
    result=[]
    source_hashes={}
    for width in SCALES:
        r,nscope=regions[width],nodal_regions[width]
        ids=list(map(int,r["parent_node_ids"]))
        feg_path=multiscale/f"OUTER_A_{width:02d}x{width:02d}.feg"
        pre_path=multiscale/f"OUTER_A_{width:02d}x{width:02d}_PRE_T0_PASSIVE.dat"
        need(sha(feg_path)==r["output_FEG_sha256"]
             and sha(pre_path)==r["output_PRE_sha256"]
             and sha(pre_path)==nscope["source_regional_PRE_sha256"],
             "T0_CONTACT_ORIGINAL_FEG_PRE_SHA_DRIFT")
        feg=parse_feg(feg_path.read_text(),mode="SHELLS_READY")
        need(len(feg.nodes)==len(ids) and
             len(feg.elements)==2*width**2,
             "T0_CONTACT_ORIGINAL_FEG_SHAPE_DRIFT")
        pre=parse_regional_pre(pre_path,r["PRE_source_field_order"],ids)
        need({str(k):v for k,v in pre.items()}==
             nscope["source_PRE_by_parent_node"],
             "T0_CONTACT_PRE_NODAL_SOURCE_DRIFT")
        faces=[tuple(ids[int(n)-1] for n in f.node_ids)
               for f in feg.elements]
        result.append(survey_contact_face_source(
            r,pre,faces,list(map(int,r["parent_triangle_plate_ids"])),width=width))
        source_hashes[str(width)]={
            "original_FEG_sha256":sha(feg_path),
            "original_PRE_sha256":sha(pre_path)}
    report={"schema":SCHEMA,"status":STATUS,
        "source_multiscale_manifest_sha256":ms,
        "source_nodal_manifest_sha256":ns,
        "source_lab_stability_report_sha256":lab_sha,
        "source_lab_stability_manifest_sha256":lab_manifest_sha,
        "source_lab_raw_pangaea_sha256":RSF_SOURCE_SHA,
        "source_original_files":source_hashes,
        "lab_earth_fitted_model_rows":lab["inventory"]["fitted_model_rows"],
        "lab_temperature_k":LAB_T_K,
        "lab_effective_normal_pressure_per_experiment":None,
        "lab_wet_gouge_composition_to_arcana":None,
        "exact_original_t0_regions":result,
        "isotherm_means_temperature_possibly_reached_NOT_co_located_fault_physics":True,
        "source_crust_material_codes_NOT_lithology":True,
        "gouge_mineralogy_by_fault":None,"fault_hydration_by_fault":None,
        "fault_depth_by_source_boundary":None,
        "absolute_fault_traction_pa":None,
        "fault_slip_sidedness_authorized":False,
        "rsf_laboratory_fit_to_arcana_assignments":0,
        "mechanical_solve_authorized":False,
        "solver_runs":0,"physical_T1":None,"D_024":"ACTIVE"}
    # Recheck all relevant upstream manifests before materializing evidence.
    need(sha(multiscale/"MANIFEST.json")==ms
         and sha(nodal/"MANIFEST.json")==ns
         and sha(rsf_stability/"MANIFEST.json")==lab_manifest_sha
         and sha(rsf_stability/"REPORT.json")==lab_sha,
         "T0_CONTACT_UPSTREAM_CHANGED_DURING_READ")
    out.mkdir(parents=True,exist_ok=False)
    path=out/"REPORT.json"
    path.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema":"ARCANA_R6_G2_G3_T0_CONTACT_MATERIAL_APPLICABILITY_MANIFEST_V1",
        "status":STATUS,
        "source_multiscale_manifest_sha256":ms,
        "source_nodal_manifest_sha256":ns,
        "source_lab_stability_manifest_sha256":lab_manifest_sha,
        "files":{"REPORT.json":sha(path)},
        "no_physical_solve":True,"no_T1":True,
        "no_canonical_promotion":True,
    },indent=2)+"\n")
    return {"status":STATUS,
            "regions":[{"extent":r["extent_cells"],
                "contact_edges":r["source_exact_contact_edges"],
                "contact_both_sides_thermal_isotherm":
                    r["contacts_with_both_side_nodewise_isotherm"],
                "source_plate_pairs":r["source_plate_pairs"]}
                for r in result],
            "lab_fitted_rows_compatible_in_mechanical_physics":0,
            "source_gouge_mineralogy_bound":False,
            "physical_T1":None,"mechanical_solve_authorized":False}


def discover_fair_sources(root:Path) -> tuple[Path,Path]:
    """Read-only find of SHA-chained multis and nodal providers in FAIR evidence.

    Several byte-identical copies may coexist; different valid provider SHA
    pairs are ambiguous and MUST NOT be selected by file date.
    """
    need(root.is_dir(),"T0_CONTACT_EVIDENCE_ROOT_MISSING")
    multis={}
    for target in sorted(root.rglob("CONTINUATION_A.json")):
        try:
            row,digest=read_pinned("multiscale",target.parent)
        except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
            continue
        if {int(x["cell_extent_per_side"]) for x in
            row.get("topological_comparative_extents",[])}==set(SCALES):
            multis.setdefault(digest,[]).append(target.parent)
    candidates={}
    for target in sorted(root.rglob("SOURCE_NODAL_ELEMENT_G2.json")):
        try:
            row,digest=read_pinned("nodal",target.parent)
        except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
            continue
        parent=row.get("source_multiscale_manifest_sha256")
        if (parent in multis and
            {int(x["extent_cells"]) for x in row.get("scales",[])}==set(SCALES)):
            candidates.setdefault((parent,digest),[]).append(
                (multis[parent][0],target.parent))
    need(len(candidates)==1,"T0_CONTACT_SOURCE_PROVIDER_MISSING_OR_AMBIGUOUS")
    return candidates[next(iter(candidates))][0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",type=Path)
    p.add_argument("--nodal",type=Path)
    p.add_argument("--evidence-root",type=Path,
                   help="Discover one unambiguous SHA-chained pair under FAIR R6")
    p.add_argument("--rsf-stability",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.evidence_root is not None:
        need(a.multiscale is None and a.nodal is None,
             "T0_CONTACT_DISCOVERY_AND_EXPLICIT_PATHS_CONFLICT")
        multiscale,nodal=discover_fair_sources(a.evidence_root)
    else:
        need(a.multiscale is not None and a.nodal is not None,
             "T0_CONTACT_BOTH_EXPLICIT_SOURCE_DIRECTORIES_REQUIRED")
        multiscale,nodal=a.multiscale,a.nodal
    print(json.dumps(build(multiscale,nodal,a.rsf_stability,a.output),indent=2))


if __name__=="__main__":
    main()

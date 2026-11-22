"""ARCANA R6 original-T0 lithostatic *increment* and P/T reference.

Compute gravity-weight overburden increments and true cubic PRE temperature
ranges on every original source node of the FAIR-certified 8x8 and 16x16
regions. This is a noncanonical, *conditional* 1D column balance, NOT a
sourced fault-normal pressure, pore pressure, author-ratified petrology,
three-dimensional mantle traction, GPE/force closure or physical T1.

Pressure zero at the source model surface means DELTA pressure relative to
that surface, NOT assuming actual surface fluid or dynamic pressure is zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from experiments.plate58_deforming_explore_v1.g2_exact_thermal_validity import (
    exact_layer_temperature_bounds_k,
)
from experiments.plate58_deforming_explore_v1.g2_g3_physical_source_packet import (
    content_sha, gitblob, verify_cross_extent_provider_chain,
)
from experiments.plate58_deforming_explore_v1.g2_g3_source_to_coupled_handoff import (
    load_packet, verify_candidate, sha256,
)

SCHEMA = "ARCANA_R6_T0_SOURCE_PRE_LITHOSTATIC_PT_REFERENCE_V1"
STATUS = "ORIGINAL_T0_CONDITIONAL_LITHOSTATIC_PRESSURE_AND_EXACT_THERMAL_PT__NOT_PHYSICAL_STRESS"
SCENARIO_PATH = "experiments/plate58_deforming_explore_v1/G2_G3_PAIRED_PHYSICAL_SCENARIO_V1.json"
SCENARIO_BLOB = "7b182347014747f14ffcd591bdcf4f7f87640e87"
SAMPLE_FRACTIONS = (0., .25, .5, .75, 1.)
EXTENTS = {8: (81, 128, 32), 16: (289, 512, 64)}
HANDOFF_FILES = ("SCENARIO_8X8_UNSELECTED.json", "SCENARIO_16X16_UNSELECTED.json", "AUDIT.json")


class OverburdenInputError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise OverburdenInputError(code)


def positive(value, label):
    require(type(value) in (float, int) and math.isfinite(value) and value > 0,
            "R6_PT_INVALID_POSITIVE:" + label)
    return float(value)


def source_gravity_and_lab(root: Path):
    """Only exact pinned source model; lab T is a temperature-only analogue."""
    raw = (Path(root) / SCENARIO_PATH).read_bytes()
    require(gitblob(raw) == SCENARIO_BLOB, "R6_PT_GRAVITY_AND_LAB_SOURCE_BLOB_DRIFT")
    scenario = json.loads(raw)
    require(scenario.get("schema") == "ARCANA_R6_G2_G3_REGIONAL_PAIRED_PHYSICAL_SCENARIO_V1"
            and scenario.get("selected_model", {}).get("physical_execution_authorized") is False
            and scenario.get("g3", {}).get("gpe", {}).get("gravity_authority") == "CANONICAL_PARAMETER"
            and scenario.get("g2", {}).get("literature_references", {}).get("quartzite_GT95", {}).get("authority") == "LITERATURE_ANALOGUE_EXPERIMENT"
            and scenario["g2"]["literature_references"]["quartzite_GT95"]["arcana_rock_identity_ratified"] is False,
            "R6_PT_SOURCE_MODEL_AUTHORITY_INVALID")
    gravity = positive(scenario["g3"]["gpe"]["gravity_m_s2"], "gravity_m_s2")
    lab = scenario["g2"]["literature_references"]["quartzite_GT95"]
    interval = lab["valid_temperature_k"]
    require(type(interval) is list and len(interval) == 2,
            "R6_PT_LAB_T_INTERVAL_INVALID")
    lo, hi = (positive(v, "lab_temperature_k") for v in interval)
    require(lo < hi and lab["doi"] == "10.1016/0040-1951(95)00011-B",
            "R6_PT_LAB_AUTHORITY_OR_T_RANGE_DRIFT")
    return gravity, (lo, hi), {"scenario_git_blob": SCENARIO_BLOB,
        "gravity_m_s2": gravity, "gravity_authority": "CANONICAL_PARAMETER_IN_PINNED_R6_MODEL",
        "lab_temperature_reference": "GT95_WET_QUARTZITE_TERRESTRIAL_ANALOGUE_T_ONLY",
        "lab_temperature_k": [lo, hi], "lab_doi": lab["doi"],
        "lab_pressure_is_not_certified_as_an_applicability_interval": True,
        "lab_rock_is_not_ARCANA_rock_identity": True}


def _layer(pre, layer):
    prefix = f"layer{layer}_"
    keys = ("z0_m", "z1_m", "c0_k", "c1_k_m", "c2_k_m2", "c3_k_m3")
    require(all(k in pre for k in (prefix + k for k in keys)),
            "R6_PT_LAYER_SOURCE_FIELDS_MISSING")
    values = [pre[prefix + k] for k in keys]
    require(all(type(v) in (int, float) and math.isfinite(v) for v in values),
            "R6_PT_SOURCE_THERMAL_NONFINITE")
    z0,z1,c0,c1,c2,c3 = map(float, values)
    require(z0 >= 0 and z1 > z0 and c0 > 0,
            "R6_PT_SOURCE_LAYER_GEOMETRY_INVALID")
    return z0,z1,c0,c1,c2,c3


def temperature_at_depth_k(pre, layer, z_m):
    z0,z1,c0,c1,c2,c3 = _layer(pre, layer)
    require(type(z_m) in (float,int) and math.isfinite(z_m)
            and z0 <= z_m <= z1, "R6_PT_TEMPERATURE_DEPTH_OUTSIDE_LAYER")
    x = float(z_m) - z0
    value = ((c3*x+c2)*x+c1)*x+c0
    require(math.isfinite(value) and value > 0,
            "R6_PT_TEMPERATURE_INVALID")
    return value


def overburden_increment_pa(pre, depth_m, gravity_m_s2):
    """Exact d(sigma_v)/dz=rho*g in the two-layer PRE column.

    Delta is referenced to z=0 at source surface, with physical surface
    load UNKNOWN. Do not use as effective normal stress or true fault load.
    """
    g = positive(gravity_m_s2, "g")
    c = positive(pre.get("crust_thickness_m"), "H_crust_m")
    m = positive(pre.get("mantle_lithosphere_thickness_m"), "H_mantle_m")
    rho_c = positive(pre.get("crust_density_kg_m3"), "rho_crust")
    rho_m = positive(pre.get("mantle_density_kg_m3"), "rho_mantle")
    require(type(depth_m) in (float,int) and math.isfinite(depth_m)
            and 0 <= depth_m <= c+m, "R6_PT_DEPTH_OUTSIDE_SOURCE_COLUMN")
    z = float(depth_m)
    result = g*(rho_c*min(z,c)+rho_m*max(z-c,0.))
    require(math.isfinite(result) and result >= 0,
            "R6_PT_OVERBURDEN_NONFINITE")
    return result


def _column_structure(pre,gravity):
    c = positive(pre.get("crust_thickness_m"), "crust_thickness_m")
    m = positive(pre.get("mantle_lithosphere_thickness_m"), "mantle_lithosphere_thickness_m")
    rho_c = positive(pre.get("crust_density_kg_m3"), "crust_density_kg_m3")
    rho_m = positive(pre.get("mantle_density_kg_m3"), "mantle_density_kg_m3")
    z1 = _layer(pre, 1)
    z2 = _layer(pre, 2)
    require(abs(z1[0]) < 1e-6 and abs(z1[1]-c) < 1e-5
            and abs(z2[0]-c) < 1e-5 and abs(z2[1]-c-m) < 1e-5,
            "R6_PT_SOURCE_LAYER_BOUNDARIES_DO_NOT_MATCH_DENSITY")
    moho = gravity * rho_c * c
    base = moho + gravity * rho_m * m
    # Integral_0^(c+m) Delta_sigma_v(z) dz [Pa*m = N/m].
    integrated = gravity*(.5*rho_c*c*c + rho_c*c*m + .5*rho_m*m*m)
    # Independent piecewise pressure integration check via endpoints.
    independent = .5*c*moho + .5*m*(moho+base)
    require(math.isfinite(integrated) and integrated > 0
            and math.isclose(integrated, independent, rel_tol=2e-14),
            "R6_PT_HYDROSTATIC_PRESSURE_INTEGRAL_NOT_CONSERVED")
    return c,m,rho_c,rho_m,moho,base,integrated


def evaluate_node(pre, *, gravity_m_s2, lab_temperature_k):
    """Actual original PRE 2-layer material-density weight, no P0 assumption."""
    c,m,rc,rm,moho,base,integrated = _column_structure(pre,gravity_m_s2)
    require(type(lab_temperature_k) in (list,tuple) and len(lab_temperature_k)==2,
            "R6_PT_LAB_WINDOW_INVALID")
    low,high = map(lambda n:positive(n,"lab_temperature"),lab_temperature_k)
    require(low<high, "R6_PT_LAB_WINDOW_ORDER_INVALID")
    samples=[]
    layer_ranges={}
    lab_check={}
    for layer, thickness in ((1,c),(2,m)):
        z0, z1, *_ = _layer(pre,layer)
        try:
            tmin,tmax=exact_layer_temperature_bounds_k(pre,layer)
        except (ValueError,ArithmeticError,FloatingPointError) as exc:
            raise OverburdenInputError("R6_PT_EXACT_SOURCE_TEMPERATURE_INVALID") from exc
        require(math.isfinite(tmin) and math.isfinite(tmax) and tmin>0 and tmax>=tmin,
                "R6_PT_EXACT_T_RANGE_NONPHYSICAL")
        name="crust" if layer==1 else "mantle_lithosphere"
        layer_ranges[name]=[tmin,tmax]
        lab_check[name]={
            "temperature_only_full_layer_covered": bool(low<=tmin and tmax<=high),
            "temperature_only_some_overlap": bool(tmin<=high and tmax>=low),
            "mechanism_applicable_to_ARCANA": False,
            "P_rate_water_rock_identity_qualified": False,
        }
        for f in SAMPLE_FRACTIONS:
            depth=z0+(z1-z0)*f
            samples.append({
                "layer":name, "fraction_of_layer":f, "source_depth_m":depth,
                "source_PRE_temperature_k":temperature_at_depth_k(pre,layer,depth),
                "conditional_delta_vertical_overburden_pa":
                    overburden_increment_pa(pre,depth,gravity_m_s2),
                "source_depth_is_not_actual_fault_depth":True,
            })
    crust_moho_T=temperature_at_depth_k(pre,1,c)
    mantle_moho_T=temperature_at_depth_k(pre,2,c)
    return {
        "source_crust_thickness_m":c, "source_lithospheric_mantle_thickness_m":m,
        "source_crust_density_kg_m3":rc,"source_lithospheric_mantle_density_kg_m3":rm,
        "source_model_moho_depth_m":c,
        "source_model_base_depth_m":c+m,
        "conditional_moho_delta_overburden_pa":moho,
        "conditional_base_delta_overburden_pa":base,
        "integrated_delta_overburden_N_per_m":integrated,
        "source_temperature_jump_at_moho_mantle_minus_crust_k":mantle_moho_T-crust_moho_T,
        "exact_PRE_temperature_bounds_k":layer_ranges,
        "terrestrial_GT95_lab_temperature_only_coverage":lab_check,
        "source_depth_pt_samples":samples,
        "absolute_surface_pressure_pa":None,
        "pore_pressure_pa":None,
        "effective_pressure_pa":None,
        "fault_normal_pressure_pa":None,
        "actual_vertical_stress_pa":None,
        "mechanical_LAB_depth_m":None,
        "mantle_traction_pa":None,
        "constitutive_law_assigned":False,
        "GPE_owner_authorized":False,
    }


def compute_region(index, proposal, receipt, *, extent, gravity_m_s2,lab_temperature_k):
    """Numerical T0 reference on every *exact original source parent node*."""
    require(index.get("extent_cells")==extent and extent in EXTENTS,
            "R6_PT_REGION_SCOPE_INVALID")
    count, facets, cuts=EXTENTS[extent]
    ids=index["original_parent_node_order"]
    profiles=index["source_original_PRE_model_T0_thermal_profiles_by_parent_node"]
    require(type(ids) is list and len(ids)==count and len(set(ids))==count
            and set(profiles)=={str(n) for n in ids}
            and index["counts"]["source_original_full_basal_triangles"]==facets
            and index["counts"]["original_external_cut_edges"]==cuts,
            "R6_PT_ORIGINAL_SOURCE_COVERAGE_INVALID")
    require(proposal.get("physical_T1") is None
            and proposal.get("input_gaps_are_UNKNOWN_not_zero") is True
            and index.get("physical_T1") is None
            and index.get("D_024")=="ACTIVE"
            and len(proposal["remaining_physical_groups"])==8,
            "R6_PT_UNSELECTED_AUTHORITY_CHANGED")
    nodes={}
    for n in ids:
        nodes[str(n)]=evaluate_node(
            profiles[str(n)],gravity_m_s2=gravity_m_s2,
            lab_temperature_k=lab_temperature_k)
    c_pressure=[x["conditional_moho_delta_overburden_pa"] for x in nodes.values()]
    b_pressure=[x["conditional_base_delta_overburden_pa"] for x in nodes.values()]
    crust_temperature=[x["exact_PRE_temperature_bounds_k"]["crust"] for x in nodes.values()]
    coverage={key:sum(int(x["terrestrial_GT95_lab_temperature_only_coverage"]["crust"][key])
                      for x in nodes.values())
              for key in ("temperature_only_some_overlap","temperature_only_full_layer_covered")}
    require(all(b>=m>0 for b,m in zip(b_pressure,c_pressure,strict=True))
            and coverage["temperature_only_full_layer_covered"]<=coverage["temperature_only_some_overlap"]<=count,
            "R6_PT_REGIONAL_PRESSURE_OR_LAB_COUNTS_INVALID")
    return {
        "schema":SCHEMA,"status":STATUS,"authority":"SOURCE_PRE_MODEL_PLUS_CONDITIONAL_1D_HYDROSTATICS_NOT_GEOLOGICAL_RATIFICATION",
        "epoch":"T0_210_Ma","extent_cells":extent,
        "source_packet_manifest_sha256":receipt["evidence_manifest_sha256"],
        "source_packet_index_file_sha256":receipt["source_index_sha256"],
        "source_index_content_sha256":content_sha(index),
        "original_parent_node_order":ids,
        "source_original_FEG_sha256":index["source_hashes"]["original_FEG_sha256"],
        "source_original_PRE_sha256":index["source_hashes"]["original_PRE_sha256"],
        "source_four_manifest_SHA256":{
            k:index["source_hashes"][k+"_manifest_sha256"]
            for k in ("multiscale","interface","nodal","force")},
        "source_node_count":count,"source_full_basal_facet_count":facets,
        "source_external_cut_edge_count":cuts,
        "summary":{
            "conditional_moho_delta_overburden_pa_min_max":[min(c_pressure),max(c_pressure)],
            "conditional_base_delta_overburden_pa_min_max":[min(b_pressure),max(b_pressure)],
            "exact_source_crust_temperature_min_max_k":[
                min(x[0] for x in crust_temperature),max(x[1] for x in crust_temperature)],
            "terrestrial_GT95_temperature_only_crust_nodes":coverage,
            "GT95_arcana_rock_assignments":0,
            "qualified_fault_normal_pressure_points":0,
            "qualified_basal_traction_facets":0,
        },
        "original_T0_source_nodes":nodes,
        "pressure_reference_is_delta_from_model_surface_not_absolute":True,
        "hydrostatic_assumption_constant_layer_density_and_g":True,
        "no_seawater_overburden_or_elevation_load_fabricated":True,
        "no_fault_depth_or_normal_pressure_inferred":True,
        "no_GPE_or_mantle_coupling_generated":True,
        "conditional_overburden_not_mechanical_vertical_traction":True,
        "real_lithology_water_and_P_T_rate_law_unassigned":True,
        "remaining_physical_groups":list(proposal["remaining_physical_groups"]),
        "mechanical_solve_authorized":False,"physical_T1":None,
        "HistoryStore_modified":False,"D_024":"ACTIVE",
        "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False,
    }


def _load_handoff(handoff_folder, index8, index16, receipt8, receipt16):
    folder=Path(handoff_folder)
    m=json.loads((folder/"MANIFEST.json").read_text())
    require(m.get("schema")=="ARCANA_R6_G2_G3_SOURCE_TO_COUPLED_HANDOFF_MANIFEST_V1"
            and m.get("no_physical_solver_run") is True
            and m.get("physical_T1") is None
            and m.get("D_024")=="ACTIVE"
            and m.get("HistoryStore_modified") is False
            and m.get("WORLD_HISTORY_PRODUCTION_AUTHORIZED") is False
            and set(m.get("files",{}))==set(HANDOFF_FILES),
            "R6_PT_UPSTREAM_COUPLED_HANDOFF_MANIFEST_INVALID")
    for name,digest in m["files"].items():
        require(type(digest) is str and len(digest)==64 and sha256(folder/name)==digest,
                "R6_PT_UPSTREAM_COUPLED_HANDOFF_HASH_DRIFT:"+name)
    s8=json.loads((folder/HANDOFF_FILES[0]).read_text())
    s16=json.loads((folder/HANDOFF_FILES[1]).read_text())
    audit=json.loads((folder/HANDOFF_FILES[2]).read_text())
    for source,scenario,receipt in ((index8,s8,receipt8),(index16,s16,receipt16)):
        verify_candidate(source,scenario)
        require(scenario["source_packet_manifest_sha256"]==receipt["evidence_manifest_sha256"]
                and scenario["source_packet_report_file_sha256"]==receipt["source_index_sha256"]
                and len(scenario["additional_required_physics"])==7,
                "R6_PT_ORIGINAL_SOURCE_TO_COUPLED_HANDOFF_MISMATCH")
    require(audit.get("source_original_8x8_index_sha256")==receipt8["source_index_sha256"]
            and audit.get("source_original_16x16_index_sha256")==receipt16["source_index_sha256"]
            and len(audit.get("unresolved_physical_groups",[]))==8
            and audit.get("material_assignments")==0
            and audit.get("qualified_traction_inputs")==0
            and audit.get("mechanical_solver_runs")==0
            and audit.get("physical_T1") is None,
            "R6_PT_HANDOFF_AUDIT_AUTHORITY_OR_SOURCE_INVALID")
    return sha256(folder/"MANIFEST.json")


def build(root,packet8,packet16,handoff):
    gravity,lab,reference=source_gravity_and_lab(root)
    i8,p8,r8=load_packet(packet8,8)
    i16,p16,r16=load_packet(packet16,16)
    verify_cross_extent_provider_chain(i8,i16)
    handoff_sha=_load_handoff(handoff,i8,i16,r8,r16)
    a=compute_region(i8,p8,r8,extent=8,gravity_m_s2=gravity,lab_temperature_k=lab)
    b=compute_region(i16,p16,r16,extent=16,gravity_m_s2=gravity,lab_temperature_k=lab)
    overlap=sorted(set(i8["original_parent_node_order"]) & set(i16["original_parent_node_order"]))
    differences=[]
    for n in overlap:
        r1=a["original_T0_source_nodes"][str(n)]
        r2=b["original_T0_source_nodes"][str(n)]
        diffs={key:abs(r1[key]-r2[key]) for key in (
            "conditional_moho_delta_overburden_pa",
            "conditional_base_delta_overburden_pa",
            "integrated_delta_overburden_N_per_m")}
        if any(value != 0 for value in diffs.values()):
            differences.append({"node_id":n,"absolute_differences":diffs})
    summary={
        "schema":"ARCANA_R6_G2_G3_CONDITIONAL_PT_CROSS_EXTENT_AUDIT_V1",
        "decision":STATUS,"physical_interpretation":"SOURCE_PRE_GRAVITY_OVERBURDEN_INCREMENT_ONLY",
        "original_8x8_nodes":a["source_node_count"],
        "original_16x16_nodes":b["source_node_count"],
        "original_shared_parent_node_count":len(overlap),
        "shared_parent_PT_increment_discrepancies":differences,
        "shared_parent_PT_consistency_asserted":False,
        "region_extent_comparison_is_not_grid_convergence":True,
        "source_handoff_manifest_sha256":handoff_sha,
        "source_packet_8_manifest_sha256":r8["evidence_manifest_sha256"],
        "source_packet_16_manifest_sha256":r16["evidence_manifest_sha256"],
        "gravity_and_GT95_source":reference,
        "physical_G2_material_law_or_rock_selected":False,
        "effective_normal_pressure_or_surface_load_selected":False,
        "G3_external_basal_GPE_loads_derived":False,
        "mechanical_solve_authorized":False,
        "HistoryStore_modified":False,"physical_T1":None,"D_024":"ACTIVE",
        "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False,
    }
    return a,b,summary


def write_once(root,output,regions):
    root=Path(root).resolve(); output=Path(output).resolve()
    require(not output.is_relative_to(root),"R6_PT_EVIDENCE_INSIDE_REPOSITORY")
    require(not output.exists(),"R6_PT_EVIDENCE_ALREADY_EXISTS")
    require(set(regions)=={"REGION_8X8_SOURCE_PT.json","REGION_16X16_SOURCE_PT.json","AUDIT.json"},
            "R6_PT_OUTPUT_FILE_SET_INVALID")
    for report in regions.values():
        require(report.get("physical_T1") is None
                and report.get("HistoryStore_modified") is False
                and report.get("mechanical_solve_authorized") is False
                and report.get("D_024")=="ACTIVE",
                "R6_PT_PHYSICAL_AUTHORIZATION_FORBIDDEN")
    bodies={name:json.dumps(record,indent=2,allow_nan=False)+"\n"
            for name,record in regions.items()}
    output.mkdir(parents=True,exist_ok=False)
    for name,contents in bodies.items():
        (output/name).write_text(contents,encoding="utf-8")
    manifest={
        "schema":"ARCANA_R6_G2_G3_CONDITIONAL_PT_REFERENCE_MANIFEST_V1",
        "decision":STATUS,
        "files":{name:hashlib.sha256(body.encode()).hexdigest()
                 for name,body in bodies.items()},
        "no_solver_run":True,"physical_T1":None,
        "HistoryStore_modified":False,"D_024":"ACTIVE",
        "WORLD_HISTORY_PRODUCTION_AUTHORIZED":False,
    }
    (output/"MANIFEST.json").write_text(
        json.dumps(manifest,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return manifest


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root",type=Path,required=True)
    ap.add_argument("--packet-8",type=Path,required=True)
    ap.add_argument("--packet-16",type=Path,required=True)
    ap.add_argument("--handoff",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    paths=[*(Path(p)/"MANIFEST.json" for p in (
        args.packet_8,args.packet_16,args.handoff)),
        *(Path(p)/"SOURCE_INDEX.json" for p in (args.packet_8,args.packet_16)),
        *(Path(args.handoff)/p for p in HANDOFF_FILES)]
    hashes_before=[sha256(p) for p in paths]
    a,b,audit=build(args.repo_root,args.packet_8,args.packet_16,args.handoff)
    require([sha256(p) for p in paths]==hashes_before,
            "R6_PT_UPSTREAM_EVIDENCE_CHANGED_DURING_COMPILE")
    write_once(args.repo_root,args.output,{
        "REGION_8X8_SOURCE_PT.json":a,
        "REGION_16X16_SOURCE_PT.json":b,
        "AUDIT.json":audit,
    })
    print(json.dumps({
        "decision":STATUS,
        "original_8x8_nodes":a["source_node_count"],
        "original_16x16_nodes":b["source_node_count"],
        "source_8x8_moho_delta_overburden_Pa_range":a["summary"]["conditional_moho_delta_overburden_pa_min_max"],
        "source_8x8_base_delta_overburden_Pa_range":a["summary"]["conditional_base_delta_overburden_pa_min_max"],
        "GT95_T_only_whole_crust_count_8x8":a["summary"]["terrestrial_GT95_temperature_only_crust_nodes"]["temperature_only_full_layer_covered"],
        "unresolved_G2_G3_FAULT_groups":len(a["remaining_physical_groups"]),
        "mechanical_solve_authorized":False,"physical_T1":None,"D_024":"ACTIVE",
    },allow_nan=False))


if __name__=="__main__":
    main()

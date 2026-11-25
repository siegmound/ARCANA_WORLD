"""D11: source P/T design and unassigned geochemical reference triage, read-only."""
import json
import math
import numpy as np

from experiments.r6_thermo_provider_pilot_v1 import s3_d10_t0_pt_relevance as d10
from experiments.plate58_deforming_explore_v1 import g2_g3_t0_lithostatic_pt_reference as pt
from experiments.plate58_deforming_explore_v1.g2_g3_source_to_coupled_handoff import load_packet
from experiments.t0_geochemical_reference_v1 import compile_references as geo

EXPECTED_PT_MANIFEST = "515eb9f3fd523035d1ddba2ff2252380dc95bac7dec6d99033f37051fcef0a6f"


def clipped_joint(p_first, p_last, coefficients, box):
    """P in bar increases linearly in normalized depth f; T cubic in f.
    Return overlap by extrema of T on the P-clipped interval, not grid coverage.
    """
    p0,p1,t0,t1=box
    pt.require(all(math.isfinite(v) for v in (p_first,p_last,*coefficients,*box))
        and 0<=p_first<p_last and p0<=p1 and 0<t0<=t1,"D11_INVALID_DOMAIN")
    lo=max(0.,(p0-p_first)/(p_last-p_first))
    hi=min(1.,(p1-p_first)/(p_last-p_first))
    if lo>hi:
        return None
    a,b,c,d=coefficients
    candidates=[lo,hi]
    derivative=[3*d,2*c,b]
    scale=max(map(abs,derivative))
    if scale:
        for root in np.roots(np.asarray(derivative)/scale):
            if abs(float(np.imag(root)))<1e-11 and lo<float(np.real(root))<hi:
                candidates.append(float(np.real(root)))
    temperatures=[((d*f+c)*f+b)*f+a for f in candidates]
    pt.require(all(math.isfinite(v) and v>0 for v in temperatures),"D11_INVALID_T")
    bounds=[min(temperatures),max(temperatures)]
    return {"fraction_interval":[lo,hi],"T_bounds_K":bounds,
        "joint_overlap":bool(bounds[0]<=t1 and bounds[1]>=t0)}


def source_column(pre, layer, gravity):
    z0,z1,c0,c1,c2,c3=pt._layer(pre,layer)
    L=z1-z0
    p0=pt.overburden_increment_pa(pre,z0,gravity)/100000
    p1=pt.overburden_increment_pa(pre,z1,gravity)/100000
    return p0,p1,(c0,c1*L,c2*L**2,c3*L**3)


def design_screen(index, record, gravity):
    ids=index["original_parent_node_order"]
    profiles=index["source_original_PRE_model_T0_thermal_profiles_by_parent_node"]
    pt.require(ids==record["original_parent_node_order"] and set(profiles)==set(map(str,ids)),
        "D11_SOURCE_ID_MISMATCH")
    result={}
    for layer,name in enumerate(d10.LAYERS,1):
        columns={str(k):source_column(profiles[str(k)],layer,gravity) for k in ids}
        screens={}
        for key,box in d10.BOXES.items():
            hits={k:clipped_joint(*v,box) for k,v in columns.items()}
            p_hits=[x for x in hits.values() if x is not None]
            both=[k for k,x in hits.items() if x is not None and x["joint_overlap"]]
            screens[key]={"nodes_with_pressure_interval":len(p_hits),
                "nodes_with_joint_continuous_model_overlap":len(both),
                "pressure_clipped_T_min_max_K":[min(x["T_bounds_K"][0] for x in p_hits),
                    max(x["T_bounds_K"][1] for x in p_hits)] if p_hits else None,
                "first_joint_parent_ids":both[:5]}
        # Deterministic temperature-ranked paired source states, not independent P/T axes.
        samples=[]
        for k in ids:
            for x in record["original_T0_source_nodes"][str(k)]["source_depth_pt_samples"]:
                if x["layer"]==name:
                    samples.append({"parent_node_id":k,"depth_m":x["source_depth_m"],
                        "T_K":x["source_PRE_temperature_k"],
                        "conditional_delta_P_bar":x["conditional_delta_vertical_overburden_pa"]/100000})
        samples.sort(key=lambda x:(x["T_K"],str(x["parent_node_id"]),x["depth_m"]))
        representatives=[{"temperature_rank_fraction":f,**samples[round(f*(len(samples)-1))]}
            for f in (0.,.25,.5,.75,1.)]
        result[name]={"source_columns":len(ids),"screens":screens,
            "temperature_ranked_paired_source_samples":representatives}
    return result


def references():
    raw={}
    for name,blob in geo.SOURCES.items():
        raw[name],_=geo.source_bytes(d10.ROOT/"experiments"/"t0_geochemical_reference_v1"/"data"/name,blob)
    records=geo.continental_reference(raw["CC__Rudnick_Gao__2014.csv"])
    records.append(geo.depleted_mantle_reference(raw["DM__Salters_Stracke__2004.csv"]))
    records.append(geo.oceanic_morb_trace_reference(raw["Sun_McDonough__1989.csv"]))
    return {"source_records":records,"support":geo.read_r6_support(d10.ROOT),
        "oceanic_bulk_reference_ready":False,"redox_and_volatile_closure_ready":False,
        "source_placement_ready":False,"authorial_selection":None}


def main():
    folder=d10.BASE/"R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
    pt.require(pt.sha256(folder/"MANIFEST.json")==EXPECTED_PT_MANIFEST,"D11_PT_MANIFEST_DRIFT")
    _,reports,audit=d10.cold._load_original_pt(folder)
    packet8=d10.BASE/"R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02"
    packet16=d10.BASE/"R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02"
    a,b,expected=pt.build(d10.ROOT,packet8,packet16,d10.BASE/"R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01")
    pt.require(reports==[a,b] and audit==expected,"D11_PT_REPLAY_DRIFT")
    gravity,_,_=pt.source_gravity_and_lab(d10.ROOT)
    for extent,packet,record in ((8,packet8,a),(16,packet16,b)):
        index,_,receipt=load_packet(packet,extent)
        pt.require(receipt["evidence_manifest_sha256"]==record["source_packet_manifest_sha256"],
            "D11_PACKET_DRIFT")
        print("REGION_DESIGN",extent,json.dumps(design_screen(index,record,gravity),sort_keys=True,allow_nan=False))
    print("CHEMISTRY_REFERENCES",json.dumps(references(),sort_keys=True,allow_nan=False))
    print("D11_SCOPE",json.dumps({"conditional_delta_P_not_absolute":True,
        "continuous_model_overlap_not_calibration":True,"ranked_samples_not_authorial_choices":True,
        "native_membership_gate_pending":True,"legacy_plate_ID_1_12_mismatch_pending":True,
        "material_assignments":0,"additional_engine_runs":0,"physical_T1":None,
        "mechanical_solve_authorized":False,"WORLD_HISTORY_PRODUCTION_AUTHORIZED":False}))
    print("D11_T0_PT_MATERIAL_DESIGN_COMPLETE")


if __name__=="__main__":
    main()

"""D10: read-only original T0 regional P/T relevance, not calibration/assignment."""
import json
import math
from pathlib import Path

from experiments.plate58_deforming_explore_v1 import g2_g3_t0_lithostatic_pt_reference as pt
from experiments.plate58_deforming_explore_v1 import g2_g3_t0_cold_crust_regime as cold

BASE = Path("/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6")
ROOT = Path(__file__).resolve().parents[2]
# Bounds are numerical screening rectangles, NOT a calibrated validity domain.
BOXES = {
    "PERPLEX_D7_BOUNDING_RECTANGLE_NOT_COVERAGE": (3000, 5000, 1000, 1100),
    "PERPLEX_S3_DESIGN_RECTANGLE_NOT_COVERAGE": (2000, 6000, 950, 1150),
    "MAGEMIN_S3_DESIGN_RECTANGLE_NOT_COVERAGE": (8000, 12000, 1273.15, 1473.15),
}
LAYERS = ("crust", "mantle_lithosphere")


def classify(p_delta_pa, t_k, box):
    p0,p1,t0,t1=box
    pt.require(type(p_delta_pa) in (float,int) and math.isfinite(p_delta_pa)
               and p_delta_pa >= 0 and type(t_k) in (float,int)
               and math.isfinite(t_k) and t_k>0,"D10_BAD_SAMPLE")
    p_delta_bar=p_delta_pa/100000
    return (p0<=p_delta_bar<=p1, t0<=t_k<=t1)


def summarize(record, extent):
    nodes=record["original_T0_source_nodes"]
    ids=record["original_parent_node_order"]
    pt.require(len(ids)==len(set(ids))==(extent+1)**2 and set(nodes)==set(map(str,ids))
               and record["physical_T1"] is None and record["mechanical_solve_authorized"] is False,
               "D10_SOURCE_SCOPE")
    out={}
    for layer in LAYERS:
        samples=[]
        bounds=[]
        for key in ids:
            n=nodes[str(key)]
            pt.require(all(n[k] is None for k in ("absolute_surface_pressure_pa","pore_pressure_pa","effective_pressure_pa","fault_normal_pressure_pa")),"D10_PRESSURE_AUTHORITY")
            local=[x for x in n["source_depth_pt_samples"] if x["layer"]==layer]
            pt.require(len(local)==5 and sorted(x["fraction_of_layer"] for x in local)==[0.,.25,.5,.75,1.],"D10_SAMPLE_COVERAGE")
            b=n["exact_PRE_temperature_bounds_k"][layer]
            pt.require(len(b)==2 and 0<b[0]<=b[1],"D10_T_BOUNDS")
            bounds.append(b)
            samples.extend((str(key),x["conditional_delta_vertical_overburden_pa"],x["source_PRE_temperature_k"]) for x in local)
        result={"source_nodes":len(ids),"depth_samples":len(samples),
                "exact_temperature_range_K":[min(b[0] for b in bounds),max(b[1] for b in bounds)],
                "sample_conditional_delta_overburden_bar_range":[min(x[1] for x in samples)/100000,max(x[1] for x in samples)/100000],
                "screens":{}}
        for name,box in BOXES.items():
            marked=[(k,*classify(p,t,box)) for k,p,t in samples]
            result["screens"][name]={
                "exact_layer_T_overlap_nodes":sum(b[0]<=box[3] and b[1]>=box[2] for b in bounds),
                "exact_layer_T_fully_inside_nodes":sum(box[2]<=b[0] and b[1]<=box[3] for b in bounds),
                "sample_T_inside":sum(t for _,p,t in marked),
                "sample_delta_P_inside":sum(p for _,p,t in marked),
                "sample_both_inside":sum(p and t for _,p,t in marked),
                "nodes_with_sample_both_inside":len({k for k,p,t in marked if p and t})}
        out[layer]=result
    return out


def main():
    folder=BASE/"R6_G2G3_T0_LITHOSTATIC_PT_REFERENCE_NEW01"
    _,archived,audit=cold._load_original_pt(folder)
    a,b,expected=pt.build(ROOT,BASE/"R6_G2G3_PHYSICAL_SOURCE_PACKET_8X8_NEW02",
        BASE/"R6_G2G3_PHYSICAL_SOURCE_PACKET_16X16_NEW02",
        BASE/"R6_G2G3_SOURCE_TO_COUPLED_AUTHORING_NEW01")
    pt.require(archived==[a,b] and audit==expected,"D10_ORIGINAL_PT_REPLAY_MISMATCH")
    print("D10_ORIGINAL_PT_REPLAY_PASS")
    print("PT_MANIFEST_SHA256",pt.sha256(folder/"MANIFEST.json"))
    for extent,record in ((8,a),(16,b)):
        print("REGION",extent,json.dumps(summarize(record,extent),sort_keys=True,allow_nan=False))
    print("D10_SCOPE",json.dumps({"conditional_overburden_is_not_absolute_pressure":True,
        "rectangle_is_not_provider_calibration_or_sample_coverage":True,
        "finite_depth_samples_are_not_continuous_PT_coverage":True,
        "material_assignments":0,"additional_engine_runs":0,"physical_T1":None,
        "mechanical_solve_authorized":False,"WORLD_HISTORY_PRODUCTION_AUTHORIZED":False}))
    print("D10_T0_PT_RELEVANCE_COMPLETE")


if __name__=="__main__":
    main()

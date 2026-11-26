"""C03F closure: source-bound signed-coordinate review and C04 research handoff."""
from __future__ import annotations
import argparse
from fractions import Fraction as Q
import json
import re
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_scientific_review as r

f=r.f
c=r.c
d=r.d
s2=r.s2
need=r.need
hgp=r.hgp
PIN="d01d2f17b9a73b4354c65f0a871aabdfeaa36c84e00a28edc84a26e5093a15dc"
SOURCE="49f2d2dc4a00e785311da9ea0bfd0eec8962f3af"
OUT=s2.BASE/"R6_THERMO_C03F_RESTRICTED_RESEARCH_CLOSURE_NEW01"
STATUS="C03F_RESTRICTED_RESEARCH_CLOSURE__C04_CANDIDATE_HANDOFF_READY"
MODELS={
 "Bio(TCC)":{"missing":"mnbi","rows":(("ffbit","sdph","ftbit","ann"),("f3b_q","east","tbi_q","phl")),
    "ordered":{"obi":"2/3 phl + 1/3 ann"},
    "dependent":{"sdph":"1 east + 1 ann - 1 obi","ffbit":"1 f3b_q + 1 ann - 1 obi",
                 "ftbit":"1 tbi_q + 1/2 ann + 1/2 obi - 1 phl"},
    "roots":("f3b_q","east","tbi_q","phl","ann"),"base":"phl","ferrous":"ann",
    "increments":(Q(2,3),Q(2,3),Q(2,3),Q(1))},
 "Chl(W)":{"missing":"mnchl","rows":(("fames","fafchl","ff3cli","daph"),("ames","afchl","f3cl_q","clin")),
    "ordered":{"och1":"1 afchl - 1 clin + 1 daph","och2":"1 afchl - 1/5 clin + 1/5 daph"},
    "dependent":{"fames":"1 ames + 1 daph - 1 och2 + 1 afchl - 1 clin",
                 "fafchl":"1 och1 + 1 och2 - 1 afchl","ff3cli":"1 f3cl_q + 1 daph - 1 clin"},
    "roots":("ames","afchl","f3cl_q","clin","daph"),"base":"clin","ferrous":"daph",
    "increments":(Q(4,5),Q(6,5),Q(1),Q(1))}
}
TERM=re.compile(r"\s*([+-]?)\s*(\d+(?:/\d+|\.\d+)?|\.\d+)\s+([A-Za-z][A-Za-z0-9_]*)")


def linear(text):
    out={}
    pos=0
    while pos<len(text):
        m=TERM.match(text,pos)
        need(m is not None and (pos==0 or m[1] in ("+","-")),"C03FA_LINEAR:"+text)
        k=m[3]
        out[k]=out.get(k,Q(0))+Q(m[2])*(-1 if m[1]=="-" else 1)
        pos=m.end()
    return {k:v for k,v in out.items() if v}


def source_model(name,raw):
    spec=MODELS[name]
    lines=d.composition_audit.active_text(raw).splitlines()
    need("688" in lines and "site_check_override" not in lines,"C03FA_MODEL_FORMAT")
    # Verify native vertex rows and declared [0,1] chemical coordinates.
    flat=[" ".join(x.split()) for x in lines]
    if name=="Bio(TCC)":
        vertices=[f"{a} {b}" for a,b in zip(*spec["rows"])]
        coords=("X_Mg","X_FeTs","X_AlTs","X_TiTs")
    else:
        vertices=[" ".join(x) for x in spec["rows"]]
        coords=("X_Mames","X_Mafchl","X_Mf3cl_q","X_Mg")
    need(all(flat.count(x)==1 for x in vertices)
         and all(flat.count(x+" 0 1 .1 0")==1 for x in coords),"C03FA_VERTEX_DOMAIN:"+name)
    definitions={}
    for group in ("ordered","dependent"):
        start=lines.index("begin_"+group+"_endmembers")
        end=lines.index("end_"+group+"_endmembers")
        actual={}
        for row in lines[start+1:end]:
            if row:
                k,v=row.split("=",1)
                actual[k.strip()]=linear(v.split("delta_g_of_ordering",1)[0].strip())
        need(actual=={k:linear(v) for k,v in spec[group].items()},"C03FA_DEFINITION_DRIFT:"+name)
        definitions.update(actual)
    sites={}
    for line in lines:
        m=re.fullmatch(r"z\(([^,]+),([^)]+)\)\s*=\s*(.+)",line)
        if m:
            key=(m[2],m[1].replace("+",""))
            need(key not in sites,"C03FA_DUPLICATE_SITE")
            sites[key]=linear(m[3])
    need(len(sites)==13,"C03FA_SITE_COUNT:"+name)
    return definitions,sites


def expand(k,definitions,roots,stack=()):
    need(k not in stack,"C03FA_CYCLE")
    if k in roots:
        return {k:Q(1)}
    need(k in definitions,"C03FA_UNKNOWN_MEMBER:"+k)
    out={}
    for member,factor in definitions[k].items():
        for root,v in expand(member,definitions,roots,stack+(k,)).items():
            out[root]=out.get(root,Q(0))+factor*v
    return {k:v for k,v in out.items() if v}


def project(weights,definitions,roots):
    out={k:Q(0) for k in roots}
    for k,v in weights.items():
        if v:
            for root,factor in expand(k,definitions,roots).items():
                out[root]+=v*factor
    return out


def witness(name,coeff,definitions):
    spec=MODELS[name]
    roots=spec["roots"]
    # The two observed vectors sum exactly to one at the printed centers.
    need(sum(coeff.values())==1,"C03FA_CENTER_SUM")
    projected=project(coeff,definitions,roots)
    base,fe=spec["base"],spec["ferrous"]
    # Project ordered states into the native chemical mixing space, then
    # construct a nonnegative product-of-simplices witness. This is not an
    # equality of ordering energies or a claim of global optimality.
    q=[projected[k] for k in roots[:3]]+[projected[base]+projected[fe]]
    den=sum(x*y for x,y in zip(q,spec["increments"],strict=True))
    need(den>0 and sum(q)==1 and all(0<=x<=1 for x in q),"C03FA_CHEMICAL_SIMPLEX")
    xfe=projected[fe]/den
    need(0<=xfe<=1,"C03FA_FE_SIMPLEX")
    weights={k:x*xfe for k,x in zip(spec["rows"][0],q,strict=True)}
    weights.update({k:x*(1-xfe) for k,x in zip(spec["rows"][1],q,strict=True)})
    need(sum(weights.values())==1 and all(0<=x<=1 for x in weights.values())
         and project(weights,definitions,roots)==projected,"C03FA_VERTEX_WITNESS")
    return {"chemical_projection":{k:str(v) for k,v in projected.items()},
            "chemical_simplex":[str(x) for x in q],"Fe_coordinate":str(xfe),
            "vertex_weights":{k:str(v) for k,v in weights.items()},
            "composition_reproduced_exactly":True,"ordering_energy_equivalence_claimed":False}


def interval(token):
    return tuple(Q(v) for v in f.audit.interval(token))


def check_sites(coeff,sites,printed,missing):
    values={k:interval(v) for k,v in coeff.items()}
    values[missing]=(Q(0),Q(0))
    observed={(row["site"],k):interval(v) for row in printed for k,v in row["fractions"].items()}
    need(set(observed)<=set(sites),"C03FA_SITE_UNKNOWN")
    out=[]
    for key,expression in sites.items():
        need(set(expression)<=set(values),"C03FA_SITE_MEMBER")
        parts=[sorted((factor*values[k][0],factor*values[k][1])) for k,factor in expression.items()]
        lo,hi=(sum(x[i] for x in parts) for i in (0,1))
        target=observed.get(key,(Q(0),Q(0)))
        need(max(lo,target[0],Q(0))<=min(hi,target[1],Q(1)),"C03FA_SITE_RECONSTRUCTION:"+str(key))
        out.append({"site":key[0],"species":key[1],"predicted_interval":[str(lo),str(hi)],
                    "printed_interval":[str(x) for x in target],"compatible":True})
    return out


def replay_review(parent):
    plans,results=r.replay(parent)
    archive=r.OUT
    receipt=c.read(d.m.HERE/"c03fr_r1_fair_receipt_v1.json")
    need(archive.is_dir() and not archive.is_symlink()
         and not (archive/"MANIFEST.json").is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==receipt["manifest_sha256"],
         "C03FA_REVIEW_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==SOURCE==receipt["source_sha"]
         and receipt["exit"]==0 and receipt["regression_passed"]==205
         and man["schema"]=="R6_C03F_SCIENTIFIC_REVIEW_MANIFEST_V1"
         and man["status"]==r.STATUS and man["campaign_manifest_sha256"]==r.PIN
         and man["reviewed_points"]==4 and man["additional_engine_runs"]==0
         and man["authorized_equilibrium_solver_calls"]==0
         and man["scientific_promotion"] is False and all(man[k]==v for k,v in c.SCOPE.items()),
         "C03FA_REVIEW_MANIFEST")
    archived=c.read(archive/"REVIEW.json")
    reviewed={name:[r.review_point(p,a,plans[name],parent[-1])
                   for p,a in zip(results[name]["points"],results[name]["audit"],strict=True)]
              for name in f.NAMES}
    negatives=[n for name in f.NAMES for row in reviewed[name] for n in row["negative_coefficients"]]
    need(archived["points"]==reviewed and archived["negative_coefficients"]==negatives
         and archived["negative_basis_adjudication"]=="PENDING"
         and archived["scientific_promotion"] is False and archived["C04_material_assignment_authorized"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03FA_REVIEW_REPLAY")
    evidence=r.source_evidence(parent,negatives)
    need(evidence==c.read(archive/"MODEL_SOURCE_EVIDENCE.json"),"C03FA_SOURCE_REPLAY")
    need(len(negatives)==2 and {(x["id"],x["model"],x["endmember"]):x["coefficient"] for x in negatives}
         ==r.NEGATIVE_EXPECTED,"C03FA_NEGATIVE_DRIFT")
    return plans,results,reviewed,evidence,negatives


def close(plans,results,reviewed,evidence,negatives):
    decisions=[]
    records=[]
    for name in f.NAMES:
        for row,point in zip(reviewed[name],results[name]["points"],strict=True):
            need(all(row["elastic"]["printed_elastic_checks"].values())
                 and all(x["printed_range_and_sum_compatible"] for x in row["printed_sites"]),
                 "C03FA_REVIEW_FAILURE")
            for n in row["negative_coefficients"]:
                model=n["model"]
                definitions,sites=source_model(model,evidence["model_blocks"][model])
                missing=MODELS[model]["missing"]
                need(missing in f.r.design.r1.ed.MISSING[model],"C03FA_MISSING_MN_SCOPE")
                spec=[x for x in row["speciation"] if x["model"]==model]
                need(len(spec)==1,"C03FA_INSTANCE")
                coeff=spec[0]["coefficients"]
                printed=[x for x in row["printed_sites"] if x["model"]==model]
                result=witness(model,{k:Q(v) for k,v in coeff.items()},definitions)
                reconstructed=check_sites(coeff,sites,printed,missing)
                decisions.append({**n,"chemical_domain_witness":result,"site_reconstruction":reconstructed,
                    "classification":"SIGNED_COORDINATE_COMPATIBLE_WITH_PRINTED_SITES_AND_NATIVE_CHEMICAL_POLYTOPE",
                    "full_ordering_optimizer_domain_proof":False})
            records.append({"id":row["id"],"recipe":name,"source_chemistry_sha256":plans[name]["source_chemistry_sha256"],
                "normalized_moles":plans[name]["normalized_moles"],"source_point":point["source_point"],
                "native_potential_readback":point["native_potential_readback"],
                "phase_wt_percent":row["phase_wt_percent"],"properties":row["elastic"],
                "H2O_wt_percent":row["H2O_wt_percent"],"phase_water_moles_at_printed_centers":row["phase_water_moles_at_printed_centers"],
                "provider":"MEEMUM_HP02_ACT_RESTRICTED_SUBSOLIDUS","campaign_manifest":r.PIN,
                "review_manifest":PIN,"authority":"CONDITIONAL_RESEARCH_CANDIDATE_ONLY",
                "absolute_pressure_pa":None,"world_material_assignment":False,
                "interpolation_authorized":False,"scientific_promotion":False})
    need(len(decisions)==len(negatives)==2 and len(records)==4,"C03FA_TOTAL")
    return decisions,records


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--offline-closure-only",required=True,action="store_true")
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03FA_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03FA_OUTPUT_EXISTS")
    parent=c.parent()
    args_replay=replay_review(parent)
    print("C03FA_REVIEW_REPLAY_PASS",PIN,flush=True)
    decisions,records=close(*args_replay)
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"SIGNED_COORDINATE_ADJUDICATION.json",{"observations":decisions,
         "scope":"PRINTED_SITE_AND_CHEMICAL_DOMAIN_COMPATIBILITY_NOT_FULL_MODEL_CALIBRATION",
         "scientific_promotion":False})
    s2.write_json(OUT/"C04_RESEARCH_CANDIDATES.json",{"records":records,
         "assignment_authorized":False,"cold_felsic":"DEFERRED",
         "limitations":["conditional pressure only","eight missing endmembers",
             "no aqueous species data","restricted phase roster and nonwater PMELT exclusions",
             "no independent ordering/global-minimum proof","no rheology or regional assignments"],**c.SCOPE})
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03F_RESTRICTED_RESEARCH_CLOSURE_MANIFEST_V1",
        "source_sha":head,"status":STATUS,"review_manifest_sha256":PIN,"campaign_manifest_sha256":r.PIN,
        "files":d.launcher.inventory(OUT),"reviewed_points":4,"signed_coordinates_adjudicated":2,
        "conditional_research_candidates":4,"additional_engine_runs":0,
        "authorized_equilibrium_solver_calls":0,"scientific_promotion":False,**c.SCOPE})
    for row in decisions:
        print("C03FA_SIGNED_COORDINATE",json.dumps(row,sort_keys=True),flush=True)
    print("C03FA_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(STATUS)
    print("CONDITIONAL_RESEARCH_CANDIDATES=4")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()

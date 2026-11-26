"""C03F scientific review: independent read-only archive and native model evidence."""
from __future__ import annotations
import argparse
from decimal import Decimal as D
import json
import re
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_closed_bulk_campaign as f

c=f.c
d=f.d
s2=f.s2
need=f.need
hgp=f.hgp
a=f.audit
PIN="041110fd8cf3bc63b8c157a9b39fcb61aec7963992d6722894840d95b1c6c682"
SOURCE="c8e657682323a90809046a4208cb9c68a600e9b2"
OUT=s2.BASE/"R6_THERMO_C03F_SCIENTIFIC_REVIEW_NEW01"
STATUS="C03F_ARCHIVE_REPLAY_AND_PROPERTY_AUDIT_COMPLETE__MODEL_DOMAIN_ADJUDICATION_REQUIRED"
NEGATIVE_EXPECTED={("C01_MORB_WET_P35304","Bio(TCC)","phl"):"-0.00510",
                   ("C01_MORB_WET_P36026","Chl(W)","och2"):"-0.19418"}


def replay(parent):
    f.r.design.r1.prior.verify_readiness(parent)
    f.r.design.r1.verify_failure(parent)
    plans,inputs,expected,preflight=f.replay_preflight(parent)
    archive=f.OUT
    rec=c.read(d.m.HERE/"c03fc_fair_receipt_v1.json")
    need(archive.is_dir() and not archive.is_symlink()
         and not (archive/"MANIFEST.json").is_symlink()
         and hgp.file_sha(archive/"MANIFEST.json")==PIN==rec["manifest_sha256"],
         "C03FR_ARCHIVE_PIN")
    man=c.read(archive/"MANIFEST.json")
    inv=d.launcher.inventory(archive)
    inv.pop("MANIFEST.json")
    need(inv==man["files"] and man["source_sha"]==SOURCE==rec["source_sha"]
         and rec["exit"]==0 and rec["regression_passed"]==195
         and man["schema"]=="R6_C03F_CLOSED_BULK_CAMPAIGN_MANIFEST_V1"
         and man["status"]==f.STATUS and man["preflight_manifest_sha256"]==f.PIN
         and man["design_manifest_sha256"]==f.old.PIN
         and man["native_initialization_attempts"]==2
         and all(man[k]==4 for k in ("authorized_equilibrium_solver_calls","requested_equilibrium_points",
                                    "completed_equilibrium_points","audited_equilibrium_points"))
         and man["scientific_promotion"] is False
         and all(man[k]==v for k,v in c.SCOPE.items()),"C03FR_ARCHIVE_MANIFEST")
    need(c.read(archive/"PREFLIGHT_REPLAY.json")==preflight,"C03FR_PREFLIGHT_REPLAY")
    results={}
    for name in f.NAMES:
        work=archive/name
        need(c.read(work/"INPUT.json")==plans[name]
             and all((work/k).read_bytes()==v for k,v in inputs[name].items()),"C03FR_INPUT")
        protocol=f.CampaignDialogue(plans[name],parent[-1],expected[name],preflight[name])
        raw=(work/"RUN_STDOUT.log").read_bytes()
        replies=[]
        while True:
            reply=protocol.next_response(raw)
            if reply is None:
                break
            replies.append(reply)
        dia=c.read(work/"DIALOGUE.json")
        launch=c.read(work/"LAUNCH.json")
        need(b"".join(replies)==(work/"DIALOGUE_STDIN.log").read_bytes()
             and protocol.events==dia["events"] and protocol.state==dia["state"]=="SENTINEL_SENT"
             and protocol.acknowledged==dia["acknowledged_warning_codes"]
             and protocol.requested==dia["requested_ids"]==[p["id"] for p in plans[name]["points"]]
             and dia["completed_ids"]==[x["id"] for x in protocol.completed]
             and dia["requested_equilibrium_points"]==dia["completed_equilibrium_points"]==2
             and dia["error"] is None and dia["scientific_warning_acceptance"] is False
             and launch["exit_code"]==0 and launch["error"] is None and not launch["timeout"]
             and len(protocol.completed)==len(protocol.audits)==2,"C03FR_NATIVE_REPLAY")
        need(c.read(work/"POINT_CAPTURE.json")=={"requested_ids":protocol.requested,
             "completed":protocol.completed,"audits":protocol.audits,"scientific_acceptance":False},
             "C03FR_CAPTURE_REPLAY")
        result={"points":protocol.completed,"audit":protocol.audits,"launch":launch,
                "scientific_promotion":False}
        need(c.read(work/"RESULT.json")==result,"C03FR_RESULT_REPLAY")
        results[name]=result
    need(c.read(archive/"RESULT.json")=={"recipes":results,"requested_equilibrium_points":4,
         "completed_equilibrium_points":4,"audited_equilibrium_points":4,
         "scientific_promotion":False,**c.SCOPE},"C03FR_TOTAL_REPLAY")
    return plans,results


def quotient(x,y):
    need(y[0]>0,"C03FR_POSITIVE_DENOMINATOR")
    return a.product(x,(D(1)/y[1],D(1)/y[0]))


def scaled(x,k):
    return a.product(x,(k,k))


def system_row(text,start,end,n):
    rows=a.rows(text,start,end)
    system=[x for x in rows if x[0]=="System"]
    need(len(system)==1 and len(system[0])==n+1,"C03FR_SYSTEM_ROW:"+start)
    return system[0][1:]


def elastic_review(text):
    thermo=system_row(text,"Molar Properties and Density:","Seismic Properties:",9)
    seismic=system_row(text,"Seismic Properties:","Bulk Composition:",7)
    mass,g,entropy,volume,cp,alpha,beta,ratio,rho=map(f.number,thermo)
    gr,k,mu,v0,vp,vs,nu=map(f.number,seismic)
    need(min(mass,volume,cp,beta,rho,k,mu,v0,vp,vs)>0
         and D("-1")<nu<D(".5"),"C03FR_PHYSICAL_RANGE")
    ki,mi,ri=a.interval(seismic[1]),a.interval(seismic[2]),a.interval(thermo[8])
    predictions={"V0_squared":quotient(scaled(ki,D(".1")),ri),
        "Vp_squared":quotient(scaled(a.total([ki,scaled(mi,D(4)/3)]),D(".1")),ri),
        "Vs_squared":quotient(scaled(mi,D(".1")),ri),
        "Poisson":quotient(a.total([scaled(ki,D(3)),scaled(mi,D(-2))]),
                           scaled(a.total([scaled(ki,D(3)),mi]),D(2)))}
    observed={key:a.product(a.interval(token),a.interval(token))
              for key,token in zip(("V0_squared","Vp_squared","Vs_squared"),seismic[3:6],strict=True)}
    observed["Poisson"]=a.interval(seismic[6])
    checks={key:a.overlaps(pred,observed[key]) for key,pred in predictions.items()}
    # Distinguish an inconsistency in printed aggregate values from a solver failure.
    return {"density_kg_m3":float(rho),"Cp_J_kg_K":float(cp/mass*1000),
            "alpha_1_K":float(alpha),"beta_1_Pa":float(beta/D(100000)),
            "Ks_Pa":float(k*100000),"Mu_Pa":float(mu*100000),
            "Vp_km_s":float(vp),"Vs_km_s":float(vs),"V0_km_s":float(v0),"Poisson":float(nu),
            "printed_elastic_checks":checks,
            "predicted_intervals":{k:[str(v) for v in x] for k,x in predictions.items()},
            "observed_intervals":{k:[str(v) for v in x] for k,x in observed.items()}}


def speciation(text,ident):
    rows=a.rows(text,"Phase speciation (molar proportions):","Structural formulae for 688 format solution models:")
    out=[]
    neg=[]
    for row in rows:
        name=row[0]
        parts=" ".join(row[1:]).split(",")
        entries={}
        for p in parts:
            m=re.fullmatch(r"\s*(\S+):\s*("+f.ref.NUMBER+r")\s*",p)
            need(m is not None and m[1] not in entries,"C03FR_SPECIATION_PARSE:"+name)
            entries[m[1]]=m[2]
        summed=a.total([a.interval(x) for x in entries.values()])
        need(a.overlaps(summed,(D(1),D(1))),"C03FR_SPECIATION_SUM:"+name)
        for k,v in entries.items():
            if f.number(v)<0:
                neg.append({"id":ident,"model":name,"endmember":k,"coefficient":v,
                            "classification":"SIGNED_BASIS_OR_DOMAIN_REQUIRES_SOURCE_ADJUDICATION"})
        out.append({"model":name,"coefficients":entries,"sum_interval":[str(v) for v in summed]})
    return out,neg


def site_review(text):
    section=text.split("Structural formulae for 688 format solution models:",1)[1].split(
        "Molar Properties and Density:",1)[0]
    model=None
    sites=[]
    for line in section.splitlines():
        st=line.strip()
        if not st or st.startswith(("Phase ","Non-mixing")):
            continue
        if re.fullmatch(r"\S+\([^ ]+\)",st):
            model=st
            continue
        m=re.fullmatch(r"(\S+)\s+("+f.ref.NUMBER+r")\s+(.+)",st)
        need(m is not None and model is not None,"C03FR_SITE_PARSE:"+st)
        values=re.findall(r"([A-Za-z][A-Za-z0-9]*)\(("+f.ref.NUMBER+r")\)",m[3])
        need(values and "".join(k+"("+v+")" for k,v in values)==m[3],
             "C03FR_SITE_VALUES:"+st)
        iv=[a.interval(v) for k,v in values]
        valid=all(a.overlaps(x,(D(0),D(1))) for x in iv) and a.overlaps(a.total(iv),(D(1),D(1)))
        sites.append({"model":model,"site":m[1],"multiplicity":m[2],"fractions":dict(values),
                      "printed_range_and_sum_compatible":valid})
    need(sites,"C03FR_NO_SITE_EVIDENCE")
    return sites


def review_point(point,audit,plan,records):
    text=point["output_text"]
    phases=audit["phase_wt_percent"]
    need(all(k in plan["solution_models"] or k in records for k in phases)
         and not set(phases)&set(plan["excluded_phases"]),"C03FR_PHASE_IDENTITY")
    spec,neg=speciation(text,point["id"])
    sites=site_review(text)
    elastic=elastic_review(text)
    # Preserve normalized native molar coefficients, not inferred mineral formulae.
    phase=a.rows(text,"Phase Compositions (molar  proportions):","Phase speciation (molar proportions):")
    ix=phase[0][7:].index("H2O")
    water={}
    for row in phase[1:]:
        water[row[0]]=water.get(row[0],0.0)+float(f.number(row[4])*f.number(row[5+ix]))
    return {"id":point["id"],"node":point["source_point"]["parent_node_id"],
            "phase_wt_percent":phases,"H2O_wt_percent":audit["H2O_wt_percent"],
            "phase_water_moles_at_printed_centers":water,"elastic":elastic,
            "speciation":spec,"negative_coefficients":neg,"printed_sites":sites,
            "pressure_semantics":"HYPOTHETICAL_COMPARATIVE_ONLY",
            "scientific_promotion":False}


def source_evidence(parent,neg):
    runtime=parent[1]
    library=parent[4]
    blocks=d.c.b.model_blocks(library,tuple(sorted({x["model"] for x in neg})))
    need(set(blocks)=={x["model"] for x in neg},"C03FR_MODEL_SOURCE")
    def as_text(x):
        return x.decode("utf-8") if isinstance(x,bytes) else x
    models={k:as_text(v) for k,v in blocks.items()}
    for x in neg:
        need(re.search(r"(?<!\w)"+re.escape(x["endmember"])+r"(?!\w)",models[x["model"]]),
             "C03FR_NEGATIVE_SOURCE_IDENTITY")
    source=Path(runtime["source"])/"src"
    # The same source pins used by the parent preflight.
    f.r.corrected_reference({name:{"solution_models":parent[7]["arms"]["ACT_ONLY"]["solution_models"]}
                             for name in f.NAMES},runtime)
    excerpts={}
    pattern=re.compile(r"phase speciation|extra.simplicial|site population|negative.*(?:endmember|proportion)|(?:endmember|proportion).*negative",re.I)
    for name in ("meemum.f","rlib.f","tlib.f","olib.f"):
        path=source/name
        if not path.is_file():
            continue
        raw=path.read_bytes()
        lines=raw.decode("utf-8",errors="replace").splitlines()
        hits=[i for i,line in enumerate(lines) if pattern.search(line)]
        excerpts[name]={"sha256":hgp.sha(raw),"hits":[{"line":i+1,
             "context":"\n".join(lines[max(0,i-4):i+5])} for i in hits]}
    return {"model_blocks":models,"library_sha256":hgp.sha(library),
            "source_excerpts":excerpts,"adjudication":"NOT_AUTOMATICALLY_INFERRED_FROM_SIGN_OR_SITE_SUM"}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--review-only",action="store_true",required=True)
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"C03FR_CHECKOUT")
    need(not OUT.exists() and not OUT.is_symlink(),"C03FR_OUTPUT_EXISTS")
    parent=c.parent()
    plans,results=replay(parent)
    print("C03FR_CAMPAIGN_REPLAY_PASS",PIN,flush=True)
    reviewed={}
    negatives=[]
    for name in f.NAMES:
        reviewed[name]=[review_point(p,aud,plans[name],parent[-1])
                        for p,aud in zip(results[name]["points"],results[name]["audit"],strict=True)]
        for row in reviewed[name]:
            negatives.extend(row["negative_coefficients"])
            print("C03FR_POINT_REVIEW",name,json.dumps(row,sort_keys=True),flush=True)
    need({(x["id"],x["model"],x["endmember"]):x["coefficient"] for x in negatives}==NEGATIVE_EXPECTED
         and len(negatives)==2,"C03FR_NEGATIVE_OBSERVATION_DRIFT")
    evidence=source_evidence(parent,negatives)
    comparisons=[]
    for node in (35304,36026):
        base,wet=(next(x for x in reviewed[name] if x["node"]==node) for name in f.NAMES)
        props={k:{"BASE":base["elastic"][k],"WET":wet["elastic"][k],
                  "WET_minus_BASE":wet["elastic"][k]-base["elastic"][k]}
               for k in ("density_kg_m3","Cp_J_kg_K","Ks_Pa","Mu_Pa","Vp_km_s","Vs_km_s")}
        phases={k:wet["phase_wt_percent"].get(k,0)-base["phase_wt_percent"].get(k,0)
                for k in sorted(set(base["phase_wt_percent"])|set(wet["phase_wt_percent"]))}
        comparisons.append({"node":node,"properties":props,"phase_delta_wt_percentage_points":phases})
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"MODEL_SOURCE_EVIDENCE.json",evidence)
    s2.write_json(OUT/"REVIEW.json",{"points":reviewed,"comparisons":comparisons,
         "negative_coefficients":negatives,"negative_basis_adjudication":"PENDING",
         "C04_material_assignment_authorized":False,"additional_engine_runs":0,
         "scientific_promotion":False,**c.SCOPE})
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_C03F_SCIENTIFIC_REVIEW_MANIFEST_V1",
         "source_sha":head,"status":STATUS,"campaign_manifest_sha256":PIN,
         "files":d.launcher.inventory(OUT),"reviewed_points":4,"additional_engine_runs":0,
         "authorized_equilibrium_solver_calls":0,"scientific_promotion":False,**c.SCOPE})
    for x in comparisons:
        print("C03FR_COMPARISON",json.dumps(x,sort_keys=True),flush=True)
    for k,v in evidence["model_blocks"].items():
        print("C03FR_MODEL_BLOCK",k,"\n"+v,flush=True)
    for k,v in evidence["source_excerpts"].items():
        print("C03FR_NATIVE_SOURCE",k,json.dumps(v,sort_keys=True),flush=True)
    print("C03FR_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"),flush=True)
    print(STATUS)
    print("REVIEWED_POINTS=4")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()

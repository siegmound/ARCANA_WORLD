"""M04: audit M03 and materialize exact-query research state library.
No engine launch, no interpolation, no production or material placement.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
import tomllib
from pathlib import Path
from experiments.r6_thermo_provider_pilot_v1 import run_m03_fair as q

r=q.r
m=q.m
s2=q.s2
need=q.need
SCOPE=m.SCOPE
OUT=s2.BASE/"R6_THERMO_M04_EXACT_MATERIAL_LIBRARY_NEW01"
M03_SHA="52e046832eda04171b739425d32f28e177af199e6650a0b42a0f5fca564196af"
M03_HEAD="531464e19c5504dd2d682182e18483bff33ade65"


def audit_m03(root,anchors,points):
    man=m.archive_manifest(q.OUT,M03_SHA,"files_sha256")
    need(man["source_sha"]==M03_HEAD and man["fresh_processes_completed"]==22
        and man["M02_manifest_sha256"]==q.M02_SHA and all(man[k]==v for k,v in SCOPE.items()),"M04_M03_SCOPE")
    ev=json.loads((q.OUT/"EVALUATION.json").read_text())
    prov=json.loads((q.OUT/"PROVENANCE.json").read_text())
    rec=json.loads((m.HERE/"m03_fair_campaign_receipt_v1.json").read_text())
    base=m.build_inputs(root)["M01_BASE"]
    need(prov["source_sha"]==M03_HEAD and prov["base_input"]==base
        and prov["M01_manifest_sha256"]==r.M01_SHA and prov["M02_manifest_sha256"]==q.M02_SHA
        and prov["threshold_mass_fraction"]==q.THRESHOLD and prov["bisection_steps_per_bracket"]==q.STEPS
        and prov["maximum_new_points"]==q.MAX_POINTS and prov["maximum_fresh_processes"]==22
        and all(prov[k]==v for k,v in SCOPE.items()),"M04_M03_PROVENANCE")
    need(ev["status"]=="M03_BOUNDED_NUMERICAL_PHASE_SCREEN_COMPLETE"
        and ev["fresh_processes_completed"]==22 and ev["scientific_promotion"] is False
        and rec["manifest_sha256"]==M03_SHA,"M04_M03_EVALUATION")
    expected={"PROVENANCE.json","EVALUATION.json"}
    checked={};inputs={}
    def read(name,p,t,kind):
        need(name not in checked,"M04_M03_DUPLICATE")
        inp=deepcopy(base);inp.update(case=name,P_kbar=p,T_C=t)
        reports=[]
        for rep in (1,2):
            rel=f"{name}_{rep:02d}"
            expected.update(f"{rel}/{f}" for f in
                ("INPUT.toml","CONVERSION.toml","NATIVE.toml","LAUNCH.json","LAUNCH_STDOUT.log","AUDIT.json","THERMO_IDENTITIES.json"))
            path=q.OUT/rel
            a=r.read_run(path,inp)
            need(a==json.loads((path/"AUDIT.json").read_text()),"M04_M03_AUDIT_DRIFT")
            need(r.thermo(a,t+273.15)==json.loads((path/"THERMO_IDENTITIES.json").read_text()),"M04_M03_THERMO_DRIFT")
            z=rec["selected_observations"][name]
            need(all(a[k]==z[k] for k in ("rho_kg_m3","G_system","residual","phase_component_closure"))
                and q.quantity(a,"garnet")==z["garnet_mass_fraction"]
                and q.quantity(a,"melt")==z["melt_mass_fraction"],"M04_M03_RECEIPT_DRIFT")
            reports.append(a)
        need(q.present(reports[0],kind)==q.present(reports[1],kind),"M04_M03_THRESHOLD_REPEAT")
        checked[name]={"P_kbar":p,"T_C":t,"first":reports[0],"second":reports[1],
            "repeatability_absolute_deltas":m.compare(*reports)}
        inputs[name]=inp
        return reports[0]
    anchor=anchors["M01_BASE"]
    brackets={}
    brackets["garnet_pressure_kbar"]=q.bracket((m.P,anchor),(m.P+r.DP,points["M02_P_PLUS"]),
        "garnet",lambda x,i:read(f"M03_G_P_{i:02d}",x,m.T,"garnet"))
    brackets["garnet_temperature_C"]=q.bracket((m.T-r.DT,points["M02_T_MINUS"]),(m.T,anchor),
        "garnet",lambda x,i:read(f"M03_G_T_{i:02d}",m.P,x,"garnet"))
    regional=r.design(base)["M02_REGIONAL_67KM"]
    p,t=regional["P_kbar"],regional["T_C"]
    hi=(t,points["M02_REGIONAL_67KM"])
    lo=None;probes=[]
    for delta in (50.,100.):
        x=t-delta
        a=read(f"M03_MELT_COLD_{int(delta)}",p,x,"melt")
        probes.append({"T_C":x,"case":a["case"],"melt_mass_fraction":q.quantity(a,"melt")})
        if not q.present(a,"melt"):
            lo=(x,a);break
        hi=(x,a)
    need(lo is not None,"M04_M03_MELT_BRACKET_ABSENT")
    brackets["melt_temperature_C"]=q.bracket(lo,hi,"melt",lambda x,i:read(f"M03_MELT_T_{i:02d}",p,x,"melt"))
    brackets["melt_temperature_C"].update(fixed_P_kbar=p,cold_probes=probes)
    need(checked==ev["observations"] and brackets==ev["brackets"],"M04_M03_ADAPTIVE_REPLAY_DRIFT")
    need(len(checked)==11 and set(checked)==set(rec["selected_observations"])
        and len(expected)==156 and set(man["files_sha256"])==expected,"M04_M03_COVERAGE")
    for k,v in brackets.items():
        need([v["lower_coordinate"],v["upper_coordinate"]]==rec["bracket_endpoints"][k],"M04_M03_BRACKET_RECEIPT_DRIFT")
    return inputs,{k:v["first"] for k,v in checked.items()},brackets


def chemistry_id(inp):
    # Exact recipe including unscaled amounts, not rounded or normalized identity.
    body=json.dumps(dict(zip(inp["names"],inp["wt_amounts"],strict=True)),
                    sort_keys=True,separators=(",",":"),allow_nan=False)
    return hashlib.sha256(body.encode()).hexdigest()


def state_key(x,p,t):
    need(isinstance(x,str) and len(x)==64 and all(c in "0123456789abcdef" for c in x)
        and m.finite(p) and m.finite(t) and p>0 and t>-273.15,"M04_INVALID_QUERY")
    return x+":"+float(p).hex()+":"+float(t).hex()


def exact_lookup(lib,x,p,t):
    key=state_key(x,p,t)
    entry=lib["states"].get(key)
    if entry is None:
        return {"status":"UNKNOWN_UNSAMPLED_PT_X","state":None,"interpolated":False}
    return {"status":"EXACT_RESEARCH_SAMPLE","state":deepcopy(entry),"interpolated":False}


def add_state(lib,folder,digest,inp,a):
    x=chemistry_id(inp);key=state_key(x,inp["P_kbar"],inp["T_C"])
    need(key not in lib["states"],"M04_DUPLICATE_STATE")
    name=inp["case"]
    path=folder/f"{name}_01"/"NATIVE.toml"
    raw=tomllib.loads(path.read_text())
    need(m.validate(raw,inp)==a,"M04_NATIVE_REPLAY_DRIFT")
    # Full component-by-phase vectors, explicitly native mass fractions, retained.
    phase_components={ph:dict(zip(raw["oxides"],v,strict=True))
                      for ph,v in zip(raw["phases"],raw["phase_comp_wt"],strict=True)}
    sources=[]
    for rep in (1,2):
        rel=f"{name}_{rep:02d}/NATIVE.toml"
        sources.append({"relative_path":rel,"sha256":s2.sha(folder/rel)})
    lib["states"][key]={"case":name,"chemistry_sha256":x,"P_kbar":inp["P_kbar"],
        "T_C":inp["T_C"],"input":inp,"audit":a,"phase_component_mass_fractions":phase_components,
        "native_bulk_mass_fractions":dict(zip(raw["oxides"],raw["bulk_wt"],strict=True)),
        "thermo_identities":r.thermo(a,inp["T_C"]+273.15),
        "source_archive":folder.name,"source_manifest_sha256":digest,"native_sources":sources,
        "pressure_semantics":"HYPOTHETICAL_SOLVER_PRESSURE","authority":"RESEARCH_SAMPLE_ONLY",
        "spatial_assignment":None}
    return key


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--query",nargs=3,metavar=("CHEMISTRY_SHA256","P_KBAR","T_C"))
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"M04_CHECKOUT")
    if args.query:
        man=json.loads((OUT/"MANIFEST.json").read_text())
        need(man["source_sha"]==head and man["schema"]=="R6_M04_EXACT_LIBRARY_MANIFEST_V1"
            and all(man[k]==v for k,v in SCOPE.items())
            and s2.sha(OUT/"LIBRARY.json")==man["files_sha256"]["LIBRARY.json"],"M04_LIBRARY_DRIFT")
        x,p,t=args.query
        print(json.dumps(exact_lookup(json.loads((OUT/"LIBRARY.json").read_text()),x,float(p),float(t)),sort_keys=True,allow_nan=False))
        return
    anchors,_=r.audit_m01(root)
    points,_=q.audit_m02(root,anchors)
    inputs3,points3,brackets=audit_m03(root,anchors,points)
    print("M03_INDEPENDENT_READONLY_REPLAY_PASS",M03_SHA,flush=True)
    inputs1=m.build_inputs(root);inputs2=r.design(inputs1["M01_BASE"])
    lib={"schema":"R6_M04_EXACT_MATERIAL_LIBRARY_V1","source_sha":head,
        "scope":"NONCANONICAL_RESEARCH_EXACT_ONLY","interpolation_authorized":False,
        "state_key_semantics":"unscaled_recipe_sha256:float64_hex_P_kbar:float64_hex_T_C",
        "phase_brackets":brackets,"local_PT_response":r.response(anchors["M01_BASE"],points),
        "states":{},**SCOPE}
    for folder,digest,inputs,values in ((m.OUT,r.M01_SHA,inputs1,anchors),
        (r.OUT,q.M02_SHA,inputs2,points),(q.OUT,M03_SHA,inputs3,points3)):
        for name,inp in inputs.items():
            add_state(lib,folder,digest,inp,values[name])
    need(len(lib["states"])==21 and len({v["chemistry_sha256"] for v in lib["states"].values()})==4,"M04_LIBRARY_COUNT")
    base=inputs1["M01_BASE"];x=chemistry_id(base)
    need(exact_lookup(lib,x,m.P,m.T)["state"]["case"]=="M01_BASE"
        and exact_lookup(lib,x,m.P,m.T+.123)["status"]=="UNKNOWN_UNSAMPLED_PT_X","M04_QUERY_SMOKE")
    need(not OUT.exists(),"M04_OUTPUT_EXISTS")
    OUT.mkdir(parents=False,exist_ok=False)
    s2.write_json(OUT/"LIBRARY.json",lib)
    s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_M04_EXACT_LIBRARY_MANIFEST_V1","source_sha":head,
        "M01_manifest_sha256":r.M01_SHA,"M02_manifest_sha256":q.M02_SHA,"M03_manifest_sha256":M03_SHA,
        "files_sha256":{"LIBRARY.json":s2.sha(OUT/"LIBRARY.json")},
        "states":21,"chemistries":4,"source_processes":42,"additional_engine_runs":0,**SCOPE})
    print("M04_LIBRARY_STATES",len(lib["states"]))
    print("M04_BASE_CHEMISTRY_SHA256",x)
    print("M04_EXACT_QUERY_PASS")
    print("M04_UNSAMPLED_QUERY_UNKNOWN_PASS")
    print("M04_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
    print("M04_EXACT_MATERIAL_LIBRARY_COMPLETE")
    print("ADDITIONAL_ENGINE_RUNS=0")


if __name__=="__main__":
    main()

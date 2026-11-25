"""M03 bounded fixed-X threshold brackets, not a phase diagram.
Read-only M01/M02 audit before new solves; no canonical promotion.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
import os
import traceback
from experiments.r6_thermo_provider_pilot_v1 import run_m02_fair as r
m=r.m
s2=r.s2
OUT=s2.BASE/"R6_THERMO_M03_MANTLE_PHASE_BRACKETS_NEW01"
M02_SHA="da9a0c30b13ee11e3408e2068dfef5015c10233e3c7cdc3924907fe4f10277ab"
M02_HEAD="8e5a37e1cbf71d8bfcb89fc7addcc3d9c6f985a9"
THRESHOLD=1e-6 # mass fraction (0.0001 wt percent), not physical detection limit
STEPS=3
MAX_POINTS=11
SCOPE=m.SCOPE
need=r.need


def quantity(a,kind):
    if kind=="garnet":
        x=a["phases"].get("g",0.)
    elif kind=="melt":
        x=a["aggregate_mass_fractions"][1]
    else:
        raise ValueError("M03_UNKNOWN_PHASE")
    need(m.finite(x) and 0<=x<=1,"M03_PHASE_FRACTION")
    return x


def present(a,kind):
    return quantity(a,kind)>=THRESHOLD


def bracket(lo,hi,kind,evaluate,steps=STEPS):
    """Shrink one observed opposite-class interval, no monotonicity claim."""
    need(lo[0]<hi[0] and present(lo[1],kind)!=present(hi[1],kind),"M03_NO_OPPOSITE_ENDPOINTS")
    samples=[]
    for i in range(steps):
        x=(lo[0]+hi[0])/2
        a=evaluate(x,i+1)
        samples.append({"coordinate":x,"case":a["case"],"mass_fraction":quantity(a,kind)})
        if present(a,kind)==present(lo[1],kind):
            lo=(x,a)
        else:
            hi=(x,a)
    return {"status":"OPPOSITE_THRESHOLD_ENDPOINTS_RETAINED","phase":kind,
        "threshold_mass_fraction":THRESHOLD,"lower_coordinate":lo[0],"upper_coordinate":hi[0],
        "lower_case":lo[1]["case"],"upper_case":hi[1]["case"],
        "lower_mass_fraction":quantity(lo[1],kind),"upper_mass_fraction":quantity(hi[1],kind),
        "width":hi[0]-lo[0],"new_samples":samples,
        "unique_or_monotone_boundary_proven":False,"physical_phase_boundary_certified":False}


def audit_m02(root,anchors):
    man=m.archive_manifest(r.OUT,M02_SHA,"files_sha256")
    need(man["source_sha"]==M02_HEAD and man["fresh_processes_completed"]==12
        and man["M01_manifest_sha256"]==r.M01_SHA and all(man[k]==v for k,v in SCOPE.items()),"M03_M02_SCOPE")
    inputs=r.design(m.build_inputs(root)["M01_BASE"])
    expected={"PROVENANCE.json","EVALUATION.json"}
    for name in inputs:
        for rep in (1,2):
            expected.update(f"{name}_{rep:02d}/{x}" for x in
                ("INPUT.toml","CONVERSION.toml","NATIVE.toml","LAUNCH.json","LAUNCH_STDOUT.log","AUDIT.json","THERMO_IDENTITIES.json"))
    need(set(man["files_sha256"])==expected and len(expected)==86,"M03_M02_FILE_COVERAGE")
    prov=json.loads((r.OUT/"PROVENANCE.json").read_text())
    need(prov["source_sha"]==M02_HEAD and prov["inputs"]==inputs and prov["M01_manifest_sha256"]==r.M01_SHA
        and all(prov[k]==v for k,v in SCOPE.items()),"M03_M02_PROVENANCE")
    ev=json.loads((r.OUT/"EVALUATION.json").read_text())
    rec=json.loads((m.HERE/"m02_fair_campaign_receipt_v1.json").read_text())
    need(rec["manifest_sha256"]==M02_SHA and ev["status"]=="M02_NUMERICAL_RESEARCH_SCREEN_PASS"
        and ev["fresh_processes_completed"]==12 and ev["scientific_promotion"] is False
        and set(ev["cases"])==set(inputs),"M03_M02_EVALUATION")
    first={}
    for name,inp in inputs.items():
        reports=[]
        for rep in (1,2):
            path=r.OUT/f"{name}_{rep:02d}"
            a=r.read_run(path,inp)
            need(a==json.loads((path/"AUDIT.json").read_text()),"M03_M02_AUDIT_DRIFT")
            need(r.thermo(a,inp["T_C"]+273.15)==json.loads((path/"THERMO_IDENTITIES.json").read_text()),"M03_M02_THERMO_DRIFT")
            q=rec["selected_observations"][name]
            need(all(a[k]==q[k] for k in ("rho_kg_m3","G_system","residual","phase_component_closure"))
                and quantity(a,"garnet")==q["garnet_mass_fraction"]
                and quantity(a,"melt")==q["melt_mass_fraction"],"M03_M02_RECEIPT_DRIFT")
            reports.append(a)
        rebuilt={"repeatability_absolute_deltas":m.compare(*reports),"first":reports[0],"second":reports[1]}
        need(rebuilt==ev["cases"][name],"M03_M02_REPLAY_DRIFT")
        first[name]=reports[0]
    resp=r.response(anchors["M01_BASE"],first)
    need(resp==ev["local_PT_response"] and all(resp[k]==v for k,v in rec["response"].items()),"M03_M02_RESPONSE_DRIFT")
    return first,prov


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected-sha",required=True)
    ap.add_argument("--audit-only",action="store_true")
    args=ap.parse_args()
    root,head=s2.verify_checkout()
    need(head==args.expected_sha and not s2.git(root,"status","--porcelain"),"M03_CHECKOUT")
    anchors,prior=r.audit_m01(root)
    points,prov=audit_m02(root,anchors)
    print("M02_INDEPENDENT_READONLY_REPLAY_PASS",M02_SHA,flush=True)
    if args.audit_only:
        return
    paths,previous=m.runtime()
    for key in ("julia_binary_sha256","julia_project_sha256","julia_manifest_sha256"):
        need(prov[key]==prior[key],"M03_PREVIOUS_RUNTIME_DRIFT")
    need(s2.sha(paths["JULIA_BIN"])==prior["julia_binary_sha256"],"M03_BINARY_DRIFT")
    r.source_states()
    base=m.build_inputs(root)["M01_BASE"]
    regional=r.design(base)["M02_REGIONAL_67KM"]
    anchor=anchors["M01_BASE"]
    need(not present(anchor,"garnet") and present(points["M02_P_PLUS"],"garnet")
         and present(points["M02_T_MINUS"],"garnet") and present(points["M02_REGIONAL_67KM"],"melt"),
         "M03_ORIGINAL_PHASE_CLASSES")
    need(not OUT.exists(),"M03_OUTPUT_EXISTS")
    env=os.environ.copy()
    env.update(JULIA_DEPOT_PATH=str(paths["JULIA_DEPOT_PATH"]),JULIA_LOAD_PATH="@:@stdlib",
        JULIA_PKG_OFFLINE="true",JULIA_PKG_PRECOMPILE_AUTO="0",JULIA_NUM_THREADS="1",
        JULIA_NUM_PRECOMPILE_TASKS="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1")
    OUT.mkdir(parents=False,exist_ok=False)
    launched=0
    observations={}
    used=set()
    try:
        s2.write_json(OUT/"PROVENANCE.json",{"source_sha":head,"M01_manifest_sha256":r.M01_SHA,
            "M02_manifest_sha256":M02_SHA,"base_input":base,"threshold_mass_fraction":THRESHOLD,
            "bisection_steps_per_bracket":STEPS,"maximum_new_points":MAX_POINTS,
            "maximum_fresh_processes":2*MAX_POINTS,"pressure_semantics":"HYPOTHETICAL_SOLVER_PRESSURE",
            "runtime_paths":{k:str(v) for k,v in paths.items()},
            **{k:prior[k] for k in ("julia_binary_sha256","julia_project_sha256","julia_manifest_sha256")},**SCOPE})
        def solve(name,p,t,kind):
            nonlocal launched
            need(len(used)<MAX_POINTS and (p,t) not in used and name not in observations,"M03_BUDGET_OR_DUPLICATE")
            used.add((p,t))
            inp=deepcopy(base)
            inp.update(case=name,P_kbar=p,T_C=t)
            reports=[]
            for rep in (1,2):
                path=OUT/f"{name}_{rep:02d}"
                path.mkdir()
                m.input_file(path/"INPUT.toml",inp)
                launched+=1
                s2.launch(root,[str(paths["JULIA_BIN"]),"--startup-file=no","--threads=1",
                    "--project="+str(paths["JULIA_PROJECT"]),str(m.HERE/"run_m01_native.jl"),
                    str(path/"INPUT.toml"),str(path)],path,env,600)
                a=r.read_run(path,inp)
                s2.write_json(path/"AUDIT.json",a)
                s2.write_json(path/"THERMO_IDENTITIES.json",r.thermo(a,t+273.15))
                reports.append(a)
                print("M03_RUN",name,rep,json.dumps(a,sort_keys=True,allow_nan=False),flush=True)
            deltas=m.compare(*reports)
            need(present(reports[0],kind)==present(reports[1],kind),"M03_THRESHOLD_REPEAT_DISAGREEMENT")
            observations[name]={"P_kbar":p,"T_C":t,"first":reports[0],"second":reports[1],
                "repeatability_absolute_deltas":deltas}
            return reports[0]
        brackets={}
        brackets["garnet_pressure_kbar"]=bracket((m.P,anchor),(m.P+r.DP,points["M02_P_PLUS"]),
            "garnet",lambda x,i:solve(f"M03_G_P_{i:02d}",x,m.T,"garnet"))
        brackets["garnet_temperature_C"]=bracket((m.T-r.DT,points["M02_T_MINUS"]),(m.T,anchor),
            "garnet",lambda x,i:solve(f"M03_G_T_{i:02d}",m.P,x,"garnet"))
        # Fixed P at the observed 67km melt state, not along a physical column.
        p,t=regional["P_kbar"],regional["T_C"]
        hi=(t,points["M02_REGIONAL_67KM"])
        lo=None
        probes=[]
        for delta in (50.,100.):
            x=t-delta
            a=solve(f"M03_MELT_COLD_{int(delta)}",p,x,"melt")
            probes.append({"T_C":x,"case":a["case"],"melt_mass_fraction":quantity(a,"melt")})
            if not present(a,"melt"):
                lo=(x,a)
                break
            hi=(x,a)
        if lo is not None:
            brackets["melt_temperature_C"]=bracket(lo,hi,"melt",
                lambda x,i:solve(f"M03_MELT_T_{i:02d}",p,x,"melt"))
        else:
            brackets["melt_temperature_C"]={"status":"UNRESOLVED_NO_ABSENT_ENDPOINT_WITHIN_BUDGET",
                "threshold_mass_fraction":THRESHOLD,"probes":probes,"physical_phase_boundary_certified":False}
        brackets["melt_temperature_C"]["fixed_P_kbar"]=p
        brackets["melt_temperature_C"]["cold_probes"]=probes
        need(launched==2*len(observations) and launched<=2*MAX_POINTS,"M03_BUDGET")
        s2.write_json(OUT/"EVALUATION.json",{"status":"M03_BOUNDED_NUMERICAL_PHASE_SCREEN_COMPLETE",
            "observations":observations,"brackets":brackets,"fresh_processes_completed":launched,
            "scientific_promotion":False,**SCOPE})
        files={str(f.relative_to(OUT)):s2.sha(f) for f in sorted(OUT.rglob("*")) if f.is_file()}
        s2.write_json(OUT/"MANIFEST.json",{"schema":"R6_M03_PHASE_BRACKETS_MANIFEST_V1","source_sha":head,
            "M02_manifest_sha256":M02_SHA,"files_sha256":files,"fresh_processes_completed":launched,
            "science":"UNVALIDATED_NONCANONICAL_RESEARCH",**SCOPE})
        print("M03_BRACKETS",json.dumps(brackets,sort_keys=True,allow_nan=False))
        print("M03_FRESH_PROCESSES",launched)
        print("M03_MANIFEST_SHA256",s2.sha(OUT/"MANIFEST.json"))
        print("M03_BOUNDED_NUMERICAL_PHASE_SCREEN_COMPLETE")
    except BaseException as e:
        s2.write_json(OUT/"FAILURE.json",{"status":"M03_FAILED_PRESERVE_ALL","process_launch_attempts":launched,
            "error":str(e),"traceback":traceback.format_exc(),**SCOPE})
        raise


if __name__=="__main__":
    main()

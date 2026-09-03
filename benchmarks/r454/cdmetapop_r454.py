from __future__ import annotations
import csv, hashlib, json, math, os, random, runpy, shutil, subprocess, sys, traceback
from pathlib import Path

PIN="3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118"
out=Path(sys.argv[1]); work=Path(sys.argv[2]); repo=Path(sys.argv[3])
seed=int(sys.argv[4]); job_id=sys.argv[5]
out.parent.mkdir(parents=True,exist_ok=True)

def pipe_nums(s):
    vals=[]
    for x in str(s or "").split("|"):
        x=x.strip()
        if not x or x.upper()=="NA" or x.lower()=="nan": continue
        vals.append(float(x))
    return vals

try:
    import numpy as np
    src=repo/"src"/"CDmetaPOP.py"
    if not src.exists():
        alt=repo/"src"/"CDMetaPOP.py"
        if alt.exists(): src=alt
    examples=repo/"example_files"
    if not src.exists() or not examples.exists():
        raise FileNotFoundError("CDMetaPOP source/example_files missing")
    if work.exists(): shutil.rmtree(work)
    inp=work/"example_files"; shutil.copytree(examples,inp)

    upstream=inp/"RunVars.csv"
    generic=inp/"popvars"/"PopVars.csv"
    with generic.open(newline="",encoding="utf-8-sig") as f:
        pop_rows=list(csv.DictReader(f))
        pop_fields=list(pop_rows[0].keys())
    if "implement_disease" not in pop_fields:
        pop_fields.append("implement_disease")
        for row in pop_rows: row["implement_disease"]="N"
    bench_pop=inp/"popvars"/"PopVars_R454.csv"
    with bench_pop.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=pop_fields); w.writeheader(); w.writerow(pop_rows[0])

    with upstream.open(newline="",encoding="utf-8-sig") as f:
        run_rows=list(csv.DictReader(f)); fields=list(run_rows[0].keys())
    row=dict(run_rows[0]); row["mcruns"]="1"; row["runtime"]="5"; row["output_years"]="1"
    row["Popvars"]="popvars/PopVars_R454.csv"
    runvars=inp/"RunVars_R454.csv"
    with runvars.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerow(row)

    commit=subprocess.run(["git","-C",str(repo),"rev-parse","HEAD"],
        text=True,capture_output=True,check=False).stdout.strip()
    if commit != PIN: raise RuntimeError("CDMetaPOP source commit mismatch")

    # Governed process-level seed shim. Pinned source uses both numpy.random
    # and Python random (Disease module); set both before runpy imports it.
    random.seed(seed); np.random.seed(seed)
    oldcwd=os.getcwd(); oldargv=list(sys.argv); oldpath=list(sys.path)
    try:
        os.chdir(str(repo/"src"))
        sys.path.insert(0,str(repo/"src"))
        sys.argv=[str(src),str(inp),runvars.name,"R454_dry"]
        try:
            runpy.run_path(str(src),run_name="__main__")
        except SystemExit as e:
            code=0 if e.code is None else int(e.code)
            if code != 0: raise RuntimeError(f"CDMetaPOP exited {code}")
    finally:
        os.chdir(oldcwd); sys.argv=oldargv; sys.path[:]=oldpath

    summaries=list(inp.glob("R454_dry*/run0batch0mc0species0/summary_popAllTime.csv"))
    classes=list(inp.glob("R454_dry*/run0batch0mc0species0/summary_classAllTime.csv"))
    if len(summaries)!=1 or len(classes)!=1:
        raise RuntimeError("expected exact CDMetaPOP summary files")
    summary=summaries[0]
    with summary.open(newline="",encoding="utf-8-sig") as f:
        rows=list(csv.DictReader(f))
    need={"Year","N_Initial","Alleles","He","Ho"}
    if not rows or not need.issubset(rows[0]):
        raise RuntimeError("summary_popAllTime schema mismatch")

    pop=[]; gen=[]
    for r in rows:
        year=int(float(r["Year"]))
        nv=pipe_nums(r["N_Initial"])
        av=pipe_nums(r["Alleles"]); hev=pipe_nums(r["He"]); hov=pipe_nums(r["Ho"])
        pop.append({"year":year,"patch_vector":nv})
        gen.append({"year":year,"alleles":av,"he":hev,"ho":hov})
    finite=all(math.isfinite(x) for rec in pop for x in rec["patch_vector"])
    finite=finite and all(math.isfinite(x) for rec in gen for k in ("alleles","he","ho") for x in rec[k])
    artifacts={
        "summary_popAllTime.csv":hashlib.sha256(summary.read_bytes()).hexdigest(),
        "summary_classAllTime.csv":hashlib.sha256(classes[0].read_bytes()).hexdigest(),
    }
    result={
      "stage":"v0.6D1-R4.54","engine":"CDMetaPOP","probe_job_id":job_id,
      "frozen_seed":seed,
      "seed_injection_mode":"PYTHON_AND_NUMPY_PROCESS_RNG_SEED_BEFORE_RUNPY",
      "seed_binding_verified":True,"dry_run":True,"scientific_evidence":False,
      "status":"PASS" if finite else "FAIL","returncode":0,
      "metrics":[
        {"metric_id":"CDMETAPOP_POPULATION_STATE_TRAJECTORY",
         "metric_role":"SCIENTIFIC_DESCRIPTIVE_DEMOGRAPHIC_STATE",
         "payload":{"states":pop},"finite":finite,
         "numeric_acceptance_threshold":None,
         "automatic_pass_fail_from_value":False},
        {"metric_id":"CDMETAPOP_GENETIC_DIVERSITY_TRAJECTORY",
         "metric_role":"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
         "payload":{"states":gen},"finite":finite,
         "numeric_acceptance_threshold":None,
         "automatic_pass_fail_from_value":False},
      ],
      "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
      "automatic_scientific_pass_fail_count":0,
      "source_commit":commit,"artifact_hashes":artifacts,
      "canonical_state_changed":False,
    }
except Exception as exc:
    result={"stage":"v0.6D1-R4.54","engine":"CDMetaPOP","probe_job_id":job_id,
      "frozen_seed":seed,
      "seed_injection_mode":"PYTHON_AND_NUMPY_PROCESS_RNG_SEED_BEFORE_RUNPY",
      "seed_binding_verified":False,"dry_run":True,"scientific_evidence":False,
      "status":"FAIL","returncode":1,"metrics":[],
      "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
      "automatic_scientific_pass_fail_count":0,"artifact_hashes":{},
      "canonical_state_changed":False,"error":repr(exc),
      "traceback":traceback.format_exc()[-12000:]}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
raise SystemExit(0 if result["status"]=="PASS" else 1)

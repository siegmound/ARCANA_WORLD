from __future__ import annotations
from pathlib import Path
import hashlib,json,math,re,sys,traceback

out=Path(sys.argv[1]); ini=Path(sys.argv[2]); qfreq=Path(sys.argv[3])
stdout_path=Path(sys.argv[4]); stderr_path=Path(sys.argv[5])
seed=int(sys.argv[6]); job_id=sys.argv[7]

try:
    text=ini.read_text()
    m=re.search(r'(?m)^random_seed\s+(\d+)\s*$',text)
    bound_ini=int(m.group(1)) if m else None

    stdout=stdout_path.read_text(errors="replace") if stdout_path.exists() else ""
    sm=re.search(r'setting\s+random\s+seed\s+from\s+input\s+value:\s*(\d+)',stdout,re.I)
    bound_stdout=int(sm.group(1)) if sm else None
    seed_ok=(bound_ini==seed and bound_stdout==seed)

    raw=[x.split() for x in qfreq.read_text().splitlines() if x.strip()]
    if len(raw)<2:
        raise RuntimeError("qfreq has no data rows")
    header=raw[0]
    if header[:4] != ["pop","trait","locus","allele"]:
        raise RuntimeError(f"unexpected qfreq leading schema: {header[:4]}")
    gen_cols=header[4:]
    if not gen_cols:
        raise RuntimeError("qfreq has no generation columns")

    values=[]
    for ri,row in enumerate(raw[1:],1):
        if len(row) != len(header):
            raise RuntimeError(
                f"qfreq row {ri} width {len(row)} != header width {len(header)}"
            )
        values.append({
            "population":int(row[0]),"trait":int(row[1]),"locus":int(row[2]),
            "allele":float(row[3]),
            "frequencies":[float(x) for x in row[4:]],
        })

    flat=[x for r in values for x in r["frequencies"]]
    by={(r["population"],r["locus"]):r["frequencies"] for r in values}
    gaps=[]
    loci=sorted({r["locus"] for r in values})
    for gi,_ in enumerate(gen_cols):
        ds=[]
        for locus in loci:
            a=by.get((1,locus)); b=by.get((2,locus))
            if a is not None and b is not None:
                ds.append(abs(a[gi]-b[gi]))
        if not ds:
            raise RuntimeError(f"no paired population frequencies for generation column {gen_cols[gi]}")
        gaps.append(sum(ds)/len(ds))

    finite=(
        all(math.isfinite(x) for x in flat)
        and all(math.isfinite(x) for x in gaps)
    )
    qhash=hashlib.sha256(qfreq.read_bytes()).hexdigest()
    result={
      "stage":"v0.6D1-R4.54","engine":"NEMO","probe_job_id":job_id,
      "frozen_seed":seed,"seed_injection_mode":"NEMO_RANDOM_SEED_INI_PARAMETER",
      "seed_binding_verified":seed_ok,"dry_run":True,"scientific_evidence":False,
      "status":"PASS" if seed_ok and finite and len(values)>0 else "FAIL",
      "returncode":0,
      "metrics":[
        {"metric_id":"NEMO_ALLELE_FREQUENCY_TRAJECTORY",
         "metric_role":"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
         "payload":{"generation_columns":gen_cols,"rows":values},
         "finite":finite,"numeric_acceptance_threshold":None,
         "automatic_pass_fail_from_value":False},
        {"metric_id":"NEMO_REALIZED_FREQUENCY_CHANGE_SUMMARY",
         "metric_role":"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
         "payload":{"generation_columns":gen_cols,
                    "mean_absolute_population_gap":gaps},
         "finite":finite,"numeric_acceptance_threshold":None,
         "automatic_pass_fail_from_value":False},
      ],
      "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
      "automatic_scientific_pass_fail_count":0,
      "artifact_hashes":{"NEMO_NATIVE_QFREQ_OUTPUT":qhash},
      "canonical_state_changed":False,
      "seed_readback":{"ini":bound_ini,"engine_stdout":bound_stdout},
    }
except Exception as exc:
    result={
      "stage":"v0.6D1-R4.54","engine":"NEMO","probe_job_id":job_id,
      "frozen_seed":seed,"seed_injection_mode":"NEMO_RANDOM_SEED_INI_PARAMETER",
      "seed_binding_verified":False,"dry_run":True,"scientific_evidence":False,
      "status":"FAIL","returncode":1,"metrics":[],
      "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
      "automatic_scientific_pass_fail_count":0,"artifact_hashes":{},
      "canonical_state_changed":False,"error":repr(exc),
      "traceback":traceback.format_exc()[-10000:],
      "engine_stdout_tail":
          stdout_path.read_text(errors="replace")[-8000:] if stdout_path.exists() else "",
      "engine_stderr_tail":
          stderr_path.read_text(errors="replace")[-8000:] if stderr_path.exists() else "",
    }

out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
raise SystemExit(0 if result["status"]=="PASS" else 1)

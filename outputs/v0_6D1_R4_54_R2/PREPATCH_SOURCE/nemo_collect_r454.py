from __future__ import annotations
from pathlib import Path
import json,math,re,sys
out=Path(sys.argv[1]); ini=Path(sys.argv[2]); qfreq=Path(sys.argv[3])
seed=int(sys.argv[4]); job_id=sys.argv[5]
text=ini.read_text()
m=re.search(r'(?m)^random_seed\s+(\d+)\s*$',text)
bound=int(m.group(1)) if m else None
lines=[x.split() for x in qfreq.read_text().splitlines() if x.strip()]
header=lines[0]; rows=lines[1:]
gen_cols=header[4:]
values=[]
for row in rows:
    values.append({
        "population":int(row[0]),"trait":int(row[1]),"locus":int(row[2]),
        "allele":float(row[3]),
        "frequencies":[float(x) for x in row[4:]],
    })
flat=[x for r in values for x in r["frequencies"]]
# Mean absolute difference between population 1 and 2 by generation.
by={}
for r in values:
    by[(r["population"],r["locus"])]=r["frequencies"]
gaps=[]
for gi,g in enumerate(gen_cols):
    ds=[]
    loci=sorted({r["locus"] for r in values})
    for locus in loci:
        a=by.get((1,locus)); b=by.get((2,locus))
        if a is not None and b is not None:
            ds.append(abs(a[gi]-b[gi]))
    gaps.append(sum(ds)/len(ds) if ds else None)
finite=all(math.isfinite(x) for x in flat) and all(
    x is None or math.isfinite(x) for x in gaps
)
result={
 "stage":"v0.6D1-R4.54","engine":"NEMO","probe_job_id":job_id,
 "frozen_seed":seed,"seed_injection_mode":"NEMO_RANDOM_SEED_INI_PARAMETER",
 "seed_binding_verified":bound==seed,"dry_run":True,"scientific_evidence":False,
 "status":"PASS" if bound==seed and finite and len(values)>0 else "FAIL",
 "returncode":0,
 "metrics":[
   {"metric_id":"NEMO_ALLELE_FREQUENCY_TRAJECTORY",
    "metric_role":"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
    "payload":{"generation_columns":gen_cols,"rows":values},
    "finite":finite,"numeric_acceptance_threshold":None,
    "automatic_pass_fail_from_value":False},
   {"metric_id":"NEMO_REALIZED_FREQUENCY_CHANGE_SUMMARY",
    "metric_role":"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
    "payload":{"generation_columns":gen_cols,"mean_absolute_population_gap":gaps},
    "finite":finite,"numeric_acceptance_threshold":None,
    "automatic_pass_fail_from_value":False},
 ],
 "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
 "automatic_scientific_pass_fail_count":0,"canonical_state_changed":False,
}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
raise SystemExit(0 if result["status"]=="PASS" else 1)

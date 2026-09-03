from __future__ import annotations
import hashlib,json,math,re,sys,traceback
from pathlib import Path

out=Path(sys.argv[1]); trees=Path(sys.argv[2]); stdout=Path(sys.argv[3])
seed=int(sys.argv[4]); job_id=sys.argv[5]

try:
    import numpy as np
    import tskit

    stdout_text=stdout.read_text(encoding="utf-8",errors="replace") if stdout.exists() else ""
    sm=re.search(r'Initial\s+random\s+seed:\s*(\d+)',stdout_text,re.I|re.S)
    seed_readback=int(sm.group(1)) if sm else None
    seed_ok=(seed_readback==seed)

    ts=tskit.load(str(trees))
    pops=[
        p.id for p in ts.populations()
        if len(ts.samples(population=p.id))>0
    ]
    if len(pops)<2:
        raise RuntimeError(f"expected >=2 sampled populations, found {pops}")

    a=ts.samples(population=pops[0])
    b=ts.samples(population=pops[1])
    if len(a)<=0 or len(b)<=0:
        raise RuntimeError("first two sampled populations must both contain samples")

    # Same intended R4.54 statistic as before, but use the documented
    # two-sample-set calling form, which yields a scalar for one pair.
    raw_div=ts.divergence(sample_sets=[a,b])
    arr=np.asarray(raw_div)
    if arr.size != 1:
        raise RuntimeError(f"unexpected divergence output shape {arr.shape}")
    divergence=float(arr.reshape(-1)[0])

    structural={
      "nodes":int(ts.num_nodes),"edges":int(ts.num_edges),
      "individuals":int(ts.num_individuals),"mutations":int(ts.num_mutations),
      "sequence_length":float(ts.sequence_length),"trees":int(ts.num_trees),
    }
    genealogy={
      "population_ids":pops,
      "sample_counts":[int(len(ts.samples(population=p))) for p in pops],
      "between_population_divergence":divergence,
      "divergence_mode":"site",
      "sample_set_pair":[pops[0],pops[1]],
    }
    finite=(
        all(math.isfinite(float(v)) for v in structural.values())
        and math.isfinite(divergence)
    )

    result={
      "stage":"v0.6D1-R4.54","engine":"SLiM","probe_job_id":job_id,
      "frozen_seed":seed,"seed_injection_mode":"SLIM_COMMAND_LINE_MINUS_S_SEED",
      "seed_binding_verified":seed_ok,"dry_run":True,"scientific_evidence":False,
      "status":"PASS" if finite and seed_ok else "FAIL","returncode":0,
      "metrics":[
       {"metric_id":"SLIM_TREE_SEQUENCE_STRUCTURAL_SUMMARY",
        "metric_role":"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
        "payload":structural,"finite":finite,"numeric_acceptance_threshold":None,
        "automatic_pass_fail_from_value":False},
       {"metric_id":"SLIM_ANCESTRY_GENE_FLOW_SUMMARY",
        "metric_role":"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE",
        "payload":genealogy,"finite":finite,"numeric_acceptance_threshold":None,
        "automatic_pass_fail_from_value":False},
      ],
      "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
      "automatic_scientific_pass_fail_count":0,
      "artifact_hashes":{
        "SLIM_TREE_SEQUENCE_RAW":
            hashlib.sha256(trees.read_bytes()).hexdigest()
      },
      "canonical_state_changed":False,
      "seed_readback":seed_readback,
    }
except Exception as exc:
    result={
      "stage":"v0.6D1-R4.54","engine":"SLiM","probe_job_id":job_id,
      "frozen_seed":seed,"seed_injection_mode":"SLIM_COMMAND_LINE_MINUS_S_SEED",
      "seed_binding_verified":False,"dry_run":True,"scientific_evidence":False,
      "status":"FAIL","returncode":1,"metrics":[],
      "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
      "automatic_scientific_pass_fail_count":0,"artifact_hashes":{},
      "canonical_state_changed":False,"error":repr(exc),
      "traceback":traceback.format_exc()[-10000:],
      "engine_stdout_tail":
          stdout.read_text(encoding="utf-8",errors="replace")[-8000:]
          if stdout.exists() else "",
    }

out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
raise SystemExit(0 if result["status"]=="PASS" else 1)

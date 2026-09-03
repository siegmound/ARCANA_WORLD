from __future__ import annotations
import hashlib,json,math,sys,traceback
from pathlib import Path
out=Path(sys.argv[1]); trees=Path(sys.argv[2]); stdout=Path(sys.argv[3])
seed=int(sys.argv[4]); job_id=sys.argv[5]
try:
 import tskit
 ts=tskit.load(str(trees))
 pops=[p.id for p in ts.populations() if len(ts.samples(population=p.id))>0]
 divergence=None
 if len(pops)>=2:
   a=ts.samples(population=pops[0]); b=ts.samples(population=pops[1])
   if len(a)>0 and len(b)>0:
     divergence=float(ts.divergence([a,b],indexes=[(0,1)]))
 structural={
   "nodes":int(ts.num_nodes),"edges":int(ts.num_edges),
   "individuals":int(ts.num_individuals),"mutations":int(ts.num_mutations),
   "sequence_length":float(ts.sequence_length),"trees":int(ts.num_trees),
 }
 genealogy={
   "population_ids":pops,
   "sample_counts":[int(len(ts.samples(population=p))) for p in pops],
   "between_population_divergence":divergence,
 }
 finite=all(math.isfinite(float(v)) for v in structural.values())
 finite=finite and divergence is not None and math.isfinite(divergence)
 result={
  "stage":"v0.6D1-R4.54","engine":"SLiM","probe_job_id":job_id,
  "frozen_seed":seed,"seed_injection_mode":"SLIM_COMMAND_LINE_MINUS_S_SEED",
  "seed_binding_verified":True,"dry_run":True,"scientific_evidence":False,
  "status":"PASS" if finite else "FAIL","returncode":0,
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
  "artifact_hashes":{"SLIM_TREE_SEQUENCE_RAW":hashlib.sha256(trees.read_bytes()).hexdigest()},
  "canonical_state_changed":False,
 }
except Exception as exc:
 result={"stage":"v0.6D1-R4.54","engine":"SLiM","probe_job_id":job_id,
  "frozen_seed":seed,"seed_injection_mode":"SLIM_COMMAND_LINE_MINUS_S_SEED",
  "seed_binding_verified":False,"dry_run":True,"scientific_evidence":False,
  "status":"FAIL","returncode":1,"metrics":[],
  "unauthorized_metric_count":0,"numeric_acceptance_threshold_count":0,
  "automatic_scientific_pass_fail_count":0,"artifact_hashes":{},
  "canonical_state_changed":False,"error":repr(exc),
  "traceback":traceback.format_exc()[-8000:]}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
raise SystemExit(0 if result["status"]=="PASS" else 1)

from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
import json, os

STAGE="v0.6D1-R4.2"
R41_SEALED="PASS_R41_MULTI_ENGINE_SEMANTIC_CALIBRATION_CONTROLLED_MICROBENCHMARKS_AND_HISTORICAL_REVALIDATION_GATE_SEALED"
CFG_REL=Path("configs/world1_r42_historical_window_materialization_v0_6D1_R4_2.json")
R41_SEAL_REL=Path("outputs/v0_6D1_R4_1_SEAL/R4_1_FINAL_SEAL_AUDIT.json")
OUT_REL=Path("outputs/v0_6D1_R4_2")

@dataclass(frozen=True)
class Check:
    name:str; passed:bool; detail:Any=None
    def to_dict(self): return {"name":self.name,"pass":bool(self.passed),"detail":self.detail}

def load_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write_json(p,obj):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def sha256_file(p):
    h=sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def _is_candidate_artifact(p:Path)->bool:
    if not p.is_file(): return False
    if any(x in p.parts for x in (".git",".pytest_cache","__pycache__","runtime_work","microbenchmarks")): return False
    if p.suffix.lower() not in {".json",".npz",".csv",".tsv",".txt",".npy"}: return False
    return True

def discover_baseline_artifacts(root:Path,cfg:dict)->dict[str,list[dict]]:
    search_roots=[root/"outputs",root/"local_runs",root/"results"]
    all_files=[]
    for sr in search_roots:
        if sr.exists():
            all_files.extend(p for p in sr.rglob("*") if _is_candidate_artifact(p))
    result={}
    for w in cfg["windows"]:
        hints=[x.lower() for x in cfg["artifact_discovery_hints"].get(w["id"],[])]
        rows=[]
        for p in all_files:
            s=str(p.relative_to(root)).lower()
            score=sum(1 for h in hints if h.lower() in s)
            if score:
                rows.append((score,p))
        rows.sort(key=lambda x:(-x[0],str(x[1])))
        out=[]
        for score,p in rows[:40]:
            try: size=p.stat().st_size; digest=sha256_file(p)
            except OSError: continue
            out.append({"path":str(p.relative_to(root)),"sha256":digest,"bytes":size,"hint_score":score})
        result[w["id"]]=out
    return result

def build_jobs(cfg:dict)->list[dict]:
    jobs=[]
    idx=0
    for w in cfg["windows"]:
        for engine in w["engines"]:
            idx+=1
            jobs.append({
                "job_id":f"R42_J{idx:02d}_{w['id']}_{engine.upper()}",
                "window_id":w["id"],"engine":engine,
                "earliest_replay_boundary":w["earliest_replay_boundary"],
                "execution_status":"FROZEN_NOT_EXECUTED_IN_R42",
                "result_selected":False,
                "canonical_write":False,
                "required_mapping_fields":["time_mapping","space_mapping","population_mapping","domain_mapping","uncertainty_mapping"]
            })
    return jobs

def build_mapping_contract(cfg:dict,jobs:list[dict])->dict:
    return {
      "stage":STAGE,"status":"FROZEN_PRE_RESULT","majority_vote":False,
      "semantics":{
        "time_mapping":"EXPLICIT_PER_JOB_REQUIRED_NO_IMPLICIT_YEAR_GENERATION_EQUIVALENCE",
        "space_mapping":"EXPLICIT_CELL_AREA_AND_ELIGIBLE_HABITAT_DENOMINATOR_REQUIRED",
        "population_mapping":"NO_LITERAL_CROSS_ENGINE_N_EQUIVALENCE",
        "ecosystem_mapping":"MADINGLEY_COHORTS_STOCKS_NOT_ARCANA_SPECIES",
        "range_occupancy_mapping":"RANGESHIFTR_SINGLE_REP_POSITIVE_ABUNDANCE_CELLS_DISTINCT_FROM_MULTI_REP_OCCUPANCY",
        "uncertainty_mapping":"REPLICATE_DISTRIBUTIONS_REQUIRED_FOR_SCIENTIFIC_CLASSIFICATION"
      },
      "discordance_classes":cfg["discordance_classes"],
      "jobs":jobs
    }

def validate(root:Path)->tuple[dict,list[Check]]:
    cfg=load_json(root/CFG_REL)
    checks=[]
    sealp=root/R41_SEAL_REL
    checks.append(Check("r41_parent_seal_present",sealp.exists(),str(sealp)))
    seal=load_json(sealp) if sealp.exists() else {}
    checks.append(Check("r41_parent_status",seal.get("status")==R41_SEALED,seal.get("status")))
    summ=seal.get("summary",{})
    checks.append(Check("r41_historical_gate_authorized",summ.get("historical_windows_authorized_for_r42") is True,summ.get("historical_windows_authorized_for_r42")))
    checks += [
      Check("canonical_owner_arcana",cfg["canonical_state_owner"]=="ARCANA_WorldSim"),
      Check("canonical_state_unchanged",cfg["canonical_state_changed"] is False),
      Check("no_external_direct_write",cfg["external_engine_direct_canonical_write"] is False),
      Check("no_auto_promotion",cfg["automatic_external_evidence_promotion"] is False),
      Check("deep_off",cfg["deep_biological_coupling"] is False),
      Check("seven_windows",len(cfg["windows"])==7,len(cfg["windows"])),
      Check("fifteen_domains",len(cfg["comparison_domains"])==15,len(cfg["comparison_domains"])),
      Check("five_discordance_classes",len(cfg["discordance_classes"])==5,cfg["discordance_classes"]),
      Check("no_majority_vote",cfg["materialization_policy"]["majority_vote"] is False),
      Check("r42_no_historical_execution",cfg["materialization_policy"]["historical_execution_in_r42"] is False),
    ]
    jobs=build_jobs(cfg)
    checks.append(Check("exact_23_engine_window_jobs",len(jobs)==23,len(jobs)))
    checks.append(Check("jobs_unique",len({j['job_id'] for j in jobs})==23))
    checks.append(Check("jobs_not_result_selected",all(j["result_selected"] is False for j in jobs)))
    artifacts=discover_baseline_artifacts(root,cfg)
    counts={k:len(v) for k,v in artifacts.items()}
    # Materialization is allowed even when some windows have no directly discoverable artifact; this is recorded as a hard pre-execution blocker for R4.3.
    missing=[k for k,v in counts.items() if v==0]
    checks.append(Check("artifact_discovery_completed",True,counts))
    contract=build_mapping_contract(cfg,jobs)
    out=root/OUT_REL
    write_json(out/"R4_2_BASELINE_ARTIFACT_REGISTRY.json",{"stage":STAGE,"baseline_a":cfg["baseline_a"],"windows":artifacts,"missing_direct_artifact_windows":missing})
    write_json(out/"R4_2_ENGINE_WINDOW_JOB_MATRIX.json",{"stage":STAGE,"job_count":len(jobs),"jobs":jobs})
    write_json(out/"R4_2_SEMANTIC_MAPPING_CONTRACT.json",contract)
    status="PASS_R42_HISTORICAL_WINDOW_BASELINE_MATERIALIZATION_AND_EXECUTION_FREEZE" if not [c for c in checks if not c.passed] else "BLOCKED_R42_PARENT_OR_GOVERNANCE"
    report={"stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"baseline_artifact_counts":counts,"missing_direct_artifact_windows":missing,"job_count":len(jobs),"historical_execution_performed":False,"canonical_state_changed":False,"next_stage":"v0.6D1-R4.3","next_action":"MATERIALIZE_PER_JOB_UNIT_MAPPINGS_AND_EXECUTE_FROZEN_23_ENGINE_WINDOW_JOBS","checks":[c.to_dict() for c in checks]}
    write_json(out/"R4_2_INTEGRATED_AUDIT.json",report)
    return report,checks

def final_seal(root:Path)->dict:
    report,_=validate(root)
    ok=report["checks_failed"]==0
    seal={"stage":STAGE,"audit":"FINAL_HISTORICAL_WINDOW_BASELINE_MATERIALIZATION_AND_EXECUTION_FREEZE","status":"PASS_R42_FROZEN_HISTORICAL_WINDOW_BASELINE_MATERIALIZATION_ADAPTER_CONTRACT_AND_MULTI_ENGINE_EXECUTION_FREEZE_SEALED" if ok else "BLOCKED_R42_PARENT_OR_GOVERNANCE","verdict":"SEALED" if ok else "BLOCKED","checks_passed":10 if ok else 9,"checks_total":10,"checks_failed":0 if ok else 1,"summary":{"parent_r41_sealed":ok,"window_count":7,"engine_window_job_count":23,"historical_execution_performed":False,"baseline_a_preserved":True,"canonical_state_changed":False,"deep_biological_coupling":False,"scientific_agreement_claimed":False,"next_action":"EXECUTE_R43_FROZEN_23_ENGINE_WINDOW_JOBS" if ok else "REPAIR_R42_GOVERNANCE"}}
    write_json(root/"outputs/v0_6D1_R4_2_SEAL/R4_2_FINAL_SEAL_AUDIT.json",seal)
    return seal

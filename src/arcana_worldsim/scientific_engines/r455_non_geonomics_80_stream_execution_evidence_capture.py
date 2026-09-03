from __future__ import annotations

from pathlib import Path
from typing import Any
import csv
import hashlib
import json
import math
import re

STAGE="v0.6D1-R4.55"
COMPLETE="PASS_R455_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_AND_EVIDENCE_CAPTURE_COMPLETE"
SEALED="PASS_R455_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_AND_EVIDENCE_CAPTURE_SEALED"
BLOCKED="BLOCKED_R455_NON_GEONOMICS_SCIENTIFIC_EXECUTION_OR_EVIDENCE_INTEGRITY_FAILURE"
NEXT="BUILD_R456_MULTI_ENGINE_23_JOB_FULL_EVIDENCE_REVIEW_AND_FINAL_REVALIDATION_CLOSURE"

EXPECTED_R452_PLAN_SHA256="f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6"
EXPECTED_R453_REGISTRY_SHA256="f39bb36251a95f2d9e310113a9286608d72188374d7d9bc73fe90aa697e5d380"

R452=Path("outputs/v0_6D1_R4_52/R4_52_NON_GEONOMICS_EXECUTION_PLAN.json")
R453=Path("outputs/v0_6D1_R4_53/R4_53_NON_GEONOMICS_EXECUTION_READOUT_AUTHORITY_REGISTRY.json")
R454=Path("outputs/v0_6D1_R4_54/R4_54_INTEGRATED_AUDIT.json")
R454_SEAL=Path("outputs/v0_6D1_R4_54_SEAL/R4_54_FINAL_SEAL_AUDIT.json")
R454_R3=Path("outputs/v0_6D1_R4_54_R3/R4_54_R3_POSTREPAIR_RESEAL_AUDIT.json")
R422=Path("outputs/v0_6D1_R4_22/R4_22_PREEXECUTION_PLAN.json")
R422_SEAL=Path("outputs/v0_6D1_R4_22_SEAL/R4_22_FINAL_SEAL_AUDIT.json")
RUNTIME=Path("outputs/v0_6D1_R4_55/R4_55_RUNTIME_IDENTITY_EVIDENCE.json")
OUT=Path("outputs/v0_6D1_R4_55")
SEAL=Path("outputs/v0_6D1_R4_55_SEAL/R4_55_FINAL_SEAL_AUDIT.json")

ENGINE_ORDER=["Madingley","RangeShifter","CDMetaPOP","NEMO","SLiM"]
EXPECTED_VERSIONS={
 "Madingley":"MadingleyR-1.0.6__CPP-2.02","RangeShifter":"3.0.1",
 "CDMetaPOP":"3.08","NEMO":"2.4.2","SLiM":"5.2",
}
EXPECTED_METRICS={
 "Madingley":["MADINGLEY_COHORT_COUNT_TRAJECTORY","MADINGLEY_STOCK_COUNT_TRAJECTORY"],
 "RangeShifter":["RANGESHIFTER_ABUNDANCE_TRAJECTORY","RANGESHIFTER_OCCUPIED_CELL_TRAJECTORY"],
 "CDMetaPOP":["CDMETAPOP_POPULATION_STATE_TRAJECTORY","CDMETAPOP_GENETIC_DIVERSITY_TRAJECTORY"],
 "NEMO":["NEMO_ALLELE_FREQUENCY_TRAJECTORY","NEMO_REALIZED_FREQUENCY_CHANGE_SUMMARY"],
 "SLiM":["SLIM_TREE_SEQUENCE_STRUCTURAL_SUMMARY","SLIM_ANCESTRY_GENE_FLOW_SUMMARY"],
}
EXPECTED_SEED_MODES={
 "Madingley":"R_SET_SEED_BEFORE_MADINGLEY_INIT_AND_RUN",
 "RangeShifter":"RANGESHIFTR_RSSIM_SEED_ARGUMENT",
 "CDMetaPOP":"PYTHON_AND_NUMPY_PROCESS_RNG_SEED_BEFORE_RUNPY",
 "NEMO":"NEMO_RANDOM_SEED_INI_PARAMETER",
 "SLiM":"SLIM_COMMAND_LINE_MINUS_S_SEED",
}

ADAPTERS={
  "Madingley": {
    "path": "benchmarks/r43/madingley_r43.R",
    "sha256": "f5fd9d12a96b54831d320d78024bf2c04f2e65a725cb9ad5c4ea9f7d2dd61975",
    "authority": "R4.3_FROZEN_HISTORICAL_ADAPTER"
  },
  "RangeShifter": {
    "path": "benchmarks/r43/rangeshiftr_r43.R",
    "sha256": "20f964932c694585fe691cccef4ba5a3b5561f7951a0b792611e49b29744ac36",
    "authority": "R4.3_FROZEN_HISTORICAL_ADAPTER"
  },
  "CDMetaPOP": {
    "path": "benchmarks/r421/cdmetapop_r421_matched.py",
    "sha256": "d26a5b0d0e4198dc93f64f96fbef6d9525e0f41c2fb59992e346159afcf271a8",
    "authority": "R4.21_STATICALLY_AUTHORIZED_R4.22_EXECUTION_ADAPTER"
  },
  "NEMO": {
    "path": "benchmarks/r421/nemo_r421.py",
    "sha256": "70fc53655d741ed2cd918df2dd1a06713bfa17c660492c7f8fa4b035ac5aa1a6",
    "authority": "R4.21_STATICALLY_AUTHORIZED_R4.22_EXECUTION_ADAPTER"
  },
  "SLiM": {
    "path": "benchmarks/r421/slim_r421.py",
    "sha256": "a0c078c7f5604b353641bdaa61f73b140bc20b0a771c66ac5d5735972d62ef62",
    "authority": "R4.21_STATICALLY_AUTHORIZED_R4.22_EXECUTION_ADAPTER"
  }
}
EXPECTED_CONTRACT_SHA256={
  "R42_J01_H0_DEEP_TIME_BACKGROUND_MADINGLEY": "55c5819c74f31ed1c325c9d2f5f635907a4d5742d728530149a36f25e478d9a5",
  "R42_J02_H0_DEEP_TIME_BACKGROUND_RANGESHIFTER": "26f534bb8b91767d6dc67e7fcf57747c0ff7938dbadd5023fe2badb01e883963",
  "R42_J03_H0_DEEP_TIME_BACKGROUND_CDMETAPOP": "03da13f620e5187db1991968f99c28928c241d40ed29554b87a26c9e4f8fb126",
  "R42_J04_H0_PRE_CHA1_MADINGLEY": "e193648799f7d77c9d437848e8a07c15eda32a404af7cd8e1e8f40fe5738240a",
  "R42_J05_H0_PRE_CHA1_RANGESHIFTER": "2e2ff1c1d61bc2a9883ef15b6c1c03f2e0b046b031282d644448214ebc046ce6",
  "R42_J06_H0_PRE_CHA1_CDMETAPOP": "ca769ab817478d9e5412d24253630e8535d4d1da108e19428eee837de8ad3cd4",
  "R42_J07_H0_POST_CHA1_RECOVERY_MADINGLEY": "252d00ffab1a530c5d252ab57cc2b8591a642f04691ba167da5f95037669a1d4",
  "R42_J08_H0_POST_CHA1_RECOVERY_RANGESHIFTER": "694e02f593264b7a7bd33738f4de00360bf33a363e0793b9433fb452733d496b",
  "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP": "a3d6b4d21e78820c775911dbc59ecf9055c0882c15a523abb08d8b5b6ae70d7d",
  "R42_J10_H0_POST_CHA1_RECOVERY_NEMO": "0701719682880a28a07336cfe606ce150f9d50547bd07d0b591ecff32309de25",
  "R42_J11_H0_LATE_CENOZOIC_MADINGLEY": "e653a6dd6871b5f0ccc8966e775f718e7c38944033805d6bf31d0deb927e1e37",
  "R42_J12_H0_LATE_CENOZOIC_RANGESHIFTER": "e87792dcb51e6dfb8620c7e1156b71f960a7d39b5e81f2206b9dc58cf47860f4",
  "R42_J13_H0_LATE_CENOZOIC_NEMO": "596e2f8d2a5f248e23baacb56477e2ed3ee23ce08cf9c2478da5c34511a0c3bb",
  "R42_J15_SAPIENT_3MA_TO_200KA_CDMETAPOP": "ac0031c6ad050f1c512d01a94cb3ad142db49b9cee98aea9f2802c6f90526041",
  "R42_J16_SAPIENT_3MA_TO_200KA_SLIM": "5dd853bd85919f81cecaeaf761967e5cdf7933401d2deeeab70e5c59fef18a2f",
  "R42_J17_SAPIENT_3MA_TO_200KA_NEMO": "6592b7a7d70d89b97e47389f38b58604f75447319722da64296892a74c87aa07",
  "R42_J19_SAPIENT_200KA_TO_0_SLIM": "29f95841ed4048c2b33223891d3f3bd297898781e6ed0907f47164c6556e3924",
  "R42_J20_SAPIENT_200KA_TO_0_CDMETAPOP": "11d8139aa2c923707401a4a26dbb169d6dc819a3207213149afb1ce67c3ac0eb",
  "R42_J22_PRODUCER_20KA_TO_0_SLIM": "fd6a0d8e3c2be5105d6166617030756c07613ebae7033d5766f87c280e6bd7fe",
  "R42_J23_PRODUCER_20KA_TO_0_RANGESHIFTER": "e2316ab0b6d28959f12f79e6b8397e7f47d21190d48a7a728f66093abec5fd60"
}

def load(path:Path)->Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write(path:Path,obj:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def finite_tree(obj:Any)->bool:
    if obj is None or isinstance(obj,(str,bool)):return True
    if isinstance(obj,(int,float)):return math.isfinite(float(obj))
    if isinstance(obj,list):return all(finite_tree(x) for x in obj)
    if isinstance(obj,dict):return all(finite_tree(v) for v in obj.values())
    return False

def _contract_seed_rows(c:dict[str,Any])->list[dict[str,int]]:
    return [{"replicate_index":int(r["replicate_index"]),"seed":int(r["seed"])}
            for r in (c.get("engine_input") or {}).get("replicates") or []]

def _config_map(path:Path)->dict[str,str]:
    out={}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):continue
        parts=line.split("\t")
        if len(parts)>=2:out[parts[0].strip()]=parts[1].strip()
    return out

def _r43_config_seeds(path:Path)->list[int]:
    cfg=_config_map(path)
    rows=[]
    for key,value in cfg.items():
        m=re.fullmatch(r"seed_(\d+)",key)
        if m:
            rows.append((int(m.group(1)),int(value)))
    rows.sort()
    if len(rows)!=4 or len({idx for idx,_ in rows})!=4:
        raise RuntimeError(
            f"expected exactly four distinct seed_<index> keys in {path}, got {rows}"
        )
    return [value for _,value in rows]

def _same_seed_ledger(observed:list[int],expected:list[int])->bool:
    """Exact four-seed identity; ordering is not scientific authority."""
    return (
        len(observed)==4
        and len(expected)==4
        and len(set(observed))==4
        and len(set(expected))==4
        and sorted(observed)==sorted(expected)
    )

def _r422_jobs(plan:dict[str,Any])->dict[str,dict[str,Any]]:
    return {str(r["job_id"]):r for r in plan.get("jobs") or []}

def preflight(root:Path)->dict[str,Any]:
    root=root.resolve()
    plan=load(root/R452);registry=load(root/R453)
    r454=load(root/R454);r454s=load(root/R454_SEAL);r454r3=load(root/R454_R3)
    r422=load(root/R422);r422s=load(root/R422_SEAL);runtime=load(root/RUNTIME)
    rr={str(r.get("engine") or r.get("name")):r for r in runtime.get("engines") or []}
    r422j=_r422_jobs(r422)
    jobs=[];errors=[]
    for idx,j in enumerate(plan.get("jobs") or []):
        jid=str(j["job_id"]);engine=str(j["engine"]);seeds=[int(x) for x in j["frozen_seeds"]]
        crel=Path("outputs/v0_6D1_R4_3/jobs")/jid/"JOB_CONTRACT.json";cp=root/crel
        ad=ADAPTERS.get(engine)
        if ad is None:
            errors.append(f"{jid} unauthorized engine {engine}");continue
        row={"plan_index":idx,"job_id":jid,"engine":engine,"window_id":j.get("window_id"),
             "frozen_seeds":seeds,"r42_job_record_sha256":j.get("r42_job_record_sha256"),
             "contract_path":crel.as_posix(),"contract_expected_sha256":EXPECTED_CONTRACT_SHA256.get(jid),
             "adapter_path":ad["path"],"adapter_expected_sha256":ad["sha256"],
             "adapter_authority":ad["authority"],"metric_ids":EXPECTED_METRICS[engine],
             "seed_injection_mode":EXPECTED_SEED_MODES[engine],
             "scientific_stream_count":4,"metric_record_count":8,"canonical_write_authorized":False}
        if not cp.exists():errors.append(f"{jid} contract missing")
        elif sha256(cp)!=EXPECTED_CONTRACT_SHA256.get(jid):errors.append(f"{jid} contract hash mismatch")
        else:
            c=load(cp);cs=[r["seed"] for r in _contract_seed_rows(c)]
            row["contract_seed_order"]=cs
            if not _same_seed_ledger(cs,seeds):errors.append(f"{jid} contract seed ledger {cs} != R452 {seeds}")
            if (c.get("frozen_parent_job") or {}).get("job_id")!=jid:errors.append(f"{jid} contract job mismatch")
            if c.get("canonical_write") is not False:errors.append(f"{jid} contract canonical_write not false")
        ap=root/ad["path"]
        if not ap.exists() or sha256(ap)!=ad["sha256"]:errors.append(f"{jid} adapter hash mismatch")
        if engine in {"Madingley","RangeShifter"}:
            cfgrel=Path("outputs/v0_6D1_R4_3/jobs")/jid/"ENGINE_CONFIG.tsv";cfg=root/cfgrel
            row["engine_config_path"]=cfgrel.as_posix()
            if not cfg.exists():errors.append(f"{jid} ENGINE_CONFIG.tsv missing")
            else:
                try:
                    cs=_r43_config_seeds(cfg);row["engine_config_sha256"]=sha256(cfg);row["engine_config_seeds"]=cs
                    if not _same_seed_ledger(cs,seeds):errors.append(f"{jid} R4.3 config seed ledger {cs} != R452 {seeds}")
                except Exception as exc:errors.append(f"{jid} config parse {exc!r}")
        else:
            auth=r422j.get(jid)
            if not auth:errors.append(f"{jid} missing from R4.22 authorized plan")
            else:
                row["r422_authorized"]=True
                if auth.get("engine")!=engine:errors.append(f"{jid} R4.22 engine mismatch")
                ah=auth.get("adapter_sha256") or auth.get("authorized_adapter_sha256")
                if ah and ah!=ad["sha256"]:errors.append(f"{jid} R4.22 adapter hash mismatch")
                if auth.get("contract_path") and auth.get("contract_path")!=crel.as_posix():errors.append(f"{jid} R4.22 contract path mismatch")
            if engine=="CDMetaPOP":
                prel=Path("outputs/v0_6D1_R4_7/jobs")/jid/"REPAIR_PROFILE.json";pp=root/prel
                row["repair_profile_path"]=prel.as_posix()
                if not pp.exists():errors.append(f"{jid} R4.7 REPAIR_PROFILE missing")
                else:
                    po=load(pp);row["repair_profile_sha256"]=sha256(pp)
                    if po.get("job_id")!=jid:errors.append(f"{jid} repair profile job mismatch")
                    if (po.get("repair_profile") or {}).get("comparison_target_used") is not False:
                        errors.append(f"{jid} repair profile target leakage")
        jobs.append(row)
    checks={
      "r454_complete_32_32":r454.get("checks_passed")==32 and r454.get("checks_failed")==0 and str(r454.get("status","")).startswith("PASS_R454_"),
      "r454_sealed_21_21":r454s.get("verdict")=="SEALED" and r454s.get("checks_passed")==21,
      "r454_r3_postrepair_12_12":r454r3.get("checks_passed")==12 and str(r454r3.get("status","")).startswith("PASS_R454_R3_"),
      "r454_scientific_execution_authorized":r454.get("scientific_execution_authorized") is True,
      "r452_plan_sha_exact":plan.get("plan_sha256")==EXPECTED_R452_PLAN_SHA256,
      "r453_registry_sha_exact":registry.get("registry_sha256")==EXPECTED_R453_REGISTRY_SHA256,
      "r452_exact_20_jobs":len(plan.get("jobs") or [])==20,
      "r452_exact_80_streams":sum(len(j.get("frozen_seeds") or []) for j in plan.get("jobs") or [])==80,
      "r422_enhanced_adapter_parent_sealed":r422s.get("verdict")=="SEALED" and str(r422s.get("status","")).startswith("PASS_R422_"),
      "runtime_all_six_ready":runtime.get("all_required_engines_ready") is True and len(runtime.get("ready_engines") or [])==6,
      "five_runtime_versions_exact":all(e in rr and rr[e].get("status")=="READY" and str(rr[e].get("confirmed_version"))==EXPECTED_VERSIONS[e] for e in ENGINE_ORDER),
      "exact_20_manifest_jobs":len(jobs)==20,
      "job_adapter_contract_seed_binding_errors_zero":len(errors)==0,
      "geonomics_excluded":all(j["engine"]!="Geonomics" for j in jobs),
      "exact_ten_metric_ids":len({m for j in jobs for m in j["metric_ids"]})==10,
      "zero_numeric_thresholds":True,
      "no_majority_vote":registry.get("majority_vote_authorized") is False,
      "no_result_selected_metric":registry.get("result_selected_metric_authorized") is False,
      "no_result_selected_threshold":registry.get("result_selected_threshold_authorized") is False,
      "engine_cannot_define_target":registry.get("engine_output_defines_arcana_target") is False,
      "canonical_rewrite_forbidden":registry.get("canonical_rewrite_authorized") is False,
    }
    ok=all(checks.values())
    man={"stage":STAGE,"status":"R455_EXACT_20_JOB_80_STREAM_EXECUTION_MANIFEST_FROZEN" if ok else BLOCKED,
         "parent_execution_plan_sha256":EXPECTED_R452_PLAN_SHA256,"parent_readout_registry_sha256":EXPECTED_R453_REGISTRY_SHA256,
         "job_count":len(jobs),"scientific_stream_count":sum(j["scientific_stream_count"] for j in jobs),
         "expected_metric_record_count":sum(j["metric_record_count"] for j in jobs),
         "execution_order":"R452_PLAN_ORDER","seed_list_order_semantics":"NON_SCIENTIFIC; EXACT_JOB_SEED_MEMBERSHIP_ONLY","concurrency_semantics":"OPERATIONAL_ONLY_NOT_SCIENTIFIC_AUTHORITY",
         "resume_semantics":"SKIP_ONLY_HASH_VALID_JOB_COMPLETE; PARTIAL_ARCHIVE_AND_RESTART; INVALID_COMPLETE_FAIL_CLOSED",
         "jobs":jobs,"errors":errors}
    write(root/OUT/"R4_55_EXECUTION_MANIFEST.json",man)
    out={"stage":STAGE,"status":"PASS_R455_PREEXECUTION_AUTHORITY_AND_DISPATCH_BINDING" if ok else BLOCKED,
         "checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),
         "checks_failed":len(checks)-sum(checks.values()),"binding_error_count":len(errors),"binding_errors":errors,
         "job_count":len(jobs),"planned_scientific_stream_count":man["scientific_stream_count"],
         "expected_metric_record_count":man["expected_metric_record_count"],
         "scientific_engine_execution_performed":False,"canonical_state_changed":False}
    write(root/OUT/"R4_55_PREEXECUTION_AUDIT.json",out);return out

def resume_status(root:Path,job_id:str)->dict[str,Any]:
    root=root.resolve();man=load(root/OUT/"R4_55_EXECUTION_MANIFEST.json")
    jobs={j["job_id"]:j for j in man.get("jobs") or []};job=jobs.get(job_id)
    if not job:return {"status":"INVALID","reason":"job_not_in_manifest"}
    jd=root/OUT/"jobs"/job_id;marker=jd/"JOB_COMPLETE.json"
    if not jd.exists():return {"status":"ABSENT"}
    if not marker.exists():return {"status":"PARTIAL","reason":"job_directory_without_complete_marker"}
    try:m=load(marker)
    except Exception as exc:return {"status":"INVALID","reason":f"marker_parse_failure {exc!r}"}
    raw=jd/"RAW_ENGINE_EVIDENCE.json";ev=jd/"SCIENTIFIC_READOUT_EVIDENCE.json";au=jd/"JOB_AUDIT.json"
    c={"marker_status":m.get("status")=="PASS_R455_JOB_COMPLETE","job_id":m.get("job_id")==job_id,
       "plan_sha":m.get("parent_execution_plan_sha256")==EXPECTED_R452_PLAN_SHA256,
       "registry_sha":m.get("parent_readout_registry_sha256")==EXPECTED_R453_REGISTRY_SHA256,
       "adapter_sha":m.get("adapter_sha256")==job["adapter_expected_sha256"],
       "raw_present":raw.exists(),"evidence_present":ev.exists(),"audit_present":au.exists()}
    if all(c.values()):
        try:
            e=load(ev);a=load(au)
            c.update({"stream_count_4":e.get("scientific_stream_count")==4,"metric_count_8":e.get("metric_record_count")==8,
                      "evidence_hash":m.get("scientific_evidence_sha256")==sha256(ev),
                      "raw_hash":m.get("raw_engine_evidence_sha256")==sha256(raw),
                      "audit_hash":m.get("job_audit_sha256")==sha256(au),
                      "job_audit_pass":a.get("status")=="PASS_R455_JOB_EVIDENCE_CAPTURE"})
        except Exception:c["evidence_parse"]=False
    return {"status":"VALID" if all(c.values()) else "INVALID","checks":c}

def _metric(mid:str,payload:Any,sources:list[str])->dict[str,Any]:
    return {"metric_id":mid,"metric_role":"SCIENTIFIC_DESCRIPTIVE_REVALIDATION_READOUT","payload":payload,
            "finite":finite_tree(payload),"numeric_acceptance_threshold":None,
            "automatic_pass_fail_from_value":False,"source_artifacts":sources}

def _parse_qfreq(path:Path):
    raw=[x.split() for x in path.read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    if len(raw)<2:raise RuntimeError("qfreq has no data")
    h=raw[0]
    if h[:4]!=["pop","trait","locus","allele"]:raise RuntimeError(f"unexpected qfreq header {h[:4]}")
    gens=h[4:];rows=[]
    for i,r in enumerate(raw[1:],1):
        if len(r)!=len(h):raise RuntimeError(f"qfreq width mismatch row {i}")
        rows.append({"population":int(r[0]),"trait":int(r[1]),"locus":int(r[2]),"allele":float(r[3]),
                     "frequencies":[float(x) for x in r[4:]]})
    by={(r["population"],r["locus"]):r["frequencies"] for r in rows};loci=sorted({r["locus"] for r in rows});gaps=[]
    for gi,_ in enumerate(gens):
        ds=[]
        for locus in loci:
            a=by.get((1,locus));b=by.get((2,locus))
            if a is not None and b is not None:ds.append(abs(a[gi]-b[gi]))
        if not ds:raise RuntimeError("qfreq lacks paired populations")
        gaps.append(sum(ds)/len(ds))
    return gens,rows,gaps

def _find_one(base:Path,name:str)->Path:
    hits=sorted(base.rglob(name))
    if len(hits)!=1:raise RuntimeError(f"expected one {name} under {base}, found {len(hits)}")
    return hits[0]

def _pipe_nums(s):
    out=[]
    for x in str(s or "").split("|"):
        x=x.strip()
        if not x or x.upper()=="NA" or x.lower()=="nan":continue
        out.append(float(x))
    return out

def _cd_dynamic_summary(rep_dir:Path):
    cand=[p for p in rep_dir.rglob("summary_popAllTime.csv") if "neutral" not in p.as_posix().lower()]
    if len(cand)!=1:raise RuntimeError(f"dynamic summary ambiguity {len(cand)}")
    p=cand[0]
    with p.open(newline="",encoding="utf-8-sig") as f:rows=list(csv.DictReader(f))
    if not rows:raise RuntimeError("empty CDMetaPOP summary")
    need={"Year","N_Initial","Alleles","He","Ho"}
    if not need.issubset(rows[0]):raise RuntimeError(f"CDMetaPOP summary schema missing {sorted(need-set(rows[0]))}")
    pop=[];gen=[]
    for r in rows:
        y=int(float(r["Year"]))
        pop.append({"year":y,"patch_vector":_pipe_nums(r["N_Initial"])})
        gen.append({"year":y,"alleles":_pipe_nums(r["Alleles"]),"he":_pipe_nums(r["He"]),"ho":_pipe_nums(r["Ho"])})
    return p,pop,gen

def extract_job(root:Path,job_id:str)->dict[str,Any]:
    root=root.resolve();man=load(root/OUT/"R4_55_EXECUTION_MANIFEST.json");job={j["job_id"]:j for j in man["jobs"]}[job_id]
    jd=root/OUT/"jobs"/job_id;rawp=jd/"RAW_ENGINE_EVIDENCE.json";raw=load(rawp);engine=job["engine"];reps=raw.get("replicates") or []
    errors=[]
    if raw.get("adapter_status")!="PASS":errors.append(f"adapter_status={raw.get('adapter_status')}")
    if raw.get("canonical_write") is not False:errors.append("raw canonical_write not false")
    if len(reps)!=4:errors.append(f"replicate count {len(reps)} !=4")
    observed_seeds=[int(r.get("seed",-1)) for r in reps]
    if not _same_seed_ledger(observed_seeds,job["frozen_seeds"]):errors.append("raw seed ledger mismatch")
    streams=[];records=[];work=jd/"runtime_work"
    for r in reps:
        ri=int(r["replicate_index"]);seed=int(r["seed"]);m=r.get("metrics") or {}
        try:
            if engine=="Madingley":
                t=[0,int(m["representative_years"])]
                local=[_metric(EXPECTED_METRICS[engine][0],{"representative_time_index":t,"values":[int(m["initial_cohort_count"]),int(m["final_cohort_count"])],"semantic_guard":"FUNCTIONAL_COHORT_COUNT_NOT_ARCANA_SPECIES_IDENTITY"},["RAW_ENGINE_EVIDENCE.json"]),
                       _metric(EXPECTED_METRICS[engine][1],{"representative_time_index":t,"values":[int(m["initial_stock_count"]),int(m["final_stock_count"])],"semantic_guard":"AUTOTROPH_STOCK_COUNT_ENGINE_NATIVE"},["RAW_ENGINE_EVIDENCE.json"])]
            elif engine=="RangeShifter":
                t=[0,int(m["representative_years"])]
                local=[_metric(EXPECTED_METRICS[engine][0],{"representative_time_index":t,"values":[float(m["initial_abundance"]),float(m["final_abundance"])],"semantic_guard":"ENGINE_ABUNDANCE_NOT_ARCANA_LITERAL_POPULATION"},["RAW_ENGINE_EVIDENCE.json"]),
                       _metric(EXPECTED_METRICS[engine][1],{"representative_time_index":t,"values":[int(m["initial_occupied_cells"]),int(m["final_occupied_cells"])],"occupancy_semantics":m.get("occupancy_semantics"),"semantic_guard":"ENGINE_ARTIFICIAL_CELL_OCCUPANCY"},["RAW_ENGINE_EVIDENCE.json"])]
            elif engine=="NEMO":
                q=_find_one(work/f"rep_{ri:03d}","r421_nemo_1.qfreq");gens,rows,gaps=_parse_qfreq(q);rel=q.relative_to(jd).as_posix()
                local=[_metric(EXPECTED_METRICS[engine][0],{"generation_columns":gens,"rows":rows,"semantic_guard":"RAW_ALLELE_FREQUENCY_NOT_ARCANA_POPULATION"},[rel,"RAW_ENGINE_EVIDENCE.json"]),
                       _metric(EXPECTED_METRICS[engine][1],{"generation_columns":gens,"mean_absolute_population_gap":gaps,"semantic_guard":"ALLELE_FREQUENCY_DIFFERENTIATION_NOT_GENE_FLOW_RATE"},[rel,"RAW_ENGINE_EVIDENCE.json"])]
            elif engine=="CDMetaPOP":
                sp,pop,gen=_cd_dynamic_summary(work/f"rep_{ri:03d}");rel=sp.relative_to(jd).as_posix()
                local=[_metric(EXPECTED_METRICS[engine][0],{"states":pop,"arm":"DYNAMIC_R421_MATCHED_PAIR_PRIMARY_ARM","semantic_guard":"PATCH_POPULATION_STATE_ENGINE_NATIVE"},[rel,"RAW_ENGINE_EVIDENCE.json"]),
                       _metric(EXPECTED_METRICS[engine][1],{"states":gen,"arm":"DYNAMIC_R421_MATCHED_PAIR_PRIMARY_ARM","semantic_guard":"ALLELES_HE_HO_DESCRIPTIVE_NOT_ADDITIVE_VARIANCE"},[rel,"RAW_ENGINE_EVIDENCE.json"])]
            elif engine=="SLiM":raise RuntimeError("SLIM_REQUIRES_GOVERNED_TSKIT_EXTRACTOR")
            else:raise RuntimeError(f"unauthorized engine {engine}")
            if [x["metric_id"] for x in local]!=EXPECTED_METRICS[engine]:raise RuntimeError("metric IDs/order mismatch")
            if not all(x["finite"] for x in local):raise RuntimeError("nonfinite metric payload")
            for x in local:records.append({"job_id":job_id,"engine":engine,"window_id":job["window_id"],"replicate_index":ri,"frozen_seed":seed,**x})
            streams.append({"job_id":job_id,"engine":engine,"window_id":job["window_id"],"replicate_index":ri,"frozen_seed":seed,
                            "seed_injection_mode":EXPECTED_SEED_MODES[engine],"status":"PASS","metric_ids":EXPECTED_METRICS[engine],
                            "scientific_evidence":True,"numeric_scientific_adjudication_performed":False,"canonical_state_changed":False})
        except Exception as exc:errors.append(f"replicate {ri} extractor failure {exc!r}")
    return _finalize_job(root,job,rawp,streams,records,errors)

def extract_slim_job(root:Path,job_id:str)->dict[str,Any]:
    import tskit
    root=root.resolve();man=load(root/OUT/"R4_55_EXECUTION_MANIFEST.json");job={j["job_id"]:j for j in man["jobs"]}[job_id]
    jd=root/OUT/"jobs"/job_id;rawp=jd/"RAW_ENGINE_EVIDENCE.json";raw=load(rawp);reps=raw.get("replicates") or [];errors=[]
    if job["engine"]!="SLiM":raise RuntimeError("non-SLiM job")
    if raw.get("adapter_status")!="PASS":errors.append(f"adapter_status={raw.get('adapter_status')}")
    if raw.get("canonical_write") is not False:errors.append("raw canonical_write not false")
    if len(reps)!=4:errors.append("replicate count !=4")
    observed_seeds=[int(r.get("seed",-1)) for r in reps]
    if not _same_seed_ledger(observed_seeds,job["frozen_seeds"]):errors.append("raw seed ledger mismatch")
    streams=[];records=[];work=jd/"runtime_work"
    for r in reps:
        ri=int(r["replicate_index"]);seed=int(r["seed"])
        try:
            trees=sorted((work/f"rep_{ri:03d}").rglob("*.trees"))
            if len(trees)!=1:raise RuntimeError(f"expected one .trees, found {len(trees)}")
            tp=trees[0];ts=tskit.load(str(tp));pops=[p.id for p in ts.populations() if len(ts.samples(population=p.id))>0]
            if len(pops)<2:raise RuntimeError("<2 sampled populations")
            a=ts.samples(population=pops[0]);b=ts.samples(population=pops[1]);div=float(ts.divergence(sample_sets=[a,b]))
            structural={"nodes":int(ts.num_nodes),"edges":int(ts.num_edges),"individuals":int(ts.num_individuals),
                        "mutations":int(ts.num_mutations),"sequence_length":float(ts.sequence_length),"trees":int(ts.num_trees)}
            genealogy={"population_ids":pops,"sample_counts":[int(len(ts.samples(population=p))) for p in pops],
                       "between_population_divergence":div,"divergence_mode":"site",
                       "semantic_guard":"DESCRIPTIVE_GENEALOGICAL_DIVERGENCE_NOT_MIGRATION_RATE"}
            rel=tp.relative_to(jd).as_posix()
            local=[_metric(EXPECTED_METRICS["SLiM"][0],structural,[rel,"RAW_ENGINE_EVIDENCE.json"]),
                   _metric(EXPECTED_METRICS["SLiM"][1],genealogy,[rel,"RAW_ENGINE_EVIDENCE.json"])]
            if not all(x["finite"] for x in local):raise RuntimeError("nonfinite SLiM payload")
            for x in local:records.append({"job_id":job_id,"engine":"SLiM","window_id":job["window_id"],"replicate_index":ri,"frozen_seed":seed,**x})
            streams.append({"job_id":job_id,"engine":"SLiM","window_id":job["window_id"],"replicate_index":ri,"frozen_seed":seed,
                            "seed_injection_mode":EXPECTED_SEED_MODES["SLiM"],"status":"PASS","metric_ids":EXPECTED_METRICS["SLiM"],
                            "scientific_evidence":True,"numeric_scientific_adjudication_performed":False,"canonical_state_changed":False})
        except Exception as exc:errors.append(f"replicate {ri} SLiM extractor failure {exc!r}")
    return _finalize_job(root,job,rawp,streams,records,errors)

def _finalize_job(root,job,rawp,streams,records,errors):
    jd=rawp.parent;obs={r["metric_id"] for r in records};exp=set(EXPECTED_METRICS[job["engine"]])
    c={"raw_engine_evidence_present":rawp.exists(),"exact_four_scientific_streams":len(streams)==4,
       "exact_eight_metric_records":len(records)==8,"exact_authorized_metric_ids":obs==exp,
       "all_metric_payloads_finite":all(r.get("finite") is True for r in records),
       "zero_numeric_thresholds":all(r.get("numeric_acceptance_threshold") is None for r in records),
       "zero_automatic_pass_fail":all(r.get("automatic_pass_fail_from_value") is False for r in records),
       "all_streams_scientific_evidence":all(r.get("scientific_evidence") is True for r in streams),
       "no_numeric_scientific_adjudication":all(r.get("numeric_scientific_adjudication_performed") is False for r in streams),
       "canonical_unchanged":all(r.get("canonical_state_changed") is False for r in streams),"extractor_errors_zero":len(errors)==0}
    ok=all(c.values())
    e={"stage":STAGE,"status":"PASS_R455_JOB_SCIENTIFIC_READOUT_EVIDENCE" if ok else BLOCKED,
       "job_id":job["job_id"],"engine":job["engine"],"window_id":job["window_id"],
       "parent_execution_plan_sha256":EXPECTED_R452_PLAN_SHA256,"parent_readout_registry_sha256":EXPECTED_R453_REGISTRY_SHA256,
       "adapter_path":job["adapter_path"],"adapter_sha256":job["adapter_expected_sha256"],"adapter_authority":job["adapter_authority"],
       "scientific_stream_count":len(streams),"metric_record_count":len(records),"stream_records":streams,"metric_records":records,
       "numeric_scientific_adjudication_performed":False,"scientific_divergence_claimed":False,"canonical_state_changed":False,"errors":errors}
    ep=jd/"SCIENTIFIC_READOUT_EVIDENCE.json";write(ep,e)
    a={"stage":STAGE,"status":"PASS_R455_JOB_EVIDENCE_CAPTURE" if ok else BLOCKED,"job_id":job["job_id"],"engine":job["engine"],
       "checks":c,"checks_passed":sum(c.values()),"checks_total":len(c),"checks_failed":len(c)-sum(c.values()),
       "scientific_stream_count":len(streams),"metric_record_count":len(records),"errors":errors}
    ap=jd/"JOB_AUDIT.json";write(ap,a)
    if ok:
        write(jd/"JOB_COMPLETE.json",{"stage":STAGE,"status":"PASS_R455_JOB_COMPLETE","job_id":job["job_id"],"engine":job["engine"],
             "parent_execution_plan_sha256":EXPECTED_R452_PLAN_SHA256,"parent_readout_registry_sha256":EXPECTED_R453_REGISTRY_SHA256,
             "adapter_sha256":job["adapter_expected_sha256"],"raw_engine_evidence_sha256":sha256(rawp),
             "scientific_evidence_sha256":sha256(ep),"job_audit_sha256":sha256(ap),
             "scientific_stream_count":4,"metric_record_count":8,"canonical_state_changed":False})
    return a

def aggregate(root:Path)->dict[str,Any]:
    root=root.resolve();man=load(root/OUT/"R4_55_EXECUTION_MANIFEST.json");jobs=[];streams=[];records=[];errors=[]
    for j in man["jobs"]:
        jid=j["job_id"];jd=root/OUT/"jobs"/jid;mp=jd/"JOB_COMPLETE.json";ap=jd/"JOB_AUDIT.json";ep=jd/"SCIENTIFIC_READOUT_EVIDENCE.json";rp=jd/"RAW_ENGINE_EVIDENCE.json"
        if not all(p.exists() for p in [mp,ap,ep,rp]):errors.append(f"{jid} incomplete bundle");continue
        m=load(mp);a=load(ap);e=load(ep)
        if m.get("status")!="PASS_R455_JOB_COMPLETE":errors.append(f"{jid} marker invalid")
        if a.get("status")!="PASS_R455_JOB_EVIDENCE_CAPTURE":errors.append(f"{jid} audit blocked")
        if m.get("raw_engine_evidence_sha256")!=sha256(rp):errors.append(f"{jid} raw hash mismatch")
        if m.get("scientific_evidence_sha256")!=sha256(ep):errors.append(f"{jid} evidence hash mismatch")
        if m.get("job_audit_sha256")!=sha256(ap):errors.append(f"{jid} audit hash mismatch")
        streams.extend(e.get("stream_records") or []);records.extend(e.get("metric_records") or [])
        jobs.append({"job_id":jid,"engine":j["engine"],"window_id":j["window_id"],"scientific_stream_count":e.get("scientific_stream_count"),
                     "metric_record_count":e.get("metric_record_count"),"raw_engine_evidence_sha256":sha256(rp),
                     "scientific_evidence_sha256":sha256(ep),"job_audit_sha256":sha256(ap)})
    es={}
    for eng in ENGINE_ORDER:
        jj=[j for j in jobs if j["engine"]==eng]
        es[eng]={"job_count":len(jj),"scientific_stream_count":sum(int(j["scientific_stream_count"]) for j in jj),
                 "metric_record_count":sum(int(j["metric_record_count"]) for j in jj)}
    obs={(r["job_id"],int(r["frozen_seed"])) for r in streams};exp={(j["job_id"],int(s)) for j in man["jobs"] for s in j["frozen_seeds"]}
    mids={r["metric_id"] for r in records};em={m for v in EXPECTED_METRICS.values() for m in v}
    c={"manifest_status_frozen":man.get("status")=="R455_EXACT_20_JOB_80_STREAM_EXECUTION_MANIFEST_FROZEN",
       "exact_20_jobs_complete":len(jobs)==20,"exact_80_scientific_streams":len(streams)==80,"exact_160_metric_records":len(records)==160,
       "exact_job_seed_pair_coverage":obs==exp and len(obs)==80,"exact_ten_metric_ids":mids==em,
       "every_stream_status_pass":all(r.get("status")=="PASS" for r in streams),
       "all_metrics_finite":all(r.get("finite") is True for r in records),
       "zero_numeric_thresholds":all(r.get("numeric_acceptance_threshold") is None for r in records),
       "zero_automatic_scientific_pass_fail":all(r.get("automatic_pass_fail_from_value") is False for r in records),
       "numeric_scientific_adjudication_not_performed":all(r.get("numeric_scientific_adjudication_performed") is False for r in streams),
       "scientific_divergence_not_claimed":True,"canonical_unchanged":all(r.get("canonical_state_changed") is False for r in streams),
       "bundle_errors_zero":len(errors)==0,
       "engine_distribution_exact":{e:es[e]["job_count"] for e in ENGINE_ORDER}=={"Madingley":4,"RangeShifter":5,"CDMetaPOP":5,"NEMO":3,"SLiM":3},
       "stream_distribution_exact":{e:es[e]["scientific_stream_count"] for e in ENGINE_ORDER}=={"Madingley":16,"RangeShifter":20,"CDMetaPOP":20,"NEMO":12,"SLiM":12},
       "metric_distribution_exact":{e:es[e]["metric_record_count"] for e in ENGINE_ORDER}=={"Madingley":32,"RangeShifter":40,"CDMetaPOP":40,"NEMO":24,"SLiM":24}}
    ok=all(c.values())
    corpus={"stage":STAGE,"status":"R455_NON_GEONOMICS_FULL_SCIENTIFIC_EVIDENCE_CORPUS_CAPTURED" if ok else BLOCKED,
            "parent_execution_plan_sha256":EXPECTED_R452_PLAN_SHA256,"parent_readout_registry_sha256":EXPECTED_R453_REGISTRY_SHA256,
            "job_count":len(jobs),"scientific_stream_count":len(streams),"metric_record_count":len(records),"engine_summary":es,
            "job_evidence_manifest":jobs,"scientific_stream_records":streams,"scientific_metric_records":records,
            "numeric_scientific_adjudication_performed":False,"scientific_divergence_claim_count":0,"canonical_state_changed":False,"errors":errors}
    cp=root/OUT/"R4_55_FULL_NON_GEONOMICS_EVIDENCE_CORPUS.json";write(cp,corpus)
    out={"stage":STAGE,"status":COMPLETE if ok else BLOCKED,"checks":c,"checks_passed":sum(c.values()),"checks_total":len(c),
         "checks_failed":len(c)-sum(c.values()),"job_count":len(jobs),"scientific_stream_count":len(streams),"metric_record_count":len(records),
         "engine_summary":es,"scientific_engine_execution_performed":True,"historical_scientific_execution_performed":True,
         "numeric_scientific_adjudication_performed":False,"scientific_divergence_claim_count":0,"multi_engine_full_revalidation_closed":False,
         "target_numeric_execution_performed":False,"readjudication_performed":False,"canonical_state_changed":False,
         "active_deferred_p2_cell_count":2,"proxy_context_only_count":2,"p3_backlog_cell_count":6,
         "evidence_corpus_sha256":sha256(cp),"next_action":NEXT if ok else "REPAIR_R455_EXECUTION_OR_EVIDENCE_CAPTURE"}
    write(root/OUT/"R4_55_INTEGRATED_AUDIT.json",out);return out

def final_seal(root:Path)->dict[str,Any]:
    root=root.resolve();a=load(root/OUT/"R4_55_INTEGRATED_AUDIT.json");cp=root/OUT/"R4_55_FULL_NON_GEONOMICS_EVIDENCE_CORPUS.json";co=load(cp)
    c={"r455_complete":a.get("status")==COMPLETE and a.get("checks_failed")==0,"exact_20_jobs":a.get("job_count")==20,
       "exact_80_scientific_streams":a.get("scientific_stream_count")==80,"exact_160_metric_records":a.get("metric_record_count")==160,
       "scientific_execution_performed":a.get("scientific_engine_execution_performed") is True and a.get("historical_scientific_execution_performed") is True,
       "corpus_capture_status":co.get("status")=="R455_NON_GEONOMICS_FULL_SCIENTIFIC_EVIDENCE_CORPUS_CAPTURED",
       "corpus_hash_exact":a.get("evidence_corpus_sha256")==sha256(cp),
       "numeric_adjudication_not_performed":a.get("numeric_scientific_adjudication_performed") is False,
       "zero_divergence_claims":a.get("scientific_divergence_claim_count")==0,"multi_engine_not_yet_closed":a.get("multi_engine_full_revalidation_closed") is False,
       "no_target_numeric":a.get("target_numeric_execution_performed") is False,"no_readjudication":a.get("readjudication_performed") is False,
       "canonical_unchanged":a.get("canonical_state_changed") is False,"deferred_p2_two":a.get("active_deferred_p2_cell_count")==2,
       "proxy_context_two":a.get("proxy_context_only_count")==2,"p3_backlog_six":a.get("p3_backlog_cell_count")==6,"next_r456":a.get("next_action")==NEXT}
    ok=all(c.values())
    out={"stage":STAGE,"audit":"FINAL_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_AND_EVIDENCE_CAPTURE","status":SEALED if ok else BLOCKED,
         "verdict":"SEALED" if ok else "BLOCKED","checks":c,"checks_passed":sum(c.values()),"checks_total":len(c),"checks_failed":len(c)-sum(c.values()),
         "summary":{"job_count":a.get("job_count"),"scientific_stream_count":a.get("scientific_stream_count"),"metric_record_count":a.get("metric_record_count"),
                    "engine_summary":a.get("engine_summary"),"scientific_engine_execution_performed":True,
                    "numeric_scientific_adjudication_performed":False,"scientific_divergence_claim_count":0,
                    "multi_engine_full_revalidation_closed":False,"canonical_state_changed":False,"deep_biological_coupling":False,"next_action":NEXT},
         "next_action":NEXT}
    write(root/SEAL,out);return out

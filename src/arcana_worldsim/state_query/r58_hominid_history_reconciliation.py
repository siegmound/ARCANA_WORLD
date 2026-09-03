from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import numpy as np

STAGE = "v0.6D1-R5.8"
OUT_REL = Path("outputs/v0_6D1_R5_8")
TARGET_COHORT = ("RPT_010_D02", "RPT_009_D02")
START_AGE_MA = 3.0
END_AGE_MA = 0.2
EXPECTED_AGE_STATES = 141
EXPECTED_MACROSTEP_KYR = 20.0
EXPECTED_R57_FINAL_SEAL_SHA256 = "3914d106b67a070bd4f7beb6ba7289302cf4b11fcb0fad8a91c10a5eb97d8d53"
EXPECTED_R327_FINAL_SEAL_AUDIT_SHA256 = "272b9b06e4bbfe99c80c7660731c58bb93ea6dc13f6bc1d98f002b27a47c7d72"
EXPECTED_R327_OUTPUT_MANIFEST_SHA256 = "2485afcfb085823ecea06e982298973d4a2e4d0de31434bad7fc564e0c3bbea2"
EXPECTED_R321_CLOSURE_SHA256 = "2dcf79131643ca441fbee6f61939782df94b895533fdb7a3e9b4e2695291b041"
EXPECTED_R321_REGISTRY_SHA256 = "0eb43167347f0b691ee703ecc5ab1bc477f26f785b26b7f47a468a7eb9b848cf"
EXPECTED_DIRECT_EVENTS = {
    "RPT_010_D02": ("E002910", "deme_fission", 2.0),
    "RPT_009_D02": ("E002909", "deme_fission", 2.0),
}

R57_OUT = Path("outputs/v0_6D1_R5_7")
R57_SEAL = R57_OUT / "R5_7_FINAL_BLOCK_SEAL.json"
R57_SEAL_MANIFEST = R57_OUT / "R5_7_FINAL_BLOCK_SEAL_MANIFEST.json"
R327_OUT = Path("outputs/v0_6D1_R3_27")
R327_SEAL_OUT = Path("outputs/v0_6D1_R3_27_SEAL")
R327_SEAL_AUDIT = R327_SEAL_OUT / "R3_27_FINAL_SEAL_AUDIT.json"
R327_OUTPUT_MANIFEST = R327_OUT / "R3_27_OUTPUT_MANIFEST.json"
R327_CHECKPOINT = R327_OUT / "R3_27_HUMAN_200KA_CHECKPOINT.json"
R327_TRAJECTORIES = R327_OUT / "R3_27_MACRO_REPLAY_TRAJECTORIES.npz"
R321_OUT = Path("outputs/v0_6D1_R3_21")
R321_CLOSURE = R321_OUT / "R3_21_HISTORICAL_LINEAGE_CLOSURE.json"
R321_REGISTRY = R321_OUT / "R3_21_PRESENT_LINEAGE_REGISTRY.json"
R55_OUT = Path("outputs/v0_6D1_R5_5")
R55_MANIFEST = R55_OUT / "R5_5_OUTPUT_MANIFEST.json"
R55_HISTORY = R55_OUT / "R5_5_CONTACT_ZONE_HISTORY.json"
R55_ATLAS = R55_OUT / "R5_5_CONTACT_OPPORTUNITY_ATLAS.npz"
R56_OUT = Path("outputs/v0_6D1_R5_6")
R56_MANIFEST = R56_OUT / "R5_6_OUTPUT_MANIFEST.json"
R56_PLAN = R56_OUT / "R5_6_SLIM_EXECUTION_PLAN.json"

FINAL_STATUS = "PASS_R58_3MA_200KA_HOMINID_HISTORY_RECONCILIATION_CANDIDATE"

class R58Error(RuntimeError):
    pass

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path: Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def _manifest_integrity(base: Path, manifest_path: Path) -> tuple[bool, dict[str, Any]]:
    if not manifest_path.is_file():
        return False, {"error":"missing_manifest","path":str(manifest_path)}
    try:
        m = load_json(manifest_path); files = dict(m.get("files") or {})
        ok = bool(files); mismatches=[]
        for name, meta in files.items():
            p=base/name
            same=p.is_file() and p.stat().st_size==int(meta.get("bytes",-1)) and sha256_file(p)==meta.get("sha256")
            if not same: mismatches.append(name); ok=False
        return bool(ok), {"file_count":len(files),"mismatches":mismatches}
    except Exception as exc:
        return False, {"error":repr(exc)}

def _direct_target(raw: dict[str, Any], target: str) -> bool:
    direct_fields = (
        "species_id", "species_id_at_fission", "species_id_at_coalescence",
        "parent_species_id", "daughter_species_id",
    )
    return any(raw.get(k) == target for k in direct_fields)

def _r57_bound_stage_hash(seal: dict[str, Any], stage: str, field: str) -> str | None:
    return (((seal.get("block_input_binding") or {}).get("candidate_stages") or {}).get(stage) or {}).get(field)

def validate_parent_authority(root: Path) -> dict[str, Any]:
    root=Path(root).resolve(); checks: dict[str,bool]={}
    required=[R57_SEAL,R57_SEAL_MANIFEST,R327_SEAL_AUDIT,R327_OUTPUT_MANIFEST,R327_CHECKPOINT,R327_TRAJECTORIES,R321_CLOSURE,R321_REGISTRY,R55_MANIFEST,R55_HISTORY,R55_ATLAS,R56_MANIFEST,R56_PLAN]
    for p in required: checks[f"present::{p.as_posix()}"]=(root/p).is_file()
    try:
        seal=load_json(root/R57_SEAL); sm=load_json(root/R57_SEAL_MANIFEST)
        checks["r57_final_seal_exact_hash"] = sha256_file(root/R57_SEAL)==EXPECTED_R57_FINAL_SEAL_SHA256
        checks["r57_final_seal_semantics"] = seal.get("sealed") is True and seal.get("status")=="PASS_R57_R53_R56_HOMINID_DEMOGRAPHY_GENE_FLOW_ANCESTRY_BLOCK_SEALED" and int(seal.get("checks_passed",-1))==43 and int(seal.get("checks_total",-1))==43 and (seal.get("summary") or {}).get("closure_readiness")=="SEALED_R53_R56_GOVERNED_EVIDENCE_BLOCK_READY_FOR_POST_BLOCK_HOMINID_HISTORY_RECONCILIATION"
        checks["r57_seal_manifest_binds_seal"] = (sm.get("final_seal_file") or {}).get("sha256")==EXPECTED_R57_FINAL_SEAL_SHA256
        checks["r57_no_numeric_history_or_canon_change"] = (seal.get("summary") or {}).get("numeric_historical_truth_claimed") is False and (seal.get("summary") or {}).get("realized_historical_admixture_claimed") is False and (seal.get("summary") or {}).get("canonical_state_changed") is False and (seal.get("summary") or {}).get("deep_biological_coupling") is False
        checks["r57_binds_live_r55_manifest"] = sha256_file(root/R55_MANIFEST)==_r57_bound_stage_hash(seal,"R5.5","output_manifest_sha256")
        checks["r57_binds_live_r56_manifest"] = sha256_file(root/R56_MANIFEST)==_r57_bound_stage_hash(seal,"R5.6","output_manifest_sha256")
    except Exception:
        for k in ["r57_final_seal_exact_hash","r57_final_seal_semantics","r57_seal_manifest_binds_seal","r57_no_numeric_history_or_canon_change","r57_binds_live_r55_manifest","r57_binds_live_r56_manifest"]: checks[k]=False
    try:
        a=load_json(root/R327_SEAL_AUDIT); cp=load_json(root/R327_CHECKPOINT)
        checks["r327_final_seal_audit_exact_hash"] = sha256_file(root/R327_SEAL_AUDIT)==EXPECTED_R327_FINAL_SEAL_AUDIT_SHA256
        checks["r327_final_seal_semantics"] = a.get("verdict")=="SEALED" and a.get("status")=="PASS_R327_HOMININ_MACRO_EVOLUTION_REPLAY_TO_200KA_ROBUSTNESS_AND_HUMAN_200KA_CHECKPOINT_SEALED" and int(a.get("checks_passed",-1))==28 and int(a.get("checks_failed",-1))==0
        checks["r327_output_manifest_exact_hash"] = sha256_file(root/R327_OUTPUT_MANIFEST)==EXPECTED_R327_OUTPUT_MANIFEST_SHA256
        mi,_=_manifest_integrity(root/R327_OUT,root/R327_OUTPUT_MANIFEST); checks["r327_output_manifest_integrity"]=mi
        checks["r327_checkpoint_cohort_exact"] = tuple(cp.get("candidate_cohort") or [])==TARGET_COHORT and int(cp.get("candidate_count",-1))==2 and float(cp.get("age_ka",-1))==200.0
        checks["r327_checkpoint_not_final_identity"] = cp.get("unique_human_identity_materialized") is False and "NOT_FINAL_HUMAN_SPECIES_IDENTITY" in str(cp.get("interpretation",""))
    except Exception:
        for k in ["r327_final_seal_audit_exact_hash","r327_final_seal_semantics","r327_output_manifest_exact_hash","r327_output_manifest_integrity","r327_checkpoint_cohort_exact","r327_checkpoint_not_final_identity"]: checks[k]=False
    checks["r321_closure_exact_hash"]=(root/R321_CLOSURE).is_file() and sha256_file(root/R321_CLOSURE)==EXPECTED_R321_CLOSURE_SHA256
    checks["r321_registry_exact_hash"]=(root/R321_REGISTRY).is_file() and sha256_file(root/R321_REGISTRY)==EXPECTED_R321_REGISTRY_SHA256
    mi55,_=_manifest_integrity(root/R55_OUT,root/R55_MANIFEST); checks["r55_output_manifest_integrity_under_r57"]=mi55
    mi56,_=_manifest_integrity(root/R56_OUT,root/R56_MANIFEST); checks["r56_output_manifest_integrity_under_r57"]=mi56
    failed=[k for k,v in checks.items() if not v]
    return {"stage":STAGE,"status":"PASS_R58_IMMUTABLE_R57_R327_R321_PARENT_AUTHORITY" if not failed else "BLOCKED_R58_PARENT_AUTHORITY","checks_passed":sum(checks.values()),"checks_total":len(checks),"failed":failed,"checks":checks}

def _event_projection(event: dict[str, Any]) -> dict[str, Any]:
    raw=dict(event.get("raw") or {})
    keep=["age_ma","elapsed_year","event","authority","species_id","species_id_at_fission","species_id_at_coalescence","parent_species_id","daughter_species_id","parent_component_id","daughter_component_id","component_id","population","daughter_population","parent_remainder_population","centroid_lat_deg","centroid_lon_deg","semantic_status"]
    return {"event_id":event.get("event_id"),"raw":{k:raw[k] for k in keep if k in raw}}

def _state_summary(state: np.ndarray, varnames: list[str], index: int) -> dict[str, Any]:
    x=np.asarray(state[:,index,:],float)
    return {name:{"q10":float(np.quantile(x[:,j],.10)),"median":float(np.median(x[:,j])),"q90":float(np.quantile(x[:,j],.90))} for j,name in enumerate(varnames)}

def reconcile(root: Path, out: Path | None=None) -> dict[str, Any]:
    root=Path(root).resolve(); out=Path(out).resolve() if out else root/OUT_REL
    parent=validate_parent_authority(root)
    if parent.get("failed"): raise R58Error(f"R5.8 parent authority failed: {parent['failed']}")
    cfg=load_json(root/"configs/world1_r58_hominid_history_reconciliation_v0_6D1_R5_8.json")
    reg=load_json(root/R321_REGISTRY); closure=load_json(root/R321_CLOSURE); cp=load_json(root/R327_CHECKPOINT)
    lineages={str(x.get("species_id")):x for x in reg.get("lineages") or []}
    with np.load(root/R327_TRAJECTORIES,allow_pickle=False) as z:
        r327_ids=tuple(map(str,z["candidate_ids"].tolist())); ages=np.asarray(z["age_ma"],float); varnames=list(map(str,z["variable_names"].tolist())); state=np.asarray(z["state"],float)
    with np.load(root/R55_ATLAS,allow_pickle=False) as z:
        ages55=np.asarray(z["age_ma"],float); pair_ids=tuple(map(str,z["pair_ids"].tolist())); exact=np.asarray(z["exact_contact_ensemble_fraction"],float); near=np.asarray(z["one_cell_contact_ensemble_fraction"],float)
    h55=load_json(root/R55_HISTORY); p56=load_json(root/R56_PLAN)

    ledger=[]; all_event_ids=[]
    for target in TARGET_COHORT:
        lr=lineages.get(target)
        if lr is None: raise R58Error(f"target lineage missing: {target}")
        evs=[]
        for event in closure.get("historical_events") or []:
            raw=dict(event.get("raw") or {}); age=raw.get("age_ma")
            if age is None or float(age)>START_AGE_MA+1e-12 or float(age)<END_AGE_MA-1e-12: continue
            if _direct_target(raw,target): evs.append(event)
        evs.sort(key=lambda e:(-float((e.get("raw") or {}).get("age_ma",-1)),str(e.get("event_id"))))
        all_event_ids.extend(str(e.get("event_id")) for e in evs)
        ledger.append({
            "species_id":target,"ancestry_chain_root_to_present":lr.get("ancestry_chain_root_to_present"),"parent_species_id":lr.get("parent_species_id"),"root_species_id":lr.get("root_species_id"),"birth_age_ma":lr.get("birth_age_ma"),"birth_predates_3ma_window":float(lr.get("birth_age_ma"))>START_AGE_MA,"direct_in_window_event_count":len(evs),"direct_in_window_events":[_event_projection(e) for e in evs],"event_semantics":"DIRECT_R3_21_ATTESTATION_ONLY_NOT_INFERRED_FROM_R3_27_OR_R5X"
        })

    # Macro alignment at start, each directly attested event age, and 200 ka endpoint.
    anchor_ages=sorted({START_AGE_MA,END_AGE_MA,*[float(((e.get("raw") or {}).get("age_ma"))) for e in (closure.get("historical_events") or []) if str(e.get("event_id")) in set(all_event_ids)]},reverse=True)
    macro=[]
    for target in TARGET_COHORT:
        ci=r327_ids.index(target); rows=[]
        for age in anchor_ages:
            hits=np.where(np.isclose(ages,age,atol=1e-10))[0]
            if len(hits)!=1: raise R58Error(f"R3.27 age anchor {age} not unique")
            ti=int(hits[0]); rows.append({"age_ma":float(age),"time_index":ti,"state_envelope":_state_summary(state[:,ci,:,:],varnames,ti)})
        macro.append({"species_id":target,"anchors":rows})

    binary=(near>0.0)
    unique_schedules=np.unique(binary.astype(np.int8),axis=0)
    active_any=np.any(binary,axis=0); active_all=np.all(binary,axis=0)
    exact_any=np.any(exact>0.0,axis=0)
    def age_list(mask): return [float(x) for x in ages55[np.asarray(mask,bool)]]
    contact_alignment={
        "pair_count":len(pair_ids),"r55_candidate_ids":h55.get("candidate_ids"),"age_state_count":len(ages55),"r327_r55_age_axis_exact":bool(np.array_equal(ages,ages55)),"binary_schedule_class_count_recomputed":int(len(unique_schedules)),"r56_schedule_class_count_declared":int(p56.get("schedule_class_count",-1)),"one_cell_contact_any_pair_age_count":int(active_any.sum()),"one_cell_contact_all_pairs_age_count":int(active_all.sum()),"exact_overlap_any_pair_age_count":int(exact_any.sum()),"one_cell_contact_any_pair_oldest_age_ma":float(ages55[np.where(active_any)[0][0]]) if active_any.any() else None,"one_cell_contact_any_pair_youngest_age_ma":float(ages55[np.where(active_any)[0][-1]]) if active_any.any() else None,"semantics":"CONTACT_OPPORTUNITY_ALIGNMENT_ONLY_NOT_REALIZED_GENE_FLOW_OR_ADMIXTURE"
    }

    checks: dict[str,bool]={}
    checks["parent_authority_pass"]=not parent.get("failed")
    checks["config_target_cohort_exact"]=tuple(cfg.get("target_cohort") or [])==TARGET_COHORT
    checks["r327_target_cohort_exact"]=tuple(cp.get("candidate_cohort") or [])==TARGET_COHORT
    checks["r327_macro_candidate_contains_both_targets"]=all(x in r327_ids for x in TARGET_COHORT)
    checks["r327_age_axis_exact_3ma_to_200ka_141_states"]=len(ages)==EXPECTED_AGE_STATES and abs(float(ages[0])-START_AGE_MA)<1e-10 and abs(float(ages[-1])-END_AGE_MA)<1e-10 and np.allclose(np.diff(ages),-EXPECTED_MACROSTEP_KYR/1000.0,atol=1e-10)
    checks["r55_age_axis_exactly_matches_r327"]=np.array_equal(ages,ages55)
    checks["r55_candidate_ids_exact"]=tuple(h55.get("candidate_ids") or [])==TARGET_COHORT
    checks["r55_pair_count_exact"]=len(pair_ids)==35 and int(h55.get("cross_lineage_pair_count",-1))==35
    checks["r56_schedule_class_recomputed_exact"]=len(unique_schedules)==int(p56.get("schedule_class_count",-1))==1
    checks["target_lineages_present_in_r321"]=all(t in lineages for t in TARGET_COHORT)
    checks["target_lineages_preexist_3ma_window"]=all(float(lineages[t].get("birth_age_ma"))>START_AGE_MA for t in TARGET_COHORT)
    for target,(eid,etype,eage) in EXPECTED_DIRECT_EVENTS.items():
        rec=next(x for x in ledger if x["species_id"]==target); evs=rec["direct_in_window_events"]
        checks[f"{target}_direct_event_exact"] = len(evs)==1 and evs[0].get("event_id")==eid and (evs[0].get("raw") or {}).get("event")==etype and abs(float((evs[0].get("raw") or {}).get("age_ma"))-eage)<1e-12
    checks["direct_events_align_to_r327_macrostep_axis"]=all(any(abs(float(a)-float(eage))<1e-12 for a in ages) for _,_,eage in EXPECTED_DIRECT_EVENTS.values())
    checks["macro_replay_not_reinterpreted_as_event_history"]=True
    checks["contact_opportunity_not_realized_gene_flow"]=True
    checks["slim_ancestry_not_realized_history"]=True
    checks["human_200ka_not_final_unique_species_identity"]=cp.get("unique_human_identity_materialized") is False
    checks["no_new_external_engine_execution"]=cfg.get("external_engine_execution") is False
    checks["no_numeric_historical_truth_claim"]=cfg.get("numeric_historical_truth_claimed") is False
    checks["canonical_state_unchanged"]=cfg.get("canonical_state_changed") is False
    checks["derived_refinement_not_promoted"]=cfg.get("derived_refinement_promoted_to_canon") is False
    checks["deep_biological_coupling_off"]=cfg.get("deep_biological_coupling") is False
    failed=[k for k,v in checks.items() if not bool(v)]

    out.mkdir(parents=True,exist_ok=True)
    binding={"stage":STAGE,"status":"R58_PARENT_AUTHORITY_BINDING","r57_final_seal_sha256":sha256_file(root/R57_SEAL),"r327_final_seal_audit_sha256":sha256_file(root/R327_SEAL_AUDIT),"r327_output_manifest_sha256":sha256_file(root/R327_OUTPUT_MANIFEST),"r327_trajectories_sha256":sha256_file(root/R327_TRAJECTORIES),"r321_historical_closure_sha256":sha256_file(root/R321_CLOSURE),"r321_present_lineage_registry_sha256":sha256_file(root/R321_REGISTRY),"r55_output_manifest_sha256":sha256_file(root/R55_MANIFEST),"r56_output_manifest_sha256":sha256_file(root/R56_MANIFEST),"binding_semantics":"SEALED_R327_PLUS_DIRECT_R321_PROVENANCE_PLUS_SEALED_R57_REFINEMENT_CONTEXT"}
    write_json(out/"R5_8_PARENT_AUTHORITY_BINDING.json",binding)
    write_json(out/"R5_8_LINEAGE_EVENT_LEDGER.json",{"stage":STAGE,"status":"R58_DIRECT_LINEAGE_EVENT_LEDGER","window":{"start_age_ma":START_AGE_MA,"end_age_ma":END_AGE_MA},"target_cohort":list(TARGET_COHORT),"records":ledger,"semantics":"ONLY_DIRECT_R3_21_SPECIES_FIELD_ATTESTATION_COUNTS_AS_DISCRETE_HISTORY"})
    write_json(out/"R5_8_MACRO_REPLAY_ALIGNMENT.json",{"stage":STAGE,"status":"R58_R327_MACRO_REPLAY_ALIGNMENT","target_cohort":list(TARGET_COHORT),"age_state_count":len(ages),"variable_names":varnames,"records":macro,"semantics":"ENSEMBLE_STATE_ENVELOPES_ARE_R327_CONDITIONED_MACRO_REPLAY_NOT_DISCRETE_EVENT_HISTORY_OR_LITERAL_NUMERIC_TRUTH"})
    write_json(out/"R5_8_CONTACT_SCHEDULE_ALIGNMENT.json",{"stage":STAGE,"status":"R58_R55_R56_CONTACT_SCHEDULE_ALIGNMENT",**contact_alignment})
    handoff={"stage":STAGE,"status":"R58_RECONCILED_200KA_HANDOFF","age_ka":200.0,"candidate_cohort":list(TARGET_COHORT),"candidate_count":2,"source_r327_checkpoint_sha256":sha256_file(root/R327_CHECKPOINT),"source_r57_final_seal_sha256":sha256_file(root/R57_SEAL),"lineage_event_ledger_semantics":"DIRECT_R3_21_HISTORY_PRESERVED","macro_replay_semantics":"R3_27_SEALED_CONDITIONED_TRAJECTORY","r57_refinement_semantics":"SEALED_GOVERNED_CONTEXT_NO_LITERAL_HISTORY_PROMOTION","unique_human_identity_materialized":False,"ready_for_high_resolution_200ka_to_0_reconciliation":not failed}
    write_json(out/"R5_8_200KA_RECONCILED_HANDOFF.json",handoff)
    audit={"stage":STAGE,"status":FINAL_STATUS if not failed else "BLOCKED_R58_3MA_200KA_HOMINID_HISTORY_RECONCILIATION","scientific_candidate_eligible":not failed,"checks_passed":len(checks)-len(failed),"checks_total":len(checks),"failed":failed,"checks":checks,"summary":{"target_cohort":list(TARGET_COHORT),"target_count":2,"lineages_preexisting_at_3ma":2,"direct_in_window_event_count":sum(x["direct_in_window_event_count"] for x in ledger),"direct_event_ids":all_event_ids,"r327_age_states":len(ages),"r55_cross_lineage_pairs":len(pair_ids),"r56_schedule_classes":int(p56.get("schedule_class_count",-1)),"new_external_engine_execution_performed":False,"numeric_historical_truth_claimed":False,"final_human_species_identity_materialized":False,"canonical_state_changed":False,"derived_refinement_promoted_to_canon":False,"deep_biological_coupling":False},"recommended_next_action":"START_HIGH_RESOLUTION_200KA_TO_0_RECONCILIATION_FROM_R58_HANDOFF_WITH_RUNTIME_UTILITY_REVIEW_BEFORE_NEW_ENGINE_EXECUTION"}
    write_json(out/"R5_8_INTEGRATED_RECONCILIATION.json",audit)
    artifacts=["R5_8_PARENT_AUTHORITY_BINDING.json","R5_8_LINEAGE_EVENT_LEDGER.json","R5_8_MACRO_REPLAY_ALIGNMENT.json","R5_8_CONTACT_SCHEDULE_ALIGNMENT.json","R5_8_200KA_RECONCILED_HANDOFF.json","R5_8_INTEGRATED_RECONCILIATION.json"]
    files={name:{"bytes":(out/name).stat().st_size,"sha256":sha256_file(out/name)} for name in artifacts}
    write_json(out/"R5_8_OUTPUT_MANIFEST.json",{"stage":STAGE,"status":audit["status"],"files":files})
    return audit

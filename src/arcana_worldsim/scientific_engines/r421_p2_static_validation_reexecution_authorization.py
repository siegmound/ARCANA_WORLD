from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib, json, ast

STAGE='v0.6D1-R4.21'
PARENT_SEALED='PASS_R420_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT_AND_TARGET_DESIGN_PROTOCOL_REPAIR_SEALED'
COMPLETE='PASS_R421_P2_ADAPTER_IMPLEMENTATION_STATIC_VALIDATION_AND_SYMMETRIC_REEXECUTION_AUTHORIZATION_COMPLETE'
SEALED='PASS_R421_P2_ADAPTER_IMPLEMENTATION_STATIC_VALIDATION_AND_SYMMETRIC_REEXECUTION_AUTHORIZATION_SEALED'
BLOCKED='BLOCKED_R421_PARENT_PREFLIGHT_STATIC_VALIDATION_OR_AUTHORIZATION_FAILURE'
CFG=Path('configs/world1_r421_p2_static_validation_reexecution_authorization_v0_6D1_R4_21.json')
PSEAL=Path('outputs/v0_6D1_R4_20_SEAL/R4_20_FINAL_SEAL_AUDIT.json')
PAUDIT=Path('outputs/v0_6D1_R4_20/R4_20_INTEGRATED_AUDIT.json')
P2PF=Path('outputs/v0_6D1_R4_20/R4_20_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT.json')
TP=Path('outputs/v0_6D1_R4_20/R4_20_TARGET_DESIGN_PROTOCOL_REPAIR.json')
PPLAN=Path('outputs/v0_6D1_R4_20/R4_20_R421_STATIC_VALIDATION_AND_REEXECUTION_AUTHORIZATION_PLAN.json')
R42=Path('outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json')
OUT=Path('outputs/v0_6D1_R4_21')
SEAL=Path('outputs/v0_6D1_R4_21_SEAL/R4_21_FINAL_SEAL_AUDIT.json')
CANDIDATES={
 'NEMO':Path('benchmarks/r421/nemo_r421.py'),
 'SLiM':Path('benchmarks/r421/slim_r421.py'),
 'CDMetaPOP':Path('benchmarks/r421/cdmetapop_r421_matched.py'),
 'Geonomics':Path('benchmarks/r421/geonomics_r421.py'),
}

@dataclass(frozen=True)
class Check:
    name:str; passed:bool; detail:Any=None
    def d(self): return {'name':self.name,'pass':bool(self.passed),'detail':self.detail}

def load(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p:Path,o:Any):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def expected_jobs_by_engine(r42:dict[str,Any])->dict[str,list[str]]:
    out={}
    for j in r42.get('jobs') or []:
        out.setdefault(str(j.get('engine')),[]).append(str(j.get('job_id')))
    return {k:sorted(v) for k,v in out.items()}

def _candidate_static_audit(root:Path,engine:str)->dict[str,Any]:
    p=root/CANDIDATES[engine]; rec={'engine':engine,'path':str(CANDIDATES[engine]),'present':p.exists(),'sha256':None,'python_syntax_ok':False,'required_tokens_ok':False,'forbidden_tokens_absent':False,'required_tokens':[],'missing_required_tokens':[],'forbidden_tokens_found':[]}
    if not p.exists():return rec
    text=p.read_text(encoding='utf-8',errors='replace');rec['sha256']=sha256(p)
    try:ast.parse(text);rec['python_syntax_ok']=True
    except SyntaxError:pass
    req={
      'NEMO':['engine_input','replicates','seed','qfreq','mean_expected_heterozygosity','mean_population_frequency_range','comparison_target_used'],
      'SLiM':['engine_input','replicates','seed','treeSeqOutput','ts.Fst','DIVERSITY_NOT_ANCESTRY_CONTRIBUTION','comparison_target_used'],
      'CDMetaPOP':['engine_input','replicates','seed','summary_popAllTime.csv','matched_control_population_effect_ratio','PROXY_ONLY','REPAIR_PROFILE','comparison_target_used'],
      'Geonomics':['engine_input','replicates','seed','CANONICAL_SPATIAL_BINDING_MATERIALIZED','make_model','default_model_used','comparison_target_used'],
    }[engine]
    forb={
      'NEMO':["c['comparison_target']",'comparison_target_end_state'],
      'SLiM':["c['comparison_target']",'comparison_target_end_state'],
      'CDMetaPOP':["c['comparison_target']",'comparison_target_end_state',"'ind' in p.name.lower()"],
      'Geonomics':['run_default_model',"c['comparison_target']",'comparison_target_end_state'],
    }[engine]
    rec['required_tokens']=req;rec['missing_required_tokens']=[x for x in req if x not in text];rec['forbidden_tokens_found']=[x for x in forb if x in text];rec['required_tokens_ok']=not rec['missing_required_tokens'];rec['forbidden_tokens_absent']=not rec['forbidden_tokens_found'];return rec

def _parent_source_integrity(root:Path,records:list[dict[str,Any]],engine:str)->dict[str,Any]:
    srcs=[]
    for r in records:
        if str(r.get('resolved_engine'))!=engine:continue
        for s in r.get('parent_adapter_source_candidates') or []:
            key=(str(s.get('path')),str(s.get('sha256')))
            if key not in [(x['path'],x['registered_sha256']) for x in srcs]:
                p=root/str(s.get('path')); obs=sha256(p) if p.exists() else None
                srcs.append({'path':str(s.get('path')),'registered_sha256':str(s.get('sha256')),'present':p.exists(),'observed_sha256':obs,'hash_match':obs==str(s.get('sha256'))})
    return {'engine':engine,'source_count':len(srcs),'sources':srcs,'all_present_and_hash_match':bool(srcs) and all(x['present'] and x['hash_match'] for x in srcs)}

def _cdmetapop_profile_audit(root:Path,jobs:list[str])->dict[str,Any]:
    rows=[]
    for jid in jobs:
        p=root/'outputs/v0_6D1_R4_7/jobs'/jid/'REPAIR_PROFILE.json'; ok=False; detail=None
        if p.exists():
            try:
                o=load(p); rp=o.get('repair_profile') or {}; ok=o.get('job_id')==jid and rp.get('comparison_target_used') is False and isinstance(rp.get('bounded_end_support_ratio'),(int,float)); detail={'job_id':o.get('job_id'),'forcing_source':rp.get('forcing_source'),'bounded_end_support_ratio':rp.get('bounded_end_support_ratio'),'comparison_target_used':rp.get('comparison_target_used')}
            except Exception as exc:detail={'error':repr(exc)}
        rows.append({'job_id':jid,'path':str(p.relative_to(root)) if p.is_absolute() and root in p.parents else str(p),'present':p.exists(),'valid':ok,'detail':detail})
    return {'required_job_count':len(jobs),'valid_profile_count':sum(x['valid'] for x in rows),'all_profiles_valid':bool(jobs) and all(x['valid'] for x in rows),'records':rows}

def _geonomics_binding_audit(root:Path,jobs:list[str])->dict[str,Any]:
    rows=[]
    # R4.21 deliberately refuses to synthesize a spatial landscape from scalar descriptors.
    # A separately materialized, hash-bound canonical profile is required per frozen job.
    for jid in jobs:
        candidates=[root/'outputs/v0_6D1_R4_20/geonomics_profiles'/jid/'LANDSCAPE_PROFILE.json',root/'outputs/v0_6D1_R4_21/geonomics_profiles'/jid/'LANDSCAPE_PROFILE.json']
        chosen=next((p for p in candidates if p.exists()),None); valid=False; detail=None
        if chosen:
            try:
                o=load(chosen); src=o.get('canonical_spatial_source') or {}; sp=root/str(src.get('path','')); valid=o.get('job_id')==jid and o.get('profile_status')=='CANONICAL_SPATIAL_BINDING_MATERIALIZED' and o.get('comparison_target_used') is False and sp.exists() and sha256(sp)==src.get('sha256') and bool(o.get('geonomics_parameters_file')); detail={'profile_status':o.get('profile_status'),'canonical_spatial_source':src,'geonomics_parameters_file':o.get('geonomics_parameters_file')}
            except Exception as exc:detail={'error':repr(exc)}
        rows.append({'job_id':jid,'profile_path':str(chosen.relative_to(root)) if chosen else None,'present':chosen is not None,'valid':valid,'detail':detail})
    return {'required_job_count':len(jobs),'valid_profile_count':sum(x['valid'] for x in rows),'all_profiles_valid':bool(jobs) and all(x['valid'] for x in rows),'records':rows,'scalar_descriptor_synthesis_forbidden':True}

def static_validate_p2(root:Path,pf:dict[str,Any],r42:dict[str,Any])->dict[str,Any]:
    expected=expected_jobs_by_engine(r42); recs=pf.get('records') or []; engines=sorted({str(r.get('resolved_engine')) for r in recs if r.get('resolved_engine')}); family=[]
    for eng in engines:
        er=[r for r in recs if str(r.get('resolved_engine'))==eng]; exp=expected.get(eng,[]); declared=sorted(set(x for r in er for x in (r.get('frozen_engine_job_ids') or []))); scope_ok=all(r.get('symmetric_reexecution_scope')=='ALL_FROZEN_R4_2_JOBS_FOR_SHARED_ENGINE_ADAPTER' for r in er) and declared==exp
        cand=_candidate_static_audit(root,eng); parent=_parent_source_integrity(root,recs,eng)
        extra={'type':'NONE','ready':True}
        if eng=='CDMetaPOP':
            a=_cdmetapop_profile_audit(root,exp);extra={'type':'R47_REPAIR_PROFILE_BINDING','ready':a['all_profiles_valid'],'audit':a}
        elif eng=='Geonomics':
            a=_geonomics_binding_audit(root,exp);extra={'type':'CANONICAL_SPATIAL_BINDING_PROFILE','ready':a['all_profiles_valid'],'audit':a}
        static_ok=bool(scope_ok and cand['present'] and cand['python_syntax_ok'] and cand['required_tokens_ok'] and cand['forbidden_tokens_absent'] and parent['all_present_and_hash_match'] and extra['ready'])
        disposition='AUTHORIZED_FOR_R422_SYMMETRIC_REEXECUTION_PREPARE' if static_ok else 'DEFERRED_STATIC_IMPLEMENTATION_OR_BINDING_COMPLETION_REQUIRED'
        family.append({'engine':eng,'p2_cell_count':len(er),'expected_frozen_job_ids':exp,'declared_frozen_job_ids':declared,'symmetric_scope_exact':scope_ok,'candidate_adapter':cand,'parent_source_integrity':parent,'engine_specific_binding':extra,'static_validation_pass':static_ok,'authorization_disposition':disposition,'engine_execution_performed_in_r421':False})
    byeng={r['engine']:r for r in family}; cells=[]
    for r in recs:
        e=byeng.get(str(r.get('resolved_engine')),{});cells.append({'window_id':r.get('window_id'),'domain':r.get('domain'),'engine':r.get('resolved_engine'),'source_stage':r.get('source_stage'),'static_validation_pass':bool(e.get('static_validation_pass')),'authorization_disposition':e.get('authorization_disposition'),'frozen_engine_job_ids':r.get('frozen_engine_job_ids') or []})
    return {'stage':STAGE,'status':'R421_P2_STATIC_VALIDATION_COMPLETE','p2_cell_count':len(cells),'engine_family_count':len(family),'authorized_engine_family_count':sum(r['static_validation_pass'] for r in family),'deferred_engine_family_count':sum(not r['static_validation_pass'] for r in family),'authorized_p2_cell_count':sum(r['static_validation_pass'] for r in cells),'deferred_p2_cell_count':sum(not r['static_validation_pass'] for r in cells),'engine_families':family,'cells':cells,'engine_execution_performed':False}

def validate_target_repairs(tp:dict[str,Any])->dict[str,Any]:
    rows=[]
    for r in tp.get('records') or []:
        disp=str(r.get('repair_disposition') or ''); active=disp!='CONTEXT_ONLY_PROXY_PRESERVED'; ok=True; reason='PRESERVED_CONTEXT_ONLY_PROXY'
        if disp=='CANONICAL_DESCRIPTOR_EXTRACTOR_SPEC_FROZEN':
            req=r.get('required_fields') or []; ok=len(req)>=7 and r.get('external_result_may_define_target') is False and r.get('numeric_target_materialized_in_r420') is False; reason='STATIC_EXTRACTOR_SCHEMA_READY_FOR_SOURCE_BOUND_IMPLEMENTATION' if ok else 'BLOCKED_EXTRACTOR_SCHEMA_INCOMPLETE'
        elif disp=='TARGET_DESIGN_REQUIREMENTS_FROZEN_NO_NUMERIC_TARGET_INVENTED':
            req=r.get('required_fields') or []; ok=len(req)>=7 and r.get('external_result_may_define_target') is False and r.get('numeric_target_materialized_in_r420') is False; reason='TARGET_DESIGN_SCHEMA_READY_SOURCE_AUTHORITY_STILL_REQUIRED' if ok else 'BLOCKED_TARGET_DESIGN_SCHEMA_INCOMPLETE'
        elif disp=='R418_REJECTION_CAUSE_PRESERVED_AND_REPAIR_SPEC_FROZEN':
            ok=r.get('numeric_value_change_authorized') is False and r.get('external_result_may_define_target') is False; reason='R418_REJECTION_REPAIR_SCHEMA_READY_WITH_NUMERIC_VALUE_FROZEN' if ok else 'BLOCKED_REJECTION_REPAIR_POLICY_VIOLATION'
        elif disp=='CONTEXT_ONLY_PROXY_PRESERVED': ok=True
        else: ok=False; reason='UNKNOWN_REPAIR_DISPOSITION_FAIL_CLOSED'
        rows.append({'window_id':r.get('window_id'),'domain':r.get('domain'),'repair_disposition':disp,'active':active,'static_validation_pass':ok,'static_validation_reason':reason,'numeric_target_execution_authorized_in_r421':False})
    active=[r for r in rows if r['active']]; return {'stage':STAGE,'status':'R421_TARGET_REPAIR_STATIC_VALIDATION_COMPLETE','record_count':len(rows),'active_count':len(active),'context_only_count':sum(not r['active'] for r in rows),'active_static_validation_pass_count':sum(r['static_validation_pass'] for r in active),'records':rows,'numeric_target_execution_authorized':False}

def build_authorization(p2v:dict[str,Any],targetv:dict[str,Any],r42:dict[str,Any])->dict[str,Any]:
    auth=[r for r in p2v.get('engine_families') or [] if r.get('static_validation_pass')]; deff=[r for r in p2v.get('engine_families') or [] if not r.get('static_validation_pass')]
    job_ids=sorted(set(j for r in auth for j in r.get('expected_frozen_job_ids') or [])); expected=expected_jobs_by_engine(r42)
    jobs=[j for j in (r42.get('jobs') or []) if str(j.get('job_id')) in job_ids]
    if auth and deff: nxt='BUILD_R422_AUTHORIZED_P2_SYMMETRIC_REEXECUTION_AND_DEFERRED_IMPLEMENTATION_COMPLETION'
    elif auth: nxt='BUILD_R422_AUTHORIZED_P2_SYMMETRIC_REEXECUTION_AND_EVIDENCE_COLLECTION'
    else: nxt='BUILD_R422_P2_IMPLEMENTATION_COMPLETION_NO_ENGINE_EXECUTION'
    return {'stage':STAGE,'status':'R421_SYMMETRIC_REEXECUTION_AUTHORIZATION_FROZEN','authorized_engine_families':[r['engine'] for r in auth],'deferred_engine_families':[r['engine'] for r in deff],'authorized_job_count':len(jobs),'authorized_job_ids':[j['job_id'] for j in jobs],'authorized_jobs':jobs,'authorization_scope':'ALL_FROZEN_R4_2_JOBS_FOR_EACH_AUTHORIZED_SHARED_ENGINE_ADAPTER','frozen_seed_ledger_source':'R4.3 JOB_CONTRACT.engine_input.replicates; exact seeds must be reused in R4.22','target_repair_execution_authorized':False,'p3_execution_authorized':False,'engine_execution_performed_in_r421':False,'next_action':nxt}

def build(root:Path)->dict[str,Any]:
    cfg=load(root/CFG); checks=[]
    pseal=load(root/PSEAL) if (root/PSEAL).exists() else {}; pa=load(root/PAUDIT) if (root/PAUDIT).exists() else {}; pf=load(root/P2PF) if (root/P2PF).exists() else {};tp=load(root/TP) if (root/TP).exists() else {};pp=load(root/PPLAN) if (root/PPLAN).exists() else {};r42=load(root/R42) if (root/R42).exists() else {}
    checks += [
      Check('parent_r420_seal_present',(root/PSEAL).exists(),str(PSEAL)),Check('parent_r420_sealed',pseal.get('status')==PARENT_SEALED,pseal.get('status')),Check('parent_next_action_matches_r421',pseal.get('next_action')=='BUILD_R421_P2_ADAPTER_IMPLEMENTATION_STATIC_VALIDATION_AND_SYMMETRIC_REEXECUTION_AUTHORIZATION',pseal.get('next_action')),Check('parent_p2_preflight_six',pa.get('p2_preflight_ready_cell_count')==6,pa.get('p2_preflight_ready_cell_count')),Check('parent_target_repairs_57',pa.get('active_target_protocol_repair_count')==57,pa.get('active_target_protocol_repair_count')),Check('parent_proxy_two',pa.get('proxy_context_only_count')==2,pa.get('proxy_context_only_count')),Check('parent_p3_six',pa.get('p3_backlog_cell_count')==6,pa.get('p3_backlog_cell_count')),Check('parent_r421_plan_frozen',pp.get('status')=='R420_IMPLEMENTATION_PREFLIGHT_AND_TARGET_PROTOCOL_REPAIR_FROZEN',pp.get('status')),Check('r42_exact_23_jobs',r42.get('job_count')==23 and len(r42.get('jobs') or [])==23,r42.get('job_count')),Check('policy_frozen',cfg.get('policy_freeze')=='FROZEN_PRE_P2_STATIC_VALIDATION_AND_REEXECUTION_AUTHORIZATION',cfg.get('policy_freeze')),Check('engine_execution_forbidden_in_r421',cfg.get('engine_execution_performed') is False),Check('canonical_state_unchanged',cfg.get('canonical_state_changed') is False),Check('canonical_replay_not_authorized',cfg.get('canonical_replay_authorized') is False),Check('canonical_parameter_change_not_authorized',cfg.get('canonical_parameter_change_authorized') is False),Check('deep_off',cfg.get('deep_biological_coupling') is False),Check('majority_vote_forbidden',cfg.get('majority_vote') is False)]
    if not all(c.passed for c in checks):
        out={'stage':STAGE,'status':BLOCKED,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],'engine_execution_performed':False,'canonical_state_changed':False,'next_action':'REPAIR_R421_PARENT_OR_PREFLIGHT_INPUTS'};write(root/OUT/'R4_21_INTEGRATED_AUDIT.json',out);return out
    p2v=static_validate_p2(root,pf,r42);tv=validate_target_repairs(tp);auth=build_authorization(p2v,tv,r42)
    terminal=len(p2v.get('cells') or [])==6 and p2v.get('authorized_p2_cell_count',0)+p2v.get('deferred_p2_cell_count',0)==6
    checks += [
      Check('all_six_p2_cells_receive_terminal_static_disposition',terminal,{'authorized':p2v.get('authorized_p2_cell_count'),'deferred':p2v.get('deferred_p2_cell_count')}),Check('all_p2_engine_families_have_candidate_source',all(r.get('candidate_adapter',{}).get('present') for r in p2v.get('engine_families') or [])),Check('all_p2_candidate_sources_python_syntax_valid',all(r.get('candidate_adapter',{}).get('python_syntax_ok') for r in p2v.get('engine_families') or [])),Check('all_p2_candidate_sources_target_leakage_static_guard_pass',all(r.get('candidate_adapter',{}).get('forbidden_tokens_absent') for r in p2v.get('engine_families') or [])),Check('all_parent_adapter_sources_hash_preserved',all(r.get('parent_source_integrity',{}).get('all_present_and_hash_match') for r in p2v.get('engine_families') or [])),Check('authorization_scope_only_full_frozen_engine_job_sets',all(r.get('symmetric_scope_exact') for r in p2v.get('engine_families') or [])),Check('geonomics_requires_explicit_canonical_spatial_binding',all(r.get('engine')!='Geonomics' or r.get('engine_specific_binding',{}).get('type')=='CANONICAL_SPATIAL_BINDING_PROFILE' for r in p2v.get('engine_families') or [])),Check('cdmetapop_requires_r47_profile_binding',all(r.get('engine')!='CDMetaPOP' or r.get('engine_specific_binding',{}).get('type')=='R47_REPAIR_PROFILE_BINDING' for r in p2v.get('engine_families') or [])),Check('target_repair_records_59',tv.get('record_count')==59,tv.get('record_count')),Check('target_active_repairs_57',tv.get('active_count')==57,tv.get('active_count')),Check('target_context_only_two',tv.get('context_only_count')==2,tv.get('context_only_count')),Check('all_active_target_repair_schemas_static_valid',tv.get('active_static_validation_pass_count')==57,tv.get('active_static_validation_pass_count')),Check('no_numeric_target_execution_authorized',tv.get('numeric_target_execution_authorized') is False),Check('authorized_job_ids_are_r42_subset',set(auth.get('authorized_job_ids') or []).issubset({j.get('job_id') for j in r42.get('jobs') or []}),auth.get('authorized_job_ids')),Check('no_engine_execution_in_r421',cfg.get('engine_execution_performed') is False),Check('canonical_state_still_unchanged',cfg.get('canonical_state_changed') is False)]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    out={'stage':STAGE,'status':status,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],'p2_authorized_cell_count':p2v.get('authorized_p2_cell_count'),'p2_deferred_cell_count':p2v.get('deferred_p2_cell_count'),'authorized_engine_families':auth.get('authorized_engine_families'),'deferred_engine_families':auth.get('deferred_engine_families'),'authorized_job_count':auth.get('authorized_job_count'),'active_target_protocol_repair_count':tv.get('active_count'),'proxy_context_only_count':tv.get('context_only_count'),'p3_backlog_cell_count':6,'engine_execution_performed':False,'canonical_state_changed':False,'next_action':auth.get('next_action')}
    write(root/OUT/'R4_21_P2_STATIC_VALIDATION.json',p2v);write(root/OUT/'R4_21_TARGET_REPAIR_STATIC_VALIDATION.json',tv);write(root/OUT/'R4_21_SYMMETRIC_REEXECUTION_AUTHORIZATION.json',auth);write(root/OUT/'R4_21_R422_EXECUTION_PLAN.json',auth);write(root/OUT/'R4_21_INTEGRATED_AUDIT.json',out);return out

def final_seal(root:Path)->dict[str,Any]:
    p=load(root/PSEAL) if (root/PSEAL).exists() else {};a=load(root/OUT/'R4_21_INTEGRATED_AUDIT.json') if (root/OUT/'R4_21_INTEGRATED_AUDIT.json').exists() else {};v=load(root/OUT/'R4_21_P2_STATIC_VALIDATION.json') if (root/OUT/'R4_21_P2_STATIC_VALIDATION.json').exists() else {};t=load(root/OUT/'R4_21_TARGET_REPAIR_STATIC_VALIDATION.json') if (root/OUT/'R4_21_TARGET_REPAIR_STATIC_VALIDATION.json').exists() else {};auth=load(root/OUT/'R4_21_SYMMETRIC_REEXECUTION_AUTHORIZATION.json') if (root/OUT/'R4_21_SYMMETRIC_REEXECUTION_AUTHORIZATION.json').exists() else {}
    checks=[Check('parent_r420_sealed',p.get('status')==PARENT_SEALED,p.get('status')),Check('r421_complete',a.get('status')==COMPLETE,a.get('status')),Check('r421_zero_process_failures',a.get('checks_failed')==0,a.get('checks_failed')),Check('all_six_p2_terminally_disposed',v.get('p2_cell_count')==6 and v.get('authorized_p2_cell_count',0)+v.get('deferred_p2_cell_count',0)==6,{'authorized':v.get('authorized_p2_cell_count'),'deferred':v.get('deferred_p2_cell_count')}),Check('authorization_registry_frozen',auth.get('status')=='R421_SYMMETRIC_REEXECUTION_AUTHORIZATION_FROZEN',auth.get('status')),Check('authorized_scope_full_engine_sets',auth.get('authorization_scope')=='ALL_FROZEN_R4_2_JOBS_FOR_EACH_AUTHORIZED_SHARED_ENGINE_ADAPTER',auth.get('authorization_scope')),Check('target_active_repairs_57',t.get('active_count')==57,t.get('active_count')),Check('target_execution_not_authorized',auth.get('target_repair_execution_authorized') is False),Check('p3_execution_not_authorized',auth.get('p3_execution_authorized') is False),Check('no_engine_execution',a.get('engine_execution_performed') is False),Check('canonical_state_unchanged',a.get('canonical_state_changed') is False),Check('next_action_present',a.get('next_action')==auth.get('next_action') and bool(a.get('next_action')),a.get('next_action'))]
    ok=all(c.passed for c in checks);out={'stage':STAGE,'audit':'FINAL_P2_ADAPTER_IMPLEMENTATION_STATIC_VALIDATION_AND_SYMMETRIC_REEXECUTION_AUTHORIZATION','status':SEALED if ok else BLOCKED,'verdict':'SEALED' if ok else 'BLOCKED','checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],'summary':{'p2_authorized_cell_count':a.get('p2_authorized_cell_count'),'p2_deferred_cell_count':a.get('p2_deferred_cell_count'),'authorized_engine_families':a.get('authorized_engine_families'),'deferred_engine_families':a.get('deferred_engine_families'),'authorized_job_count':a.get('authorized_job_count'),'active_target_protocol_repair_count':a.get('active_target_protocol_repair_count'),'proxy_context_only_count':a.get('proxy_context_only_count'),'p3_backlog_cell_count':a.get('p3_backlog_cell_count'),'engine_execution_performed':False,'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'deep_biological_coupling':False,'next_action':a.get('next_action')},'next_action':a.get('next_action')}
    write(root/SEAL,out);return out

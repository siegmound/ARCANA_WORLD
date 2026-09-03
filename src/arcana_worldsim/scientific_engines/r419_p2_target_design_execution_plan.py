from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

STAGE='v0.6D1-R4.19'
PARENT_SEALED='PASS_R418_TARGET_MATERIALIZATION_VALIDATION_PARTIAL_READJUDICATION_AND_P2_BACKLOG_FREEZE_SEALED'
COMPLETE='PASS_R419_P2_ADAPTER_ENHANCEMENT_AND_TARGET_DESIGN_BACKLOG_EXECUTION_PLAN_COMPLETE'
SEALED='PASS_R419_P2_ADAPTER_ENHANCEMENT_AND_TARGET_DESIGN_BACKLOG_EXECUTION_PLAN_SEALED'
BLOCKED='BLOCKED_R419_PARENT_BACKLOG_OR_EXECUTION_PLAN_FAILURE'
NEXT='BUILD_R420_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT_AND_TARGET_DESIGN_PROTOCOL_REPAIR'
CFG=Path('configs/world1_r419_p2_adapter_target_design_execution_plan_v0_6D1_R4_19.json')
PSEAL=Path('outputs/v0_6D1_R4_18_SEAL/R4_18_FINAL_SEAL_AUDIT.json')
PAUDIT=Path('outputs/v0_6D1_R4_18/R4_18_INTEGRATED_AUDIT.json')
P2FREEZE=Path('outputs/v0_6D1_R4_18/R4_18_P2_BACKLOG_FREEZE.json')
PVAL=Path('outputs/v0_6D1_R4_18/R4_18_TARGET_MATERIALIZATION_VALIDATION.json')
P417T=Path('outputs/v0_6D1_R4_17/R4_17_ARCANA_TARGET_EXTRACTOR_RESULTS.json')
P417M=Path('outputs/v0_6D1_R4_17/R4_17_RECOVERED_METRIC_PROMOTION_CLOSURE.json')
R42JOBS=Path('outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json')
R413=Path('outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json')
OUT=Path('outputs/v0_6D1_R4_19')
SEAL=Path('outputs/v0_6D1_R4_19_SEAL/R4_19_FINAL_SEAL_AUDIT.json')

@dataclass(frozen=True)
class Check:
    name:str; passed:bool; detail:Any=None
    def d(self): return {'name':self.name,'pass':bool(self.passed),'detail':self.detail}

def load(p:Path)->Any: return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p:Path,o:Any):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def _infer_engine(rec:dict[str,Any], parent_rows:list[dict[str,Any]])->tuple[str|None,str]:
    if rec.get('engine'): return str(rec['engine']),'EXPLICIT_PARENT_BACKLOG_ENGINE'
    action=str(rec.get('closure_action') or '').upper()
    if 'GEONOMICS' in action: return 'Geonomics','CLOSURE_ACTION_ENGINE_BINDING'
    w,d=rec.get('window_id'),rec.get('domain')
    eng=sorted({str(r.get('engine')) for r in parent_rows if r.get('window_id')==w and r.get('domain')==d and r.get('authority_role')=='PRIMARY' and r.get('engine')})
    if len(eng)==1:return eng[0],'UNIQUE_PRIMARY_ENGINE_FOR_CELL'
    return None,'ENGINE_UNRESOLVED_FAIL_CLOSED'

def _job_list(obj:dict[str,Any])->list[dict[str,Any]]:
    x=obj.get('jobs')
    if isinstance(x,list): return [r for r in x if isinstance(r,dict)]
    x=obj.get('records')
    if isinstance(x,list): return [r for r in x if isinstance(r,dict)]
    return []

def _job_id(j:dict[str,Any])->str|None:
    for k in ('job_id','id'):
        if j.get(k): return str(j[k])
    return None

def _engine_jobs(jobs:list[dict[str,Any]],engine:str|None)->list[str]:
    if not engine:return []
    out=[]
    for j in jobs:
        if str(j.get('engine') or '').lower()==engine.lower():
            jid=_job_id(j)
            if jid: out.append(jid)
    return sorted(set(out))

def _p2_mechanism(rec:dict[str,Any])->str:
    src=str(rec.get('source_stage') or '')
    action=str(rec.get('closure_action') or '').upper()
    reason=str(rec.get('reason') or '').upper()
    if 'GEONOMICS' in action or 'SEMANTIC_NONCOMPARABILITY' in reason:
        return 'INPUT_SEMANTIC_ADAPTER_ENHANCEMENT'
    if src=='R4.15-R1':
        return 'OUTPUT_METRIC_EXTRACTION_OR_RUNTIME_BINDING_ENHANCEMENT'
    if src=='R4.17':
        return 'DOMAIN_METRIC_SEMANTIC_ADAPTER_OR_MATCHED_PROTOCOL_ENHANCEMENT'
    return 'EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT'

def build_p2_plan(p2:dict[str,Any],jobs_obj:dict[str,Any],parent_rows:list[dict[str,Any]])->dict[str,Any]:
    jobs=_job_list(jobs_obj); records=[]
    for r in p2.get('records') or []:
        engine,basis=_infer_engine(r,parent_rows)
        sym=_engine_jobs(jobs,engine)
        records.append({
            **r,
            'resolved_engine':engine,
            'engine_resolution_basis':basis,
            'enhancement_mechanism':_p2_mechanism(r),
            'frozen_engine_job_ids':sym,
            'symmetric_reexecution_scope':'ALL_FROZEN_R4_2_JOBS_FOR_SHARED_ENGINE_ADAPTER' if sym else 'UNRESOLVED_NO_EXECUTION',
            'adapter_implementation_authorized_in_r419':False,
            'engine_reexecution_authorized_in_r419':False,
            'r42_registry_mutation_authorized':False,
            'result_selected_scope':False,
        })
    families=sorted({r['resolved_engine'] for r in records if r.get('resolved_engine')})
    return {'stage':STAGE,'status':'R419_P2_EXECUTION_PLAN_FROZEN','cell_count':len(records),'engine_families':families,'records':records,'execution_authorized':False,'r42_registry_mutation_authorized':False}

def build_target_plan(targ:dict[str,Any],val:dict[str,Any])->dict[str,Any]:
    vals={(r.get('window_id'),r.get('domain')):r for r in (val.get('records') or [])}
    recs=[]; active=0; proxy=0
    for r in targ.get('records') or []:
        w,d=r.get('window_id'),r.get('domain'); st=str(r.get('materialization_status') or ''); comp=str(r.get('candidate_comparability') or '')
        if comp=='PROXY_ONLY' and r.get('materialized_target') is not None:
            cls='CONTEXT_ONLY_PROXY_PRESERVE'; pr='P4_PRESERVE_NONADJUDICATIVE_UNLESS_NEW_PROTOCOL'; proxy+=1
        elif st=='SOURCE_CANDIDATES_INSPECTED_NO_STRICT_TARGET_MATERIALIZED':
            cls='CANONICAL_TARGET_EXTRACTOR_OR_EXPLICIT_DESCRIPTOR_REQUIRED'; pr='P1_TARGET_EXTRACTOR_REPAIR'; active+=1
        elif st=='NO_CANONICAL_SOURCE_CANDIDATE_TARGET_DESIGN_GAP':
            cls='NEW_CANONICAL_TARGET_DESIGN_REQUIRED'; pr='P1_TARGET_DESIGN'; active+=1
        elif (w,d) in vals and vals[(w,d)].get('validation_status')!='VALIDATED_FOR_PARTIAL_READJUDICATION':
            cls='MATERIALIZED_TARGET_OR_PRIMARY_METRIC_SEMANTIC_REPAIR_REQUIRED'; pr='P1_SEMANTIC_REPAIR'; active+=1
        else:
            cls='NO_ACTIVE_TARGET_DESIGN_ACTION'; pr='PRESERVE'
        v=vals.get((w,d))
        recs.append({'window_id':w,'domain':d,'source_candidate_count':r.get('candidate_source_count'), 'materialization_status':st,'candidate_comparability':comp,'backlog_class':cls,'priority':pr,'r418_validation_status':v.get('validation_status') if v else None,'r418_validation_reason':v.get('reason') if v else None,'r418_failed_validation_fields':({k:v.get(k) for k in ['strict_target_fields_present','temporal_basis_matches_window','provenance_integrity_pass','protocol_record_present','eligible_primary_row_count']} if v and v.get('validation_status')!='VALIDATED_FOR_PARTIAL_READJUDICATION' else None),'execution_authorized_in_r419':False})
    return {'stage':STAGE,'status':'R419_TARGET_DESIGN_BACKLOG_FROZEN','total_p1_records':len(recs),'active_target_design_or_semantic_repair_count':active,'context_only_proxy_count':proxy,'records':recs,'execution_authorized':False}

def build(root:Path)->dict[str,Any]:
    cfg=load(root/CFG) if (root/CFG).exists() else {}; seal=load(root/PSEAL) if (root/PSEAL).exists() else {}; audit=load(root/PAUDIT) if (root/PAUDIT).exists() else {}; p2=load(root/P2FREEZE) if (root/P2FREEZE).exists() else {}; val=load(root/PVAL) if (root/PVAL).exists() else {}; targ=load(root/P417T) if (root/P417T).exists() else {}; jobs=load(root/R42JOBS) if (root/R42JOBS).exists() else {}; mat=load(root/R413) if (root/R413).exists() else {}
    rows=list(mat.get('evidence_rows') or [])
    ps=seal.get('summary') or {}
    checks=[
        Check('parent_r418_seal_present',(root/PSEAL).exists(),str(PSEAL)),
        Check('parent_r418_sealed',seal.get('status')==PARENT_SEALED,seal.get('status')),
        Check('parent_next_action_matches_r419',seal.get('next_action')=='BUILD_R419_P2_ADAPTER_ENHANCEMENT_AND_TARGET_DESIGN_BACKLOG_EXECUTION_PLAN',seal.get('next_action')),
        Check('parent_zero_validated_targets',ps.get('target_validated_for_partial_readjudication_count')==0,ps.get('target_validated_for_partial_readjudication_count')),
        Check('parent_zero_partial_readjudication_changes',ps.get('partial_readjudication_changed_cell_count')==0,ps.get('partial_readjudication_changed_cell_count')),
        Check('parent_zero_structural_disagreements',ps.get('structural_disagreement_count_after_partial_readjudication')==0,ps.get('structural_disagreement_count_after_partial_readjudication')),
        Check('parent_p2_backlog_six',ps.get('p2_backlog_cell_count')==6,ps.get('p2_backlog_cell_count')),
        Check('parent_p3_backlog_six',ps.get('p3_backlog_cell_count')==6,ps.get('p3_backlog_cell_count')),
        Check('p2_freeze_exact_six',p2.get('cell_count')==6 and len(p2.get('records') or [])==6,{'declared':p2.get('cell_count'),'loaded':len(p2.get('records') or [])}),
        Check('p2_parent_execution_not_authorized',p2.get('execution_authorized') is False,p2.get('execution_authorized')),
        Check('r42_frozen_jobs_present',len(_job_list(jobs))==23,len(_job_list(jobs))),
        Check('r413_parent_rows_present',len(rows)>0,len(rows)),
        Check('r417_target_records_59',len(targ.get('records') or [])==59,len(targ.get('records') or [])),
        Check('r418_validation_candidate_disposition_one',val.get('candidate_count')==1 and len(val.get('records') or [])==1,{'declared':val.get('candidate_count'),'loaded':len(val.get('records') or [])}),
        Check('policy_frozen',cfg.get('policy_freeze')=='FROZEN_PRE_P2_IMPLEMENTATION_AND_TARGET_DESIGN_EXECUTION',cfg.get('policy_freeze')),
        Check('engine_execution_forbidden',cfg.get('engine_execution_performed') is False),
        Check('canonical_state_unchanged',cfg.get('canonical_state_changed') is False),
        Check('canonical_replay_not_authorized',cfg.get('canonical_replay_authorized') is False),
        Check('canonical_parameter_change_not_authorized',cfg.get('canonical_parameter_change_authorized') is False),
        Check('deep_off',cfg.get('deep_biological_coupling') is False),
        Check('majority_vote_forbidden',cfg.get('majority_vote') is False),
    ]
    if any(not c.passed for c in checks):
        out={'stage':STAGE,'status':BLOCKED,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],'canonical_state_changed':False,'next_action':NEXT}; write(root/OUT/'R4_19_INTEGRATED_AUDIT.json',out); return out
    p2plan=build_p2_plan(p2,jobs,rows); tplan=build_target_plan(targ,val)
    unresolved=[r for r in p2plan['records'] if not r.get('resolved_engine') or not r.get('frozen_engine_job_ids')]
    unique_cells={(r.get('window_id'),r.get('domain'),r.get('source_stage')) for r in p2plan['records']}
    active_expected=57  # 44 exhausted + 12 design-gap + 1 rejected materialization; 2 proxies remain context-only.
    checks += [
        Check('all_six_p2_records_planned',p2plan.get('cell_count')==6,p2plan.get('cell_count')),
        Check('all_six_p2_records_unique',len(unique_cells)==6,len(unique_cells)),
        Check('all_p2_engines_resolved_fail_closed',not unresolved,unresolved),
        Check('all_p2_shared_adapter_scopes_symmetric',all(r.get('symmetric_reexecution_scope')=='ALL_FROZEN_R4_2_JOBS_FOR_SHARED_ENGINE_ADAPTER' for r in p2plan['records'])),
        Check('no_p2_execution_authorized_in_r419',all(r.get('engine_reexecution_authorized_in_r419') is False and r.get('adapter_implementation_authorized_in_r419') is False for r in p2plan['records'])),
        Check('all_59_target_records_planned',tplan.get('total_p1_records')==59,tplan.get('total_p1_records')),
        Check('target_active_backlog_57',tplan.get('active_target_design_or_semantic_repair_count')==active_expected,tplan.get('active_target_design_or_semantic_repair_count')),
        Check('proxy_context_only_two',tplan.get('context_only_proxy_count')==2,tplan.get('context_only_proxy_count')),
        Check('no_target_execution_authorized_in_r419',tplan.get('execution_authorized') is False),
        Check('p3_preserved_six',ps.get('p3_backlog_cell_count')==6,ps.get('p3_backlog_cell_count')),
        Check('no_r42_registry_mutation',p2plan.get('r42_registry_mutation_authorized') is False),
        Check('no_engine_execution',cfg.get('engine_execution_performed') is False),
        Check('canonical_state_still_unchanged',cfg.get('canonical_state_changed') is False),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    execplan={'stage':STAGE,'status':'R419_P2_AND_TARGET_DESIGN_EXECUTION_PLAN_FROZEN' if status==COMPLETE else BLOCKED,'p2':{'cell_count':6,'engine_families':p2plan.get('engine_families'),'implementation_next_stage':'R4.20','engine_execution_authorized_now':False},'target_design':{'active_count':tplan.get('active_target_design_or_semantic_repair_count'),'proxy_context_only_count':tplan.get('context_only_proxy_count'),'parallel_protocol_repair_authorized_now':False},'p3':{'cell_count':6,'extension_job_execution_authorized_now':False},'sequencing':['R4.20 implement and statically validate P2 adapter changes plus target-protocol repairs','later stage performs symmetric external-engine reexecution only after implementation/preflight seal','P3 extension jobs remain separate new-namespace work'],'rules':['no result-selected adapter repair','shared adapter changes require symmetric reexecution of all frozen R4.2 jobs for that engine','no target may be defined by external result','no canonical replay or parameter change'], 'next_action':NEXT}
    out={'stage':STAGE,'status':status,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],'p2_backlog_cell_count':6,'p2_engine_families':p2plan.get('engine_families'),'active_target_design_or_semantic_repair_count':tplan.get('active_target_design_or_semantic_repair_count'),'proxy_context_only_count':tplan.get('context_only_proxy_count'),'p3_backlog_cell_count':6,'engine_execution_performed':False,'canonical_state_changed':False,'next_action':NEXT}
    write(root/OUT/'R4_19_P2_ADAPTER_EXECUTION_PLAN.json',p2plan);write(root/OUT/'R4_19_TARGET_DESIGN_BACKLOG_PLAN.json',tplan);write(root/OUT/'R4_19_R420_EXECUTION_AUTHORIZATION_PLAN.json',execplan);write(root/OUT/'R4_19_INTEGRATED_AUDIT.json',out)
    return out

def final_seal(root:Path)->dict[str,Any]:
    p=load(root/PSEAL) if (root/PSEAL).exists() else {}; a=load(root/OUT/'R4_19_INTEGRATED_AUDIT.json') if (root/OUT/'R4_19_INTEGRATED_AUDIT.json').exists() else {}; p2=load(root/OUT/'R4_19_P2_ADAPTER_EXECUTION_PLAN.json') if (root/OUT/'R4_19_P2_ADAPTER_EXECUTION_PLAN.json').exists() else {}; tp=load(root/OUT/'R4_19_TARGET_DESIGN_BACKLOG_PLAN.json') if (root/OUT/'R4_19_TARGET_DESIGN_BACKLOG_PLAN.json').exists() else {}; ep=load(root/OUT/'R4_19_R420_EXECUTION_AUTHORIZATION_PLAN.json') if (root/OUT/'R4_19_R420_EXECUTION_AUTHORIZATION_PLAN.json').exists() else {}
    checks=[
        Check('parent_r418_sealed',p.get('status')==PARENT_SEALED,p.get('status')),
        Check('r419_complete',a.get('status')==COMPLETE,a.get('status')),
        Check('r419_zero_process_failures',a.get('checks_failed')==0,a.get('checks_failed')),
        Check('p2_plan_exact_six',p2.get('cell_count')==6,p2.get('cell_count')),
        Check('all_p2_engines_resolved',all(r.get('resolved_engine') and r.get('frozen_engine_job_ids') for r in p2.get('records') or [])),
        Check('target_active_backlog_57',tp.get('active_target_design_or_semantic_repair_count')==57,tp.get('active_target_design_or_semantic_repair_count')),
        Check('proxy_context_only_two',tp.get('context_only_proxy_count')==2,tp.get('context_only_proxy_count')),
        Check('p3_backlog_six',a.get('p3_backlog_cell_count')==6,a.get('p3_backlog_cell_count')),
        Check('r420_plan_frozen',ep.get('status')=='R419_P2_AND_TARGET_DESIGN_EXECUTION_PLAN_FROZEN',ep.get('status')),
        Check('no_engine_execution',a.get('engine_execution_performed') is False),
        Check('canonical_state_unchanged',a.get('canonical_state_changed') is False),
        Check('next_action_present',a.get('next_action')==NEXT,a.get('next_action')),
    ]
    ok=all(c.passed for c in checks)
    out={'stage':STAGE,'audit':'FINAL_P2_ADAPTER_ENHANCEMENT_AND_TARGET_DESIGN_BACKLOG_EXECUTION_PLAN','status':SEALED if ok else BLOCKED,'verdict':'SEALED' if ok else 'BLOCKED','checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],'summary':{'p2_backlog_cell_count':p2.get('cell_count'),'p2_engine_families':p2.get('engine_families'),'active_target_design_or_semantic_repair_count':tp.get('active_target_design_or_semantic_repair_count'),'proxy_context_only_count':tp.get('context_only_proxy_count'),'p3_backlog_cell_count':a.get('p3_backlog_cell_count'),'engine_execution_performed':False,'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'deep_biological_coupling':False,'next_action':NEXT},'next_action':NEXT}
    write(root/SEAL,out);return out

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib, json, re

STAGE='v0.6D1-R4.20'
PARENT_SEALED='PASS_R419_P2_ADAPTER_ENHANCEMENT_AND_TARGET_DESIGN_BACKLOG_EXECUTION_PLAN_SEALED'
COMPLETE='PASS_R420_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT_AND_TARGET_DESIGN_PROTOCOL_REPAIR_COMPLETE'
SEALED='PASS_R420_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT_AND_TARGET_DESIGN_PROTOCOL_REPAIR_SEALED'
BLOCKED='BLOCKED_R420_PARENT_PLAN_ADAPTER_PREFLIGHT_OR_TARGET_PROTOCOL_REPAIR_FAILURE'
NEXT='BUILD_R421_P2_ADAPTER_IMPLEMENTATION_STATIC_VALIDATION_AND_SYMMETRIC_REEXECUTION_AUTHORIZATION'
CFG=Path('configs/world1_r420_p2_adapter_preflight_target_protocol_repair_v0_6D1_R4_20.json')
PSEAL=Path('outputs/v0_6D1_R4_19_SEAL/R4_19_FINAL_SEAL_AUDIT.json')
PAUDIT=Path('outputs/v0_6D1_R4_19/R4_19_INTEGRATED_AUDIT.json')
P2PLAN=Path('outputs/v0_6D1_R4_19/R4_19_P2_ADAPTER_EXECUTION_PLAN.json')
TPLAN=Path('outputs/v0_6D1_R4_19/R4_19_TARGET_DESIGN_BACKLOG_PLAN.json')
R420AUTH=Path('outputs/v0_6D1_R4_19/R4_19_R420_EXECUTION_AUTHORIZATION_PLAN.json')
R42JOBS=Path('outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json')
OUT=Path('outputs/v0_6D1_R4_20')
SEAL=Path('outputs/v0_6D1_R4_20_SEAL/R4_20_FINAL_SEAL_AUDIT.json')

@dataclass(frozen=True)
class Check:
    name:str; passed:bool; detail:Any=None
    def d(self): return {'name':self.name,'pass':bool(self.passed),'detail':self.detail}

def load(p:Path)->Any: return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p:Path,o:Any):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def _engine_token(engine:str)->str:
    return {'CDMetaPOP':'cdmetapop','Geonomics':'geonomics','NEMO':'nemo','SLiM':'slim'}.get(engine,engine.lower())

def discover_adapter_sources(root:Path, engine:str)->list[dict[str,Any]]:
    token=_engine_token(engine)
    hits=[]
    search_roots=[root/'benchmarks',root/'scripts',root/'src']
    for base in search_roots:
        if not base.exists(): continue
        for p in base.rglob('*.py'):
            low=str(p.relative_to(root)).lower()
            if token not in low: continue
            # Exclude this stage's generic implementation module from parent-source discovery.
            if 'r420_p2_adapter_preflight_target_protocol_repair' in low: continue
            try:
                text=p.read_text(encoding='utf-8',errors='ignore')
            except Exception:
                continue
            hits.append({'path':str(p.relative_to(root)),'sha256':sha256(p),'bytes':p.stat().st_size,'mentions_engine_token':token in text.lower() or token in p.name.lower()})
    # Prefer historical benchmark adapters over generic scripts.
    hits.sort(key=lambda x:(0 if str(x['path']).lower().startswith('benchmarks') else 1,str(x['path'])))
    return hits[:64]

def engine_enhancement_contract(engine:str, mechanism:str, domain:str|None)->dict[str,Any]:
    common={
        'new_namespace':'R4.20+',
        'historical_adapter_overwrite_forbidden':True,
        'frozen_seed_preservation_required':True,
        'frozen_job_scope_preservation_required':True,
        'target_value_must_not_parameterize_engine':True,
        'scientific_result_selected_tuning_forbidden':True,
    }
    d=str(domain or '')
    if engine=='Geonomics':
        return {**common,'implementation_family':'ARCANA_LANDSCAPE_BINDING_LAYER','requirements':[
            'replace default/example landscape with explicit ARCANA window landscape descriptor',
            'bind habitat/environment support from frozen ARCANA pre-result descriptors or canonical provider artifacts',
            'preserve engine-native spatial dynamics after initialization',
            'record raster/grid provenance and start/end temporal basis',
            'fail closed if canonical landscape cannot be materialized without external-result dependence',
        ],'forbidden':['default Geonomics landscape as adjudicative evidence','post-result landscape fitting']}
    if engine=='CDMetaPOP':
        return {**common,'implementation_family':'METRIC_EXTRACTION_AND_MATCHED_CONTROL_SEMANTIC_LAYER','requirements':[
            'use summary_popAllTime.csv lifecycle semantics for population metrics',
            'retain engine-effective N0 semantics including non-natal zeroing',
            'absolute population_agent_response_ratio remains PROXY_ONLY after R4.12 neutral-invariance failure',
            'population-persistence adjudication requires a predeclared matched-control semantic protocol',
            'no filename substring selector may identify individual-population output files',
        ],'domain':d,'forbidden':['promotion of absolute response to NORMALIZABLE','legacy hindex filename collision selector']}
    if engine=='NEMO':
        return {**common,'implementation_family':'QFREQ_DOMAIN_METRIC_EXTRACTION_LAYER','requirements':[
            'parse retained/executed qfreq using explicit generation/locus/population semantics',
            'map only predeclared domain-compatible statistics',
            'heterozygosity or allele-frequency spread must not be relabeled additive genetic variance without effect-size model',
            'frequency differentiation must not be relabeled migration/gene-flow rate without causal transport mapping',
            'write metric provenance including locus aggregation and temporal basis',
        ],'domain':d,'forbidden':['heterozygosity == additive_variance','FST/frequency gap == gene_flow rate']}
    if engine=='SLiM':
        return {**common,'implementation_family':'TREE_SEQUENCE_DOMAIN_METRIC_EXTRACTION_LAYER','requirements':[
            'derive statistics only from retained/new tree sequences with explicit sample/node/population sets',
            'record generation/time conversion and population semantics',
            'diversity/FST/ancestry statistics require domain-specific identity before promotion',
            'ancestry contribution must not be inferred from generic diversity alone',
            'fail closed when tree metadata lacks the population labels required by the requested domain',
        ],'domain':d,'forbidden':['diversity == ancestry','FST == migration rate']}
    return {**common,'implementation_family':'UNSUPPORTED_ENGINE_FAIL_CLOSED','requirements':[],'domain':d}

def build_p2_preflight(root:Path,p2:dict[str,Any])->dict[str,Any]:
    recs=[]
    for r in p2.get('records') or []:
        eng=str(r.get('resolved_engine') or '')
        mech=str(r.get('enhancement_mechanism') or '')
        sources=discover_adapter_sources(root,eng) if eng else []
        contract=engine_enhancement_contract(eng,mech,r.get('domain'))
        ready=bool(eng in {'CDMetaPOP','Geonomics','NEMO','SLiM'} and sources and r.get('frozen_engine_job_ids') and r.get('symmetric_reexecution_scope')=='ALL_FROZEN_R4_2_JOBS_FOR_SHARED_ENGINE_ADAPTER')
        recs.append({
            'window_id':r.get('window_id'),'domain':r.get('domain'),'source_stage':r.get('source_stage'),
            'resolved_engine':eng,'enhancement_mechanism':mech,'frozen_engine_job_ids':r.get('frozen_engine_job_ids') or [],
            'symmetric_reexecution_scope':r.get('symmetric_reexecution_scope'),
            'parent_adapter_source_candidates':sources,
            'enhancement_contract':contract,
            'implementation_layer_status':'IMPLEMENTATION_CONTRACT_READY_FOR_STATIC_VALIDATION' if ready else 'BLOCKED_PARENT_ADAPTER_SOURCE_OR_SCOPE_NOT_RESOLVED',
            'engine_execution_authorized_in_r420':False,
            'historical_adapter_overwrite_authorized':False,
        })
    fam=sorted({r['resolved_engine'] for r in recs if r.get('resolved_engine')})
    ready=sum(r['implementation_layer_status'].startswith('IMPLEMENTATION_CONTRACT_READY') for r in recs)
    return {'stage':STAGE,'status':'R420_P2_IMPLEMENTATION_PREFLIGHT_COMPLETE' if ready==len(recs)==6 else BLOCKED,'cell_count':len(recs),'ready_count':ready,'engine_families':fam,'records':recs,'engine_execution_authorized':False}

def _repair_target_record(r:dict[str,Any])->dict[str,Any]:
    cls=str(r.get('backlog_class') or '')
    base={'window_id':r.get('window_id'),'domain':r.get('domain'),'backlog_class':cls,'priority':r.get('priority'),'external_result_may_define_target':False,'numeric_target_materialized_in_r420':False,'adjudicative_promotion_authorized_in_r420':False}
    if cls=='CANONICAL_TARGET_EXTRACTOR_OR_EXPLICIT_DESCRIPTOR_REQUIRED':
        return {**base,'repair_disposition':'CANONICAL_DESCRIPTOR_EXTRACTOR_SPEC_FROZEN','required_fields':['value_or_statistic_definition','unit_or_normalization','temporal_basis','spatial_population_basis','deterministic_transform','canonical_provenance','aggregation_or_uncertainty'],'next_priority':'R4.21_CANONICAL_TARGET_EXTRACTOR_IMPLEMENTATION'}
    if cls=='NEW_CANONICAL_TARGET_DESIGN_REQUIRED':
        return {**base,'repair_disposition':'TARGET_DESIGN_REQUIREMENTS_FROZEN_NO_NUMERIC_TARGET_INVENTED','required_fields':['scientific_construct_definition','canonical_observable_or_provider','unit_or_normalization','temporal_basis','spatial_population_basis','uncertainty_model','pre-result_transform'],'next_priority':'R4.21_TARGET_DESIGN_SOURCE_AUTHORITY_GATE'}
    if cls=='MATERIALIZED_TARGET_OR_PRIMARY_METRIC_SEMANTIC_REPAIR_REQUIRED':
        failed=r.get('r418_failed_validation_fields') or {}
        fail_keys=[k for k,v in failed.items() if (v is False or v==0 or v is None)]
        return {**base,'repair_disposition':'R418_REJECTION_CAUSE_PRESERVED_AND_REPAIR_SPEC_FROZEN','r418_validation_status':r.get('r418_validation_status'),'r418_validation_reason':r.get('r418_validation_reason'),'failed_validation_fields':failed,'failed_validation_keys':fail_keys,'numeric_value_change_authorized':False,'next_priority':'R4.21_REPAIR_ONLY_FAILED_SEMANTIC_OR_PRIMARY_METRIC_GATES'}
    if cls=='CONTEXT_ONLY_PROXY_PRESERVE':
        return {**base,'repair_disposition':'CONTEXT_ONLY_PROXY_PRESERVED','next_priority':'P4_PRESERVE_NONADJUDICATIVE'}
    return {**base,'repair_disposition':'NO_ACTIVE_REPAIR','next_priority':'PRESERVE'}

def build_target_repairs(tp:dict[str,Any])->dict[str,Any]:
    recs=[_repair_target_record(r) for r in (tp.get('records') or [])]
    active=[r for r in recs if r['backlog_class']!='CONTEXT_ONLY_PROXY_PRESERVE' and r['repair_disposition']!='NO_ACTIVE_REPAIR']
    proxies=[r for r in recs if r['backlog_class']=='CONTEXT_ONLY_PROXY_PRESERVE']
    counts={}
    for r in recs: counts[r['repair_disposition']]=counts.get(r['repair_disposition'],0)+1
    return {'stage':STAGE,'status':'R420_TARGET_DESIGN_PROTOCOL_REPAIR_FROZEN','record_count':len(recs),'active_repair_count':len(active),'context_only_proxy_count':len(proxies),'repair_disposition_counts':counts,'records':recs,'target_execution_authorized':False}

def build(root:Path)->dict[str,Any]:
    cfg=load(root/CFG) if (root/CFG).exists() else {}
    seal=load(root/PSEAL) if (root/PSEAL).exists() else {}
    audit=load(root/PAUDIT) if (root/PAUDIT).exists() else {}
    p2=load(root/P2PLAN) if (root/P2PLAN).exists() else {}
    tp=load(root/TPLAN) if (root/TPLAN).exists() else {}
    auth=load(root/R420AUTH) if (root/R420AUTH).exists() else {}
    ps=seal.get('summary') or {}
    checks=[
        Check('parent_r419_seal_present',(root/PSEAL).exists(),str(PSEAL)),
        Check('parent_r419_sealed',seal.get('status')==PARENT_SEALED,seal.get('status')),
        Check('parent_next_action_matches_r420',seal.get('next_action')=='BUILD_R420_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT_AND_TARGET_DESIGN_PROTOCOL_REPAIR',seal.get('next_action')),
        Check('parent_p2_backlog_six',ps.get('p2_backlog_cell_count')==6,ps.get('p2_backlog_cell_count')),
        Check('parent_target_active_backlog_57',ps.get('active_target_design_or_semantic_repair_count')==57,ps.get('active_target_design_or_semantic_repair_count')),
        Check('parent_proxy_context_two',ps.get('proxy_context_only_count')==2,ps.get('proxy_context_only_count')),
        Check('parent_p3_backlog_six',ps.get('p3_backlog_cell_count')==6,ps.get('p3_backlog_cell_count')),
        Check('parent_p2_plan_exact_six',p2.get('cell_count')==6 and len(p2.get('records') or [])==6,{'declared':p2.get('cell_count'),'loaded':len(p2.get('records') or [])}),
        Check('parent_target_plan_59',tp.get('total_p1_records')==59 and len(tp.get('records') or [])==59,{'declared':tp.get('total_p1_records'),'loaded':len(tp.get('records') or [])}),
        Check('parent_r420_plan_frozen',auth.get('status')=='R419_P2_AND_TARGET_DESIGN_EXECUTION_PLAN_FROZEN',auth.get('status')),
        Check('policy_frozen',cfg.get('policy_freeze')=='FROZEN_PRE_P2_STATIC_IMPLEMENTATION_VALIDATION_AND_TARGET_PROTOCOL_REPAIR',cfg.get('policy_freeze')),
        Check('engine_execution_forbidden',cfg.get('engine_execution_performed') is False),
        Check('canonical_state_unchanged',cfg.get('canonical_state_changed') is False),
        Check('canonical_replay_not_authorized',cfg.get('canonical_replay_authorized') is False),
        Check('canonical_parameter_change_not_authorized',cfg.get('canonical_parameter_change_authorized') is False),
        Check('deep_off',cfg.get('deep_biological_coupling') is False),
        Check('majority_vote_forbidden',cfg.get('majority_vote') is False),
    ]
    if any(not c.passed for c in checks):
        out={'stage':STAGE,'status':BLOCKED,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],'engine_execution_performed':False,'canonical_state_changed':False,'next_action':NEXT};write(root/OUT/'R4_20_INTEGRATED_AUDIT.json',out);return out
    p2pf=build_p2_preflight(root,p2)
    tr=build_target_repairs(tp)
    p2_unready=[r for r in p2pf['records'] if not r['implementation_layer_status'].startswith('IMPLEMENTATION_CONTRACT_READY')]
    family_set=set(p2pf.get('engine_families') or [])
    expected_families=set(ps.get('p2_engine_families') or [])
    checks += [
        Check('all_six_p2_implementation_contracts_built',p2pf.get('cell_count')==6,p2pf.get('cell_count')),
        Check('all_six_p2_preflight_ready',p2pf.get('ready_count')==6,{'ready':p2pf.get('ready_count'),'unready':p2_unready}),
        Check('p2_engine_family_set_preserved',family_set==expected_families,{'parent':sorted(expected_families),'r420':sorted(family_set)}),
        Check('all_p2_parent_adapter_sources_provenanced',all(bool(r.get('parent_adapter_source_candidates')) for r in p2pf['records'])),
        Check('all_p2_scopes_remain_symmetric',all(r.get('symmetric_reexecution_scope')=='ALL_FROZEN_R4_2_JOBS_FOR_SHARED_ENGINE_ADAPTER' for r in p2pf['records'])),
        Check('historical_adapter_overwrite_forbidden',all(r.get('historical_adapter_overwrite_authorized') is False for r in p2pf['records'])),
        Check('engine_execution_still_not_authorized',p2pf.get('engine_execution_authorized') is False),
        Check('all_59_target_protocol_records_repaired_or_preserved',tr.get('record_count')==59,tr.get('record_count')),
        Check('active_target_repair_count_57',tr.get('active_repair_count')==57,tr.get('active_repair_count')),
        Check('context_only_proxy_count_two',tr.get('context_only_proxy_count')==2,tr.get('context_only_proxy_count')),
        Check('no_numeric_target_invented_in_r420',all(r.get('numeric_target_materialized_in_r420') is False for r in tr['records'])),
        Check('no_target_adjudicative_promotion_in_r420',all(r.get('adjudicative_promotion_authorized_in_r420') is False for r in tr['records'])),
        Check('r418_rejection_repairs_do_not_change_numeric_value',all(r.get('numeric_value_change_authorized') is not True for r in tr['records'])),
        Check('p3_backlog_preserved_six',ps.get('p3_backlog_cell_count')==6,ps.get('p3_backlog_cell_count')),
        Check('no_engine_execution',cfg.get('engine_execution_performed') is False),
        Check('canonical_state_still_unchanged',cfg.get('canonical_state_changed') is False),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    r421={
        'stage':STAGE,'status':'R420_IMPLEMENTATION_PREFLIGHT_AND_TARGET_PROTOCOL_REPAIR_FROZEN' if status==COMPLETE else BLOCKED,
        'p2':{'cell_count':6,'engine_families':p2pf.get('engine_families'),'static_validation_required_next':True,'symmetric_engine_reexecution_authorized_now':False},
        'target_repair':{'active_count':tr.get('active_repair_count'),'proxy_context_only_count':tr.get('context_only_proxy_count'),'numeric_target_execution_authorized_now':False},
        'p3':{'cell_count':6,'execution_authorized_now':False},
        'r421_gate_requirements':['all R4.20 adapter enhancement contracts statically validated against parent adapter source','new-namespace implementation must preserve frozen seeds/job scope','target extractor/design repairs must be source-authority and result-independent','only then may symmetric external-engine reexecution be separately authorized'],
        'next_action':NEXT,
    }
    out={'stage':STAGE,'status':status,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],
         'p2_preflight_ready_cell_count':p2pf.get('ready_count'),'p2_engine_families':p2pf.get('engine_families'),'active_target_protocol_repair_count':tr.get('active_repair_count'),'proxy_context_only_count':tr.get('context_only_proxy_count'),'p3_backlog_cell_count':6,
         'engine_execution_performed':False,'canonical_state_changed':False,'next_action':NEXT}
    write(root/OUT/'R4_20_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT.json',p2pf)
    write(root/OUT/'R4_20_TARGET_DESIGN_PROTOCOL_REPAIR.json',tr)
    write(root/OUT/'R4_20_R421_STATIC_VALIDATION_AND_REEXECUTION_AUTHORIZATION_PLAN.json',r421)
    write(root/OUT/'R4_20_INTEGRATED_AUDIT.json',out)
    return out

def final_seal(root:Path)->dict[str,Any]:
    p=load(root/PSEAL) if (root/PSEAL).exists() else {}
    a=load(root/OUT/'R4_20_INTEGRATED_AUDIT.json') if (root/OUT/'R4_20_INTEGRATED_AUDIT.json').exists() else {}
    pf=load(root/OUT/'R4_20_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT.json') if (root/OUT/'R4_20_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT.json').exists() else {}
    tr=load(root/OUT/'R4_20_TARGET_DESIGN_PROTOCOL_REPAIR.json') if (root/OUT/'R4_20_TARGET_DESIGN_PROTOCOL_REPAIR.json').exists() else {}
    pl=load(root/OUT/'R4_20_R421_STATIC_VALIDATION_AND_REEXECUTION_AUTHORIZATION_PLAN.json') if (root/OUT/'R4_20_R421_STATIC_VALIDATION_AND_REEXECUTION_AUTHORIZATION_PLAN.json').exists() else {}
    checks=[
        Check('parent_r419_sealed',p.get('status')==PARENT_SEALED,p.get('status')),
        Check('r420_complete',a.get('status')==COMPLETE,a.get('status')),
        Check('r420_zero_process_failures',a.get('checks_failed')==0,a.get('checks_failed')),
        Check('p2_preflight_exact_six_ready',pf.get('cell_count')==6 and pf.get('ready_count')==6,{'cells':pf.get('cell_count'),'ready':pf.get('ready_count')}),
        Check('target_active_repairs_57',tr.get('active_repair_count')==57,tr.get('active_repair_count')),
        Check('proxy_context_only_two',tr.get('context_only_proxy_count')==2,tr.get('context_only_proxy_count')),
        Check('r421_plan_frozen',pl.get('status')=='R420_IMPLEMENTATION_PREFLIGHT_AND_TARGET_PROTOCOL_REPAIR_FROZEN',pl.get('status')),
        Check('symmetric_reexecution_not_yet_authorized',pl.get('p2',{}).get('symmetric_engine_reexecution_authorized_now') is False),
        Check('p3_backlog_six',a.get('p3_backlog_cell_count')==6,a.get('p3_backlog_cell_count')),
        Check('no_engine_execution',a.get('engine_execution_performed') is False),
        Check('canonical_state_unchanged',a.get('canonical_state_changed') is False),
        Check('next_action_present',a.get('next_action')==NEXT,a.get('next_action')),
    ]
    ok=all(c.passed for c in checks)
    out={'stage':STAGE,'audit':'FINAL_P2_ADAPTER_IMPLEMENTATION_PREFLIGHT_AND_TARGET_DESIGN_PROTOCOL_REPAIR','status':SEALED if ok else BLOCKED,'verdict':'SEALED' if ok else 'BLOCKED','checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],
         'summary':{'p2_preflight_ready_cell_count':pf.get('ready_count'),'p2_engine_families':pf.get('engine_families'),'active_target_protocol_repair_count':tr.get('active_repair_count'),'proxy_context_only_count':tr.get('context_only_proxy_count'),'p3_backlog_cell_count':a.get('p3_backlog_cell_count'),'engine_execution_performed':False,'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'deep_biological_coupling':False,'next_action':NEXT},'next_action':NEXT}
    write(root/SEAL,out);return out

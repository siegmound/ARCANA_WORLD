from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib, json

STAGE='v0.6D1-R4.32'
PARENT_SEALED='PASS_R431_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_SELECTOR_AND_TARGET_DESIGN_AUTHORITY_CLOSURE_AND_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL_SEALED'
PARENT_COMPLETE='PASS_R431_TARGET_MATERIALIZATION_SEMANTIC_VALIDATION_SELECTOR_AND_TARGET_DESIGN_AUTHORITY_CLOSURE_AND_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL_COMPLETE'
PARENT_NEXT='BUILD_R432_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_AND_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_STATIC_VALIDATION'
COMPLETE='PASS_R432_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_AND_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_STATIC_VALIDATION_COMPLETE'
SEALED='PASS_R432_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_AND_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_STATIC_VALIDATION_SEALED'
BLOCKED='BLOCKED_R432_PARENT_TARGET_AUTHORITY_BINDING_OR_GEONOMICS_STATIC_VALIDATION_FAILURE'
NEXT='BUILD_R433_TARGET_AUTHORITY_BINDING_STATIC_ADJUDICATION_AND_GEONOMICS_RUNTIME_PARAMETER_COMPILATION_PREFLIGHT'

CFG=Path('configs/world1_r432_target_authority_binding_geonomics_static_v0_6D1_R4_32.json')
PSEAL=Path('outputs/v0_6D1_R4_31_SEAL/R4_31_FINAL_SEAL_AUDIT.json')
PAUDIT=Path('outputs/v0_6D1_R4_31/R4_31_INTEGRATED_AUDIT.json')
PCLOSURE=Path('outputs/v0_6D1_R4_31/R4_31_TARGET_AUTHORITY_CLOSURE_REGISTRY.json')
PJ14SEAL=Path('outputs/v0_6D1_R4_31/authority/R4_31_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL.json')
R428SEL=Path('outputs/v0_6D1_R4_28/R4_28_TARGET_SELECTOR_AUTHORITY_IMPLEMENTATION_PREFLIGHT.json')
R428DES=Path('outputs/v0_6D1_R4_28/R4_28_TARGET_DESIGN_AUTHORITY_IMPLEMENTATION_REGISTRY.json')
R429SEL=Path('outputs/v0_6D1_R4_29/R4_29_EXPLICIT_TARGET_SELECTOR_AUTHORITY_FREEZE.json')
R429DES=Path('outputs/v0_6D1_R4_29/R4_29_TARGET_DESIGN_IMPLEMENTATION_VALIDATION.json')
R423GEO=Path('outputs/v0_6D1_R4_23/R4_23_GEONOMICS_CANONICAL_SPATIAL_BINDING_REGISTRY.json')
R430J14=Path('outputs/v0_6D1_R4_30/authority/R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz')
OUT=Path('outputs/v0_6D1_R4_32')
SEAL=Path('outputs/v0_6D1_R4_32_SEAL/R4_32_FINAL_SEAL_AUDIT.json')

J14='R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS'
J18='R42_J18_SAPIENT_200KA_TO_0_GEONOMICS'
J21='R42_J21_PRODUCER_20KA_TO_0_GEONOMICS'

@dataclass(frozen=True)
class Check:
    name:str; passed:bool; detail:Any=None
    def d(self): return {'name':self.name,'pass':bool(self.passed),'detail':self.detail}

def load(p:Path)->Any: return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p:Path,o:Any): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def key(r): return (str(r.get('window_id')),str(r.get('domain')))

def _packet_current(root:Path,pkt:dict[str,Any],selector:str|None=None)->dict[str,Any]:
    rel=str(pkt.get('source') or '')
    p=root/rel
    exists=p.exists()
    obs=sha256(p) if exists and p.is_file() else None
    exp=pkt.get('expected_sha256') or pkt.get('observed_sha256')
    hash_ok=bool(exists and exp and obs==exp)
    inv=list(pkt.get('exact_schema_inventory') or [])
    return {'source':rel,'expected_sha256':exp,'observed_sha256':obs,'hash_match':hash_ok,'exact_schema_inventory':inv,
            'contains_frozen_selector': bool(selector and selector in inv),'parser_family':pkt.get('parser_family'),'static_schema_valid':pkt.get('static_schema_valid') is True}

def build_target_binding(root:Path)->dict[str,Any]:
    closure=load(root/PCLOSURE)
    pre=load(root/R428SEL); freeze=load(root/R429SEL); desdef=load(root/R428DES); desval=load(root/R429DES)
    prem={key(r):r for r in pre.get('records') or []}; frm={key(r):r for r in freeze.get('records') or []}
    ddm={key(r):r for r in desdef.get('records') or []}; dvm={key(r):r for r in desval.get('records') or []}
    out=[]; blocked=0; source_frozen=0; source_unresolved=0; catalog=0; designs=0; primary=0
    for c in closure.get('records') or []:
        k=key(c); branch=c.get('source_branch'); status=c.get('closure_status'); rec={'window_id':k[0],'domain':k[1],'source_branch':branch,'parent_closure_status':status,
            'numeric_target_execution_authorized_in_r432':False,'external_engine_result_used_to_define_binding':False,'result_selected_binding_used':False}
        if branch=='R430_AUTHORIZED_SELECTOR_ATTEMPT':
            pr=prem.get(k,{}) ; fr=frm.get(k,{}) ; selector=fr.get('frozen_selector'); packets=[_packet_current(root,p,selector) for p in pr.get('source_packets') or []]
            exact=[p for p in packets if p['hash_match'] and p['contains_frozen_selector'] and p['static_schema_valid']]
            any_hash=any(p['hash_match'] for p in packets)
            if len(exact)==1:
                source_frozen+=1; disp='EXPLICIT_SOURCE_IDENTITY_AUTHORITY_FROZEN'; source=exact[0]; ready=True
            elif len(exact)>1:
                source_unresolved+=1; disp='SOURCE_IDENTITY_AMBIGUITY_AUTHORITY_IMPLEMENTED_PENDING_R433_ADJUDICATION'; source=None; ready=True
            elif any_hash:
                source_unresolved+=1; disp='SOURCE_IDENTITY_AUTHORITY_IMPLEMENTED_PENDING_R433_EXPLICIT_BINDING'; source=None; ready=True
            else:
                blocked+=1; disp='BLOCKED_SOURCE_IDENTITY_PARENT_SOURCE_INTEGRITY_FAILURE'; source=None; ready=False
            rec.update({'binding_kind':'AUTHORIZED_SELECTOR_SOURCE_IDENTITY','frozen_selector':selector,'frozen_transform_id':fr.get('frozen_transform_id'),
                        'source_packets':packets,'exact_hash_valid_selector_source_count':len(exact),'bound_source':source,'binding_disposition':disp,'implementation_ready':ready})
        elif branch=='R430_SELECTOR_GAP':
            catalog+=1; pr=prem.get(k,{}); fr=frm.get(k,{})
            rec.update({'binding_kind':'PRE_RESULT_SELECTOR_RULE_CATALOG_EXTENSION','exact_schema_inventory':list(fr.get('exact_schema_inventory') or pr.get('exact_schema_inventory') or []),
                        'domain_protocol':pr.get('domain_protocol'),'selector_chosen_in_r432':None,
                        'binding_disposition':'CATALOG_EXTENSION_AUTHORITY_IMPLEMENTED_NONNUMERIC_PENDING_R433_ADJUDICATION','implementation_ready':True})
        elif branch=='R429_VALIDATED_TARGET_DESIGN':
            designs+=1; dd=ddm.get(k,{}); dv=dvm.get(k,{})
            ready=bool(dd.get('authority_definition_implemented')) and dv.get('implementation_validation_pass') is True
            if not ready: blocked+=1
            rec.update({'binding_kind':'TARGET_DESIGN_OBSERVABLE_BINDING','authority_definition_id':dd.get('authority_definition_id'),
                        'scientific_construct':dd.get('scientific_construct'),'required_canonical_observables':dd.get('required_canonical_observables'),
                        'permitted_unit_families':dd.get('permitted_unit_families'),'required_governance':dd.get('required_governance'),
                        'forbidden_shortcuts':dd.get('forbidden_shortcuts'),'binding_disposition':'OBSERVABLE_BINDING_AUTHORITY_IMPLEMENTED_NONNUMERIC_PENDING_R433_EXACT_SOURCE_BINDING' if ready else 'BLOCKED_TARGET_DESIGN_AUTHORITY_DRIFT',
                        'implementation_ready':ready})
        elif branch=='R430_SEMANTIC_REPAIR':
            primary+=1
            rec.update({'binding_kind':'PRIMARY_MAPPING_AUTHORITY_DEFINITION','binding_disposition':'PRIMARY_MAPPING_AUTHORITY_DEFINITION_IMPLEMENTED_NONNUMERIC_PENDING_R433_ELIGIBILITY_ADJUDICATION','implementation_ready':True,
                        'mapping_class_change_authorized':False,'numeric_value_change_authorized':False})
        else:
            blocked+=1; rec.update({'binding_kind':'UNKNOWN','binding_disposition':'BLOCKED_UNKNOWN_R431_AUTHORITY_BRANCH','implementation_ready':False})
        out.append(rec)
    return {'stage':STAGE,'status':'R432_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_COMPLETE' if len(out)==57 and blocked==0 else BLOCKED,
            'record_count':len(out),'source_identity_authority_frozen_count':source_frozen,'source_identity_authority_pending_count':source_unresolved,
            'selector_catalog_extension_authority_implemented_count':catalog,'target_design_observable_binding_implemented_count':designs,
            'primary_mapping_authority_definition_implemented_count':primary,'blocked_count':blocked,'numeric_target_execution_authorized_count':0,'records':out}

def _geo_profiles(root:Path)->dict[str,Any]:
    geo=load(root/R423GEO); j14s=load(root/PJ14SEAL)
    by={r.get('job_id'):r for r in geo.get('records') or []}
    records=[]
    # J14 source from sealed derived authority
    p=root/R430J14; ok=p.exists() and j14s.get('verdict')=='SEALED' and sha256(p)==j14s.get('source_candidate_npz_sha256')
    records.append({'job_id':J14,'window_id':'SAPIENT_3MA_TO_200KA','source_authority_kind':'R431_SEALED_DERIVED_CANONICAL_SPATIAL_AUTHORITY',
        'sources':[{'path':R430J14.as_posix(),'sha256':sha256(p) if p.exists() else None,'hash_match_and_authority_sealed':ok}],
        'required_mappings':{'time_mapping':'age_ma exact R3.27 axis','space_mapping':'deme_state grid_row/grid_col on age-matched canonical support','population_mapping':'population per active deme preserving R3.27 effective_population','domain_mapping':'SAPIENT_3MA_TO_200KA spatial population support','uncertainty_mapping':'candidate/forcing-regime ensemble retained as explicit authority dimensions'},
        'static_parameter_manifest_valid':ok})
    # J18 R423 translation
    r=by.get(J18,{}) ; src=r.get('canonical_spatial_source') or {}; sp=root/str(src.get('path','')); ok=bool(sp.exists() and src.get('sha256') and sha256(sp)==src.get('sha256'))
    records.append({'job_id':J18,'window_id':'SAPIENT_200KA_TO_0','source_authority_kind':'R3_28_CANONICAL_HIGH_RESOLUTION_SPATIAL_REPLAY',
        'sources':[{'path':src.get('path'),'sha256':src.get('sha256'),'hash_match':ok}],
        'required_mappings':{'time_mapping':'snapshot_age_ka','space_mapping':'snapshot_deme_state:grid_row,grid_col + snapshot_active','population_mapping':'population_proxy','domain_mapping':'sapient spatial population support','uncertainty_mapping':'preserve replay/candidate dimensions; no target-derived tuning'},
        'static_parameter_manifest_valid':ok and r.get('binding_translation_materialized') is True})
    # J21 R423 translation
    r=by.get(J21,{}) ; ss=r.get('canonical_spatial_sources') or []; chk=[]
    for s in ss:
        sp=root/str(s.get('path','')); chk.append({'path':s.get('path'),'sha256':s.get('sha256'),'role':s.get('role'),'hash_match':bool(sp.exists() and s.get('sha256') and sha256(sp)==s.get('sha256'))})
    ok=bool(len(chk)==2 and all(x['hash_match'] for x in chk))
    records.append({'job_id':J21,'window_id':'PRODUCER_20KA_TO_0','source_authority_kind':'R3_33_R3_34_CANONICAL_HOLOCENE_RESOURCE_LANDSCAPE_BINDING',
        'sources':chk,'required_mappings':{'time_mapping':'anchor_age_ka exact shared anchors','space_mapping':'shared raster grid index; no cross-layer interpolation','population_mapping':'producer_landscape resource_abundance/suitability as producer support only, not agent count synthesis','domain_mapping':'producer resource landscape','uncertainty_mapping':'environment and producer layers remain provenance-separate; cross-layer numeric mixing forbidden without later explicit authority'},
        'static_parameter_manifest_valid':ok and r.get('binding_translation_materialized') is True})
    valid=sum(bool(r['static_parameter_manifest_valid']) for r in records)
    for r in records:
        d=root/OUT/'geonomics_profiles'/r['job_id']; d.mkdir(parents=True,exist_ok=True)
        manifest={'stage':STAGE,'engine':'Geonomics','job_id':r['job_id'],'window_id':r['window_id'],'profile_status':'CANONICAL_PARAMETER_MANIFEST_STATIC_VALIDATED_PENDING_RUNTIME_COMPILATION' if r['static_parameter_manifest_valid'] else 'BLOCKED_CANONICAL_PARAMETER_MANIFEST_STATIC_VALIDATION',
          'comparison_target_used':False,'default_model_used':False,'canonical_write':False,'source_authority_kind':r['source_authority_kind'],'canonical_spatial_sources':r['sources'],
          'mapping_fields':r['required_mappings'],'geonomics_parameters_file':None,'runtime_make_model_validation_performed':False,'geonomics_execution_ready':False,'external_engine_execution_authorized_in_r432':False}
        mf=d/'GEONOMICS_CANONICAL_PARAMETER_MANIFEST.json'; write(mf,manifest)
        profile={'stage':STAGE,'job_id':r['job_id'],'window_id':r['window_id'],'profile_status':manifest['profile_status'],'comparison_target_used':False,'default_model_used':False,
          'canonical_spatial_sources':r['sources'],'canonical_parameter_manifest_file':str(mf.relative_to(root)).replace('\\','/'),'canonical_parameter_manifest_sha256':sha256(mf),
          'geonomics_parameters_file':None,'runtime_parameter_compilation_pending':True,'geonomics_execution_ready':False}
        write(d/'LANDSCAPE_PROFILE.json',profile)
        r['canonical_parameter_manifest_file']=str(mf.relative_to(root)).replace('\\','/'); r['canonical_parameter_manifest_sha256']=sha256(mf)
    return {'stage':STAGE,'status':'R432_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_STATIC_VALIDATION_COMPLETE' if valid==3 else BLOCKED,
            'record_count':3,'static_valid_count':valid,'runtime_parameter_compiled_count':0,'geonomics_execution_ready_count':0,'external_engine_execution_authorized':False,'records':records}

def build(root:Path)->dict[str,Any]:
    cfg=load(root/CFG); ps=load(root/PSEAL); pa=load(root/PAUDIT); closure=load(root/PCLOSURE); j14=load(root/PJ14SEAL)
    tb=build_target_binding(root); write(root/OUT/'R4_32_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_REGISTRY.json',tb)
    gp=_geo_profiles(root); write(root/OUT/'R4_32_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_REGISTRY.json',gp)
    checks=[
      Check('parent_r431_sealed',ps.get('status')==PARENT_SEALED and ps.get('verdict')=='SEALED',ps.get('status')),
      Check('parent_r431_complete',pa.get('status')==PARENT_COMPLETE,pa.get('status')),
      Check('parent_next_action_matches_r432',pa.get('next_action')==PARENT_NEXT,pa.get('next_action')),
      Check('parent_target_authority_accounting_57',closure.get('active_target_repair_accounting_count')==57,closure.get('active_target_repair_accounting_count')),
      Check('parent_j14_spatial_authority_sealed',j14.get('verdict')=='SEALED' and j14.get('status')=='PASS_R431_J14_DERIVED_CANONICAL_SPATIAL_AUTHORITY_VALIDATION_SEALED',j14.get('status')),
      Check('parent_geonomics_static_materialization_authorized',pa.get('geonomics_parameter_materialization_static_validation_authorized_for_r432') is True),
      Check('policy_frozen',cfg.get('policy')=='FROZEN_POST_R431_PRE_TARGET_BINDING_EXECUTION_AND_PRE_GEONOMICS_RUNTIME_COMPILATION'),
      Check('target_binding_exact_57_records',tb.get('record_count')==57,tb.get('record_count')),
      Check('target_binding_zero_blocks',tb.get('blocked_count')==0,tb.get('blocked_count')),
      Check('target_binding_five_authorized_selector_branch_accounted',int(tb.get('source_identity_authority_frozen_count') or 0)+int(tb.get('source_identity_authority_pending_count') or 0)==5,{'frozen':tb.get('source_identity_authority_frozen_count'),'pending':tb.get('source_identity_authority_pending_count')}),
      Check('selector_catalog_extension_authorities_39',tb.get('selector_catalog_extension_authority_implemented_count')==39,tb.get('selector_catalog_extension_authority_implemented_count')),
      Check('target_design_observable_binding_12',tb.get('target_design_observable_binding_implemented_count')==12,tb.get('target_design_observable_binding_implemented_count')),
      Check('primary_mapping_authority_one',tb.get('primary_mapping_authority_definition_implemented_count')==1,tb.get('primary_mapping_authority_definition_implemented_count')),
      Check('target_numeric_execution_still_not_authorized',tb.get('numeric_target_execution_authorized_count')==0),
      Check('geonomics_exact_three_parameter_manifests',gp.get('record_count')==3,gp.get('record_count')),
      Check('geonomics_all_three_static_valid',gp.get('static_valid_count')==3,gp.get('static_valid_count')),
      Check('geonomics_runtime_parameter_compilation_not_performed',gp.get('runtime_parameter_compiled_count')==0),
      Check('geonomics_execution_not_ready_in_r432',gp.get('geonomics_execution_ready_count')==0 and gp.get('external_engine_execution_authorized') is False),
      Check('no_external_engine_execution',cfg.get('external_engine_execution_performed') is False and cfg.get('geonomics_execution_performed') is False),
      Check('no_target_numeric_execution',cfg.get('target_numeric_execution_performed') is False),
      Check('no_readjudication',cfg.get('readjudication_performed') is False),
      Check('canonical_state_unchanged',cfg.get('canonical_state_changed') is False),
      Check('deep_off',cfg.get('deep_biological_coupling') is False),
      Check('majority_vote_forbidden',cfg.get('majority_vote_forbidden') is True),
      Check('result_selected_selector_forbidden',cfg.get('result_selected_selector_forbidden') is True),
      Check('result_selected_transform_forbidden',cfg.get('result_selected_transform_forbidden') is True),
      Check('deferred_p2_two_preserved',pa.get('active_deferred_p2_cell_count')==2),
      Check('proxy_context_two_preserved',pa.get('proxy_context_only_count')==2),
      Check('p3_backlog_six_preserved',pa.get('p3_backlog_cell_count')==6),
    ]
    ok=all(c.passed for c in checks)
    plan={'stage':STAGE,'status':'R432_TARGET_BINDING_AND_GEONOMICS_STATIC_VALIDATION_EVIDENCE_FROZEN' if ok else BLOCKED,
      'target_authority_binding_record_count':tb.get('record_count'),'source_identity_authority_frozen_count':tb.get('source_identity_authority_frozen_count'),'source_identity_authority_pending_count':tb.get('source_identity_authority_pending_count'),
      'selector_catalog_extension_authority_implemented_count':tb.get('selector_catalog_extension_authority_implemented_count'),'target_design_observable_binding_implemented_count':tb.get('target_design_observable_binding_implemented_count'),'primary_mapping_authority_definition_implemented_count':tb.get('primary_mapping_authority_definition_implemented_count'),
      'geonomics_parameter_manifest_static_valid_count':gp.get('static_valid_count'),'geonomics_runtime_parameter_compilation_authorized_for_r433':ok,'geonomics_execution_authorized_in_r432':False,
      'target_numeric_execution_authorized_in_r432':False,'active_deferred_p2_cell_count':2,'proxy_context_only_count':2,'p3_backlog_cell_count':6,'next_action':NEXT if ok else 'REPAIR_R432_TARGET_BINDING_OR_GEONOMICS_STATIC_VALIDATION'}
    write(root/OUT/'R4_32_R433_EXECUTION_PLAN.json',plan)
    out={'stage':STAGE,'status':COMPLETE if ok else BLOCKED,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],
      'target_authority_binding_record_count':tb.get('record_count'),'source_identity_authority_frozen_count':tb.get('source_identity_authority_frozen_count'),'source_identity_authority_pending_count':tb.get('source_identity_authority_pending_count'),
      'selector_catalog_extension_authority_implemented_count':tb.get('selector_catalog_extension_authority_implemented_count'),'target_design_observable_binding_implemented_count':tb.get('target_design_observable_binding_implemented_count'),'primary_mapping_authority_definition_implemented_count':tb.get('primary_mapping_authority_definition_implemented_count'),
      'geonomics_parameter_manifest_static_valid_count':gp.get('static_valid_count'),'geonomics_runtime_parameter_compiled_count':0,'geonomics_execution_ready':False,
      'external_engine_execution_performed':False,'target_numeric_execution_performed':False,'readjudication_performed':False,'canonical_state_changed':False,
      'active_deferred_p2_cell_count':2,'proxy_context_only_count':2,'p3_backlog_cell_count':6,'next_action':plan['next_action']}
    write(root/OUT/'R4_32_INTEGRATED_AUDIT.json',out); return out

def final_seal(root:Path)->dict[str,Any]:
    ps=load(root/PSEAL) if (root/PSEAL).exists() else {}; a=load(root/OUT/'R4_32_INTEGRATED_AUDIT.json') if (root/OUT/'R4_32_INTEGRATED_AUDIT.json').exists() else {}; tb=load(root/OUT/'R4_32_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_REGISTRY.json') if (root/OUT/'R4_32_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_REGISTRY.json').exists() else {}; gp=load(root/OUT/'R4_32_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_REGISTRY.json') if (root/OUT/'R4_32_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_REGISTRY.json').exists() else {}; plan=load(root/OUT/'R4_32_R433_EXECUTION_PLAN.json') if (root/OUT/'R4_32_R433_EXECUTION_PLAN.json').exists() else {}
    checks=[Check('parent_r431_sealed',ps.get('status')==PARENT_SEALED and ps.get('verdict')=='SEALED'),Check('r432_complete',a.get('status')==COMPLETE,a.get('status')),Check('r432_zero_process_failures',a.get('checks_failed')==0,a.get('checks_failed')),
      Check('target_authority_binding_exact_57',tb.get('record_count')==57,tb.get('record_count')),Check('target_authority_binding_zero_blocks',tb.get('blocked_count')==0,tb.get('blocked_count')),Check('authorized_selector_source_identity_five_terminal',int(tb.get('source_identity_authority_frozen_count') or 0)+int(tb.get('source_identity_authority_pending_count') or 0)==5),
      Check('selector_catalog_39_implemented',tb.get('selector_catalog_extension_authority_implemented_count')==39),Check('target_design_12_observable_bindings_implemented',tb.get('target_design_observable_binding_implemented_count')==12),Check('primary_mapping_one_implemented',tb.get('primary_mapping_authority_definition_implemented_count')==1),
      Check('geonomics_three_static_parameter_manifests_valid',gp.get('record_count')==3 and gp.get('static_valid_count')==3,{'records':gp.get('record_count'),'valid':gp.get('static_valid_count')}),Check('geonomics_runtime_compilation_pending',gp.get('runtime_parameter_compiled_count')==0 and gp.get('geonomics_execution_ready_count')==0),
      Check('r433_plan_frozen',plan.get('status')=='R432_TARGET_BINDING_AND_GEONOMICS_STATIC_VALIDATION_EVIDENCE_FROZEN',plan.get('status')),Check('geonomics_execution_not_authorized',plan.get('geonomics_execution_authorized_in_r432') is False),Check('target_numeric_execution_not_authorized',plan.get('target_numeric_execution_authorized_in_r432') is False),
      Check('deferred_p2_two',plan.get('active_deferred_p2_cell_count')==2),Check('proxy_context_two',plan.get('proxy_context_only_count')==2),Check('p3_backlog_six',plan.get('p3_backlog_cell_count')==6),Check('no_external_engine_execution',a.get('external_engine_execution_performed') is False),Check('no_readjudication',a.get('readjudication_performed') is False),Check('canonical_state_unchanged',a.get('canonical_state_changed') is False),Check('next_action_present',a.get('next_action')==NEXT,a.get('next_action'))]
    verdict='SEALED' if all(c.passed for c in checks) else 'BLOCKED'
    out={'stage':STAGE,'audit':'FINAL_TARGET_AUTHORITY_BINDING_IMPLEMENTATION_AND_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_STATIC_VALIDATION','status':SEALED if verdict=='SEALED' else BLOCKED,'verdict':verdict,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.d() for c in checks],
      'summary':{'target_authority_binding_record_count':tb.get('record_count'),'source_identity_authority_frozen_count':tb.get('source_identity_authority_frozen_count'),'source_identity_authority_pending_count':tb.get('source_identity_authority_pending_count'),'selector_catalog_extension_authority_implemented_count':tb.get('selector_catalog_extension_authority_implemented_count'),'target_design_observable_binding_implemented_count':tb.get('target_design_observable_binding_implemented_count'),'primary_mapping_authority_definition_implemented_count':tb.get('primary_mapping_authority_definition_implemented_count'),'geonomics_parameter_manifest_static_valid_count':gp.get('static_valid_count'),'geonomics_runtime_parameter_compilation_authorized_for_r433':plan.get('geonomics_runtime_parameter_compilation_authorized_for_r433'),'geonomics_execution_authorized':False,'external_engine_execution_performed':False,'target_numeric_execution_performed':False,'readjudication_performed':False,'canonical_state_changed':False,'deep_biological_coupling':False,'active_deferred_p2_cell_count':2,'proxy_context_only_count':2,'p3_backlog_cell_count':6,'next_action':NEXT},'next_action':NEXT}
    write(root/SEAL,out); return out

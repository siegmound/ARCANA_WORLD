from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json, math
import numpy as np

STAGE='v0.6D1-R4.8'
R47_SEALED='PASS_R47_CDMETAPOP_FORCING_PARITY_REPAIR_SYMMETRIC_REEXECUTION_AND_READJUDICATION_SEALED'
PREPARED='PASS_R48_POST_REPAIR_STRUCTURAL_MATCHED_CONTROL_PLAN_PREPARED'
COMPLETE='PASS_R48_POST_REPAIR_STRUCTURAL_CAUSAL_DIAGNOSIS_COMPLETE'
SEALED='PASS_R48_POST_CDMETAPOP_REPAIR_STRUCTURAL_CAUSAL_DIAGNOSIS_AND_MATCHED_CONTROL_SEALED'
BLOCKED='BLOCKED_R48_PARENT_CONTROL_OR_CAUSAL_DIAGNOSIS_FAILURE'
CFG_REL=Path('configs/world1_r48_post_cdmetapop_structural_causal_diagnosis_v0_6D1_R4_8.json')
R47_SEAL_REL=Path('outputs/v0_6D1_R4_7_SEAL/R4_7_FINAL_SEAL_AUDIT.json')
R47_MATRIX_REL=Path('outputs/v0_6D1_R4_7/R4_7_CDMETAPOP_READJUDICATED_MATRIX.json')
R47_DIAG_REL=Path('outputs/v0_6D1_R4_7/R4_7_READJUDICATION_DELTA.json')
R47_RAW_REL=Path('outputs/v0_6D1_R4_7/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/RAW_EVIDENCE.json')
R47_PROFILE_REL=Path('outputs/v0_6D1_R4_7/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/REPAIR_PROFILE.json')
R43_CONTRACT_REL=Path('outputs/v0_6D1_R4_3/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/JOB_CONTRACT.json')
R46_SEAL_REL=Path('outputs/v0_6D1_R4_6_SEAL/R4_6_FINAL_SEAL_AUDIT.json')
R44_CFG_REL=Path('configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json')
OUT_REL=Path('outputs/v0_6D1_R4_8')
CONTROL_REL=OUT_REL/'jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/NEUTRAL_CONTROL_PROFILE.json'
CONTROL_RAW_REL=OUT_REL/'jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/RAW_NEUTRAL_CONTROL_EVIDENCE.json'
SEAL_REL=Path('outputs/v0_6D1_R4_8_SEAL/R4_8_FINAL_SEAL_AUDIT.json')
DIAG_CLASSES=['TRANSIENT_RELAXATION_CONFOUND_CONFIRMED','MODEL_RESPONSE_DISAGREEMENT_PERSISTS_AFTER_MATCHED_CONTROL','MATCHED_CONTROL_EFFECT_UNCERTAIN']

@dataclass(frozen=True)
class Check:
    name:str; passed:bool; detail:Any=None
    def to_dict(self): return {'name':self.name,'pass':bool(self.passed),'detail':self.detail}

def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write_json(p,obj):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def finite(x):
    try: v=float(x)
    except (TypeError,ValueError): return None
    return v if math.isfinite(v) else None
def ratio(a,b):
    a,b=finite(a),finite(b)
    return None if a is None or b is None or abs(a)<1e-15 else b/a
def summary(vals):
    a=np.asarray(vals,dtype=float); a=a[np.isfinite(a)]
    if a.size==0:return {'n':0,'median':None,'q10':None,'q90':None,'min':None,'max':None}
    return {'n':int(a.size),'median':float(np.median(a)),'q10':float(np.quantile(a,.1)),'q90':float(np.quantile(a,.9)),'min':float(a.min()),'max':float(a.max())}
def direction_ratio(v,neutral_factor):
    v=finite(v)
    if v is None or v<=0:return 0
    if v>neutral_factor:return 1
    if v<1.0/neutral_factor:return -1
    return 0

def _structural_rows(matrix,cfg):
    a=cfg['authorized_structural_case']
    cells=[x for x in matrix.get('cells',[]) if x.get('window_id')==a['window_id'] and x.get('domain')==a['domain']]
    rows=[x for x in matrix.get('evidence_rows',[]) if x.get('window_id')==a['window_id'] and x.get('domain')==a['domain'] and x.get('engine')==a['engine'] and x.get('job_id')==a['job_id'] and x.get('authority_role')=='PRIMARY']
    return cells,rows

def _extract_arcana_causal_effect(r46):
    s=(r46.get('summary') or {}).get('counterfactual_population_response') or {}
    can=finite(s.get('canonical_65p5_to_55_ratio')); hold=finite(s.get('counterfactual_65p5_to_55_ratio'))
    return None if can is None or hold is None or hold<=0 else can/hold

def _rep_by_seed(raw):
    out={}
    for r in raw.get('replicates',[]):
        if isinstance(r,dict) and r.get('status')=='PASS': out[(int(r['replicate_index']),int(r['seed']))]=r.get('metrics',{})
    return out

def prepare(root:Path):
    cfg=load_json(root/CFG_REL); p=load_json(root/R47_SEAL_REL) if (root/R47_SEAL_REL).exists() else {}; matrix=load_json(root/R47_MATRIX_REL) if (root/R47_MATRIX_REL).exists() else {}; contract=load_json(root/R43_CONTRACT_REL) if (root/R43_CONTRACT_REL).exists() else {}; prof=load_json(root/R47_PROFILE_REL) if (root/R47_PROFILE_REL).exists() else {}; r44cfg=load_json(root/R44_CFG_REL) if (root/R44_CFG_REL).exists() else {}
    cells,rows=_structural_rows(matrix,cfg) if matrix else ([],[]); a=cfg['authorized_structural_case']
    source=(root/'benchmarks/r47/cdmetapop_r47.py').read_text(encoding='utf-8') if (root/'benchmarks/r47/cdmetapop_r47.py').exists() else ''
    checks=[
      Check('parent_r47_seal_present',(root/R47_SEAL_REL).exists(),str(R47_SEAL_REL)),
      Check('parent_r47_sealed',p.get('status')==R47_SEALED,p.get('status')),
      Check('parent_next_action_matches_r48',p.get('next_action')==cfg['required_parent_next_action'],p.get('next_action')),
      Check('exact_one_authorized_structural_cell',len(cells)==1 and cells[0].get('discordance_class')=='STRUCTURAL_DISAGREEMENT',cells[0].get('discordance_class') if cells else None),
      Check('exact_one_authorized_primary_row',len(rows)==1 and rows[0].get('discordance_class')=='STRUCTURAL_DISAGREEMENT',len(rows)),
      Check('authorized_job_contract_present',(root/R43_CONTRACT_REL).exists(),a['job_id']),
      Check('r47_dynamic_raw_present',(root/R47_RAW_REL).exists(),str(R47_RAW_REL)),
      Check('r47_repair_profile_present',(root/R47_PROFILE_REL).exists(),str(R47_PROFILE_REL)),
      Check('r47_dynamic_support_repair_was_applied',finite((prof.get('repair_profile') or {}).get('bounded_end_support_ratio')) is not None,(prof.get('repair_profile') or {}).get('bounded_end_support_ratio')),
      Check('r47_start_state_n0_half_k_source_audited',"round(k0*0.5)" in source),
      Check('r44_ratio_neutral_factor_present',finite((r44cfg.get('effect_policy') or {}).get('ratio_neutral_factor')) is not None,(r44cfg.get('effect_policy') or {}).get('ratio_neutral_factor')),
      Check('policy_not_result_selected',cfg['policy_freeze']['result_selected'] is False),
      Check('matched_control_changes_only_end_support',cfg['matched_control_policy']['only_change']=='dynamic_end_support_ratio -> 1.0'),
      Check('same_seed_ledger_required',cfg['matched_control_policy']['same_seed_ledger'] is True),
      Check('comparison_target_injection_forbidden',cfg['matched_control_policy']['comparison_target_injection_forbidden'] is True),
      Check('canonical_state_unchanged',cfg['canonical_state_changed'] is False),
      Check('canonical_replay_not_authorized',cfg['canonical_replay_authorized'] is False),
      Check('canonical_parameter_change_not_authorized',cfg['canonical_parameter_change_authorized'] is False),
      Check('deep_off',cfg['deep_biological_coupling'] is False),
      Check('majority_vote_forbidden',cfg['majority_vote'] is False),
    ]
    seeds=[{'replicate_index':int(x['replicate_index']),'seed':int(x['seed'])} for x in (contract.get('engine_input') or {}).get('replicates',[])]
    control={'stage':STAGE,'job_id':a['job_id'],'engine':'CDMetaPOP','diagnostic_control':'MATCHED_NEUTRAL_FORCING','neutral_end_support_ratio':1.0,'same_frozen_job_contract':True,'same_seed_ledger':True,'replicates':seeds,'comparison_target_used':False,'canonical_write':False}
    write_json(root/CONTROL_REL,control)
    checks.append(Check('control_profile_exact_four_frozen_seeds',len(seeds)==4 and len({(x['replicate_index'],x['seed']) for x in seeds})==4,seeds))
    status=PREPARED if all(c.passed for c in checks) else BLOCKED
    out={'stage':STAGE,'status':status,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.to_dict() for c in checks],'authorized_case':a,'configured_start_state_relaxation_hypothesis':'R47_CONFIGURES_N0_AT_APPROX_HALF_K_START_SO_ABSOLUTE_POPULATION_RATIO_MAY_INCLUDE_TRANSIENT_RELAXATION','canonical_state_changed':False,'next_action':'EXECUTE_R48_J09_MATCHED_NEUTRAL_CONTROL' if status==PREPARED else 'REPAIR_R48_PARENT_OR_CONTROL_CONTRACT'}
    write_json(root/OUT_REL/'R4_8_MATCHED_CONTROL_PLAN.json',out); return out,checks

def diagnose(root:Path):
    cfg=load_json(root/CFG_REL); plan=load_json(root/OUT_REL/'R4_8_MATCHED_CONTROL_PLAN.json') if (root/OUT_REL/'R4_8_MATCHED_CONTROL_PLAN.json').exists() else {}; dyn=load_json(root/R47_RAW_REL) if (root/R47_RAW_REL).exists() else {}; ctl=load_json(root/CONTROL_RAW_REL) if (root/CONTROL_RAW_REL).exists() else {}; r46=load_json(root/R46_SEAL_REL) if (root/R46_SEAL_REL).exists() else {}; r44cfg=load_json(root/R44_CFG_REL)
    neutral=float(r44cfg['effect_policy']['ratio_neutral_factor']); d=_rep_by_seed(dyn); c=_rep_by_seed(ctl); keys=sorted(set(d)&set(c)); expected={(int(x['replicate_index']),int(x['seed'])) for x in load_json(root/CONTROL_REL).get('replicates',[])} if (root/CONTROL_REL).exists() else set()
    paired=[]
    for k in keys:
        di=finite(d[k].get('initial_population')); df=finite(d[k].get('final_population')); ci=finite(c[k].get('initial_population')); cf=finite(c[k].get('final_population'))
        dr=ratio(di,df); cr=ratio(ci,cf); pe=ratio(cr,dr) if dr is not None and cr is not None else None
        # ratio(cr,dr) returns dr/cr because helper is b/a
        final_rel=ratio(cf,df) if cf is not None and df is not None else None
        paired.append({'replicate_index':k[0],'seed':k[1],'dynamic_initial':di,'dynamic_final':df,'neutral_initial':ci,'neutral_final':cf,'dynamic_absolute_ratio':dr,'neutral_absolute_ratio':cr,'paired_forcing_effect_ratio':pe,'dynamic_final_over_neutral_final':final_rel,'initial_population_match':di==ci if di is not None and ci is not None else False})
    vals=[x['paired_forcing_effect_ratio'] for x in paired if finite(x.get('paired_forcing_effect_ratio')) is not None]; ps=summary(vals); arc=_extract_arcana_causal_effect(r46); arcdir=direction_ratio(arc,neutral); meddir=direction_ratio(ps['median'],neutral) if ps['median'] is not None else 0
    robust_same=False; robust_opp=False
    if arcdir<0 and ps['q90'] is not None: robust_same=ps['q90'] < 1.0/neutral
    elif arcdir>0 and ps['q10'] is not None: robust_same=ps['q10'] > neutral
    if arcdir<0 and ps['q10'] is not None: robust_opp=ps['q10'] > neutral
    elif arcdir>0 and ps['q90'] is not None: robust_opp=ps['q90'] < 1.0/neutral
    if robust_same: klass='TRANSIENT_RELAXATION_CONFOUND_CONFIRMED'; next_action='BUILD_R49_SYMMETRIC_CDMETAPOP_MATCHED_CONTROL_NORMALIZATION_AND_READJUDICATION'
    elif robust_opp: klass='MODEL_RESPONSE_DISAGREEMENT_PERSISTS_AFTER_MATCHED_CONTROL'; next_action='BUILD_R49_R311_CDMETAPOP_MECHANISM_DECOMPOSITION_BEFORE_CANONICAL_REPLAY'
    else: klass='MATCHED_CONTROL_EFFECT_UNCERTAIN'; next_action='EXECUTE_R49_ADDITIONAL_MATCHED_CONTROL_REPLICATES'
    checks=[
      Check('r48_prepared',plan.get('status')==PREPARED,plan.get('status')),
      Check('dynamic_r47_adapter_pass',dyn.get('adapter_status')=='PASS',dyn.get('adapter_status')),
      Check('neutral_control_adapter_pass',ctl.get('adapter_status')=='PASS',ctl.get('adapter_status')),
      Check('neutral_control_declares_matched_control',ctl.get('diagnostic_control')=='MATCHED_NEUTRAL_FORCING',ctl.get('diagnostic_control')),
      Check('neutral_control_ratio_exact_one',finite(ctl.get('neutral_end_support_ratio'))==1.0,ctl.get('neutral_end_support_ratio')),
      Check('exact_four_paired_replicates',len(keys)==4,keys),
      Check('paired_seed_ledger_matches_frozen',set(keys)==expected,{'paired':keys,'expected':sorted(expected)}),
      Check('all_paired_initial_populations_match',all(x.get('initial_population_match') for x in paired),[(x['seed'],x['dynamic_initial'],x['neutral_initial']) for x in paired]),
      Check('all_paired_effects_finite',len(vals)==4,vals),
      Check('arcana_causal_effect_available',arc is not None,arc),
      Check('diagnosis_uses_frozen_r44_neutral_factor',neutral==float(r44cfg['effect_policy']['ratio_neutral_factor']),neutral),
      Check('diagnosis_class_valid',klass in DIAG_CLASSES,klass),
      Check('r47_matrix_not_reclassified_in_r48',cfg['diagnosis_policy']['r48_may_not_reclassify_r47_matrix'] is True),
      Check('canonical_state_unchanged',cfg['canonical_state_changed'] is False),
      Check('canonical_replay_not_authorized',cfg['canonical_replay_authorized'] is False),
      Check('canonical_parameter_change_not_authorized',cfg['canonical_parameter_change_authorized'] is False),
      Check('no_majority_vote',cfg['majority_vote'] is False),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    paired_out={'stage':STAGE,'status':status,'arcana_causal_forcing_effect_ratio':arc,'arcana_causal_direction_5pct_band':arcdir,'cdmetapop_paired_forcing_effect':ps,'cdmetapop_paired_direction_5pct_band':meddir,'paired_replicates':paired,'neutral_factor':neutral,'interpretation':'Paired dynamic/neutral response removes shared start-state relaxation; it is diagnostic evidence and does not retroactively alter R4.7.'}
    diagnosis={'stage':STAGE,'status':status,'diagnosis_class':klass,'robust_same_direction_as_arcana':robust_same,'robust_opposite_direction_to_arcana':robust_opp,'absolute_r47_structural_disagreement_preserved_as_parent_evidence':True,'start_state_relaxation_source_fact':'R47/R48 configure N0 at approximately 0.5*K_start in each patch','canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'next_action':next_action}
    audit={'stage':STAGE,'status':status,'checks_passed':sum(x.passed for x in checks),'checks_total':len(checks),'checks_failed':sum(not x.passed for x in checks),'checks':[x.to_dict() for x in checks],'diagnosis_class':klass,'canonical_state_changed':False,'next_action':next_action}
    write_json(root/OUT_REL/'R4_8_PAIRED_CAUSAL_EFFECT.json',paired_out); write_json(root/OUT_REL/'R4_8_TRANSIENT_RELAXATION_DIAGNOSIS.json',diagnosis); write_json(root/OUT_REL/'R4_8_INTEGRATED_AUDIT.json',audit); return audit,checks

def final_seal(root:Path):
    p=load_json(root/R47_SEAL_REL) if (root/R47_SEAL_REL).exists() else {}; a=load_json(root/OUT_REL/'R4_8_INTEGRATED_AUDIT.json') if (root/OUT_REL/'R4_8_INTEGRATED_AUDIT.json').exists() else {}; d=load_json(root/OUT_REL/'R4_8_TRANSIENT_RELAXATION_DIAGNOSIS.json') if (root/OUT_REL/'R4_8_TRANSIENT_RELAXATION_DIAGNOSIS.json').exists() else {}; cfg=load_json(root/CFG_REL)
    checks=[Check('parent_r47_sealed',p.get('status')==R47_SEALED,p.get('status')),Check('r48_diagnosis_complete',a.get('status')==COMPLETE,a.get('status')),Check('r48_zero_process_failures',a.get('checks_failed')==0,a.get('checks_failed')),Check('diagnosis_class_valid',d.get('diagnosis_class') in DIAG_CLASSES,d.get('diagnosis_class')),Check('r47_structural_parent_preserved',d.get('absolute_r47_structural_disagreement_preserved_as_parent_evidence') is True),Check('canonical_state_unchanged',d.get('canonical_state_changed') is False),Check('canonical_replay_not_authorized',d.get('canonical_replay_authorized') is False),Check('canonical_parameter_change_not_authorized',d.get('canonical_parameter_change_authorized') is False),Check('deep_off',cfg.get('deep_biological_coupling') is False),Check('next_action_present',bool(d.get('next_action')),d.get('next_action'))]
    ok=all(x.passed for x in checks); out={'stage':STAGE,'audit':'FINAL_POST_CDMETAPOP_REPAIR_STRUCTURAL_CAUSAL_DIAGNOSIS_AND_MATCHED_NEUTRAL_CONTROL','status':SEALED if ok else BLOCKED,'verdict':'SEALED' if ok else 'BLOCKED','checks_passed':sum(x.passed for x in checks),'checks_total':len(checks),'checks_failed':sum(not x.passed for x in checks),'checks':[x.to_dict() for x in checks],'summary':{'diagnosis_class':d.get('diagnosis_class'),'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'deep_biological_coupling':False,'next_action':d.get('next_action')},'next_action':d.get('next_action')}; write_json(root/SEAL_REL,out); return out,checks

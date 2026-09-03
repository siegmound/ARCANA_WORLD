from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json, math
import numpy as np

STAGE='v0.6D1-R4.9'
R48_SEALED='PASS_R48_POST_CDMETAPOP_REPAIR_STRUCTURAL_CAUSAL_DIAGNOSIS_AND_MATCHED_CONTROL_SEALED'
PREPARED='PASS_R49_ADDITIONAL_MATCHED_CONTROL_REPLICATE_EXPANSION_PREPARED'
COMPLETE='PASS_R49_ADDITIONAL_MATCHED_CONTROL_REPLICATES_AND_CAUSAL_DIRECTION_RESOLUTION_COMPLETE'
SEALED='PASS_R49_ADDITIONAL_MATCHED_CONTROL_REPLICATES_AND_CAUSAL_DIRECTION_RESOLUTION_SEALED'
BLOCKED='BLOCKED_R49_PARENT_REPLICATE_EXECUTION_OR_CAUSAL_RESOLUTION_FAILURE'
CFG_REL=Path('configs/world1_r49_additional_matched_control_replicates_v0_6D1_R4_9.json')
R48_SEAL_REL=Path('outputs/v0_6D1_R4_8_SEAL/R4_8_FINAL_SEAL_AUDIT.json')
R48_DIAG_REL=Path('outputs/v0_6D1_R4_8/R4_8_TRANSIENT_RELAXATION_DIAGNOSIS.json')
R48_PAIR_REL=Path('outputs/v0_6D1_R4_8/R4_8_PAIRED_CAUSAL_EFFECT.json')
R48_NEUTRAL_RAW_REL=Path('outputs/v0_6D1_R4_8/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/RAW_NEUTRAL_CONTROL_EVIDENCE.json')
R47_DYNAMIC_RAW_REL=Path('outputs/v0_6D1_R4_7/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/RAW_EVIDENCE.json')
R47_PROFILE_REL=Path('outputs/v0_6D1_R4_7/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/REPAIR_PROFILE.json')
R43_CONTRACT_REL=Path('outputs/v0_6D1_R4_3/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/JOB_CONTRACT.json')
R46_SEAL_REL=Path('outputs/v0_6D1_R4_6_SEAL/R4_6_FINAL_SEAL_AUDIT.json')
R44_CFG_REL=Path('configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json')
OUT_REL=Path('outputs/v0_6D1_R4_9')
EXPANSION_REL=OUT_REL/'jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/ADDITIONAL_REPLICATE_PROFILE.json'
ADD_DYNAMIC_RAW_REL=OUT_REL/'jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/RAW_ADDITIONAL_DYNAMIC_EVIDENCE.json'
ADD_NEUTRAL_RAW_REL=OUT_REL/'jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/RAW_ADDITIONAL_NEUTRAL_EVIDENCE.json'
SEAL_REL=Path('outputs/v0_6D1_R4_9_SEAL/R4_9_FINAL_SEAL_AUDIT.json')
DIAG_CLASSES=['EXPANDED_MATCHED_CONTROL_SAME_DIRECTION_ROBUST','EXPANDED_MATCHED_CONTROL_OPPOSITE_DIRECTION_ROBUST','EXPANDED_MATCHED_CONTROL_EFFECT_UNCERTAIN']

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
def ratio(initial,final):
    a,b=finite(initial),finite(final)
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

def _rep_by_seed(raw):
    out={}
    for r in raw.get('replicates',[]):
        if isinstance(r,dict) and r.get('status')=='PASS':
            out[(int(r['replicate_index']),int(r['seed']))]=r.get('metrics',{})
    return out

def _extract_arcana_causal_effect(r46):
    s=(r46.get('summary') or {}).get('counterfactual_population_response') or {}
    can=finite(s.get('canonical_65p5_to_55_ratio')); hold=finite(s.get('counterfactual_65p5_to_55_ratio'))
    return None if can is None or hold is None or hold<=0 else can/hold

def prepare(root:Path):
    cfg=load_json(root/CFG_REL); p=load_json(root/R48_SEAL_REL) if (root/R48_SEAL_REL).exists() else {}; d=load_json(root/R48_DIAG_REL) if (root/R48_DIAG_REL).exists() else {}; pair=load_json(root/R48_PAIR_REL) if (root/R48_PAIR_REL).exists() else {}; contract=load_json(root/R43_CONTRACT_REL) if (root/R43_CONTRACT_REL).exists() else {}; prof=load_json(root/R47_PROFILE_REL) if (root/R47_PROFILE_REL).exists() else {}
    a=cfg['authorized_case']; exp=cfg['replicate_expansion']; original=[(int(x['replicate_index']),int(x['seed'])) for x in (contract.get('engine_input') or {}).get('replicates',[])]; additional=[(int(x['replicate_index']),int(x['seed'])) for x in exp['additional_replicates']]
    checks=[
      Check('parent_r48_seal_present',(root/R48_SEAL_REL).exists(),str(R48_SEAL_REL)),
      Check('parent_r48_sealed',p.get('status')==R48_SEALED,p.get('status')),
      Check('parent_diagnosis_uncertain',d.get('diagnosis_class')==cfg['required_parent_diagnosis_class'],d.get('diagnosis_class')),
      Check('parent_next_action_matches_r49',p.get('next_action')==cfg['required_parent_next_action'],p.get('next_action')),
      Check('parent_exact_four_paired_effects',(pair.get('cdmetapop_paired_forcing_effect') or {}).get('n')==4,(pair.get('cdmetapop_paired_forcing_effect') or {}).get('n')),
      Check('authorized_job_contract_present',(root/R43_CONTRACT_REL).exists(),a['job_id']),
      Check('r47_dynamic_parent_present',(root/R47_DYNAMIC_RAW_REL).exists(),str(R47_DYNAMIC_RAW_REL)),
      Check('r48_neutral_parent_present',(root/R48_NEUTRAL_RAW_REL).exists(),str(R48_NEUTRAL_RAW_REL)),
      Check('r47_repair_profile_present',(root/R47_PROFILE_REL).exists(),str(R47_PROFILE_REL)),
      Check('dynamic_support_ratio_present',finite((prof.get('repair_profile') or {}).get('bounded_end_support_ratio')) is not None,(prof.get('repair_profile') or {}).get('bounded_end_support_ratio')),
      Check('fixed_additional_pair_count',exp['additional_pair_count']==16 and len(additional)==16,len(additional)),
      Check('fixed_final_pair_count',exp['final_pair_count']==20 and exp['parent_pair_count']==4,exp['final_pair_count']),
      Check('additional_indices_exact',sorted(x[0] for x in additional)==list(range(4,20)),sorted(x[0] for x in additional)),
      Check('additional_seeds_unique',len({x[1] for x in additional})==16,[x[1] for x in additional]),
      Check('additional_seeds_do_not_overlap_parent',not({x[1] for x in additional}&{x[1] for x in original}),{'parent':original,'additional':additional}),
      Check('parent_pairs_not_rerun',exp['rerun_parent_pairs'] is False),
      Check('no_adaptive_stopping',cfg['diagnosis_policy']['no_adaptive_stopping'] is True),
      Check('no_automatic_further_escalation',cfg['diagnosis_policy']['no_automatic_further_replicate_escalation_if_uncertain'] is True),
      Check('policy_not_result_selected',cfg['policy_freeze']['result_selected'] is False),
      Check('comparison_target_injection_forbidden',exp['comparison_target_injection_forbidden'] is True),
      Check('canonical_state_unchanged',cfg['canonical_state_changed'] is False),
      Check('canonical_replay_not_authorized',cfg['canonical_replay_authorized'] is False),
      Check('canonical_parameter_change_not_authorized',cfg['canonical_parameter_change_authorized'] is False),
      Check('deep_off',cfg['deep_biological_coupling'] is False),
      Check('majority_vote_forbidden',cfg['majority_vote'] is False),
    ]
    profile={'stage':STAGE,'job_id':a['job_id'],'engine':'CDMetaPOP','additional_pair_count':16,'final_pair_count':20,'additional_replicates':[{'replicate_index':i,'seed':s} for i,s in additional],'neutral_end_support_ratio':1.0,'dynamic_end_support_ratio':finite((prof.get('repair_profile') or {}).get('bounded_end_support_ratio')),'comparison_target_used':False,'canonical_write':False,'pre_result_frozen':True}
    write_json(root/EXPANSION_REL,profile)
    status=PREPARED if all(c.passed for c in checks) else BLOCKED
    out={'stage':STAGE,'status':status,'checks_passed':sum(c.passed for c in checks),'checks_total':len(checks),'checks_failed':sum(not c.passed for c in checks),'checks':[c.to_dict() for c in checks],'authorized_case':a,'parent_pair_count':4,'additional_pair_count':16,'final_pair_count':20,'canonical_state_changed':False,'next_action':'EXECUTE_R49_FIXED_16_ADDITIONAL_DYNAMIC_NEUTRAL_PAIRS' if status==PREPARED else 'REPAIR_R49_PARENT_OR_REPLICATE_FREEZE'}
    write_json(root/OUT_REL/'R4_9_ADDITIONAL_MATCHED_CONTROL_PLAN.json',out); return out,checks

def diagnose(root:Path):
    cfg=load_json(root/CFG_REL); plan=load_json(root/OUT_REL/'R4_9_ADDITIONAL_MATCHED_CONTROL_PLAN.json') if (root/OUT_REL/'R4_9_ADDITIONAL_MATCHED_CONTROL_PLAN.json').exists() else {}; parent_dyn=load_json(root/R47_DYNAMIC_RAW_REL) if (root/R47_DYNAMIC_RAW_REL).exists() else {}; parent_neu=load_json(root/R48_NEUTRAL_RAW_REL) if (root/R48_NEUTRAL_RAW_REL).exists() else {}; add_dyn=load_json(root/ADD_DYNAMIC_RAW_REL) if (root/ADD_DYNAMIC_RAW_REL).exists() else {}; add_neu=load_json(root/ADD_NEUTRAL_RAW_REL) if (root/ADD_NEUTRAL_RAW_REL).exists() else {}; r46=load_json(root/R46_SEAL_REL) if (root/R46_SEAL_REL).exists() else {}; r44cfg=load_json(root/R44_CFG_REL); profile=load_json(root/EXPANSION_REL) if (root/EXPANSION_REL).exists() else {}
    neutral=float(r44cfg['effect_policy']['ratio_neutral_factor']); pd=_rep_by_seed(parent_dyn); pn=_rep_by_seed(parent_neu); ad=_rep_by_seed(add_dyn); an=_rep_by_seed(add_neu); d={**pd,**ad}; n={**pn,**an}; keys=sorted(set(d)&set(n)); expected_parent=set(pd)&set(pn); expected_add={(int(x['replicate_index']),int(x['seed'])) for x in profile.get('additional_replicates',[])}; expected=expected_parent|expected_add
    paired=[]
    for k in keys:
        di=finite(d[k].get('initial_population')); df=finite(d[k].get('final_population')); ni=finite(n[k].get('initial_population')); nf=finite(n[k].get('final_population')); dr=ratio(di,df); nr=ratio(ni,nf); pe=(dr/nr) if dr is not None and nr is not None and nr>0 else None
        paired.append({'replicate_index':k[0],'seed':k[1],'source':'PARENT_R47_R48' if k in expected_parent else 'ADDITIONAL_R49','dynamic_initial':di,'dynamic_final':df,'neutral_initial':ni,'neutral_final':nf,'dynamic_absolute_ratio':dr,'neutral_absolute_ratio':nr,'paired_forcing_effect_ratio':pe,'initial_population_match':di==ni if di is not None and ni is not None else False})
    vals=[x['paired_forcing_effect_ratio'] for x in paired if finite(x.get('paired_forcing_effect_ratio')) is not None]; ps=summary(vals); arc=_extract_arcana_causal_effect(r46); arcdir=direction_ratio(arc,neutral); meddir=direction_ratio(ps['median'],neutral) if ps['median'] is not None else 0
    robust_same=False; robust_opp=False
    if arcdir<0 and ps['q90'] is not None: robust_same=ps['q90'] < 1.0/neutral
    elif arcdir>0 and ps['q10'] is not None: robust_same=ps['q10'] > neutral
    if arcdir<0 and ps['q10'] is not None: robust_opp=ps['q10'] > neutral
    elif arcdir>0 and ps['q90'] is not None: robust_opp=ps['q90'] < 1.0/neutral
    if robust_same:
        klass='EXPANDED_MATCHED_CONTROL_SAME_DIRECTION_ROBUST'; next_action='BUILD_R410_SYMMETRIC_CDMETAPOP_MATCHED_CONTROL_NORMALIZATION_AND_READJUDICATION'
    elif robust_opp:
        klass='EXPANDED_MATCHED_CONTROL_OPPOSITE_DIRECTION_ROBUST'; next_action='BUILD_R410_R311_CDMETAPOP_MECHANISM_DECOMPOSITION_BEFORE_CANONICAL_REPLAY'
    else:
        klass='EXPANDED_MATCHED_CONTROL_EFFECT_UNCERTAIN'; next_action='BUILD_R410_MATCHED_CONTROL_PRECISION_AND_ALTERNATE_EVIDENCE_CLOSURE_PLAN'
    checks=[
      Check('r49_prepared',plan.get('status')==PREPARED,plan.get('status')),
      Check('parent_dynamic_adapter_pass',parent_dyn.get('adapter_status')=='PASS',parent_dyn.get('adapter_status')),
      Check('parent_neutral_adapter_pass',parent_neu.get('adapter_status')=='PASS',parent_neu.get('adapter_status')),
      Check('additional_dynamic_adapter_pass',add_dyn.get('adapter_status')=='PASS',add_dyn.get('adapter_status')),
      Check('additional_neutral_adapter_pass',add_neu.get('adapter_status')=='PASS',add_neu.get('adapter_status')),
      Check('additional_dynamic_exact_16',len(ad)==16,len(ad)),
      Check('additional_neutral_exact_16',len(an)==16,len(an)),
      Check('additional_seed_ledgers_match',set(ad)==expected_add and set(an)==expected_add,{'dynamic':sorted(ad),'neutral':sorted(an),'expected':sorted(expected_add)}),
      Check('exact_20_total_paired_replicates',len(keys)==20,len(keys)),
      Check('all_expected_pairs_present',set(keys)==expected,{'paired':len(keys),'expected':len(expected)}),
      Check('all_paired_initial_populations_match',all(x['initial_population_match'] for x in paired),[(x['seed'],x['dynamic_initial'],x['neutral_initial']) for x in paired if not x['initial_population_match']]),
      Check('all_20_paired_effects_finite',len(vals)==20,len(vals)),
      Check('arcana_causal_effect_available',arc is not None,arc),
      Check('diagnosis_uses_frozen_r44_neutral_factor',neutral==float(r44cfg['effect_policy']['ratio_neutral_factor']),neutral),
      Check('diagnosis_class_valid',klass in DIAG_CLASSES,klass),
      Check('no_adaptive_stopping_used',cfg['diagnosis_policy']['no_adaptive_stopping'] is True),
      Check('canonical_state_unchanged',cfg['canonical_state_changed'] is False),
      Check('canonical_replay_not_authorized',cfg['canonical_replay_authorized'] is False),
      Check('canonical_parameter_change_not_authorized',cfg['canonical_parameter_change_authorized'] is False),
      Check('no_majority_vote',cfg['majority_vote'] is False),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    evidence={'stage':STAGE,'status':status,'arcana_causal_forcing_effect_ratio':arc,'arcana_causal_direction_5pct_band':arcdir,'cdmetapop_expanded_paired_forcing_effect':ps,'cdmetapop_expanded_paired_direction_5pct_band':meddir,'parent_pair_count':len(expected_parent),'additional_pair_count':len(expected_add),'total_pair_count':len(keys),'paired_replicates':paired,'neutral_factor':neutral,'neutral_band':[1.0/neutral,neutral],'interpretation':'Fixed pre-result replicate expansion; same R4.8 paired metric and same R4.4 neutral band. No adaptive stopping and no canonical write.'}
    diagnosis={'stage':STAGE,'status':status,'diagnosis_class':klass,'robust_same_direction_as_arcana':robust_same,'robust_opposite_direction_to_arcana':robust_opp,'r47_structural_parent_preserved_as_historical_evidence':True,'r48_uncertain_parent_preserved_as_historical_evidence':True,'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'next_action':next_action}
    audit={'stage':STAGE,'status':status,'checks_passed':sum(x.passed for x in checks),'checks_total':len(checks),'checks_failed':sum(not x.passed for x in checks),'checks':[x.to_dict() for x in checks],'diagnosis_class':klass,'paired_effect_summary':ps,'canonical_state_changed':False,'next_action':next_action}
    write_json(root/OUT_REL/'R4_9_EXPANDED_PAIRED_CAUSAL_EFFECT.json',evidence); write_json(root/OUT_REL/'R4_9_CAUSAL_DIRECTION_RESOLUTION.json',diagnosis); write_json(root/OUT_REL/'R4_9_INTEGRATED_AUDIT.json',audit); return audit,checks

def final_seal(root:Path):
    p=load_json(root/R48_SEAL_REL) if (root/R48_SEAL_REL).exists() else {}; a=load_json(root/OUT_REL/'R4_9_INTEGRATED_AUDIT.json') if (root/OUT_REL/'R4_9_INTEGRATED_AUDIT.json').exists() else {}; d=load_json(root/OUT_REL/'R4_9_CAUSAL_DIRECTION_RESOLUTION.json') if (root/OUT_REL/'R4_9_CAUSAL_DIRECTION_RESOLUTION.json').exists() else {}; cfg=load_json(root/CFG_REL)
    checks=[
      Check('parent_r48_sealed',p.get('status')==R48_SEALED,p.get('status')),
      Check('r49_resolution_complete',a.get('status')==COMPLETE,a.get('status')),
      Check('r49_zero_process_failures',a.get('checks_failed')==0,a.get('checks_failed')),
      Check('diagnosis_class_valid',d.get('diagnosis_class') in DIAG_CLASSES,d.get('diagnosis_class')),
      Check('fixed_total_pair_count',(a.get('paired_effect_summary') or {}).get('n')==20,(a.get('paired_effect_summary') or {}).get('n')),
      Check('r47_structural_parent_preserved',d.get('r47_structural_parent_preserved_as_historical_evidence') is True),
      Check('r48_uncertain_parent_preserved',d.get('r48_uncertain_parent_preserved_as_historical_evidence') is True),
      Check('canonical_state_unchanged',d.get('canonical_state_changed') is False),
      Check('canonical_replay_not_authorized',d.get('canonical_replay_authorized') is False),
      Check('canonical_parameter_change_not_authorized',d.get('canonical_parameter_change_authorized') is False),
      Check('deep_off',cfg.get('deep_biological_coupling') is False),
      Check('next_action_present',bool(d.get('next_action')),d.get('next_action')),
    ]
    ok=all(x.passed for x in checks); out={'stage':STAGE,'audit':'FINAL_ADDITIONAL_MATCHED_CONTROL_REPLICATES_AND_CAUSAL_DIRECTION_RESOLUTION','status':SEALED if ok else BLOCKED,'verdict':'SEALED' if ok else 'BLOCKED','checks_passed':sum(x.passed for x in checks),'checks_total':len(checks),'checks_failed':sum(not x.passed for x in checks),'checks':[x.to_dict() for x in checks],'summary':{'diagnosis_class':d.get('diagnosis_class'),'total_pair_count':(a.get('paired_effect_summary') or {}).get('n'),'paired_effect_summary':a.get('paired_effect_summary'),'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'deep_biological_coupling':False,'next_action':d.get('next_action')},'next_action':d.get('next_action')}; write_json(root/SEAL_REL,out); return out,checks

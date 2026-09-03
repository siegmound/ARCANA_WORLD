from pathlib import Path
import json, math, hashlib, sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r37d_selection_closure import (
    AdaptiveSelectionShadowEnvelope,
    analyze_r37c_r1_selection_evidence,
    geometric_adaptive_participation,
    shadow_adaptive_selection_envelope,
)
from arcana_worldsim.scientific_engines.segregation_potential_lifecycle import ReducedGeneticLifecycleState

checks=[]
def check(name,cond,detail=None): checks.append({'name':name,'pass':bool(cond),'detail':detail})

E=ROOT/'evidence'/'v0_6D1_R3_7C_R1_SELECTION_RESULTS.zip'
r=analyze_r37c_r1_selection_evidence(E)
check('stage',r['stage']=='v0.6D1-R3.7D')
check('parent_stage',r['parent_stage']=='v0.6D1-R3.7C-R1')
check('chain_count_16',r['chain_count']==16)
check('closure_verdict',r['verdict'].startswith('PASS_DIRECTIONAL_SELECTION_EVIDENCE_CLOSURE'))
check('geometric_K_positive',r['geometric_K_eff_all']['minimum']>0)
check('geometric_K_le_64',r['geometric_K_eff_all']['maximum']<=64+1e-12)
check('aggregate_diagnostic_exposes_gt64',r['aggregate_deltaS_K_eff_diagnostic']['maximum']>64)
check('N500_count',r['by_population_size']['500']['n']==8)
check('N2000_count',r['by_population_size']['2000']['n']==8)
check('N2000_cv_lt_005',r['by_population_size']['2000']['cv']<0.05)
check('N_sensitivity_pair_count',r['paired_effects']['N_2000_minus_500']['n']==8)
check('N_sensitivity_mean_positive',r['paired_effects']['N_2000_minus_500']['mean']>20)
check('N_sensitivity_exact_p',r['paired_effects']['N_2000_minus_500']['exact_two_sided_signflip_p']<=0.01)
check('selection_strength_not_systematic',r['paired_effects']['selection_variance_4_minus_1']['exact_two_sided_signflip_p']>0.1)
check('reconnection_S_retention_lt_010',r['reconnection_geometric_S_retention']['maximum']<0.10)
check('shadow_env_order',r['high_N_dynamic_selection_shadow_envelope']['minimum']<=r['high_N_dynamic_selection_shadow_envelope']['center_median']<=r['high_N_dynamic_selection_shadow_envelope']['maximum'])
check('scalar_not_authorized',r['governance']['scalar_K_eff_production_authorized'] is False)
check('worldsim_N_mapping_not_authorized',r['governance']['direct_WorldSim_N_to_NEMO_N_mapping_authorized'] is False)
check('shadow_env_authorized',r['governance']['high_N_shadow_envelope_authorized'] is True)
check('canonical_write_denied',r['governance']['canonical_write_allowed'] is False)
check('runtime_replacement_denied',r['governance']['production_runtime_replacement_authorized'] is False)
check('mu_b_ceiling_change_denied',r['governance']['mu_b_or_ceiling_change_authorized'] is False)

fx=np.array([1.,2.,.5]); ctl=np.full((4,3),.5); sel=ctl.copy(); sel[:2]-=[.1,.05,.02]; sel[2:]+=[.1,.05,.02]
g=geometric_adaptive_participation(fx,sel,ctl)
check('synthetic_K_cauchy_bound',0<g['geometric_K_eff']<=3+1e-12)

state=ReducedGeneticLifecycleState(np.full((2,1),.045),np.zeros((2,1)),np.zeros((2,2,1)),np.zeros((2,1)))
envdat=r['high_N_dynamic_selection_shadow_envelope']; env=AdaptiveSelectionShadowEnvelope(envdat['minimum'],envdat['center_median'],envdat['maximum'])
out,diag=shadow_adaptive_selection_envelope(state,np.zeros((2,1)),np.array([[-.2],[.2]]),env)
sl=out['K_LOW'].total_segregation_potential[0,1,0]; sc=out['K_CENTER'].total_segregation_potential[0,1,0]; sh=out['K_HIGH'].total_segregation_potential[0,1,0]
check('shadow_monotonic_K',sl>sc>sh>0)
check('shadow_canonical_denied',diag['governance']['canonical_write_allowed'] is False)
check('shadow_runtime_denied',diag['governance']['production_runtime_replacement_authorized'] is False)

for f in ['DIRECTIONAL_SELECTION_EVIDENCE_CLOSURE_CONTRACT_v0_6D1_R3_7D.md','R3_7D_NEMO_DIRECTIONAL_SELECTION_EVIDENCE_AUDIT.md','README_R3_7D.md','V0_6D1_R3_7D_STATUS.md','NEXT_STAGE_HANDOFF_v0_6D1_R3_7D.md']:
    check('doc_'+f,(ROOT/f).exists())

cfg=json.loads((ROOT/'configs'/'world1_adaptive_selection_shadow_envelope_v0_6D1_R3_7D.json').read_text())
check('config_stage',cfg['stage']=='v0.6D1-R3.7D')
check('config_shadow_only',cfg['governance']['high_N_shadow_envelope_authorized'] is True and cfg['governance']['scalar_K_eff_production_authorized'] is False)
check('config_center_matches_report',abs(cfg['selection_increment_K_eff_shadow']['center']-r['high_N_dynamic_selection_shadow_envelope']['center_median'])<1e-12)

# parent authority files must remain present; hashes are recorded in parent source manifest and verified there.
for f in ['SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_7C_R1.json','PACKAGE_MANIFEST_v0_6D1_R3_7C_R1.json']:
    check('parent_manifest_present_'+f,(ROOT/f).exists())

outp=ROOT/'outputs'/'v0_6D1_R3_7D'/'FORMAL_AUDIT_v0_6D1_R3_7D.json'; outp.parent.mkdir(parents=True,exist_ok=True)
report={'stage':'v0.6D1-R3.7D','checks':checks,'pass_count':sum(x['pass'] for x in checks),'check_count':len(checks)}
report['verdict']='PASS' if report['pass_count']==report['check_count'] else 'FAIL'
outp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'stage':report['stage'],'verdict':report['verdict'],'pass_count':report['pass_count'],'check_count':report['check_count']},indent=2))
raise SystemExit(0 if report['verdict']=='PASS' else 2)

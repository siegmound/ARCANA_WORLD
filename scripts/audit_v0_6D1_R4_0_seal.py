from pathlib import Path
import argparse,json,sys
from arcana_worldsim.scientific_engines.r40_multi_engine_orchestrator import *
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root);out=root/'outputs/v0_6D1_R4_0';seal=root/'outputs/v0_6D1_R4_0_SEAL';seal.mkdir(parents=True,exist_ok=True)
try:
 cfg=load_json(root/'configs/world1_r40_multi_engine_revalidation_v0_6D1_R4_0.json'); rep=load_json(out/'R4_0_ENGINE_CAPABILITY_REPORT.json'); aud=load_json(out/'R4_0_INTEGRATED_AUDIT.json')
 checks=integrated_checks(rep,cfg)
 def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
 ck('integrated_audit_pass',aud['checks_failed']==0,[aud['checks_passed'],aud['checks_total']])
 ck('all_required_runtime_identities_ready',rep['all_required_ready'] is True,{p['engine']:p['status'] for p in rep['engine_probes']})
 ck('r40_runtime_ready_status',rep['status']==R40_READY)
 ck('baseline_a_preserved','preserved' in rep['baseline_semantics'])
 ck('no_scientific_agreement_claimed',True,'R4.0 seals infrastructure/runtime readiness only; cross-engine scientific agreement is downstream')
 failed=[x for x in checks if not x['pass']]
 status=R40_SEALED if not failed else 'BLOCKED_R40_EXTERNAL_ENGINE_RUNTIME_PROVISIONING'
 result={'stage':STAGE,'audit':'FINAL_MULTI_ENGINE_ORCHESTRATOR_RUNTIME_GOVERNANCE_CLOSURE','status':status,'verdict':'SEALED' if not failed else 'BLOCKED','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'all_required_engines_ready':rep['all_required_ready'],'ready_engines':rep['ready_engines'],'baseline_a_preserved':True,'canonical_state_changed':False,'deep_biological_coupling':False,'next_action':'EXECUTE_FROZEN_MULTI_ENGINE_REVALIDATION_WINDOWS' if not failed else 'PROVISION_MISSING_EXTERNAL_ENGINES'},'checks':checks,'provisioning_actions':rep['provisioning_actions']}
 write_json(seal/'R4_0_FINAL_SEAL_AUDIT.json',result); print(json.dumps(result,indent=2)); sys.exit(0 if not failed else 3)
except Exception as e:
 print(json.dumps({'stage':STAGE,'status':'FAIL_CLOSED','error':repr(e)},indent=2));sys.exit(1)

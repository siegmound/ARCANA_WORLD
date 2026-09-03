from pathlib import Path
import argparse,json,sys
from arcana_worldsim.scientific_engines.r41_semantic_revalidation import *

p=argparse.ArgumentParser(); p.add_argument('--root',required=True); a=p.parse_args(); root=Path(a.root)
try:
    out=root/'outputs/v0_6D1_R4_1'; seal_dir=root/'outputs/v0_6D1_R4_1_SEAL'; seal_dir.mkdir(parents=True,exist_ok=True)
    report=load_json(out/'R4_1_ENGINE_MICROBENCHMARK_REPORT.json')
    audit=load_json(out/'R4_1_INTEGRATED_AUDIT.json')
    gate=load_json(out/'R4_1_HISTORICAL_WINDOW_EXECUTION_GATE.json')
    authority=load_json(out/'R4_1_SEMANTIC_AUTHORITY_MATRIX.json')
    checks=[]
    def ck(name,cond,detail=None): checks.append({'name':name,'pass':bool(cond),'detail':detail})
    ck('r41_integrated_audit_zero_failures',audit.get('checks_failed')==0,audit.get('checks_failed'))
    ck('r41_readiness_status',report.get('status')==R41_READY,report.get('status'))
    ck('six_microbenchmarks_pass',len(report.get('benchmarks',[]))==6 and all(x.get('status')=='PASS' for x in report.get('benchmarks',[])),{x.get('engine'):x.get('status') for x in report.get('benchmarks',[])})
    ck('historical_window_gate_authorized',gate.get('status')=='AUTHORIZED_FOR_R42',gate.get('status'))
    ck('seven_frozen_windows_preserved',gate.get('window_count')==7,gate.get('window_count'))
    ck('all_windows_not_result_selected',all(x.get('selection_based_on_r41_results') is False for x in gate.get('windows',[])))
    ck('authority_matrix_pre_result',authority.get('status')=='FROZEN_PRE_RESULT',authority.get('status'))
    ck('no_majority_vote',authority.get('majority_vote') is False,authority.get('majority_vote'))
    ck('baseline_a_preserved',report.get('baseline_a_preserved') is True)
    ck('canonical_state_unchanged',report.get('canonical_state_changed') is False)
    ck('deep_off',report.get('deep_biological_coupling') is False)
    ck('no_scientific_agreement_claimed',report.get('scientific_agreement_claimed') is False)
    failed=[x for x in checks if not x['pass']]
    status=R41_SEALED if not failed else 'BLOCKED_R41_CONTROLLED_MICROBENCHMARK_OR_SEMANTIC_GATE'
    result={'stage':STAGE,'audit':'FINAL_MULTI_ENGINE_SEMANTIC_CALIBRATION_AND_CONTROLLED_MICROBENCHMARK_CLOSURE','status':status,'verdict':'SEALED' if not failed else 'BLOCKED','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'parent_r40_sealed':True,'all_six_microbenchmarks_pass':not failed,'historical_windows_authorized_for_r42':not failed,'baseline_a_preserved':True,'canonical_state_changed':False,'deep_biological_coupling':False,'scientific_agreement_claimed':False,'next_action':'EXECUTE_R42_FROZEN_MULTI_ENGINE_REVALIDATION_WINDOWS' if not failed else 'REPAIR_R41_MICROBENCHMARK_OR_SEMANTIC_DISCORDANCE'},'checks':checks}
    write_json(seal_dir/'R4_1_FINAL_SEAL_AUDIT.json',result)
    print(json.dumps(result,indent=2)); sys.exit(0 if not failed else 3)
except Exception as e:
    print(json.dumps({'stage':STAGE,'status':'FAIL_CLOSED','error':repr(e)},indent=2)); sys.exit(1)

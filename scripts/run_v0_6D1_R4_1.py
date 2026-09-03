from pathlib import Path
import argparse,json,sys
from arcana_worldsim.scientific_engines.r41_semantic_revalidation import *

p=argparse.ArgumentParser(); p.add_argument('--root',required=True); a=p.parse_args(); root=Path(a.root)
try:
    cfg=load_json(root/R41_CONFIG_REL)
    report, checks=build_report(root)
    failed=[x for x in checks if not x.passed]
    out=root/'outputs/v0_6D1_R4_1'; out.mkdir(parents=True,exist_ok=True)
    r40_cfg=load_json(root/R40_CONFIG_REL) if (root/R40_CONFIG_REL).exists() else {'frozen_revalidation_windows':[]}
    authority=build_authority_matrix(cfg)
    gate=build_historical_gate(cfg,r40_cfg,not failed)
    write_json(out/'R4_1_ENGINE_MICROBENCHMARK_REPORT.json',report)
    write_json(out/'R4_1_SEMANTIC_AUTHORITY_MATRIX.json',authority)
    write_json(out/'R4_1_HISTORICAL_WINDOW_EXECUTION_GATE.json',gate)
    audit={'stage':STAGE,'status':report['status'],'checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':[x.to_dict() for x in checks],'historical_window_gate':gate['status'],'canonical_state_changed':False,'scientific_agreement_claimed':False}
    write_json(out/'R4_1_INTEGRATED_AUDIT.json',audit)
    print(json.dumps({'stage':STAGE,'status':report['status'],'checks_passed':audit['checks_passed'],'checks_total':audit['checks_total'],'checks_failed':audit['checks_failed'],'benchmarks':[{'engine':x.get('engine'),'benchmark_id':x.get('benchmark_id'),'status':x.get('status'),'returncode':x.get('returncode'),'confirmed_version':x.get('confirmed_version'),'metrics':x.get('metrics'),'error':x.get('error') if x.get('status')!='PASS' else None,'stdout_tail':x.get('stdout_tail') if x.get('status')!='PASS' else None,'stderr_tail':x.get('stderr_tail') if x.get('status')!='PASS' else None,'result_stdout_tail':x.get('result_stdout_tail') if x.get('status')!='PASS' else None,'result_stderr_tail':x.get('result_stderr_tail') if x.get('status')!='PASS' else None,'engine_log_tail':x.get('engine_log_tail') if x.get('status')!='PASS' else None} for x in report.get('benchmarks',[])],'historical_window_gate':gate['status'],'next_stage':gate['next_stage'],'output_dir':str(out)},indent=2))
    sys.exit(0 if not failed else 3)
except Exception as e:
    print(json.dumps({'stage':STAGE,'status':'FAIL_CLOSED','error':repr(e)},indent=2)); sys.exit(1)

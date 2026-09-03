from pathlib import Path
import argparse,json,sys
from arcana_worldsim.scientific_engines.r40_multi_engine_orchestrator import *
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root)
try:
 cfg=load_json(root/'configs/world1_r40_multi_engine_revalidation_v0_6D1_R4_0.json')
 report=run_inventory(root,cfg); checks=integrated_checks(report,cfg); failed=[x for x in checks if not x['pass']]
 out=root/'outputs/v0_6D1_R4_0';out.mkdir(parents=True,exist_ok=True)
 write_json(out/'R4_0_ENGINE_CAPABILITY_REPORT.json',report)
 write_json(out/'R4_0_REVALIDATION_MATRIX.json',report['revalidation_matrix'])
 audit={'stage':STAGE,'status':report['status'],'checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':checks,'all_required_engines_ready':report['all_required_ready'],'provisioning_actions':report['provisioning_actions']}
 write_json(out/'R4_0_INTEGRATED_AUDIT.json',audit)
 print(json.dumps({'stage':STAGE,'status':report['status'],'checks_passed':audit['checks_passed'],'checks_total':audit['checks_total'],'all_required_engines_ready':report['all_required_ready'],'ready_engines':report['ready_engines'],'engine_probes':[{'engine':x['engine'],'status':x['status'],'confirmed_version':x['confirmed_version'],'invocation':x['invocation'],'returncode':x['returncode']} for x in report['engine_probes']],'provisioning_actions':report['provisioning_actions'],'output_dir':str(out)},indent=2))
 sys.exit(1 if failed else 0)
except Exception as e:
 print(json.dumps({'stage':STAGE,'status':'FAIL_CLOSED','error':repr(e)},indent=2));sys.exit(1)

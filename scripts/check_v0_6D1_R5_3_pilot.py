from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r53_demography import load_json, summarize_cdmetapop_summary, EXPECTED_CDMETAPOP_COMMIT, EXPECTED_CDMETAPOP_VERSION, SEEDS

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); a=ap.parse_args(); root=a.root.resolve(); out=root/'outputs/v0_6D1_R5_3'
    plan=load_json(out/'R5_3_CDMETAPOP_EXECUTION_PLAN.json'); g=plan['groups'][0]; seed=SEEDS[0]; ev=root/g['evidence_dir']/f'seed_{seed}'
    checks={}
    meta=load_json(ev/'STREAM_RUNTIME.json') if (ev/'STREAM_RUNTIME.json').is_file() else {}
    checks['pilot_stream_status_pass']=meta.get('status')=='PASS_R53_CDMETAPOP_STREAM'
    checks['pilot_seed_exact']=meta.get('seed')==seed
    checks['pilot_version_exact']=meta.get('cdmetapop_version')==EXPECTED_CDMETAPOP_VERSION
    checks['pilot_commit_exact']=meta.get('cdmetapop_commit')==EXPECTED_CDMETAPOP_COMMIT
    try:
        sm=summarize_cdmetapop_summary(ev/'summary_popAllTime.csv'); checks['pilot_authorized_summary_parse']=sm.get('authorized_fields_present') is True
    except Exception: checks['pilot_authorized_summary_parse']=False
    failed=[k for k,v in checks.items() if not v]
    r={'stage':'v0.6D1-R5.3','status':'PASS_R53_CDMETAPOP_PILOT_PREFLIGHT' if not failed else 'BLOCKED_R53_CDMETAPOP_PILOT_PREFLIGHT','checks_passed':sum(checks.values()),'checks_total':len(checks),'failed':failed,'checks':checks}
    print(json.dumps(r,indent=2)); raise SystemExit(0 if not failed else 3)
if __name__=='__main__': main()

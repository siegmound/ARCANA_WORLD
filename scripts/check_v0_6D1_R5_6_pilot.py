from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r56_slim_ancestry import OUT_REL, load_json, SEEDS, VARIANTS

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); a=ap.parse_args(); root=a.root.resolve(); out=root/OUT_REL
    plan=load_json(out/'R5_6_SLIM_EXECUTION_PLAN.json')
    sid=sorted(str(s['schedule_id']) for s in plan['schedules'])[0]
    rows=[s for s in plan['streams'] if str(s['schedule_id'])==sid and int(s['seed'])==SEEDS[0]]
    checks={'pilot_stream_count_exact':len(rows)==len(VARIANTS),'pilot_variant_set_exact':{str(s['variant']) for s in rows}==set(VARIANTS)}
    results={}
    for s in rows:
        wd=root/Path(str(s['work_dir'])); rp=wd/'ANCESTRY_RESULT.json'; runp=wd/'STREAM_RUNTIME.json'
        ok=rp.is_file() and runp.is_file()
        if ok:
            r=load_json(rp); rr=load_json(runp); ok=(r.get('status')=='PASS_R56_ANCESTRY_RESULT' and rr.get('status')=='PASS_R56_SLIM_STREAM')
            results[str(s['variant'])]=r
        checks[f"pilot_{s['variant'].lower()}_pass"]=ok
    c=results.get('NO_FLOW')
    checks['pilot_no_flow_cross_ancestry_zero']=bool(c and abs(float(c['p1_from_p2']['donor_ancestry_fraction_mean']))<=1e-12 and abs(float(c['p2_from_p1']['donor_ancestry_fraction_mean']))<=1e-12)
    failed=[k for k,v in checks.items() if not bool(v)]
    outdoc={'stage':'v0.6D1-R5.6','status':'PASS_R56_SLIM_PILOT_PREFLIGHT' if not failed else 'BLOCKED_R56_SLIM_PILOT','checks_passed':sum(bool(v) for v in checks.values()),'checks_total':len(checks),'failed':failed,'checks':checks,'schedule_id':sid}
    print(json.dumps(outdoc,indent=2,sort_keys=True)); return 0 if not failed else 2
if __name__=='__main__': raise SystemExit(main())

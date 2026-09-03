from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.state_query.r54_nemo_genetics import load_json, parse_qfreq, OUT_REL, EXPECTED_NEMO_VERSION, SEEDS, VARIANTS

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT); a=ap.parse_args(); root=a.root.resolve(); out=root/OUT_REL
    plan=load_json(out/'R5_4_NEMO_EXECUTION_PLAN.json'); streams=plan.get('streams') or []
    pilot=[s for s in streams if int(s['group_numeric_id'])==1 and int(s['seed'])==SEEDS[0] and s['variant'] in VARIANTS]
    checks={'pilot_stream_count_exact':len(pilot)==2}
    for variant in VARIANTS:
        ss=[s for s in pilot if s['variant']==variant]
        ok=len(ss)==1
        if ok:
            wd=root/ss[0]['work_dir']; meta=wd/'STREAM_RUNTIME.json'; q=list(wd.glob('*.qfreq')); rc=wd/'engine.returncode.txt'
            ok=meta.is_file() and rc.is_file() and rc.read_text().strip()=='0' and len(q)==1
            if ok:
                md=load_json(meta); ok=md.get('status')=='PASS_R54_NEMO_STREAM' and md.get('nemo_version')==EXPECTED_NEMO_VERSION and int(md.get('seed',-1))==SEEDS[0]
            if ok:
                try: parse_qfreq(q[0])
                except Exception: ok=False
        checks[f'pilot_{variant.lower()}_pass']=ok
    failed=[k for k,v in checks.items() if not v]
    r={'stage':'v0.6D1-R5.4','status':'PASS_R54_NEMO_PILOT_PREFLIGHT' if not failed else 'BLOCKED_R54_NEMO_PILOT','checks_passed':sum(bool(v) for v in checks.values()),'checks_total':len(checks),'failed':failed,'checks':checks}
    print(json.dumps(r,indent=2,sort_keys=True)); return 0 if not failed else 2
if __name__=='__main__': raise SystemExit(main())

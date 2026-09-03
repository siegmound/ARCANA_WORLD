from __future__ import annotations
import argparse, json
from pathlib import Path
from arcana_worldsim.state_query.r56_slim_ancestry import OUT_REL, load_json, write_json

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path('.')); a=ap.parse_args(); root=a.root.resolve(); out=root/OUT_REL
    plan=load_json(out/'R5_6_SLIM_EXECUTION_PLAN.json'); streams=plan.get('streams') or []
    rows=[]
    for s in streams:
        wd=root/Path(str(s['work_dir'])); rp=wd/'STREAM_RUNTIME.json'
        if not rp.is_file():
            rows.append({'stream_numeric_id':s['stream_numeric_id'],'status':'MISSING','returncode':None}); continue
        r=load_json(rp); rows.append({'stream_numeric_id':s['stream_numeric_id'],'schedule_id':s['schedule_id'],'variant':s['variant'],'seed':s['seed'],'status':r.get('status'),'returncode':r.get('returncode'),'collector_returncode':r.get('collector_returncode')})
    exit_zero=sum(r.get('status')=='PASS_R56_SLIM_STREAM' and int(r.get('returncode',-1))==0 and int(r.get('collector_returncode',-1))==0 for r in rows)
    bridge={'stage':'v0.6D1-R5.6','status':'R56_POWERSHELL_WSL_SLIM_EXECUTION_BRIDGE','stream_count':len(rows),'exit_zero_count':exit_zero,'streams':rows}
    write_json(out/'R5_6_EXECUTION_BRIDGE.json',bridge)
    print(json.dumps({k:bridge[k] for k in ('stage','status','stream_count','exit_zero_count')},indent=2,sort_keys=True))
    return 0 if len(rows)==int(plan['planned_stream_count']) and exit_zero==len(rows) else 2
if __name__=='__main__': raise SystemExit(main())

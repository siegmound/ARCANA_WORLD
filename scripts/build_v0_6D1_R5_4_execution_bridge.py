from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.state_query.r54_nemo_genetics import load_json, write_json, OUT_REL

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT); a=ap.parse_args(); root=a.root.resolve(); out=root/OUT_REL
    plan=load_json(out/'R5_4_NEMO_EXECUTION_PLAN.json'); recs=[]
    for s in plan.get('streams') or []:
        wd=root/s['work_dir']; rcfile=wd/'engine.returncode.txt'; meta=wd/'STREAM_RUNTIME.json'
        rc=int(rcfile.read_text().strip()) if rcfile.is_file() else -999
        md=load_json(meta) if meta.is_file() else {}
        recs.append({'group_id':s['group_id'],'candidate_id':s['candidate_id'],'family_id':s['family_id'],'demographic_stress_profile':s['demographic_stress_profile'],'variant':s['variant'],'seed':int(s['seed']),'exit_code':rc,'stream_status':md.get('status'),'qfreq_file_count':int(md.get('qfreq_file_count',0))})
    bridge={'stage':'v0.6D1-R5.4','status':'R54_POWERSHELL_WSL_NEMO_EXECUTION_BRIDGE','stream_count':len(recs),'records':recs}
    write_json(out/'R5_4_NEMO_EXECUTION_BRIDGE.json',bridge); print(json.dumps({'stage':bridge['stage'],'status':bridge['status'],'stream_count':len(recs),'exit_zero_count':sum(r['exit_code']==0 for r in recs)},indent=2)); return 0 if recs and all(r['exit_code']==0 and r['stream_status']=='PASS_R54_NEMO_STREAM' and r['qfreq_file_count']==1 for r in recs) else 2
if __name__=='__main__': raise SystemExit(main())

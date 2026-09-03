from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from pathlib import Path

EXPECTED_COMMIT='3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118'
EXPECTED_VERSION='3.08'

def run(cmd, **kw):
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--conda-exe',required=True)
    ap.add_argument('--engine-root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--preferred-env',default='')
    a=ap.parse_args()
    engine=a.engine_root.resolve(); src=engine/'src/CDmetaPOP.py'
    if not src.is_file(): raise SystemExit(f'CDMetaPOP source missing: {src}')
    text=src.read_text(encoding='utf-8',errors='replace')
    m=re.search(r'appVers\s*=\s*[\'\"]version\s+([^\'\"]+)',text)
    version=m.group(1).strip() if m else None
    git=run(['git','-c',f'safe.directory={engine}','-C',str(engine),'rev-parse','HEAD'])
    commit=git.stdout.strip() if git.returncode==0 else None
    if version!=EXPECTED_VERSION: raise SystemExit(f'CDMetaPOP version marker mismatch: {version}')
    if commit!=EXPECTED_COMMIT: raise SystemExit(f'CDMetaPOP git pin mismatch: {commit}')

    envj=run([a.conda_exe,'env','list','--json'])
    if envj.returncode!=0: raise SystemExit('conda env list failed: '+envj.stderr[-2000:])
    envs=list(json.loads(envj.stdout).get('envs') or [])
    preferred=a.preferred_env.strip()
    candidates=[]
    for prefix in envs:
        name=Path(prefix).name
        if preferred and name!=preferred and prefix!=preferred:
            continue
        code='import sys, numpy, scipy; print(sys.version.split()[0]); print(numpy.__version__); print(scipy.__version__)'
        p=run([a.conda_exe,'run','-p',prefix,'python','-c',code])
        if p.returncode!=0: continue
        lines=[x.strip() for x in p.stdout.splitlines() if x.strip()]
        pyver=lines[-3] if len(lines)>=3 else ''
        score=0
        low=name.lower()
        if 'cdmetapop' in low: score+=100
        if 'arcana' in low: score+=30
        if pyver.startswith('3.8'): score+=40
        if pyver.startswith(('3.9','3.10','3.11')): score+=10
        candidates.append({'prefix':prefix,'name':name,'python_version':pyver,'score':score,'probe_stdout':p.stdout[-1000:]})
    if not candidates:
        raise SystemExit('No conda environment with Python+NumPy+SciPy available for CDMetaPOP. Set ARCANA_CDMETAPOP_CONDA_ENV to the governed environment name.')
    candidates.sort(key=lambda x:(-x['score'],x['prefix']))
    if not preferred and len(candidates)>1 and candidates[0]['score']==candidates[1]['score']:
        top=[x for x in candidates if x['score']==candidates[0]['score']]
        raise SystemExit('Ambiguous CDMetaPOP runtime candidates: '+', '.join(x['name'] for x in top)+'. Set ARCANA_CDMETAPOP_CONDA_ENV explicitly.')
    chosen=candidates[0]
    out={
      'stage':'v0.6D1-R5.3','status':'PASS_R53_CDMETAPOP_3_08_PINNED_RUNTIME_IDENTITY',
      'cdmetapop_version':version,'cdmetapop_commit':commit,
      'engine_root':str(engine),'conda_executable':a.conda_exe,
      'conda_env_prefix':chosen['prefix'],'conda_env_name':chosen['name'],
      'python_version':chosen['python_version'],'candidate_count':len(candidates),
      'selection_semantics':'PREFER_EXPLICIT_ENV_THEN_CDMETAPOP_NAMED_THEN_ARCANA_NAMED_THEN_PYTHON38_FAIL_ON_TOP_SCORE_TIE',
    }
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(out,separators=(',',':')))
if __name__=='__main__': main()

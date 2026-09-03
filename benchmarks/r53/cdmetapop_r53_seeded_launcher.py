from __future__ import annotations
import argparse, csv, json, os, random, re, runpy, shutil, sys, time
from pathlib import Path
import numpy as np

EXPECTED_COMMIT='3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118'
EXPECTED_VERSION='3.08'

def git_commit(engine_root:Path)->str:
    import subprocess
    p=subprocess.run(['git','-c',f'safe.directory={engine_root}','-C',str(engine_root),'rev-parse','HEAD'],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return p.stdout.strip() if p.returncode==0 else ''

def version(engine_src:Path)->str:
    t=(engine_src/'CDmetaPOP.py').read_text(encoding='utf-8',errors='replace')
    m=re.search(r'appVers\s*=\s*[\'\"]version\s+([^\'\"]+)',t)
    return m.group(1).strip() if m else ''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--engine-root',type=Path,required=True)
    ap.add_argument('--data-dir',type=Path,required=True)
    ap.add_argument('--runvars',default='RunVars_R53.csv')
    ap.add_argument('--output-prefix',required=True)
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--evidence-dir',type=Path,required=True)
    a=ap.parse_args()
    engine=a.engine_root.resolve(); esrc=engine/'src'; data=a.data_dir.resolve(); ev=a.evidence_dir.resolve()
    commit=git_commit(engine); ver=version(esrc)
    if commit!=EXPECTED_COMMIT or ver!=EXPECTED_VERSION:
        raise SystemExit(f'CDMetaPOP runtime identity mismatch version={ver} commit={commit}')
    ev.mkdir(parents=True,exist_ok=True)
    random.seed(a.seed); np.random.seed(a.seed)
    before={p.resolve() for p in data.iterdir() if p.is_dir() and p.name.startswith(a.output_prefix)}
    start=time.time(); old=os.getcwd()
    try:
        os.chdir(esrc)
        sys.argv=[str(esrc/'CDmetaPOP.py'),str(data),a.runvars,a.output_prefix]
        runpy.run_path(str(esrc/'CDmetaPOP.py'),run_name='__main__')
    finally:
        os.chdir(old)
    after=[p.resolve() for p in data.iterdir() if p.is_dir() and p.name.startswith(a.output_prefix) and p.resolve() not in before]
    if not after:
        # Timestamp collision or rerun: use newest matching directory.
        after=sorted([p.resolve() for p in data.iterdir() if p.is_dir() and p.name.startswith(a.output_prefix)],key=lambda p:p.stat().st_mtime,reverse=True)
    if not after: raise SystemExit('CDMetaPOP created no output directory')
    outdir=after[0]
    summaries=list(outdir.rglob('summary_popAllTime.csv'))
    if len(summaries)!=1:
        raise SystemExit(f'Expected exactly one summary_popAllTime.csv, got {len(summaries)} under {outdir}')
    shutil.copy2(summaries[0],ev/'summary_popAllTime.csv')
    logs=list(outdir.glob('CDmetaPOP*.log'))
    if logs: shutil.copy2(logs[0],ev/'CDmetaPOP.log')
    meta={
      'stage':'v0.6D1-R5.3','status':'PASS_R53_CDMETAPOP_STREAM','seed':a.seed,
      'cdmetapop_version':ver,'cdmetapop_commit':commit,'elapsed_seconds':time.time()-start,
      'engine_output_dir':str(outdir),'summary_source':str(summaries[0]),
      'random_seed_semantics':'PYTHON_RANDOM_AND_NUMPY_GLOBAL_RNG_SEEDED_IN_SAME_SINGLE_SPECIES_PROCESS_BEFORE_RUNPY',
    }
    (ev/'STREAM_RUNTIME.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(meta,separators=(',',':')))
if __name__=='__main__': main()

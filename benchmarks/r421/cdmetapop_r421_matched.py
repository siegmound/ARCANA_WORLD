from __future__ import annotations
import csv, json, random, runpy, shutil, subprocess, sys, traceback
from pathlib import Path
import numpy as np

PIN='3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118'
# REPAIR_PROFILE: frozen R4.7 forcing profile, never comparison-target derived.
contract=Path(sys.argv[1]); profile_path=Path(sys.argv[2]); out=Path(sys.argv[3]); work=Path(sys.argv[4]); repo=Path(sys.argv[5])
out.parent.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)

def read_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def write_csv(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def knots(end_ratio,n):
    if n<2: raise RuntimeError('requires >=2 CDClimate knots')
    return [1.0+(float(end_ratio)-1.0)*(i/(n-1)) for i in range(n)]
def parse_total(token):
    s=str(token or '').split('|')[0].strip(); return float(s) if s not in ('','NA','nan') else None
def summary_ratio(root:Path):
    fs=[p for p in root.rglob('summary_popAllTime.csv') if p.name=='summary_popAllTime.csv']
    if not fs: raise RuntimeError('summary_popAllTime.csv missing')
    rows=read_csv(sorted(fs,key=lambda p:len(str(p)))[0]);
    if not rows: raise RuntimeError('summary_popAllTime.csv empty')
    start=parse_total(rows[0].get('N_Initial')); last=parse_total(rows[-1].get('N_Initial')); growth=float(rows[-1].get('GrowthRate'))
    if start is None or last is None: raise RuntimeError('N_Initial total unavailable')
    final=last*growth; return {'initial_population':start,'final_population':final,'population_response_ratio':final/start if start else None,'summary_rows':len(rows)}
def arm(c,prof,repo,rw,seed,arm_name):
    d=c['engine_input']['drivers']; runtime=int(c['engine_input']['representative_runtime']['steps']); rp=prof['repair_profile']; end_ratio=float(rp['bounded_end_support_ratio']) if arm_name=='dynamic' else 1.0
    src=repo/'src'/'CDmetaPOP.py';
    if not src.exists(): src=repo/'src'/'CDMetaPOP.py'
    examples=repo/'example_files'
    if not src.exists() or not examples.exists(): raise FileNotFoundError('CDMetaPOP pinned source/example_files missing')
    inp=rw/'example_files'; shutil.copytree(examples,inp)
    popsrc=inp/'popvars'/'PopVars.csv'; prows=read_csv(popsrc); pfields=list(prows[0].keys())
    if 'implement_disease' not in pfields:pfields.append('implement_disease')
    prow=dict(prows[0]); prow['implement_disease']='N'; popdst=inp/'popvars'/f'PopVars_R421_{arm_name}.csv'; write_csv(popdst,[prow],pfields)
    runsrc=inp/'RunVars.csv'; rrows=read_csv(runsrc); rfields=list(rrows[0].keys()); rr=dict(rrows[0]); climate=[x.strip() for x in str(rr.get('cdclimgentime') or '0').split('|') if x.strip()]
    habitat=max(0.1,min(0.9,float(d['normalized_habitat_fraction_start']))); gf=max(0.001,min(0.10,float(d['engine_gene_flow_rate']))); ratios=knots(end_ratio,len(climate))
    patch=inp/'patchvars'/'PatchVars.csv'; rows=read_csv(patch); fields=list(rows[0].keys()); kscale=0.70+0.60*habitat
    for row in rows:
        try: base=float(str(row.get('K') or '300').split('|')[0])
        except Exception: base=300.0
        k0=max(20,int(round(base*kscale))); row['K']='|'.join(str(max(20,int(round(k0*r)))) for r in ratios); row['N0']=str(max(10,int(round(k0*0.5))))
        if 'Migration Out Prob' in row: row['Migration Out Prob']=f'{max(0.02,min(0.25,0.02+gf)):.8f}'
        if 'Straying Prob' in row: row['Straying Prob']=f'{max(0.01,min(0.20,gf)):.8f}'
        if 'Dispersal Prob' in row: row['Dispersal Prob']=f'{max(0.02,min(0.30,0.03+gf)):.8f}'
    write_csv(patch,rows,fields); rr['mcruns']='1'; rr['runtime']=str(runtime); rr['output_years']='1'; rr['Popvars']=f'popvars/{popdst.name}'; rundst=inp/f'RunVars_R421_{arm_name}.csv'; write_csv(rundst,[rr],rfields)
    runner="""import random,runpy,sys,numpy as np\nseed=int(sys.argv[1]); src=sys.argv[2]; inp=sys.argv[3]; rv=sys.argv[4]; tag=sys.argv[5]\nrandom.seed(seed); np.random.seed(seed); sys.argv=[src,inp,rv,tag]; runpy.run_path(src,run_name='__main__')\n"""
    proc=subprocess.run([sys.executable,'-c',runner,str(seed),str(src),str(inp),rundst.name,f'R421_{arm_name}_{seed}'],cwd=str(repo/'src'),text=True,capture_output=True,check=False,timeout=600)
    m=summary_ratio(rw) if proc.returncode==0 else {}; return proc,m
try:
    c=json.loads(contract.read_text(encoding='utf-8-sig')); prof=json.loads(profile_path.read_text(encoding='utf-8-sig'))
    if prof.get('job_id')!=c['frozen_parent_job']['job_id']: raise RuntimeError('R4.7 repair profile/job contract mismatch')
    if prof.get('repair_profile',{}).get('comparison_target_used') is not False: raise RuntimeError('comparison target leakage forbidden')
    cp=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],text=True,capture_output=True,check=False); commit=cp.stdout.strip()
    if commit!=PIN: raise RuntimeError(f'CDMetaPOP commit mismatch: {commit}')
    reps=[]
    for spec in c['engine_input']['replicates']:
        ri=int(spec['replicate_index']); seed=int(spec['seed']); base=work/f'rep_{ri:03d}'
        if base.exists(): shutil.rmtree(base)
        ddir=base/'dynamic'; ndir=base/'neutral'; ddir.mkdir(parents=True); ndir.mkdir(parents=True)
        pd,md=arm(c,prof,repo,ddir,seed,'dynamic'); pn,mn=arm(c,prof,repo,ndir,seed,'neutral'); ok=pd.returncode==0 and pn.returncode==0 and md.get('population_response_ratio') and mn.get('population_response_ratio')
        eff=(md['population_response_ratio']/mn['population_response_ratio']) if ok else None
        reps.append({'replicate_index':ri,'seed':seed,'status':'PASS' if ok else 'FAIL','dynamic':md,'neutral':mn,'matched_control_population_effect_ratio':eff,'dynamic_returncode':pd.returncode,'neutral_returncode':pn.returncode})
    result={'stage':'v0.6D1-R4.21','job_id':c['frozen_parent_job']['job_id'],'engine':'CDMetaPOP','adapter_status':'PASS' if all(r['status']=='PASS' for r in reps) else 'ENGINE_EXECUTION_FAILURE','driver_application':'R47_DYNAMIC_FORCING_PLUS_MATCHED_NEUTRAL_CONTROL_WITH_CORRECTED_SUMMARY_EXTRACTION','absolute_population_response_comparability':'PROXY_ONLY','matched_control_semantics':'DIAGNOSTIC_DOMAIN_CANDIDATE_REQUIRES_ARCANA_CAUSAL_TARGET','comparison_target_used':False,'source_commit':commit,'replicates':reps,'canonical_write':False}
except Exception as exc:
    result={'stage':'v0.6D1-R4.21','engine':'CDMetaPOP','adapter_status':'ADAPTER_FAILURE','replicates':[],'error':repr(exc),'traceback':traceback.format_exc()[-12000:],'comparison_target_used':False,'canonical_write':False}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
raise SystemExit(0 if result['adapter_status']=='PASS' else 1)

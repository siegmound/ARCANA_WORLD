from __future__ import annotations
import csv, json, random, re, runpy, shutil, subprocess, sys, traceback
from pathlib import Path
import numpy as np

PIN='3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118'
contract=Path(sys.argv[1]); control_path=Path(sys.argv[2]); out=Path(sys.argv[3]); work=Path(sys.argv[4]); repo=Path(sys.argv[5])
out.parent.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)

def read_csv(p):
    with p.open(newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def write_csv(p,rows,fields):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def count_individual_file(p):
    try:
        with p.open(newline='',encoding='utf-8-sig',errors='replace') as f:
            r=csv.reader(f); hdr=next(r,None); rows=list(r)
        if not hdr: return 0,0
        popidx=next((i for i,x in enumerate(hdr) if str(x).strip().lower() in ('population','natalpop','subpopulation')),None)
        pops=len({row[popidx] for row in rows if popidx is not None and len(row)>popidx}) if popidx is not None else 0
        return len(rows),pops
    except Exception: return 0,0
def generation_key(p):
    nums=[int(x) for x in re.findall(r'\d+',p.stem)]; return nums[-1] if nums else -1

try:
    c=json.loads(contract.read_text(encoding='utf-8-sig')); ctrl=json.loads(control_path.read_text(encoding='utf-8-sig'))
    d=c['engine_input']['drivers']; runtime=int(c['engine_input']['representative_runtime']['steps'])
    if ctrl.get('job_id')!=c['frozen_parent_job']['job_id']: raise RuntimeError('control/job contract identity mismatch')
    if float(ctrl['neutral_end_support_ratio'])!=1.0: raise RuntimeError('R4.8 control must use neutral end support ratio 1.0')
    if ctrl.get('comparison_target_used') is not False: raise RuntimeError('comparison target leakage forbidden')
    src=repo/'src'/'CDmetaPOP.py'
    if not src.exists(): src=repo/'src'/'CDMetaPOP.py'
    examples=repo/'example_files'
    if not src.exists() or not examples.exists(): raise FileNotFoundError('CDMetaPOP pinned source/example_files missing')
    cp=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],text=True,capture_output=True,check=False); commit=cp.stdout.strip()
    if commit!=PIN: raise RuntimeError(f'CDMetaPOP commit mismatch: {commit}')
    habitat=max(0.1,min(0.9,float(d['normalized_habitat_fraction_start']))); gf=max(0.001,min(0.10,float(d['engine_gene_flow_rate'])))
    reps=[]
    for spec in c['engine_input']['replicates']:
        ri=int(spec['replicate_index']); seed=int(spec['seed']); rw=work/f'rep_{ri:03d}'
        if rw.exists(): shutil.rmtree(rw)
        inp=rw/'example_files'; shutil.copytree(examples,inp)
        popsrc=inp/'popvars'/'PopVars.csv'; prows=read_csv(popsrc); pfields=list(prows[0].keys())
        if 'implement_disease' not in pfields: pfields.append('implement_disease')
        prow=dict(prows[0]); prow['implement_disease']='N'; popdst=inp/'popvars'/'PopVars_R48.csv'; write_csv(popdst,[prow],pfields)
        runsrc=inp/'RunVars.csv'; rrows=read_csv(runsrc); rfields=list(rrows[0].keys()); rr=dict(rrows[0])
        climate_raw=str(rr.get('cdclimgentime') or '0'); climate_knots=[x.strip() for x in climate_raw.split('|') if x.strip()!='']
        if len(climate_knots)<2: raise RuntimeError('CDMetaPOP neutral control requires >=2 existing CDClimate knots')
        patch=inp/'patchvars'/'PatchVars.csv'; rows=read_csv(patch); fields=list(rows[0].keys()); kscale=0.70+0.60*habitat
        first_k_series=None; first_n0=None
        for row in rows:
            try: base=float(str(row.get('K') or '300').split('|')[0])
            except Exception: base=300.0
            k0=max(20,int(round(base*kscale))); kvals=[k0 for _ in climate_knots]
            row['K']='|'.join(str(x) for x in kvals)
            n0=max(10,int(round(k0*0.5))); row['N0']=str(n0)
            if first_k_series is None: first_k_series=kvals; first_n0=n0
            if 'Migration Out Prob' in row: row['Migration Out Prob']=f'{max(0.02,min(0.25,0.02+gf)):.8f}'
            if 'Straying Prob' in row: row['Straying Prob']=f'{max(0.01,min(0.20,gf)):.8f}'
            if 'Dispersal Prob' in row: row['Dispersal Prob']=f'{max(0.02,min(0.30,0.03+gf)):.8f}'
        write_csv(patch,rows,fields)
        rr['mcruns']='1'; rr['runtime']=str(runtime); rr['output_years']='1'; rr['Popvars']='popvars/PopVars_R48.csv'; rundst=inp/'RunVars_R48.csv'; write_csv(rundst,[rr],rfields)
        before={p.relative_to(rw).as_posix() for p in rw.rglob('*') if p.is_file()}
        runner="""import random,runpy,sys,numpy as np\nseed=int(sys.argv[1]); src=sys.argv[2]; inp=sys.argv[3]; rv=sys.argv[4]; tag=sys.argv[5]\nrandom.seed(seed); np.random.seed(seed); sys.argv=[src,inp,rv,tag]; runpy.run_path(src,run_name='__main__')\n"""
        proc=subprocess.run([sys.executable,'-c',runner,str(seed),str(src),str(inp),rundst.name,f'R48_{ri:03d}'],cwd=str(repo/'src'),text=True,capture_output=True,check=False,timeout=600)
        after={p.relative_to(rw).as_posix() for p in rw.rglob('*') if p.is_file()}; new=sorted(after-before)
        indfiles=sorted([p for p in rw.rglob('*.csv') if 'ind' in p.name.lower() and p not in (popsrc,popdst)],key=generation_key)
        n0obs,np0=count_individual_file(indfiles[0]) if indfiles else (0,0); n1,np1=count_individual_file(indfiles[-1]) if indfiles else (0,0)
        metrics={'initial_population':n0obs if n0obs>0 else None,'final_population':n1 if n1>0 else None,'initial_occupied_patches':np0 if np0>0 else None,'final_occupied_patches':np1 if np1>0 else None,'runtime_generations':runtime,'new_output_files':len(new),'individual_output_files':len(indfiles),'source_commit':commit,'configured_habitat_support_start':habitat,'configured_gene_flow_rate':gf,'dynamic_k_end_support_ratio':1.0,'cdclimate_knots':climate_knots,'example_patch_k_series':first_k_series,'example_patch_configured_n0':first_n0,'configured_n0_to_k_start_ratio':(first_n0/first_k_series[0]) if first_k_series and first_k_series[0] else None,'forcing_source':'R48_MATCHED_NEUTRAL_CONTROL'}
        status='PASS' if proc.returncode==0 and len(new)>0 else 'FAIL'
        reps.append({'replicate_index':ri,'seed':seed,'status':status,'returncode':proc.returncode,'metrics':metrics,'stdout_tail':proc.stdout[-5000:],'stderr_tail':proc.stderr[-5000:]})
    result={'stage':'v0.6D1-R4.8','job_id':c['frozen_parent_job']['job_id'],'engine':'CDMetaPOP','adapter_status':'PASS' if all(r['status']=='PASS' for r in reps) else 'ENGINE_EXECUTION_FAILURE','diagnostic_control':'MATCHED_NEUTRAL_FORCING','driver_application':'R48_constant_PatchVars.K_via_existing_CDClimate_knots__same_start_N0__same_gene_flow__same_runtime__same_seeds','neutral_end_support_ratio':1.0,'comparison_target_used':False,'compatibility_shim':'implement_disease=N benchmark-local only','source_tree_modified':False,'replicates':reps,'canonical_write':False}
except Exception as exc:
    result={'stage':'v0.6D1-R4.8','engine':'CDMetaPOP','adapter_status':'ADAPTER_FAILURE','diagnostic_control':'MATCHED_NEUTRAL_FORCING','replicates':[],'error':repr(exc),'traceback':traceback.format_exc()[-12000:],'canonical_write':False}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
raise SystemExit(0 if result['adapter_status']=='PASS' else 1)

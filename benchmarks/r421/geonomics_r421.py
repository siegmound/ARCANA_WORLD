from __future__ import annotations
import hashlib, json, os, random, shutil, sys, traceback
from pathlib import Path
import numpy as np

contract=Path(sys.argv[1]); profile=Path(sys.argv[2]); out=Path(sys.argv[3]); work=Path(sys.argv[4])
out.parent.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)

def sha256(p:Path):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
try:
    import geonomics as gnx
    c=json.loads(contract.read_text(encoding='utf-8-sig')); p=json.loads(profile.read_text(encoding='utf-8-sig'))
    if p.get('job_id')!=c['frozen_parent_job']['job_id']: raise RuntimeError('landscape profile/job mismatch')
    if p.get('comparison_target_used') is not False: raise RuntimeError('comparison target leakage forbidden')
    if p.get('profile_status')!='CANONICAL_SPATIAL_BINDING_MATERIALIZED': raise RuntimeError('canonical spatial binding profile not materialized')
    params=Path(p['geonomics_parameters_file']); source=Path(p['canonical_spatial_source']['path'])
    if not params.exists() or not source.exists(): raise FileNotFoundError('materialized Geonomics params or canonical spatial source missing')
    if sha256(source)!=p['canonical_spatial_source']['sha256']: raise RuntimeError('canonical spatial source hash mismatch')
    reps=[]
    for spec in c['engine_input']['replicates']:
        ri=int(spec['replicate_index']); seed=int(spec['seed']); random.seed(seed); np.random.seed(seed); rw=work/f'rep_{ri:03d}'
        if rw.exists(): shutil.rmtree(rw)
        rw.mkdir(parents=True); local_params=rw/params.name; shutil.copy2(params,local_params); old=os.getcwd(); os.chdir(rw)
        try:
            mod=gnx.make_model(str(local_params)); comm=getattr(mod,'comm',{}); species=list(comm.values()) if hasattr(comm,'values') else list(comm)
            initial_population=sum(int(len(sp)) for sp in species); mod.run(); final_population=sum(int(len(sp)) for sp in species)
            metrics={'initial_population':initial_population,'final_population':final_population,'species_count':len(species),'canonical_spatial_source_sha256':p['canonical_spatial_source']['sha256']}; status='PASS' if final_population>0 else 'FAIL'; err=None
        except Exception as exc: metrics={}; status='FAIL'; err=repr(exc)
        finally: os.chdir(old)
        reps.append({'replicate_index':ri,'seed':seed,'status':status,'returncode':0 if status=='PASS' else 1,'metrics':metrics,'error':err})
    result={'stage':'v0.6D1-R4.21','job_id':c['frozen_parent_job']['job_id'],'engine':'Geonomics','adapter_status':'PASS' if all(r['status']=='PASS' for r in reps) else 'ENGINE_EXECUTION_FAILURE','driver_application':'EXPLICIT_CANONICAL_SPATIAL_BINDING_PROFILE','default_model_used':False,'comparison_target_used':False,'replicates':reps,'canonical_write':False}
except Exception as exc:
    result={'stage':'v0.6D1-R4.21','engine':'Geonomics','adapter_status':'ADAPTER_FAILURE','replicates':[],'error':repr(exc),'traceback':traceback.format_exc()[-12000:],'default_model_used':False,'comparison_target_used':False,'canonical_write':False}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
raise SystemExit(0 if result['adapter_status']=='PASS' else 1)

from __future__ import annotations
import json, os, random, shutil, sys, traceback
from pathlib import Path
import numpy as np

contract=Path(sys.argv[1]); out=Path(sys.argv[2]); work=Path(sys.argv[3])
out.parent.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)
try:
    import geonomics as gnx
    c=json.loads(contract.read_text(encoding='utf-8-sig')); reps=[]
    for spec in c['engine_input']['replicates']:
        ri=int(spec['replicate_index']); seed=int(spec['seed']); random.seed(seed); np.random.seed(seed)
        rw=work/f'rep_{ri:03d}'
        if rw.exists(): shutil.rmtree(rw)
        rw.mkdir(parents=True); old=os.getcwd(); os.chdir(rw)
        try:
            mod=gnx.run_default_model()
            comm=getattr(mod,'comm',{}); species=list(comm.values()) if hasattr(comm,'values') else list(comm)
            pops=[]; occ=[]
            for sp in species:
                try: pops.append(int(len(sp)))
                except Exception:
                    nt=getattr(sp,'Nt',[]) or []; pops.append(int(nt[-1]) if nt else 0)
                try: occ.append(int(np.count_nonzero(np.asarray(getattr(sp,'N',None)))))
                except Exception: occ.append(0)
            metrics={'initial_population':None,'final_population':int(sum(pops)),'final_occupied_cells':int(sum(occ)),'species_count':len(species),'model_t':int(getattr(mod,'t',-1)) if isinstance(getattr(mod,'t',-1),(int,np.integer)) else str(getattr(mod,'t',None))}
            status='PASS' if metrics['final_population']>0 and metrics['final_occupied_cells']>0 else 'FAIL'; err=None
        except Exception as exc:
            metrics={}; status='FAIL'; err=repr(exc)
        finally: os.chdir(old)
        reps.append({'replicate_index':ri,'seed':seed,'status':status,'returncode':0 if status=='PASS' else 1,'metrics':metrics,'error':err})
    all_ok=all(r['status']=='PASS' for r in reps)
    # R4.3 deliberately preserves this limitation instead of pretending the default model cells/landscape are ARCANA history.
    result={'stage':'v0.6D1-R4.3','job_id':c['frozen_parent_job']['job_id'],'engine':'Geonomics','adapter_status':'SEMANTIC_NONCOMPARABILITY' if all_ok else 'ENGINE_EXECUTION_FAILURE','execution_status':'ENGINE_EXECUTED','driver_application':'NONE__PINNED_DEFAULT_SPATIAL_MODEL_EXECUTION_ONLY','semantic_limitation':'R4.3_HAS_NOT_YET_MATERIALIZED_A_GEONOMICS_PARAMETER_FILE_FROM_ARCANA_RASTERS;_DO_NOT_INTERPRET_DEFAULT_MODEL_AS_HISTORICAL_CONCORDANCE','replicates':reps,'canonical_write':False}
except Exception as exc:
    result={'stage':'v0.6D1-R4.3','engine':'Geonomics','adapter_status':'ADAPTER_FAILURE','replicates':[],'error':repr(exc),'traceback':traceback.format_exc()[-12000:],'canonical_write':False}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
raise SystemExit(0 if result['adapter_status'] in ('PASS','SEMANTIC_NONCOMPARABILITY') else 1)

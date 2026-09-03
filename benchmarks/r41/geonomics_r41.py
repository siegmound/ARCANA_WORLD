from __future__ import annotations
import json, os, sys, traceback
from pathlib import Path
import numpy as np

out=Path(sys.argv[1]); work=Path(sys.argv[2])
out.parent.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)
os.chdir(work)
try:
    import geonomics as gnx
    mod=gnx.run_default_model()
    comm=getattr(mod,'comm',{})
    species=list(comm.values()) if hasattr(comm,'values') else list(comm)
    pops=[]; occ=[]
    for sp in species:
        try: pops.append(int(len(sp)))
        except Exception:
            nt=getattr(sp,'Nt',[]) or []
            pops.append(int(nt[-1]) if nt else 0)
        ngrid=getattr(sp,'N',None)
        try: occ.append(int(np.count_nonzero(np.asarray(ngrid))))
        except Exception: occ.append(0)
    metrics={
        'species_count':len(species),
        'terminal_population_total':int(sum(pops)),
        'occupied_cells_total':int(sum(occ)),
        'model_class':type(mod).__name__,
        'model_t':int(getattr(mod,'t',-1)) if isinstance(getattr(mod,'t',-1),(int,np.integer)) else str(getattr(mod,'t',None)),
    }
    status='PASS' if metrics['species_count']>=1 and metrics['terminal_population_total']>0 and metrics['occupied_cells_total']>0 else 'FAIL'
    result={'status':status,'returncode':0,'metrics':metrics}
except Exception as exc:
    result={'status':'FAIL','returncode':1,'metrics':{},'error':repr(exc),'traceback':traceback.format_exc()[-8000:]}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
if result['status']!='PASS': raise SystemExit(1)

from pathlib import Path
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from rebaseline_210ma_v0_6D1_R1 import RebaselineConfig,decompose_guild_state

def loadnp(p): z=np.load(p,allow_pickle=False); return {k:z[k] for k in z.files}
meta=json.loads((ROOT/'references/v0_6D1_R1/D1_species_metadata_120.json').read_text())
a1=loadnp(ROOT/'references/v0_6D1_R1/A1_WORLD1_210Ma_REFERENCE.npz')
base=decompose_guild_state(meta,a1,RebaselineConfig())['species_population'].sum((1,2))
out={"status":"PASS","reference_radius_km":6371.0088,"cases":{}}
for factor in (0.95,1.05):
    x=decompose_guild_state(meta,a1,RebaselineConfig(compatibility_radius_km=6371.0088*factor))['species_population'].sum((1,2))
    rel=np.abs(x-base)/np.maximum(base,1e-30)
    out['cases'][str(factor)]={"median_species_total_relative_delta":float(np.median(rel)),"p90":float(np.quantile(rel,.9)),"max":float(rel.max())}
    if rel.max()>=0.05: out['status']='FAIL'
(ROOT/'outputs/v0_6D1_R1/REBASELINE_RADIUS_SENSITIVITY_v0_6D1_R1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['status']=='PASS' else 1)

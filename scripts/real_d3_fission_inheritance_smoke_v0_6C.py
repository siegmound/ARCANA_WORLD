from pathlib import Path
import argparse, json, pickle, sys
import numpy as np
PKG=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PKG/'src'))
from deep_production_runtime_v0_6C import *
from deep_heritable_selection_v0_6B import DeepHeritableConfig
ap=argparse.ArgumentParser(); ap.add_argument('--runpack-root',type=Path,required=True); ap.add_argument('--deep-root',type=Path,required=True); a=ap.parse_args()
R=a.runpack_root.resolve(); D=a.deep_root.resolve(); sys.path.insert(0,str(R/'src'))
from arcana_worldsim.post_cha1 import ordinary_turnover as ot
from arcana_worldsim.late_cenozoic.production_interface import build_production_adapter
ck=pickle.load(open(R/'local_runs/v0_6_5B_natural_control_30Ma_0/checkpoints/checkpoint_061000000.pkl','rb'))
initial=ck['result']; rstate=ck['runtime_state']
cfg=ot.load_config(R/'configs/speciation_bound_cross_trophic_reassignment_v0_6_3D3_3B2_3.json'); adapter=build_production_adapter(R)
prov=V05DeepFieldProvider(D,photo_share=.05); frame=prov.frame(5.0)
va=np.asarray(initial.endpoint_additive_variance,float); scales=np.ones_like(va)
st=initialize_runtime_state(initial.deme_ids,va,scales,frame,61_000_000.,DeepHeritableConfig()); st.d3_runtime_state=rstate
start_events=list(initial.deme_fission_events); result=initial; diag_last=None
for t in np.arange(61_025_000.,61_500_000.+1,25_000.):
    result,st,diag_last=advance_deep_coupled_one_step(R,cfg,result,adapter,prov,st,json.loads((PKG/'references/deep_biological_coupling_v0_4.json').read_text()),scales,end_relative_year=float(t),runtime_cfg=DeepRuntimeConfig(deep_enabled=False))
new_events=result.deme_fission_events[len(start_events):]
serialized=[]
for e in new_events:
    if isinstance(e,dict): serialized.append(e)
    else:
        serialized.append({k:getattr(e,k) for k in dir(e) if not k.startswith('_') and k in ('parent_deme_id','daughter_deme_id','relative_year','year','species_id')})
out={
 'status':'PASS_REAL_D3_FISSION_SIDECAR_INHERITANCE' if len(new_events)==1 and st.deme_ids==result.deme_ids else 'FAIL',
 'deep_enabled':False,
 'start_relative_year':61_000_000.0,
 'end_relative_year':61_500_000.0,
 'start_demes':len(initial.deme_ids),
 'end_demes':len(result.deme_ids),
 'new_fission_count':len(new_events),
 'new_fission_events':serialized,
 'sidecar_ids_match_d3':st.deme_ids==result.deme_ids,
 'last_runtime_diag':diag_last,
 'historical_HX':False,
 'interpretation':'Real SEALED-D3 runtime fission authority; Deep-OFF wrapper only inherits sidecar after D3-authorized birth.'
}
(PKG/'outputs/REAL_D3_FISSION_INHERITANCE_v0_6C.json').write_text(json.dumps(out,indent=2,default=str))
print(json.dumps(out,indent=2,default=str))
raise SystemExit(0 if out['status'].startswith('PASS') else 1)

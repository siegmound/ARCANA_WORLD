from pathlib import Path
import argparse, copy, json, pickle, sys, zipfile
import numpy as np
PKG=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PKG/'src'))
from deep_production_runtime_v0_6C import *
from deep_heritable_selection_v0_6B import DeepHeritableConfig
ap=argparse.ArgumentParser(); ap.add_argument('--runpack-root',type=Path,required=True); ap.add_argument('--deep-root',type=Path,required=True); a=ap.parse_args(); R=a.runpack_root.resolve(); D=a.deep_root.resolve(); sys.path.insert(0,str(R/'src'))
from arcana_worldsim.post_cha1 import ordinary_turnover as ot
from arcana_worldsim.late_cenozoic.production_interface import build_production_adapter
with zipfile.ZipFile(R/'seal_evidence/D3_3B2_LONG_HORIZON_LOCAL_RESULTS.zip') as z: initial=pickle.loads(z.read('d33b2_long_horizon/p2/p2_32_36.pkl'))
cfg=ot.load_config(R/'configs/speciation_bound_cross_trophic_reassignment_v0_6_3D3_3B2_3.json'); adapter=build_production_adapter(R); bio=json.loads((PKG/'references/deep_biological_coupling_v0_4.json').read_text()); prov=V05DeepFieldProvider(D,photo_share=.05); frame=prov.frame(30.0)
va=np.asarray(initial.endpoint_additive_variance,float); scales=np.ones_like(va); hc=DeepHeritableConfig(); rc=DeepRuntimeConfig(deep_enabled=True)
base=initialize_runtime_state(initial.deme_ids,va,scales,frame,36_000_000.,hc)
# Branch A: two continuous governed steps.
r1a,s1a,_=advance_deep_coupled_one_step(R,cfg,initial,adapter,prov,copy.deepcopy(base),bio,scales,end_relative_year=36_025_000.,runtime_cfg=rc)
r2a,s2a,_=advance_deep_coupled_one_step(R,cfg,r1a,adapter,prov,s1a,bio,scales,end_relative_year=36_050_000.,runtime_cfg=rc)
# Branch B: checkpoint + pickle + restore between the same two steps.
r1b,s1b,_=advance_deep_coupled_one_step(R,cfg,initial,adapter,prov,copy.deepcopy(base),bio,scales,end_relative_year=36_025_000.,runtime_cfg=rc)
fp={'d3':'SEALED_R2_REFERENCE','deep':'v0.6C_TEST'}; payload=pickle.loads(pickle.dumps(runtime_checkpoint_payload(s1b,fp))); restored=restore_runtime_checkpoint(payload,fp)
r2b,s2b,_=advance_deep_coupled_one_step(R,cfg,r1b,adapter,prov,restored,bio,scales,end_relative_year=36_050_000.,runtime_cfg=rc)
fields=['endpoint_population','endpoint_trait','endpoint_additive_variance','endpoint_resource_trait','endpoint_resource_variance','endpoint_ecological_ri','endpoint_genomic_ri','endpoint_isolation_clock_generations','endpoint_trophic_mode','endpoint_trophic_mode_variance']
d3={f:bool(np.array_equal(np.asarray(getattr(r2a,f)),np.asarray(getattr(r2b,f)))) for f in fields}
deep={k:bool(np.array_equal(np.asarray(getattr(s2a,k)),np.asarray(getattr(s2b,k)))) for k in ['latent_mean','latent_va','acclimatization','remodeling','recoverable_load','injury','surface_background_energy_j','photo_energy_j','source_buffer_j','cumulative_gross_uptake_j','cumulative_return_flow_j','cumulative_net_sink_j','cumulative_stellar_pump_j']}
out={'status':'PASS_DEEP_ON_CHECKPOINT_RESUME_BIT_EXACT' if all(d3.values()) and all(deep.values()) and r2a.deme_ids==r2b.deme_ids else 'FAIL','d3_field_bit_exact':d3,'deep_field_bit_exact':deep,'deme_ids_exact':r2a.deme_ids==r2b.deme_ids,'endpoint_relative_year':s2b.endpoint_relative_year}
(PKG/'outputs/DEEP_ON_CHECKPOINT_RESUME_v0_6C.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2)); raise SystemExit(0 if out['status'].startswith('PASS') else 1)

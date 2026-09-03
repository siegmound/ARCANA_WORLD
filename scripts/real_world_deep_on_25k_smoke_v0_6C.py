from pathlib import Path
import argparse,json,pickle,sys,zipfile
import numpy as np
PKG=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PKG/'src'))
from deep_production_runtime_v0_6C import *
from deep_heritable_selection_v0_6B import DeepHeritableConfig
ap=argparse.ArgumentParser(); ap.add_argument('--runpack-root',type=Path,required=True); ap.add_argument('--deep-root',type=Path,required=True); a=ap.parse_args(); R=a.runpack_root.resolve(); D=a.deep_root.resolve(); sys.path.insert(0,str(R/'src'))
from arcana_worldsim.post_cha1 import ordinary_turnover as ot
from arcana_worldsim.late_cenozoic.production_interface import build_production_adapter
with zipfile.ZipFile(R/'seal_evidence/D3_3B2_LONG_HORIZON_LOCAL_RESULTS.zip') as z: initial=pickle.loads(z.read('d33b2_long_horizon/p2/p2_32_36.pkl'))
cfg=ot.load_config(R/'configs/speciation_bound_cross_trophic_reassignment_v0_6_3D3_3B2_3.json'); adapter=build_production_adapter(R); bio=json.loads((PKG/'references/deep_biological_coupling_v0_4.json').read_text()); prov=V05DeepFieldProvider(D,photo_share=.05); frame=prov.frame(30.0)
# Dimensionless Deep VA initialization scale only; no trait-direction mapping.
va=np.asarray(initial.endpoint_additive_variance,float); roots=initial.root_species_ids; ridx=np.asarray(initial.root_species_index,int); md={x['species_id']:x for x in json.loads((R/'inputs/D1_METADATA/species_metadata.json').read_text())}; scales=np.zeros_like(va)
for d,r in enumerate(ridx):
    m=md.get(str(roots[int(r)]),{}); scales[d]=[float(m.get('thermal_niche_sigma_c',1.0)),float(m.get('aridity_niche_sigma',1.55))/1.55,.35]
scales=np.maximum(scales,1e-6); st=initialize_runtime_state(initial.deme_ids,va,scales,frame,36_000_000.,DeepHeritableConfig())
res,st,diag=advance_deep_coupled_one_step(R,cfg,initial,adapter,prov,st,bio,scales,end_relative_year=36_025_000.,runtime_cfg=DeepRuntimeConfig(deep_enabled=True))
out={'status':'PASS_REAL_WORLD_DEEP_ON_25K_RUNTIME_SMOKE','start_demes':len(initial.deme_ids),'end_demes':len(res.deme_ids),'start_population':float(np.asarray(initial.endpoint_population).sum()),'end_population':float(np.asarray(res.endpoint_population).sum()),'latent_max_abs':float(np.max(np.abs(st.latent_mean))),'latent_va_median':float(np.median(st.latent_va)),'acclimatization_mean':float(np.mean(st.acclimatization)),'remodeling_mean':float(np.mean(st.remodeling)),'injury_max':float(np.max(st.injury)),'surface_background_energy_j':float(st.surface_background_energy_j.sum()),'photo_energy_j':float(st.photo_energy_j.sum()),'source_buffer_j':float(st.source_buffer_j.sum()),'cumulative_net_sink_j':float(st.cumulative_net_sink_j.sum()),'cumulative_stellar_pump_j':float(st.cumulative_stellar_pump_j.sum()),'diag':diag,'D3_source_modified':False,'historical_HX':False}
(PKG/'outputs/REAL_WORLD_DEEP_ON_25K_SMOKE_v0_6C.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

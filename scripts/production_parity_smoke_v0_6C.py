from pathlib import Path
import argparse, json, pickle, sys, zipfile
from dataclasses import replace
import numpy as np
PKG=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(PKG/'src'))
from deep_production_runtime_v0_6C import *
from deep_heritable_selection_v0_6B import DeepHeritableConfig

ap=argparse.ArgumentParser(); ap.add_argument('--runpack-root',type=Path,required=True); ap.add_argument('--deep-root',type=Path,required=True); a=ap.parse_args()
R=a.runpack_root.resolve(); D=a.deep_root.resolve(); sys.path.insert(0,str(R/'src'))
from arcana_worldsim.post_cha1 import ordinary_turnover as ot
from arcana_worldsim.late_cenozoic.production_interface import build_production_adapter, patched_sealed_d3_substrate
from arcana_worldsim.production_replay.orchestrator import run_variable_step, AbsoluteCadencePolicy
with zipfile.ZipFile(R/'seal_evidence/D3_3B2_LONG_HORIZON_LOCAL_RESULTS.zip') as z: initial=pickle.loads(z.read('d33b2_long_horizon/p2/p2_32_36.pkl'))
cfg=ot.load_config(R/'configs/speciation_bound_cross_trophic_reassignment_v0_6_3D3_3B2_3.json'); adapter=build_production_adapter(R)
fullcfg=replace(cfg,start_relative_year=36_000_000.,end_relative_year=36_100_000.,dt_years=25_000.)
schedule=[(36_025_000.,25_000.),(36_050_000.,25_000.),(36_075_000.,25_000.),(36_100_000.,25_000.)]
with patched_sealed_d3_substrate(adapter): ref=run_variable_step(R,fullcfg,initial_result=initial,step_schedule=schedule,cadence=AbsoluteCadencePolicy(),allow_d33_stability_extension=True)
prov=V05DeepFieldProvider(D,photo_share=.05); frame=prov.frame(30.0); nd=len(initial.deme_ids); va=np.asarray(initial.endpoint_additive_variance,float); scales=np.ones_like(va); st=initialize_runtime_state(initial.deme_ids,va,scales,frame,36_000_000.,DeepHeritableConfig())
r=initial
for t,_ in schedule:
    r,st,diag=advance_deep_coupled_one_step(R,cfg,r,adapter,prov,st,json.loads((PKG/'references/deep_biological_coupling_v0_4.json').read_text()),scales,end_relative_year=t,runtime_cfg=DeepRuntimeConfig(deep_enabled=False))
fields=['endpoint_population','endpoint_trait','endpoint_additive_variance','endpoint_resource_trait','endpoint_resource_variance','endpoint_ecological_ri','endpoint_genomic_ri','endpoint_isolation_clock_generations','endpoint_trophic_mode','endpoint_trophic_mode_variance']
diffs={f:bool(np.array_equal(np.asarray(getattr(ref,f)),np.asarray(getattr(r,f)))) for f in fields}
out={'status':'PASS_DEEP_OFF_PRODUCTION_WRAPPER_PARITY' if all(diffs.values()) and ref.current_species_id==r.current_species_id and ref.deme_ids==r.deme_ids else 'FAIL','field_bit_exact':diffs,'species_ids_exact':ref.current_species_id==r.current_species_id,'deme_ids_exact':ref.deme_ids==r.deme_ids,'speciation_events_exact':ref.speciation_events==r.speciation_events,'fission_events_exact':ref.deme_fission_events==r.deme_fission_events,'endpoint_relative_year':st.endpoint_relative_year,'deep_state_latent_unchanged':bool(np.all(st.latent_mean==0))}
(PKG/'outputs/PRODUCTION_DEEP_OFF_PARITY_v0_6C.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2)); raise SystemExit(0 if out['status'].startswith('PASS') else 1)

from pathlib import Path
import argparse, json, time
import numpy as np
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import rebased_natural_control_runtime_v0_6D1_R2_1 as m


def jsonable(x):
    if isinstance(x,dict): return {str(k):jsonable(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [jsonable(v) for v in x]
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,(np.floating,np.integer)): return x.item()
    return x

ap=argparse.ArgumentParser()
ap.add_argument('--end-age',type=float,default=180.0)
ap.add_argument('--macrostep',type=float,default=500000.0)
ap.add_argument('--biology-cadence',type=float,default=125000.0)
ap.add_argument('--transport-cadence',type=float,default=62500.0)
ap.add_argument('--prefix',default='H0_REBASED_210_180_R21')
ap.add_argument('--enable-vicariance-fission',action='store_true')
args=ap.parse_args()
common=np.load(ROOT/'references/v0_6D1_R2/WORLD1_210Ma_REBASELINE_COMMON_STATE_PARENT_R1.npz',allow_pickle=False)
a1=np.load(ROOT/'references/v0_6D1_R2/A1_WORLD1_210_180_REFERENCE_v0_6D1_R2.npz',allow_pickle=False)
metadata=json.loads((ROOT/'references/v0_6D1_R2/D1_species_metadata_120.json').read_text())
cfg=m.R21Config(end_age_ma=args.end_age,macrostep_years=args.macrostep,biology_cadence_years=args.biology_cadence,
                dt_years=args.biology_cadence,transport_cadence_years=args.transport_cadence,
                persistent_vicariance_fission_enabled=bool(args.enable_vicariance_fission))
t0=time.time();r=m.run(common,a1,metadata,cfg);elapsed=time.time()-t0
out=ROOT/'outputs/v0_6D1_R2_1';out.mkdir(parents=True,exist_ok=True)
prefix=args.prefix
np.savez_compressed(out/f'{prefix}_STATE.npz',population=r['population'],trait=r['trait'],va=r['va'],generation_time=r['generation_time'],
                    component_id=np.asarray(r['component_ids'],dtype='U80'),component_root_species=np.asarray(r['component_root_species'],dtype='U40'),
                    component_species=np.asarray(r['component_species'],dtype='U40'),component_guild=r['component_guild'],ri=r['ri'],clock=r['clock'],contact=r['contact'],trait_distance=r['trait_distance'])
raw={k:v for k,v in r.items() if k not in {'population','trait','va','generation_time','component_guild','ri','clock','contact','trait_distance'}}
raw['wall_seconds']=elapsed
(out/f'{prefix}_RAW.json').write_text(json.dumps(jsonable(raw),indent=2,sort_keys=True),encoding='utf-8')
# Endpoint A1 audit.
env180=m.r2.environment_at(args.end_age,a1,cfg.topology_switch_age_ma)
final=float(r['population'].sum()); ref=float(env180['reference_population'].sum())
guild_tot=[float(r['population'][r['component_guild']==g].sum()) for g in range(1,7)]
ref_g=[float(env180['reference_population'][g-1].sum()) for g in range(1,7)]
ev=[e for e in r['events'] if e['event']=='speciation'];ex=[e for e in r['events'] if e['event']=='ordinary_background_extinction'];fi=[e for e in r['events'] if e['event']=='deme_fission']
ep={'stage':'v0.6D1-R2.1','end_age_ma':args.end_age,'final_total_population':final,'A1_reference_population':ref,
    'global_relative_error_vs_A1':abs(final-ref)/max(abs(ref),1e-15),'final_species_richness':len(r['species_ids']),
    'final_component_count':len(r['component_ids']),'speciation_event_count':len(ev),'ordinary_extinction_event_count':len(ex),'deme_fission_event_count':len(fi),
    'guild_population':guild_tot,'A1_guild_reference':ref_g,'guild_relative_error':[abs(a-b)/max(abs(b),1e-15) for a,b in zip(guild_tot,ref_g)],
    'gate_diagnostics':r['gate_diagnostics'],'gene_flow_closure':r['gene_flow_closure'],'wall_seconds':elapsed}
(out/f'{prefix}_ENDPOINT_AUDIT.json').write_text(json.dumps(ep,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(ep,indent=2))

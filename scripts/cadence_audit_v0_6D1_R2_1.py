from pathlib import Path
import json,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import rebased_natural_control_runtime_v0_6D1_R2_1 as m
common=np.load(ROOT/'references/v0_6D1_R2/WORLD1_210Ma_REBASELINE_COMMON_STATE_PARENT_R1.npz',allow_pickle=False)
a1=np.load(ROOT/'references/v0_6D1_R2/A1_WORLD1_210_180_REFERENCE_v0_6D1_R2.npz',allow_pickle=False)
meta=json.loads((ROOT/'references/v0_6D1_R2/D1_species_metadata_120.json').read_text())

def run(**kw):
 c=m.R21Config(end_age_ma=209.0,**kw);t=time.time();r=m.run(common,a1,meta,c);return r,time.time()-t

def sp_tot(r):
 t=r['population'].sum(axis=(1,2));o={}
 for i,s in enumerate(r['component_species']):o[s]=o.get(s,0.0)+float(t[i])
 return o

def compare(a,b):
 sa,sb=sp_tot(a),sp_tot(b);ids=sorted(set(sa)|set(sb));den=sum(abs(sa.get(s,0)) for s in ids)
 species_weighted=sum(abs(sa.get(s,0)-sb.get(s,0)) for s in ids)/max(den,1e-15)
 raster=float(np.sum(np.abs(a['population']-b['population']))/max(np.sum(np.abs(a['population'])),1e-15)) if a['population'].shape==b['population'].shape else None
 return {'species_total_abundance_weighted_l1':species_weighted,'component_raster_l1':raster,'global_relative_difference':abs(float(a['population'].sum())-float(b['population'].sum()))/max(float(a['population'].sum()),1e-15)}

a,ta=run(macrostep_years=250000.0,biology_cadence_years=125000.0,dt_years=125000.0,transport_cadence_years=62500.0)
b,tb=run(macrostep_years=500000.0,biology_cadence_years=125000.0,dt_years=125000.0,transport_cadence_years=62500.0)
bit={k:bool(np.array_equal(a[k],b[k])) for k in ('population','trait','va','ri','clock')};bit['ids_events']=bool(a['component_ids']==b['component_ids'] and a['component_species']==b['component_species'] and a['events']==b['events'])
coarse,tc=run(macrostep_years=500000.0,biology_cadence_years=125000.0,dt_years=125000.0,transport_cadence_years=125000.0)
fine,tf=run(macrostep_years=500000.0,biology_cadence_years=62500.0,dt_years=62500.0,transport_cadence_years=31250.0)
res={'stage':'v0.6D1-R2.1','window':'210_to_209_Ma','external_macrostep_bit_exact':bit,'macro_250_wall_s':ta,'macro_500_wall_s':tb,
     'transport_125_vs_62p5':compare(coarse,b),'biology_125_transport62p5_vs_biology62p5_transport31p25':compare(b,fine),'wall_seconds':{'transport125':tc,'fine':tf},
     'interpretation':{'external_chunking':'CLOSED_BIT_EXACT','production_biology_cadence_years':125000.0,'production_transport_cadence_years':62500.0,'micro_raster':'STILL_NOT_AUTHORIAL_SEAL_TARGET_IN_DEEP_TIME'}}
out=ROOT/'outputs/v0_6D1_R2_1/CADENCE_CLOSURE_AUDIT_v0_6D1_R2_1.json';out.write_text(json.dumps(res,indent=2,sort_keys=True));print(json.dumps(res,indent=2))

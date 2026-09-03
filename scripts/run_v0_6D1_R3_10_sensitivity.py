from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines import r310_cha1_highres_bridge as r

def main():
 out=ROOT/'local_runs/v0_6D1_R3_10'; out.mkdir(parents=True,exist_ok=True)
 parent=r.validate_parent_r39_authority(ROOT)
 a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
 d=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text()); md=d['species'] if isinstance(d,dict) and 'species' in d else d
 rows=[]
 for amp in (0.15,0.25,0.35):
  prev=None
  for scale in (0.85,1.0,1.15):
   _,rep=r.run_event_bridge(parent['state'],a1,md,r.R310Config(species_risk_amplitude=amp,guild_hazard_scale=scale))
   surv=int(rep['postimpact_survivor_species'])
   rows.append({'species_risk_amplitude':amp,'guild_hazard_scale':scale,'survivors':surv,'extinctions':int(rep['direct_cha1_extinctions']),'extinction_fraction':rep['extinction_fraction'],'median_extinction_year':rep['extinction_time']['median_year'],'max_extinction_year':rep['extinction_time']['max_year']})
   if prev is not None and surv>prev: raise RuntimeError('stronger guild hazard unexpectedly increased survivor count')
   prev=surv
 canonical=[x for x in rows if x['species_risk_amplitude']==0.25 and x['guild_hazard_scale']==1.0][0]
 summary={'schema':'ARCANA_R310_CHA1_SENSITIVITY_V1','stage':r.STAGE,'verdict':'PASS_PREDECLARED_CHA1_HAZARD_SENSITIVITY__CANONICAL_NOT_SELECTED_FROM_ENSEMBLE','canonical_selection_rule':'amp=0.25 and scale=1.0 were fixed before rebased outcome generation','rows':rows,'survivor_range':[min(x['survivors'] for x in rows),max(x['survivors'] for x in rows)],'canonical':canonical,'governance':{'ensemble_used_to_select_canonical':False,'historical_survivor_ids_used':False}}
 p=out/'R3_10_CHA1_SENSITIVITY_SUMMARY.json'; p.write_text(json.dumps(summary,indent=2),encoding='utf-8'); print(json.dumps(summary,indent=2))
if __name__=='__main__': main()

from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines.r39_precha1_continuation import R39Config,validate_r38_checkpoint_authority,validate_cha1_exact_event_authority

def main():
 a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
 md=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text()); rows=md['species'] if isinstance(md,dict) and 'species' in md else md
 a=validate_r38_checkpoint_authority(ROOT); c=validate_cha1_exact_event_authority(ROOT); cfg=R39Config()
 s149,rec=r38.advance_state(a['state'],a1,rows,cfg,149.875)
 out={'stage':'v0.6D1-R3.9','verdict':'PASS_R39_150MA_RESTART_INPUT_AND_ORDINARY_CONTINUATION_SMOKE','biology_steps':len(rec),'end_age_ma':s149.age_ma,'r38_checkpoint_hashes_valid':True,'cha1_exact_event_authority_valid':True,'cha1_applied':False,'deep_biological_coupling':False}
 p=ROOT/'outputs/v0_6D1_R3_9/R3_9_DIAGNOSTIC_SMOKE.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
if __name__=='__main__': main()

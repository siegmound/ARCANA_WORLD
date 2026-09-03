from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines.r39_precha1_continuation import (
 R39Config, PRE_CHA1_AGE_MA, EXPECTED_STEPS_150_TO_66,
 validate_r38_checkpoint_authority, validate_cha1_exact_event_authority,
 save_precha1_checkpoint, load_precha1_checkpoint, event_counts)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',type=Path,default=ROOT/'local_runs/v0_6D1_R3_9'); args=ap.parse_args()
 out=args.out_dir; out.mkdir(parents=True,exist_ok=True)
 a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
 md=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text(encoding='utf-8')); rows=md['species'] if isinstance(md,dict) and 'species' in md else md
 r38auth=validate_r38_checkpoint_authority(ROOT); cha=validate_cha1_exact_event_authority(ROOT)
 cfg=R39Config(); t0=time.time(); s150=r38auth['state']
 s66,records=r38.advance_state(s150,a1,rows,cfg,PRE_CHA1_AGE_MA)
 cp=save_precha1_checkpoint(s66,out,r38auth,cha,cfg); loaded=load_precha1_checkpoint(Path(cp['json']))
 serial=r38.compare_runtime_states(s66,loaded)
 ev=event_counts(s66); forbidden=[e for e in s66.events if 'cha' in str(e.get('event','')).lower()]
 proj=r38.state_projection(s66,rows,cfg)
 valid=bool(len(records)==EXPECTED_STEPS_150_TO_66 and abs(s66.age_ma-66.0)<1e-12 and serial['equivalent'] and not forbidden)
 summary={
  'schema':'ARCANA_R39_150_TO_66_PRE_CHA1_CONTINUATION_V1','stage':'v0.6D1-R3.9',
  'verdict':'PASS_CANONICAL_150_TO_66_H0_CONTINUATION__PRE_CHA1_66MA_CHECKPOINT_READY__CHA1_NOT_APPLIED' if valid else 'FAIL_R39_PRE_CHA1_CONTINUATION',
  'wall_seconds':time.time()-t0,'biology_steps_150_to_66':len(records),'age_ma':s66.age_ma,
  'event_side':'PRE_IMPACT_66P0_MINUS','checkpoint':cp,'serialization_identity':serial,
  'r38_checkpoint_authority':{'json_sha256':r38auth['json_sha256'],'npz_sha256':r38auth['npz_sha256']},
  'cha1_exact_event_authority':{'sha256':cha['sha256'],'exact_event_time_preferred':True,'pulse_before_impact_j':cha['audit']['pulse_before_impact_j'],'pulse_at_impact_total_j':cha['audit']['pulse_at_impact_total_j']},
  'state_66_projection':proj,'event_counts':ev,'forbidden_cha1_events_found':len(forbidden),
  'governance':{'pre_cha1_checkpoint_authorized':valid,'cha1_applied':False,'deep_biological_coupling':False,'ordinary_continuation_past_66_authorized':False,'next_stage_requires_dedicated_cha1_high_resolution_event':True,'scalar_k_physical_constant_authorized':False,'mu_b_or_ceiling_change_authorized':False}}
 sp=out/'R3_9_PRE_CHA1_CONTINUATION_SUMMARY.json'; sp.write_text(json.dumps(summary,indent=2),encoding='utf-8')
 print(json.dumps({k:summary[k] for k in ['stage','verdict','wall_seconds','biology_steps_150_to_66','age_ma','event_side','event_counts','forbidden_cha1_events_found']},indent=2))
 print(json.dumps({'checkpoint':cp,'serialization_identity':serial['equivalent'],'summary':str(sp)},indent=2))
 if not valid: raise SystemExit(2)
if __name__=='__main__': main()

from __future__ import annotations
import json, hashlib, sys, tempfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r37i_production_runtime import validate_promotion_seal
from arcana_worldsim.scientific_engines.r38_restartable_checkpoint import *

def sha(p):
 h=hashlib.sha256();
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()

def main():
 common=np.load(ROOT/'outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz',allow_pickle=False)
 a1=np.load(ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',allow_pickle=False)
 md=json.loads((ROOT/'references/v0_6D1_R3/D1_SPECIES_METADATA.json').read_text()); rows=md['species'] if isinstance(md,dict) and 'species' in md else md
 sealp=ROOT/'outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json'; validate_promotion_seal(sealp)
 cfg=R38Config(end_age_ma=149.0); s0=initialize_210ma_state(common,a1,rows,cfg); s209,recs=advance_state(s0,a1,rows,cfg,209.0)
 old=json.loads((ROOT/'local_runs/v0_6D1_R3_7I/210_to_209p0Ma_R3_7I_canonical.json').read_text())
 p=state_projection(s209,rows,cfg)
 smoke_cmp={
   'biology_steps_equal':len(recs)==8,
   'population_abs_error':abs(p['final_total_population']-float(old['final_total_population'])),
   'q_max_abs_error':abs(p['q_max']-float(old['peak_q'])),
   'species_count_equal':p['species_count']==int(old['species_count']),
   'component_count_equal':p['component_count']==int(old['component_count']),
   'event_counts_equal':p['event_counts']==old['event_counts'],
 }
 smoke_eq=smoke_cmp['biology_steps_equal'] and smoke_cmp['population_abs_error']<=2e-12 and smoke_cmp['q_max_abs_error']<=2e-12 and all(smoke_cmp[k] for k in ('species_count_equal','component_count_equal','event_counts_equal'))
 with tempfile.TemporaryDirectory() as td:
  jp=Path(td)/'s209.json'; save_runtime_state(s209,jp,cfg,sha(sealp)); loaded=load_runtime_state(jp,RUNTIME_SCHEMA)
  serial_cmp=compare_runtime_states(s209,loaded)
  d208,_=advance_state(s209,a1,rows,cfg,208.0); r208,_=advance_state(loaded,a1,rows,cfg,208.0); restart_cmp=compare_runtime_states(d208,r208)
 out={'stage':STAGE,'verdict':'PASS_R38_DIAGNOSTIC_SMOKE__R37I_PARITY__SERIALIZATION_AND_RESTART_IDENTITY' if smoke_eq and serial_cmp['equivalent'] and restart_cmp['equivalent'] else 'FAIL_R38_DIAGNOSTIC_SMOKE',
      'r37i_210_209_equivalence':smoke_cmp,'checkpoint_serialization_identity':serial_cmp,'restart_209_to_208_identity':restart_cmp,
      'governance':{'canonical_150ma_checkpoint_authorized':False,'diagnostic_smoke_only':True}}
 op=ROOT/'outputs/v0_6D1_R3_8/R3_8_DIAGNOSTIC_SMOKE_AUDIT.json'; op.parent.mkdir(parents=True,exist_ok=True); op.write_text(json.dumps(out,indent=2))
 print(json.dumps({'stage':out['stage'],'verdict':out['verdict'],'output':str(op)},indent=2))
 if out['verdict'].startswith('FAIL'): raise SystemExit(2)
if __name__=='__main__': main()

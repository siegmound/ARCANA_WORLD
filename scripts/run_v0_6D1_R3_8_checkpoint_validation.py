from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.scientific_engines.r37i_production_runtime import validate_promotion_seal
from arcana_worldsim.scientific_engines.r38_restartable_checkpoint import (
    R38Config, CHECKPOINT_AGE_MA, initialize_210ma_state, advance_state,
    save_checkpoint, load_checkpoint, compare_runtime_states,
    compare_to_r37h_center_reference, state_projection,
)


def sha(path: Path) -> str:
    h=hashlib.sha256();
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()


def load_inputs():
    common=np.load(ROOT/"outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz",allow_pickle=False)
    a1=np.load(ROOT/"references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz",allow_pickle=False)
    md=json.loads((ROOT/"references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding='utf-8'))
    rows=md['species'] if isinstance(md,dict) and 'species' in md else md
    refp=ROOT/"references/v0_6D1_R3_8/R37H_210_150_K_CENTER_SEALED_REFERENCE.json"
    ref=json.loads(refp.read_text(encoding='utf-8'))
    return common,a1,rows,ref,refp


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--restart-end-age-ma',type=float,default=149.0)
    ap.add_argument('--out-dir',type=Path,default=ROOT/"local_runs/v0_6D1_R3_8")
    args=ap.parse_args()
    if abs(args.restart_end_age_ma-149.0)>1e-12:
        raise SystemExit('R3.8 governed equivalence gate is fixed to 150->149 Ma')
    sealp=ROOT/"outputs/v0_6D1_R3_7I/PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json"
    seal=validate_promotion_seal(sealp); seal_hash=sha(sealp)
    common,a1,rows,ref,refp=load_inputs()
    sealed_ref_hash=seal['r37h_full_closed_loop_evidence']['json_sha256']['K_CENTER']
    if sha(refp)!=sealed_ref_hash:
        raise RuntimeError('R3.8 R3.7H K_CENTER reference hash does not match promotion seal')
    cfg=R38Config(end_age_ma=args.restart_end_age_ma)
    out_dir=args.out_dir; out_dir.mkdir(parents=True,exist_ok=True)
    t0=time.time()
    s0=initialize_210ma_state(common,a1,rows,cfg)
    s150,records_to_150=advance_state(s0,a1,rows,cfg,CHECKPOINT_AGE_MA)
    parent_cmp=compare_to_r37h_center_reference(s150,ref,rows,cfg)
    cp=save_checkpoint(s150,out_dir,seal_hash,cfg)
    direct149,records_direct=advance_state(s150,a1,rows,cfg,args.restart_end_age_ma)
    loaded=load_checkpoint(Path(cp['json']))
    serialized_cmp=compare_runtime_states(s150,loaded)
    restart149,records_restart=advance_state(loaded,a1,rows,cfg,args.restart_end_age_ma)
    restart_cmp=compare_runtime_states(direct149,restart149)
    valid=bool(parent_cmp['equivalent'] and serialized_cmp['equivalent'] and restart_cmp['equivalent']
               and len(records_to_150)==480 and len(records_direct)==8 and len(records_restart)==8)
    summary={
      'schema':'ARCANA_R38_CHECKPOINT_AND_RESTART_VALIDATION_V1','stage':'v0.6D1-R3.8',
      'verdict':'PASS_CANONICAL_150MA_CHECKPOINT__R37I_EQUIVALENT__150_TO_149_RESTART_EXACT__POST_PROMOTION_CONTINUATION_READY' if valid else 'FAIL_R38_CHECKPOINT_OR_RESTART_EQUIVALENCE',
      'wall_seconds':time.time()-t0,
      'promotion_seal_sha256':seal_hash,'r37h_k_center_reference_sha256':sha(refp),
      'biology_steps_210_to_150':len(records_to_150),'biology_steps_150_to_149_direct':len(records_direct),'biology_steps_150_to_149_restart':len(records_restart),
      'checkpoint':cp,'r37i_150ma_exposed_state_equivalence':parent_cmp,
      'checkpoint_serialization_identity':serialized_cmp,'restart_150_to_149_identity':restart_cmp,
      'state_150_projection':state_projection(s150,rows,cfg),'state_149_projection':state_projection(direct149,rows,cfg),
      'governance':{
        'canonical_150ma_checkpoint_authorized':valid,'post_150_continuation_authorized':valid,
        'production_runtime_authority':'R3.7I_SEALED_SEGREGATION_AWARE_RUNTIME',
        'scalar_k_physical_constant_authorized':False,'low_high_release_sentinels_retained':True,
        'mu_b_or_ceiling_change_authorized':False,'deep_biological_coupling':False,
      }
    }
    sp=out_dir/'R3_8_CHECKPOINT_VALIDATION_SUMMARY.json'; sp.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('stage','verdict','wall_seconds','biology_steps_210_to_150','biology_steps_150_to_149_direct','biology_steps_150_to_149_restart')},indent=2))
    print(json.dumps({'checkpoint':cp,'r37i_equivalent':parent_cmp['equivalent'],'serialization_identity':serialized_cmp['equivalent'],'restart_identity':restart_cmp['equivalent'],'summary':str(sp)},indent=2))
    if not valid: raise SystemExit(2)

if __name__=='__main__': main()
